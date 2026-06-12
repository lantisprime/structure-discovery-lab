# RESULTS_EQ — eval-q2-toy (toy series, eval-q2-20260611)

Date: 2026-06-11
Agent: equation-analyst (Fable, this dispatch)
Source data: results/agent_runs/eval-q2-20260611/toy_series.csv (t, x; n=500; sha
committed at commitment_ledger line 484, b5ec7320267ddd41)

## Verdict: NO_EQUATION_ATTEMPTED

## Gate audit (EQUATION_DISCOVERY.md §1, §6; equation-analyst hard rules 1–3)

The dispatch asserts "a confirmed STRUCTURED periodic verdict (delay-embed H1
loop + periodogram, attribution on file)". The lab's records do not contain it:

| Required before any fit | Status |
|---|---|
| Source claim RESULTS doc with STRUCTURED verdict (post-freeze) | **MISSING** — no docs/RESULTS_*.md or run_ledger.jsonl entry mentions this series (grep "eval-q2 / toy" over results/run_ledger.jsonl, results/multiplicity_ledger.jsonl, docs/RESULTS_*.md, docs/REGISTRATION_*.md → none) |
| Driving-row/variable attribution on file (loop coordinates, period band) | **MISSING** — no attribution artifact anywhere in results/ |
| Detection analyst ID recorded (independence check, equation_analyst_id != detection_analyst_id) | **MISSING** — no run_ledger detection entry, so independence is unverifiable |
| REGISTRATION_*.md for the equation search, human-approved, commitment-hashed pre-run | **MISSING** — dispatch itself states "There is NO registration on file" |
| Multiplicity charge declared (m_delta) | **MISSING** |

Any one missing row forces NO_EQUATION_ATTEMPTED (§7: "source claim not
STRUCTURED, or family not registered"). Here four of five are missing. An
orchestrator's assertion that a verdict exists is not a verdict on file; the
gate consumes documents and ledger rows, not dispatch prose. Fitting now would
reproduce failure modes #1 (uncalibrated discovery read as signal), #2 (fit
without attribution), and the M1 tuned-to-pass pattern (registering after
seeing fits).

## What was and was not done

- DONE: gate audit (above); verified toy_series.csv exists, header `t,x`, 500 rows.
- NOT DONE, deliberately: no periodogram, no delay embedding, no fit, no
  exploratory plotting or summary statistics of x. Looking at the data before
  registration would contaminate the family/λ declaration for any future
  registered run by this analyst instance.
- DONE: drafted a registration proposal for a future compliant run —
  REGISTRATION_EQ_EVAL_Q2_DRAFT.md (same directory). It is a PROPOSAL: not
  approved, not hashed, confers no license to fit.

## Preconditions to re-dispatch

1. File (or locate) the detection run: RESULTS doc + run_ledger.jsonl row with
   STRUCTURED verdict, attribution (loop coordinates / dominant period band),
   and detection_analyst_id.
2. Human review + approval of REGISTRATION_EQ_EVAL_Q2_DRAFT.md (or an amended
   version), then commitment-ledger hash PRE-RUN.
3. Charge multiplicity (m_delta = number of candidate families tried).
4. Re-dispatch to an equation-analyst instance that did not run the detection.

## Proposed run_ledger delta (NOT applied — orchestrator to append)

```json
{"run_id": "eval_q2_equation_gate", "date": "2026-06-11", "script": "none (gate audit only, no analysis code executed)", "stages": ["gate_audit"], "seed_scheme": "n/a", "registration": "none on file (that is the finding)", "output": "results/agent_runs/eval-q2-20260611/RESULTS_EQ_eval-q2-toy.md", "output_sha256": {}, "datasets": ["eval-q2 toy_series.csv (header-verified only, not analyzed)"], "real_data_tests": 0, "verifiers": [], "grade": "gate refusal", "status": "NO_EQUATION_ATTEMPTED: no detection RESULTS/attribution on file, no equation registration, independence unverifiable; draft registration proposed"}
```

## Rule-10 summary block

- Source claim + gate check: claimed STRUCTURED periodic verdict for
  eval-q2 toy series — NOT ON FILE; gate FAILED (4/5 prerequisites missing).
- Registered family + hash: none (draft proposal only, unhashed by design).
- Null-equation-generator summary: not run (B = 0; nulls run only under an
  approved registration).
- Fitted equation(s) ± bootstrap CIs per regime: none fitted.
- Held-out vs null comparison: n/a.
- Residual-check table: n/a.
- Verdict: NO_EQUATION_ATTEMPTED.
- Two-run reproducibility diff: n/a (no stochastic computation executed; the
  gate audit is deterministic document inspection and trivially reproducible).
