# REGISTRATION AMENDMENT v2 — pcso.registry.seq1, pcso.lowdim-tilt.seq1, pcso.popularity-share.confirm1

**STATUS: APPROVED 2026-09-23 (lab owner, in session; plan and text).**
Written before any draw dated after 2026-09-23 exists or is scored. On approval this file and the amended
implementation are commitment-hashed before the first registered draw. The v1 documents stay in the
repository unchanged; v1 results already computed are reported **as registered, failures included**.

Source of every change: the senior referee (Codex gpt-6-astra, xhigh) design/implementation audit and
round-2 report, 2026-09-23, which also overruled parts of the first design review (Kimi K3).

## A. pcso.registry.seq1 → seq1-v2

| # | v1 text | v2 | Reason |
|---|---|---|---|
| A1 | Registered window stated but not implemented | `run_registered`: draws ≤ 2026-09-23 condition the models only; evidence E starts at 1 and the Shiryaev–Roberts M at 0 at the first registered draw, t counted from it | Harness omitted the boundary (audit §2) |
| A2 | Ensemble and alarm each "≤ 0.01" | Each keeps its own α = 0.01; the decision "either crosses" has family error ≤ 0.02 (union bound), stated as such | Joint error policy missing (audit §2) |
| A3 | C2 median over crossing streams, M = 32 | Censoring-aware lower median over all streams ("not reached by horizon" when infinite), n_crossed, one-sided 95% Clopper–Pearson bound; CP-NEST at production M = 128 | Conditional median biased; M not authorised for C2 (audit §6) |
| A4 | C3 bound "≈ 1.7 nats per 1,000 draws" | −log E_T ≤ −log v₀(0) + (T−1)·log(1/(1−6ρ/7)); conservative form 0.685304 + 0.0010005·T | v1 scaled the prior penalty with T; one-draw counterexample (audit §6) |
| A5 | C3 collapse: median v_T(0) ≥ 0.9 | **Withdrawn** as ill-posed: under M₀ fixed-share weights tend to uniform over levels, not to level 0. The v1 result is reported unchanged. Replaced by a descriptive report of predictive convergence to uniform (no pass/fail) | Audit §6 |
| A6 | C4 Holm "over registered looks" | Fixed terminal analysis at 780 registered pooled draws (≈ 1 year); Holm across the six registered models at that analysis only; earlier values descriptive | Repeated fixed-horizon looks are not protected by Holm (audit §6) |
| A7 | Mode-gap certificate ≤ ½ φ_SᵀΣφ_S; "mixture mode to first order" | **Withdrawn.** The maximum-inclusion set maximises expected overlap exactly; it equals the joint mode for a single conditional-Poisson law, not in general for mixtures, and not for pair_parity | Counterexamples: 0.353-nat symmetric-mixture gap; 0.108-nat Monte Carlo gap above the "bound" (audit §5) |
| A8 | Confidence sequences reported as intervals | Labelled confidence sequences over the declared 161-point grid | Grid inversion is not a continuous-parameter CS (audit §7) |
| A9 | Ensemble reported beside standalone models | Registered ensemble reports its own components' cumulative evidence | Standalone and ensemble components are different randomised predictors (audit §7) |
| A10 | `--verify` read live inputs | Draws ≤ 2026-09-23 read from commit `bcf39ca` under `--verify` | Frozen-input reproducibility (audit §7) |
| A11 | Basis "fixed a priori"; high31 rejection "weaker evidence" | Basis fixed before registered evaluation; a fresh rejection is valid confirmation of the ensemble alternative but gives no automatic feature-specific or causal attribution | Audit §4 |

Unchanged: every model's constants and predictive mathematics, α = 0.01, thresholds 100, weights 1/(t(t+1)).

## B. pcso.lowdim-tilt.seq1 → seq1-v2 (text corrections; statistic unchanged)

- The d = P−1 detection horizons (~7,400–9,900 draws per game at ε = 10%) are withdrawn as quantitative
  claims: with Dirichlet(100) the Clarke–Barron constant is material at that dimension (referees GLM and Codex).
  The d = 1 statement stands on simulation.
- The quoted power figures (θ = 0.05: median 921; θ = 0.10: 222 pooled draws) are medians conditional on
  crossing, under initialisation at the prior. The registered process conditions on history; power figures
  for it will be re-derived with censoring-aware medians under that initialisation.
- Pooling five games requires joint conditional uniformity P₀(S_t | 𝓕_{t−1}, P_t) = 1/C(P_t, 6); stated explicitly.

## C. pcso.popularity-share.confirm1 → confirm1-v2

- **Evaluation time:** the first refresh on or after **2027-09-23** (fixed calendar endpoint), replacing the
  outcome-dependent "≥ 90 winning tickets" rule.
- **Test:** W = β̂ / ŝe_HC1 > Φ⁻¹(0.95), declared an **asymptotic** test under the stated mean-model and
  dependence assumptions, CSI weights frozen as committed.
- **Mean matching:** λ(z) = λ̄ · e^{βz} / E_ref[e^{βZ}] at fixed exposure, with game and jackpot effects handled
  as in `src/csi_popularity.py`.
- **Promotion:** a confirmation is followed by one H6 replication on further fresh draws before the sharing
  term enters any decision value; confirming β > 0 validates the direction, not the Poisson sharing law or
  absolute λ(S).

## D. Picker (not a registration; corrected alongside)

The picker's predictive multiplier becomes the normalised model-averaged law
q_mix(S) = (1 − π₁) p₀(S) + π₁ q₁(S), i.e. R_mix = 1 + π₁ (R_post − 1), with π₁ from the held-out evidence.
R_c (H5) is shown separately as a null-centred **diagnostic**, never as a probability.
