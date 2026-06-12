# Registration — Batches 6 & 7 Rerun under Remediated Methodology (run id: batch67_r2)

**Date**: 2026-06-11 · expectation-free (no outcome predictions for discovery
tests) · hash-committed before any result exists · **Script**:
`src/rerun_batch67.py`, built on `src/core` + `src/domains/pcso_lotto`
(first full-batch use of the sanitized architecture) · seed 20260611 (+300s).

**Why a rerun**: the original batch 6/7 runs predate four standing rules and
carry historical floor warnings in the design verifier. This rerun applies:
(1) the **floor rule** (p_floor ≤ α'/2 per family); (2) **M4 three-regime
sensitivity** for hit-count statistics; (3) **M7 multi-split** for CCA;
(4) **GW as G0 exploratory** (demoted instrument — outputs reported, never
verdicts). Originals remain on record; deltas will be reported side by side.

## Claim table (floor arithmetic shown)

| stage | statistic · null | family m → Šidák α' | α'/2 | m_perm (floor) |
|---|---|---|---|---|
| b6_mmd | cross-quarter MMD on [value-features], pool-and-relabel | 30 → .001709 | .000854 | **1199** (.000833 ✓) |
| b6_spectra | cross-quarter co-occurrence spectra, constrained-generator pairs | 30 → .001709 | .000854 | **1199** (.000833 ✓) |
| b6_halves | half-vs-half deviation corr, constrained generator; **3 regimes** (all/ex-suspicious/verified-only) | 5 → .0102 | .0051 | **199** (.005 ✓) |
| b7_seasons | pressure quarter-pair MMD, pool-and-relabel | 6 → .00851 | .00426 | **399** (.0025 ✓) |
| b7_cca | pressure vs sun-moon & vs geomagnetics, held-out CCA, shuffled pairing; **3 splits** (50/60/70%) | 2 → .0253 | .0127 | **199** (.005 ✓) |
| b7_gw | GW distortion, matched-Gaussian regeneration | exploratory G0 — no corrected claim | n/a | 99 |

Decision rules: Phipson–Smyth +1; verdict per family at α'; raw excursions
above α' = exploratory notes; regime/split variants are sensitivity members of
one class, not extra multiplicity (per the refined family convention). Any
hit-count flag gets the C9 row trace against the domain ANOMALY_REGISTRY.
Shape gates: reuse the n=200 quarter-shape gate (PASS, REMEDIATION_LOG M2) —
shapes unchanged from the originals.

Output: `results/rerun_batch67.json`; comparison vs originals in
`docs/RESULTS_BATCH6_7_RERUN.md`; run-ledger row `batch67_r2`.
