# LAB-RSI-R3 Gate and Merge Implementation Plan

## §1 Status

Current stage: **IN PROGRESS (2026-09-07)** -- autonomous session under
constitution article A0 (lab owner: "go r3, be autonomous"). Pulled ahead of
R2 (plan v1.4 change set 7 before 6) because the minimal R4 healer already
produces `heal/…` pull requests that wait for a human, which constraint 6
counts as a loop defect.

| Field | Value |
|---|---|
| Parent requirements | `LAB-RELIABILITY-2026Q3` v1.4 Milestone R stage R3; controls `C7`, `C8`, `C11`; constraints 6--7; change set 7 |
| Predecessor | R1 + minimal R4/R5 (`docs/plans/LAB_RSI_R1_IMPLEMENTATION_PLAN.md`, PR #28) |
| Target branch | `feature/rsi-r3-gate` |
| Pull request | filled at closeout |
| Executor altitude | `low` -- every MUST has a falsifiable test |

## §2 Freshness checks

`src/lab_heal.py` (PR #28) commits a repair on a `heal/…` branch and, with
`--push`, opens a PR whose body says "Merging is R3 (not automated yet)". The
ledger has schema v1 sources `heal` (signals `PROPOSED` / `REJECTED`) and
`attribution`; `lab_heal.run()` skips any occurrence with a `PROPOSED` row, so
a rejected proposal can never be retried today. CI (`.github/workflows/ci.yml`)
has three required-quality jobs (`install + verify (ubuntu-latest)`,
`install + verify (macos-latest)`, `browser e2e (ubuntu)`) and one
informational Windows job; `master` has no branch protection and the repo
allows merge commits (PRs #20--#28 were merged as `Merge PR #n: <title>`).
`gh` is authenticated. Different-model-family executors on this machine:
`codex` (OpenAI gpt-6-astra; its review channel is blocked in Claude sessions
by the repo's `codex-review-handoff` preflight gate, kernel K-10 -- not
bypassed) and `pi` against the homelab LiteLLM gateway (GLM, Kimi, MiniMax,
DeepSeek: open-weights families, not gated). No sealed holdout path exists
yet (M4, last tier).

## §3 Objective

A heal proposal is merged, rejected, or routed to the owner with **no human
in the loop**, by mechanical checks plus an independent verifier of a
different model family, and every decision is a ledger row. After R3 the
whole chain observe → attribute → heal → gate → merge → learn runs from one
scheduled command.

## §4 Requirements (Ground Truth)

| ID | Requirement (concrete, testable) | Test(s) | Priority |
|---|---|---|---|
| REQ-1 | `src/lab_gate.py --new` evaluates every `PROPOSED` heal row that has a PR and no later `gate` row for the same `(defect_key, defect_commit, branch)`; `--pr N` evaluates one. Each evaluation appends exactly one `gate` row: `MERGED`, `REJECTED`, or `ROUTED` (all info). Schema v1 gains source `gate` and signals `MERGED`, `ROUTED`. | `test_gate_evaluates_pending_proposals_once`, `test_schema_accepts_gate_rows` | MUST |
| REQ-2 | Merge condition, all mechanical and each recorded in `detail.checks`: (a) every required CI check on the PR head is `SUCCESS` (informational Windows job ignored); (b) the defect's own check passes in a fresh worktree at the PR head; (c) the diff touches no gate-machinery path (`tools/check.sh`, `.github/workflows/`, `src/outcome_*.py`, `src/artifact_registry.py`, `src/lab_*.py`, `src/lint_*.py`, `src/verify_*.py`, `src/design_verifier.py`) and does not delete a test file; (d) ledger files (`results/*.jsonl`) change by appended lines only; (e) `docs/THEOREM_GOVERNANCE.md` is byte-identical (A0 and A1--A8 text preserved). Any failure of (a)--(e) → `REJECTED`, PR closed with the reasons as a comment. | `test_gate_merges_when_all_green`, `test_gate_rejects_red_ci`, `test_gate_rejects_gate_machinery_edits_and_ledger_rewrites`, `test_gate_rejects_failed_defect_check` | MUST |
| REQ-3 | Independent verifier: a read-only agent of a **different model family** than the healer's (C7) reads the brief, notes, diff and mechanical results and returns `{"verdict": "AGREE"\|"DISAGREE", "reasons": [...]}`; the gate parses the last JSON object in its output. Presets: `codex` (OpenAI) and `pi` (open-weights via LiteLLM); `LAB_VERIFY_CMD` overrides the command and `LAB_VERIFY_FAMILY` its family. Same family as the healer, unparseable output, timeout, or `DISAGREE` → `REJECTED` (reason `verifier`). | `test_verifier_verdict_parsing`, `test_gate_rejects_same_family_verifier`, `test_gate_rejects_when_verifier_disagrees`, `test_verifier_presets_are_read_only_and_not_anthropic` | MUST |
| REQ-4 | Owner-reserved routing (constraint 6): a diff touching `docs/THEOREM_GOVERNANCE.md` with A0 text, `docs/REGISTRATION_*.md`, or adding a `G3+` grade line under `docs/kb/`, or notes containing `OWNER-RESERVED`, or an occurrence at the heal attempt cap (3 `heal` rows) → `ROUTED`: one GitHub issue per occurrence (label `owner-decision`, evidence attached: defect row, attribution, PR, verifier verdict), PR left open, no merge. Idempotent: a second run reuses the issue. | `test_gate_routes_owner_reserved_paths`, `test_gate_routes_at_attempt_cap` | MUST |
| REQ-5 | On `MERGED` the PR is merged with a merge commit titled `Merge PR #N: <title>`, the branch deleted, and `detail.merge_commit` recorded. The defect row itself closes only when the collector observes PASS (R0 semantics unchanged). | `test_gate_merges_when_all_green` | MUST |
| REQ-6 | `lab_heal.run()` retries an occurrence whose latest proposal was `REJECTED` by the gate (a `PROPOSED` row is pending only until a `gate` row for the same branch exists) and never beyond the attempt cap. `--base` selects the PR base branch (default `master`). | `test_heal_retries_after_gate_rejection_until_cap` | MUST |
| REQ-7 | `tools/lab_loop.sh` runs collect → attribute → heal `--push` → gate → learn under a lock, commits appended ledger/lessons rows (append-only verified against `origin/master` before push), logs outside the repo, and `--install-launchd` / `--uninstall-launchd` schedule it on the lab machine (macOS); `--print-cron` gives the equivalent crontab line. | `test_loop_script_steps_and_lock` (dry run) | MUST |
| REQ-8 | No instrument, verifier, result, or ledger row is edited; rows are appended only. `./tools/check.sh` passes before and after. | §15 | MUST |
| REQ-9 | Live proof on the real repository: a planted defect on the feature branch is observed, attributed, healed (real headless agent, PR against the feature branch), gated (real CI + real different-family verifier) and merged with zero human actions. | §15 | MUST |

## §5 Non-Goals

- R2 proposer generalization and its evals (change set 6).
- Re-graded eval set and calibration fixtures in the gate (needs M3; the
  R0 collector's `STALE_EVAL` gate already covers definition changes).
- A semantic A1--A8 checker (M5); R3 checks the constitution text is
  untouched and relies on CI's design verifier and ledger integrity.
- Holdout unseal routing (no sealed holdout exists; M4).
- A CI-hosted scheduler (needs a provider key in CI; the lab machine runs
  the loop).

## §8 Design

`gate` row (schema v1, additive):

```json
{"source": "gate", "signal": "MERGED | REJECTED | ROUTED", "severity": "info",
 "artifact": "<same as the defect>", "artifact_class": "<same>",
 "evidence": "MERGED PR #31 -> a1b2c3d; ci ok, check ok, scope ok, verifier AGREE (pi/minimax)",
 "detail": {"subject": "<slot subject>", "defect_key": "…", "defect_commit": "…", "branch": "heal/…",
            "pr": "<url>", "pr_number": 31, "head": "<sha>", "base": "master",
            "checks": {"ci": {...}, "defect_check": {...}, "scope": {...}, "ledger_append_only": {...},
                       "constitution": {...}, "verifier": {"family": "openweights", "model": "minimax",
                       "verdict": "AGREE", "reasons": [...]}},
            "reasons": ["…"], "merge_commit": "<sha>|null", "issue": "<url>|null"}}
```

Decision order: reserved → `ROUTED`; else any mechanical failure → `REJECTED`
(the verifier is not called when a mechanical check already failed; its cost
is spent only on candidates); else verifier → `MERGED` / `REJECTED`.

Verifier families: healer = `anthropic` (claude); `codex` preset = `openai`;
`pi` preset = `openweights` (LiteLLM model id recorded). The family inequality
is enforced in code, not prose (C7).

Scheduler: `tools/lab_loop.sh` is the single entry point; launchd runs it
every 6 h with the user's login environment (gh and provider auth), a
`mkdir` lock prevents overlap, and each run's log goes to
`~/Library/Logs/lab-loop/`.

## §10 Slice Ladder

| Slice | Objective | Files |
|---|---|---|
| `R3-S1` | Schema + gate core (checks, verifier, routing, merge) with a fake GitHub adapter | `src/outcome_ledger.py`, `src/lab_gate.py`, `tests/test_lab_gate.py` |
| `R3-S2` | Healer retry semantics, `--base`, PR body; loop script + launchd | `src/lab_heal.py`, `tests/test_lab_heal_learn.py`, `tools/lab_loop.sh` |
| `R3-S3` | Live proof on the feature branch, docs, closeout | ledger rows, this plan §15, `docs/LAB_IMPROVEMENT_PLAN.md`, `docs/AGENT_WORKFLOW.md` |

## §15 Verification Ledger (filled at closeout)

| Check | Command | Result |
|---|---|---|

## §18 Done Criteria

- [ ] Every MUST in §4 has its mapped test passing.
- [ ] Live proof (REQ-9) recorded in §15 with PR, CI run, verifier identity and merge commit.
- [ ] `check.sh` green; CI green on the PR.
- [ ] §15 filled; §19 review disposition recorded.

## §19 Review Consensus

(filled at closeout)
