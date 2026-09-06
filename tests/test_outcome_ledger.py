#!/usr/bin/env python3
"""R0-S1: outcome ledger schema, atomic append, dedup, --verify.

Run: python3 -m pytest tests/test_outcome_ledger.py -q
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load():
    spec = importlib.util.spec_from_file_location(
        "outcome_ledger", os.path.join(REPO, "src", "outcome_ledger.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OL = load()


def row(**over):
    base = dict(source="design_verifier", artifact="docs/design_map",
                artifact_class="design", signal="PASS",
                evidence="design verifier: PASS | 0 violations",
                detail={"violations": 0}, ts="2026-09-06T10:00:00Z",
                commit="abc1234", executor="tester@host")
    base.update(over)
    return OL.make_row(**base)


# REQ-1 -------------------------------------------------------------------

def test_schema_accepts_valid_row():
    r = row()
    OL.validate_row(r)
    assert r["severity"] == "info"
    assert OL.make_row(**{**dict(source="pytest", artifact="tests/", artifact_class="suite",
                                 signal="FAIL", evidence="1 failed", detail={},
                                 ts="2026-09-06T10:00:00Z", commit="x", executor="e")})["severity"] == "defect"


@pytest.mark.parametrize("field", OL.REQUIRED)
def test_schema_rejects_each_missing_field(field):
    r = row()
    del r[field]
    with pytest.raises(ValueError) as e:
        OL.validate_row(r)
    assert field in str(e.value)


def test_verify_rejects_unknown_enum(tmp_path):
    p = tmp_path / "l.jsonl"
    r = row()
    r["signal"] = "MAYBE"
    p.write_text(json.dumps(r) + "\n")
    probs = OL.verify_ledger(str(p))
    assert probs and "signal" in probs[0]
    r = row()
    r["severity"] = "defect"  # inconsistent with PASS
    p.write_text(json.dumps(r) + "\n")
    assert any("severity" in x for x in OL.verify_ledger(str(p)))


def test_verify_rejects_out_of_order_ts(tmp_path):
    p = tmp_path / "l.jsonl"
    OL.append_rows(str(p), [row(ts="2026-09-06T10:00:05Z")])
    OL.append_rows(str(p), [row(signal="FAIL", evidence="x", ts="2026-09-06T10:00:01Z")])
    probs = OL.verify_ledger(str(p))
    assert probs and "earlier than previous" in probs[0]


def test_verify_ok_on_missing_and_empty(tmp_path):
    assert OL.verify_ledger(str(tmp_path / "none.jsonl")) == []
    p = tmp_path / "empty.jsonl"
    p.write_bytes(b"")
    assert OL.verify_ledger(str(p)) == []


def test_verify_cli_exit_codes(tmp_path):
    p = tmp_path / "l.jsonl"
    OL.append_rows(str(p), [row()])
    good = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_ledger.py"),
                           "--verify", "--ledger", str(p)], capture_output=True, text=True)
    assert good.returncode == 0 and "OUTCOME LEDGER: OK (1 rows)" in good.stdout
    p.write_text('{"schema_version": 1}\n')
    bad = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_ledger.py"),
                          "--verify", "--ledger", str(p)], capture_output=True, text=True)
    assert bad.returncode == 1 and "OUTCOME LEDGER: FAIL" in bad.stdout
    env = dict(os.environ, LAB_OUTCOME_LEDGER=str(p))
    via_env = subprocess.run([sys.executable, os.path.join(REPO, "src", "outcome_ledger.py"),
                              "--verify"], capture_output=True, text=True, env=env)
    assert via_env.returncode == 1


# REQ-2 -------------------------------------------------------------------

def test_append_preserves_prior_bytes(tmp_path):
    p = tmp_path / "l.jsonl"
    OL.append_rows(str(p), [row()])
    before = p.read_bytes()
    OL.append_rows(str(p), [row(signal="FAIL", evidence="1 violation", detail={"violations": 1})])
    after = p.read_bytes()
    assert after.startswith(before)
    assert after.count(b"\n") == 2
    assert not [f for f in os.listdir(tmp_path) if f.startswith(".outcome_ledger.")]


def test_append_failure_leaves_prior_file_intact(tmp_path, monkeypatch):
    p = tmp_path / "l.jsonl"
    OL.append_rows(str(p), [row()])
    before = p.read_bytes()

    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(OL.os, "replace", boom)
    with pytest.raises(OSError):
        OL.append_rows(str(p), [row(signal="FAIL", evidence="x")])
    assert p.read_bytes() == before
    assert not [f for f in os.listdir(tmp_path) if f.startswith(".outcome_ledger.")]


def test_append_rejects_invalid_row_before_writing(tmp_path):
    p = tmp_path / "l.jsonl"
    bad = row()
    bad["source"] = "nope"
    with pytest.raises(ValueError):
        OL.append_rows(str(p), [bad])
    assert not p.exists()


# REQ-3 -------------------------------------------------------------------

def test_dedup_skips_identical_state(tmp_path):
    p = tmp_path / "l.jsonl"
    assert len(OL.append_rows(str(p), [row()])) == 1
    again = OL.append_rows(str(p), [row(ts="2026-09-06T11:00:00Z", commit="other")])
    assert again == []
    assert len(OL.read_rows(str(p))) == 1


def test_dedup_appends_on_state_change(tmp_path):
    p = tmp_path / "l.jsonl"
    OL.append_rows(str(p), [row()])
    changed = OL.append_rows(str(p), [row(detail={"violations": 2}, signal="FAIL", evidence="2")])
    assert len(changed) == 1
    back = OL.append_rows(str(p), [row()])  # state flips back -> new row
    assert len(back) == 1
    assert len(OL.read_rows(str(p))) == 3


def test_dedup_slot_includes_detail_subject(tmp_path):
    p = tmp_path / "l.jsonl"
    v1 = row(source="agent_eval", artifact="agents/independent-verifier.md", artifact_class="agent",
             detail={"subject": "V-1", "checks": {"a": True}})
    v2 = row(source="agent_eval", artifact="agents/independent-verifier.md", artifact_class="agent",
             detail={"subject": "V-2", "checks": {"b": True}})
    assert len(OL.append_rows(str(p), [v1, v2])) == 2
    assert OL.append_rows(str(p), [v1, v2]) == []          # no thrash on re-run
    assert len(OL.read_rows(str(p))) == 2


def test_dedup_ignores_provenance_detail_keys(tmp_path):
    p = tmp_path / "l.jsonl"
    a = row(source="agent_eval", artifact="agents/x.md", artifact_class="agent",
            detail={"subject": "V-1", "checks": {"a": True}, "record_commit": "6da211a",
                    "at_eval_from_prior_row": False})
    b = row(source="agent_eval", artifact="agents/x.md", artifact_class="agent",
            detail={"subject": "V-1", "checks": {"a": True}, "record_commit": "7548b95",
                    "at_eval_from_prior_row": True})
    assert len(OL.append_rows(str(p), [a])) == 1
    assert OL.append_rows(str(p), [b]) == []          # same state, different provenance
    c = row(source="agent_eval", artifact="agents/x.md", artifact_class="agent",
            detail={"subject": "V-1", "checks": {"a": False}, "record_commit": "7548b95"})
    assert len(OL.append_rows(str(p), [c])) == 1      # real state change still lands


def test_dedup_is_per_source_artifact(tmp_path):
    p = tmp_path / "l.jsonl"
    a = row(artifact="src/a.py", source="verify_entrypoint", artifact_class="instrument")
    b = row(artifact="src/b.py", source="verify_entrypoint", artifact_class="instrument")
    assert len(OL.append_rows(str(p), [a, b, a])) == 2
