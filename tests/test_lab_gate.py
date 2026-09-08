#!/usr/bin/env python3
"""R3 gate: mechanical checks, independent verifier of a different model
family, owner-reserved routing, merge. GitHub, the verifier and the
per-defect check are injected fakes; no network, no LLM.

Run: python3 -m pytest tests/test_lab_gate.py -q
"""
import importlib.util
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "src", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LG = load("lab_gate")
LH = LG.LH
OL = LG.OL

PR = "https://github.com/x/y/pull/7"
BRANCH = "heal/src-inst-py-fail-1"
DEFECT_COMMIT = "abc1234"


class FakeGH:
    def __init__(self, checks=None, diff=None, state="OPEN", issue=None, base="master"):
        self.calls = []
        self._checks = checks if checks is not None else [{"name": n, "bucket": "pass"} for n in LG.REQUIRED_CHECKS]
        self._diff = diff or {"paths": ["src/inst.py", "HEAL_NOTES.md"], "deleted": [], "ledger_deletions": {},
                              "kb_added_lines": [], "text": "--- a/src/inst.py\n+++ b/src/inst.py\n-bad\n+good\n"}
        self.state, self.issue, self.base = state, issue, base

    def pr_view(self, n):
        return {"number": n, "url": PR, "headRefName": BRANCH, "headRefOid": "h" * 40, "baseRefName": self.base,
                "title": "heal: src/inst.py FAIL (linux)", "state": self.state,
                "mergeCommit": {"oid": "e" * 40} if self.state == "MERGED" else None}

    def checks(self, n):
        return self._checks

    def diff(self, base, branch):
        return self._diff

    def merge(self, n, subject, head):
        assert head == "h" * 40                      # the verified head is pinned into the merge
        self.calls.append(("merge", n, subject))
        return "m" * 40

    def close(self, n, comment):
        self.calls.append(("close", n, comment))

    def comment(self, n, body):
        self.calls.append(("comment", n, body))

    def find_issue(self, title):
        return self.issue

    def create_issue(self, title, body):
        self.calls.append(("issue", title, body))
        return "https://github.com/x/y/issues/9"


def agree(brief, cwd):
    return {"family": "openweights", "model": "fake", "verdict": "AGREE", "reasons": [], "raw": "", "exit": 0}


def ok_check(head, defect):
    return True, "exit 0"


def defect_row(commit=DEFECT_COMMIT, ts="2026-09-06T10:00:00Z"):
    return OL.make_row("verify_entrypoint", "src/inst.py", "instrument", "FAIL", "FAIL src/inst.py",
                       {"subject": "linux", "exit": 1, "sha256": None, "args": ["--verify"]}, ts, commit, "tester")


def heal_row(defect, signal="PROPOSED", branch=BRANCH, pr=PR, notes="root cause: x", ts="2026-09-06T10:20:00Z"):
    key = "|".join(OL.state_key(defect))
    return OL.make_row("heal", "src/inst.py", "instrument", signal, f"{signal} {pr or branch}",
                       {"subject": "linux", "defect_key": key, "defect_commit": defect["commit"], "branch": branch,
                        "stage": "proposed" if signal == "PROPOSED" else "gate", "pr": pr, "notes": notes},
                       ts, defect["commit"], "tester")


def ledger_with(tmp_path, rows):
    path = str(tmp_path / "l.jsonl")
    OL.append_rows(path, rows)
    return path


def run(ledger, gh, verifier=agree, check=ok_check, **kw):
    return LG.run(ledger, root=REPO, gh=gh, verifier=verifier, defect_check=check, out=open(os.devnull, "w"), **kw)


# ---------------------------------------------------------------- merge ----

def test_gate_merges_when_all_green(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH()
    rows = run(ledger, gh)
    assert len(rows) == 1 and rows[0]["signal"] == "MERGED" and rows[0]["source"] == "gate"
    det = rows[0]["detail"]
    assert det["merge_commit"] == "m" * 40 and det["pr_number"] == 7 and det["branch"] == BRANCH
    assert det["checks"]["ci"]["ok"] and det["checks"]["defect_check"]["ok"]
    assert det["checks"]["verifier"]["verdict"] == "AGREE" and det["checks"]["verifier"]["family"] == "openweights"
    assert gh.calls == [("merge", 7, "Merge PR #7: heal: src/inst.py FAIL (linux)")]
    assert OL.verify_ledger(ledger) == []
    assert run(ledger, gh) == []                         # decided once; nothing pending


def test_gate_evaluates_pending_proposals_once_and_ignores_unpushed(tmp_path):
    d = defect_row()
    local_only = heal_row(d, pr=None, branch="heal/local")
    ledger = ledger_with(tmp_path, [d, local_only])
    assert run(ledger, FakeGH()) == []                   # no PR -> nothing for the gate
    assert LG.pending_proposals(OL.read_rows(ledger)) == []


def test_gate_records_human_merge_and_outside_close(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    rows = run(ledger, FakeGH(state="MERGED"))
    assert rows[0]["signal"] == "MERGED" and rows[0]["detail"]["merge_commit"] == "e" * 40
    assert "human" in rows[0]["evidence"]
    d2 = defect_row(commit="bbb2222", ts="2026-09-06T12:00:00Z")
    ledger = ledger_with(tmp_path / "2", [d2, heal_row(d2, branch="heal/b", pr="https://github.com/x/y/pull/8",
                                                       ts="2026-09-06T12:20:00Z")])
    rows = run(ledger, FakeGH(state="CLOSED"))
    assert rows[0]["signal"] == "REJECTED" and "closed outside" in rows[0]["evidence"]


# --------------------------------------------------------------- reject ----

def test_gate_rejects_red_ci_without_calling_verifier(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    checks = [{"name": n, "bucket": "pass"} for n in LG.REQUIRED_CHECKS]
    checks[0] = {"name": LG.REQUIRED_CHECKS[0], "bucket": "fail"}
    checks.append({"name": "install + verify (windows, informational)", "bucket": "fail"})
    gh = FakeGH(checks=checks)
    called = []
    rows = run(ledger, gh, verifier=lambda b, c: called.append(1) or agree(b, c))
    assert rows[0]["signal"] == "REJECTED" and not called
    assert rows[0]["detail"]["checks"]["ci"]["required"][LG.REQUIRED_CHECKS[0]] == "fail"
    assert gh.calls[0][0] == "close" and "not all green" in gh.calls[0][2]
    # windows informational alone never blocks
    ok = [{"name": n, "bucket": "pass"} for n in LG.REQUIRED_CHECKS] + [{"name": "install + verify (windows, informational)", "bucket": "fail"}]
    assert LG.check_ci(ok)["ok"]
    assert not LG.check_ci([{"name": LG.REQUIRED_CHECKS[0], "bucket": "pending"}])["ok"]   # missing/pending = not green


def test_gate_rejects_failed_defect_check(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH()
    rows = run(ledger, gh, check=lambda head, defect: (False, "exit 1: still broken"))
    assert rows[0]["signal"] == "REJECTED" and "still fails" in rows[0]["evidence"]
    assert rows[0]["detail"]["checks"]["defect_check"]["summary"].startswith("exit 1")
    assert gh.calls[0][0] == "close"


def test_gate_rejects_ledger_rewrites_and_deleted_tests(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    diff = {"paths": ["src/inst.py", "results/outcome_ledger.jsonl"], "deleted": [],
            "ledger_deletions": {"results/outcome_ledger.jsonl": 2}, "kb_added_lines": [], "text": ""}
    rows = run(ledger, FakeGH(diff=diff))
    assert rows[0]["signal"] == "REJECTED" and "append-only" in rows[0]["evidence"]
    diff = {"paths": ["src/inst.py", "tests/test_inst.py"], "deleted": ["tests/test_inst.py"],
            "ledger_deletions": {}, "kb_added_lines": [], "text": ""}
    d2 = defect_row(commit="ccc3333", ts="2026-09-06T12:00:00Z")
    ledger = ledger_with(tmp_path / "2", [d2, heal_row(d2, ts="2026-09-06T12:20:00Z")])
    rows = run(ledger, FakeGH(diff=diff))
    assert rows[0]["signal"] == "REJECTED" and "test file deleted" in rows[0]["evidence"]


def test_gate_rejects_retargeted_base_missing_defect_row_and_oversized_diff(tmp_path):
    d = defect_row()
    # base retargeted away from what the proposal recorded
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH(base="develop")
    rows = run(ledger, gh)
    assert rows[0]["signal"] == "REJECTED" and "PR base 'develop'" in rows[0]["evidence"] and gh.calls[0][0] == "close"
    # a proposal recording its own base is judged against that base
    d2 = defect_row(commit="bbb2222", ts="2026-09-06T12:00:00Z")
    h2 = heal_row(d2, ts="2026-09-06T12:20:00Z")
    h2["detail"]["base"] = "develop"
    ledger = ledger_with(tmp_path / "2", [d2, h2])
    assert run(ledger, FakeGH(base="develop"))[0]["signal"] == "MERGED"
    # heal row whose defect occurrence is not in the ledger: fail closed
    d3 = defect_row(commit="ccc3333", ts="2026-09-06T13:00:00Z")
    h3 = heal_row(d3, ts="2026-09-06T13:20:00Z")
    h3["detail"]["defect_commit"] = "zzz9999"
    ledger = ledger_with(tmp_path / "3", [d3, h3])
    rows = run(ledger, FakeGH())
    assert rows[0]["signal"] == "REJECTED" and "defect row not found" in rows[0]["evidence"]
    # diff the verifier could not see in full
    d4 = defect_row(commit="ddd4444", ts="2026-09-06T14:00:00Z")
    ledger = ledger_with(tmp_path / "4", [d4, heal_row(d4, ts="2026-09-06T14:20:00Z")])
    big = {"paths": ["src/inst.py"], "deleted": [], "ledger_deletions": {}, "kb_added_lines": [],
           "text": "x" * LG.DIFF_MAX, "truncated": True, "text_chars": LG.DIFF_MAX + 5}
    rows = run(ledger, FakeGH(diff=big))
    assert rows[0]["signal"] == "REJECTED" and "too large" in rows[0]["evidence"]


def test_family_is_derived_from_the_verifier_binary(monkeypatch):
    assert LG.family_of("claude -p --model sonnet") == "anthropic"
    assert LG.family_of("codex exec --sandbox read-only -m gpt-6-astra") == "openai"
    assert LG.family_of("pi -p --provider litellm --model minimax") == "openweights"
    assert LG.family_of("pi -p --model anthropic/claude-sonnet-5") == "anthropic"
    assert LG.family_of("gemini -p") == "google"
    assert LG.family_of("/opt/tools/my-verifier --x") is None
    monkeypatch.setenv("LAB_VERIFY_CMD", "claude -p --model sonnet")
    monkeypatch.setenv("LAB_VERIFY_FAMILY", "openweights")          # a label cannot launder the healer's family
    assert LG.verifier_spec("pi")["family"] == "anthropic"
    monkeypatch.setenv("LAB_VERIFY_CMD", "/opt/tools/my-verifier --x")
    monkeypatch.delenv("LAB_VERIFY_FAMILY")
    assert LG.verifier_spec("pi")["family"] == "unknown"


def test_gate_rejects_unknown_family_verifier(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    unknown = lambda b, c: {"family": "unknown", "model": "x", "verdict": "AGREE", "reasons": []}
    rows = run(ledger, FakeGH(), verifier=unknown)
    assert rows[0]["signal"] == "REJECTED" and "family unknown" in rows[0]["evidence"]


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def test_real_git_diff_sees_renames_ledger_rewrites_and_reserved_paths(tmp_path):
    """The real adapter against a real origin: a renamed test shows as a deletion
    (no rename detection), a rewritten ledger line is counted, and both old and
    new paths of a moved gate file reach the reserved check."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", str(origin))
    root = tmp_path / "repo"
    git(tmp_path, "clone", "-q", str(origin), str(root))
    git(root, "config", "user.email", "t@t"), git(root, "config", "user.name", "t")
    (root / "tests").mkdir(), (root / "results").mkdir(), (root / "src").mkdir(), (root / "docs").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): pass\n")
    (root / "results" / "l.jsonl").write_text('{"a":1}\n{"a":2}\n')
    (root / "results" / "frozen.json").write_text('{"v": 1}\n')
    (root / "results" / "agent_runs" / "eval-old").mkdir(parents=True)
    (root / "results" / "agent_runs" / "eval-old" / "grade.json").write_text('{"grade": "FAIL"}\n')
    (root / "src" / "lab_gate.py").write_text("gate = 1\n")
    (root / "docs" / "THEOREM_GOVERNANCE.md").write_text("A0\n")
    git(root, "checkout", "-q", "-b", "main"), git(root, "add", "-A"), git(root, "commit", "-qm", "base")
    git(root, "push", "-q", "-u", "origin", "main")
    git(root, "checkout", "-q", "-b", "heal/x")
    git(root, "mv", "tests/test_x.py", "tests/test_x.py.bak")
    git(root, "mv", "src/lab_gate.py", "src/lab_gate2.py")
    (root / "results" / "l.jsonl").write_text('{"a":1}\n{"a":3}\n')          # rewrote a line
    (root / "results" / "frozen.json").write_text('{"v": 2}\n')                # rewrote a frozen result
    (root / "results" / "agent_runs" / "eval-old" / "grade.json").write_text('{"grade": "PASS"}\n')  # rewrote history
    (root / "results" / "new_version.json").write_text('{"v": 2}\n')           # a NEW file is fine
    (root / "docs" / "THEOREM_GOVERNANCE.md").write_text("A0 changed\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "bad heal"), git(root, "push", "-q", "-u", "origin", "heal/x")
    diff = LG.GitHub(str(root)).diff("main", "heal/x")
    assert "tests/test_x.py" in diff["deleted"] and "src/lab_gate.py" in diff["deleted"]
    assert diff["ledger_deletions"] == {"results/l.jsonl": 1}
    assert sorted(diff["results_modified"]) == ["results/agent_runs/eval-old/grade.json", "results/frozen.json"]
    assert diff["truncated"] is False and diff["text_chars"] > 0
    reasons = LG.scope_reasons(diff)
    assert any("test file deleted: tests/test_x.py" in r for r in reasons)
    assert any("frozen result or historical record rewritten: results/frozen.json" in r for r in reasons)
    assert any("eval-old/grade.json" in r for r in reasons) and not any("new_version" in r for r in reasons)
    routed = LG.reserved_reasons(diff, "", 0)
    assert any("docs/THEOREM_GOVERNANCE.md" in r for r in routed)
    assert any("src/lab_gate.py" in r for r in routed) and any("src/lab_gate2.py" in r for r in routed)


def test_gate_rejects_rewritten_frozen_result_without_calling_verifier(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH(diff={"paths": ["src/inst.py", "results/frozen.json"], "deleted": [], "ledger_deletions": {},
                      "results_modified": ["results/frozen.json"], "kb_added_lines": [], "text": "x"})
    called = []
    rows = run(ledger, gh, verifier=lambda b, c: called.append(1) or {"family": "openai", "model": "x",
                                                                       "verdict": "AGREE", "reasons": []})
    assert rows[0]["signal"] == "REJECTED" and "frozen result or historical record rewritten" in rows[0]["evidence"]
    assert called == [] and all(c[0] != "merge" for c in gh.calls)


def test_gate_scope_exempts_declared_outputs_only(tmp_path, monkeypatch):
    """R4 full REQ-3: the gate applies the healer's exemption and no other."""
    monkeypatch.setattr(LG.OC, "REPLAY_TARGETS", [("src/inst.py", [], ["results/panel.json"])])
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH(diff={"paths": ["results/panel.json"], "deleted": [], "ledger_deletions": {},
                      "results_modified": ["results/panel.json"], "kb_added_lines": [], "text": "x"})
    rows = run(ledger, gh)
    assert rows[0]["signal"] == "MERGED" and rows[0]["detail"]["checks"]["scope"]["regenerable"] == ["results/panel.json"]
    d2 = defect_row(commit="bbb2222", ts="2026-09-06T12:00:00Z")
    ledger = ledger_with(tmp_path / "2", [d2, heal_row(d2, ts="2026-09-06T12:20:00Z")])
    gh = FakeGH(diff={"paths": ["results/panel.json", "results/frozen.json"], "deleted": [], "ledger_deletions": {},
                      "results_modified": ["results/panel.json", "results/frozen.json"], "kb_added_lines": [], "text": "x"})
    rows = run(ledger, gh)
    assert rows[0]["signal"] == "REJECTED" and "results/frozen.json" in rows[0]["evidence"] and "panel.json" not in rows[0]["evidence"]
    assert LG.scope_reasons({"results_modified": ["results/panel.json"], "deleted": ["results/panel.json"]},
                            ["results/panel.json"])                                   # deleted = rewritten
    assert LG.scope_reasons({"results_modified": ["results/panel.json"]}, ["results/panel.json"]) == []


def test_gate_rejects_same_family_verifier(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH()
    same = lambda b, c: {"family": LG.HEALER_FAMILY, "model": "sonnet", "verdict": "AGREE", "reasons": []}
    rows = run(ledger, gh, verifier=same)
    assert rows[0]["signal"] == "REJECTED" and "C7" in rows[0]["evidence"]
    assert all(c[0] != "merge" for c in gh.calls)


def test_gate_rejects_when_verifier_disagrees_or_is_silent(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH()
    dis = lambda b, c: {"family": "openai", "model": "x", "verdict": "DISAGREE", "reasons": ["weakens a check"]}
    rows = run(ledger, gh, verifier=dis)
    assert rows[0]["signal"] == "REJECTED" and "weakens a check" in rows[0]["evidence"]
    d2 = defect_row(commit="ddd4444", ts="2026-09-06T12:00:00Z")
    ledger = ledger_with(tmp_path / "2", [d2, heal_row(d2, ts="2026-09-06T12:20:00Z")])
    silent = lambda b, c: {"family": "openai", "model": "x", "verdict": None, "reasons": [], "raw": "timed out"}
    rows = run(ledger, FakeGH(), verifier=silent)
    assert rows[0]["signal"] == "REJECTED" and "no verdict" in rows[0]["evidence"]


# ---------------------------------------------------------------- route ----

@pytest.mark.parametrize("diff_patch,notes,needle", [
    ({"paths": ["docs/THEOREM_GOVERNANCE.md", "src/inst.py"]}, "", "owner-reserved path"),
    ({"paths": ["docs/REGISTRATION_BATCH9.md"]}, "", "owner-reserved path"),
    ({"paths": ["tools/check.sh", "src/inst.py"]}, "", "gate machinery"),
    ({"paths": ["src/lab_gate.py"]}, "", "gate machinery"),
    ({"paths": ["docs/kb/x.md"], "kb_added_lines": ["grade: G3 (confirmed)"]}, "", "G3+"),
    ({"paths": ["src/inst.py"]}, "root cause needs A0 change: OWNER-RESERVED", "OWNER-RESERVED"),
])
def test_gate_routes_owner_reserved_changes(tmp_path, diff_patch, notes, needle):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d, notes=notes)])
    diff = {"paths": ["src/inst.py"], "deleted": [], "ledger_deletions": {}, "kb_added_lines": [], "text": "", **diff_patch}
    gh = FakeGH(diff=diff)
    called = []
    rows = run(ledger, gh, verifier=lambda b, c: called.append(1) or agree(b, c))
    assert rows[0]["signal"] == "ROUTED" and needle in rows[0]["evidence"] and not called
    kinds = [c[0] for c in gh.calls]
    assert "issue" in kinds and "comment" in kinds and "merge" not in kinds and "close" not in kinds
    title = next(c[1] for c in gh.calls if c[0] == "issue")
    assert title == f"owner-decision: src/inst.py FAIL [linux] @{DEFECT_COMMIT}"
    assert rows[0]["detail"]["issue"] == "https://github.com/x/y/issues/9"
    assert run(ledger, gh) == []                         # decided; not re-routed


def test_gate_reuses_existing_issue(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH(diff={"paths": ["docs/THEOREM_GOVERNANCE.md"], "deleted": [], "ledger_deletions": {},
                      "kb_added_lines": [], "text": ""}, issue="https://github.com/x/y/issues/3")
    rows = run(ledger, gh)
    assert rows[0]["detail"]["issue"] == "https://github.com/x/y/issues/3"
    assert all(c[0] != "issue" for c in gh.calls)


def test_gate_routes_at_attempt_cap(tmp_path):
    d = defect_row()
    rejected = [heal_row(d, "REJECTED", branch=f"heal/try{i}", pr=None, ts=f"2026-09-06T1{i}:00:00Z")
                for i in range(LG.HEAL_ATTEMPT_CAP)]
    ledger = ledger_with(tmp_path, [d, *rejected])
    gh = FakeGH()
    rows = run(ledger, gh)
    assert len(rows) == 1 and rows[0]["signal"] == "ROUTED" and "attempt cap" in rows[0]["evidence"]
    assert rows[0]["detail"]["pr"] is None and [c[0] for c in gh.calls] == ["issue"]
    assert run(ledger, gh) == []                         # idempotent
    # below the cap nothing is routed
    ledger2 = ledger_with(tmp_path / "2", [d, *rejected[:-1]])
    assert run(ledger2, FakeGH()) == []


def test_gate_dry_run_touches_nothing(tmp_path):
    d = defect_row()
    ledger = ledger_with(tmp_path, [d, heal_row(d)])
    gh = FakeGH()
    rows = run(ledger, gh, dry_run=True)
    assert rows[0]["signal"] == "MERGED" and rows[0]["detail"]["merge_commit"] is None
    assert gh.calls == [] and len(OL.read_rows(ledger)) == 2


# ------------------------------------------------------------- verifier ----

def test_verifier_verdict_parsing():
    assert LG.parse_verdict('chatter\n{"verdict": "agree", "reasons": ["fixes root cause"]}\n') == \
        {"verdict": "AGREE", "reasons": ["fixes root cause"]}
    two = '{"verdict": "AGREE", "reasons": []} ... on reflection {"verdict": "DISAGREE", "reasons": ["x"]}'
    assert LG.parse_verdict(two)["verdict"] == "DISAGREE"      # the last one counts
    assert LG.parse_verdict("no json here") is None
    assert LG.parse_verdict('{"verdict": "MAYBE"}') is None
    # braces inside a reason (the R2 live proof's real verifier output, PR #31): a brace regex
    # could not span "(ledger_deletions: {})" and a genuine AGREE became "no verdict"
    live = ('<think>weighing the diff</think>\n{"verdict": "AGREE", "reasons": ["Frozen result untouched and no '
            'ledger rows are deleted (ledger_deletions: {}); stale HEAL_NOTES.md replaced.", "Scope {instrument} ok"]}\n')
    assert LG.parse_verdict(live) == {"verdict": "AGREE", "reasons": [
        "Frozen result untouched and no ledger rows are deleted (ledger_deletions: {}); stale HEAL_NOTES.md replaced.",
        "Scope {instrument} ok"]}
    assert LG.parse_verdict('{"nested": {"verdict": "AGREE"}} {"verdict": "DISAGREE", "reasons": ["x"]}')["verdict"] == "DISAGREE"
    assert LG.parse_verdict('```json\n{"verdict": "AGREE", "reasons": ["a {b} c"]}\n```')["verdict"] == "AGREE"


def test_verifier_presets_are_read_only_and_not_the_healer_family(monkeypatch):
    for name, p in LG.VERIFIER_PRESETS.items():
        assert p["family"] != LG.HEALER_FAMILY, name
        spec = LG.verifier_spec(name)
        cmd = spec["cmd"].format(model=spec["model"])
        assert "{" not in cmd
        if name == "pi":
            assert "--no-tools" in cmd and " -p" in cmd and "--no-session" in cmd
        if name == "codex":
            assert "--sandbox read-only" in cmd
    monkeypatch.setenv("LAB_VERIFY_CMD", "my-verifier --x")
    monkeypatch.setenv("LAB_VERIFY_FAMILY", "gemini")
    spec = LG.verifier_spec("pi")
    assert spec["cmd"] == "my-verifier --x" and spec["family"] == "gemini"


def test_verify_brief_carries_evidence_and_asks_for_json():
    d = defect_row()
    brief = LG.verify_brief(d, None, "notes here", {"text": "+fixed line"}, {"ci": {"ok": True}})
    for needle in ("READ-ONLY", "A1-A8", "+fixed line", "notes here", '"verdict"', "src/inst.py"):
        assert needle in brief


def test_run_verifier_with_fake_command(tmp_path):
    script = tmp_path / "v.py"
    script.write_text('import sys\nb = sys.stdin.read()\nassert "READ-ONLY" in b\n'
                      'print("thinking...")\nprint(\'{"verdict": "AGREE", "reasons": ["ok"]}\')\n')
    spec = {"family": "openweights", "model": "m", "cmd": f'"{sys.executable}" "{script.as_posix()}"'}
    v = LG.run_verifier(LG.verify_brief(defect_row(), None, "", {"text": ""}, {}), REPO, spec)
    assert v["verdict"] == "AGREE" and v["reasons"] == ["ok"] and v["family"] == "openweights"
    bad = {"family": "openweights", "model": "m", "cmd": "/nonexistent/verifier"}
    assert LG.run_verifier("x", REPO, bad)["verdict"] is None


# ---------------------------------------------------------------- schema ----

def test_schema_accepts_gate_rows():
    for sig in ("MERGED", "REJECTED", "ROUTED"):
        r = OL.make_row("gate", "src/inst.py", "instrument", sig, sig, {"subject": "linux"},
                        "2026-09-06T10:00:00Z", "abc1234", "tester")
        assert r["severity"] == "info"
    with pytest.raises(ValueError):
        OL.make_row("gate", "src/inst.py", "instrument", "APPROVED", "x", {}, "2026-09-06T10:00:00Z", "abc1234", "t")


# ---------------------------------------------------------------- loop ----

def test_loop_script_steps_and_lock(tmp_path):
    lock = tmp_path / "lock"
    env = dict(os.environ, LAB_LOOP_LOCK=str(lock))
    r = subprocess.run(["bash", os.path.join(REPO, "tools", "lab_loop.sh"), "--dry-run"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    steps = [l for l in r.stdout.splitlines() if l.startswith("step ")]
    names = " ".join(steps)
    for s in ("outcome_collect.py --all --gate", "agent_eval_dispatch.py --stale", "outcome_attribute.py --new",
              "lab_heal.py --new --push", "lab_gate.py --new", "lab_learn.py --derive", "ledger commit"):
        assert s in names, names
    assert names.index("outcome_collect") < names.index("agent_eval_dispatch") < names.index("outcome_attribute") \
        < names.index("lab_heal") < names.index("lab_gate") < names.index("lab_learn") < names.index("ledger commit")
    assert "results/agent_runs" in names                   # new records are committed with the rows
    assert not lock.exists()                              # released
    lock.mkdir()
    r = subprocess.run(["bash", os.path.join(REPO, "tools", "lab_loop.sh"), "--dry-run"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 3 and "already running" in r.stdout + r.stderr
    (lock / "pid").write_text("999999999\n")                # a lock left by a dead run is taken over
    r = subprocess.run(["bash", os.path.join(REPO, "tools", "lab_loop.sh"), "--dry-run"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0 and not lock.exists()
    r = subprocess.run(["bash", os.path.join(REPO, "tools", "lab_loop.sh"), "--print-cron"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0 and "lab_loop.sh" in r.stdout and r.stdout.startswith("0 */6")
