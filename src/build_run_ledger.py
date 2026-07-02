#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
"""Run-level global ledger: one row per experiment execution across the lab's
relational program. Complements:
  - results/multiplicity_ledger.jsonl  (test-level: one row per p-value)
  - docs/THEOREM_SYNTHESIS.md §5       (instrument-level results ledger)
  - results/commitment_ledger.txt      (file-level hashes)

Each row: run_id, date, script, stages, seed scheme, registration artifact,
output JSON (+sha256), datasets touched, n tests contributed to the
multiplicity ledger, verifiers passed, evidence grade, status notes.

Going forward, new runs append via append_run(); the backfill below is the
authoritative reconstruction of the 2026-06-11 session, cross-checkable
against each output JSON's _meta block.

Output: results/run_ledger.jsonl
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LEDGER = os.path.join(ROOT, "results", "run_ledger.jsonl")


def sha(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def n_ledger_tests(run_id):
    path = os.path.join(ROOT, "results", "multiplicity_ledger.jsonl")
    # .get: family_charge rows (schema v2) carry no run_id
    return sum(1 for l in open(path) if json.loads(l).get("run_id") == run_id)


BACKFILL = [
    {"run_id": "admission", "date": "2026-06-11",
     "script": "src/relational_admission.py",
     "stages": ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
     "seed_scheme": "20260611 + 1000*instrument_index",
     "registration": "THEOREM_GOVERNANCE Part 3 Step 4 (protocol, not per-run doc)",
     "output": "results/relational_admission.json",
     "datasets": ["synthetic only"],
     "real_data_tests": 0,
     "verifiers": ["numeric"],
     "grade": "G1", "status": "all 7 admitted; instruments R1/R5 tuned during "
     "admission (M1, superseded by frozen power curves); GW later demoted (M2)"},
    {"run_id": "firstrun", "date": "2026-06-11",
     "script": "src/relational_first_run.py",
     "stages": ["curves", "presence", "cca"],
     "seed_scheme": "20260611 (+1,+2 per stage)",
     "registration": "script-header H-R1..H-R4 (retroactive, pre-commitment-device; "
     "expectations style superseded by expectation-free protocol)",
     "output": "results/relational_first_run.json",
     "datasets": ["pcso-lotto 6/55", "tidal-manila", "jpl-horizons-sun-moon",
                  "gfz-kp-geomagnetic"],
     "real_data_tests": n_ledger_tests("firstrun"),
     "verifiers": ["numeric"],
     "grade": "G2 (series verdicts G4 via blind replication)",
     "status": "presence test later relabeled (C3); recovery floors warned (historical)"},
    {"run_id": "batch5", "date": "2026-06-11",
     "script": "src/relational_batch5.py",
     "stages": ["shapegate", "crossgame", "topology", "recovery_tidal",
                "recovery_lotto"],
     "seed_scheme": "20260611 (+50..+53)",
     "registration": "docs/REGISTRATION_BATCH5.md (retroactive label)",
     "output": "results/relational_batch5.json",
     "datasets": ["pcso-lotto all 5 games", "tidal", "sun-moon", "kp"],
     "real_data_tests": n_ledger_tests("batch5"),
     "verifiers": ["numeric"],
     "grade": "G2",
     "status": "all 10 cross-game pairs null; #45 shadow traced (C9); "
     "lambda_max floors superseded by remediation m=999 rerun"},
    {"run_id": "allgames", "date": "2026-06-11",
     "script": "src/relational_allgames.py",
     "stages": ["g42", "g45", "g49", "g55", "g58"],
     "seed_scheme": "20260611 + hash(game)%1000",
     "registration": "amendment in REGISTRATION_BATCH5.md",
     "output": "results/relational_allgames.json",
     "datasets": ["pcso-lotto all 5 games", "covariate bundle"],
     "real_data_tests": n_ledger_tests("allgames"),
     "verifiers": ["numeric"],
     "grade": "G2 (series verdicts G4 via blind replication)",
     "status": "all null, all games"},
    {"run_id": "batch6", "date": "2026-06-11",
     "script": "src/relational_subsets.py",
     "stages": ["gate", "mmd", "spectra", "halves"],
     "seed_scheme": "20260611 (+60..+63)",
     "registration": "docs/REGISTRATION_BATCH6.md (retroactive label)",
     "output": "results/relational_subsets.json",
     "datasets": ["pcso-lotto all 5 games, quarters+halves"],
     "real_data_tests": n_ledger_tests("batch6"),
     "verifiers": ["numeric", "design"],
     "grade": "G2 (6/55 half-corr sensitivity G4 via independent replication)",
     "status": "joint null x3; 6/55 half-corr is data-quality-sensitive (M4)"},
    {"run_id": "pressure", "date": "2026-06-11",
     "script": "src/relational_pressure.py + src/relational_batch7.py",
     "stages": ["baseline", "seasons", "cca", "gwgate", "gw"],
     "seed_scheme": "20260611 (+70, +80..+83)",
     "registration": "DATASET.md §6 + docs/REGISTRATION_BATCH7.md (retroactive label)",
     "output": "results/relational_pressure.json + results/relational_batch7.json",
     "datasets": ["openmeteo-pressure-manila (single-source caveat)",
                  "pcso-lotto", "covariate bundle"],
     "real_data_tests": n_ledger_tests("pressure"),
     "verifiers": ["numeric", "design"],
     "grade": "G2; GW pairs G0 (instrument demoted)",
     "status": "B7-1 seasons rerun at m=199 after floor-rule catch; "
     "GW gate later failed at n=200 (M2)"},
    {"run_id": "remediation", "date": "2026-06-11",
     "script": "src/remediation_r1.py",
     "stages": ["presence_mc(m=199)", "floors_lmax(m=999)", "floors_gw",
                "gate_quarter(n=200)", "gate_gw(n=200)", "pc_r1..pc_r7",
                "sensitivity", "cca_splits"],
     "seed_scheme": "20260611 (+90..+111)",
     "registration": "expectation-free protocol (REMEDIATION_LOG); "
     "hash ledger commitment",
     "output": "results/remediation_r1.json",
     "datasets": ["pcso-lotto all 5 games, 3 data regimes", "covariate bundle",
                  "synthetic (power curves, gates)"],
     "real_data_tests": n_ledger_tests("remediation"),
     "verifiers": ["numeric", "design"],
     "grade": "G2-G3 (hash-committed)",
     "status": "6/45 flag opened at m=399, closed at m=999; 6/55 lambda_max "
     "p=0.0010 sole corrected rejection; GW demoted; gates: quarter PASS, gw FAIL"},
    {"run_id": "blind_verification", "date": "2026-06-11",
     "script": "results/blind/_indep_task1.py + _indep_task2.py (independent agent)",
     "stages": ["task1 blind classification", "task2 numerical replication"],
     "seed_scheme": "12345 / 2026 (agent-chosen)",
     "registration": "EXTERNAL_REVIEW_BRIEF protocol; agent barred from "
     "lab code/docs/key",
     "output": "results/independent_verification.json",
     "datasets": ["9 blinded standardized series", "pcso-lotto 6/55 raw"],
     "real_data_tests": 0,
     "verifiers": ["independent (it IS the verifier)"],
     "grade": "G4 evidence generator",
     "status": "9/9 blind concordance; replication to 3 decimals"},
]


def append_run(row):
    """For future runs: append one row; refuse duplicate run_ids."""
    existing = {json.loads(l)["run_id"] for l in open(LEDGER)} if \
        os.path.exists(LEDGER) else set()
    if row["run_id"] in existing:
        raise ValueError(f"run_id {row['run_id']} already in ledger (append-only)")
    with open(LEDGER, "a") as f:
        f.write(json.dumps(row) + "\n")


def main():
    # AUDIT G-1 (2026-07-02): was a truncating write over the backfill while
    # the live ledger held more rows — one rerun deleted every appended run
    # (all Phase-5, remediation-era and riemann rows). Now non-destructive:
    # rows beyond the backfill are preserved; conflicts on backfill rows abort.
    preserved = []
    if os.path.exists(LEDGER):
        disk = [json.loads(l) for l in open(LEDGER)]
        backfill_ids = {r["run_id"] for r in BACKFILL}
        for d in disk:
            if d["run_id"] not in backfill_ids:
                preserved.append(d)
            else:
                b = next(r for r in BACKFILL if r["run_id"] == d["run_id"])
                if b.get("real_data_tests") != d.get("real_data_tests"):
                    raise SystemExit(
                        f"ABORT: backfill disagrees with ledger on disk for "
                        f"{d['run_id']} — append-only invariant violated")
    tmp = LEDGER + ".tmp"
    with open(tmp, "w") as f:
        for r in BACKFILL:
            outs = [o.strip() for o in r["output"].split("+")]
            r["output_sha256"] = {o: sha(o) for o in outs}
            f.write(json.dumps(r) + "\n")
        for d in preserved:
            f.write(json.dumps(d) + "\n")
    os.replace(tmp, LEDGER)
    total = sum(r["real_data_tests"] for r in BACKFILL) + \
        sum(d.get("real_data_tests", 0) for d in preserved)
    print(f"run ledger: {len(BACKFILL)} backfill + {len(preserved)} preserved "
          f"runs, {total} real-data tests")
    for r in BACKFILL:
        print(f"  {r['run_id']:<20} tests={r['real_data_tests']:>3}  grade={r['grade'].split()[0]}")


if __name__ == "__main__":
    main()
