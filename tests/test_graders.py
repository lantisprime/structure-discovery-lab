#!/usr/bin/env python3
"""Regression: every recorded agent-eval dispatch regrades cleanly with the
mechanical graders — no record may regress to FAIL, the rich records must
still PASS outright, and grading must never mutate a dispatch record.

Run: python3 -m pytest tests/test_graders.py -q
"""
import importlib.util
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_grader():
    spec = importlib.util.spec_from_file_location(
        "grade_agent_eval", os.path.join(REPO, "src", "grade_agent_eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


grader = load_grader()

# Records rich enough to re-verify end-to-end today — these must PASS.
MUST_PASS = {"V-1", "O-1", "R-1", "E-1", "Q-1", "Q-3",
             "Z-V1", "Z-V2", "Z-O1"}
# Thin records (no report.md saved on 2026-06-11) — INCOMPLETE_RECORD is the
# honest grade; they must never regress to FAIL.
MAY_BE_INCOMPLETE = {"V-2", "V-3", "D-1+D-2", "A-2", "X-2"}


@pytest.mark.parametrize("eval_id", sorted(grader.RECORDS))
def test_record_regrades_cleanly(eval_id):
    run_dir = os.path.join(REPO, grader.RECORDS[eval_id])
    if not os.path.isdir(run_dir):
        pytest.skip(f"record absent (clean-ledger install): {run_dir}")
    res = grader.grade_one(eval_id, run_dir)
    assert res["grade"] != "FAIL", res
    if eval_id in MUST_PASS:
        assert res["grade"] == "PASS", res
    else:
        assert eval_id in MAY_BE_INCOMPLETE
        assert res["grade"] in ("PASS", "INCOMPLETE_RECORD"), res
    # never contradict the grade on file
    if res.get("recorded_grade") in ("PASS", "PASS*"):
        assert res["grade"] != "FAIL"


def test_grading_never_mutates_records():
    before = {}
    for rel in grader.RECORDS.values():
        d = os.path.join(REPO, rel)
        if os.path.isdir(d):
            before[rel] = sorted(os.listdir(d))
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "src", "grade_agent_eval.py"),
                        "--all"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    for rel, listing in before.items():
        assert sorted(os.listdir(os.path.join(REPO, rel))) == listing, \
            f"grading mutated the dispatch record {rel}"


def test_grader_detects_a_real_failure(tmp_path):
    """Negative control: a Q-3 record whose floor discipline is violated
    (a below-floor coefficient carries an estimate) must FAIL."""
    import json
    import shutil
    src = os.path.join(REPO, grader.RECORDS["Q-3"])
    if not os.path.isdir(src):
        pytest.skip("Q-3 record absent")
    dst = str(tmp_path / "q3")
    shutil.copytree(src, dst)
    fit = os.path.join(dst, "eq_fit_results.json")
    j = json.load(open(fit))
    for c in j["claims"].values():
        for coef in c.get("coefficients", []):
            if coef.get("below_floor"):
                coef["estimate"] = 0.123   # the violation
    json.dump(j, open(fit, "w"))
    res = grader.GRADERS["Q-3"](dst)
    assert res["grade"] == "FAIL"
    assert res["checks"]["floor_discipline_enforced"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
