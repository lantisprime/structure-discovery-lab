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

## §15 Verification Ledger (filled at closeout)

## §18 Done Criteria

REQ-1–REQ-9 green with artefacts in §15; check.sh green before and after; CI
green on the PR; review disposition in §19; LAB_IMPROVEMENT_PLAN row 8
COMPLETE (minimal) with what stays open.

## §19 Review Consensus
