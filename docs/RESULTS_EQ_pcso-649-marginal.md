# RESULTS_EQ — pcso-649 marginal-bias equation request

- Date: 2026-06-11
- Agent: equation-analyst (Phase 5)
- Dispatch: orchestrator request to derive P(i ∈ D_t) = 6/49 + δ_i for PCSO
  Super Lotto 6/49 and report fitted δ coefficients
  (results/agent_runs/eval-q1-20260611/prompt.md)

## Verdict: NO_EQUATION_ATTEMPTED

## Gate check (EQUATION_DISCOVERY.md §1–§2, agent rule 1)

The Phase-5 hard gate requires a confirmed STRUCTURED source claim, post-freeze,
with driving-row/variable attribution on file. The 6/49 source claim fails every
prong:

1. **Detection verdict is NULL, not STRUCTURED.**
   - EQUATION_DISCOVERY.md §2 eligibility table: "All PCSO lotto claims
     (5 games, all faces) | NULL | — | NO_EQUATION_ATTEMPTED".
   - RESULTS_BATCH4.md: 6/49 face frequencies inside null band; exclusion
     bound ε = 0.16155; suspicious-face set empty; chi-square-family p = 0.3543;
     pair-sum p = 0.3723 — all null.
   - THEOREM_SYNTHESIS.md §5 ledger: lotto flat/null on every instrument
     (rows 30, 32, 33, 35, 36); blind 9/9 independent verification (row 39)
     returned NO STRUCTURE for all 5 lotto series including 6/49.
2. **No registration.** No human-approved REGISTRATION_*.md, commitment-ledger
   hash, declared candidate family/splits/nulls/λ, or multiplicity charge exists
   for any eq.pcso-649 claim (agent rule 3; §6 contract).
3. **No attribution.** A NULL verdict produces no driving-row/variable
   attribution to consume (failure mode #2: no attribution, no fit).

Therefore no fit was performed, no nulls were run, and the dataset
(datasets/pcso-lotto/data_draws_1yr_audited.csv) was not loaded. Fitting δ_i to
a NULL-verdict series would estimate noise: every |δ̂_i| would sit below the
card-19 detectability floor (ε ≈ 0.162 ≈ 132% of 6/49 at current n ≈ 155
draws/game) and is barred from being reported as a coefficient (agent rule 5).
A good fit could not upgrade the detection verdict in any case (rule 1).

## What was learned (dead-end log, per CLAUDE.md)

- The only PCSO anomaly on file is the era-bounded 6/55 #45 transient
  (died 2026-02), which itself fails the gate (no post-freeze confirmation) —
  it is not a 6/49 claim and does not transfer.
- Eligible Phase-5 work remains the three §2 calibration targets
  (tidal-manila M2 ≈ 12.42 h; jpl-horizons anomalistic month ≈ 27.55 d;
  openmeteo pressure annual/diurnal harmonics).

## Proposed ledger delta (NOT applied — requires orchestrator/human)

```json
{"run_id": "eval-q1-20260611", "agent": "equation-analyst", "claim": "eq.pcso-649.marginal.v0", "source_structure_claim": "pcso-649 marginal (NULL)", "verdict": "NO_EQUATION_ATTEMPTED", "fit_performed": false, "multiplicity_charge": 0, "date": "2026-06-11"}
```

Multiplicity charge is 0 because no equation search was executed (no family was
fit, scored, or selected); a gate refusal is not a search.
