# PROPOSAL — GW (R2) null redesign and readmission path

**Status: DRAFT / PROPOSED — not a registration.** No run may execute from
this document. Per THEOREM_GOVERNANCE, the path is: human approval of this
proposal → a REGISTRATION doc with seeds/m/floor/family charge → commitment
snapshot (`python3 tools/snapshot_commitment.py`) → execution → independent
verification. Written 2026-07-07 by the maintenance session; the
structure-analyst role should own the registration.

## Problem on file

- **REMEDIATION_LOG M2:** the GW admission gate rerun at n=200 **fails
  p-uniformity** — FPR@0.05 is fine (0.055) but the null p-distribution is
  non-uniform (lattice χ² p=0.002). A symmetric-null variant also fails
  (p=0.005; `results/gw_symmetric_gate_pilot.json`). Conclusion on file:
  *"moment-matched regeneration nulls for GW are inherently miscalibrated in
  distribution."*
- Consequence: **GW demoted to G0 exploratory-only** (README Limitations;
  RESULTS_BATCH6_7_RERUN §4). The M3 GW pair results (tidal|moon p=0.010,
  pressure|lotto p=0.280, pressure|tidal p=1.0 at m=99) are exploratory and
  unpublishable until readmission.
- Original admission (results/admission_log.txt R2) passed at the older,
  weaker gate — the A4 flag stands.

## Why moment-matched regeneration plausibly fails for GW

GW distance is a *minimum over couplings* of a quadratic objective. The
distribution of such minima is sensitive to fine geometric structure that
moment matching does not preserve (higher-order shape of the distance
matrices), and the exact POT solver's discreteness at small n produces a
lattice-like statistic distribution — matching the observed χ² lattice
failure rather than an FPR failure. Any redesigned null must condition on
the *observed geometries*, not on regenerated surrogates.

## Candidate nulls (register ONE as primary before any run)

1. **Coupling-label permutation (recommended primary).** Pool the two point
   sets, permute the dataset labels, recompute GW between the permuted
   halves. Exchangeability under H₀ (no shared structure) holds by
   construction and both empirical geometries are conditioned on. Standard,
   assumption-light.
2. **Row-permutation within one side.** Permute the row order of one
   distance matrix relative to its measure. Preserves each geometry exactly;
   tests alignment rather than distributional similarity — matches R2's
   registered claim type (cross-dataset similarity via alignment).
3. **Entropic-GW variant.** Replace exact GW with entropic regularization
   (smoother objective, non-degenerate minima, less lattice). This CHANGES
   the instrument: requires fresh onboarding (new KB card + full admission),
   not just readmission.

## Readmission protocol (mirrors the R1–R7 admission gates)

At n=200, seeds `20260707 + 1000*variant_index`, m ≥ 399 with
p_floor = 1/(m+1) ≤ α_corr/2 (floor rule):

1. **FPR gate:** FPR@0.05 within binomial band of 0.05.
2. **Uniformity gate:** KS *and* lattice χ² on the null p-distribution —
   the gate that failed in M2 must be the gate that readmits.
3. **Power gate:** recover at least the M1 frozen power curve
   (0.95 @ noise 0.1 → 0.15 @ 0.5) on the same pre-declared effect grid;
   report the full curve, no tuning after seeing it.

All calibration runs are synthetic → **no real-data multiplicity charge**.
Ledger: one run-ledger row (`gw_readmission_v1`), admission-log lines per
gate, commitment snapshot BEFORE execution.

## After readmission

Any real-data GW claim (including re-testing M3's tidal|moon p=0.010) is a
NEW registration with its own family charge — the exploratory M3 numbers
must not be graded retroactively. If no candidate null passes all three
gates, record the dead end (CLAUDE.md: dead ends are logged, not hidden)
and retire R2 to the conflict registry.
