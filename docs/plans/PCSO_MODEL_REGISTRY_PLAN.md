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

## 4. Falsifiable claims to test

C1 CP-NEST's evidence process keeps error control under uniform draws (null crossing ≤ α).
C2 Under a planted smooth tilt (θ₁ = 0.05), CP-NEST reaches 1/α in fewer draws than the Dirichlet(100) model.
C3 On held-out draws CP-NEST's predictive log-score is ≥ uniform's minus its learning cost; it collapses to
   d = 0 weight when nothing is present (v(0) → high).
C4 Its predicted set does not beat uniform in the walk-forward test unless C2-type structure exists (E1).
