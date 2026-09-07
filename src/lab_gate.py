#!/usr/bin/env python3
"""Gate and merge (R3): decide every heal proposal with no human in the loop.

    python3 src/lab_gate.py --new [--verifier pi|codex] [--dry-run]
    python3 src/lab_gate.py --pr N  [--verifier pi|codex] [--dry-run]

For each `heal` PROPOSED row that has a pull request and no later `gate` row
for the same (defect_key, defect_commit, branch), the gate decides ONE of:

  ROUTED    owner-reserved (constraint 6): the diff touches the constitution,
            a registration, a G3+ grade line under docs/kb/, or the loop's own
            gate machinery; the agent's notes say OWNER-RESERVED; or the
            occurrence has used its heal attempts. One GitHub issue per
            occurrence (label owner-decision) carries the evidence; the PR
            stays open; nothing is merged.
  REJECTED  a mechanical check failed (required CI checks not green; the
            defect's own check fails at the PR head in a fresh worktree; a
            ledger file lost lines; a test file was deleted) or the
            independent verifier disagreed / was of the healer's own model
            family (C7) / did not answer. The PR is closed with the reasons.
  MERGED    every mechanical check passed AND a read-only verifier of a
            different model family answered AGREE. Merge commit
            `Merge PR #N: <title>`, branch deleted.

Each decision appends exactly one `gate` row. The defect row itself closes
only when the collector observes PASS (R0 semantics). LAB_VERIFY_CMD /
LAB_VERIFY_FAMILY / LAB_VERIFY_MODEL override the verifier preset; tests
inject fakes for GitHub, the verifier and the defect check.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402
import outcome_collect as OC  # noqa: E402
import outcome_attribute as OA  # noqa: E402
import lab_heal as LH  # noqa: E402

REQUIRED_CHECKS = ("install + verify (ubuntu-latest)", "install + verify (macos-latest)",
                   "browser e2e (ubuntu)")          # the Windows job is informational by contract
CONSTITUTION = "docs/THEOREM_GOVERNANCE.md"
RESERVED_PREFIXES = (CONSTITUTION, "docs/REGISTRATION_")
# The gate may not merge changes to itself or to the checks it relies on
# (self-approval); such changes go to the owner.
GATE_MACHINERY_PREFIXES = ("tools/check.sh", "tools/lab_loop.sh", ".github/workflows/", "src/outcome_",
                           "src/artifact_registry.py", "src/lab_", "src/lint_", "src/verify_",
                           "src/design_verifier.py")
LEDGER_GLOB_PREFIX = "results/"
KB_GRADE_RE = re.compile(r"\bG[3-9]\b")
OWNER_MARK = "OWNER-RESERVED"
HEAL_ATTEMPT_CAP = LH.HEAL_ATTEMPT_CAP
HEALER_FAMILY = "anthropic"                        # lab_heal dispatches `claude`
ISSUE_LABEL = "owner-decision"
VERIFIER_TIMEOUT = 900
DIFF_MAX = 60000

# Read-only verifier presets. The brief is passed as the last argument (and on
# stdin); the verifier must not edit, commit or reach the network on our behalf.
VERIFIER_PRESETS = {
    "pi": {"family": "openweights", "model": "minimax",
           "cmd": "pi -p --no-session --no-tools --no-extensions --no-skills --no-prompt-templates "
                  "--no-context-files --provider litellm --model {model}"},
    "codex": {"family": "openai", "model": "gpt-6-astra",
              "cmd": "codex exec --sandbox read-only --skip-git-repo-check -m {model}"},
}
DEFAULT_VERIFIER = "pi"


def sh(argv, cwd, timeout=600, stdin=None, env=None):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, input=stdin, env=env)
    return p.returncode, p.stdout, p.stderr


# --------------------------------------------------------------- github ----

class GitHub:
    """Thin `gh`/`git` adapter; tests replace it with a fake exposing the same methods."""

    def __init__(self, root):
        self.root = root

    def _gh(self, *args, timeout=120):
        rc, out, err = sh(["gh", *args], self.root, timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"gh {' '.join(args[:3])}: {err.strip()[-300:]}")
        return out

    def pr_view(self, number):
        out = self._gh("pr", "view", str(number), "--json",
                       "number,url,headRefName,headRefOid,baseRefName,title,state,mergeCommit")
        return json.loads(out)

    def checks(self, number):
        rc, out, err = sh(["gh", "pr", "checks", str(number), "--json", "name,bucket,state"], self.root, timeout=120)
        return json.loads(out) if out.strip() else []      # gh exits 1 on a failing check; the JSON is still there

    def diff(self, base, branch):
        r = self.root
        sh(["git", "fetch", "-q", "origin", f"+refs/heads/{base}:refs/remotes/origin/{base}",
            f"+refs/heads/{branch}:refs/remotes/origin/{branch}"], r, timeout=300)
        rng = f"origin/{base}...origin/{branch}"
        rc, numstat, _ = sh(["git", "diff", "--numstat", rng], r)
        paths = [l.split("\t")[2] for l in numstat.splitlines() if l.count("\t") >= 2]
        rc, deleted, _ = sh(["git", "diff", "--diff-filter=D", "--name-only", rng], r)
        ledger_paths = [p for p in paths if p.startswith(LEDGER_GLOB_PREFIX) and p.endswith(".jsonl")]
        ledger_deletions = {}
        for p in ledger_paths:
            rc, d, _ = sh(["git", "diff", "-U0", rng, "--", p], r)
            n = sum(1 for l in d.splitlines() if l.startswith("-") and not l.startswith("---"))
            if n:
                ledger_deletions[p] = n
        kb = [p for p in paths if p.startswith("docs/kb/")]
        kb_added = []
        for p in kb:
            rc, d, _ = sh(["git", "diff", "-U0", rng, "--", p], r)
            kb_added += [l[1:] for l in d.splitlines() if l.startswith("+") and not l.startswith("+++")]
        rc, text, _ = sh(["git", "diff", rng, "--", ".", ":(exclude)*.jsonl"], r)
        return {"paths": paths, "deleted": deleted.split(), "ledger_deletions": ledger_deletions,
                "kb_added_lines": kb_added, "text": text[:DIFF_MAX]}

    def head_available(self, sha):
        rc, out, err = sh(["git", "cat-file", "-e", f"{sha}^{{commit}}"], self.root)
        return rc == 0

    def merge(self, number, subject):
        self._gh("pr", "merge", str(number), "--merge", "--subject", subject, "--delete-branch", timeout=300)
        return (self.pr_view(number).get("mergeCommit") or {}).get("oid")

    def close(self, number, comment):
        self._gh("pr", "close", str(number), "--comment", comment, timeout=120)

    def comment(self, number, body):
        self._gh("pr", "comment", str(number), "--body", body, timeout=120)

    def find_issue(self, title):
        out = self._gh("issue", "list", "--state", "all", "--search", f'"{title}" in:title', "--json", "url,title",
                       "--limit", "20")
        for it in json.loads(out or "[]"):
            if it.get("title") == title:
                return it["url"]
        return None

    def create_issue(self, title, body):
        rc, _, _ = sh(["gh", "label", "create", ISSUE_LABEL, "--force", "--color", "B60205",
                       "--description", "Owner-reserved decision routed by the R3 gate (constraint 6)"],
                      self.root, timeout=120)
        return self._gh("issue", "create", "--title", title, "--body", body, "--label", ISSUE_LABEL,
                        timeout=120).strip()


# --------------------------------------------------------------- checks ----

def check_ci(checks):
    seen = {c.get("name"): (c.get("bucket") or c.get("state", "")).lower() for c in checks}
    required = {n: seen.get(n) for n in REQUIRED_CHECKS}
    return {"ok": all(v == "pass" for v in required.values()), "required": required}


def reserved_reasons(diff, notes, attempts):
    why = []
    for p in diff["paths"]:
        if p.startswith(RESERVED_PREFIXES):
            why.append(f"owner-reserved path changed: {p}")
        elif p.startswith(GATE_MACHINERY_PREFIXES):
            why.append(f"gate machinery changed (the gate may not approve changes to itself): {p}")
    if any(KB_GRADE_RE.search(l) for l in diff.get("kb_added_lines", [])):
        why.append("a G3+ evidence grade line was added under docs/kb/ (promotion is owner-reserved)")
    if OWNER_MARK in (notes or ""):
        why.append(f"the repair agent flagged {OWNER_MARK} in its notes")
    if attempts >= HEAL_ATTEMPT_CAP:
        why.append(f"heal attempt cap reached ({attempts} >= {HEAL_ATTEMPT_CAP}); the loop cannot fix this alone")
    return why


def scope_reasons(diff):
    why = [f"ledger file lost {n} line(s) (append-only): {p}" for p, n in diff.get("ledger_deletions", {}).items()]
    why += [f"test file deleted: {p}" for p in diff.get("deleted", [])
            if p.startswith("tests/") or os.path.basename(p).startswith("test_")]
    return why


def run_defect_check(root, head_sha, defect):
    """(ok, summary): the defect's own check in a fresh detached worktree at the PR head."""
    check = OA.check_command(defect)
    if not check:
        return True, "no per-defect check for this source"
    path = tempfile.mkdtemp(prefix="lab-gate-")
    os.rmdir(path)
    rc, out, err = sh(["git", "worktree", "add", "--quiet", "--detach", path, head_sha], root, timeout=300)
    if rc != 0:
        return False, f"worktree add failed: {err.strip()[-200:]}"
    try:
        rc, out, err = sh(check, path, timeout=900)
        tail = "\n".join((out + err).strip().splitlines()[-3:])
        return rc == 0, f"exit {rc}: {tail}"
    finally:
        sh(["git", "worktree", "remove", "--force", path], root)
        sh(["git", "worktree", "prune"], root)


# ------------------------------------------------------------- verifier ----

def verifier_spec(preset=None):
    name = preset or os.environ.get("LAB_VERIFIER") or DEFAULT_VERIFIER
    p = dict(VERIFIER_PRESETS[name])
    p["model"] = os.environ.get("LAB_VERIFY_MODEL") or p["model"]
    p["cmd"] = os.environ.get("LAB_VERIFY_CMD") or p["cmd"]
    p["family"] = os.environ.get("LAB_VERIFY_FAMILY") or p["family"]
    p["name"] = name
    return p


def verify_brief(defect, attr, notes, diff, checks):
    return "\n".join([
        "# Independent verification brief (R3 gate, constitution A0 / control C7)",
        "",
        "You are a READ-ONLY verifier of a different model family than the agent that wrote this",
        "repair. Decide whether the change below should be merged. Do not edit anything.",
        "",
        "## The defect (outcome-ledger row)",
        "```json", json.dumps({k: defect[k] for k in ("source", "artifact", "artifact_class", "signal",
                                                      "evidence", "detail", "commit")}, indent=1), "```",
        "## Attribution (R1)", "```json", json.dumps(attr["detail"] if attr else None, indent=1), "```",
        "## The repair agent's notes", notes or "(none)",
        "## Mechanical checks already passed", "```json", json.dumps(checks, indent=1), "```",
        "## Diff", "```diff", diff.get("text", ""), "```",
        "## Answer",
        "AGREE only if ALL hold: the change fixes the root cause the attribution and notes describe (not a",
        "symptom); it does not weaken, skip or delete any test, verifier or check; it does not rewrite frozen",
        "results, registrations or existing ledger rows; it is the smallest reasonable change; it preserves",
        "constitution articles A1-A8 (calibrated null, null-trial admission, class accounting, asymmetric",
        "verdicts, stationarity gate, designated arbiter, one-way flow, deterministic certificate).",
        "Otherwise DISAGREE. End your reply with exactly one JSON object on its own line:",
        '{"verdict": "AGREE" | "DISAGREE", "reasons": ["..."]}',
    ]) + "\n"


VERDICT_RE = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}", re.S)


def parse_verdict(text):
    last = None
    for m in VERDICT_RE.finditer(text or ""):
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if str(obj.get("verdict", "")).upper() in ("AGREE", "DISAGREE"):
            last = {"verdict": obj["verdict"].upper(),
                    "reasons": [str(r) for r in (obj.get("reasons") or [])][:10]}
    return last


def run_verifier(brief, cwd, spec):
    argv = shlex.split(spec["cmd"].format(model=spec["model"]), posix=(os.name != "nt")) + [brief]
    try:
        rc, out, err = sh(argv, cwd, timeout=VERIFIER_TIMEOUT, stdin=brief, env=LH.agent_env())
    except subprocess.TimeoutExpired:
        return {"family": spec["family"], "model": spec["model"], "verdict": None, "raw": "timed out"}
    except OSError as e:
        return {"family": spec["family"], "model": spec["model"], "verdict": None, "raw": f"failed to start: {e}"}
    v = parse_verdict(out) if rc == 0 else None
    return {"family": spec["family"], "model": spec["model"], "verdict": v["verdict"] if v else None,
            "reasons": v["reasons"] if v else [], "raw": LH.redact((out + err).strip()[-800:]), "exit": rc}


# ---------------------------------------------------------------- gate ----

def pr_number(url):
    m = re.search(r"/pull/(\d+)", url or "")
    return int(m.group(1)) if m else None


def gated_triples(rows):
    return {(r["detail"].get("defect_key"), r["detail"].get("defect_commit"), r["detail"].get("branch"))
            for r in rows if r["source"] == "gate"}


def pending_proposals(rows):
    done = gated_triples(rows)
    return [r for r in rows if r["source"] == "heal" and r["signal"] == "PROPOSED" and r["detail"].get("pr")
            and (r["detail"].get("defect_key"), r["detail"].get("defect_commit"), r["detail"].get("branch")) not in done]


def heal_attempts(rows, defect_key, defect_commit):
    return sum(1 for r in rows if r["source"] == "heal"
               and r["detail"].get("defect_key") == defect_key and r["detail"].get("defect_commit") == defect_commit)


def find_defect(rows, defect_key, defect_commit):
    for r in reversed(rows):
        if r["severity"] == "defect" and "|".join(OL.state_key(r)) == defect_key and r["commit"] == defect_commit:
            return r
    return None


def find_attribution(rows, defect_key, defect_commit):
    return next((r for r in reversed(rows) if r["source"] == "attribution"
                 and r["detail"].get("defect_key") == defect_key
                 and r["detail"].get("defect_commit") == defect_commit), None)


def issue_title(defect, defect_commit):
    return f"owner-decision: {defect['artifact']} {defect['signal']} [{defect['detail'].get('subject', '')}] @{defect_commit}"


def issue_body(defect, attr, proposal, reasons, checks):
    return "\n".join([
        "Routed by `src/lab_gate.py` (R3, constitution A0, constraint 6): this decision is owner-reserved,",
        "so the loop stops here with the evidence attached. Nothing was merged.",
        "", "## Why", *[f"- {r}" for r in reasons],
        "", "## Defect", "```json", json.dumps(defect, indent=1), "```",
        "## Attribution", "```json", json.dumps(attr["detail"] if attr else None, indent=1), "```",
        "## Proposal", f"PR: {proposal['detail'].get('pr') or '(none)'}  branch: `{proposal['detail'].get('branch')}`",
        "", "### Agent notes", proposal["detail"].get("notes") or "(none)",
        "", "## Gate checks", "```json", json.dumps(checks, indent=1), "```",
    ])


class Gate:
    def __init__(self, root=ROOT, gh=None, verifier=None, defect_check=None, verifier_preset=None,
                 dry_run=False, out=sys.stdout):
        self.root = root
        self.gh = gh or GitHub(root)
        self.spec = verifier_spec(verifier_preset)
        self.verifier = verifier or (lambda brief, cwd: run_verifier(brief, cwd, self.spec))
        self.defect_check = defect_check or (lambda head, defect: run_defect_check(root, head, defect))
        self.dry_run = dry_run
        self.out = out

    def decide(self, proposal, rows):
        d = proposal["detail"]
        key, dcommit, branch = d.get("defect_key"), d.get("defect_commit"), d.get("branch")
        defect = find_defect(rows, key, dcommit) or {"artifact": proposal["artifact"], "signal": "FAIL",
                                                     "artifact_class": proposal["artifact_class"],
                                                     "source": "unknown", "evidence": "", "detail": {}, "commit": dcommit}
        attr = find_attribution(rows, key, dcommit)
        num = pr_number(d.get("pr"))
        pr = self.gh.pr_view(num)
        base_detail = {"subject": d.get("subject", ""), "defect_key": key, "defect_commit": dcommit, "branch": branch,
                       "pr": d.get("pr"), "pr_number": num, "head": pr.get("headRefOid"), "base": pr.get("baseRefName")}
        checks, reasons = {}, []
        if pr.get("state") == "MERGED":          # a human merged it: record the fact, stop treating it as pending
            sha = (pr.get("mergeCommit") or {}).get("oid")
            return self._row(proposal, "MERGED", f"MERGED PR #{num} outside the gate (human action) -> {(sha or '?')[:7]}",
                             base_detail, checks, ["merged outside the gate: a decision waited for a human (constraint 6)"],
                             merge_commit=sha)
        if pr.get("state") != "OPEN":
            return self._row(proposal, "REJECTED", f"PR #{num} is {pr.get('state')} (closed outside the gate)",
                             base_detail, checks, [f"pr state {pr.get('state')}"])
        diff = self.gh.diff(pr["baseRefName"], pr["headRefName"])
        attempts = heal_attempts(rows, key, dcommit)
        checks["scope"] = {"paths": diff["paths"][:50], "deleted": diff.get("deleted", []),
                           "ledger_deletions": diff.get("ledger_deletions", {})}
        routed = reserved_reasons(diff, d.get("notes"), attempts)
        if routed:
            return self._route(proposal, defect, attr, base_detail, checks, routed)
        reasons += scope_reasons(diff)
        checks["ci"] = check_ci(self.gh.checks(num))
        if not checks["ci"]["ok"]:
            reasons.append("required CI checks not all green: " + json.dumps(checks["ci"]["required"]))
        if not reasons:
            ok, summary = self.defect_check(pr["headRefOid"], defect)
            checks["defect_check"] = {"ok": ok, "summary": LH.redact(summary)[:400]}
            if not ok:
                reasons.append("the defect's own check still fails at the PR head")
        if reasons:
            return self._reject(proposal, num, base_detail, checks, reasons)
        v = self.verifier(verify_brief(defect, attr, d.get("notes"), diff, checks), self.root)
        checks["verifier"] = {k: v.get(k) for k in ("family", "model", "verdict", "reasons", "raw", "exit")}
        if v.get("family") == HEALER_FAMILY:
            reasons.append(f"verifier family {v.get('family')!r} equals the healer's (C7: a different family is required)")
        elif v.get("verdict") != "AGREE":
            reasons.append(f"independent verifier ({v.get('family')}/{v.get('model')}) did not agree: "
                           f"{v.get('verdict') or 'no verdict'} " + "; ".join(v.get("reasons") or [])[:300])
        if reasons:
            return self._reject(proposal, num, base_detail, checks, reasons)
        subject = f"Merge PR #{num}: {pr['title']}"
        merge_sha = None if self.dry_run else self.gh.merge(num, subject)
        ev = (f"MERGED PR #{num} -> {(merge_sha or 'dry-run')[:7]}; ci ok, check ok, scope ok, "
              f"verifier AGREE ({v.get('family')}/{v.get('model')})")
        return self._row(proposal, "MERGED", ev, base_detail, checks, [], merge_commit=merge_sha)

    def _reject(self, proposal, num, base_detail, checks, reasons):
        body = "R3 gate REJECTED this proposal (no human action):\n" + "\n".join(f"- {r}" for r in reasons)
        if not self.dry_run:
            self.gh.close(num, LH.redact(body))
        return self._row(proposal, "REJECTED", f"REJECTED PR #{num}: " + "; ".join(reasons), base_detail, checks, reasons)

    def _route(self, proposal, defect, attr, base_detail, checks, reasons):
        title = issue_title(defect, base_detail["defect_commit"])
        url = None
        if not self.dry_run:
            url = self.gh.find_issue(title) or self.gh.create_issue(
                title, LH.redact(issue_body(defect, attr, proposal, reasons, checks)))
            if base_detail.get("pr_number"):
                self.gh.comment(base_detail["pr_number"], f"R3 gate: owner-reserved decision, routed to {url}. "
                                                          "Left open for the owner; not merged.")
        return self._row(proposal, "ROUTED", f"ROUTED to owner {url or '(dry-run)'}: " + "; ".join(reasons),
                         base_detail, checks, reasons, issue=url)

    def _row(self, proposal, signal, evidence, base_detail, checks, reasons, merge_commit=None, issue=None):
        ctx = OC.Ctx(self.root, [])
        row = ctx.row("gate", proposal["artifact"], proposal["artifact_class"], signal,
                      LH.redact(evidence)[:OL.EVIDENCE_MAX],
                      {**base_detail, "checks": checks, "reasons": reasons, "merge_commit": merge_commit, "issue": issue})
        print(row["evidence"], file=self.out)
        return row

    def route_exhausted(self, rows):
        """Open occurrences that used every heal attempt without a proposal
        reaching the gate: route them so no defect waits in silence."""
        out = []
        done = gated_triples(rows)
        for defect in OA.open_defects(rows):
            key = "|".join(OL.state_key(defect))
            n = heal_attempts(rows, key, defect["commit"])
            if n < HEAL_ATTEMPT_CAP or (key, defect["commit"], None) in done:
                continue
            if any(r["source"] == "gate" and r["signal"] == "ROUTED" and r["detail"].get("defect_key") == key
                   and r["detail"].get("defect_commit") == defect["commit"] for r in rows):
                continue
            pseudo = {"artifact": defect["artifact"], "artifact_class": defect["artifact_class"],
                      "detail": {"subject": defect["detail"].get("subject", ""), "defect_key": key,
                                 "defect_commit": defect["commit"], "branch": None, "pr": None, "notes": ""}}
            base_detail = {"subject": defect["detail"].get("subject", ""), "defect_key": key,
                           "defect_commit": defect["commit"], "branch": None, "pr": None, "pr_number": None,
                           "head": None, "base": None}
            attr = find_attribution(rows, key, defect["commit"])
            out.append(self._route(pseudo, defect, attr, base_detail, {"heal_attempts": n},
                                   [f"heal attempt cap reached ({n} >= {HEAL_ATTEMPT_CAP}) with no mergeable proposal"]))
        return out


def run(ledger, root=ROOT, pr=None, **kw):
    rows = OL.read_rows(ledger)
    gate = Gate(root=root, **kw)
    todo = pending_proposals(rows)
    if pr is not None:
        todo = [r for r in todo if pr_number(r["detail"].get("pr")) == pr]
        if not todo:
            print(f"gate: PR #{pr} is not a pending heal proposal", file=gate.out)
            return []
    new = []
    for p in todo:
        try:
            new.append(gate.decide(p, rows + new))
        except Exception as e:      # never lose the signal; the proposal stays pending for the next run
            print(f"gate: error on {p['detail'].get('pr')}: {type(e).__name__}: {LH.redact(str(e))}", file=gate.out)
    if pr is None:
        new += gate.route_exhausted(rows + new)
    if not new:
        print("gate: nothing pending", file=gate.out)
    if new and not gate.dry_run:
        OL.append_rows(ledger, new)
    return new


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new", action="store_true")
    g.add_argument("--pr", type=int)
    ap.add_argument("--verifier", choices=sorted(VERIFIER_PRESETS), default=None)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--dry-run", action="store_true", help="decide and print, but do not merge/close/route or append")
    a = ap.parse_args(argv)
    ledger = OL.ledger_path(a.ledger)
    if OL.verify_ledger(ledger):
        print("refusing to work from an invalid ledger")
        return 2
    rows = run(ledger, pr=a.pr, verifier_preset=a.verifier, dry_run=a.dry_run)
    return 0 if all(r["signal"] == "MERGED" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
