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
| E5 | prequential predictive likelihood (arXiv:2210.01948) | e = ∏ q_t(S_t)/p₀(S_t) on held-out draws | held-out evidence ≈ 1: approximate mixture monitor 0.67, exact a = 100 model 1.17 (product over five games) — no out-of-sample support either way |
| E6 | Stern–Cover, Poisson sharing (`conscious-selection-popularity.md`) | E[share] = (1 − e^{−λ})/λ, λ = λ̄ e^{βz} | popularity changes payout, never P(win); percentages illustrative (λ̄ implied by winner counts, counts overdispersed); gated until confirmed (§5) |
| E7 | Bayesian model averaging | R_eff = π₀ + π₁ R_c, π₁ = e/(1 + e), e = exact a = 100 held-out evidence | the picker's multiplier, replacing equal-odds R_mix; V(S) = (J/C)·R_eff·E[share] is the jackpot-tier term only, not the full expected value |

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
tail p moved between 0.025 and 0.005 across seeds; 1,000 histories settle it at 0.012.

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
| L | one-parameter argmax (six largest numbers) | 0.760 | 0.318 | 0.153 | 21 / 16.2 | 0 |

Holm over the six looks: minimum 0.25. No rule reproduces the data better than uniform, and no
ticket matched a full draw (expected 7.5 × 10⁻⁵ over 844 draws).

## 5. Decision layer

Jev check of the lab record (A4 = 0.22): the popularity slope β = 0.519 is exploratory and may not
enter the decision value before a fresh-draw confirmation (H6/H7, card Step 8). It is registered as
`pcso.popularity-share.confirm1`. Until then the picker shows R_eff and keeps the sharing term
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

(pending)
