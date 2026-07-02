# ADDENDUM — Equation-Program Re-adjudication under the Verdict-Time Correction

**STATUS: RATIFIED by the lab owner (Cha), 2026-07-02.** The corrected
statuses below are now the lab's standing verdicts, superseding the frozen
labels per docs/SUPERSEDED_LABELS.md. The ratified correction convention —
**Šidák at base α=0.05 over the cumulative charged family m at verdict
time** — is the standing versioned rule (convention v1) for accumulating
claim families; PLAYBOOK_THEOREM_HARMONIZATION.md H-4 carries the
reconciliation note. The §2b basis-sensitivity grid remains published so the
convention-dependence of v2-B stays visible.

| Ratification | Decision | Signed | Date |
|---|---|---|---|
| Correction convention (Šidák .05, cumulative m) | ☑ RATIFIED | Cha (lab owner) | 2026-07-02 |
| v1-B → AT_FLOOR_RESOLUTION_LIMITED | ☑ RATIFIED | Cha (lab owner) | 2026-07-02 |
| v2-B → FAIL_corrected (basis-dependent, see §2b) | ☑ RATIFIED | Cha (lab owner) | 2026-07-02 |
| confirm1 → UNCONFIRMED | ☑ RATIFIED | Cha (lab owner) | 2026-07-02 |
| v3 36.34d anomaly → instrument artifact pending re-test | ☑ RATIFIED | Cha (lab owner) | 2026-07-02 |

Ratification received via Cowork session, 2026-07-02 ("yes i ratify
RESULTS_EQ_READJUDICATION"); recorded by the session agent.

2026-07-02 · machine artifact: `results/eq_readjudication_2026-07-02.json`
(`src/eq_verdict_correction.py` — pure arithmetic on frozen outputs, no refits)
Source findings: AUDIT_CORRECTNESS_2026-07-02.md E-1, E-2, E-3.
This addendum does not edit any frozen registration/results doc; it states the
corrected status of their claims. It supersedes the *verdict labels* (not the
numbers) of RESULTS_EQ_TIDAL.md, RESULTS_EQ_TIDAL_V2.md,
RESULTS_EQ_MOONDIST_CONFIRM1.md wherever they conflict.

## 1. What was applied

Every eq registration deferred multiplicity to "the orchestrator … at verdict
time"; no artifact ever executed that step (audit E-2). It is now executed:
Šidák at base α=0.05 over the family's cumulative charged m at each run's
verdict time (ledger charges: v1 +5 → m=5; v2 +3 → m=8; v3 +1 → m=9;
confirm1 +1 → m=10), plus the relational program's floor rule
(1/(B+1) ≤ α_corrected/2).

## 2. Corrected claim statuses

| Claim | binding p | m at verdict | α corrected | raw verdict | **corrected status** |
|---|---|---|---|---|---|
| v1 claim A (tidal phase) | 0.2090 | 5 | 0.0102 | FAIL | FAIL (unchanged) |
| v1 claim B (moon dist) | 0.004975 | 5 | 0.0102 | pass 0.01 | **AT_FLOOR_RESOLUTION_LIMITED** — p equals the B=200 floor exactly; rerun at B≥399 required before this pass is citable |
| v2 claim A (tidal phase) | 0.1940 | 8 | 0.00639 | FAIL | FAIL (unchanged); **design also under-resolved** (floor 0.004975 > α/2 = 0.0032; B=200 < 312 required) |
| v2 claim B (moon dist) | 0.00995 | 8 | 0.00639 | pass 0.01 | **FAIL_corrected** — does not survive the family correction it deferred; design also under-resolved at m=8 (B=200 < 312 required) |

### 2b. Basis sensitivity (adversarial review B-2 — the convention was discretionary)

The registrations deferred the correction without fixing its convention.
Verdicts under every defensible reading (full grid in the JSON):

| Basis | v1-B | v2-B |
|---|---|---|
| Šidák .05, cumulative m (PRIMARY) | pass (at floor) | FAIL |
| Šidák .05, final m=10 | pass (by 0.00014) | FAIL |
| Bonferroni .05, cumulative | pass | FAIL |
| Bonferroni on declared α=.01 | **FAIL** | FAIL |
| Per-run within m (ledger rows) | pass (at floor) | **pass** |
| Playbook H-4 (families engaged = 1) | pass | **pass** |

v2-B is therefore **basis-dependent**: FAIL under family-cumulative readings,
pass under per-run readings. Note the primary basis is *more lenient* than
the declared raw α for v1 (Šidák(.05, m=5) = 0.0102 > 0.01) — the chosen
convention is neither the harshest nor the most lenient available. The
playbook H-4 text ("m = families engaged in a run") and this addendum's
cumulative-family practice currently conflict; the ratified convention must
reconcile them and becomes the standing versioned rule. Regardless of basis,
v1-B remains at-floor (B=200 resolution-censored) and confirm1's downgrade is
overdetermined by E-3 (no baselines) and same-source data alone.

## 3. Consequence for confirm1

`RESULTS_EQ_MOONDIST_CONFIRM1.md`'s MECHANISM_SUPPORTED rested on
(a) v2 claim B's raw pass — now FAIL_corrected;
(b) no registered skill baselines (audit E-3): a textbook a-priori sinusoid
    was never scored against the frozen equation;
(c) fresh rows from the same DE441 integrator (the registration itself
    concedes non-independence).

**Corrected status: UNCONFIRMED.** The gates it did pass (C1/C2 RMSE bounds,
freeze verification) remain valid as recorded; they were necessary, not
sufficient. Per `src/eq_selection_v4.py::confirmation_label`, same-source
data can never yield more than MECHANISM_CONSISTENT even after a valid pass.

## 4. E-1: selection-criterion re-check (from stored family_records)

Corrected criterion = pure held-out validation NLL (no complexity penalty
stacked on held-out loss; the frozen J's "BIC-rate" λ was derived for train
likelihoods and double-charges complexity).

| Claim | frozen-J winner | pure-val-NLL winner | agree? |
|---|---|---|---|
| v2 claim A | A2 (2 freq) | A2 (−3.148 vs A5 −2.979) | yes — but by 0.17 NLL, within noise, while A5 had the best TEST NLL (61.26 vs 67.10) |
| v2 claim B | B1 | B1 (13.535 vs 13.858) | yes — robust to criterion |

Consequence: v2 "learning #1" (capacity refuted as the binding constraint)
is **downgraded from finding to open question** — under the corrected
criterion the 2- vs 3-frequency decision is within selection noise, and the
frozen J made 3-frequency families structurally unable to win. v4 must
re-run selection with `select_family()` and a pre-registered tie-break
before any capacity statement is repeated.

## 5. What v4 must do differently (all implemented in src/eq_selection_v4.py)

1. Selection: `select_family` (pure held-out NLL, train-σ², optional
   registered 1-SE rule). Rename the metric (it was never a held-out
   log-likelihood).
2. Null budget: `b_required(corrected_alpha(0.05, m))` — at the family's
   current m=10 that is B≥390 (use 399) per generator, not 200.
3. Correction applied in-run by `adjudicate()`; no deferral language
   permitted in v4 registration.
4. Residual anomalies: `residual_scan_mc` (pre-whiten declared whitelist,
   single AR-surrogate max-ordinate test). The v3 "36.34 d discovery-grade
   anomaly" is **downgraded to instrument artifact pending this re-test**
   (audit E-6: iterative Fisher-g deletion has the wrong conditional null and
   assumes white ordinates).
5. Frequency uncertainty: `profile_ci_omega` replaces the residual
   bootstrap as primary CI (audit E-4); bootstrap allowed only behind a
   whiteness gate.
6. Confirmation: ≥2 registered baselines via `beat_baselines`;
   `confirmation_label` caps same-source passes at MECHANISM_CONSISTENT.
7. Attribution bands and whitelists from a-priori tables/identifiability
   calculations only (audit E-5); the v2 evection band remains descriptive.

## 6. Multiplicity accounting for this addendum

No new real-data tests were run (arithmetic on frozen outputs): 0 m charged.
The corrected statuses are recorded in
`results/eq_readjudication_2026-07-02.json`; ledger charge rows unchanged;
the 5 eq test rows added to the multiplicity ledger (schema v2 migration)
carry the binding p's above.

Per CLAUDE.md: adopting v4 materially changes methodology — run
`agents/evals` (structure_eval_set_v1) before the first v4 publication.
