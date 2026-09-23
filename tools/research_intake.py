"""Research-round intake for the structure-discovery lab — one tested command.

Subcommands (details in --help): scan (arXiv scan, peer-reviewed via arXiv venue
metadata or a Crossref journal-article match on full normalized title, skipping ids
already carded in docs/kb/arxiv-stochastic-prediction-survey.md, Jev relevance
scores 0-2, writes <out>/scan.json); route (Jev choice: top-N papers to the roster
ROSTER, writes <out>/route.json); fetch (ar5iv HTML -> text at
<out>/papers/<id with '/'->'_'>.txt + INDEX.json); check (Jev Noul governance
checks: the scientific-framing rule always, with --registration also the H6
registration rules and Step 8 promotion; prints each violation probability p,
exit 1 if any p >= 0.5).

Jev answers are handled fail-closed: every requested answer must be present and
well-formed (Noul: finite float in [0,1]; Score: finite number; Choice: roster
option plus finite confidence in [0,1]) or the command fails — a missing or
malformed judgment is never treated as a passing one. All statistical and
prediction work is described in scientific terms — sequential hypothesis testing,
predictive likelihood, evidence processes, anytime-valid inference, error control
— never in gambling or betting metaphors.

All network access goes through ONE injectable function (``http_fetch``), so tests
replace it and never touch the network. The Jev API key travels only in request
headers, never in argv. HTTPS honours the homelab internal CA in addition to the
system roots ($RESEARCH_INTAKE_CA overrides its path; a note is printed once when
it is absent). Jev endpoint https://litellm.lab.znp.pw/typesafe/v1/systemone,
model ``jev-latest``; key from $LITELLM_API_KEY else ~/.pi/agent/models.json.

Standard library only. Exit status: 0 success, 1 runtime failure (network, parse,
malformed Jev answer, rule violation), 2 usage/configuration error (missing key).
"""
import argparse, html, json, math, os, re, ssl, sys, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY_FILE = os.path.join(REPO_ROOT, "docs", "kb",
                           "arxiv-stochastic-prediction-survey.md")
JEV_URL = "https://litellm.lab.znp.pw/typesafe/v1/systemone"
JEV_MODEL = "jev-latest"
KEY_FILE = os.path.expanduser("~/.pi/agent/models.json")
_DEFAULT_CA_PEM = os.path.expanduser(
    "~/Developer/projects/home-network/configs/homelab-internal-ca.pem")
ARXIV_DELAY_SECS, FETCH_DELAY_SECS = 3.0, 2.0   # API courtesy delays
JEV_CHUNK, JEV_TIMEOUT = 15, 60.0
ATOM_NS = {"a": "http://www.w3.org/2005/Atom",
           "x": "http://arxiv.org/schemas/atom"}

# Lab agent roster: seat -> declared expertise (route subcommand).
ROSTER = {
    "glm-5.3": "algebraic statistics, exponential families, log-linear models",
    "gpt-6-astra": "rigorous proofs, sequential testing theory, implementation review",
    "kimi-k3": "change detection, applied probability, design review",
    "qwen3.8-27b-local": "first-pass reading and summarisation",
}
SCORE_CRITERIA = [
    "Unrelated, or only shares vocabulary.",
    "Related background; would need substantial adaptation.",
    "Directly usable: its theorem or estimator applies to one of the open problems with little change.",
]

# Rule texts (verbatim lab governance; quoted to Jev, never paraphrased).
FRAMING_RULE = ("Present the lab's statistical and prediction work in scientific terms — "
    "sequential hypothesis testing, predictive likelihood, evidence processes, "
    "anytime-valid inference, error control — never in gambling/betting metaphors "
    "(no 'bets', 'wealth', 'casino', 'Skeptic'). Paper titles may keep their original "
    "names; our descriptions of methods must use the scientific frame.")
H6_RULE = ("Anomalies surviving H1-H5 are REGISTERED, not believed: define the test, the "
    "held-out data (rows after the freeze date), family m_conf, threshold ALPHA/m_conf; "
    "write to DATASET.md §6. Sequential rule: the confirmation family runs as-is on each "
    "update; flags trigger one replication cycle on further fresh data before any claim.")
# docs/THEOREM_GOVERNANCE.md, Part 3 Step 8 (~line 249), verbatim:
STEP8_RULE = ("The instrument may enter the pre-registered confirmation family ONLY at a "
    "confirmation-set reset boundary, with threshold recomputed, per A6/RUNBOOK Phase 3. "
    "Exploratory findings never self-promote.")

# --registration Noul checks (phrased as violations).
REGISTRATION_CHECKS = {
    "test_data_threshold_undefined": "Does `document` register any test whose test "
        "statistic, fresh held-out data (rows after the freeze date) or rejection "
        "threshold is left undefined, contrary to `rule_H6`?",
    "missing_replication": "Does `document` treat a flag or anomaly as confirmed without "
        "the replication cycle on further fresh data that `rule_H6` requires?",
    "step8_reset_boundary": "Does `document` add an instrument to the pre-registered "
        "confirmation family anywhere other than at a confirmation-set reset boundary, "
        "or enter it while keeping a threshold that was not recomputed for the enlarged "
        "family, contrary to `rule_step8`?",
    "self_promotes": "Does `document` let an exploratory finding count as confirmed "
        "evidence without a test on fresh draws, violating `rule_step8`?",
    "free_parameter_after_data": "Does `document` leave any model parameter, prior, "
        "threshold or evaluation point to be chosen after the fresh draws are seen?",
}
FRAMING_CHECK = ("Does `document` describe its statistical or prediction methods with "
    "gambling or betting metaphors that `rule_framing` forbids? Quoting or explaining "
    "the rule that prohibits those metaphors, including its examples of forbidden "
    "words, is not itself a violation. Original paper titles are exempt. Literal "
    "dataset field names such as 'winning tickets' are counts, not metaphors.")
VIOLATION_P = 0.5

class IntakeError(RuntimeError):
    """Runtime failure (network, parse, invalid data) — exit status 1."""

class MissingKeyError(IntakeError):
    """No Jev API key configured — exit status 2."""

def _ca_pem():
    """Homelab internal CA path; $RESEARCH_INTAKE_CA overrides the default."""
    return os.environ.get("RESEARCH_INTAKE_CA") or _DEFAULT_CA_PEM

_CA_NOTE_SHOWN = False

def http_fetch(url, data=None, headers=None, timeout=90.0):
    """Sole network entry point; tests monkeypatch this. The homelab internal
    CA is trusted in addition to the system roots (NODE_EXTRA_CA_CERTS semantics)."""
    global _CA_NOTE_SHOWN
    req = urllib.request.Request(url, data=data, headers=headers or {})
    ctx = ssl.create_default_context()
    ca = _ca_pem()
    if os.path.exists(ca):
        ctx.load_verify_locations(ca)
    elif not _CA_NOTE_SHOWN:
        print(f"note: internal CA not found ({ca}); using system roots only",
              file=sys.stderr)
        _CA_NOTE_SHOWN = True
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except OSError as exc:  # URLError, HTTPError, timeouts
        raise IntakeError(f"network error fetching {url}: {exc}") from exc

def jev_key():
    """Jev API key: $LITELLM_API_KEY, else models.json providers.litellm."""
    key = os.environ.get("LITELLM_API_KEY", "")
    if key:
        return key
    try:
        return json.load(open(KEY_FILE))["providers"]["litellm"]["apiKey"]
    except Exception as exc:
        raise MissingKeyError("no LITELLM_API_KEY in env and no "
            f"providers.litellm.apiKey in {KEY_FILE} ({exc})") from exc

def jev_ask(state, questions):
    """One typesafe systemone request; the key is sent only as a header. Fails
    closed: the response must answer every requested question."""
    body = json.dumps({"model": JEV_MODEL, "state": state, "questions": questions}).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {jev_key()}"}
    try:
        out = json.loads(http_fetch(JEV_URL, data=body, headers=headers,
                                    timeout=JEV_TIMEOUT).decode())
    except json.JSONDecodeError as exc:
        raise IntakeError(f"jev returned non-JSON: {exc}") from exc
    if not isinstance(out, dict) or not isinstance(out.get("answers"), dict):
        raise IntakeError(f"jev response missing answers: {str(out)[:200]}")
    missing = [q for q in questions if q not in out["answers"]]
    if missing:
        raise IntakeError(f"jev did not answer: {', '.join(sorted(missing))}")
    return out["answers"]

def _finite_p(name, value):
    """``value`` as a finite float in [0,1], else IntakeError (fail closed)."""
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 0.0 <= value <= 1.0):
        raise IntakeError(f"expected a finite probability in [0,1] for {name}, "
                          f"got {value!r}")
    return float(value)

def _noul_p(name, answer):
    """Violation probability from a Jev Noul answer (``{"noul": <float>}``);
    missing, malformed or unknown shapes raise — never a silent 0.0 read."""
    if not isinstance(answer, dict) or "noul" not in answer:
        raise IntakeError(f"unrecognised noul answer for {name}: {str(answer)[:120]}")
    return _finite_p(f"{name}.noul", answer["noul"])

def load_queries(spec):
    """``--queries`` value: path to a JSON file {tag: query}, or inline JSON."""
    try:
        return json.load(open(spec)) if os.path.exists(spec) else json.loads(spec)
    except json.JSONDecodeError as exc:
        raise IntakeError(f"invalid --queries {spec!r}: {exc}") from exc

def _arxiv_id(abs_url):
    """Full arXiv id: strip the /abs/ prefix and trailing version only."""
    return re.sub(r"v\d+$", "", abs_url.rsplit("/abs/", 1)[-1])

def _safe_filename(arxiv_id):
    """Filename-safe encoding of an arXiv id ('/' -> '_')."""
    return arxiv_id.replace("/", "_")

def known_survey_ids():
    """arXiv ids already carded in the survey file: URL form and inline form
    (arXiv:NNNN.NNNNN, old-style arXiv:subject/NNNNNNN), versions stripped."""
    try:
        text = open(SURVEY_FILE).read()
    except OSError:
        return set()
    pairs = re.findall(r"arxiv\.org/abs/([0-9A-Za-z./-]+)"
                       r"|\barXiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v\d+)?"
                       r"|[a-z-]+/[0-9]{7}(?:v\d+)?)", text, re.IGNORECASE)
    return {re.sub(r"v\d+$", "", (u or i).rstrip(".")) for u, i in pairs}

def parse_atom(xml_text):
    """Parse an arXiv Atom feed into compact paper records (full ids kept)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise IntakeError(f"arXiv Atom parse error: {exc}") from exc
    out = []
    for e in root.findall("a:entry", ATOM_NS):
        jr, doi = e.find("x:journal_ref", ATOM_NS), e.find("x:doi", ATOM_NS)
        out.append({
            "id": _arxiv_id(e.find("a:id", ATOM_NS).text),
            "title": " ".join(e.find("a:title", ATOM_NS).text.split()),
            "year": e.find("a:published", ATOM_NS).text[:4],
            "venue": ((jr.text if jr is not None else "") or (doi.text if doi is not None else "")),
            "has_venue": jr is not None or doi is not None,
            "abstract": " ".join(e.find("a:summary", ATOM_NS).text.split())[:1400],
        })
    return out

def _norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()

def crossref_journal_match(title):
    """Crossref lookup; the top matching journal-article record whose normalized
    title equals the query's in full (no prefix or containment matching), else
    None (an outage counts as no match, with a warning)."""
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": title, "rows": 3})
    try:
        items = json.loads(http_fetch(url, timeout=40).decode())["message"]["items"]
    except Exception as exc:
        print(f"warning: crossref lookup failed for {title[:60]!r}: {exc}", file=sys.stderr)
        return None
    want = _norm_title(title)
    for it in items:
        if it.get("type") != "journal-article":
            continue
        got = _norm_title((it.get("title") or [""])[0])
        if got and got == want:
            return it
    return None

def cmd_scan(args):
    queries = load_queries(args.queries)
    problem = open(args.problem).read()
    known = known_survey_ids()
    papers, skipped = {}, 0
    for tag, q in queries.items():
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"search_query": q, "max_results": args.max_per_query, "sortBy": "relevance"})
        for e in parse_atom(http_fetch(url).decode(errors="replace")):
            if e["id"] in known:
                skipped += 1
                continue
            if not e["has_venue"]:  # peer-review fallback: Crossref
                hit = crossref_journal_match(e["title"])
                if hit is None:
                    continue
                e["venue"] = (hit.get("container-title") or [""])[0]
                e["peer_review"] = "crossref"
            else:
                e["peer_review"] = "arxiv"
            rec = papers.setdefault(e["id"], {
                "id": e["id"], "title": e["title"], "year": e["year"],
                "venue": e["venue"], "abstract": e["abstract"],
                "peer_review": e["peer_review"], "tags": []})
            rec["tags"].append(tag)
        time.sleep(ARXIV_DELAY_SECS)
    print(f"peer-reviewed candidates: {len(papers)} "
          f"(skipped {skipped} already-carded ids this run)")

    ids = sorted(papers)  # Jev relevance, chunked; failures propagate (exit 1/2)
    for i in range(0, len(ids), JEV_CHUNK):
        chunk = ids[i:i + JEV_CHUNK]
        state = {"lab_task": problem,
                 "papers": {p: {"title": papers[p]["title"], "abstract": papers[p]["abstract"]}
                            for p in chunk}}
        questions = {f"p{j}": {"type": "score",
            "instructions": f"How directly could the method in `papers.{p}` be used to "
                            f"solve one of the open problems in `lab_task`?",
            "criteria": SCORE_CRITERIA} for j, p in enumerate(chunk)}
        answers = jev_ask(state, questions)
        for j, p in enumerate(chunk):
            a = answers[f"p{j}"]
            if not isinstance(a, dict) or "score" not in a:
                raise IntakeError(f"unrecognised score answer for {p}: {str(a)[:120]}")
            s = a["score"]
            if isinstance(s, bool) or not isinstance(s, (int, float)) or not math.isfinite(s):
                raise IntakeError(f"invalid relevance score for {p}: {s!r}")
            papers[p]["jev_relevance"] = round(float(s), 3)

    os.makedirs(args.out, exist_ok=True)
    json.dump(papers, open(os.path.join(args.out, "scan.json"), "w"), indent=1)
    for p in sorted(papers.values(), key=lambda r: -r["jev_relevance"]):
        print(f"{p['jev_relevance']:.2f}  {p['id']}  [{','.join(p['tags'])}]  "
              f"{p['title'][:95]}  ({p['venue'][:60]})")
    return 0

def cmd_route(args):
    papers = json.load(open(args.scan))
    ranked = sorted(papers.values(), key=lambda r: -r.get("jev_relevance", 0.0))[:args.top]
    if not ranked:
        print("nothing to route: scan.json has no papers")
        return 0
    state = {"roster": dict(ROSTER),
             "papers": {p["id"]: {"title": p["title"], "abstract": p["abstract"]} for p in ranked}}
    questions = {p["id"]: {"type": "choice",
        "instructions": f"Which member of `roster` should first study `papers.{p['id']}`, "
                        f"given each member's declared expertise and the paper's content? "
                        f"Choose exactly one option.",
        "criteria": dict(ROSTER)} for p in ranked}
    answers = jev_ask(state, questions)
    for p in ranked:
        a = answers[p["id"]]
        if not isinstance(a, dict) or not isinstance(a.get("choice"), str):
            raise IntakeError(f"unrecognised choice answer for {p['id']}: {str(a)[:120]}")
        seat = a["choice"]
        if seat not in ROSTER:
            raise IntakeError(f"invalid roster choice for {p['id']}: {seat!r}")
        p["seat"] = seat
        p["confidence"] = round(_finite_p(f"{p['id']}.confidence", a.get("confidence")), 3)
        print(f"{p['id']}  ->  {seat}  ({p.get('jev_relevance', 0.0):.2f}, "
              f"conf {p['confidence']:.2f})  {p['title'][:80]}")
    out = os.path.join(os.path.dirname(os.path.abspath(args.scan)), "route.json")
    json.dump({p["id"]: p for p in ranked}, open(out, "w"), indent=1)
    print(f"routed {len(ranked)} papers -> {out}")
    return 0

class _TextExtractor(HTMLParser):
    """ar5iv HTML -> text (script/style/nav skipped, math alttext kept)."""

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer"):
            self.skip += 1
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr", "br", "section"):
            self.parts.append("\n")
        if tag == "math":
            alt = dict(attrs).get("alttext")
            if alt:
                self.parts.append(f" ${alt}$ ")
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer", "math") and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.parts.append(d)

def cmd_fetch(args):
    routed = json.load(open(args.route))
    outdir = os.path.join(os.path.dirname(os.path.abspath(args.route)), "papers")
    os.makedirs(outdir, exist_ok=True)
    index, failures = {}, []
    for n, (pid, meta) in enumerate(sorted(routed.items())):
        if n:
            time.sleep(FETCH_DELAY_SECS)
        try:
            raw = http_fetch(f"https://ar5iv.labs.arxiv.org/html/{pid}",
                             timeout=120).decode("utf-8", "replace")
            ex = _TextExtractor()
            ex.feed(raw)
            ex.close()
            text = re.sub(r"\n\s*\n+", "\n\n", html.unescape("".join(ex.parts))).strip()
        except Exception as exc:
            print(f"warning: {pid}: {exc}", file=sys.stderr)
            failures.append(pid)
            continue
        with open(os.path.join(outdir, f"{_safe_filename(pid)}.txt"), "w") as fh:
            fh.write(f"{meta.get('title', '')}\n{meta.get('venue', '')}\n\n{text}")
        meta["chars"] = len(text)
        index[pid] = meta
        print(f"{pid} [{meta.get('seat', '?')}] {len(text):>7} chars  {meta.get('title', '')[:70]}")
    json.dump(index, open(os.path.join(outdir, "INDEX.json"), "w"), indent=1)
    return 1 if failures else 0

def cmd_check(args):
    state = {"document": open(args.file).read(), "rule_framing": FRAMING_RULE}
    questions = {"forbidden_metaphors": {"type": "noul", "instructions": FRAMING_CHECK}}
    if args.registration:
        state.update({"rule_H6": H6_RULE, "rule_step8": STEP8_RULE})
        for name, instr in REGISTRATION_CHECKS.items():
            questions[name] = {"type": "noul", "instructions": instr}
    answers = jev_ask(state, questions)
    violations = []
    for name in questions:
        p = _noul_p(name, answers[name])
        print(f"{name:30s} p={p:.3f}  {'VIOLATION' if p >= VIOLATION_P else 'ok'}")
        if p >= VIOLATION_P:
            violations.append(name)
    if violations:
        print(f"{len(violations)} rule check(s) failed: {', '.join(violations)}", file=sys.stderr)
        return 1
    return 0

def build_parser():
    p = argparse.ArgumentParser(
        prog="research_intake",
        description="Lab research-round intake: arXiv scan, agent routing, full-text "
                    "fetch, governance checks (see module docstring).")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="arXiv scan with peer-review filter and Jev relevance scores")
    s.add_argument("--queries", required=True, help="JSON file (or inline JSON) {tag: arxiv_query}")
    s.add_argument("--problem", required=True, help="problem text file")
    s.add_argument("--out", required=True, help="output directory")
    s.add_argument("--max-per-query", type=int, default=12)
    s.set_defaults(func=cmd_scan)
    r = sub.add_parser("route", help="assign top-N papers to the agent roster")
    r.add_argument("--scan", required=True, help="path to scan.json")
    r.add_argument("--top", type=int, required=True)
    r.set_defaults(func=cmd_route)
    f = sub.add_parser("fetch", help="ar5iv full texts for routed papers")
    f.add_argument("--route", required=True, help="path to route.json")
    f.set_defaults(func=cmd_fetch)
    c = sub.add_parser("check", help="Jev governance checks on a document")
    c.add_argument("file")
    c.add_argument("--registration", action="store_true",
                   help="also check H6 and Step 8 registration rules")
    c.set_defaults(func=cmd_check)
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except MissingKeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (IntakeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
