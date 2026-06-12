# REGISTRATION (DRAFT — CLOSED 2026-06-11: archived as eval-Q2 artifact, never
# approved; lab owner elected to proceed to the real tidal target instead.
# Preserved for the dispatch record. NOT APPROVED, NOT HASHED, NO LICENSE TO FIT)

Status: PROPOSAL ONLY. Requires (a) the source detection claim's RESULTS +
attribution to be filed in results/run_ledger.jsonl first, (b) human approval,
(c) commitment-ledger hash PRE-RUN, (d) multiplicity charge. Drafted by the
equation-analyst during the eval-q2 gate refusal so a compliant run can be
dispatched quickly once the prerequisites exist. The drafting analyst has NOT
inspected the data values (header only), so this declaration is uncontaminated.

```yaml
equation_claim_id: eq.eval-q2-toy.periodic.v1
source_structure_claim: <FILL: claim id of the detection run, with RESULTS doc
  path, STRUCTURED verdict, post-freeze, and detection_analyst_id — currently
  MISSING; this registration is void until filled>
structure_verdict: STRUCTURED            # must be verified on file, not asserted
attribution_inputs: <FILL: H1 loop coordinates / dominant period band from the
  detection run's attribution output>
equation_type: periodic                  # one family class per claim (§4.4/§4.8)
candidate_family: [fourier_k1, fourier_k2, fourier_k3, circle_phase]
  # declared BEFORE any look at the data; K chosen by the selection rule below,
  # never extended post hoc. Per-harmonic sin/cos pairs only (no redundant
  # phase parameter); amplitude/phase reported as derived quantities.
inputs: [t]
target: [x_t]
fit_split: {train: first_60pct, validation: next_20pct, test: final_20pct}
  # chronological, no shuffling; test touched once, after selection
null_baseline: [permutation, phase_randomized_surrogate, AR1_null]
null_equation_generator: >
  B = 200 matched synthetic nulls (AR(1) fitted to TRAIN ONLY, plus
  phase-randomized surrogates of train), each pushed through the identical
  family-search + selection procedure; record distribution of recovered
  equations, complexities, and J scores; null-adjusted p computed against this
  distribution (A1 requirement, EQUATION_DISCOVERY.md §6)
selection_rule: min J(f) = L_validation(f) + lambda*complexity(f)
lambda: 2.0 per free parameter (BIC-like, ln(n_train)/2 ≈ 2.85 capped at 2.0;
  DECLARED HERE, never tuned after test scores — M1 guard)
complexity: count of free parameters (a0 + 2 per harmonic; circle_phase: dim(A)+dim(b)+phase-model params)
metrics: [RMSE, heldout_loglik, residual_autocorrelation(ljung_box),
  fisher_g_on_residuals, parameter_stability(bootstrap B=500),
  null_adjusted_p]
residual_checks: EQUATION_DISCOVERY.md §8 full table; structured residuals =>
  FAILED_EQUATION_SEARCH or new registration, never quiet extension
data_regimes: [all_rows]   # toy series has no suspicious/verified partition;
  # declared explicitly so the M4 column is not silently skipped
floors: coefficients below the card-19 detectability floor at n=500 for this
  noise level are reported as "below floor", never as candidates
multiplicity_charge: {family_id: eval_q2_equation_search, m_delta: 4}
seed_scheme: 20260611 (+500..+520), two-run verification by a second executor
  (Haiku, execute-only) with verbatim-output diff
verifier: independent-verifier instance != this analyst != detection analyst
public_claim_allowed: false_until_confirmed
max_verdict_without_fresh_data: PREDICTIVE_EQUATION
```

Approval block (human):
- [ ] Source detection claim filed and verified
- [ ] Family list / lambda / splits / nulls approved
- [ ] Hash appended to results/commitment_ledger.txt: ________________
- [ ] Multiplicity ledger row appended
