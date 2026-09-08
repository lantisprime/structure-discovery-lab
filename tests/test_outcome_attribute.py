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


def test_bisect_retries_error_once_and_flags_persistent_skips(planted_repo):
    root, shas = planted_repo
    real = probe_for(root)
    calls = {"n": 0}

    def flaky(c):                       # first probe of every commit errors, second succeeds
        calls["n"] += 1
        return "ERROR" if calls["n"] % 2 == 1 else real(c)
    first_bad, steps, skipped = OA.bisect(shas[1:], flaky)
    assert first_bad == shas[3] and skipped == []

    def dead_at_c3(c):                  # c3 can never be probed
        return "ERROR" if c == shas[3] else real(c)
    first_bad, steps, skipped = OA.bisect(shas[1:], dead_at_c3)
    assert first_bad == shas[3] and skipped == [shas[3][:7]]     # conservative, and flagged


def test_creation_commit_resolves_composite_suite_names(planted_repo, monkeypatch):
    root, shas = planted_repo
    monkeypatch.setattr(OA.OC, "PYTEST_SUITES", [("src/inst.py+data.txt", ["src/inst.py", "data.txt"])])
    assert OA.creation_commit(root, "src/inst.py+data.txt") == shas[0]
    assert OA.creation_commit(root, "src/inst.py") == shas[0]
    assert OA.creation_commit(root, "nope.txt") is None


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
    # the SAME failure state recurring at a later commit is a new occurrence and is attributed again
    (root / "data.txt").write_text("broken again\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "c6 regress")
    c6 = git(root, "rev-parse", "--short", "HEAD")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", c6, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]}, ts="2026-09-06T13:00:00Z")])
    again = OA.run(ledger, root=root, probe=probe_for(root), out=open(os.devnull, "w"))
    assert len(again) == 1 and again[0]["detail"]["defect_commit"] == c6
    assert again[0]["detail"]["introduced_by"] == c6


def test_new_is_noop_on_committed_ledger():
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_attribute.py"), "--new", "--dry-run"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no unattributed defects" in r.stdout or "attributed" in r.stdout


# R4 full REQ-2: replay check ------------------------------------------------------

GEN = ("import json\nopen('results/side.txt', 'w').write('side\\n')\n"
       "json.dump({'n': open('data.txt').read().strip()}, open('results/out.json', 'w'))\n")


@pytest.fixture
def drift_repo(tmp_path):
    """c0: generator + fresh artefact; c1: data changed, artefact not regenerated (the drift);
    c2: unrelated commit. The replay checker exists at none of them."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True), (root / "results").mkdir()
    (root / "src" / "gen.py").write_text(GEN)
    (root / "data.txt").write_text("7\n")
    (root / "results" / "out.json").write_text('{"n": "7"}')
    (root / "results" / "side.txt").write_text("old\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t"), git(root, "config", "user.name", "t")
    git(root, "add", "-A"), git(root, "commit", "-qm", "c0 fresh")
    shas = [git(root, "rev-parse", "HEAD")]
    (root / "data.txt").write_text("16\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "c1 data changed, artefact stale")
    shas.append(git(root, "rev-parse", "HEAD"))
    (root / "readme.txt").write_text("x")
    git(root, "add", "-A"), git(root, "commit", "-qm", "c2 unrelated")
    shas.append(git(root, "rev-parse", "HEAD"))
    return root, shas


def test_replay_check_cli(drift_repo):
    root, shas = drift_repo
    cli = [sys.executable, os.path.join(REPO, "src", "replay_check.py"), "src/gen.py", "--outputs", "results/out.json"]
    r = subprocess.run(cli, cwd=root, capture_output=True, text=True)
    assert r.returncode == 1 and r.stdout.strip().splitlines()[-1].startswith("FAIL results/out.json drifted"), r.stdout + r.stderr
    assert "committed" in r.stdout and "regenerated" in r.stdout
    # every byte restored: the declared output and the side-effect file; nothing new left behind
    assert git(root, "status", "--porcelain") == ""
    assert (root / "results" / "out.json").read_text() == '{"n": "7"}' and (root / "results" / "side.txt").read_text() == "old\n"
    # an uncommitted regeneration (the healer's worktree) is judged as the candidate, not HEAD
    (root / "results" / "out.json").write_text('{"n": "16"}')
    r = subprocess.run(cli, cwd=root, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.startswith("PASS sha256="), r.stdout + r.stderr
    assert (root / "results" / "out.json").read_text() == '{"n": "16"}'
    git(root, "checkout", "--", "results/out.json")
    # a generator that fails is ERROR (exit 2), and the output is still restored
    (root / "src" / "gen.py").write_text("import sys\nopen('results/out.json','w').write('half')\nsys.exit(3)\n")
    r = subprocess.run(cli, cwd=root, capture_output=True, text=True)
    assert r.returncode == 2 and "ERROR" in r.stdout and (root / "results" / "out.json").read_text() == '{"n": "7"}'


def test_check_command_replay_and_bisect_attributes_the_stale_input_commit(drift_repo, tmp_path):
    root, shas = drift_repo
    row = mkrow("replay", "src/gen.py", "instrument", "FAIL", shas[2][:7], "linux",
                {"args": [], "exit": 0, "outputs": {"results/out.json": {"committed": "a", "regenerated": "b", "same": False}}})
    argv = OA.check_command(row)
    assert argv == [sys.executable, os.path.join(REPO, "src", "replay_check.py"), "src/gen.py",
                    "--outputs", "results/out.json", "--args"]
    assert OA.check_command(mkrow("replay", "src/nothing.py", "instrument", "FAIL", "abc1234", "linux", {})) is None
    # the lab's checker runs in the probe worktree against the probe commit's artefact
    assert OA.run_check_at(root, shas[0], argv) == "PASS"
    assert OA.run_check_at(root, shas[2], argv) == "FAIL"
    assert git(root, "status", "--porcelain") == "" and "lab-probe-" not in git(root, "worktree", "list")
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [row])
    appended = OA.run(ledger, root=root, out=open(os.devnull, "w"))
    d = appended[0]["detail"]
    assert d["method"] == "bisect" and d["introduced_by"] == shas[1][:7] and d["last_good"] == shas[0][:7]


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
