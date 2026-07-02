#!/usr/bin/env python3
"""Scorer for eq_eval_set_v1. Run ONLY after the lab's verdicts JSON is
hash-committed (SEAL_NOTICE). Compares results/eq_eval_verdicts.json against
answer_key/ground_truth.json.

Usage: score_eq_eval.py [path/to/eq_eval_verdicts.json]
Writes results/eq_eval_score.md (lab root) + prints the table.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..")
LAB = os.path.join(PACK, "..", "..")

ACCEPT = {"CANDIDATE_EQUATION", "MECHANISM_CONSISTENT", "MECHANISM_SUPPORTED",
          "PARTIAL_MODEL"}
NULLISH = {"FAILED_EQUATION_SEARCH", "REFUSED_NULL_DETECTION",
           "FAIL_corrected"}


def ci_contains(ci, truth_period):
    lo, hi = sorted(ci)
    f = 1.0 / truth_period
    return lo <= f <= hi or lo <= truth_period <= hi   # accept either axis


def score_unit(uid, v, gt):
    cls = gt["expected_class"]
    verdict = v.get("verdict", "MISSING")
    accepted = verdict in ACCEPT
    out = {"verdict": verdict, "expected_class": cls, "marks": []}

    if cls == "null":
        out["result"] = "TN" if not accepted else "FP"
        if accepted:
            out["marks"].append("FALSE POSITIVE: " + gt["scoring"])
        return out

    if cls == "trap":                      # unit_12 era-bounded
        era_ok = bool(v.get("era_flag"))
        if accepted and not era_ok:
            out["result"] = "OVERCLAIM"
            out["marks"].append("pooled candidate without era language")
        else:
            out["result"] = "TP" if era_ok else "TN"
        return out

    # detect / borderline
    truths = gt["params"].get("periods_d") or \
        [gt["params"].get("period_d") or gt["params"].get("main_period_d")]
    if not accepted:
        if cls == "borderline":
            out["result"] = "TN-borderline" if v.get("power_floor_amp") \
                else "MISS (no power statement)"
        else:
            out["result"] = "MISS" if not v.get("power_floor_amp") else \
                "MISS-with-power-statement (lesser)"
        return out
    cis = v.get("period_cis") or []
    got = [any(ci_contains(ci, t) for ci in cis) for t in truths]
    if all(got):
        out["result"] = "TP"
    elif any(got):
        out["result"] = "TP-partial"
        out["marks"].append("one planted line not covered by any CI")
    else:
        out["result"] = "FALSE_RECOVERY"
        out["marks"].append("no reported CI contains any true period")
    # unit_11 scan behaviors
    if uid == "unit_11":
        scan = v.get("residual_scan", {})
        if scan.get("no_whitelist_p", 1) > 0.05:
            out["marks"].append("SCAN MISS: hidden 9.3d line not flagged")
        if scan.get("whitelisted_p", 1) <= 0.05:
            out["marks"].append("SCAN FALSE ALARM after whitelist")
    return out


def main():
    vpath = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(LAB, "results", "eq_eval_verdicts.json")
    V = json.load(open(vpath))
    GT = json.load(open(os.path.join(PACK, "answer_key",
                                     "ground_truth.json")))["units"]
    rows, tally = [], {}
    for uid in sorted(GT):
        r = score_unit(uid, V.get(uid, {}), GT[uid])
        tally[r["result"]] = tally.get(r["result"], 0) + 1
        rows.append((uid, r))
    lines = ["# eq_eval_set_v1 score", "",
             "| unit | expected | verdict | result | marks |", "|---|---|---|---|---|"]
    for uid, r in rows:
        lines.append(f"| {uid} | {r['expected_class']} | {r['verdict']} | "
                     f"**{r['result']}** | {'; '.join(r['marks']) or '—'} |")
    lines += ["", f"Tally: {json.dumps(tally)}",
              "", "Pass targets: 0 FP, 0 FALSE_RECOVERY, 0 OVERCLAIM; "
              ">=3 of 4 detect-class TP (06,09,10,11); unit_11 scan marks clean."]
    out = "\n".join(lines)
    dest = os.path.join(LAB, "results", "eq_eval_score.md")
    if os.path.isdir(os.path.dirname(dest)):
        open(dest, "w").write(out)
    else:  # standalone/smoke use: write next to the verdicts file
        open(os.path.join(os.path.dirname(os.path.abspath(vpath)),
                          "eq_eval_score.md"), "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
