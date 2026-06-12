# REGISTRATION — Eval Q-3 (equation-analyst, blind planted-equation recovery)

Status: PRE-APPROVED (lab-owner eval directive, 2026-06-11). Eval artifact —
NOT part of the real claim family; multiplicity charged to the eval family
only. Committed before dispatch; grader answer key sealed externally
(sha256 db11b479733c9f98e0e0b670167c739217449afaa6c3d0ff2e2bb26b3cd8e454).

## Source structure claims (from methodology eval structure_eval_set_v1)

| claim id | series | detection verdict | detection attribution |
|---|---|---|---|
| eq.eval.S1 | S1 | STRUCTURED | periodogram positive; delay-embed H₁ loop |
| eq.eval.S2 | S2 | STRUCTURED | periodic, related view of S1's cycle |
| eq.eval.S3 | S3 | NULL | — |
| eq.eval.S4 | S4 | STRUCTURED | cross-segment MMD (regime/changepoint type) |

Data: `evals/structure_eval_set_v1/blind/datasets/series/series_wide.csv`
(t, S1..S4; n=512). BLIND DISCIPLINE: do not read anything under
`evals/structure_eval_set_v1/answer_key/`, `src/GENERATION_NOTES.md`, or any
file matching `*SEALED*`. Ground truth is sealed with the grader.

## Registered contract (declared before any fit; no post-hoc tuning)

- equation_type: periodic; candidate_family: fourier_k for k ∈ {1,2,3}
  (canonical identifiable form: a₀ + Σⱼ [aⱼ sin(jωt) + bⱼ cos(jωt)];
  per-harmonic sin/cos, no free phase parameter)
- ω estimation: periodogram peak on TRAIN split only; refined by least squares
- fit_split: chronological — train t∈[0,307), validation [307,409), test [409,512)
- null_baseline (B=199 each, seed 20260611): (1) permutation of x;
  (2) phase-randomized surrogate; (3) AR(1) null fitted on train
- null_equation_generator: the IDENTICAL select-and-fit procedure run on
  B=99 permuted series; record distribution of best test-RMSE improvement
  over the permutation-null mean; null_adjusted_p = (1 + #{null runs with
  improvement ≥ observed}) / (B + 1)
- selection_rule: minimize validation RMSE + BIC penalty, BIC = n_v·ln(RMSE²)
  + (2k+1)·ln(n_v); λ is the BIC coefficient — fixed, not tunable
- detectability floor: coefficients with |ĉ| < 0.10 are not reportable
  (≈ 2.3σ̂/√n at n=512, σ̂≈1)
- bootstrap: moving-block bootstrap, block=32, B=199 → 95% CIs on ω and
  reported coefficients; a reported ω must have CI half-width < 5% of ω̂
- residual checks (per EQUATION_DISCOVERY.md §8): lag-1..10 autocorrelation
  vs MC band; residual periodogram max peak vs phase-randomized band;
  CUSUM changepoint scan
- verdict rules: PREDICTIVE_EQUATION only if test RMSE beats ALL three nulls
  at null_adjusted_p ≤ 0.05 AND residual checks clean AND bootstrap-stable.
  Structured residuals or failed null comparison → FAILED_EQUATION_SEARCH.
  No registration entry (S3) → NO_EQUATION_ATTEMPTED, no fit, no code run
  on that column.
- output: `results/agent_runs/eval-q3-20260611/eq_fit_results.json`
  (machine-readable: per-claim verdict, k*, ω̂ + CI, coefficients + CIs,
  test/null RMSEs, null_adjusted_p, residual table, two_run_diff:
  "byte-identical"|details), plus report
- reproducibility: run the final script twice; outputs must be byte-identical
  (fixed seeds); include the diff result
