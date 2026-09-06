#!/usr/bin/env python3
"""R1-S2: attribution of ledger defects -- path history, bisection in a temp
git repo, not-reproducible-here, idempotence, and (opt-in, slow) the real-history
ground truth: the darwin July-runner FAIL was introduced by PR #20's append.

Run: python3 -m pytest tests/test_outcome_attribute.py -q
     LAB_SLOW_TESTS=1 python3 -m pytest tests/test_outcome_attribute.py -q -k real_history
"""
import importlib.util
import json
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


OA = load("outcome_attribute")
OL = OA.OL


def mkrow(source, artifact, cls, signal, commit, subject="", detail=None, ts="2026-09-06T10:00:00Z"):
    d = {"subject": subject, **(detail or {})}
    return OL.make_row(source, artifact, cls, signal, f"{signal} {artifact}", d, ts, commit, "tester")


# ----------------------------------------------------------- temp git repo --

def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def planted_repo(tmp_path):
    """A repo whose 'instrument' passes until commit 3 of 6 changes its data."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t"), git(root, "config", "user.name", "t")
    (root / "src").mkdir()
    (root / "src" / "inst.py").write_text(
        "import sys\nd=open('data.txt').read().strip()\n"
        "print('PASS sha256=' + 'a'*64 + '; wrote=none') if d=='ok' else sys.exit(1)\n")
    (root / "data.txt").write_text("ok\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "c0 create")
    shas = [git(root, "rev-parse", "HEAD")]
    for i in range(1, 6):
        (root / f"f{i}.txt").write_text(str(i))
        if i == 3:
            (root / "data.txt").write_text("broken\n")
        git(root, "add", "-A"), git(root, "commit", "-qm", f"c{i}")
        shas.append(git(root, "rev-parse", "HEAD"))
    return root, shas


def probe_for(root):
    return lambda c: OA.run_check_at(root, c, [sys.executable, "src/inst.py", "--verify"])


# REQ-4 -----------------------------------------------------------------------

def test_bisect_finds_planted_regression_in_instrument(planted_repo, tmp_path):
    root, shas = planted_repo
    ledger = str(tmp_path / "l.jsonl")
    rows = [mkrow("verify_entrypoint", "src/inst.py", "instrument", "PASS", shas[1][:7], "linux",
                  {"exit": 0, "sha256": "a" * 64, "args": ["--verify"]}),
            mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", shas[5][:7], "linux",
                  {"exit": 1, "sha256": None, "args": ["--verify"]}, ts="2026-09-06T11:00:00Z")]
    OL.append_rows(ledger, rows)
    appended = OA.run(ledger, root=root, probe=probe_for(root), out=open(os.devnull, "w"))
    assert len(appended) == 1
    d = appended[0]["detail"]
    assert d["method"] == "bisect"
    assert d["introduced_by"] == shas[3][:7]          # c3 changed data.txt
    assert d["last_good"] == shas[1][:7]              # from the ledger's last PASS
    assert {s["result"] for s in d["steps"] if "result" in s} <= {"PASS", "FAIL", "ERROR"}
    assert appended[0]["signal"] == "ATTRIBUTED" and appended[0]["severity"] == "info"


def test_bisect_falls_back_to_creation_commit(planted_repo, tmp_path):
    root, shas = planted_repo
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", shas[5][:7], "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    appended = OA.run(ledger, root=root, probe=probe_for(root), out=open(os.devnull, "w"))
    d = appended[0]["detail"]
    assert d["last_good"] == shas[0][:7] and d["introduced_by"] == shas[3][:7]


def test_bisect_cleans_worktrees(planted_repo):
    root, shas = planted_repo
    before = git(root, "worktree", "list")
    assert OA.run_check_at(root, shas[5], [sys.executable, "src/inst.py", "--verify"]) == "FAIL"
    assert OA.run_check_at(root, shas[1], [sys.executable, "src/inst.py", "--verify"]) == "PASS"
    assert git(root, "worktree", "list") == before


# REQ-5 -----------------------------------------------------------------------

def test_not_reproducible_on_this_platform(planted_repo, tmp_path):
    root, shas = planted_repo
    ledger = str(tmp_path / "l.jsonl")
    # a FAIL recorded at a commit where the check passes here (e.g. Linux-only)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", shas[2][:7], "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    appended = OA.run(ledger, root=root, probe=probe_for(root), out=open(os.devnull, "w"))
    d = appended[0]["detail"]
    assert d["method"] == "not_reproducible_here" and d["introduced_by"] is None
    assert d["platform"] == sys.platform


def test_commit_unavailable(planted_repo, tmp_path):
    root, _ = planted_repo
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", "0000000", "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    appended = OA.run(ledger, root=root, out=open(os.devnull, "w"))
    assert appended[0]["detail"]["method"] == "commit_unavailable"


# REQ-3 -----------------------------------------------------------------------

def test_stale_eval_attributed_by_path_history(planted_repo, tmp_path):
    root, shas = planted_repo
    (root / "agents").mkdir()
    (root / "agents" / "x.md").write_text("v1")
    git(root, "add", "-A"), git(root, "commit", "-qm", "add agent")
    rec = git(root, "rev-parse", "HEAD")
    (root / "agents" / "x.md").write_text("v2")
    git(root, "add", "-A"), git(root, "commit", "-qm", "edit agent")
    edit = git(root, "rev-parse", "HEAD")
    (root / "agents" / "x.md").write_text("v3")
    git(root, "add", "-A"), git(root, "commit", "-qm", "edit agent again")
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("agent_eval", "agents/x.md", "agent", "STALE_EVAL", git(root, "rev-parse", "--short", "HEAD"),
                                  "V-1:staleness", {"record_commit": rec[:7], "agent_sha256_now": "n", "agent_sha256_at_eval": "e"})])
    appended = OA.run(ledger, root=root, out=open(os.devnull, "w"))
    d = appended[0]["detail"]
    assert d["method"] == "path_history" and d["introduced_by"] == edit[:7]


# REQ-2 -----------------------------------------------------------------------

def test_attribute_is_idempotent_and_skips_closed_defects(planted_repo, tmp_path):
    root, shas = planted_repo
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [
        mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", shas[5][:7], "linux",
              {"exit": 1, "sha256": None, "args": ["--verify"]}),
        mkrow("verify_entrypoint", "src/inst.py", "instrument", "PASS", shas[5][:7], "linux",
              {"exit": 0, "sha256": "a" * 64, "args": ["--verify"]}, ts="2026-09-06T12:00:00Z")])
    assert OA.run(ledger, root=root, probe=probe_for(root), out=open(os.devnull, "w")) == []   # closed: --new skips
    replayed = OA.run(ledger, root=root, replay=True, probe=probe_for(root), out=open(os.devnull, "w"))
    assert len(replayed) == 1
    assert OA.run(ledger, root=root, replay=True, probe=probe_for(root), out=open(os.devnull, "w")) == []
    assert OL.verify_ledger(ledger) == []


def test_new_is_noop_on_committed_ledger():
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_attribute.py"), "--new", "--dry-run"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no unattributed defects" in r.stdout or "attributed" in r.stdout


# REQ-8 (slow, opt-in) ----------------------------------------------------------

@pytest.mark.skipif(not os.environ.get("LAB_SLOW_TESTS"), reason="real-history bisection (~1-2 min); LAB_SLOW_TESTS=1")
def test_real_history_attributes_pr20_append(tmp_path):
    rows = OL.read_rows(os.path.join(REPO, "results", "outcome_ledger.jsonl"))
    weekly_fail = next(r for r in rows if r["source"] == "verify_entrypoint"
                       and r["artifact"] == "src/pcso_weekly_update.py" and r["signal"] == "FAIL"
                       and r["detail"].get("subject") == "darwin")
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [weekly_fail])
    appended = OA.run(ledger, root=REPO, out=open(os.devnull, "w"))
    d = appended[0]["detail"]
    assert d["method"] == "bisect"
    assert d["introduced_by"] == "9488a9a", json.dumps(d, indent=1)
    assert d.get("merged_by") == "1aff3dc"
