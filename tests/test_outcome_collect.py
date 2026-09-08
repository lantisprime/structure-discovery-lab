#!/usr/bin/env python3
"""R0-S2: the outcome collector -- sources, staleness, gate, write discipline.

Run: python3 -m pytest tests/test_outcome_collect.py -q
Fast sources run for real against this repository; the slow sources
(verify entry points, pytest suites) are covered by parser tests on captured
stdout so this suite stays seconds long and never recurses into itself.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "src", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OC = load("outcome_collect")
OL = OC.OL


@pytest.fixture
def seeded_ledger(tmp_path):
    """A scratch ledger seeded from the committed one, exactly as CI seeds its
    runner-temp copy. Needed wherever a test relies on definition hashes at
    eval time: in a shallow checkout (CI default) git history is unavailable
    and the collector must fall back to the hashes the committed ledger
    carries -- the same path production takes."""
    src = os.path.join(REPO, "results", "outcome_ledger.jsonl")
    dst = tmp_path / "seeded.jsonl"
    if os.path.exists(src):
        shutil.copy(src, dst)
    return str(dst)


def fake_source(signal, artifact="src/fake.py", detail=None):
    def fn(ctx):
        return [ctx.row("verify_entrypoint", artifact, "instrument", signal,
                        f"fake {signal}", detail or {"k": signal})]
    return fn


# REQ-4 -------------------------------------------------------------------

def test_collect_fast_sources_emit_rows(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    appended, new_defects = OC.run(list(OC.FAST), ledger, out=open(os.devnull, "w"))
    rows = OL.read_rows(ledger)
    assert OL.verify_ledger(ledger) == []
    g = OC.load_grader(REPO)
    eval_rows = [r for r in rows if r["source"] == "agent_eval" and ":staleness" not in r["detail"]["subject"]]
    assert {r["detail"]["subject"] for r in eval_rows} == set(g.RECORDS)
    assert sum(1 for r in rows if r["source"] == "design_verifier") == 1
    assert sum(1 for r in rows if r["source"] == "ledger_integrity") == 1
    assert all(r["signal"] in OL.SIGNALS for r in rows)
    # re-run: state unchanged -> nothing appended, ledger byte-identical
    before = open(ledger, "rb").read()
    appended2, _ = OC.run(list(OC.FAST), ledger, out=open(os.devnull, "w"))
    assert appended2 == [] and open(ledger, "rb").read() == before


@pytest.mark.parametrize("stdout,rc,expect", [
    ("PASS sha256=" + "a" * 64 + "; validated=128; wrote=none\n", 0, ("PASS", "a" * 64)),
    ("FAIL sha256 mismatch\n", 1, ("FAIL", None)),
    ("PASS sha256=" + "b" * 64 + "; wrote=none\n", 1, ("ERROR", "b" * 64)),
    ("nothing useful\n", 0, ("ERROR", None)),
])
def test_collect_verify_sources_parse_fixture_stdout(stdout, rc, expect):
    signal, sha, evidence = OC.parse_verify_output(stdout, rc)
    assert (signal, sha) == expect
    assert len(evidence) <= OL.EVIDENCE_MAX


def test_platform_is_the_slot_for_verify_and_pytest_rows(tmp_path, monkeypatch):
    """A Linux FAIL and a macOS PASS of the same script are different
    observations: neither may overwrite the other's state or re-trip the gate."""
    ledger = str(tmp_path / "l.jsonl")
    linux_fail = OL.make_row("verify_entrypoint", "src/x.py", "instrument", "FAIL", "exit 1",
                             {"subject": "linux", "exit": 1, "sha256": None, "args": ["--verify"]},
                             "2026-09-06T10:00:00Z", "abc", "ci")
    OL.append_rows(ledger, [linux_fail])
    monkeypatch.setattr(OC, "VERIFY_ENTRYPOINTS", [("src/x.py", ["--verify"])])
    monkeypatch.setattr(OC, "run_cmd", lambda root, argv: (0, "PASS sha256=" + "c" * 64 + "; wrote=none\n", ""))
    _, nd = OC.run(["verify_entrypoint"], ledger, gate=True, out=open(os.devnull, "w"))
    rows = OL.read_rows(ledger)
    assert nd == [] and len(rows) == 2
    assert {r["detail"]["subject"] for r in rows} == {"linux", sys.platform}
    _, nd = OC.run(["verify_entrypoint"], ledger, gate=True, out=open(os.devnull, "w"))
    assert nd == [] and len(OL.read_rows(ledger)) == 2          # stable on re-run


def test_pytest_summary_parser_drops_timing():
    s = OC.parse_pytest_summary("....\n72 passed in 2.77s\n")
    assert s == {"passed": 72, "failed": 0, "errors": 0}
    s = OC.parse_pytest_summary("F..\n1 failed, 2 passed in 0.10s\n")
    assert s["failed"] == 1 and s["passed"] == 2


# R4 full REQ-1: replay source ---------------------------------------------

GEN = ("import json, os\n"
       "os.makedirs('results/figures', exist_ok=True)\n"
       "open('results/figures/side.txt', 'w').write('side effect\\n')\n"
       "json.dump({'n': open('data.txt').read().strip()}, open('results/out.json', 'w'))\n")


@pytest.fixture
def replay_repo(tmp_path):
    """A repo whose derived results/out.json is stale against data.txt."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True), (root / "results" / "figures").mkdir(parents=True)
    (root / "src" / "gen.py").write_text(GEN)
    (root / "data.txt").write_text("16\n")
    (root / "results" / "out.json").write_text('{"n": "7"}')
    (root / "results" / "figures" / "side.txt").write_text("old figure\n")
    for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"],
              ["add", "-A"], ["commit", "-qm", "stale derived artefact"]):
        subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)
    return root


def test_replay_source_detects_drift_and_leaves_tree_clean(replay_repo, tmp_path, monkeypatch):
    root = replay_repo
    monkeypatch.setattr(OC, "REPLAY_TARGETS", [("src/gen.py", [], ["results/out.json"])])
    ledger = str(tmp_path / "l.jsonl")
    assert "replay" in OC.SOURCES and OC.replay_outputs("src/gen.py") == ["results/out.json"]
    assert OC.replay_outputs("src/other.py") == []
    _, nd = OC.run(["replay"], ledger, root=str(root), gate=True, out=open(os.devnull, "w"))
    assert len(nd) == 1 and nd[0]["source"] == "replay" and nd[0]["signal"] == "FAIL"
    r = nd[0]
    assert r["artifact"] == "src/gen.py" and r["artifact_class"] == "instrument"
    assert r["detail"]["subject"] == sys.platform and r["detail"]["args"] == []
    o = r["detail"]["outputs"]["results/out.json"]
    assert o["same"] is False and o["committed"][:8] in r["evidence"] and o["regenerated"][:8] in r["evidence"]
    # the working tree and its worktree list are untouched
    assert subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout == ""
    assert "lab-replay-" not in subprocess.run(["git", "worktree", "list"], cwd=root, capture_output=True, text=True).stdout
    assert (root / "results" / "out.json").read_text() == '{"n": "7"}'
    # same state on re-run: nothing appended; the healed (regenerated) artefact closes the slot with PASS
    _, nd = OC.run(["replay"], ledger, root=str(root), gate=True, out=open(os.devnull, "w"))
    assert nd == [] and len(OL.read_rows(ledger)) == 1
    (root / "results" / "out.json").write_text('{"n": "16"}')
    subprocess.run(["git", "commit", "-qam", "regenerated"], cwd=root, check=True, capture_output=True)
    appended, nd = OC.run(["replay"], ledger, root=str(root), gate=True, out=open(os.devnull, "w"))
    assert nd == [] and [r["signal"] for r in appended] == ["PASS"] and appended[0]["evidence"].startswith("PASS sha256=")
    # a script that fails is an ERROR row, not silence
    (root / "src" / "gen.py").write_text("import sys\nsys.exit(3)\n")
    subprocess.run(["git", "commit", "-qam", "broken generator"], cwd=root, check=True, capture_output=True)
    appended, nd = OC.run(["replay"], ledger, root=str(root), gate=True, out=open(os.devnull, "w"))
    assert nd and nd[0]["signal"] == "ERROR" and "exit 3" in nd[0]["evidence"]


def test_replay_targets_are_registered_and_all_includes_replay():
    AR = load("artifact_registry")
    reg = AR.build_registry(REPO)
    for script, _args, outputs in OC.REPLAY_TARGETS:
        assert os.path.exists(os.path.join(REPO, script))
        assert reg[script]["class"] == "instrument" and reg[script]["regenerates"] == outputs
        for o in outputs:
            assert subprocess.run(["git", "ls-files", "--error-unmatch", o], cwd=REPO, capture_output=True).returncode == 0
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_collect.py"), "--help"],
                       capture_output=True, text=True, cwd=REPO)
    assert "replay" in r.stdout


# REQ-5 -------------------------------------------------------------------

def test_no_stale_row_when_hashes_match(seeded_ledger):
    ledger = seeded_ledger
    OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))
    latest = {}
    for r in OL.read_rows(ledger):            # current state per slot: history legitimately holds past STALE rows
        latest[OL.slot(r)] = r
    rows = list(latest.values())
    stale = [r for r in rows if r["signal"] == "STALE_EVAL"]
    assert stale == [], [r["evidence"] for r in stale]
    with_hashes = [r for r in rows if r["detail"].get("agent_sha256_now")]
    assert with_hashes, "agent rows must carry definition hashes"
    assert all(r["detail"]["agent_sha256_at_eval"] == r["detail"]["agent_sha256_now"]
               for r in with_hashes)


def test_stale_eval_detected_when_definition_changes(seeded_ledger, monkeypatch):
    target = os.path.join(REPO, "agents", "data-reader.md")
    real = OC.read_agent_bytes

    def altered(path):
        b = real(path)
        return b + b"\n<!-- altered by test -->\n" if os.path.abspath(path) == target else b
    monkeypatch.setattr(OC, "read_agent_bytes", altered)
    ledger = seeded_ledger
    appended, _ = OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))
    stale = [r for r in appended if r["signal"] == "STALE_EVAL"]      # this run's rows, not the ledger's history
    assert stale and all(r["artifact"] == "agents/data-reader.md" for r in stale)
    assert all(r["severity"] == "defect" for r in stale)
    assert os.path.exists(target) and b"altered by test" not in real(target)


def test_uncommitted_record_carries_its_definition_hash(tmp_path):
    """A record dispatched this cycle has no record commit yet; its agent.txt
    (R2 dispatcher) names the definition hash it ran against, which beats the
    prior row's hash (the previous definition) and avoids a false STALE_EVAL."""
    rec = tmp_path / "eval-p1-20260907T225619"
    rec.mkdir()
    assert OC.record_definition_hash(str(rec)) is None
    (rec / "agent.txt").write_text("agent: lab-proposer | model: sonnet | definition sha256: " + "ab" * 32 +
                                   " | eval: P-1 | 2026-09-07\n")
    assert OC.record_definition_hash(str(rec)) == "ab" * 32
    (rec / "agent.txt").write_text("agent: independent-verifier | model: haiku | id: ae820cd3825941c40 | eval: V-2\n")
    assert OC.record_definition_hash(str(rec)) is None          # 2026-06 identity stamp


def test_stale_slot_closes_when_definition_matches_again(seeded_ledger, monkeypatch):
    """R2: after a re-dispatch (or a revert) the definition matches a record
    again; the open STALE_EVAL slot must close with a PASS row, else the
    proposer's eval gate would stay shut forever."""
    ledger = seeded_ledger
    target = os.path.join(REPO, "agents", "data-reader.md")
    real = OC.read_agent_bytes
    monkeypatch.setattr(OC, "read_agent_bytes",
                        lambda p: real(p) + b"x" if os.path.abspath(p) == target else real(p))
    appended, _ = OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))
    stale = [r for r in appended if r["signal"] == "STALE_EVAL"]
    assert stale
    monkeypatch.setattr(OC, "read_agent_bytes", real)                 # back in sync
    appended, nd = OC.run(["agent_eval"], ledger, gate=True, out=open(os.devnull, "w"))
    assert nd == []
    closing = [r for r in appended if r["detail"]["subject"].endswith(":staleness")]
    assert closing and all(r["signal"] == "PASS" and r["artifact"] == "agents/data-reader.md" for r in closing)
    assert {r["detail"]["subject"] for r in closing} == {r["detail"]["subject"] for r in stale}
    # a third run in sync is silent again
    appended, _ = OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))
    assert not [r for r in appended if r["detail"]["subject"].endswith(":staleness")]


def test_altered_agent_definition_turns_gate_red(seeded_ledger, monkeypatch):
    ledger = seeded_ledger
    # baseline: clean run, gate green
    _, nd = OC.run(["agent_eval"], ledger, gate=True, out=open(os.devnull, "w"))
    assert nd == []
    target = os.path.join(REPO, "agents", "data-reader.md")
    real = OC.read_agent_bytes
    monkeypatch.setattr(OC, "read_agent_bytes",
                        lambda p: real(p) + b"x" if os.path.abspath(p) == target else real(p))
    _, nd = OC.run(["agent_eval"], ledger, gate=True, out=open(os.devnull, "w"))
    assert nd and nd[0]["signal"] == "STALE_EVAL"


def test_shallow_history_falls_back_to_prior_row(seeded_ledger, monkeypatch):
    ledger = seeded_ledger
    OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))
    monkeypatch.setattr(OC, "git_blob_sha256", lambda *a: None)
    rows, _ = OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))   # rows appended by this run
    assert not [r for r in rows if r["signal"] == "STALE_EVAL"]
    assert not [r for r in rows if r["signal"] == "INCOMPLETE_RECORD" and "cannot compare" in r["evidence"]]


def test_shallow_clone_uses_prior_row_and_still_detects_staleness(seeded_ledger, monkeypatch):
    """CI checkouts are shallow: git history must be treated as unavailable so
    a changed definition is compared with the committed ledger's hash, not
    with HEAD (which would equal the working tree and mask the change)."""
    ledger = seeded_ledger
    OC.run(["agent_eval"], ledger, out=open(os.devnull, "w"))          # baseline (seeded, as CI is)

    def eval_rows(artifact):
        return [r for r in OL.read_rows(ledger) if r["artifact"] == artifact
                and ":staleness" not in r["detail"]["subject"]]
    baseline = len(eval_rows("agents/data-reader.md"))     # the committed history (grows with every re-dispatch)
    monkeypatch.setattr(OC, "is_shallow", lambda root: True)
    calls = []
    real_show = OC.git_blob_sha256
    monkeypatch.setattr(OC, "git_blob_sha256", lambda *a: calls.append(a) or real_show(*a))
    target = os.path.join(REPO, "agents", "data-reader.md")
    real = OC.read_agent_bytes
    monkeypatch.setattr(OC, "read_agent_bytes",
                        lambda p: real(p) + b"x" if os.path.abspath(p) == target else real(p))
    _, nd = OC.run(["agent_eval"], ledger, gate=True, out=open(os.devnull, "w"))
    assert calls == [], "shallow clone must not consult git show"
    rows = OL.read_rows(ledger)
    assert nd and nd[0]["signal"] == "STALE_EVAL" and nd[0]["artifact"] == "agents/data-reader.md"
    changed_eval_rows = eval_rows("agents/data-reader.md")
    assert len(changed_eval_rows) == baseline + 1           # exactly one new state: the altered one
    last = changed_eval_rows[-1]["detail"]
    assert last["record_commit"] is None
    # without git history the hash at eval comes from the record's own agent.txt (an R2
    # record) or, for a 2026-06 record, from the prior committed row -- never from HEAD
    g = OC.load_grader(REPO)
    stamped = OC.record_definition_hash(os.path.join(REPO, g.record_dir("D-1+D-2")))
    assert last["agent_sha256_at_eval"] == stamped if stamped else last["at_eval_from_prior_row"] is True
    # unchanged definitions did not produce noise rows despite the shallow clone
    dupes = [r for r in rows if r["artifact"] == "agents/research-scout.md" and ":staleness" not in r["detail"]["subject"]]
    assert len(dupes) == 1


def test_adopt_merges_only_new_states(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    art = str(tmp_path / "ci.jsonl")
    reg = {"f": fake_source("PASS")}
    OC.run(["f"], ledger, registry=reg, out=open(os.devnull, "w"))
    OC.run(["f"], art, registry=reg, out=open(os.devnull, "w"))                 # same state
    OC.run(["g"], art, registry={"g": fake_source("FAIL", artifact="src/g.py")}, out=open(os.devnull, "w"))
    # history inside the artifact must not be replayed: g flipped FAIL -> PASS
    # there, so only its latest state (PASS) may be adopted
    OC.run(["g"], art, registry={"g": fake_source("PASS", artifact="src/g.py")}, out=open(os.devnull, "w"))
    # the artifact rows were observed EARLIER than the ledger's last row
    rows = OL.read_rows(art)
    for r in rows:
        r["ts"] = "2026-01-01T00:00:00Z"
    with open(art, "w") as fh:
        fh.write("".join(json.dumps(r) + "\n" for r in rows))
    appended = OC.adopt(ledger, art, out=open(os.devnull, "w"))
    assert [(r["artifact"], r["signal"]) for r in appended] == [("src/g.py", "PASS")]
    assert len(OL.read_rows(ledger)) == 2
    assert OL.verify_ledger(ledger) == []                      # ts re-stamped, still monotonic
    adopted = OL.read_rows(ledger)[-1]
    assert adopted["ts"] != "2026-01-01T00:00:00Z"
    assert adopted["executor"] == rows[-1]["executor"]         # observer identity kept
    assert OC.adopt(ledger, art, out=open(os.devnull, "w")) == []
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_collect.py"),
                        "--adopt", art, "--ledger", ledger], capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0 and "adopted 0 of" in r.stdout


# REQ-6 -------------------------------------------------------------------

def test_gate_fails_on_new_defect(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    _, nd = OC.run(["f"], ledger, gate=True, registry={"f": fake_source("FAIL")}, out=open(os.devnull, "w"))
    assert len(nd) == 1 and nd[0]["severity"] == "defect"


def test_gate_passes_on_known_defect(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    reg = {"f": fake_source("FAIL")}
    OC.run(["f"], ledger, gate=True, registry=reg, out=open(os.devnull, "w"))
    _, nd = OC.run(["f"], ledger, gate=True, registry=reg, out=open(os.devnull, "w"))
    assert nd == []
    rows = OL.read_rows(ledger)
    assert len(rows) == 1 and rows[0]["signal"] == "FAIL"   # still visible, still open


def test_gate_fails_on_reopened_defect(tmp_path):
    """FAIL -> PASS -> identical FAIL: the third run is a regression and must
    trip the gate even though that exact state was seen before (review #1)."""
    ledger = str(tmp_path / "l.jsonl")
    quiet = open(os.devnull, "w")
    OC.run(["f"], ledger, gate=True, registry={"f": fake_source("FAIL")}, out=quiet)
    OC.run(["f"], ledger, gate=True, registry={"f": fake_source("PASS")}, out=quiet)
    _, nd = OC.run(["f"], ledger, gate=True, registry={"f": fake_source("FAIL")}, out=quiet)
    assert len(nd) == 1
    assert len(OL.read_rows(ledger)) == 3


def test_verify_evidence_falls_back_to_stderr():
    signal, sha, evidence = OC.parse_verify_output(
        "", 1, "Traceback (most recent call last):\n  ...\nValueError: data_draws.csv: expected 252 rows, got 380\n")
    assert signal == "FAIL" and sha is None
    assert evidence == "ValueError: data_draws.csv: expected 252 rows, got 380"


def test_gate_passes_when_clean(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    _, nd = OC.run(["f"], ledger, gate=True, registry={"f": fake_source("PASS")}, out=open(os.devnull, "w"))
    assert nd == []


def test_gate_cli_exit_codes(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    cli = [sys.executable, os.path.join(REPO, "src", "outcome_collect.py")]
    r = subprocess.run(cli + ["--sources", "ledger_integrity", "--gate", "--ledger", ledger],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode in (0, 1), r.stdout + r.stderr
    assert "appended" in r.stdout
    r = subprocess.run(cli + ["--sources", "nope", "--gate", "--ledger", ledger],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 1 and "unknown source" in r.stdout
    r = subprocess.run(cli, capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 2


# REQ-7 / §7 ----------------------------------------------------------------

def test_collector_writes_only_ledger(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    before = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True).stdout
    OC.run(["agent_eval", "ledger_integrity"], ledger, out=open(os.devnull, "w"))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True).stdout
    assert before == after
    assert os.path.exists(ledger)


def test_missing_source_yields_error_row(tmp_path):
    def boom(ctx):
        raise RuntimeError("source exploded")
    ledger = str(tmp_path / "l.jsonl")
    _, nd = OC.run(["b"], ledger, gate=True, registry={"b": boom}, out=open(os.devnull, "w"))
    rows = OL.read_rows(ledger)
    assert rows[0]["source"] == "collector" and rows[0]["signal"] == "ERROR"
    assert "source exploded" in rows[0]["evidence"] and nd


def test_row_contains_no_raw_stdout(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    OC.run(list(OC.FAST), ledger, out=open(os.devnull, "w"))
    for r in OL.read_rows(ledger):
        assert len(r["evidence"]) <= OL.EVIDENCE_MAX
        assert "stdout" not in r["detail"]


def test_env_override_path(tmp_path):
    ledger = str(tmp_path / "env.jsonl")
    env = dict(os.environ, LAB_OUTCOME_LEDGER=ledger)
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_collect.py"),
                        "--sources", "ledger_integrity"], capture_output=True, text=True, cwd=REPO, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.path.exists(ledger) and ledger in r.stdout


def test_dry_run_appends_nothing(tmp_path):
    ledger = str(tmp_path / "l.jsonl")
    OC.run(["f"], ledger, dry_run=True, registry={"f": fake_source("FAIL")}, out=open(os.devnull, "w"))
    assert not os.path.exists(ledger)


def test_refuses_invalid_ledger(tmp_path):
    ledger = tmp_path / "bad.jsonl"
    ledger.write_text('{"schema_version": 1}\n')
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_collect.py"),
                        "--sources", "ledger_integrity", "--ledger", str(ledger)],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 2 and "refusing" in r.stdout
