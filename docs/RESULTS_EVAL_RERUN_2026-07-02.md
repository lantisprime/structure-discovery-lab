# Eval-Set Rerun (structure_eval_set_v1) — Post-Remediation Methodology Check

2026-07-02 · trigger: CLAUDE.md ("when something changes that drastically alters the
behaviour of the project's agents and methodologies, execute an eval set") — the
audit remediation (AUDIT_RESOLUTION_2026-07-02.md) changed core infrastructure and
introduced corrected instruments.

Driver: `evals/structure_eval_set_v1/src/run_blind_eval_r2.py` (does not touch the
frozen Jun-11 artifact). Artifacts: `results/blind_eval_r2.json` (regression),
`results/blind_eval_r2_corrected.json` (corrected instruments). Answer key was
already unsealed on 2026-06-11; this rerun is a methodology-stability check, not a
new blind evaluation (a fresh blind eval requires a new sealed set — noted in §4).

## 1. Regression mode — registered battery, identical seed, remediated codebase

All 18 stages executed. Comparison against the frozen `results/blind_eval.json`:

**235 result leaves compared · 0 differences · 0 missing/extra keys.**

The remediated repo (rewritten `core/stats.py`, ledger schema v2, verifier suite,
non-destructive builders) reproduces the registered battery **p-for-p**. The
Jun-11 headline therefore carries over unchanged by construction:
**specificity 1.000 (0 FP / 45 TN), sensitivity 0.826 (19/23 TP), accuracy 0.941**
(`results/blind_eval_score.md`).

## 2. Corrected-instrument mode — audit M-3 standardized CCA

Same battery, same seed, with the two CCA stages using
`corrected_reruns.ridge_cca_heldout_std` (train-moment z-scoring before
whitening). Any difference is attributable to the fix alone.

| Stage | verdict flips | notes |
|---|---|---|
| draws_cross (10 pairs, Šidák α .0051) | **0** | max |Δp| = 0.0025; all 10 remain null (matches key: no planted cross-links among draw streams) |
| draws_sensor (5 streams, Šidák α .0102) | **0** | true links D, E still detected at the p-floor (0.0025); ρ̂ *increases* under standardization (D: 0.383→0.395, E: 0.456→0.463) — the predicted power gain, visible even here where features were already z-scored |

No other stage uses the changed instruments; their regression identity (§1) covers
them.

## 3. Verdict

The remediation is **behavior-preserving where it should be** (bit-identical
registered battery) and **beneficial where it changes anything** (CCA effect sizes
move up, no false positives introduced). The eval-set precondition for the next
verdict-bearing publication is satisfied for the infrastructure and M-3 changes.

## 4. Scope limits (stated plainly)

1. This is a rerun against an **unsealed** key — it validates stability, not blind
   performance. The equation-pipeline v4 changes (selection criterion, in-run
   correction, calibrated residual scan) are NOT exercised by this eval set, which
   contains no equation-discovery units; v4 needs either a new sealed eval pack
   with planted-equation units or its own synthetic calibration battery
   (`results/v4_smoke.json` covers the components, not the assembled pipeline).
2. The corrected presence-MC and graphon-attribution instruments are likewise not
   in this battery (their calibration evidence lives in
   `results/corrected_reruns_2026-07-02.json` and `readmission_v2.json`).
3. Multiplicity: 0 new real-data tests (synthetic eval data); run-ledger row
   `blind_eval_r2` records the execution.
