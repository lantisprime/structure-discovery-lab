# Registration — Batch 7: Atmospheric-Pressure Relational Experiments

**Date**: 2026-06-11 · declared before execution · **Script**:
`src/relational_batch7.py` · seed 20260611 · Dataset:
`datasets/openmeteo-pressure-manila/` (card complete; single-source caveat in
force — positive draws-coupling claims would need the second source; none are
expected).

## B7-1 — Seasonal partition: cross-quarter MMD on pressure (R1)

The batch-6 partition pipeline, run verbatim on the pressure series (daily
[P_mean, P_min, P_max, P_range], standardized; quarters = contiguous ~91-day
blocks; pool-and-relabel null, m=99; 6 pairs).
**Registered expectation: REJECT for pairs spanning the monsoon transition**
(the dataset card's era registry declares wet ≈May–Oct vs dry ≈Nov–Apr) — this
is the real-data POSITIVE control for the B6-1 pipeline: the same instrument
that returned 30 nulls on lotto quarters must detect a true regime change here,
or its lotto nulls mean little. Same-season pairs (e.g. Q1|Q2 within one regime)
may or may not reject; only the cross-regime rejection is registered.

## B7-2 — Pressure vs other covariates: date-paired CCA (R3)

Held-out ridge CCA, shuffled-pairing null, m=199, time-ordered 60/40 split:
- pressure vs sun/moon ephemerides — **registered expectation: POSITIVE**
  (mechanism: both carry the annual cycle; sun distance tracks season, Manila
  MSL pressure tracks monsoon season).
- pressure vs Kp geomagnetic — **registered expectation: NULL** (no accepted
  mechanism couples daily Kp to surface pressure at detectable size; any
  positive would be exploratory and single-source-gated).

## B7-3 — First real-data Gromov–Wasserstein run (R2): intrinsic geometry of
delay embeddings

τ=3, dim=3 embeddings (declared in batch 5), subsampled to 120 points
(every-kth, declared); GW distortion vs matched mean/cov Gaussian regeneration
of the second cloud, m=19; **shape gate first**: 20 independent-Gaussian trials
at (120, 3) must be calibrated (Part 4 D7 — R2's admission ran at n=50).
Pairs and registered expectations:
- pressure ↔ tidal accel: **exploratory, no direction registered** (both
  structured, geometries may differ; honest uncertainty).
- pressure ↔ lotto 6/55 draw-sum: **NULL** (the lotto embedding is a Gaussian-
  like blob; its geometry should be as alignable with a matched Gaussian as
  with pressure).
- tidal ↔ moon distance: **POSITIVE** (both are loops driven by the same lunar
  cycle — mechanism known; real-data positive control for GW).

## Multiplicity & classes

B7-1 joins {R1} (6 tests, Šidák m=6 within-run); B7-2 joins {R3} (2 tests);
B7-3 joins {R2,R4} intrinsic-geometry (3 tests). No new class. C9/C10 duties:
any draws-side flag traces to rows; representations are the declared bundles.

## Output contract

`results/relational_batch7.json`; figure `fig8_pressure_experiments.png`;
results appended to `docs/RESULTS_PRESSURE.md`; verification extension in
`src/verify_relational_docs.py`.
