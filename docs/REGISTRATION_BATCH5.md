# Registration — Batch 5 (Relational), declared before execution

**Date**: 2026-06-11 · **Protocol**: RELATIONAL_RUNBOOK Phase 1 ·
**Script (to be run after this page is committed)**: `src/relational_batch5.py` ·
seed 20260611. Both experiments use admitted instruments (R5, R4 —
`docs/ADMISSION_RELATIONAL.md`) and re-run negative controls at the real-data
shape per the Phase 0 shape gate.

---

## Experiment B5-A — Cross-game co-occurrence comparison (instrument R5)

- **Claim type** (§1.2): cross-dataset similarity (scalar) — "do two games share
  co-occurrence community structure beyond what two independent constrained-uniform
  machines produce?"
- **Datasets**: the five games in `data_draws_1yr_audited.csv` (6/42 n=154, 6/45
  n=156, 6/49 n=155, 6/55 n=156, 6/58 n=155), all ten unordered pairs.
- **Representation** (one, declared): per-game co-occurrence count matrix → centered
  and standardized cell-wise by the constrained-generator null (A1: 6-of-P uniform,
  same number of draws) → sorted top-10 eigenvalues.
- **Statistic**: L2 distance between the two games' standardized top-10 spectra;
  score = −distance (larger = more shared structure). Secondary (per-game, not new —
  joins the row-27 graphon class): λ_max z vs its own null.
- **Matched null**: 99 pairs of independent constrained-uniform datasets at the same
  (T_A, P_A; T_B, P_B), identical pipeline. **Shape-gate negative control**: 40
  synthetic uniform-vs-uniform trials at the 6/55-vs-6/45 shape must give
  FPR ≈ α and p ~ U(0,1) before the real pairs are scored.
- **Registered expectation**: all ten pairs NULL (every game is a constant graphon;
  there is no shared community structure to find). The 6/55 per-game λ_max may
  re-flag — that is the known #45 shadow and joins the row-27 equivalence class
  under C9 (trace-to-rows mandatory, no new evidence counted).
- **Multiplicity**: 10 pairwise tests within one statistic class → report min-p
  against the Šidák-corrected threshold for m=10 within the run; the run itself
  joins the relational graph class (no new class created).
- **Era/freeze**: full 1-yr window, pooled (era boundaries per dataset card; the
  Feb-2026 6/55 era boundary noted for interpretation of the per-game shadow).

## Experiment B5-B — Topology of delay embeddings + landmark recovery (instrument R4)

- **Claim type** (§1.2): topological structure (within-series, against matched
  temporal null) + subset-to-whole topological recovery (§4.4).
- **Datasets/series** (standardized): tidal total acceleration (n=366), moon
  distance (n=366), Kp daily mean (n=365), lotto 6/55 draw-sum (n=156).
- **Representation** (one, declared): delay embedding (x_t, x_{t+τ}, x_{t+2τ}),
  τ = 3 steps, dim 3. τ chosen a priori from the known ~14-day spring–neap and
  ~27.55-day lunar cycles (τ ≪ period); not tuned after seeing results.
- **Statistic 1 (existence)**: max H₁ persistence of the embedded cloud.
  **Null**: within-series value permutation, then the identical embedding pipeline,
  m=99. Registered expectation: tidal and moon REJECT (persistent loop — these are
  near-periodic signals); lotto draw-sum NULL; Kp not registered as either (genuinely
  uncertain: storms are bursty, not periodic — whatever results, it is reported as
  exploratory, A7).
- **Statistic 2 (recovery)**: for k ∈ {5, 10, 20, 40}% farthest-first landmarks of
  the tidal and lotto embeddings, max H₁ persistence of the landmark subcloud vs the
  same permutation null at the same k, 10 seeds. Registered expectation: tidal loop
  recoverable from small k (curve above null early); lotto flat at every k.
- **Multiplicity**: 4 series × 1 statistic + 2 recovery curves; joins the relational
  intrinsic-geometry class ({R2, R4}); τ and dim are fixed constants, so no
  representation charge beyond the declared bundle (C10 satisfied).

## Amendment (same day, before any all-games result was viewed)

At user direction, every per-game test is extended symmetrically to **all five
games** (6/42, 6/45, 6/49, 6/55, 6/58): draw-sum recovery curve, presence-matrix
recovery, delay-embedding H₁ existence, and date-paired CCA vs physical covariates
(`src/relational_allgames.py`). **Registered expectation: all null, all games.**
Same nulls, seeds per game, same pipelines as the originals; flags trace to rows
(C9) before reporting.

## Output contract

Both experiments write `results/relational_batch5.json`; figures to
`results/figures/`; every number quoted in RESULTS_BATCH5.md must re-derive from the
JSON (extension of `src/verify_relational_docs.py`). Verdicts use the asymmetric A4
rule and the §9 claim-strength tiers; nulls are reported as first-class results.
