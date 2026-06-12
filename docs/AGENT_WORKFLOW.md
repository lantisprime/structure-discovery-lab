# Agent Workflow — model-routed execution of the lab protocol

Added: 2026-06-11. Updated 2026-06-11: Phase 5 — Equation Discovery inserted
(docs/EQUATION_DISCOVERY.md); Decide renumbered to Phase 6. Maps the RUNBOOK's
seven phases (0–6) onto specialized agents with
explicit model assignments and fallback chains, so any executor (Claude model, other
LLM, or human) knows its role, its boundaries, and who verifies it.

## Why model routing

The lab already requires two independent executors producing byte-identical numbers
(deterministic reproducibility, README). Routing different phases to different models
makes executor independence structural instead of aspirational: the model that wrote
an analysis is never the model that verifies or publishes it.

## The agent roster (expanded 2026-06-11 after review finding C2: the original
## three-agent design was bypassed in practice by a single generalist session —
## the roster below makes the separation structural, with an orchestrator that
## coordinates but produces nothing)

Definitions: `agents/*.md` (copy into `.claude/agents/` to activate as Claude Code
subagents: `cp agents/*.md .claude/agents/`).

| Agent | Role | Phases | Primary model (token economy) | Escalation chain |
|---|---|---|---|---|
| `lab-orchestrator` | **manages experiments**: routes phases, enforces gates + role-ID separation, maintains the run ledger; produces nothing itself | all (coordination only) | **Fable** — routing/gate errors are the expensive ones; footprint kept small (reads ledgers, not datasets) | fable → opus; never below |
| `research-scout` | **researches**: literature, canonical references, dataset sources, prior art — sourced briefs with provenance | 0 (sourcing) | **Sonnet** — search + synthesis | sonnet → opus (contested literature) |
| `data-reader` | **reads files**: extraction, row audits, schema checks, result-JSON lookups; read-only, no interpretation | 0–6 (support) | **Haiku** — most token spend is reading; it belongs at the cheapest tier | haiku → sonnet (ambiguous formats) |
| `theorem-dataset-onboarder` | cards theorems + onboards datasets (gate-checked, clerical) | 0–1 | **Haiku** | haiku → sonnet (gate failure) → opus → any LLM via wizard + human diff |
| `structure-analyst` | **analyzes**: null design, instrument implementation, real-data runs, attribution, multiplicity | 2–4 | **Fable** (design/interpretation); **Haiku** (execute-only re-runs) | design: fable → opus → sonnet; execution: haiku → any LLM execute-only |
| `equation-analyst` | **derives equations**: candidate-family registration, null-equation generator, constrained fits, MDL selection, residual checks, equation verdicts (docs/EQUATION_DISCOVERY.md §6 contract); never detects, never decides | 5 | **Fable** (design/interpretation); **Haiku** (execute-only registered fits) | design: fable → opus → sonnet; execution: haiku → any LLM execute-only |
| `docs-web-editor` | **generates files**: RESULTS docs, figures-from-JSON, ledger sync, web pages — numbers copy-only | 6 | **Sonnet** | sonnet → opus (narrative restructuring) → human diff review |
| `independent-verifier` | **checks**: numeric + design verification, reproduction diffs, blind replication, ledger reconciliation; never verifies own authorship | all (after each) | **Haiku** (numeric/reproduction) / **Sonnet** (design interpretation) | identity rule has no fallback: a different instance than the author, always |

**Role-ID separation (mechanical, recorded per run in `results/run_ledger.jsonl`):**

```text
onboarder_id != analyst_id
analyst_id   != verifier_id
editor_id    != analyst_id
equation_analyst_id != detection_analyst_id   (per claim: the detector never
                                               fits its own equations)
equation_analyst_id != verifier_id
verification_executor != script_author
registration_approved_by_human = true   (for confirmation-family and
                                         equation-family runs)
```

A run missing these fields, or violating them, is unpublishable. The
orchestrator fills them at dispatch time; the verifier refuses self-verification
even if asked.

**Token-economy rule:** every task routes to the *cheapest* model whose gates it can
pass; escalation happens on gate failure or on explicit task class (design,
interpretation, narrative restructuring), never by default. The two-run/cross-model
verification makes cheap execution safe: a weak executor cannot corrupt a
deterministic pipeline without the diff catching it.

## Handoff contract (who may touch what)

- Onboarder writes: `docs/kb/*`, `docs/kb/INDEX.md`, `datasets/*`. Never: `src/`
  statistics, `RESULTS_*`, web pages.
- Analyst writes: `src/*`, `docs/RESULTS_*.md`, proposes `REGISTRATION_*.md` and
  ledger deltas. Never: kb cards, README, web pages.
- Equation-analyst writes: `src/eq_*`, `docs/RESULTS_EQ_*.md`, proposes
  equation `REGISTRATION_*.md` and ledger deltas. Never: detection
  `RESULTS_*.md`, kb cards, README, web pages; never EV/action computations
  (Phase 6 belongs to the decision layer).
- Editor writes: `README.md`, `docs/RUNBOOK.md`, `docs/THEOREM_SYNTHESIS.md` prose,
  `docs/RESEARCH_NOTES.md`, `*.html`. Never: a number that isn't traceable to a
  script output or RESULTS table; never pick logic.
- Human approves: every `REGISTRATION_*.md` (pre-registration is a human commitment),
  every confirmation run trigger, every fallback past the Claude chain.

## Cross-executor verification (hardens the existing rule)

1. **Two-run rule (unchanged):** every analysis script runs twice; outputs must be
   byte-identical (fixed seeds).
2. **Cross-model rule (new):** the second run is executed by a *different* model
   than the one that wrote the script — per the token-economy rule, the cheapest
   one (e.g., Fable writes, Haiku re-runs). Since
   outputs are deterministic, any diff indicates an environment or contract
   violation, not opinion.
3. **Cross-role review:** the editor may not publish a number the analyst didn't
   log; the analyst may not run an instrument the onboarder didn't card; the
   onboarder may not card a theorem without a registered MC-derivable null.

## Replay & audit (added 2026-06-11, lab-owner directive)

Every agent dispatch must be **replayable**: an auditor reconstructs what an
agent was asked, what it did, and what it produced — and can re-execute it.

**Dispatch record** — for every dispatch, the orchestrator creates
`results/agent_runs/<run_id>/` containing:

```text
prompt.md        exact dispatch prompt, saved BEFORE dispatch (commitment)
agent.txt        agent name, model tier, agent-instance id, date
report.md        the agent's final report, verbatim, saved on return
files.txt        files the agent created/modified (from its report + diff
                 against the commitment ledger)
grade.json       eval grade when the dispatch is an eval (grade_agent_eval.py)
```

**Replay mechanics** (why re-execution reproduces the run):
1. All analysis is in deterministic seeded scripts — replaying an analyst or
   verifier run = re-running the script named in `report.md`; byte-identical
   output is the pass condition.
2. `_CHECKPOINT.md` files are append-only action logs (`[done] step -> files`)
   — the step-by-step trace for troubleshooting partial runs.
3. The commitment ledger snapshots file hashes; diffing snapshots brackets
   exactly what changed during a dispatch window.
4. The run ledger row links registration → script → output SHA → verifier
   identity, closing the audit chain.

**Eval gate**: agents are re-evaled (agents/evals/EVAL_SET.md) after any
change to their definition file; eval grades live in the dispatch record and
the EVAL_SET log. No eval pass, no dispatch.

## Checkpoint rule (added 2026-06-11 after a dropped onboarder run)

Motivating incident: an onboarder agent ran 141 tool calls (~112 min) re-sourcing the
covariate datasets, lost its connection, and left only empty folders — all work lost
because nothing was persisted until the end.

Rules, mandatory for every agent run expected to exceed ~10 tool calls:

1. **Checkpoint file first.** Before substantive work, create `_CHECKPOINT.md` in the
   primary target folder with the step plan. After EACH completed step, append one
   line: `[done] <step> -> <files written>`. The orchestrator (or a restarted agent)
   resumes from the last `[done]` line instead of starting over.
2. **Persist raw before parsing.** Fetched data (API responses, raw blocks) is written
   to disk immediately upon receipt — never held only in context while further fetches
   or parsing continue. A dropped connection then costs at most one fetch.
3. **Small irreversible steps early.** Order work so cheap, durable artifacts (raw
   files, provenance notes) land before expensive derived ones (parsed CSVs, docs).
4. **Budget declaration.** Agent prompts state an expected tool-call budget; an agent
   exceeding ~3× its budget should checkpoint and return a partial report rather than
   press on (a partial report + checkpoint is recoverable; a timeout is not).
5. **Orchestrator duty.** After any failed/disconnected agent run, the orchestrator's
   FIRST action is to inspect the target folders and `_CHECKPOINT.md` for partial
   state before re-dispatching or redoing work. Delete `_CHECKPOINT.md` only after
   the run's deliverables are validated.

## Fallback protocol for non-Claude LLMs

The lab's docs are written to be executor-agnostic (EVALUATION_PROTOCOL is a
formula-level spec; admin_onboarding.html is a gate-checked wizard; scripts are
deterministic with fixed seeds). A non-Claude LLM slots in as follows:

- **Onboarding:** follow admin_onboarding.html; output must pass the same gates;
  human reviews the diff before merge.
- **Analysis:** execute-only. Run the existing scripts, report stdout verbatim,
  diff against the stored outputs. No statistic design, no fire interpretation,
  no threshold decisions. (Rationale: the protocol's safety lives in its
  pre-registration and calibration discipline, which an unfamiliar executor is
  most likely to shortcut — see the failure-mode gallery.)
- **Editing:** allowed with mandatory human diff review; the caveat-preservation
  rule (AGENTS: docs-web-editor rule 2) is checked line-by-line.
- **Degraded mode (no LLM available):** the RUNBOOK + EVALUATION_PROTOCOL are
  sufficient for a human executor; that was the design requirement from the start.

## Worked example (this is how batch 4 would route)

1. Onboarder (Haiku; escalate Sonnet on gate failure): cards 17–19, INDEX rows, dataset untouched (already onboarded).
2. Analyst (Fable): REGISTRATION_BATCH4 proposal → human approves → admission
   trials → real runs → attribution of the 6/55 fire → RESULTS_BATCH4.md.
3. Cross-model rule: Haiku re-runs all three scripts, diffs outputs (must be
   byte-identical).
4. Editor (Sonnet): RESEARCH_NOTES §9, ledger rows 26–28, lotto_picker.html update
   + render smoke test, caveats carried ("vacuous at feasible n", "era-bounded,
   zero forward value").
5. Human: approved the registration (step 2) and reviews the editor's diff.

## Invocation

From Claude Code / Cowork with the agent files installed:

- "Use the theorem-dataset-onboarder to card the Stein–Chen Poisson approximation."
- "Use the structure-analyst to run the batch-4 confirmation when the held-out set
  reaches 150 draws."
- "Use the docs-web-editor to sync THEOREM_SYNTHESIS prose with RESULTS_BATCH4."

Each agent's definition file pins its model; the orchestrating session enforces the
handoff contract and runs the cross-model verification step.
