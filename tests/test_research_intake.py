#!/usr/bin/env python3
"""Offline tests for tools/research_intake.py — no network, no credentials.

``http_fetch`` (the tool's single network entry point) is replaced with
fixture-backed responders; the Jev responder validates the outgoing request
shapes against the TypeSafe contract (question types, `criteria` on choice
questions), so contract drift fails tests. The network fixture sets a dummy
API key and isolates KEY_FILE: operator credentials are never read.

Run: python -m pytest tests/test_research_intake.py -q
"""
import importlib.util
import json
import os
import urllib.parse

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(REPO, "tools", "research_intake.py")
FIX = os.path.join(REPO, "tests", "fixtures", "research_intake")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ri = load("research_intake", TOOL)


def fixture(name):
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


def score_answer(value):
    return {**json.loads(fixture("jev_score_answer.json")), "score": value}


class FakeNet:
    """Replaces ri.http_fetch; dispatches on URL substring, records calls."""

    def __init__(self, monkeypatch):
        self.handlers = []  # (substring, callable(url, data, headers) -> bytes)
        self.calls = []
        self.last_jev_body = None
        monkeypatch.setattr(ri, "http_fetch", self)
        monkeypatch.setattr(ri, "ARXIV_DELAY_SECS", 0.0)
        monkeypatch.setattr(ri, "FETCH_DELAY_SECS", 0.0)
        # Tests never need operator credentials: dummy key, isolated KEY_FILE.
        monkeypatch.setenv("LITELLM_API_KEY", "test-dummy-key")
        monkeypatch.setattr(ri, "KEY_FILE", "/nonexistent/models.json")

    def add(self, substring, handler):
        self.handlers.append((substring, handler))

    def jev(self, answers, default=None, drop=()):
        """Jev responder that validates the request contract. `answers` maps
        question id -> answer object; questions not stubbed get `default`
        (AssertionError if default is None, so tests cannot silently pass).
        `drop` removes ids from the response to simulate partial answers."""
        def handler(url, data, headers):
            assert url == ri.JEV_URL
            assert headers.get("Authorization", "").startswith("Bearer ")
            assert headers.get("Content-Type") == "application/json"
            body = json.loads(data)
            assert body["model"] == ri.JEV_MODEL
            for qid, q in body["questions"].items():
                assert q.get("type") in ("noul", "choice", "score"), (qid, q)
                assert isinstance(q.get("instructions"), str) and q["instructions"], qid
                if q["type"] == "choice":  # contract: options live in `criteria`
                    assert q.get("criteria") == dict(ri.ROSTER), (qid, q)
                    assert "options" not in q, qid
                elif q["type"] == "score":
                    assert isinstance(q.get("criteria"), list) and q["criteria"], qid
            self.last_jev_body = body
            out = {}
            for qid in body["questions"]:
                if qid in answers:
                    out[qid] = answers[qid]
                elif default is not None:
                    out[qid] = default
                else:
                    raise AssertionError(f"test did not stub answer for {qid!r}")
            for k in drop:
                out.pop(k, None)
            return json.dumps({"answers": out}).encode()

        self.add("litellm.lab.znp.pw", handler)

    def __call__(self, url, data=None, headers=None, timeout=90.0):
        self.calls.append((url, data, headers))
        for substring, handler in self.handlers:
            if substring in url:
                return handler(url, data, headers)
        raise AssertionError(f"unexpected url in offline test: {url}")


@pytest.fixture
def net(monkeypatch):
    return FakeNet(monkeypatch)


@pytest.fixture
def survey(monkeypatch, tmp_path):
    path = tmp_path / "survey.md"
    path.write_text("carded: https://arxiv.org/abs/2004.00001 and (arXiv:2501.09999)\n")
    monkeypatch.setattr(ri, "SURVEY_FILE", str(path))
    return path


# ---------------------------------------------------------------------------
# arXiv ids and survey-card matching
# ---------------------------------------------------------------------------

def test_parse_atom_keeps_full_arxiv_ids():
    ids = {p["id"] for p in ri.parse_atom(fixture("arxiv_atom.xml"))}
    assert "math/0608100" in ids  # old-style subject prefix kept whole
    assert "2501.01001" in ids  # version suffix stripped
    assert not any(i.endswith(("v1", "v2")) or i.startswith("0608100") for i in ids)


def test_known_survey_ids_url_inline_and_old_style(monkeypatch, tmp_path):
    path = tmp_path / "survey.md"
    path.write_text("See https://arxiv.org/abs/2004.00001v2, cite (arXiv:1901.05710) "
                    "and arXiv:2009.03167, plus old-style "
                    "https://arxiv.org/abs/math/0608100v2 and arXiv:math/0608100.\n")
    monkeypatch.setattr(ri, "SURVEY_FILE", str(path))
    assert ri.known_survey_ids() == {"2004.00001", "1901.05710", "2009.03167",
                                     "math/0608100"}


def test_known_survey_ids_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(ri, "SURVEY_FILE", str(tmp_path / "nope.md"))
    assert ri.known_survey_ids() == set()


# ---------------------------------------------------------------------------
# scan: peer-review filter, known-id skip, Crossref fallback, ranking, failures
# ---------------------------------------------------------------------------

def test_scan_filter_skip_crossref_ranking(net, survey, tmp_path, capsys):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    net.add("api.crossref.org", lambda u, d, h: fixture("crossref_items.json"))
    net.jev({"p0": score_answer(2.0),    # 2501.01001 (journal_ref)
             "p1": score_answer(0.5),    # 2501.01002 (DOI)
             "p2": score_answer(1.25),   # 2501.01003 (Crossref fallback)
             "p3": score_answer(1.75)})  # math/0608100 (journal_ref)
    problem = tmp_path / "problem.txt"
    problem.write_text("Open problems: anytime-valid tests; change detection.")
    out = tmp_path / "out"
    queries = tmp_path / "queries.json"
    queries.write_text(json.dumps({"eprocess": 'abs:"e-process"'}))

    rc = ri.main(["scan", "--queries", str(queries), "--problem", str(problem),
                  "--out", str(out)])
    assert rc == 0
    scan = json.load(open(out / "scan.json"))
    # 2004.00001 (survey URL form) and 2501.09999 (survey inline form) skipped.
    assert sorted(scan) == ["2501.01001", "2501.01002", "2501.01003", "math/0608100"]
    assert scan["2501.01001"]["peer_review"] == "arxiv"
    assert scan["2501.01001"]["venue"] == "Biometrika"
    assert scan["2501.01002"]["peer_review"] == "arxiv"
    assert scan["2501.01002"]["venue"] == "10.1234/demo.2025"
    assert scan["2501.01003"]["peer_review"] == "crossref"
    assert scan["2501.01003"]["venue"] == "Sequential Analysis"
    assert scan["math/0608100"]["id"] == "math/0608100"
    assert scan["2501.01001"]["jev_relevance"] == 2.0
    assert scan["2501.01002"]["jev_relevance"] == 0.5
    assert scan["2501.01003"]["jev_relevance"] == 1.25
    out_text = capsys.readouterr().out
    # Summary counts the ids actually skipped this run, not the survey total.
    assert "skipped 2 already-carded ids this run" in out_text
    ranked = [ln for ln in out_text.splitlines() if ln.startswith(("0.", "1.", "2."))]
    assert [ln.split()[1] for ln in ranked] == ["2501.01001", "math/0608100",
                                                "2501.01003", "2501.01002"]


def test_scan_arxiv_request_has_query_and_max_results(net, survey, tmp_path):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    net.jev({f"p{i}": score_answer(1.0) for i in range(4)})
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"eprocess": "abs:e-process"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out"),
                  "--max-per-query", "7"])
    assert rc == 0
    arxiv_urls = [u for u, d, h in net.calls if "export.arxiv.org" in u]
    assert len(arxiv_urls) == 1
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(arxiv_urls[0]).query)
    assert qs["search_query"] == ["abs:e-process"]
    assert qs["max_results"] == ["7"]


def test_scan_crossref_no_match_drops_paper(net, survey, tmp_path):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))

    def no_journal_article(url, data, headers):  # only a non-journal preprint
        body = json.loads(fixture("crossref_items.json"))
        body["message"]["items"] = [body["message"]["items"][1]]
        return json.dumps(body).encode()

    net.add("api.crossref.org", no_journal_article)
    net.jev({f"p{i}": score_answer(1.0) for i in range(3)})
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"eprocess": "abs:test"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out")])
    assert rc == 0
    scan = json.load(open(tmp_path / "out" / "scan.json"))
    assert sorted(scan) == ["2501.01001", "2501.01002", "math/0608100"]  # 01003 dropped


def test_crossref_requires_full_normalized_title_equality(net):
    net.add("api.crossref.org", lambda u, d, h: fixture("crossref_items.json"))
    hit = ri.crossref_journal_match("E-Detectors for Low-Dimensional Deviations")
    assert hit and hit["type"] == "journal-article"
    assert hit["container-title"] == ["Sequential Analysis"]
    # Near-titles must not match: no containment either way, no prefix equality.
    for near in ("E-Detectors for Low-Dimensional Deviations: Optimality",
                 "E-Detectors for Low-Dimensional Deviations (extended)",
                 "E-Detectors",
                 "Sequential Testing for Exponential Families: Counterexamples"):
        assert ri.crossref_journal_match(near) is None


def test_scan_missing_key_exit_2(net, monkeypatch, survey, tmp_path):
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)  # fixture dummy removed
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"t": "abs:test"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out")])
    assert rc == 2
    assert not (tmp_path / "out" / "scan.json").exists()


def test_scan_scoring_failure_exit_1(net, survey, tmp_path, capsys):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    net.add("litellm.lab.znp.pw", lambda u, d, h: b"<html>502 Bad Gateway</html>")
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"t": "abs:test"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out")])
    assert rc == 1
    assert not (tmp_path / "out" / "scan.json").exists()
    assert not capsys.readouterr().out.count("  0.00  ")  # never printed as scored


def test_scan_missing_relevance_answer_exit_1(net, survey, tmp_path):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    net.jev({f"p{i}": score_answer(1.0) for i in range(4)}, drop=("p2",))
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"t": "abs:test"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out")])
    assert rc == 1
    assert not (tmp_path / "out" / "scan.json").exists()


def test_scan_malformed_relevance_answer_exit_1(net, survey, tmp_path):
    net.add("export.arxiv.org", lambda u, d, h: fixture("arxiv_atom.xml"))
    net.jev({}, default={"score": "very relevant"})  # not a finite number
    problem = tmp_path / "problem.txt"
    problem.write_text("problems")
    rc = ri.main(["scan", "--queries", '{"t": "abs:test"}',
                  "--problem", str(problem), "--out", str(tmp_path / "out")])
    assert rc == 1
    assert not (tmp_path / "out" / "scan.json").exists()


def test_load_queries_inline_and_file(tmp_path):
    qfile = tmp_path / "q.json"
    qfile.write_text(json.dumps({"tag": "abs:x"}))
    assert ri.load_queries(str(qfile)) == {"tag": "abs:x"}
    assert ri.load_queries('{"tag": "abs:x"}') == {"tag": "abs:x"}
    with pytest.raises(ri.IntakeError):
        ri.load_queries("{not json")


# ---------------------------------------------------------------------------
# route: choice contract (criteria), answer reading, invalid seats
# ---------------------------------------------------------------------------

def write_scan(path, papers):
    json.dump(papers, open(path, "w"))


def paper(pid, title, relevance):
    return {"id": pid, "title": title, "abstract": "a", "venue": "V",
            "jev_relevance": relevance}


def test_route_assigns_top_n_seats(net, tmp_path, capsys):
    write_scan(tmp_path / "scan.json", {
        "2501.01001": paper("2501.01001", "Anytime-Valid Testing", 2.0),
        "2501.01002": paper("2501.01002", "Change Detection", 1.0),
        "2501.01003": paper("2501.01003", "E-Detectors", 1.5)})
    choice = json.loads(fixture("jev_choice_answer.json"))
    net.jev({pid: {**choice, "choice": seat} for pid, seat in
             [("2501.01001", "gpt-6-astra"), ("2501.01003", "kimi-k3")]})
    rc = ri.main(["route", "--scan", str(tmp_path / "scan.json"), "--top", "2"])
    assert rc == 0
    routed = json.load(open(tmp_path / "route.json"))
    assert sorted(routed) == ["2501.01001", "2501.01003"]  # top-2 by relevance
    assert routed["2501.01001"]["seat"] == "gpt-6-astra"
    assert 0.0 <= routed["2501.01001"]["confidence"] <= 1.0
    # Choice contract: the whole roster is sent as `criteria`, never `options`.
    question = net.last_jev_body["questions"]["2501.01001"]
    assert question["type"] == "choice"
    assert question["criteria"] == dict(ri.ROSTER)
    assert "options" not in question
    assert net.last_jev_body["state"]["roster"] == dict(ri.ROSTER)
    assert "kimi-k3" in capsys.readouterr().out


@pytest.mark.parametrize("answer", [{"choice": "not-on-the-roster", "confidence": 0.9},
                                    {"confidence": 0.9},   # no `choice` key
                                    "kimi-k3"])            # bare string, not an object
def test_route_rejects_invalid_answers(net, tmp_path, answer):
    write_scan(tmp_path / "scan.json",
               {"2501.01001": paper("2501.01001", "T", 1.0)})
    net.jev({"2501.01001": answer})
    assert ri.main(["route", "--scan", str(tmp_path / "scan.json"),
                    "--top", "1"]) == 1


def test_route_rejects_missing_confidence(net, tmp_path):
    write_scan(tmp_path / "scan.json",
               {"2501.01001": paper("2501.01001", "T", 1.0)})
    net.jev({"2501.01001": {"choice": "kimi-k3"}})  # confidence absent
    assert ri.main(["route", "--scan", str(tmp_path / "scan.json"),
                    "--top", "1"]) == 1


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

AR5IV_HTML = (b"<html><head><style>body{color:red}</style></head><body>"
              b"<nav>menu</nav><h1>Title</h1>"
              b"<p>Intro paragraph with <math alttext='\\theta'>x</math> symbol.</p>"
              b"<script>evil()</script><p>Second paragraph &amp; more.</p>"
              b"</body></html>")


def test_fetch_writes_texts_and_index(net, tmp_path):
    write_scan(tmp_path / "route.json", {
        "2501.01001": {"id": "2501.01001", "title": "Anytime-Valid Testing",
                       "venue": "Biometrika", "seat": "gpt-6-astra",
                       "jev_relevance": 2.0}})
    net.add("ar5iv.labs.arxiv.org", lambda u, d, h: AR5IV_HTML)
    rc = ri.main(["fetch", "--route", str(tmp_path / "route.json")])
    assert rc == 0
    text = open(tmp_path / "papers" / "2501.01001.txt").read()
    assert text.startswith("Anytime-Valid Testing\nBiometrika\n")
    import re as _re
    flat = _re.sub(r"\s+", " ", text)
    assert "Intro paragraph with $\\theta$ symbol." in flat
    assert "Second paragraph & more." in flat
    assert "evil()" not in text and "menu" not in text
    index = json.load(open(tmp_path / "papers" / "INDEX.json"))
    assert index["2501.01001"]["chars"] == len(text.split("\n\n", 1)[1])
    assert index["2501.01001"]["seat"] == "gpt-6-astra"


def test_fetch_old_style_id_keeps_url_and_encodes_filename(net, tmp_path):
    write_scan(tmp_path / "route.json", {
        "math/0608100": {"id": "math/0608100", "title": "Game-Theoretic Probability",
                         "venue": "Annals of Probability", "seat": "glm-5.3"}})
    net.add("ar5iv.labs.arxiv.org", lambda u, d, h: AR5IV_HTML)
    rc = ri.main(["fetch", "--route", str(tmp_path / "route.json")])
    assert rc == 0
    assert (tmp_path / "papers" / "math_0608100.txt").exists()
    url = next(u for u, d, h in net.calls if "ar5iv" in u)
    assert url.endswith("/html/math/0608100")  # full identifier in the URL


def test_fetch_failure_exit_1(net, tmp_path):
    write_scan(tmp_path / "route.json", {
        "9999.99999": {"id": "9999.99999", "title": "Missing", "venue": "",
                       "seat": "kimi-k3"}})
    rc = ri.main(["fetch", "--route", str(tmp_path / "route.json")])
    assert rc == 1  # paper failed -> runtime failure exit code
    index = json.load(open(tmp_path / "papers" / "INDEX.json"))
    assert index == {}


# ---------------------------------------------------------------------------
# check: noul probabilities, fail-closed shapes, framing rules, registration
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pval,expected_rc", [(0.04, 0), (0.5, 1), (0.93, 1)])
def test_check_noul_threshold_below_at_above_half(net, tmp_path, capsys, pval, expected_rc):
    net.jev({}, default={"noul": pval})
    doc = tmp_path / "draft.md"
    doc.write_text("We use sequential hypothesis testing with anytime-valid "
                   "error control.")
    rc = ri.main(["check", str(doc)])
    assert rc == expected_rc
    out = capsys.readouterr().out
    assert f"forbidden_metaphors" in out
    assert f"p={pval:.3f}" in out
    assert ("VIOLATION" in out) == (expected_rc == 1)


@pytest.mark.parametrize("bad", [True, False, "0.9", 1.5, -0.1, {"p": 0.9}, {},
                                 [0.5], "", float("nan")])
def test_check_malformed_noul_fails_closed(net, tmp_path, bad):
    net.jev({}, default=bad)  # unknown/malformed shapes, incl. bool truthiness
    doc = tmp_path / "draft.md"
    doc.write_text("draft")
    assert ri.main(["check", str(doc)]) == 1


def test_check_missing_answer_fails_closed(net, tmp_path):
    net.jev({}, default={"noul": 0.04}, drop=("forbidden_metaphors",))
    doc = tmp_path / "draft.md"
    doc.write_text("draft")
    assert ri.main(["check", str(doc)]) == 1


def test_check_clean_document_exit_0(net, tmp_path, capsys):
    net.jev({}, default=json.loads(fixture("jev_noul_clean.json")))
    doc = tmp_path / "draft.md"
    doc.write_text("We use sequential hypothesis testing with anytime-valid "
                   "error control.")
    rc = ri.main(["check", str(doc)])
    assert rc == 0
    assert "forbidden_metaphors" in capsys.readouterr().out


def test_framing_rule_and_check_text():
    # FRAMING_RULE carries the full lab sentence including the title exemption.
    assert "Paper titles may keep their original names" in ri.FRAMING_RULE
    assert "our descriptions of methods must use the scientific frame" in ri.FRAMING_RULE
    # FRAMING_CHECK exempts quoting/explaining the rule and original titles.
    assert "Quoting or explaining the rule" in ri.FRAMING_CHECK
    assert "Original paper titles are exempt" in ri.FRAMING_CHECK
    assert "'winning tickets' are counts, not metaphors" in ri.FRAMING_CHECK


def test_check_registration_question_set_and_rules(net, tmp_path):
    net.jev({}, default=json.loads(fixture("jev_noul_clean.json")))
    doc = tmp_path / "registration.md"
    doc.write_text("Test statistic defined on draws after the freeze date; "
                   "threshold ALPHA/m_conf; one replication cycle before any "
                   "claim.")
    assert ri.main(["check", str(doc)]) == 0
    asked_plain = set(net.last_jev_body["questions"])
    assert ri.main(["check", str(doc), "--registration"]) == 0
    asked_reg = set(net.last_jev_body["questions"])
    assert asked_plain == {"forbidden_metaphors"}
    assert asked_reg == {"forbidden_metaphors", "test_data_threshold_undefined",
                         "missing_replication", "step8_reset_boundary",
                         "self_promotes", "free_parameter_after_data"}
    state = net.last_jev_body["state"]
    assert state["rule_framing"] == ri.FRAMING_RULE
    assert "reset boundary" in state["rule_step8"]
    assert "recomputed" in state["rule_step8"]


def test_step8_checks_cover_boundary_threshold_and_fresh_draws():
    boundary = ri.REGISTRATION_CHECKS["step8_reset_boundary"]
    assert "confirmation-set reset boundary" in boundary
    assert "recomputed for the enlarged family" in boundary
    assert "fresh draws" in ri.REGISTRATION_CHECKS["self_promotes"]


def test_check_registration_violation_exit_1(net, tmp_path):
    net.jev({"free_parameter_after_data": json.loads(fixture("jev_noul_violation.json"))},
            default=json.loads(fixture("jev_noul_clean.json")))
    doc = tmp_path / "registration.md"
    doc.write_text("registration draft")
    assert ri.main(["check", str(doc), "--registration"]) == 1


# ---------------------------------------------------------------------------
# key handling and CA configuration
# ---------------------------------------------------------------------------

def test_missing_key_exit_2(monkeypatch, tmp_path):
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.setattr(ri, "KEY_FILE", str(tmp_path / "no" / "models.json"))
    doc = tmp_path / "draft.md"
    doc.write_text("text")
    assert ri.main(["check", str(doc)]) == 2


def test_jev_key_from_env_sent_as_header_only(monkeypatch, net, tmp_path):
    monkeypatch.setenv("LITELLM_API_KEY", "secret-key-123")
    net.add("litellm.lab.znp.pw", lambda u, d, h: json.dumps(
        {"answers": {k: json.loads(fixture("jev_noul_clean.json"))
                     for k in json.loads(d)["questions"]}}).encode())
    doc = tmp_path / "draft.md"
    doc.write_text("clean draft")
    assert ri.main(["check", str(doc)]) == 0
    url, data, headers = net.calls[-1]
    assert headers["Authorization"] == "Bearer secret-key-123"
    assert "secret-key-123" not in url  # key never in argv/URL
    assert b"secret-key-123" not in data  # and never in the body


def test_ca_pem_env_override(monkeypatch):
    monkeypatch.setenv("RESEARCH_INTAKE_CA", "/tmp/lab-internal-ca.pem")
    assert ri._ca_pem() == "/tmp/lab-internal-ca.pem"
    monkeypatch.delenv("RESEARCH_INTAKE_CA", raising=False)
    assert ri._ca_pem() == ri._DEFAULT_CA_PEM
