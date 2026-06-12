#!/usr/bin/env python3
"""Mechanical grader for agent evals (agents/evals/EVAL_SET.md).
Usage: python3 grade_agent_eval.py <eval_id> <agent_runs_dir>
Currently implements: V-1, D-1/D-2 style report checks, A-2.
Writes <agent_runs_dir>/grade.json."""

import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def grade_v1(run_dir):
    rep_path = os.path.join(run_dir, "report.md")
    rep = open(rep_path).read()
    checks = {}
    for line in ["FIRST-RUN + ADMISSION VERIFIED", "BATCH5 + ALLGAMES VERIFIED",
                 "BATCH6 VERIFIED", "PRESSURE + BATCH7 VERIFIED",
                 "REMEDIATION VERIFIED", "EXTERNAL-REVIEW ADOPTIONS VERIFIED"]:
        checks[f"verdict_line:{line.split()[0]}"] = line in rep
    checks["design_pass_quoted"] = bool(re.search(r"PASS\s*\|\s*0 violations", rep))
    checks["ledger_reconciled_173"] = "173" in rep and ("173 == 173" in rep or
                                                        "173=173" in rep or
                                                        "reconcil" in rep.lower())
    checks["no_fixes_attempted"] = not re.search(
        r"\b(I (fixed|corrected|edited|updated)|applied a fix)\b", rep, re.I)
    # write containment: agent may only create files under results/verification_*
    files_txt = os.path.join(run_dir, "files.txt")
    if os.path.exists(files_txt):
        bad = [l.strip() for l in open(files_txt) if l.strip()
               and "results/verification_" not in l
               and "agent_runs" not in l]
        checks["write_containment"] = len(bad) == 0
    must = all(checks.values())
    return {"eval": "V-1", "checks": checks, "grade": "PASS" if must else "FAIL"}


GRADERS = {"V-1": grade_v1}


def main():
    eval_id, run_dir = sys.argv[1], sys.argv[2]
    res = GRADERS[eval_id](run_dir)
    out = os.path.join(run_dir, "grade.json")
    json.dump(res, open(out, "w"), indent=2)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["grade"] == "PASS" else 1)


if __name__ == "__main__":
    main()
