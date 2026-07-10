#!/usr/bin/env python3
"""Tests for the ledger tooling: src/verify_ledger_integrity.py and
tools/snapshot_commitment.py.

Run: python3 -m pytest tests/test_ledger_tools.py -q
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def make_lab(root, run_rows, mult_rows, commitment="# header\n",
             admission=""):
    """Both tools resolve the repo root relative to their own file, so the
    fixture copies them into a synthetic tree."""
    for d in ("src", "tools", "results"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    shutil.copy(os.path.join(REPO, "src", "verify_ledger_integrity.py"),
                os.path.join(root, "src"))
    shutil.copy(os.path.join(REPO, "tools", "snapshot_commitment.py"),
                os.path.join(root, "tools"))
    res = os.path.join(root, "results")
    with open(os.path.join(res, "run_ledger.jsonl"), "w") as f:
        for r in run_rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(res, "multiplicity_ledger.jsonl"), "w") as f:
        for r in mult_rows:
            f.write(json.dumps(r) + "\n")
    open(os.path.join(res, "commitment_ledger.txt"), "w").write(commitment)
    open(os.path.join(res, "admission_log.txt"), "w").write(admission)


def verify(root, *args):
    return subprocess.run(
        [sys.executable, os.path.join("src", "verify_ledger_integrity.py"),
         *args], cwd=root, capture_output=True, text=True)


GOOD_RUN = {"run_id": "r1", "date": "2026-01-01", "script": "src/x.py",
            "output": "results/out.json",
            "output_sha256": {"results/out.json": None}}
GOOD_TEST = {"run_id": "r1", "dataset": "toy", "claim_type": "marginal",
             "method": "ks", "raw_p": 0.5, "m_perm": 49, "p_floor": 0.02,
             "family_id": "fam", "within_run_m": 1, "data_filter": "all",
             "global_m": 1, "row_type": "test"}


# --------------------------------------------------------------- verifier
def test_verifier_passes_on_real_repo():
    r = verify(REPO, "--quiet")
    assert r.returncode == 0, r.stdout
    assert "LEDGER INTEGRITY: OK" in r.stdout


def test_verifier_detects_duplicate_run_id(tmp_path):
    make_lab(str(tmp_path), [GOOD_RUN, GOOD_RUN], [GOOD_TEST])
    r = verify(str(tmp_path))
    assert r.returncode == 1
    assert "duplicate run_ids" in r.stdout


def test_verifier_detects_hash_mismatch(tmp_path):
    root = str(tmp_path)
    run = dict(GOOD_RUN,
               output_sha256={"results/out.json": "0" * 16})
    make_lab(root, [run], [GOOD_TEST])
    open(os.path.join(root, "results", "out.json"), "w").write("{}")
    r = verify(root)
    assert r.returncode == 1
    assert "hash mismatch" in r.stdout


def test_verifier_detects_bad_raw_p_but_allows_gate_based(tmp_path):
    bad = dict(GOOD_TEST, raw_p=1.7)
    gate = dict(GOOD_TEST, raw_p=None, p_floor=None, m_perm=None,
                gate_based=True, claim_type="equation_discovery")
    make_lab(str(tmp_path), [GOOD_RUN], [gate])
    assert verify(str(tmp_path)).returncode == 0
    make_lab(str(tmp_path), [GOOD_RUN], [bad])
    r = verify(str(tmp_path))
    assert r.returncode == 1 and "raw_p invalid" in r.stdout


def test_verifier_detects_malformed_json(tmp_path):
    make_lab(str(tmp_path), [GOOD_RUN], [GOOD_TEST])
    with open(os.path.join(str(tmp_path), "results",
                           "run_ledger.jsonl"), "a") as f:
        f.write("this is not json\n")
    r = verify(str(tmp_path))
    assert r.returncode == 1 and "not valid JSON" in r.stdout


def test_verifier_accepts_fresh_install(tmp_path):
    make_lab(str(tmp_path), [], [])
    r = verify(str(tmp_path))
    assert r.returncode == 0
    assert "fresh install" in r.stdout


def test_verifier_accepts_sealed_commitment_rows(tmp_path):
    commit = ("# header\n"
              "aaaaaaaaaaaaaaaa  ./src/x.py\n"
              "bbbbbbbbbbbbbbbb  evals/x/REGISTRATION.md\n"
              "cccccccccccccccc  [SEALED] evals/x/answer_key/truth.md\n")
    make_lab(str(tmp_path), [GOOD_RUN], [GOOD_TEST], commitment=commit)
    r = verify(str(tmp_path))
    assert r.returncode == 0, r.stdout


# --------------------------------------------------------------- snapshot
def snap(root, *args):
    return subprocess.run(
        [sys.executable, os.path.join("tools", "snapshot_commitment.py"),
         *args], cwd=root, capture_output=True, text=True)


def test_snapshot_appends_and_is_delta_only(tmp_path):
    root = str(tmp_path)
    make_lab(root, [GOOD_RUN], [GOOD_TEST])
    os.makedirs(os.path.join(root, "docs"))
    open(os.path.join(root, "docs", "a.md"), "w").write("v1")
    before = open(os.path.join(root, "results",
                               "commitment_ledger.txt")).read()
    r = snap(root, "first snapshot")
    assert r.returncode == 0, r.stderr
    after = open(os.path.join(root, "results",
                              "commitment_ledger.txt")).read()
    assert after.startswith(before), "must be append-only"
    assert "./docs/a.md" in after and "first snapshot" in after

    # unchanged tree -> second snapshot adds header only, zero rows
    r2 = snap(root, "second snapshot")
    assert "0 rows" in r2.stdout or "0 changed" in \
        open(os.path.join(root, "results", "commitment_ledger.txt")).read()

    # change one file -> exactly that row is appended
    open(os.path.join(root, "docs", "a.md"), "w").write("v2")
    snap(root, "third snapshot")
    tail = open(os.path.join(root, "results",
                             "commitment_ledger.txt")).read().split(
        "third snapshot")[1]
    assert "./docs/a.md" in tail
    assert "./src/verify_ledger_integrity.py" not in tail


def test_snapshot_never_hashes_secrets(tmp_path):
    root = str(tmp_path)
    make_lab(root, [GOOD_RUN], [GOOD_TEST])
    os.makedirs(os.path.join(root, "webapp"))
    open(os.path.join(root, "webapp", "config.local.json"),
         "w").write('{"api_keys": {}}')
    open(os.path.join(root, "webapp", ".keysalt"), "w").write("salt")
    snap(root, "with secrets present")
    text = open(os.path.join(root, "results",
                             "commitment_ledger.txt")).read()
    assert "config.local.json" not in text
    assert ".keysalt" not in text


def test_snapshot_dry_run_appends_nothing(tmp_path):
    root = str(tmp_path)
    make_lab(root, [GOOD_RUN], [GOOD_TEST])
    before = open(os.path.join(root, "results",
                               "commitment_ledger.txt")).read()
    r = snap(root, "dry", "--dry-run")
    assert r.returncode == 0
    assert open(os.path.join(root, "results",
                             "commitment_ledger.txt")).read() == before


def test_snapshot_hash_chain_verifies_and_breaks(tmp_path):
    """Each snapshot commits to all prior ledger bytes; verifier must accept
    an intact chain and FAIL when earlier bytes are retroactively edited."""
    root = str(tmp_path)
    make_lab(root, [GOOD_RUN], [GOOD_TEST])
    os.makedirs(os.path.join(root, "docs"))
    doc = os.path.join(root, "docs", "a.md")
    open(doc, "w").write("v1")
    assert snap(root, "one").returncode == 0
    open(doc, "w").write("v2")
    r2 = snap(root, "two")
    assert r2.returncode == 0
    assert "anchor" in r2.stdout, "post-append digest must be printed"
    ok = verify(root)
    assert ok.returncode == 0 and "hash chain intact across 2" in ok.stdout

    ledger = os.path.join(root, "results", "commitment_ledger.txt")
    text = open(ledger).read()
    open(ledger, "w").write(text.replace("one", "0ne", 1))  # retro-edit
    broken = verify(root)
    assert broken.returncode == 1
    assert "hash chain BROKEN" in broken.stdout

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
