# Batch 6 Results — Lotto Sub-Dataset Partition Experiments

**Date**: 2026-06-11 · **Registration**: `docs/REGISTRATION_BATCH6.md` (declared
before execution) · **Script**: `src/relational_subsets.py` · **Raw output**:
`results/relational_subsets.json` · **Figure**: `fig7_subset_partitions.png` ·
**Verification**: `src/verify_relational_docs.py` (extended, passing).

Each game's 1-yr history was partitioned into sub-datasets (4 contiguous quarters,
~39 draws; and 2 halves, ~78 draws) and the parts were tested against each other.

## Shape gate (Phase 0)

40 uniform-vs-uniform trials at the (39, 55) quarter shape: FPR 0.15, KS p = 0.422.
Passed — 0.15 at n=40 is inside the 3·SE band (±0.103 around α); noted as
borderline-by-MC-noise, with the p-value distribution itself clean.

## B6-1 — Cross-quarter distributional similarity (MMD, 30 pairs)

**Joint verdict: NULL.** min p = 0.040 across 30 quarter pairs vs Šidák threshold
0.0017. One raw p ≤ 0.05 (6/58 Q2|Q4 at 0.04) against an expectation of 1.5 such
values among 30 uniform p's — noise, not signal. No game's feature distribution
drifts between quarters: the machines are stationary in the declared
representation, and no A5 era action is triggered.

## B6-2 — Cross-quarter co-occurrence structure (spectra, 30 pairs)

**Joint verdict: NULL.** min p = 0.070 vs Šidák 0.0017; not a single raw flag. No
quarter of any game shares co-occurrence community structure with any other quarter
beyond what two independent constrained-uniform runs produce — including the 6/55
quarter pairs inside the 2025 #45 era (the per-quarter spectral statistic at T≈39
has power only against gross structure; see the registered power statement).

## B6-3 — Half-vs-half hot-number consistency (5 games, m=199)

| Game | corr(dev₁, dev₂) | null q95 | p | boundary | top contributors |
|---|---|---|---|---|---|
| 6/42 | +0.060 | 0.256 | 0.360 | 2025-12-09 | #19, #18, #7 |
| 6/45 | +0.147 | 0.249 | 0.210 | 2025-12-10 | #26, #4, #24 |
| 6/49 | +0.004 | 0.256 | 0.435 | 2025-12-09 | #44, #20, #26 |
| 6/55 | **+0.251** | 0.203 | **0.025** | 2025-12-10 | **#45 (68.6), #42 (56.1)**, #16 |
| 6/58 | +0.060 | 0.213 | 0.330 | 2025-12-09 | #50, #10, #12 |

**Joint verdict: NULL** (min p = 0.025 > Šidák 0.0102). The single raw flag is
6/55 — and its C9 row trace lands on **#45 and #42, the same two numbers** that
led the batch-5 λ_max eigenvector (loadings 0.439 / 0.426). This is the registered
prediction realized: the era-bounded 2025 #45 excess straddles the December
boundary weakly and shows up as a shadow in any statistic that is a function of hit
counts (C3/C9 inheritance). It joins the existing #45 equivalence class; no
hot-number persistence claim exists for any game.

## Verdict

Partitioned any way tried — quarters against quarters, halves against halves — the
lotto sub-datasets are mutually structureless: their only shared property is the
marginal law of the machine that generated them, which is exactly the relational
definition of i.i.d. (framework §0: independently generated datasets are extremal
on the relational face). The one recurring excess (#45) keeps being found by every
hit-count instrument and keeps tracing to the same expired era — the equivalence
class now spans chi-square, graphon (row 27), cross-game λ_max (row 32), and
half-consistency (this batch), and still contributes exactly one anomaly.

Power honesty (A4): at quarter resolution (T≈39) only gross structure is
detectable; these nulls bound structure at the resolution tested, not all
structure of any size.
