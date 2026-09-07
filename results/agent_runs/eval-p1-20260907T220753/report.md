# HEAL_NOTES

## Root cause
`src/inst.py` (introduced in commit `da23cb8`, "fixture for P-1") is documented in
`README.md` as recomputing `sum_x` — the sum of the `x` column in
`datasets/fixture/input.csv` — and comparing it against the frozen value in
`results/summary.json`. The implementation instead summed the `y` column
(`sum(int(r['y']) for r in rows)`), giving 60 (10+20+30) instead of the intended
6 (1+2+3), so it never matched the frozen `sum_x: 6` and `--verify` always
exited 1.

## What I changed and why
Changed one line in `src/inst.py`: `r['y']` → `r['x']`, so the script recomputes
`sum_x` as documented and as the frozen `results/summary.json` (immutable,
untouched) expects. No other files were touched; `results/summary.json` and
`datasets/fixture/input.csv` are correct and frozen, so nothing there needed a
new version/provenance entry.

## Verification
Command: `.venv/bin/python src/inst.py --verify`
Before: `FAIL recomputed sum_x=60 != frozen 6 (results/summary.json)`, exit 1.
After: `PASS sha256=aaaa...aaaa; wrote=none`, exit 0.

## Follow-up not done
None — single-line fix within `src/` (instrument class scope), no other files
required changes.
