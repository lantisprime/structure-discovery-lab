# HEAL_NOTES

## Root cause

Commit `dc48068` ("plant: July runner reads the working tree") changed
`main()` in `src/pcso_weekly_update.py` from
`ACTIVE_SNAPSHOT = INPUT_SNAPSHOT_COMMIT` to `ACTIVE_SNAPSHOT = None`. Per
the module docstring and the comment on `ACTIVE_SNAPSHOT` (lines 9-16,
45-47), this script reproduces the frozen July 2026 closeout: its result
hashes the *whole* input files as of `INPUT_SNAPSHOT_COMMIT`, and the
dataset CSVs are append-only, having grown since (PR #20, 2026-09-06).
Setting `ACTIVE_SNAPSHOT = None` made `input_bytes()` read the live
working-tree CSVs instead of the frozen commit, so `data_draws.csv` (and
the other draw/astro/workbook inputs) were read at their current, grown
size — 380 dated rows instead of the 252 the manifest's
`expected_row_counts` recorded for the July batch — tripping the row-count
guard in `validate_inputs()`. This is exactly the "reads working tree"
defect the commit's own message says was planted for the R3 live-proof.

## Fix

Reverted the one-line regression: `ACTIVE_SNAPSHOT = INPUT_SNAPSHOT_COMMIT`
in `main()` (src/pcso_weekly_update.py), restoring the July closeout
runner to reading its inputs from the pinned snapshot commit via
`input_bytes()`/`git show`, as `src/pcso_monitoring_run.py` (the live
runner) expects `ACTIVE_SNAPSHOT is None` to mean "read the working tree"
and this script alone is responsible for setting it back to the pinned
commit for its own run.

## Verification

- `.venv/bin/python src/pcso_weekly_update.py --verify` → `PASS
  sha256=11c8af729f...; validated=28; confirmation_n=58; flags=0;
  wrote=none` (exit 0).
- `./tools/check.sh` → `ALL CHECKS PASSED`, including `outcome collect
  (R0 gate)` reporting `0 new defect(s)` and `outcome attribute (R1)`
  reporting no unattributed defects.

## Follow-up not done

None needed — this was a single planted one-line regression with no
other affected callers (`src/pcso_monitoring_run.py` imports validators
from this module but sets its own module-level state and is unaffected;
its own `--verify` still passes per the check.sh run above).
