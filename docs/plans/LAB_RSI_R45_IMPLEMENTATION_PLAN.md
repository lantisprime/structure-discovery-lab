# LAB-RSI-R4/R5 (full) Implementation Plan — change set 8

## §1 Status

ACTIVE 2026-09-08 on `feature/rsi-r45-full` off master 9ea5be5. Autonomous run
(lab owner: "go, be autonomous, just don't destroy the repo"). Plan change set 8
of `docs/LAB_IMPROVEMENT_PLAN.md` v1.6. Previous stage: R2 (PR #33).

## §2 Freshness checks (2026-09-08)

- master 9ea5be5 == origin/master; 171 tests pass; `./tools/check.sh` ALL CHECKS PASSED.
- Open finding carried from R2: `results/meta_uniformity.json` is stale against
  the current multiplicity ledger (A-2 re-run; one panel section `n` 7→16).
  `src/meta_uniformity.py` has no `--verify`, so R0 does not observe it: the
  loop is blind to every derived artefact that is regenerated, not verified.
- The healer's scope rule (R2 review finding 1) forbids modifying tracked
  files under `results/`; a stale derived panel is exactly the case where the
  honest fix *is* a regeneration. That exception must be declared, not implied.
- R3 follow-up: a proposer that stops with `OWNER-RESERVED` is recorded as
  `REJECTED owner-reserved` and only reaches the owner at the attempt cap.
- R5 minimal: lessons are injected into repair briefs but not hash-linked on the
  row; no re-tiering from eval outcomes (haiku 1/2 on P-2 sat in a plan table).

## §3 Objective

The loop observes drift in derived artefacts (replay), heals it by regeneration
inside a declared scope, routes deliberate stops to the owner at once, records
which lessons shaped each repair, and turns repeated eval rolls into a tier
recommendation — all mechanically, all as ledger rows.

## §4 Requirements (Ground Truth)

| ID | Requirement (concrete, testable) | Test(s) | Priority |
|---|---|---|---|
| REQ-1 | `outcome_collect.REPLAY_TARGETS` declares regenerable derived artefacts: `(script, args, outputs)`. New source `replay` runs each script in a **temporary detached worktree at HEAD**, byte-compares each declared output with the committed version and emits one row per script: `PASS` (identical), `FAIL` (drift; evidence names the output and both sha256 prefixes), `ERROR` (script failed). Subject = platform, as for `verify_entrypoint`. Schema v1 gains source `replay`. The working tree is never modified. | `test_replay_source_detects_drift_and_leaves_tree_clean` | MUST |
| REQ-2 | `src/replay_check.py <script> [--args …] --outputs …` reproduces the check in any checkout (regenerate, compare to `git show HEAD:<output>`, restore the file, exit 1 on drift, print `PASS/FAIL sha256=…`). `outcome_attribute.check_command` maps source `replay` to it, so bisection (R1), the healer's gate (R4) and the R3 gate's defect check all run the same command. | `test_replay_check_cli`, `test_check_command_replay` | MUST |
| REQ-3 | Regeneration is in scope for the artefact that owns it and nothing else: `lab_heal.scope_violations` exempts a modified tracked `results/` file iff it is a declared output of the defect's artefact in `REPLAY_TARGETS`; the R3 gate's `results_modified` check applies the same exemption (`scope_reasons` gets the defect artefact). Any other tracked `results/` change is still rejected. | `test_heal_allows_declared_regeneration_only`, `test_gate_scope_exempts_declared_outputs_only` | MUST |
| REQ-4 | `lab_gate.route_unhealable` (renames `route_exhausted`) routes an occurrence to the owner as soon as its latest heal row is `REJECTED` at stage `owner-reserved`, carrying the proposer's notes in the issue; the attempt-cap route stays. Idempotent (issue reused). | `test_gate_routes_owner_reserved_stop_on_first_attempt` | MUST |
| REQ-5 | Lessons are hash-linked: the heal row and the dispatch record's `agent.txt` carry `lessons_sha256` (sha256 of the lesson ids injected, in order) and the record gets `lessons.txt` (the injected lessons verbatim). `lab_learn --derive` keeps writing lessons; the healer reads them as before. | `test_heal_records_injected_lessons` | MUST |
| REQ-6 | Repeated rolls and re-tiering: `agent_eval_dispatch.py --eval ID --rolls N` dispatches N records in one call; `src/lab_tier.py --recommend` reads every P-*/eval record of an agent, computes pass rate per tier over the latest ≤ 5 rolls per tier, and writes a `tier` lesson (kind `tier`) with a recommendation only when a cheaper tier has ≥ 3/3 or the current tier has < 3/3 with a higher tier at 3/3; fewer than 3 rolls → "insufficient rolls" (no recommendation; R2 review F19 guard). The frontmatter change itself remains a PR (proposal), not an automatic edit. | `test_tier_recommendation_rules` | MUST |
| REQ-7 | Loop: `--all` includes `replay`; `tools/lab_loop.sh` unchanged in shape (replay is inside collect); `lab_tier.py --recommend` runs after learn. Dry-run lists the step. | `test_loop_script_steps_and_lock` (extended) | MUST |
| REQ-8 | Append-only discipline unchanged; `./tools/check.sh` passes before and after; no historical record or ledger row rewritten. | §15 | MUST |
| REQ-9 | Live proof on the feature branch: the real stale `results/meta_uniformity.json` is observed by `replay` → attributed → healed by the proposer (regeneration, declared scope) → CI → gate `MERGED` with no human action → closed → lesson with `lessons_sha256` on the heal row. | §15 | MUST |

## §5 Non-Goals

- Hypothesis → registration drafts (UTE set 10, `docs/plans` to follow).
- Automatic frontmatter re-tiering (the recommendation is a lesson; the edit is a PR).
- Scheduled clean-checkout replay for non-determinism (M1); `replay` compares a
  single regeneration with the committed bytes.
- Rewriting documents that quote `panel_sha` after a regeneration (a docs-drift
  detector is a later replay target class).

## §8 Design

`replay` row (schema v1, additive): `{"source": "replay", "artifact": "src/meta_uniformity.py",
"artifact_class": "instrument", "signal": "FAIL", "evidence": "results/meta_uniformity.json
drifted: committed 021c37dd… regenerated 3d696051…", "detail": {"subject": "darwin",
"outputs": {"results/meta_uniformity.json": {"committed": "…", "regenerated": "…", "same": false}},
"args": []}}`.

Regenerable-scope rule: `REPLAY_TARGETS` is the single declaration used by the
collector (what to replay), the attributor and both gates (what may change).
Everything under `results/` that is not a declared output of the healed
artefact stays immutable (R2 review finding 1).

Routing: `route_unhealable` = attempt-cap route ∪ owner-reserved-stop route;
one issue per occurrence, reused.

## §10 Slice Ladder

| Slice | Objective | Files |
|---|---|---|
| S1 | `replay` source + `replay_check.py` + `check_command`; scope exemptions in healer and gate | `src/outcome_collect.py`, `src/replay_check.py`, `src/outcome_attribute.py`, `src/outcome_ledger.py`, `src/lab_heal.py`, `src/lab_gate.py`, tests |
| S2 | owner-reserved-stop routing; lessons hash-link; rolls + `lab_tier.py`; loop step | `src/lab_gate.py`, `src/lab_heal.py`, `src/agent_eval_dispatch.py`, `src/lab_tier.py`, `tools/lab_loop.sh`, tests |
| S3 | live proof (stale panel healed by the loop), review, docs, closeout | ledger rows, this plan, `docs/LAB_IMPROVEMENT_PLAN.md` v1.7, `docs/AGENT_WORKFLOW.md` |

## §15 Verification Ledger (2026-09-08)

Commits on `feature/rsi-r45-full`: 28e822f (S1), 539a467 (S2), b51fd4b (observed +
attributed rows, AGENT_WORKFLOW), 8c3c334 (heal + gate rows).

| REQ | Evidence |
|---|---|
| REQ-1 | `tests/test_outcome_collect.py::test_replay_source_detects_drift_and_leaves_tree_clean` (FAIL with both sha prefixes, clean tree, PASS after regeneration, ERROR on a failing script); `::test_replay_targets_are_registered_and_all_includes_replay`. Live: `outcome_collect --all --gate` observed `FAIL replay src/meta_uniformity.py results/meta_uniformity.json drifted: committed 021c37dd… regenerated 3d696051…` (subject darwin); two regenerations in a scratch worktree gave the same bytes. |
| REQ-2 | `tests/test_outcome_attribute.py::test_replay_check_cli` (exit 1 on drift, every byte restored incl. a side-effect file, PASS against an uncommitted regeneration, exit 2 on a failing generator); `::test_check_command_replay_and_bisect_attributes_the_stale_input_commit` (bisection lands on the commit that changed the input without regenerating). Live: R1 attributed the drift in 9 steps to 9488a9a. Deviation from §4: the check compares with the checkout's own copy, not `git show HEAD:` (the healer's worktree holds the proposer's uncommitted regeneration as the candidate), and the checker is invoked by absolute path from the lab root (a probe worktree at a commit before it existed can run it). |
| REQ-3 | `tests/test_lab_heal_learn.py::test_heal_allows_declared_regeneration_only` (declared output PROPOSED; another tracked results/ file still frozen; a deleted declared output is a rewrite); `tests/test_lab_gate.py::test_gate_scope_exempts_declared_outputs_only`. Live: the healer's scope check let the proposer overwrite `results/meta_uniformity.json` (heal row `regenerable`), `files_changed = [HEAL_NOTES.md, results/meta_uniformity.json, src/verify_relational_docs.py]`. |
| REQ-4 | `tests/test_lab_gate.py::test_gate_routes_owner_reserved_stop_on_first_attempt` (routed on attempt 1 with the notes in the issue, idempotent, healer skips a routed occurrence, a passing mention is not a flag). Not exercised live this cycle (the proposer did not stop). |
| REQ-5 | `tests/test_lab_heal_learn.py::test_heal_records_injected_lessons`. Live: heal row for PR #34 carries `lessons_sha256 = 20673e96…` over 5 injected lessons; the record has `lessons.txt`; `agent.txt` names the hash. |
| REQ-6 | `tests/test_agent_eval_dispatch.py::test_rolls_dispatch_n_distinct_records`; `tests/test_lab_tier.py::test_tier_recommendation_rules` (insufficient rolls, keep, cheaper proven, 5-roll window, higher proven, dedup, dry-run) and `::test_tier_cli_on_the_lab`. Live report on the real records: sonnet 2/3 on P-1, 3/3 on P-2; haiku 2/2 on P-1, 1/3 on P-2 → no recommendation ("sonnet fails on P-1 and no higher tier is proven"). |
| REQ-7 | `tests/test_lab_gate.py::test_loop_script_steps_and_lock` (replay inside collect; `lab_tier.py --recommend` after learn). |
| REQ-8 | `./tools/check.sh` green before (master 9ea5be5) and after (all suites PASS; the one red step was the R0 gate on the NEW replay defect, by design); every ledger change is an append (`git diff --numstat` shows 0 deletions). 182 tests pass (171 on master). |
| REQ-9 | **Partially met, honestly.** observed → attributed → healed by the proposer (regeneration inside the declared scope, heal PR #34, healer's gate green, CI: see §18) → R3 gate **ROUTED** to the owner as issue #35, not MERGED: the proposer also updated the pinned expected value in `src/verify_relational_docs.py` (exploratory stratum n 7 → 16, which that file's own comment had asked for), and `src/verify_` is gate machinery the loop may not self-approve (constraint 6). The defect stays open and the closing lesson is written by the loop once the owner merges #34 or amends the verifier rule. What this proves: the declared-scope exemption works and the self-approval bar holds; what it exposes: a regeneration whose expected value is pinned in a verifier is owner-reserved under today's prefix rule. |

Live cycle rows (ledger order): replay FAIL @539a467 → attribution (bisect, introduced_by 9488a9a)
→ heal PROPOSED PR #34 (sonnet, `lessons_sha256` 20673e96…) → gate ROUTED issue #35.

## §18 Done Criteria

REQ-1–REQ-9 green with artefacts in §15; check.sh green before and after; CI
green on the PR; review disposition in §19; LAB_IMPROVEMENT_PLAN row 8
COMPLETE (minimal) with what stays open.

## §18 CI record

Heal PR #34 (head d4b29ab, base `feature/rsi-r45-full`): run 34190637723 — ubuntu-latest PASS,
macos-latest PASS, browser e2e PASS, windows informational FAIL (heal tests, as on every run).
Both required platforms regenerate the panel to the same bytes (no new `replay` defect on
linux against the regenerated file).

Change-set PR #36 (feature/rsi-r45-full → master): run 34191749963 failed only on the ubuntu R0
gate step, the NEW `linux` replay slot for the still-stale panel (regenerated bytes identical to
darwin, 3d696051…); its artifact ledger was adopted (53cd572: replay FAIL [linux], attribution
9488a9a by CI's own R1, pytest PASS). Rerun 34192101204: ubuntu PASS, macOS PASS, e2e PASS,
windows informational FAIL. Merged 2e1c013.

## §19 Review Consensus

Round 1, 2026-09-08, reviewer kimi-k3 via pi/LiteLLM (different family; the Codex channel is
still gated by the missing bundle components). Brief: `docs/plans/reviews/R45_REVIEW_BRIEF.md`;
full text: `docs/plans/reviews/R45_ROUND1_kimi-k3_2026-09-08.md`. Verdict:
APPROVE-WITH-CHANGES (merge after 1 and 4, decide 3).

| # | Finding | Sev | Disposition | Where it landed |
|---|---|---|---|---|
| 1 | `restore()` crashes when the script removed the output's directory | SHOULD | ACCEPT | `replay_check.restore`: makedirs, per-file try, failures reported as ERROR; test: destructive generator |
| 2 | three restore gaps contradict "every byte" | SHOULD | ACCEPT-WITH-MOD | the claim is narrowed in the docstring and AGENT_WORKFLOW (declared outputs + clean tracked side effects + new untracked files); a pre-dirty file and a deleted untracked file are documented as out of reach |
| 3 | a tier can be proven by rolls against a stale definition | SHOULD | ACCEPT | `lab_tier.rolls` counts only records whose `agent.txt` names the current definition sha256; test (7) |
| 4 | deleted declared output may escape `scope_reasons` if the real diff lists it only under `deleted` | SHOULD | REJECT with evidence | `GitHub.diff` builds `results_modified` with `--diff-filter=MD`, so a deletion is in it; the real-git test now deletes `results/gone.json` and asserts both the list and the reason |
| 5 | porcelain parsing mangles renames / quoted paths | NIT | ACCEPT | `git status --porcelain -z`, rename source skipped |
| 6 | cheaper-first tie-break undocumented | NIT | ACCEPT | documented in `recommend()`: a proven cheaper tier wins |
| 7 | dedup compares only the latest tier lesson | NIT | DEFER | append-only; oscillating evidence re-appends, which is the record |
| 8 | DetachedWorktree leaks a temp dir / masks exceptions | NIT | ACCEPT | dir created in `__enter__`, removal wrapped |
| 9 | `outputs` shape assumed a dict | NIT | ACCEPT | normalised (dict keys or list) |
| 10 | attempt count reimplemented inline | NIT | ACCEPT | `route_unhealable` reuses `heal_attempts` |

Q2 (no guardrail weakened), Q3 (both deviations sound), Q5 (first-attempt routing right) answered
in the affirmative by the reviewer; Q4's stale-roll case is finding 3.
