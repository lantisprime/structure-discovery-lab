# REGISTRATION — pcso.sparse.seq1 (cp_sparse_switch: sparse ball-specific deviations)

**STATUS: APPROVED 2026-09-24 (lab owner, in session). Registration date: 2026-09-23.** This file,
`src/pcso_sparse_switch.py` and `tests/test_pcso_sparse_switch.py` are commitment-hashed into
`results/commitment_ledger.txt` before any simulation in §5 is run and before any draw dated after the
registration date is scored. The first scored draws are those dated 2026-09-24.

Design: `docs/plans/PCSO_MODEL_REGISTRY_PLAN.md` §3c (research round 2 dispositions; model approved by the lab
owner 2026-09-23). Review: GLM 5.3 APPROVE, Kimi K3 APPROVE, GPT Astra 6 APPROVE-WITH-CHANGES (PR #50).
Relation to other registrations: `pcso.registry.seq1` (and its ensemble), `pcso.lowdim-tilt.seq1`,
`pcso.popularity-share.confirm1` and the m = 9 family are unchanged. `cp_sparse_switch` is NOT added to the
`pcso.registry.seq1` ensemble; per that registration's §4 it enters as a new registration.

## 1. Statistics (fixed here)

Model `cp_sparse_switch`, constants frozen as committed: experts = uniform, and for one game a support A with
|A| ∈ {1, 2} and log-weights θ_i ∈ {−1, −0.5, −0.25, 0.25, 0.5, 1}; exact conditional-Poisson law
f(S) = exp(Σ_{i∈S∩A} θ_i)/Z; prior w₀ = 1/2, 1/10 per game, Pr(k = 1) = 2/3, Pr(k = 2) = 1/3, uniform over supports
and grid values; switching ρ_t = 1 − e^{−τ(t)}, τ(t) = 1/log(t + e − 1) − 1/log(t + e), t = pooled draw count
from the first registered draw.

- Evidence process E_t = ∏_{s≤t} q_s(S_s)/p₀(S_s), p₀ = 1/C(P_g, 6).
- Weighted Shiryaev–Roberts e-detector M_t = L_t (M_{t−1} + w_t), w_t = 1/(t(t+1)), as in pcso.registry.seq1.

## 2. Error control and decision rule

α = 0.01. Rejection of the uniform-draw null: sup_t E_t ≥ 100 (Ville). Mechanism-change alarm: sup_t M_t ≥ 100.
If both statistics are used for one combined decision, α is split 0.005/0.005 (two separately valid 1% alarms
are not one 1% procedure). A rejection or alarm triggers one replication on further fresh draws (H6) before any
change to the picker.

## 3. Data, windows, and edge cases

Official draws dated after the registration date, two-source validated (DATASET.md §6); pooled filtration ordered
by (date, game). Conditioning: the model is conditioned on every draw dated on or before the registration date;
E and M then start at 1 and 0 and the switching clock restarts at t = 1. Missed or cancelled draws: no update.
A pool-size change or a new game voids the expert dictionary for that game and requires a new registration.

## 4. Disclosures

- The target alternative (k ≤ 2 specific balls of one game) and the grid were chosen from the literature
  (plan §3c), not from the data; no exploratory fit of cp_sparse_switch to the real draws was made before this
  registration.
- Weak deviations are out of reach by design: for w = 1.1 no level-1% test has more than ≈ 2–4.5% power by 200
  draws of the affected game (Balakrishnan–Wasserman second moment, exact 6-subset form). A null result is
  therefore not evidence against small ball-specific deviations.
- k = 3 supports and continuous log-weights are deferred (compute); an MLX GPU port (exploratory, float32,
  paired-validated against CPU float64) may study them but produces no registered number.

## 5. Claims evaluated — pass criteria fixed before any result is seen

Simulations run on CPU float64 (M5 Max), seeds 20260923 + 5000 + s.

| Claim | Test | Data | Pass criterion |
|---|---|---|---|
| S1 error control (regression; the guarantee is Ville) | fraction of uniform streams with sup E_t ≥ 100, and with sup M_t ≥ 100 | 400 streams × the real pooled schedule (all draws to the registration date) | both fractions ≤ 0.02 |
| S2 excess log-loss vs uniform (theorem) | −log E_T ≤ log 2 + Σ_{t<T} τ(t) (≤ 1.693) | every S1 stream, one 10,000-draw uniform stream, and the real draws | holds at every T on every stream |
| S3 planted sparse power | fraction of streams crossing 100 within 200 draws of the affected game (pooled schedule, balanced) | 100 streams per cell: k ∈ {1, 2}, P ∈ {45, 58}, θ = 1 on a uniformly random support | crossing fraction ≥ the exact lower bound from `crossing_lower_bound` minus 2 SE, AND strictly greater than CP-NEST's and Dirichlet(100)'s crossing fractions on the same streams |
| S3b secondary (reported, no pass criterion) | as S3 | θ ∈ {0.25, 0.5}, mixed signs, unequal magnitudes | reported only |
| S4 weak-signal limit (sanity) | crossing fraction within 200 affected-game draws | 400 streams, w = 1.1, k ∈ {1, 2}, P ∈ {45, 58} | ≤ BW bound + 2 SE; a violation flags an implementation error |
| S5 tracking (theorem + measurement) | cumulative excess log-loss vs the no-switch-then-switch comparator path; detection delay | deviation (k = 1, θ = 1, P = 45) switched on at pooled draw 200 and off at 700; 100 streams | Lemma 1 path bound holds on every stream; median delay reported |

A failed criterion is reported as such and blocks promotion of the model until a revised model is registered
anew.

## 6. Frozen implementation and conformance

`src/pcso_sparse_switch.py`; `tests/test_pcso_sparse_switch.py` (exhaustive normalization and inclusion over all
6-subsets on small pools, dense-reference recurrence including 10,003-draw inactive/unseen-game histories,
predictability, the pathwise bound on adversarial sequences, helper values against enumeration, harness `run()`
compatibility). Any change to the model's constants after approval voids this registration.
