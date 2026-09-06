#!/usr/bin/env python3
"""R4/R5 minimal closed loop: lessons derived from closed defects, and the
healer dispatching a (fake) repair agent in a worktree, gating it, and
recording PROPOSED / REJECTED rows. No LLM is called here: the agent command
is a small script; the real command is exercised by the operator with --push.

Run: python3 -m pytest tests/test_lab_heal_learn.py -q
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


LH = load("lab_heal")
LL = LH.LL
OL = LH.OL


def mkrow(source, artifact, cls, signal, commit, subject="", detail=None, ts="2026-09-06T10:00:00Z"):
    return OL.make_row(source, artifact, cls, signal, f"{signal} {artifact} evidence", {"subject": subject, **(detail or {})},
                       ts, commit, "tester")


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def broken_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t"), git(root, "config", "user.name", "t")
    (root / "src").mkdir()
    (root / "src" / "inst.py").write_text(
        "import sys\nd=open('data.txt').read().strip()\n"
        "print('PASS sha256=' + 'a'*64 + '; wrote=none') if d=='ok' else sys.exit(1)\n")
    (root / "data.txt").write_text("broken\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "broken state")
    return root, git(root, "rev-parse", "--short", "HEAD")


def fake_agent(tmp_path, body):
    p = tmp_path / "fake_agent.py"
    p.write_text("import sys\nbrief = sys.stdin.read()\n" + body)
    return f"{sys.executable} {p}"


OK_GATE = f'{sys.executable} -c "import sys; sys.exit(0)"'


# --------------------------------------------------------------- learn ----

def test_lessons_derived_from_closed_defects_with_attribution(tmp_path):
    rows = [mkrow("verify_entrypoint", "src/x.py", "instrument", "FAIL", "aaaaaaa", "darwin",
                  {"exit": 1, "sha256": None, "args": ["--verify"]}),
            OL.make_row("attribution", "src/x.py", "instrument", "ATTRIBUTED", "introduced_by bbbbbbb",
                        {"subject": "darwin", "defect_key": None, "method": "bisect", "introduced_by": "bbbbbbb",
                         "merged_by": "ccccccc"}, "2026-09-06T10:30:00Z", "aaaaaaa", "tester"),
            mkrow("verify_entrypoint", "src/x.py", "instrument", "PASS", "ddddddd", "darwin",
                  {"exit": 0, "sha256": "a" * 64, "args": ["--verify"]}, ts="2026-09-06T11:00:00Z"),
            mkrow("verify_entrypoint", "src/y.py", "instrument", "FAIL", "eeeeeee", "linux",
                  {"exit": 1, "sha256": None, "args": ["--verify"]})]          # still open: no lesson
    rows[1]["detail"]["defect_key"] = "|".join(OL.state_key(rows[0]))
    lessons = LL.derive(rows, [])
    assert len(lessons) == 1
    l = lessons[0]
    assert l["artifact"] == "src/x.py" and l["introduced_by"] == "bbbbbbb" and l["merged_by"] == "ccccccc"
    assert l["fixed_at"] == "ddddddd" and l["platform"] == "darwin"
    assert "introduced by bbbbbbb via merge ccccccc" in l["lesson"]
    assert LL.derive(rows, lessons) == []                     # idempotent
    path = str(tmp_path / "lessons.jsonl")
    LL.append_lessons(path, lessons)
    assert LL.relevant(LL.read_lessons(path), "src/x.py") == lessons
    assert LL.relevant(LL.read_lessons(path), "src/other.py", "instrument") == lessons   # same class
    assert LL.relevant(LL.read_lessons(path), "agents/a.md", "agent") == []


def test_learn_cli_derive_and_add(tmp_path):
    lessons = str(tmp_path / "lessons.jsonl")
    env = dict(os.environ, LAB_LESSONS=lessons)
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "lab_learn.py"), "--derive"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "lessons:" in r.stdout
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "lab_learn.py"), "--add", "keep inputs pinned",
                        "--artifact", "src/pcso_weekly_update.py", "--class", "instrument"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0
    assert any(l["kind"] == "manual" for l in LL.read_lessons(lessons))


# ---------------------------------------------------------------- heal ----

def test_heal_proposes_when_agent_fixes_and_gate_passes(broken_repo, tmp_path, monkeypatch):
    root, sha = broken_repo
    monkeypatch.setenv("LAB_LESSONS", str(tmp_path / "lessons.jsonl"))
    LL.append_lessons(str(tmp_path / "lessons.jsonl"),
                      [{"schema_version": 1, "ts": "2026-09-06T00:00:00Z", "kind": "manual", "artifact": "src/inst.py",
                        "artifact_class": "instrument", "defect_key": None, "lesson": "data.txt must say ok"}])
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "assert 'data.txt must say ok' in brief\n"
                                 "open('data.txt','w').write('ok\\n')\n"
                                 "open('HEAL_NOTES.md','w').write('root cause: data drift\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False,
                  keep_worktree=True, out=open(os.devnull, "w"))
    assert len(rows) == 1 and rows[0]["signal"] == "PROPOSED"
    d = rows[0]["detail"]
    assert d["stage"] == "proposed" and d["commit"] and sorted(d["files_changed"]) == ["HEAL_NOTES.md", "data.txt"]
    assert "root cause" in d["notes"]
    assert d["branch"].startswith("heal/src-inst-py-fail-")
    # the fix is committed on the heal branch, HEAD of the repo untouched
    assert git(root, "rev-parse", "--short", d["branch"]) == d["commit"]
    assert git(root, "rev-parse", "--short", "main") == sha
    assert "HEAL_BRIEF.md" not in git(root, "show", "--name-only", "--format=", d["branch"])
    assert OL.verify_ledger(ledger) == []
    # cleanup worktrees the test kept
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree ") and "lab-heal-" in line:
            git(root, "worktree", "remove", "--force", line.split(" ", 1)[1])


def test_heal_rejects_when_agent_changes_nothing(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "pass\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "REJECTED" and rows[0]["detail"]["stage"] == "agent"
    assert "lab-heal-" not in git(root, "worktree", "list")          # removed


def test_heal_rejects_when_defect_check_still_fails(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "open('data.txt','w').write('still wrong\\n')\n"
                                 "open('HEAL_NOTES.md','w').write('tried\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "REJECTED" and rows[0]["detail"]["stage"] == "gate"
    assert "still exits 1" in rows[0]["evidence"]
    assert git(root, "rev-parse", "--short", "main") == sha
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree ") and "lab-heal-" in line:
            git(root, "worktree", "remove", "--force", line.split(" ", 1)[1])


def test_heal_skips_defect_with_pending_proposal_but_not_attributed_ones(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = str(tmp_path / "l.jsonl")
    defect = mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                   {"exit": 1, "sha256": None, "args": ["--verify"]})
    key = "|".join(OL.state_key(defect))
    OL.append_rows(ledger, [defect,
                            OL.make_row("attribution", "src/inst.py", "instrument", "ATTRIBUTED", "introduced_by x",
                                        {"subject": "linux", "defect_key": key, "defect_commit": sha, "method": "bisect",
                                         "introduced_by": sha}, "2026-09-06T10:10:00Z", sha, "tester")])
    # attributed but not yet healed -> still a healer target
    agent = fake_agent(tmp_path, "pass\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert len(rows) == 1 and rows[0]["signal"] == "REJECTED"
    OL.append_rows(ledger, [OL.make_row("heal", "src/inst.py", "instrument", "PROPOSED", "PROPOSED heal/x",
                                        {"subject": "linux", "defect_key": key, "defect_commit": sha, "branch": "heal/x"},
                                        "2026-09-06T10:20:00Z", sha, "tester")])
    assert LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w")) == []


def test_heal_noop_without_open_defects(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "PASS", "abc1234", "linux",
                                  {"exit": 0, "sha256": "a" * 64, "args": ["--verify"]})])
    assert LH.run(ledger, root=REPO, out=open(os.devnull, "w")) == []


def test_brief_carries_guardrails_and_check():
    rows = [mkrow("verify_entrypoint", "src/pcso_weekly_update.py", "instrument", "FAIL", "abc1234", "darwin",
                  {"exit": 1, "sha256": None, "args": ["--verify"]})]
    b = LH.brief_for(rows[0], rows, REPO)
    assert "Never edit A0" in b and "append, never rewrite" in b and "Owner-reserved" in b
    assert ".venv/bin/python src/pcso_weekly_update.py --verify" in b
    assert "HEAL_NOTES.md" in b
