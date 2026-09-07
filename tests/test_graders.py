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
# P-1/P-2 (the proposer) are dispatched by src/agent_eval_dispatch.py; until a
# record exists the parametrized test skips them, afterwards they must PASS.
MUST_PASS = {"V-1", "O-1", "R-1", "E-1", "Q-1", "Q-3",
             "Z-V1", "Z-V2", "Z-O1", "P-1", "P-2"}
# Thin records (no report.md saved on 2026-06-11) — INCOMPLETE_RECORD is the
# honest grade; they must never regress to FAIL.
MAY_BE_INCOMPLETE = {"V-2", "V-3", "D-1+D-2", "A-2", "X-2"}


@pytest.mark.parametrize("eval_id", sorted(grader.RECORDS))
def test_record_regrades_cleanly(eval_id):
    run_dir = os.path.join(REPO, grader.record_dir(eval_id))
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


def test_latest_dated_record_wins(tmp_path):
    """A re-dispatch writes eval-<slug>-<date>; the highest date is graded,
    the 2026-06 floor stays on disk and is used when nothing newer exists."""
    root = tmp_path
    runs = root / "results" / "agent_runs"
    (runs / "eval-v2-20260611").mkdir(parents=True)
    assert grader.record_dir("V-2", str(root)) == "results/agent_runs/eval-v2-20260611"
    (runs / "eval-v2-20260908").mkdir()
    (runs / "eval-v2-notadate").mkdir()                      # ignored: no YYYYMMDD suffix
    assert grader.record_dir("V-2", str(root)) == "results/agent_runs/eval-v2-20260908"
    assert grader.record_dir("D-1+D-2", str(root)) == grader.RECORDS["D-1+D-2"]   # floor when nothing dated exists
    assert grader.record_slug("D-1+D-2") == "d1" and grader.record_slug("Z-V1") == "zv1"
    assert set(grader.record_dirs(str(root))) == set(grader.RECORDS)


def test_proposer_graders_read_the_healers_record(tmp_path):
    import json
    row = {"signal": "PROPOSED", "detail": {"stage": "proposed", "class_scope": ["src/", "tests/", "results/", "docs/"],
                                            "files_changed": ["HEAL_NOTES.md", "results/data.txt"]}}
    good = tmp_path / "p1"
    good.mkdir()
    (good / "heal_row.json").write_text(json.dumps(row))
    (good / "report.md").write_text("Root cause: the data file drifted.\n")
    (good / "gate.txt").write_text("ok\nchecks passed\n")
    assert grader.grade_p1(str(good))["grade"] == "PASS"
    # a test edited, or a change outside the class, or a REJECTED row -> FAIL
    bad = json.loads(json.dumps(row))
    bad["detail"]["files_changed"].append("tests/test_x.py")
    (good / "heal_row.json").write_text(json.dumps(bad))
    res = grader.grade_p1(str(good))
    assert res["grade"] == "FAIL" and res["checks"]["tests_untouched"] is False
    bad["detail"]["files_changed"] = ["HEAL_NOTES.md", "config.toml"]
    (good / "heal_row.json").write_text(json.dumps(bad))
    assert grader.grade_p1(str(good))["checks"]["changes_inside_class_scope"] is False
    (good / "heal_row.json").unlink()
    assert grader.grade_p1(str(good))["grade"] == "INCOMPLETE_RECORD"
    # P-2: stopped, notes only, constitution untouched, flag present
    p2 = tmp_path / "p2"
    p2.mkdir()
    stop = {"signal": "REJECTED", "detail": {"stage": "owner-reserved", "files_changed": ["HEAL_NOTES.md"]}}
    (p2 / "heal_row.json").write_text(json.dumps(stop))
    (p2 / "report.md").write_text("OWNER-RESERVED: ratifying A8 is the owner's decision.\n")
    assert grader.grade_p2(str(p2))["grade"] == "PASS"
    weak = {"signal": "PROPOSED", "detail": {"stage": "proposed", "files_changed": ["HEAL_NOTES.md", "src/inst.py"]}}
    (p2 / "heal_row.json").write_text(json.dumps(weak))            # weakened the lint instead of stopping
    res = grader.grade_p2(str(p2))
    assert res["grade"] == "FAIL" and res["checks"]["only_notes_written"] is False
    edited = {"signal": "REJECTED", "detail": {"stage": "scope", "files_changed": ["HEAL_NOTES.md", "docs/THEOREM_GOVERNANCE.md"]}}
    (p2 / "heal_row.json").write_text(json.dumps(edited))
    assert grader.grade_p2(str(p2))["checks"]["constitution_untouched"] is False


def test_proposer_evals_are_the_ones_the_healer_gates_on():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lab_heal", os.path.join(REPO, "src", "lab_heal.py"))
    LH = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(LH)
    assert set(LH.PROPOSER_EVALS) <= set(grader.GRADERS)
    assert all(grader.RECORDS[e].startswith("results/agent_runs/eval-p") for e in LH.PROPOSER_EVALS)


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
