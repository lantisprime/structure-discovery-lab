REPORT — Eval Q-3 equation search (rule 10)

**Source claims + gate check.** eq.eval.S1/S2/S4: detection STRUCTURED with attribution on file (run_ledger `blind_methodology_eval_v1`; detection executed by exec-analyst haiku a538f977/a19dd55e + interpret fable a957c002 — independence from this instance holds) → gate PASS. eq.eval.S3: detection NULL → **NO_EQUATION_ATTEMPTED**, no fit, no code run on that column. Blind discipline honored: no answer_key/, no GENERATION_NOTES.md, no *SEALED* files read.

**Registered family + hash.** fourier_k, k∈{1,2,3}, canonical sin/cos form, ω from train periodogram + LS refinement, BIC-on-validation selection (λ fixed). REGISTRATION_EVAL_Q3.md sha256 `37cffb4899ab994b` — verified present in results/commitment_ledger.txt pre-dispatch; sealed key `db11b479733c9f98` grader-side.

**Null-equation generator (A1).** B=99 permuted series per fitted claim, identical select-and-fit procedure, scored on own test split. Best null improvement over perm-null mean: S1 0.081, S2 0.064, S4 0.092 — observed improvements 0.478 / 0.364 / 0.490 → null_adjusted_p = 0.01 all three (the procedure does recover "equations" on noise; the observed fits exceed everything noise produced).

**Fitted equations (all_rows regime — eval data carry no provenance flags, so the three M4 regimes degenerate; floor |ĉ|<0.10 enforced; moving-block bootstrap B=199, block=32):**
- **S2 (PREDICTIVE_EQUATION):** x_t = a₁sin(ωt)+b₁cos(ωt)+a₂sin(2ωt)+b₂cos(2ωt), ω̂=0.09842 [0.09816, 0.09876] (half-width 0.31% < 5%), period ≈ 63.84. a₁=−0.291 [−0.324,−0.245], b₁=+0.618 [0.590,0.645], a₂=+0.264 [0.235,0.285]; a₀, b₂ below floor.
- **S1 (FAILED_EQUATION_SEARCH):** k*=1, ω̂=0.09811 [0.09752, 0.09875] stable, a₁=1.012 [0.987,1.040] — but residuals structured (below). S1/S2 share the ≈64-step base cycle (CIs overlap), consistent with "related view" attribution.
- **S4 (FAILED_EQUATION_SEARCH):** ω̂ not reportable (bootstrap CI half-width 58.6% of ω̂; degenerate drift toward a step-mimicking near-zero frequency; coefficient CIs explode).

**Held-out vs nulls (test RMSE vs B=199 null-fitted equations scored on the real test split):** S1 0.320 vs perm/phase/AR1 p = 0.005/0.030/0.005 — all beaten. S2 0.206 vs 0.005/0.005/0.005 — all beaten. S4 0.263 vs 0.005/**0.055**/0.010 — phase-randomized null NOT beaten → failed null comparison.

**Residual checks (B=199 bands):**

| claim | max|ACF₁..₁₀| (band .12–.13) | Fisher-g p | CUSUM p | clean? |
|---|---|---|---|---|
| S1 | 0.615, p=0.005 FAIL | p=0.005 FAIL | p=0.87 pass | NO |
| S2 | 0.072, p=0.65 pass | p=0.85 pass | p=0.555 pass | YES |
| S4 | 0.378, p=0.005 FAIL | p=0.005 FAIL | p=0.005 FAIL | NO |

**Verdicts:** S1 FAILED_EQUATION_SEARCH, S2 PREDICTIVE_EQUATION (level 2 only; Doob separation — no action license), S3 NO_EQUATION_ATTEMPTED, S4 FAILED_EQUATION_SEARCH. Learned (dead ends logged): S1's residual peak sits at ω₂ = 0.3927 = **4.003×ω̂** — a 4th harmonic outside the registered k≤3 cap; the contract forbids quiet extension, so I propose a NEW registration (k≤4, new m-charge) rather than upgrading. S4's failure pattern (CUSUM 5.29) independently confirms the changepoint attribution; propose a §4.5 piecewise registration. One declared deviation: residual-periodogram band built from permuted (not phase-randomized) residuals, because phase randomization preserves the residual periodogram exactly — degenerate band; the substitute is strictly harder.

**Two-run reproducibility:** run1.json == run2.json **byte-identical** (sha256 `69f3157d30224c63…`), seed 20260611; final `eq_fit_results.json` sha256 `783a1438b47af2d3…`.

Files (all under results/agent_runs/eval-q3-20260611/): `eq_fit_eval_q3.py`, `eq_fit_results.json`, `run1.json`, `run2.json`, `RESULTS_EQ_EVAL_Q3.md`, `_CHECKPOINT.md`. Ledger deltas proposed in RESULTS_EQ_EVAL_Q3.md, not applied.
