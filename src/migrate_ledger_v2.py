#!/usr/bin/env python3
"""Ledger schema migration v1 -> v2 (AUDIT_CORRECTNESS_2026-07-02 C-1, G-5, F6).

Changes, all logged per-row in "migration_note":
  1. row_type field: "test" (has run_id) | "family_charge" (has m_delta)
  2. batch6 rows marked superseded_by="batch67_r2" (same statistics, same data,
     floor-compliant m; RESULTS_BATCH6_7_RERUN.md) -> excluded from global m
  3. lambda-max rows: m_perm corrected 399 -> 999 (code audit: remediation_r1
     run_floors_lmax and the ex-suspicious block both execute range(999);
     verified 2026-07-02). p_floor recomputed.
  4. 5 equation test rows appended (run/test ledger reconciliation, audit G-5):
     binding-null p per registered claim from results/eq_tidal_v{1,2}.json;
     confirm1 is gate-based (raw_p null, floor check n/a).
  5. global_m recomputed over non-superseded test rows only.

Idempotent: refuses to run twice (detects row_type). Backs up the original.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LEDGER = os.path.join(ROOT, "results", "multiplicity_ledger.jsonl")
BAK = LEDGER + ".bak-schema-v1"

EQ_ROWS = [
    # binding null-adjusted p per claim = max over the 3 declared generators
    # (results/eq_tidal_v1.json, eq_tidal_v2.json; B=200 -> floor 1/201)
    dict(run_id="eq_tidal_v1", dataset="tidal-manila accel phase",
         claim_type="equation_discovery", method="null-equation-generator",
         raw_p=0.209, m_perm=200, family_id="eq.tidal-manila.harmonic",
         within_run_m=5, data_filter="all_rows"),
    dict(run_id="eq_tidal_v1", dataset="moon distance",
         claim_type="equation_discovery", method="null-equation-generator",
         raw_p=0.005, m_perm=200, family_id="eq.tidal-manila.harmonic",
         within_run_m=5, data_filter="all_rows"),
    dict(run_id="eq_tidal_v2", dataset="tidal-manila accel phase",
         claim_type="equation_discovery", method="null-equation-generator",
         raw_p=0.194, m_perm=200, family_id="eq.tidal-manila.harmonic",
         within_run_m=3, data_filter="all_rows"),
    dict(run_id="eq_tidal_v2", dataset="moon distance",
         claim_type="equation_discovery", method="null-equation-generator",
         raw_p=0.0099, m_perm=200, family_id="eq.tidal-manila.harmonic",
         within_run_m=3, data_filter="all_rows"),
    dict(run_id="eq_moondist_confirm1", dataset="moon distance fresh 86d",
         claim_type="equation_discovery", method="frozen-equation-confirmation",
         raw_p=None, m_perm=None, family_id="eq.tidal-manila.harmonic",
         within_run_m=1, data_filter="fresh_rows", gate_based=True),
]


def main():
    rows = [json.loads(l) for l in open(LEDGER)]
    if any("row_type" in r for r in rows):
        print("already migrated; nothing to do"); return 0
    shutil.copy(LEDGER, BAK)
    out = []
    for r in rows:
        if "m_delta" in r:
            r["row_type"] = "family_charge"
        else:
            r["row_type"] = "test"
            if r["run_id"] == "batch6":
                r["superseded_by"] = "batch67_r2"
                r["migration_note"] = "superseded: rerun at floor-compliant m"
            if r["method"] == "lambda-max" and r["m_perm"] == 399:
                r["m_perm"] = 999
                r["p_floor"] = round(1 / 1000, 4)
                r["migration_note"] = ("m_perm corrected 399->999: code executes "
                                       "range(999); audit 2026-07-02")
        out.append(r)
    for e in EQ_ROWS:
        e["row_type"] = "test"
        e["p_floor"] = round(1 / (e["m_perm"] + 1), 4) if e["m_perm"] else None
        e["migration_note"] = "eq run p added for run/test reconciliation (audit G-5)"
        out.append(e)
    live = [r for r in out if r["row_type"] == "test" and "superseded_by" not in r]
    for r in out:
        if r["row_type"] == "test":
            r["global_m"] = len(live)
    with open(LEDGER + ".tmp", "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    os.replace(LEDGER + ".tmp", LEDGER)
    print(f"migrated {len(rows)} -> {len(out)} rows; "
          f"{len(live)} live test rows (global_m); backup at {os.path.basename(BAK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
