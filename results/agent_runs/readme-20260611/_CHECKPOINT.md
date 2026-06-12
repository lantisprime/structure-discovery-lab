# README rewrite checkpoint — 2026-06-11

Agent: docs-web-editor (sonnet)
Task: rewrite README.md to cover all 13 required sections including relational face,
remediation program, agent roster, ledgers, blind evals, and domain-neutral refactor.

## Step plan

1. Read agent charter (agents/docs-web-editor.md) [done above]
2. Read existing README.md [done above]
3. Read all required source files:
   - docs/CROSS_DATASET_FRAMEWORK.md §0 (five faces)
   - docs/THEOREM_GOVERNANCE.md (A1–A7, C1–C10)
   - docs/REMEDIATION_LOG.md (protocol change, M1–M7)
   - docs/kb/INDEX.md (26 KB cards, R1–R7)
   - docs/THEOREM_SYNTHESIS.md §5 (40-row ledger)
   - src/verify_relational_docs.py, src/design_verifier.py, src/lint_domain_neutrality.py
   - docs/AGENT_WORKFLOW.md (7-agent roster)
   - agents/evals/EVAL_SET.md (12/12 PASS)
   - results/independent_verification.json (9/9 blind concordance)
   - results/blind_eval_score.md (68-unit benchmark)
   - results/run_ledger.jsonl (10 runs)
   - results/multiplicity_ledger.jsonl (173 tests)
   - results/meta_uniformity.json (KS p=0.385)
   - results/commitment_ledger.txt (baseline e1bc32b)
   - docs/RESPONSE_EXTERNAL_REVIEW.md (G0–G6 ladder)
   - docs/SANITIZATION.md (domain-neutral refactor)
   - docs/RESULTS_RELATIONAL_FIRSTRUN.md (recovery curves)
   [done above]
4. Create checkpoint (this file) [done]
5. Write new README.md [in progress]
6. Self-check: grep numbers against source files

## Progress

[done] Steps 1-4: all source files read, checkpoint created
[done] Step 5: README.md written (13 required sections)
[done] Step 6: self-check complete — all 26 numeric spot-checks passed against source files

