# Registration — Batch 6: Lotto Sub-Dataset Partition Experiments

**Date**: 2026-06-11 · **Protocol**: RELATIONAL_RUNBOOK Phase 1 ·
**Script**: `src/relational_subsets.py` (run after this page) · seed 20260611.

**Question**: partition each game's 1-yr draw history into sub-datasets; do the
parts share structure with each other beyond what independent runs of the same
machine produce? For a fair memoryless machine, the parts must be mutually
unrelated except through their common marginal law.

## Partition schemes (declared)

- **Quarters**: each game's draws, date-ordered, cut into 4 contiguous segments
  (~39 draws each) → 6 segment pairs per game.
- **Halves**: date-ordered 50/50 split (~78 draws each).
- Note (A5): the registered 6/55 era boundary (Feb 2026) falls inside Q3/H2; the
  2025 #45 excess lives in Q1–Q2/H1. Segment flags in 6/55 that trace to #45 rows
  join the existing anomaly class (C9), not a new discovery.

## Experiments

**B6-1 — Cross-quarter distributional similarity (R1, admitted).**
Representation (declared): per-draw 6-feature vector (sum, min, max, range,
odd-count, mean-gap), standardized per game. Statistic: MMD² (RBF, median
heuristic) between every quarter pair. Null: pool-and-relabel, m=99.
**Registered expectation: all 30 pairs (5 games × 6) null** — the machine is
stationary in this representation. Rejections would indicate regime change and
route to the A5 era registry, not to a relationship claim.

**B6-2 — Cross-quarter co-occurrence structure (R5, admitted; shape gate
re-run at quarter shape).** Statistic: −L2 distance between standardized top-10
co-occurrence spectra of two quarters (batch-5 pipeline at T≈39). Null: independent
constrained-uniform quarter pairs, m=99. Shape gate: 40 uniform-vs-uniform trials
at the (39, 55) quarter shape must be calibrated before real data.
**Registered expectation: all 30 pairs null**, with the possible exception of
6/55 pairs within the 2025 era, which if flagged must trace to #45 (C9).

**B6-3 — Half-vs-half hot-number consistency.** Statistic: Pearson correlation
between per-number frequency deviations (observed − expected) in half 1 vs
half 2 of the same game. Null: constrained-uniform regenerations of both halves,
m=199. **Registered expectation: all 5 games null** — no number stays hot; for
6/55, the era-bounded #45 excess straddles the boundary weakly, so a mild
positive that traces to #45 is a shadow, not persistence (C9 + A5).

## Multiplicity

Three statistic classes (B6-1, B6-2, B6-3). Within-class correction: Šidák at
m=30, 30, 5 respectively. Min-p reported against its class threshold. No new
equivalence class is created (B6-1 joins {R1}, B6-2 joins the relational graph
class, B6-3 joins the chi-square/frequency family — it is a function of hit
counts and explicitly inherits C3/C9 row-trace duties).

## Power statement (A4, declared up front)

At T≈39 draws per quarter, per-cell co-occurrence expectations are ~0.5 — the
spectral statistic at quarter shape has power only against gross structure; the
shape-gate calibration plus the planted-control of batch 5 at full shape bound the
claim. Nulls at this n are "no detectable structure at quarter resolution," not
"no structure of any size" (asymmetric verdicts, A4).

## Output contract

`results/relational_subsets.json`; figure `fig7_subset_partitions.png`; results in
`RESULTS_BATCH6.md`; every number re-derived by `src/verify_relational_docs.py`.
