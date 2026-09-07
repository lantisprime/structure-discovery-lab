# LAB-RSI-R3 Gate and Merge Implementation Plan

## §1 Status

Current stage: **COMPLETE (2026-09-07), merged via the PR in §15** --
autonomous session under constitution article A0 (lab owner: "go r3, be
autonomous"). Pulled ahead of R2 (plan v1.4 change set 7 before 6) because
the minimal R4 healer already produced `heal/…` pull requests that wait for a
human, which constraint 6 counts as a loop defect. The live proof (§15) ran
the whole chain on the real repository with zero human actions between the
planted defect and the merge, and surfaced two healer defects on the way
(REQ-10), both fixed here.

| Field | Value |
|---|---|
| Parent requirements | `LAB-RELIABILITY-2026Q3` v1.4 Milestone R stage R3; controls `C7`, `C8`, `C11`; constraints 6--7; change set 7 |
| Predecessor | R1 + minimal R4/R5 (`docs/plans/LAB_RSI_R1_IMPLEMENTATION_PLAN.md`, PR #28) |
| Target branch | `feature/rsi-r3-gate` |
| Pull request | #30 (live-proof heal PR: #29, merged by the gate) |
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
| REQ-2 | Merge condition, all mechanical and each recorded in `detail.checks`: (a) every required CI check on the PR head is green (`install + verify` ubuntu and macos, `browser e2e`; the informational Windows job is ignored; missing or pending = not green); (b) the defect's own check passes in a fresh detached worktree at the PR head; (c) no test file is deleted; (d) ledger files (`results/*.jsonl`) change by appended lines only. Any failure of (a)--(d) → `REJECTED`, PR closed with the reasons as a comment; the verifier is not called for a proposal that already failed mechanically. A PR merged or closed by a human before the gate ran is recorded (`MERGED` "outside the gate" / `REJECTED`) so it stops being pending. *(Review fixes, §19:)* diffs are computed with `--no-renames` so a moved test or gate file meets the checks under both paths; the PR base must equal the base the heal row recorded (or `--base`); the merge pins the verified head (`--match-head-commit`); a diff longer than 60k chars and a heal row whose defect occurrence is missing from the ledger are rejected. | `test_gate_merges_when_all_green`, `test_gate_rejects_red_ci_without_calling_verifier`, `test_gate_rejects_failed_defect_check`, `test_gate_rejects_ledger_rewrites_and_deleted_tests`, `test_gate_records_human_merge_and_outside_close`, `test_gate_dry_run_touches_nothing`, `test_gate_rejects_retargeted_base_missing_defect_row_and_oversized_diff`, `test_real_git_diff_sees_renames_ledger_rewrites_and_reserved_paths` | MUST |
| REQ-3 | Independent verifier: a read-only agent of a **different model family** than the healer's (C7) reads the defect, attribution, notes, diff and mechanical results and returns `{"verdict": "AGREE"\|"DISAGREE", "reasons": [...]}`; the gate parses the last such JSON object in its output. Presets: `pi` (open-weights via the homelab LiteLLM gateway; default) and `codex` (OpenAI); `LAB_VERIFY_CMD` / `LAB_VERIFY_MODEL` override the command. The family is **derived from the verifier binary** (`claude` → anthropic, `codex` → openai, `gemini` → google, `pi` → anthropic if its provider/model names Anthropic or Claude, else openweights); `LAB_VERIFY_FAMILY` is consulted only for a binary the gate cannot classify. Same family as the healer, unknown family, unparseable output, timeout, or `DISAGREE` → `REJECTED`. | `test_verifier_verdict_parsing`, `test_run_verifier_with_fake_command`, `test_gate_rejects_same_family_verifier`, `test_gate_rejects_unknown_family_verifier`, `test_family_is_derived_from_the_verifier_binary`, `test_gate_rejects_when_verifier_disagrees_or_is_silent`, `test_verifier_presets_are_read_only_and_not_the_healer_family`, `test_verify_brief_carries_evidence_and_asks_for_json` | MUST |
| REQ-4 | Owner-reserved routing (constraint 6): a diff touching `docs/THEOREM_GOVERNANCE.md` (A0, article and conflict-registry ratification), `docs/REGISTRATION_*.md`, a gate-machinery path (`tools/check.sh`, `tools/lab_loop.sh`, `.github/workflows/`, `src/outcome_*.py`, `src/artifact_registry.py`, `src/lab_*.py`, `src/lint_*.py`, `src/verify_*.py`, `src/design_verifier.py`: the gate may not approve changes to itself), or adding a `G3+` grade line under `docs/kb/`; notes containing `OWNER-RESERVED`; or an occurrence at the heal attempt cap (3 `heal` rows) → `ROUTED`: one GitHub issue per occurrence (label `owner-decision`, evidence attached: defect row, attribution, PR, agent notes, gate checks), PR left open with a comment, no merge, verifier not called. Idempotent: a second run reuses the issue; an exhausted occurrence with no PR is routed too. | `test_gate_routes_owner_reserved_changes` (6 cases), `test_gate_reuses_existing_issue`, `test_gate_routes_at_attempt_cap` | MUST |
| REQ-5 | On `MERGED` the PR is merged with a merge commit titled `Merge PR #N: <title>`, the branch deleted, and `detail.merge_commit` recorded. The defect row itself closes only when the collector observes PASS (R0 semantics unchanged). | `test_gate_merges_when_all_green` | MUST |
| REQ-6 | `lab_heal.run()` retries an occurrence whose latest proposal was `REJECTED` by the gate (a `PROPOSED` row is pending only until a `gate` row for the same branch exists) and never beyond the attempt cap. `--base` selects the PR base branch (default `master`). | `test_heal_retries_after_gate_rejection_until_cap` | MUST |
| REQ-7 | `tools/lab_loop.sh` runs collect → attribute → heal `--push` → gate → learn under a lock, commits appended ledger/lessons rows (append-only verified against `origin/master` before push), logs outside the repo, and `--install-launchd` / `--uninstall-launchd` schedule it on the lab machine (macOS); `--print-cron` gives the equivalent crontab line. | `test_loop_script_steps_and_lock` (dry run) | MUST |
| REQ-8 | No instrument, verifier, result, or ledger row is edited; rows are appended only. `./tools/check.sh` passes before and after. | §15 | MUST |
| REQ-9 | Live proof on the real repository: a planted defect on the feature branch is observed, attributed, healed (real headless agent, PR against the feature branch), gated (real CI + real different-family verifier) and merged with zero human actions. | §15 | MUST |
| REQ-10 *(R4 fixes from the live run)* | The heal worktree links the main checkout's `.venv` (ignored by git, never committed) so the brief's check command and `./tools/check.sh` run with the lab's interpreter; an agent that exits non-zero (e.g. "Reached max turns") after changing files is still gated rather than rejected on its exit code, with `agent_exit` and a redacted `agent_tail` recorded in the row; only an unchanged tree is rejected at the agent stage. | `test_heal_links_venv_and_proceeds_when_agent_exits_nonzero_after_changing_files`, `test_heal_rejects_when_agent_changes_nothing` | MUST |

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
| `R3-S3` | Live proof on the feature branch, healer fixes it surfaced, docs, closeout | ledger rows, `src/lab_heal.py`, this plan §15, `docs/LAB_IMPROVEMENT_PLAN.md`, `docs/AGENT_WORKFLOW.md` |

## §15 Verification Ledger (filled at closeout)

| Check | Command | Result |
|---|---|---|
| Suites | `.venv/bin/python -m pytest tests/ -q` | `152 passed, 1 skipped` (R3: 27 gate tests incl. a real-git diff test and the loop-script dry run; R4: 2 new heal tests) |
| Full battery | `./tools/check.sh` | `ALL CHECKS PASSED` before the live run (147 tests), after it (148) and after the review fixes (152); collector 0 new defects, registry OK, attribute no-op, lessons 4 total |
| Verifier route | `pi -p --no-session --no-tools … --provider litellm --model minimax` | replied with a parseable `{"verdict": …}` JSON object (smoke test before the live run) |
| Live closed loop, plant | commit `dc48068` on `feature/rsi-r3-gate`: `ACTIVE_SNAPSHOT = None` in `src/pcso_weekly_update.py` `main()` (the same defect as R1's live run) | pushed; no human action after this commit until the merge below |
| Live: observe (R0) | `outcome_collect.py --sources verify_entrypoint` | `FAIL … expected 252 rows, got 380; 1 new defect` |
| Live: attribute (R1) | `outcome_attribute.py --new` | `introduced_by dc48068 (bisect, 4 steps)` |
| Live: heal attempt 1 (R4) | `lab_heal.py --new --push --base feature/rsi-r3-gate --model sonnet --max-turns 30` | `REJECTED (agent)`: the agent had made the exact fix and written its notes but exited 1 on "Reached max turns (30)" after spending turns looking for an interpreter (the worktree had no `.venv`); the healer rejected on the exit code and discarded the work. Two R4 defects → fixed (REQ-10) before attempt 2. |
| Live: heal attempt 2 (R4) | same command | `PROPOSED https://github.com/lantisprime/structure-discovery-lab/pull/29 commit 6e1ea32; gate green`: one-line revert + `HEAL_NOTES.md` with the root cause citing the attribution and the `--verify` PASS line |
| Live: CI on the heal PR | run 34071256126 | ubuntu, macOS, browser e2e green; Windows informational fail (unchanged contract) |
| Live: gate (R3) | `lab_gate.py --new --verifier pi` | `MERGED PR #29 -> 38dd427; ci ok, check ok, scope ok, verifier AGREE (openweights/minimax)`: the verifier's five reasons name the root cause, the untouched checks, the append-only ledger, the minimality and A1--A8; merge commit `Merge PR #29: heal: src/pcso_weekly_update.py FAIL (darwin)`, branch deleted |
| Live: close + learn (R0, R5) | `git pull`; `outcome_collect.py --sources verify_entrypoint`; `lab_learn.py --derive` | `PASS sha256=11c8af72…` (defect closed); `lessons: 1 new` (`introduced by dc48068; passing again at 38dd427 on darwin`) |
| Owner routing | unit tests only (`test_gate_routes_owner_reserved_changes` × 6, `_reuses_existing_issue`, `_routes_at_attempt_cap`) | not exercised live: creating a real `owner-decision` issue for a fake decision would be noise for the owner |
| CI on this PR | PR #30 checks | Run 34072343430 on `96eb20a` (after the review fixes): ubuntu, macOS and browser e2e green; Windows informational fail (heal tests, unchanged contract) |

## §18 Done Criteria

- [x] Every MUST in §4 has its mapped test passing (148 passed).
- [x] Live proof (REQ-9) recorded in §15 with PR #29, CI run 34071256126,
      verifier `openweights/minimax` via pi/LiteLLM, merge commit `38dd427`.
- [x] `check.sh` green before and after the live run.
- [x] CI green on the PR to master (run 34072343430); §19 review disposition recorded.

### Lessons (for the handoff and the lessons ledger)

- The exit code of a headless agent is not the verdict on its work: "Reached
  max turns" returns 1 after the fix was already on disk. Gate the tree, record
  the exit and the output tail, reject only an unchanged tree.
- A git worktree has none of the ignored files the checks rely on (`.venv`);
  link what the gate needs, and exclude it from the commit explicitly rather
  than trusting `.gitignore` (the test repos have none).
- The repo's `codex-review-handoff` preflight gate blocks any `codex …`
  invocation from a Claude session; the R3 verifier therefore defaults to the
  pi/LiteLLM open-weights route (a different family, not gated) and keeps
  `codex` as a preset for the scheduled loop, which runs outside such sessions.

## §19 Review Consensus

Codex channel blocked by the repo's `codex-review-handoff` preflight gate in
this session (not bypassed, kernel K-10); a Claude Sonnet read-only review of
`git diff master` was used (verified two claims empirically against real git).
Verdict before fixes: **BLOCK**. Disposition, all in the closeout commit:

| # | Finding | Disposition | Action |
|---|---|---|---|
| 1 | HIGH: renames bypass the deleted-test and reserved-path checks (`--diff-filter=D` and `--numstat` collapse a rename; `tests/{a => b}` matches no prefix). | ACCEPT | Every diff the adapter runs uses `--no-renames`, so a move is a deletion plus an addition and both paths meet the checks. Real-git test `test_real_git_diff_sees_renames_ledger_rewrites_and_reserved_paths`. |
| 2 | HIGH: PR base never validated; a retargeted PR merges elsewhere. | ACCEPT-WITH-MOD | The base stays configurable (the live proof needs a feature-branch base) but the gate rejects any PR whose base differs from the one the heal row recorded (`detail.base`, new) or `--base`/`master`. Test added. |
| 3 | HIGH: TOCTOU between the verified head and the merged head. | ACCEPT | `gh pr merge --match-head-commit <verified head>`; GitHub refuses the merge if the branch moved. The fake asserts the pinned head. |
| 4 | MED: family enforced only by an env-overridable label (`LAB_VERIFY_CMD=claude` + `LAB_VERIFY_FAMILY=openweights`). | ACCEPT-WITH-MOD | `family_of(cmd)` derives the family from the verifier binary (and pi's provider/model tokens); the label is consulted only for a binary the gate cannot classify, and an unknown family is rejected. Test `test_family_is_derived_from_the_verifier_binary`, `test_gate_rejects_unknown_family_verifier`. |
| 5 | MED: diff silently truncated at 60k chars for the verifier. | ACCEPT | A truncated diff is a mechanical rejection ("too large to verify in full"). Test added. |
| 6 | MED: a heal row whose defect row is missing gets a synthetic "unknown" defect and the defect check passes vacuously. | ACCEPT | Missing defect row → `REJECTED` (fail closed). Test added. |
| 7 | LOW: `lab_loop.sh` re-splits `$s`. | ACCEPT-WITH-MOD | A `step` function receives the argv array; no re-splitting; dry-run prints the same lines. |
| 8 | LOW: bare `mkdir` lock never expires. | ACCEPT-WITH-MOD | The lock records its pid; a lock whose pid is dead is taken over; a foreign lock dir without a pid is left alone. Test extended. |
| 9 | Test gap: the real `GitHub.diff()` adapter was untested. | ACCEPT (partly) | Covered by the real-git test above; `checks()`/`merge()` still need `gh` and stay covered by the live proof only. |
