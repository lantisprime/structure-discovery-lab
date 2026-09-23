# REGISTRATION — pcso.registry.seq1 (CP-NEST, pair_parity, and the registry ensemble)

**STATUS: APPROVED 2026-09-23 (lab owner, in session).** This file, `src/pcso_model_registry.py` and
`tests/test_pcso_model_registry.py` are commitment-hashed into `results/commitment_ledger.txt` before
any draw dated after 2026-09-23 is scored.

Design: `docs/plans/PCSO_MODEL_REGISTRY_PLAN.md` (theory, research round 1 disposition).
Design review: Kimi K3, 2026-09-23 (core mathematics approved; this document answers its blocking items).
Relation to other registrations: `pcso.lowdim-tilt.seq1` and `pcso.popularity-share.confirm1`
(`docs/REGISTRATION_PCSO_LOWDIM_TILT.md`) are unchanged; the m = 9 family is unchanged.

## 1. Statistics (fixed here)

For each registered model k, with predictive law q^k_t built from draws before t only:
- evidence process E^k_t = ∏_{s≤t} q^k_s(S_s)/p₀(S_s), p₀ = 1/C(P_g, 6) for the game of draw s;
- weighted Shiryaev–Roberts e-detector M^k_t = L^k_t (M^k_{t−1} + w_t), L^k_t = q^k_t(S_t)/p₀(S_t),
  w_t = 1/(t(t+1)), t counted from the first registered draw.

**Headline statistic:** the ensemble evidence E^ens_t (prequential Bayesian mixture over the registered
models, equal prior weights over the six current models). Per-model evidence values are individually
valid; simultaneous per-model claims are made only through the ensemble or an e-BH statement.

**Registered models:** uniform, dirichlet_cp_a100, tilt_high31, tilt_linear, pair_parity, cp_nest,
with constants frozen as committed (CP-NEST: basis φ₁…φ₆ in the stated order, τ = 0.05, ρ = 10⁻³,
v₀(d) ∝ 2^{−d}, M = 128, antithetic common random numbers; grid models: 161 points on [−0.4, 0.4],
prior N(0, 0.1²); Dirichlet a = 100, 2,000 importance samples).

## 2. Error control and decision rule

α = 0.01. Rejection of the uniform-draw null by the ensemble: sup_t E^ens_t ≥ 100 (Ville: probability
≤ 0.01 under M₀ at every monitoring instant; peeking at every draw is permitted by construction).
Mechanism-change alarm: sup_t M^k_t ≥ 100 for the ensemble's increments (weights sum to ≤ 1, so the
false-alarm probability over the whole stream is ≤ 0.01). A rejection or alarm triggers one
replication on further fresh draws (H6) before any change to the picker.

## 3. Data, windows, and edge cases

Official draws dated after 2026-09-23, appended by the weekly pipeline with two-source validation
(DATASET.md §6); pooled filtration ordered by (date, game). All models are conditioned on every draw
dated on or before 2026-09-23 when the window opens (as in `pcso.lowdim-tilt.seq1`); the registered
statistics start at 1 (E) and 0 (M). Missed or cancelled draws: no update (validity unaffected).
Pool-size change or a new game: features, R_g and p₀ are recomputed from the new pool (θ stays
interpretable because features are standardised); the change date is recorded as an era boundary.

## 4. Disclosures

- φ₂ = 1[i > 31] was motivated by exploratory draws (RESULTS_PCSO_REFRESH §3). Its exploratory evidence
  was null (full-history M = 0.26; θ̂ = 0.018 ± 0.014). Error control is unaffected (fixed basis); a
  rejection along φ₂ is weaker confirmatory evidence than along an a-priori direction.
- τ = 0.05 (CP-NEST) differs from the grid models' prior sd 0.1; both are fixed here.
- The predicted 6-set is the maximum-inclusion set (six largest predictive inclusion probabilities):
  the mode of a single conditional-Poisson law and of the mixture to first order; it may differ from
  the exact mixture mode only at near-ties (gap ≤ ½ φ_Sᵀ Σ_t φ_S per level).
- Registry growth: models added later enter a new registration with prior weight ∝ 1/(n(n+1)) of the
  mixture mass by registration order n, so the ensemble's regret stays bounded as the registry grows.

## 5. Claims evaluated (from the design review) — pass criteria fixed before the results were seen

| Claim | Test | Data | Pass criterion |
|---|---|---|---|
| C1 error control (implementation regression; the guarantee is Ville) | fraction of simulated uniform streams with sup E_t ≥ 100, and with sup M_t ≥ 100 | 400 streams × the real 994-draw schedule, M = 32, seed 20260923+1000+s | both fractions ≤ 0.02 (α + 2 SE) |
| C2 detection delay vs the exact one-parameter process (simulation claim) | median pooled draws to E_t ≥ 100 under planted θ₁ on φ₁ | 50 streams per θ ∈ {0.05, 0.10}, horizon 2,982 pooled draws | CP-NEST median ≤ tilt_linear median + 450 at θ = 0.05, and ≥ 90% of CP-NEST streams cross at θ = 0.10 |
| C3 excess log-loss vs uniform (theorem) | fixed-share bound log(1/v₀(0)) + T·log(1/(1−ρ)) ≈ 1.7 nats per 1,000 draws | every sequence | holds deterministically; regression check: CP-NEST full-history evidence ≥ e^{−1.7·T/1000} on the real draws |
| C3 collapse (behavioural) | median of the final d = 0 weight v_T(0) under uniform draws | the 400 C1 streams | median v_T(0) ≥ 0.9 |
| C4 null part | total matches of each registered model's maximum-inclusion set, exact two-sided test (convolution of Hypergeom(P,6,6)) | draws dated after 2026-09-23 | flag if the Holm-adjusted p over the six registered models' looks is < 0.01; a flag triggers the H6 replication |

A failed criterion is reported as such and blocks promotion of the model until a revised model is
registered anew.

## 6. Frozen implementation and conformance

`src/pcso_model_registry.py`; `tests/test_pcso_model_registry.py` (exact normalisation of every model's
law by enumeration, predictability/bit-determinism gate, exact inclusion probabilities, sampler exactness,
Shiryaev–Roberts recursion identity, confidence-sequence nesting). Any change to a registered model's
constants after approval voids its registration.
