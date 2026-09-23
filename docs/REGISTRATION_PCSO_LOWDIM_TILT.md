# REGISTRATION — pcso.lowdim-tilt.seq1 and pcso.popularity-share.confirm1

**STATUS: APPROVED 2026-09-23 (lab owner, in session).** This file and the scripts it names are
commitment-hashed into `results/commitment_ledger.txt` BEFORE any draw dated after the registration
date is scored. No draw dated after 2026-09-23 exists at approval time.

Derivation and exploratory evidence: `docs/RESULTS_PCSO_PICKER_THEOREM_2026-09-23.md`.

## 1. pcso.lowdim-tilt.seq1 — sequential test of two one-parameter weight tilts

**Why low-dimensional.** By the Bayes-mixture learning-cost theorem (Rissanen 1986; Clarke &
Barron 1990) the expected log-evidence of a prequential test after T draws is
T·KL − (d/2)·log T + O(1). The lab's product-weight alternative has d = P − 1 (41–57) and needs
~7,400–9,900 draws per game to detect a 10% RMS weight deviation; a d = 1 alternative needs ~300.

**Model (fixed here).** Ball weights w_i(θ) = exp(θ·g(i)); a draw S has probability
f_θ(S) = ∏_{i∈S} w_i / e_6(w). Two directions g, each standardised to mean 0 and sd 1 over the pool:
- `high31`: g ∝ 1[i > 31] (motivated by the exploratory over-draw in RESULTS_PCSO_REFRESH §3);
- `index`:  g ∝ i.

θ is shared by the five games. Prior N(0, 0.1²) on the 161-point grid over [−0.4, 0.4].

**Statistic.** For each direction a, Λ^a_t = q^a_t(S_t)/p₀(S_t) with q^a_t(S) = Σ_θ π^a_{t−1}(θ) f_θ(S)
and p₀ = 1/C(P,6); M^a_t = ∏_{s≤t} Λ^a_s. The registered statistic is M_t = ½(M^high31_t + M^index_t),
an e-process under the uniform-draw null (arXiv:2210.01948 §2.9, §3.2.2). The θ posterior at the
registration date is conditioned on all earlier draws; M starts at 1.

**Data.** Official draws dated after 2026-09-23, appended by the weekly pipeline with two-source
validation (DATASET.md §6); all five games in one filtration ordered by (date, game name).
No end date: the test is anytime-valid.

**Decision rule.** α = 0.01. If sup_t M_t ≥ 1/α = 100, the uniform-draw null is rejected in favour
of the tilt; Ville's inequality bounds the false-rejection probability by 0.01 at every monitoring
instant. Otherwise the null stands and monitoring continues. A rejection triggers one replication
on further fresh draws (H6) before any change to the picker.

**Calibration (exploratory, already run).** Null simulation, 4,000 replicates × 2,400 pooled uniform
draws: crossing rate 0.0095 (bound 0.01; the guarantee is Ville's inequality, the simulation is a
check). Power: θ = 0.05 → 98% crossed, median 921 pooled draws; θ = 0.10 → 100%, median 222. Exploratory evidence on pre-registration draws (not evidence for
this test): full history M = 0.26; post-freeze M = 0.97.

**Frozen implementation.** `src/pcso_lowdim_eprocess.py` (constants `REGISTERED_AFTER`, `ALPHA`,
`THETA`, `PRIOR_SD`, `ALTERNATIVES`); exact properties tested in `tests/test_pcso_lowdim_eprocess.py`.
Any change to model, prior, grid, directions or α after approval voids this registration.

## 2. pcso.popularity-share.confirm1 — fresh-draw confirmation of the sharing slope

Card 28 (`docs/kb/conscious-selection-popularity.md`) found jackpot winners ∝ exp(0.519·z_CSI)
(HC1, count ratio 1.68 per SD) on 984 exploratory draws. Step 8 and H6/H7 bar its use in the
picker's decision value until it is confirmed on fresh draws.

**Test.** On official draws dated after 2026-09-23: the Poisson pseudo-MLE of winners on the
within-game standardised CSI with game fixed effects and log-jackpot, as in `src/csi_popularity.py`,
with the CSI weights frozen exactly as committed. H₀: β ≤ 0; one-sided HC1 Wald test at α = 0.05.
**Evaluation point:** the first refresh at which the fresh set holds ≥ 90 winning tickets (the
exploratory sample had 94; at the observed ~0.09 per draw that is about one year).

**Consequence.** If confirmed, the picker's decision value becomes
V(S) = (J/C)·[π₀ + π₁·R_c(S)]·(1 − e^{−λ(S)})/λ(S), λ(S) = λ̄·exp(β z(S)).
If not, the sharing term stays descriptive.

## 3. What this registration does not change

The m = 9 confirmation family, its threshold and its data (DATASET.md §6) are unchanged. Both
tests here carry their own error budgets and never feed the m = 9 family.
