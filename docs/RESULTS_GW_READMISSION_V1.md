# RESULTS — GW (R2) readmission run v1

Registration: `docs/REGISTRATION_GW_READMISSION_V1.md` (committed
pre-execution; commitment-ledger anchor `10f557f81667ee94…`). Source JSON:
`results/gw_readmission_v1.json` (sha256-16 `c177202c1c6a9415`, ledgered in
`results/run_ledger.jsonl` run_id `gw_readmission_v1`). All numbers below are
transcribed from that JSON. Two runs with identical seeds were byte-identical
(`results/_gw_readmission_v1_run2.json`). Synthetic calibration only; zero
multiplicity charged.

## Verdict (pre-declared rule): **CALIBRATED_BUT_POWERLESS**

| Gate | Registered pass band | Observed | Result |
|---|---|---|---|
| 1 — FPR@0.05 | [0.028, 0.078] (300 H₀ trials) | **0.040** | PASS |
| 2 — p-uniformity | KS p ≥ 0.01 AND lattice χ² p ≥ 0.01 | **KS p = 0.0755, χ² p = 0.238** | PASS |
| 3 — power @ noise 0.1 | ≥ 0.85 (frozen M1 ref 0.95) | **0.62** | FAIL |

Full power curve (50 trials/point): noise 0.1 → **0.62**, 0.2 → **0.62**,
0.3 → **0.50**, 0.5 → **0.64**. Frozen M1 reference under the (miscalibrated)
regeneration null: 0.95 → 0.15 over the same grid.

## What this establishes

1. **The M2 defect is fixed by the redesigned null.** The coupling-label
   permutation null is calibrated in distribution — the lattice χ² test that
   failed at p = 0.002 under moment-matched regeneration (REMEDIATION_LOG M2)
   passes at p = 0.238, with KS uniformity and in-band FPR. The
   miscalibration was a property of the regeneration null, not of the GW
   statistic's p-machinery.
2. **But the calibrated instrument cannot see the registered effect.** Power
   against shared circle geometry is ~0.5–0.64 and — notably — flat across
   the noise grid, including at noise 0.5 where the frozen reference had
   dropped to 0.15. A permutation of pooled labels compares GW(A,B) to
   GW(mixed, mixed); when A and B genuinely share geometry the mixed halves
   share it too, so the observed statistic is not extreme under the null in
   the graded way the effect grid assumes. The flat curve is consistent with
   the test responding to residual asymmetries rather than the shared-shape
   effect itself.

## Recommendation (per the approved proposal's decision rule)

No candidate null both calibrates and powers the R2 instrument as
registered: the regeneration null has power but fails uniformity (M2); the
label-permutation null passes uniformity but fails power (this run); the
row-permutation variant is degenerate by construction (withdrawn at design
time). **Recommend retiring R2 (Gromov–Wasserstein) to the conflict
registry** — its exploratory-only status becomes retirement pending any
future proposal for a fundamentally different null family (e.g. entropic GW,
which would be a new instrument requiring fresh onboarding). The M3 GW pair
numbers (tidal|moon p = 0.010 etc.) remain exploratory and unpublishable.

The retirement itself is a governance action for the lab owner: on
ratification, update THEOREM_GOVERNANCE/conflict registry and the README
Limitations entry.

*Dead-end log (CLAUDE.md discipline): two null families exhausted for exact
GW at this n and effect grid; the negative result is the finding.*
