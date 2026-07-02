# Registration template — eq_eval_set_v1 blind run

Fill, hash, git-commit BEFORE executing. No outcome expectations for any
discovery test (expectation-free protocol). Registration-commit timestamp
must precede the first results artifact.

## Header
- run_id: eq_eval_v1_run<N>
- date / executor id (must be answer-key-clean, see SEAL_NOTICE):
- seed (fresh; never 20260702 or 20260611):
- registration_sha (of this file at commit):

## Per-unit claim table (one row per unit you gate IN)

| unit | detection-gate result | family menu (declared) | frequency bounds | B per generator | m charged |
|---|---|---|---|---|---|
| unit_01 | | harmonic{1,2 freq} × K∈{1,2} + trend | [4 d, 200 d] | ≥ b_required(α_c) | |

## Fixed by contract (do not edit)
- Selection: pure held-out validation NLL, train-σ² (`select_family`);
  optional 1-SE rule must be declared HERE, before execution.
- Nulls: permutation, AR(p)-matched, phase surrogate; binding p = max;
  null equations scored on their OWN test splits.
- Correction: convention v1 — Šidák(.05, cumulative m of family
  eq.eval-set-v1) applied in-run by `adjudicate()`.
- Residual scan: `residual_scan_mc`, empty whitelist first; both scans
  reported for any attributed line.
- CI: `profile_ci_omega` (F-form). Era checks: half-split refit; any
  segment-dependent verdict reported with era language.
- Both outcome branches per unit: DETECT -> verdict ladder Q-8;
  NULL -> refusal recorded, 0 m.

## Approval
- approved_by_human: (name, date) — required before execution.
