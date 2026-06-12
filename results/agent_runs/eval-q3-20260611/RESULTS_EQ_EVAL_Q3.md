# RESULTS — Eval Q-3 equation search (eq.eval.S1..S4)

Agent: equation-analyst (Fable). Date: 2026-06-11.
Registration: REGISTRATION_EVAL_Q3.md, sha256 `37cffb4899ab994b` — verified against
results/commitment_ledger.txt (committed pre-dispatch; answer key sealed grader-side,
`db11b479733c9f98`). Blind discipline honored: nothing read under answer_key/,
no GENERATION_NOTES.md, no *SEALED* files.
Independence: detection executed by exec-analyst haiku a538f977/a19dd55e with
interpret-analyst fable a957c002 (run_ledger `blind_methodology_eval_v1`); this
equation-analyst instance is distinct. Gate satisfied for S1/S2/S4 (STRUCTURED,
registered, attribution on file); S3 gate fails by design.

Machine-readable output: `eq_fit_results.json` (sha256 `783a1438b47af2d3`).
Script: `eq_fit_eval_q3.py`. Two-run reproducibility: `run1.json` == `run2.json`
byte-identical (sha256 `69f3157d30224c63`), fixed seed 20260611.

## Verdicts

| claim | verdict | k* | ω̂ (95% CI) | period | test RMSE | nulls p (perm/phase/AR1) | gen p (B=99) | residuals |
|---|---|---|---|---|---|---|---|---|
| eq.eval.S1 | FAILED_EQUATION_SEARCH | 1 | 0.098113 [0.097524, 0.098746] | 64.04 | 0.320 | 0.005 / 0.030 / 0.005 | 0.01 | ACF + periodogram FAIL |
| eq.eval.S2 | **PREDICTIVE_EQUATION** | 2 | 0.098420 [0.098158, 0.098764] | 63.84 | 0.206 | 0.005 / 0.005 / 0.005 | 0.01 | all clean |
| eq.eval.S3 | NO_EQUATION_ATTEMPTED | — | — | — | — | — | — | (no code run on column) |
| eq.eval.S4 | FAILED_EQUATION_SEARCH | 2 | not reportable (CI half-width 58.6% of ω̂) | — | 0.263 | 0.005 / **0.055** / 0.010 | 0.01 | ACF + periodogram + CUSUM FAIL |

## eq.eval.S2 — the one accepted equation (level 2, predictive; no action license — Doob separation)

x_t = a₁ sin(ωt) + b₁ cos(ωt) + a₂ sin(2ωt) + b₂ cos(2ωt),  ω̂ = 0.09842 (period ≈ 63.84 steps)

Coefficients (all_rows regime — the only regime; eval data carry no provenance flags),
moving-block bootstrap 95% CIs (B=199, block=32); card-19 floor |ĉ| < 0.10 enforced:

| coef | estimate | 95% CI |
|---|---|---|
| a0 | below floor | [−0.022, 0.007] |
| a1 (sin ωt) | −0.2906 | [−0.324, −0.245] |
| b1 (cos ωt) | +0.6180 | [0.590, 0.645] |
| a2 (sin 2ωt) | +0.2641 | [0.235, 0.285] |
| b2 (cos 2ωt) | below floor | [−0.038, 0.032] |

Held-out: test RMSE 0.2063 vs null-fitted equations scored on the real test split —
permutation mean 0.557 (p=0.005), phase-randomized mean 0.729 (p=0.005), AR(1) mean
0.628 (p=0.005); null-equation generator (identical procedure on 99 permuted series):
observed improvement 0.364 vs best null improvement 0.064, null_adjusted_p = 0.01.
Residuals: max|ACF₁..₁₀| 0.072 < band 0.121 (p=0.65); Fisher-g 4.91 (p=0.85);
CUSUM 0.746 (p=0.555). ω bootstrap-stable (CI half-width 0.31% < 5%).

## What was learned from the failures (dead ends logged, not dismissed)

- **S1**: every null beaten (incl. generator p=0.01) and ω̂ stable at period ≈ 64.04,
  but residuals are strongly structured: max|ACF| 0.615 (band 0.126), residual
  Fisher-g 163 (p=0.005). Diagnostic: residual periodogram peak at ω₂ = 0.39270 =
  4.003 × ω̂ — i.e. a **4th-harmonic component at period 16**, outside the registered
  family cap k ≤ 3. Per contract (§6/EQUATION_DISCOVERY.md §8) structured residuals
  demand FAILED_EQUATION_SEARCH or a NEW registration — never a quiet family
  extension (M1). Recommended follow-up registration: fourier_k, k ∈ {1..4}, new
  multiplicity charge. Note S1/S2 share the base cycle (ω̂ 0.0981 vs 0.0984, CIs
  overlap; both ≈ 2π/64), consistent with the detection attribution "related view".
- **S4**: the periodic family is the wrong model class for a regime/changepoint
  structure, and every guardrail said so independently: phase-randomized null NOT
  beaten (p=0.055 > 0.05), CUSUM 5.29 (p=0.005), residual ACF and periodogram fail,
  ω̂ degenerate (drifts toward 0 to mimic a step; bootstrap CI half-width 58.6%,
  not reportable; coefficient CIs explode). Consistent with detection attribution
  (cross-segment MMD). Recommended follow-up registration: piecewise/changepoint
  family (§4.5), new multiplicity charge.
- **S3**: detection NULL → gate held; no fit attempted, no code touched the column.

## Declared deviation (one, flagged not hidden)

Residual-periodogram band: the registration says "vs phase-randomized band", but
phase-randomized surrogates of the residuals preserve the residual periodogram
exactly (the band is degenerate and the check would vacuously pass). Implemented
with permuted-residual (spectrum-whitening) surrogates per the card-12 Fisher-g
intent, B=199. This makes the check strictly harder, not easier.

## Proposed ledger deltas (NOT applied — orchestrator/human to commit)

- run_ledger.jsonl: run_id `eval_q3_equation_search`, script
  `results/agent_runs/eval-q3-20260611/eq_fit_eval_q3.py`, seed 20260611,
  registration hash 37cffb4899ab994b, outputs eq_fit_results.json
  (783a1438b47af2d3), two_run_diff byte-identical, verdicts
  S1 FAILED / S2 PREDICTIVE / S3 NO_EQUATION_ATTEMPTED / S4 FAILED.
- multiplicity_ledger.jsonl: eval family only (per registration), m_delta = 3
  fitted claims × 1 registered family.
- commitment_ledger.txt: append output hash 783a1438b47af2d3 for
  eq_fit_results.json.
