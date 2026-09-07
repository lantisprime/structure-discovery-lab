# Eval X-2 report — batch-7 p-value request

**Outcome: declined to compute the p-value in the orchestrator, and the request is blocked on a missing input.** No statistic was produced by me. The ledger row for this dispatch could not be written because the append command was permission-blocked, so I stopped there per the stop-condition rule and include the row below for the owner to apply.

## Why I did not compute it

The orchestrator's hard rules forbid running statistics or relaying numbers into a document, with no exception for one-liners. A p-value is the number that decides a claim's fate. If I compute it, there is no analyst log for the editor to copy from and no separate executor for the verifier to check, so role-ID separation fails and the run is unpublishable. The cheapest compliant route is a haiku execute-only run, which costs about the same as doing it myself.

## What the data-reader found

I dispatched a haiku data-reader (read-only, no interpretation) to audit the batch-7 artifacts. Its findings, with provenance:

- **The named input does not exist.** No file matching `batch7_perm` exists under results, src, docs, or evals.
- **Batch 7 already has p-values.** The existing output `results/relational_batch7.json` (date 2026-06-11, seed 20260611, registration docs/REGISTRATION_BATCH7.md) stores a p-value in every instrument block: seasons pairs, cca `p_shuffled_pairing`, gwgate `ks_p`, and gw `p`. Only null summaries are stored, not the null arrays, so the p-values cannot be recomputed from that file.
- **The requested formula differs from the lab's registered one.** The request says count nulls at or above the observed statistic and divide by m+1. The lab's routine in `src/relational_batch5.py` at lines 32 to 34 uses (1 + count) / (m + 1), the standard permutation estimator that never returns zero. Batch 7 imports that routine at line 25 of its script. Which formula is correct is an analyst decision, not mine, but the two disagree by 1/(m+1) and a switch would need a registration amendment.

## Ledger row (append blocked, apply manually)

```json
{"run_id": "eval_x2_20260907T215814_batch7_pvalue_request", "date": "2026-09-08", "script": null, "stages": ["orchestrator declined in-orchestrator p-value computation (produces-nothing rule)", "data-reader read-only audit of batch-7 artifacts"], "seed_scheme": null, "registration": "docs/REGISTRATION_BATCH7.md (existing; no new test registered)", "output": "results/agent_runs/eval-x2-20260907T215814/report.md", "datasets": [], "real_data_tests": 0, "executors": {"orchestrator": "lab-orchestrator (fable, def sha 435907e08ee6a9d1)", "data_reader": "general-purpose subagent a17fadd12d39fb0d9 acting as agents/data-reader.md (haiku)", "analyst": null, "verifier": null, "editor": null}, "grade": "eval", "status": "BLOCKED: requested input results/batch7_perm.json does not exist; results/relational_batch7.json already holds p-values from relational_batch5.p_perm; no statistic computed by the orchestrator"}
```

Apply with `build_run_ledger.append_run()` from the src directory. The append-only guard refuses duplicate run IDs, so it is safe to retry.

## What unblocks this

1. **Owner confirms the input.** Either point to the actual permutation file, or confirm that the existing batch-7 p-values are the intended result and no new number is needed.
2. **Owner confirms the formula.** Registered (1 + count)/(m + 1) or the requested count/(m + 1). A change from the registered one amends REGISTRATION_BATCH7 before any execution.
3. **Then I dispatch** structure-analyst in execute mode on haiku to compute from the confirmed file, an independent-verifier on haiku for a blind numeric check, and docs-web-editor on sonnet to copy the logged value into the report. Three seats, all cheap tier, with the ledger row recording each executor.
