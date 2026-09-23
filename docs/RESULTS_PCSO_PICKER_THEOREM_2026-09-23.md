# RESULTS — Theorem-derived calibration of the lotto picker (2026-09-23, G0 exploratory)

Question (lab owner): how can the picker's prediction be improved, with mathematical theorems as
the predictor? Each equation below is derived from a lab theorem card; each lab-record assumption
was checked with Jev (typed judgments against verbatim lab excerpts), and the derivations were
refereed by two independent mathematician seats (GLM 5.3, Kimi K3; §7).

## 1. Equations

| # | Theorem (card) | Equation | Consequence for the picker |
|---|---|---|---|
| E1 | Independence / optional stopping (`doob-optional-stopping.md`) | under M₀, P(S_t = D_t) = 1/C(P,6) for every predictable rule | no history-based rule changes P(win) while the draw is fair |
| E2 | Order statistics; EVALUATION_PROTOCOL H5 | R_null ≈ exp(σ_c s₆/(a + c̄)); R_c = exp(log R_obs − E₀[log R]) | the reported R of the count-selected ticket is mostly selection inflation |
| E3 | Finite-population variance; Bayes-mixture learning cost (Rissanen; Clarke–Barron) | KL = 3(P−6)ε²/(P−1); E[log M_T] = T·KL − (d/2) log T + O(1) | d = 1 horizons are confirmed by simulation (§3); the d = P−1 horizons (~7,400–9,900 draws at ε = 10%) are illustrative only, because the Dirichlet(100) prior's ~5,000 pseudo-counts put them outside the asymptotic regime (referee panel, §7) |
| E4 | same | typical tilt: R* ≈ exp(ε s₆ − ½Σ_top6 δ²); worst case over RMS-ε tilts: exp(ε√(6(P−6))) (first order) | a known 1% tilt gives R ≈ 1.10 typical, 1.19 worst case; 10% gives ≈ 2.4–2.5 typical |
| E5 | prequential predictive likelihood (arXiv:2210.01948) | e = ∏ q_t(S_t)/p₀(S_t) on held-out draws | held-out evidence ≈ 1: approximate mixture monitor 0.67, a = 100 importance-sampled model 1.17 (product over five games) — no out-of-sample support either way |
| E6 | Stern–Cover, Poisson sharing (`conscious-selection-popularity.md`) | E[share] = (1 − e^{−λ})/λ, λ = λ̄ e^{βz} | popularity changes payout, never P(win); percentages illustrative (λ̄ implied by winner counts, counts overdispersed); gated until confirmed (§5) |
| E7 | Bayesian model averaging | normalised law q_mix = (1−π₁)p₀ + π₁q₁, R_mix = 1 + π₁(R − 1), π₁ = e/(1+e), e = held-out evidence of the a = 100 model (importance-sampled, approximate) | the picker's predictive multiplier; R_c and R_eff = π₀ + π₁R_c are null-centred diagnostics, not probabilities (amendment v2 §D, referee Codex); V(S) = (J/C)·R_eff·E[share] is the jackpot-tier term only, not the full expected value |

s₆ = E[sum of the top 6 of P iid N(0,1)] = 9.21 (P=42) … 10.18 (P=58); c̄ = 6T/P;
σ_c² = T(6/P)(1 − 6/P)·P/(P − 1).

## 2. Selection correction and model weight (`src/pcso_picker_calibration.py`)

`results/pcso_picker_calibration_2026-09-21.json`, seed 20260923, 1,000 uniform histories per game,
20,000 importance samples per posterior, the predictor of `src/pcso_next_draw_posterior.py` (a = 100).

| Game | R (reported) | R_null analytic / MC exp E₀[log R] | R_c | null tail p | held-out e (exact a=100; v2 mixture) | π₁ | R_eff |
|---|---|---|---|---|---|---|---|
| 6/42 | 1.477 | 1.430 / 1.444 | 1.023 | 0.323 | 1.108; 1.006 | 0.526 | 1.012 |
| 6/45 | 1.523 | 1.435 / 1.446 | 1.053 | 0.149 | 0.493; 0.304 | 0.330 | 1.018 |
| 6/49 | 1.578 | 1.439 / 1.449 | 1.089 | 0.044 | 3.202; 5.225 | 0.762 | 1.068 |
| 6/55 | 1.639 | 1.442 / 1.451 | 1.130 | 0.012 | 0.518; 0.293 | 0.341 | 1.044 |
| 6/58 | 1.497 | 1.442 / 1.453 | 1.030 | 0.238 | 1.291; 1.421 | 0.564 | 1.017 |

74–92% of log R is selection (log-space correction = division by the geometric mean of R under M₀).
The null tail p values are per game (MC SE ≤ 0.007 at 1,000 histories); Holm over five gives a minimum
of 0.06 — nothing survives. The analytic first-order estimate is within 0.02 of Monte Carlo in every
game. π₁ uses the held-out evidence of the same exact a = 100 model as R_c (referee GLM, §7); the v2
mixture monitor's pseudo-posterior value is shown for comparison only. With 200 histories the 6/55
tail p moved between 0.025 and 0.005 across seeds; 1,000 histories give 0.012 (MC SE ≈ 0.003); none survives Holm.

## 3. One-parameter tilts (`src/pcso_lowdim_eprocess.py`, registration draft)

`results/pcso_lowdim_eprocess_2026-09-21.json`. Directions `high31` and `index`, θ shared by the
five games, exact evidence process (no Monte Carlo inside it).

- Null check (4,000 × 2,400 pooled uniform draws): crossing rate of 1/α = 100 is 0.0095 (Ville bound 0.01).
- Power: θ = 0.05 → 98% crossed, median 921 pooled draws (~14 months at ~780 pooled draws/yr);
  θ = 0.10 → median 222.
- Exploratory (pre-registration draws, cannot confirm): full history M = 0.26; post-freeze M = 0.97;
  θ̂(high31) = 0.018 ± 0.014, θ̂(index) = 0.011 ± 0.014.
- Registered test (`docs/REGISTRATION_PCSO_LOWDIM_TILT.md`, DRAFT): 0 draws so far, M = 1.

Exact properties tested (`tests/test_pcso_lowdim_eprocess.py`, 3 passed): f_θ sums to 1 over all
6-sets; the mixture predictive has E₀[Λ] = 1 (martingale property); the law of m = #{i > cut} is exact.

## 4. Walk-forward prediction test (every draw predicted from earlier draws only)

Warm-up 30 draws per game; 844 scored draws (218 post-freeze). Under M₀ each predictable ticket's
overlap is Hypergeom(P, 6, 6), so the total has an exact null law (convolution).

| Ticket | rule | matches/ticket all (exp 0.733) | exact p all | p post-freeze | 3+ matches obs/exp | 6-matches |
|---|---|---|---|---|---|---|
| A | six largest past counts (picker) | 0.787 | 0.041 | 0.284 | 20 / 16.2 | 0 |
| B | ranks 7–12 | 0.763 | 0.256 | 0.655 | 18 / 16.2 | 0 |
| L | adaptive: six largest numbers if the pooled posterior mean θ > 0, else six smallest (always-largest: 653 matches, p = 0.123) | 0.760 | 0.318 | 0.153 | 21 / 16.2 | 0 |

Holm over the six looks: minimum 0.25. No rule reproduces the data better than uniform, and no
ticket matched a full draw (expected 7.5 × 10⁻⁵ over 844 draws).

## 4b. Model registry v1 leaderboard (`results/pcso_model_leaderboard_2026-09-21.json`, sha256 c5615c91…)

Exploratory real-data scores (pre-registration draws): evidence vs uniform over the full year / post-freeze —
uniform 1 / 1; dirichlet_cp_a100 30.5 / 1.34; tilt_high31 0.34 / 1.04; tilt_linear 0.19 / 0.89;
pair_parity 0.50 / 0.83; cp_nest 0.51 / 0.98; ensemble 5.53 / 1.19 (ensemble weight 0.92 on Dirichlet).
No model reaches 100; the Dirichlet evidence accrues pre-freeze and no low-dimensional structured
direction captures it (ball-specific heterogeneity or early-sample chance). MLE-existence gate: incidence
rank = P in all five games.

Registered v1 simulation criteria, scored exactly as registered:

| Claim | Criterion | Result | Verdict |
|---|---|---|---|
| C1 | ≤ 0.02 of 400 null streams cross 100 | evidence 0/400, SR 0/400 | PASS |
| C2 | CP-NEST median ≤ tilt_linear + 450 at θ = 0.05; ≥ 90% crossing at θ = 0.10 | 927 vs 1,161; 100% (all streams crossed, so conditional = censored median); M = 32 was not authorised for C2 by v1 (disclosed) | PASS |
| C3 bound | real-data CP-NEST evidence ≥ e^{−1.7T/1000} | 0.515 ≥ 0.185 | PASS |
| C3 collapse | median final v(0) ≥ 0.9 | 0.515; 0/400 ≥ 0.9 | **FAIL** (criterion ill-posed per referee Codex; withdrawn in amendment v2; this record stands) |

Cross-machine replay: the M5 Max (Apple M5 Max, identical Python 3.14.6 / numpy 2.5.2 / scipy 1.18.1)
regenerated the artifact byte-identically (sha256 c5615c91cbac4335…).

## 5. Decision layer

Jev check of the lab record (A4 = 0.22): the popularity slope β = 0.519 is exploratory and may not
enter the decision value before a fresh-draw confirmation (H6/H7, card Step 8). It is registered as
`pcso.popularity-share.confirm1`. Until then the picker shows R_mix (with R_c as a diagnostic) and keeps the sharing term
descriptive.

## 6. Jev validation log

| Check | Jev (noul) |
|---|---|
| lab verdict is i.i.d. uniform | 0.97 |
| raw R needs H5 bias correction | 0.73 |
| >31 over-draw is exploratory only | 0.78 |
| popularity usable in decisions now | 0.22 → gated |
| picker EV already folds evidence/popularity | 0.08 |
| registration: test/data/threshold defined | 0.73 |
| registration: replication before picker change | 0.97 |
| registration: self-promotion | 0.05 |
| registration: free parameter after data | 0.09 |
| registration: betting metaphors | 0.07 |
| registration: alters m = 9 family | 0.05 |

## 7. Mathematician referee panel

Seats: GLM 5.3 and Kimi K3 (pi via the homelab gateway), Codex gpt-6-astra at xhigh (Codex CLI in a private
herdr session, read-only sandbox; run outside the codex-review preflight channel under a one-off lab-owner
authorisation, 2026-09-23, because 5 of 7 bundle components were missing; the bundle was then restored);
builder GLM 5.3 flash; local Qwen3.8-27B via oMLX on the M5 Max. Round 1 (GLM, Kimi) verified E1–E9 and
corrected E4 (typical vs worst-case oracle) and E7 (model mismatch). Round 2 (Codex) overruled parts of the
first design review (batch-MAP rate, curvature bound, level-0 collapse, posterior reset) and found that
R_c/R_eff were being used as probabilities, that the harness lacked the registered window, and that the
popularity confirmation had an outcome-dependent stopping time. All accepted findings are implemented or
recorded in `docs/REGISTRATION_AMENDMENT_2026-09-23_V2.md`. Research round 1 (seven peer-reviewed papers
read in full) is recorded in `docs/plans/PCSO_MODEL_REGISTRY_PLAN.md` §3b.
