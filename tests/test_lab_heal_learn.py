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
    (root / "src").mkdir(), (root / "results").mkdir()
    (root / "HEAL_NOTES.md").write_text("notes of an earlier repair, tracked at the base\n")
    # The planted defect is in the instrument (it expects the token 'okay'); the frozen
    # data file is correct. The honest fix edits src/inst.py; rewriting results/data.txt
    # is the wrong-reason fix and is rejected by the scope check.
    (root / "src" / "inst.py").write_text(
        "import sys\nd=open('results/data.txt').read().strip()\n"
        "print('PASS sha256=' + 'a'*64 + '; wrote=none') if d=='okay' else sys.exit(1)\n")
    (root / "results/data.txt").write_text("ok\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "broken state")
    return root, git(root, "rev-parse", "--short", "HEAD")


def fake_agent(tmp_path, body, name="fake_agent.py"):
    p = tmp_path / name
    p.write_text("import sys\nbrief = sys.stdin.read()\n" + body)
    return f'"{sys.executable}" "{p.as_posix()}"'


OK_GATE = f'{sys.executable} -c "import sys; sys.exit(0)"'
# the honest fix for broken_repo: one token in the instrument
FIX = "s = open('src/inst.py').read().replace(\"'okay'\", \"'ok'\")\nopen('src/inst.py', 'w').write(s)\n"


def proposer_green_rows(ts="2026-09-06T09:00:00Z"):
    """The proposer's own eval rows as the collector records them when green
    (no eval pass, no dispatch: every heal test needs these on the ledger)."""
    return [OL.make_row("agent_eval", LH.PROPOSER_DEF, "agent", "PASS", f"{ev}: PASS", {"subject": ev},
                        ts, "abc1234", "tester") for ev in LH.PROPOSER_EVALS]


def new_ledger(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    OL.append_rows(ledger, proposer_green_rows())
    return ledger


# --------------------------------------------------------------- learn ----

def test_lessons_derived_from_closed_defects_with_attribution(tmp_path):
    rows = [mkrow("verify_entrypoint", "src/x.py", "instrument", "FAIL", "aaaaaaa", "darwin",
                  {"exit": 1, "sha256": None, "args": ["--verify"]}),
            OL.make_row("attribution", "src/x.py", "instrument", "ATTRIBUTED", "introduced_by bbbbbbb",
                        {"subject": "darwin", "defect_key": None, "defect_commit": "aaaaaaa", "method": "bisect",
                         "introduced_by": "bbbbbbb", "merged_by": "ccccccc"}, "2026-09-06T10:30:00Z", "aaaaaaa", "tester"),
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
    # the same failure state recurring at a later commit and refixed is a second lesson
    rows += [mkrow("verify_entrypoint", "src/x.py", "instrument", "FAIL", "fffffff", "darwin",
                   {"exit": 1, "sha256": None, "args": ["--verify"]}, ts="2026-09-06T12:00:00Z"),
             mkrow("verify_entrypoint", "src/x.py", "instrument", "PASS", "ggggggg", "darwin",
                   {"exit": 0, "sha256": "a" * 64, "args": ["--verify"]}, ts="2026-09-06T13:00:00Z")]
    again = LL.derive(rows, lessons)
    assert len(again) == 1 and again[0]["defect_commit"] == "fffffff" and again[0]["fixed_at"] == "ggggggg"
    assert again[0]["introduced_by"] is None                  # no attribution for that occurrence
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
                        "artifact_class": "instrument", "defect_key": None, "lesson": "inst.py must expect the token ok"}])
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "assert 'inst.py must expect the token ok' in brief\n" + FIX +
                                 "open('HEAL_NOTES.md','w').write('root cause: token typo\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False,
                  keep_worktree=True, out=open(os.devnull, "w"))
    assert len(rows) == 1 and rows[0]["signal"] == "PROPOSED"
    d = rows[0]["detail"]
    assert d["stage"] == "proposed" and d["commit"] and sorted(d["files_changed"]) == ["HEAL_NOTES.md", "src/inst.py"]
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


def test_heal_links_venv_and_proceeds_when_agent_exits_nonzero_after_changing_files(broken_repo, tmp_path):
    root, sha = broken_repo
    (root / ".venv" / "bin").mkdir(parents=True)          # the lab's interpreter dir, not tracked
    (root / ".gitignore").write_text(".venv\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "ignore venv")
    sha = git(root, "rev-parse", "--short", "HEAD")
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "import os\nassert os.path.islink('.venv') and os.path.isdir('.venv/bin')\n" + FIX +
                                 "open('HEAL_NOTES.md','w').write('fixed\\n')\n"
                                 "print('Error: Reached max turns (30)')\nsys.exit(1)\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "PROPOSED" and rows[0]["detail"]["agent_exit"] == 1
    assert "max turns" in rows[0]["detail"]["agent_tail"]
    assert sorted(rows[0]["detail"]["files_changed"]) == ["HEAL_NOTES.md", "src/inst.py"]
    assert ".venv" not in git(root, "show", "--name-only", "--format=", rows[0]["detail"]["branch"])
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree ") and "lab-heal-" in line:
            git(root, "worktree", "remove", "--force", line.split(" ", 1)[1])


def test_heal_rejects_when_agent_changes_nothing(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "pass\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "REJECTED" and rows[0]["detail"]["stage"] == "agent"
    assert "lab-heal-" not in git(root, "worktree", "list")          # removed


def test_heal_rejects_when_defect_check_still_fails(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    agent = fake_agent(tmp_path, "s = open('src/inst.py').read().replace(\"'okay'\", \"'nope'\")\n"
                                 "open('src/inst.py', 'w').write(s)\n"
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
    ledger = new_ledger(tmp_path)
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


def test_heal_retries_after_gate_rejection_until_cap(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    defect = mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                   {"exit": 1, "sha256": None, "args": ["--verify"]})
    key = "|".join(OL.state_key(defect))
    heal = lambda branch, ts: OL.make_row("heal", "src/inst.py", "instrument", "PROPOSED", f"PROPOSED {branch}",
                                          {"subject": "linux", "defect_key": key, "defect_commit": sha, "branch": branch,
                                           "pr": "https://x/pull/1"}, ts, sha, "tester")
    gate = lambda branch, ts: OL.make_row("gate", "src/inst.py", "instrument", "REJECTED", f"REJECTED {branch}",
                                          {"subject": "linux", "defect_key": key, "defect_commit": sha, "branch": branch},
                                          ts, sha, "tester")
    OL.append_rows(ledger, [defect, heal("heal/a", "2026-09-06T10:10:00Z")])
    agent = fake_agent(tmp_path, "pass\n")
    quiet = open(os.devnull, "w")
    assert LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=quiet) == []  # pending
    OL.append_rows(ledger, [gate("heal/a", "2026-09-06T10:20:00Z")])
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=quiet)      # retried
    assert len(rows) == 1 and rows[0]["signal"] == "REJECTED"
    OL.append_rows(ledger, [heal("heal/c", "2026-09-06T10:40:00Z"), gate("heal/c", "2026-09-06T10:50:00Z")])
    assert sum(1 for r in OL.read_rows(ledger) if r["source"] == "heal") == LH.HEAL_ATTEMPT_CAP
    assert LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=quiet) == []  # at cap


def test_heal_exception_path_cleans_worktree_and_records(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                                  {"exit": 1, "sha256": None, "args": ["--verify"]})])
    rows = LH.run(ledger, root=str(root), agent_cmd="/nonexistent/agent --x", gate_cmd=OK_GATE, push=False,
                  out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "REJECTED" and rows[0]["detail"]["agent_exit"] == 127
    assert "lab-heal-" not in git(root, "worktree", "list")
    assert OL.verify_ledger(ledger) == []


def test_redaction_and_agent_env(monkeypatch):
    assert LH.redact("token=abc123 and api_key: XYZ, ok=1") == "token=<redacted> and api_key=<redacted>, ok=1"
    assert "<redacted>" in LH.redact("Authorization: Bearer sk-ant-abcdefghijklmnop")
    assert LH.redact("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345") == "<redacted>"
    assert LH.redact("plain text 252 rows") == "plain text 252 rows"
    monkeypatch.setenv("GH_TOKEN", "x"), monkeypatch.setenv("GITHUB_TOKEN", "x"), monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    monkeypatch.setenv("MY_PASSWORD", "x"), monkeypatch.setenv("ANTHROPIC_API_KEY", "keep"), monkeypatch.setenv("CLAUDECODE", "1")
    env = LH.agent_env()
    for k in ("GH_TOKEN", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY", "MY_PASSWORD", "CLAUDECODE"):
        assert k not in env
    assert env["ANTHROPIC_API_KEY"] == "keep" and "PATH" in env


def test_default_agent_command_has_no_raw_bash_or_git_write():
    cmd = LH.DEFAULT_AGENT_CMD
    tokens = cmd.split()
    assert "Bash" not in tokens                                   # only scoped Bash(...) entries
    assert "--disallowedTools" in cmd and "Bash(git commit:*)" in cmd and "Bash(git push:*)" in cmd


def test_heal_noop_without_open_defects(tmp_path):
    ledger = new_ledger(tmp_path)
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


# ------------------------------------------------------ R2 proposer ----

def defect_row(sha):
    return mkrow("verify_entrypoint", "src/inst.py", "instrument", "FAIL", sha, "linux",
                 {"exit": 1, "sha256": None, "args": ["--verify"]})


def test_heal_refuses_when_proposer_eval_not_green(broken_repo, tmp_path, capsys):
    root, sha = broken_repo
    agent = fake_agent(tmp_path, FIX + "open('HEAL_NOTES.md','w').write('x\\n')\n")
    # (a) no eval rows at all
    bare = str(tmp_path / "bare.jsonl")
    OL.append_rows(bare, [defect_row(sha)])
    assert LH.run(bare, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False) == []
    assert "no eval pass, no dispatch" in capsys.readouterr().out
    assert not [r for r in OL.read_rows(bare) if r["source"] == "heal"]          # no attempt spent
    # (b) one eval FAIL
    failed = str(tmp_path / "failed.jsonl")
    rows = proposer_green_rows()
    rows[0] = OL.make_row("agent_eval", LH.PROPOSER_DEF, "agent", "FAIL", "P-1: FAIL", {"subject": "P-1"},
                          "2026-09-06T09:00:00Z", "abc1234", "tester")
    OL.append_rows(failed, rows + [defect_row(sha)])
    assert LH.run(failed, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False) == []
    assert "P-1: latest eval row is FAIL" in capsys.readouterr().out
    # (c) green evals but the definition drifted from its record (open STALE_EVAL slot)
    stale = str(tmp_path / "stale.jsonl")
    OL.append_rows(stale, proposer_green_rows() + [
        OL.make_row("agent_eval", LH.PROPOSER_DEF, "agent", "STALE_EVAL", "P-2 stale", {"subject": "P-2:staleness"},
                    "2026-09-06T09:30:00Z", "abc1234", "tester"), defect_row(sha)])
    assert LH.run(stale, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False) == []
    assert "P-2: definition is STALE_EVAL" in capsys.readouterr().out
    # (d) the stale slot closed again (latest state PASS) -> dispatchable
    OL.append_rows(stale, [OL.make_row("agent_eval", LH.PROPOSER_DEF, "agent", "PASS", "P-2 in sync",
                                       {"subject": "P-2:staleness"}, "2026-09-06T09:40:00Z", "abc1234", "tester")])
    assert LH.proposer_eval_block(OL.read_rows(stale)) == []


def test_heal_dispatches_registered_proposer_with_record(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [defect_row(sha)])
    meta, body, digest = LH.load_proposer()
    assert meta["name"] == "lab-proposer" and meta["model"] in ("haiku", "sonnet") and "---" not in body[:3]
    # the agent sees the definition body first, then the brief; the record already exists on disk
    agent = fake_agent(tmp_path, "import os\n"
                                 "assert brief.startswith('You are the lab\\'s repair proposer')\n"
                                 "assert '# Repair brief' in brief and 'src/inst.py' in brief\n"
                                 "rec = [d for d in os.listdir('results/agent_runs') if d.startswith('propose-')][0]\n"
                                 "assert open('results/agent_runs/' + rec + '/prompt.md').read() == brief\n"
                                 "assert 'definition sha256' in open('results/agent_runs/' + rec + '/agent.txt').read()\n"
                                 + FIX +
                                 "open('HEAL_NOTES.md','w').write('root cause: drift\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "PROPOSED", rows[0]
    d = rows[0]["detail"]
    assert d["agent"] == "lab-proposer" and d["model"] == meta["model"] and d["agent_sha256"] == digest
    assert d["record"].startswith("results/agent_runs/propose-src-inst-py-fail-")
    assert d["class_scope"] == list(LH.CLASS_SCOPE["instrument"])
    assert sorted(d["files_changed"]) == ["HEAL_NOTES.md", "src/inst.py"]     # the record is not the agent's change
    committed = git(root, "show", "--name-only", "--format=", d["branch"]).splitlines()
    assert "HEAL_NOTES.md" not in committed                                         # moved into the record
    for name in ("prompt.md", "agent.txt", "report.md", "gate.txt"):
        assert f"{d['record']}/{name}" in committed
    assert git(root, "show", f"{d['branch']}:{d['record']}/report.md") == "root cause: drift"
    assert git(root, "show", f"{d['branch']}:{d['record']}/gate.txt").startswith("ok")
    # an explicit tier override is recorded as such
    rows2 = LH.run(ledger, root=str(root), defect_key=d["defect_key"], model="haiku", agent_cmd=agent,
                   gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows2[0]["detail"]["model"] == "haiku"
    body_txt = LH.pr_body(d["defect_key"], d, "instrument", "root cause: drift", "gate ok")
    assert d["record"] in body_txt and "lab-proposer" in body_txt and "root cause: drift" in body_txt
    assert digest[:16] in body_txt and "instrument" in body_txt


def test_heal_rejects_out_of_scope_changes_before_gate(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [defect_row(sha)])
    marker = tmp_path / "gate-ran"
    gate_cmd = f'{sys.executable} -c "open({str(marker)!r},\'w\').write(\'ran\')"'
    agent = fake_agent(tmp_path, FIX +
                                 "open('config.toml','w').write('x\\n')\n"          # outside instrument scope
                                 "open('HEAL_NOTES.md','w').write('n\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=gate_cmd, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "REJECTED" and rows[0]["detail"]["stage"] == "scope"
    assert rows[0]["detail"]["out_of_scope"] == ["config.toml"] and "config.toml" in rows[0]["evidence"]
    assert not marker.exists()                                                      # gate never ran
    assert "lab-heal-" not in git(root, "worktree", "list")
    # rewriting the frozen data file (in the instrument's prefix, but tracked) is the wrong-reason fix
    rewriter = fake_agent(tmp_path, "open('results/data.txt','w').write('okay\\n')\nopen('HEAL_NOTES.md','w').write('n\\n')\n",
                          name="rewriter.py")
    rows = LH.run(ledger, root=str(root), agent_cmd=rewriter, gate_cmd=gate_cmd, push=False, out=open(os.devnull, "w"))
    assert rows[0]["detail"]["stage"] == "scope" and rows[0]["detail"]["frozen_results"] == ["results/data.txt"]
    assert "frozen" in rows[0]["evidence"] and not marker.exists()
    # touching another dispatch record is rejected too; adding a NEW results file is allowed
    meddler = fake_agent(tmp_path, FIX + "import os\nos.makedirs('results/agent_runs/eval-old', exist_ok=True)\n"
                                         "open('results/agent_runs/eval-old/grade.json','w').write('{}\\n')\n"
                                         "open('HEAL_NOTES.md','w').write('n\\n')\n", name="meddler.py")
    rows = LH.run(ledger, root=str(root), agent_cmd=meddler, gate_cmd=gate_cmd, push=False, out=open(os.devnull, "w"))
    assert rows[0]["detail"]["stage"] == "scope"
    assert rows[0]["detail"]["audit_records"] == ["results/agent_runs/eval-old/grade.json"]
    adder = fake_agent(tmp_path, FIX + "open('results/new_version.json','w').write('{}\\n')\n"
                                       "open('HEAL_NOTES.md','w').write('root cause: typo\\n')\n", name="adder.py")
    key = "|".join(OL.state_key(defect_row(sha)))          # three attempts are spent: address the occurrence directly
    rows = LH.run(ledger, root=str(root), defect_key=key, agent_cmd=adder, gate_cmd=OK_GATE, push=False,
                  out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "PROPOSED", rows[0]
    assert sorted(rows[0]["detail"]["files_changed"]) == ["HEAL_NOTES.md", "results/new_version.json", "src/inst.py"]
    assert LH.scope_violations(["src/x.py", "results/a.json"], ["results/a.json"], "instrument", "r") == \
        {"frozen_results": ["results/a.json"]}
    # a class the table does not know allows nothing
    assert LH.out_of_scope(["src/x.py"], "ledger", "results/agent_runs/propose-x") == ["src/x.py"]


def test_heal_allows_declared_regeneration_only(broken_repo, tmp_path, monkeypatch):
    """R4 full REQ-3: a tracked results/ file may be rewritten iff the defect's
    artefact declares it as its regenerable output; any other one stays frozen."""
    root, sha = broken_repo
    (root / "results" / "other.txt").write_text("frozen\n")
    git(root, "add", "-A"), git(root, "commit", "-qm", "another frozen result")
    sha = git(root, "rev-parse", "--short", "HEAD")
    monkeypatch.setattr(LH.OC, "REPLAY_TARGETS", [("src/inst.py", [], ["results/data.txt"])])
    ledger = new_ledger(tmp_path)
    defect = mkrow("replay", "src/inst.py", "instrument", "FAIL", sha, "linux",
                   {"args": [], "exit": 0, "outputs": {"results/data.txt": {"committed": "a", "regenerated": "b", "same": False}}})
    OL.append_rows(ledger, [defect])
    key = "|".join(OL.state_key(defect))
    regen = fake_agent(tmp_path, "assert 'Regenerable outputs' in brief and 'results/data.txt' in brief\n"
                                 "open('results/data.txt','w').write('okay\\n')\nopen('HEAL_NOTES.md','w').write('regenerated\\n')\n",
                       name="regen.py")
    rows = LH.run(ledger, root=str(root), defect_key=key, agent_cmd=regen, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["signal"] == "PROPOSED", (rows[0]["detail"].get("stage"), rows[0]["evidence"])
    assert rows[0]["detail"]["regenerable"] == ["results/data.txt"]
    assert sorted(rows[0]["detail"]["files_changed"]) == ["HEAL_NOTES.md", "results/data.txt"]
    # the same rewrite of a results/ file the artefact does not declare is still frozen
    other = fake_agent(tmp_path, "open('results/other.txt','w').write('x\\n')\nopen('HEAL_NOTES.md','w').write('n\\n')\n",
                       name="other.py")
    rows = LH.run(ledger, root=str(root), defect_key=key, agent_cmd=other, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["detail"]["stage"] == "scope" and rows[0]["detail"]["frozen_results"] == ["results/other.txt"]
    # deleting the declared output is a rewrite, not a regeneration
    deleter = fake_agent(tmp_path, "import os\nos.remove('results/data.txt')\nopen('HEAL_NOTES.md','w').write('n\\n')\n",
                         name="deleter.py")
    rows = LH.run(ledger, root=str(root), defect_key=key, agent_cmd=deleter, gate_cmd=OK_GATE, push=False, out=open(os.devnull, "w"))
    assert rows[0]["detail"]["stage"] == "scope" and rows[0]["detail"]["frozen_results"] == ["results/data.txt"]
    assert LH.scope_violations(["results/a.json"], ["results/a.json"], "instrument", "r", ["results/a.json"]) == {}
    assert LH.scope_violations(["results/a.json"], ["results/a.json"], "instrument", "r", []) == {"frozen_results": ["results/a.json"]}
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree ") and "lab-heal-" in line:
            git(root, "worktree", "remove", "--force", line.split(" ", 1)[1])


def test_heal_records_owner_reserved_stop_without_running_the_gate(broken_repo, tmp_path):
    root, sha = broken_repo
    ledger = new_ledger(tmp_path)
    OL.append_rows(ledger, [defect_row(sha)])
    marker = tmp_path / "gate-ran"
    gate_cmd = f'{sys.executable} -c "open({str(marker)!r},\'w\').write(\'ran\')"'
    agent = fake_agent(tmp_path, "open('HEAL_NOTES.md','w').write('## Owner-Reserved\\nthe fix needs a constitution edit.\\n')\n")
    rows = LH.run(ledger, root=str(root), agent_cmd=agent, gate_cmd=gate_cmd, push=False, out=open(os.devnull, "w"))
    d = rows[0]["detail"]
    assert rows[0]["signal"] == "REJECTED" and d["stage"] == "owner-reserved"       # any case of the token counts
    assert "Owner-Reserved" in d["notes"] and d["files_changed"] == ["HEAL_NOTES.md"]
    assert LH.flagged_owner_reserved("OWNER-RESERVED: x") and not LH.flagged_owner_reserved("owner reserved")
    assert LH.flagged_owner_reserved("## Root cause\n...\n- **OWNER-RESERVED**: needs A0\n")
    assert LH.flagged_owner_reserved("## Owner-Reserved\n") and LH.flagged_owner_reserved("**OWNER-RESERVED**\nwhy\n")
    # a mention in passing is not a flag, even wrapped onto a line start (sonnet's live P-1
    # notes were rejected on exactly this by a substring test)
    assert not LH.flagged_owner_reserved("Nothing here required an append-only version; no\n"
                                         "owner-reserved artifacts were implicated by this defect.\n")
    assert not LH.flagged_owner_reserved("The owner-reserved list does not cover data files.\n")
    assert "OWNER-RESERVED" in rows[0]["evidence"] and not marker.exists()
    # the attempt counts toward the cap, so the R3 gate routes the occurrence to the owner at the cap
    assert sum(1 for r in OL.read_rows(ledger) if r["source"] == "heal") == 1
    assert LH.out_of_scope(["HEAL_NOTES.md", "results/agent_runs/propose-x/prompt.md", "docs/kb/c.md"],
                           "theorem_card", "results/agent_runs/propose-x") == []
