# PCSO model registry and the CP-NEST prediction model — design (2026-09-23, DRAFT)

Goal (lab owner, 2026-09-23): novel estimation and prediction models that the lab can reuse and
improve over time as new techniques and peer-reviewed research arrive. Under A0 this is a
self-improving prediction layer: new models enter through a fixed, theorem-backed harness, and a
prequential mixture reallocates weight to whatever predicts fresh draws better, with error control
that no added model can break.

## 1. Lessons this design is built on (docs/RESULTS_PCSO_PICKER_THEOREM_2026-09-23.md)

| Lesson | Evidence | Design consequence |
|---|---|---|
| L1 Under M₀ no predictable rule changes P(S = D) (E1, Doob) | theorem | every model must be able to collapse to uniform; uniform is a member |
| L2 The count-selected set's multiplier is 74–92% selection inflation (E2, H5) | MC null, 1,000 histories | the harness null-calibrates every reported multiplier |
| L3 Learning cost (d/2)·log T dominates at d = P−1 (E3, Clarke–Barron) | held-out evidence ≈ 1 for the Dirichlet model (0.67 approximate monitor, 1.17 exact a = 100): no out-of-sample support after ~44 draws/game | low dimension, paid for only when the evidence supports it (nested levels, MDL prior) |
| L4 One-parameter tilts are detectable in ~200–900 pooled draws (E8) | simulated power | parameters shared across the five games (5× data) |
| L5 A normalized, predictable predictive law gives an e-process, whatever the approximation (E8, U1) | exact tests | approximations may cost power, never validity |
| L6 Monitoring must adapt to mechanism changes (e-detector, §9.1) | lab monitors | fixed-share mixing over levels (tracking) |

## 2. CP-NEST: nested conditional-Poisson tilts with fixed-share mixing

**Features.** For game g with pool P and ball i, u_i = (i − ½)/P. Ordered, fixed a priori:
φ₁ = Legendre P₁(2u−1), φ₂ = 1[i > 31], φ₃ = P₂(2u−1), φ₄ = 1[i odd], φ₅ = P₃(2u−1), φ₆ = P₄(2u−1);
each standardised to mean 0 and sd 1 over the pool, so θ_k is an RMS log-weight deviation.

**Level d ∈ {0,…,6}.** w_i(θ) = exp(Σ_{k≤d} θ_k φ_k(i)); f_θ(S) = ∏_{i∈S} w_i / e₆(w) (the conditional-Poisson
exponential family on 6-sets; d = 0 is uniform). θ is shared by the five games. Prior θ ~ N(0, τ² I_d), τ = 0.05.

**Online Laplace (assumed-density) posterior per level.** After draw S in game g:
- precision Λ_t = Λ_{t−1} + F_g, with F_g = Cov₀(Σ_{i∈S} φ_i) = 6(P−6)/(P−1) · R_g (the exact one-draw Fisher
  information at θ = 0; R_g = feature correlation matrix over pool g; data-independent);
- mean μ_t = μ_{t−1} + Λ_t⁻¹ (φ_S − E_{μ_{t−1}}[φ_S]), E_θ[φ_S] = Σ_i π_i(θ) φ_i, π_i = w_i e₅(w_{−i}) / e₆(w).
The log-likelihood is concave in θ (log e₆ is a log-partition function), so the posterior is log-concave
and near-Gaussian; F at θ = 0 is exact to O(‖θ‖).

**Predictive per level.** q^d_t(S) = (1/M) Σ_m f_{θ_m}(S), θ_m = μ_{t−1} ± L_{t−1} z_m (antithetic pairs,
Λ⁻¹ = LLᵀ), M = 128, z_m seeded by (seed, t), drawn before S_t is used. Each q^d_t is a normalized law on
6-sets built from the past only.

**Fixed-share mixture over levels** (Herbster & Warmuth 1998, Machine Learning 32:151–178):
ṽ_t(d) ∝ v_{t−1}(d) q^d_t(S_t); v_t = (1 − ρ) ṽ_t + ρ/7; v₀(d) ∝ 2^{−d}; ρ = 10⁻³.
Model predictive Q_t(S) = Σ_d v_{t−1}(d) q^d_t(S).

**Guarantees.**
- Validity: Q_t is normalized and predictable ⇒ E_t = ∏_{s≤t} Q_s(S_s)/p₀(S_s) is a nonnegative martingale under
  M₀; Ville ⇒ P(sup E_t ≥ 1/α) ≤ α.
- Tracking: cumulative log-loss regret against the best level sequence with m switches is
  ≤ log(1/v₀(d*)) + m·log(7/ρ) + T·log(1/(1−ρ)) (fixed-share bound).
- Within a level, Bayes-mixture regret ≈ (d/2) log T + O(1) (Clarke–Barron), d ≤ 6 ≪ P − 1.

**Prediction output.** Predictive inclusion probabilities π̄_i = Σ_d v(d)·mean_m π_i(θ_m); predicted 6-set =
the six largest π̄_i; multiplier R = C(P,6)·Q_t(S*), null-calibrated by the harness (L2).

## 3. Registry and harness

`src/pcso_model_registry.py`: interface (`name`, `theory`, `d`, `reset()`, `predict(game) -> law`,
`update(game, S)`; a law exposes `logq(S)`, `inclusion()`, `top6()`); models: uniform, Dirichlet(100)
product-weight (exact IS), the two one-parameter tilts, CP-NEST; the ensemble = prequential Bayesian mixture over
all registered models (equal prior weights), itself a model. Harness (deterministic, model-agnostic):
prequential evidence vs uniform (full history, post-freeze, post-registration), walk-forward exact match test,
conformance tests (exact normalization by enumeration on a small pool; predictability), null simulation of
error control, planted-tilt power. Output `results/pcso_model_leaderboard_<date>.json`, `--verify`.

**Intake loop for new research:** arXiv scan (Jev screen on abstracts) → a mathematician distils the full paper
→ proposal as a plug-in (q(S | past), d, theorem) → conformance tests → registration hash → scored on draws after
its registration date; earlier scores are exploratory.

## 3b. Research round 1 (2026-09-23) — team proposals and lead disposition

Seven peer-reviewed full texts screened by Jev on abstracts, then read in full and distilled by the
team (GLM 5.3, Kimi K3; the Codex seat was blocked by an expired OAuth token). Reports:
session scratchpad `research_glm.md`, `research_kimi.md`.

| Proposal | Source (peer-reviewed) | Disposition | Implemented as |
|---|---|---|---|
| Second-order parity-pair tilt, exact 7-term normalisation | Fienberg & Rinaldo, Ann. Statist. 40(2) 2012 | ACCEPT | `ParityPair` registry model (first model outside the first-order class) |
| MLE-existence gate (rank-P incidence, Cor. 6) | same | ACCEPT-WITH-MOD (rank check only; cone enumeration deferred) | `rank_gate` in the harness output |
| Full pairwise log-linear model | same (Thm 3/Cor 6) | REJECTED by the theorem: MLE nonexistent at T ≈ 200 (~7.8% null pair margins) | — |
| Excess-certainty calibration monitor | James, Radchenko & Rava, JASA 2022 | DEFER (diagnostic; modest derived power) | — |
| EC-oracle quoting of multipliers | same, Thm 1 | REJECT (derived effect 0.1–0.2%) | — |
| Anytime-valid confidence sequences for θ by e-process inversion | Lindon & Malek, NeurIPS 2022, Thm 2.4 | ACCEPT | `GridModel.cs(α)` for every one-parameter model |
| Weighted Shiryaev–Roberts e-detector on exact increments | Shin, Ramdas & Rinaldo, NEJSDS 2023, Defs 2.8–2.11, Rem. 2.7 | ACCEPT | harness `sr_edetector_max` for every model + null check |
| Asymptotic time-uniform CS | Gnettner & Kirch, Stat. Probab. Lett. 2025 | NULL (dominated by exact e-process CS at our n) | — |

GLM also confirmed from Fienberg–Rinaldo that CP-NEST's null Fisher information F_g = Cov₀(Aᵀn) is the
correct precision update, and that shared-θ pooling enlarges the relative interior of the pooled
convex support (Minkowski sum) — the geometric reason pooling is robust.

## 3c. Research round 2 (2026-09-23) — sparse ball-specific deviations: dispositions

Problem: a deviation confined to k ≪ P specific balls of one game. CP-NEST captures only ≈ d/(P−1) of such a
signal (13.6% at P = 45, d = 6) and the per-ball Dirichlet pays ((P−1)/2)·log T = 116.6 nats (P = 45, T = 200).
Intake: `tools/research_intake.py` (targeted arXiv scan, Jev relevance 0.92–1.17; lead re-routing so every seat
reads; 8 full texts). Readers: GLM 5.3, Kimi K3, GPT Astra 6 (reports in the session scratchpad). Lead checks were
exact computations (below). Owner approved the model and this disposition 2026-09-23.

| Proposal | Source (peer-reviewed) | Disposition | Evidence / reason |
|---|---|---|---|
| Exact sparse conditional-Poisson experts + uniform atom + summable switching (`cp_sparse_switch`) | Koolen & de Rooij, IEEE Trans. Inf. Theory 59(11) 2013, Lemma 1, Thm 11 (eq. 14) | ACCEPT-WITH-MOD (k ≤ 2 exact; k = 3 deferred) | normalized predictable law ⇒ valid evidence process; −log E_T ≤ log 2 + Σ_t τ(t) ≤ 1.693 nats on every sequence; k = 3 is 7.3M experts per game, k ≤ 2 about 223k in total |
| Support prior with mass ≈ 1/2 on "no deviation" and explicit support cost log C(P,k) | Castillo & van der Vaart, Ann. Statist. 40(4) 2012, Ex. 2.2, Thms 2.1/2.5 | ACCEPT-WITH-MOD (prior design; the theorems are for the Gaussian sequence model) | learning cost k·log P + (k/2)·log T: 7.2 / 13.6 nats (k = 1/2, P = 45, T = 200) |
| Heavy-tailed, not Gaussian, prior on log-weights | same, Thm 2.8 | ACCEPT (finite two-sided grid, equal mass per value) | Gaussian slabs shrink large deviations |
| Finite-sample impossibility bound for weak sparse deviations (exact 6-subset second moment) | Balakrishnan & Wasserman, Ann. Statist., Lemma 3 | ACCEPT-WITH-MOD (registered sanity bound) | lead-verified: P = 45, k = 1, w = 1.1, 200 draws ⇒ power ≤ 2.24% for any level-1% test, sequential tests included |
| Grid value \|θ\| = 0.1 | same | REJECT for the dictionary | undetectable at our sizes; saves prior mass |
| Exact-null-calibrated higher criticism; exact quadratic statistic A_n = Σ(C_i − np)² − nP·p(1−p) | Donoho & Jin, Ann. Statist. 32(3) 2004; Balakrishnan & Wasserman §3.1 | ACCEPT-WITH-MOD as diagnostics only | calibrated by uniform 6-subset simulation and alpha spending over looks; never part of the evidence product |
| Weighted empirical supremum | Stepanova & Pavlenko, Theory Probab. Appl. | DEFER | no established finite-sample gain over calibrated HC |
| Window-limited mixture scans; detectability-score rule | Xie & Siegmund, Ann. Statist. 41(2) 2013; Chan, Ann. Statist. | ACCEPT-WITH-MOD as design guidance | our sizes are in the Lorden domain, D ≈ 2·log γ / (k·(6/P)(1−6/P)·θ²); tracking comes from the switching model |
| Product-form per-ball evidence Π_i(1 − p₀ + p₀·e_i) | Kimi's adaptation of Chan / Xie–Siegmund | REJECT | lead check: with mixed-direction weights E₀ = 1.0001 (P = 45) and 1.0020 (P = 9, brute force) > 1; with equal weights it is constant (exactly six inclusions). e₆-normalized likelihood ratios are exact |
| GLR mixture score used as an e-variable | Xie & Siegmund eq. 7 | REJECT | E₀ exp((U⁺)²/2) = ∞ |
| Donoho–Ingster–Jin asymptotic constants ρ(β, ζ) | Donoho & Jin Thm 1.2; Chan Thms 1–2 | NULL (boundary result recorded) | for k ≤ 3 and log γ = 4.6–6.9 we are in the polynomial (Lorden) domain at P ≤ 58 |
| Sign, tail-run, longest-run, CUSUM-sign, Smirnov, signed-rank tests | Arias-Castro & Wang, TEST | NULL (dominated) | distribution-freeness is unneeded (the null is known); weakest at small n (their §4.2); no guarantee for mixed signs (§5.2) |
| Particle spike-and-slab with a continuous Laplace prior (k ≤ 3) | GLM synthesis on Castillo & van der Vaart | DEFER (k = 3 / continuous extension) | valid by normalization but loses the exact pathwise bound |
| Single-support model with an online Laplace parameter | Kimi synthesis | NULL (subsumed by the exact grid at k = 1) | the grid carries the exact finite-sample guarantee |
| Pooling a ball-specific parameter across games | — | REJECT | no shared mechanism for ball identity (L4) |

**`cp_sparse_switch` (approved for build).** Experts: uniform for all games, and for one game g a support A with
|A| ∈ {1, 2} and log-weights θ_i ∈ {−1, −0.5, −0.25, 0.25, 0.5, 1} (other games uniform). Expert law on game g:
f(S) = exp(Σ_{i∈S∩A} θ_i) / Z, Z = Σ_{B⊆A} C(P−|A|, 6−|B|)·exp(Σ_{i∈B} θ_i) (exact, ≤ 4 terms). Prior: w₀ = 1/2; the
other half split 1/5 per game, Pr(k = 1) = 2/3, Pr(k = 2) = 1/3, uniform over supports and grid values. Switching
(Koolen & de Rooij eq. 14): τ(t) = 1/log(t + e − 1) − 1/log(t + e), ρ_t = 1 − e^{−τ(t)} on the pooled clock;
v_t = (1 − ρ_t)·Bayes(v_{t−1}, f(S_t)) + ρ_t·w. Exact lower bound (lead-verified): a planted θ = 1 deviation on one
ball at P = 45 crosses 1/α = 100 within 200 draws of that game with probability ≥ 70.2%.

Registration `pcso.sparse.seq1` (to be fixed before any scored draw): S1 null error control; S2 the 1.693-nat
bound on real and null streams; S3 planted θ = 1, k ∈ {1, 2}, P ∈ {45, 58}: crossing fractions ≥ the exact bounds
and above CP-NEST and Dirichlet(100) on the same streams (θ = 0.25/0.5 and mixed signs reported without a power
claim); S4 weak-signal power respects the Balakrishnan–Wasserman bounds; S5 appearance/disappearance paths obey
the Lemma 1 path bound. Scored window: draws dated after its own registration date.

## 4. Falsifiable claims to test

C1 CP-NEST's evidence process keeps error control under uniform draws (null crossing ≤ α).
C2 Under a planted smooth tilt (θ₁ = 0.05), CP-NEST reaches 1/α in fewer draws than the Dirichlet(100) model.
C3 On held-out draws CP-NEST's predictive log-score is ≥ uniform's minus its learning cost; it collapses to
   d = 0 weight when nothing is present (v(0) → high).
C4 Its predicted set does not beat uniform in the walk-forward test unless C2-type structure exists (E1).
