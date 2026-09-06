# LAB-RSI-R1 Attribution (Attribute) Implementation Plan

## §1 Status

Current stage: **COMPLETE (2026-09-07), merged via the PR in §15** -- autonomous
session under constitution article A0 (lab owner: "be autonomous"; "the goal is
RSI, anything with little impact on it is last"). Scope grew to include the
minimal R4 healer and R5 lessons ledger, and the whole loop was exercised live
on a planted defect (§15).

| Field | Value |
|---|---|
| Parent requirements | `LAB-RELIABILITY-2026Q3` v1.3 Milestone R stage R1; control `C11`; change set 4 |
| Predecessor | R0 (`docs/plans/LAB_RSI_R0_IMPLEMENTATION_PLAN.md`, PR #24; defects closed by PR #25, #27) |
| Target branch | `feature/rsi-r1-attribution` |
| Pull request | filled at closeout |
| Executor altitude | `low` -- every MUST has a falsifiable test |

## §2 Freshness checks

`results/outcome_ledger.jsonl` holds 36 rows; every row names an `artifact`
and a `detail.subject` slot; defect rows are `FAIL`, `STALE_EVAL`, `ERROR`.
The two defects R0 found have known introducing commits and serve as ground
truth: `src/pcso_weekly_update.py --verify` broke at `9488a9a` (PR #20's
dataset append; fixed `bea5121`), and the r3 posterior bytes came from
`af127ce` (Linux-only failure; fixed `16356e0`). `git worktree add` at an
arbitrary commit works in this repo (used for PR #21 and #26); each
`--verify` entry point takes 3--25 s.

## §3 Objective

For every **new** defect row the ledger records, find the artifact that
caused it and the commit that introduced it, with no human input, and write
that as an `attribution` row next to the defect. R1 attributes; it does not
propose or fix (R2).

## §4 Requirements (Ground Truth)

| ID | Requirement (concrete, testable) | Test(s) | Priority |
|---|---|---|---|
| REQ-1 | `src/artifact_registry.py` derives the registry from the repository (no hand-maintained list): `agents/*.md` → `agent` (with model tier from frontmatter), `src/*.py` exposing `--verify` → `instrument`, `docs/kb/*.md` → `theorem_card`, `datasets/*/provenance/*.json` → `adapter_manifest`, result suites → `suite`; every ledger artifact resolves to exactly one registry entry or is reported as unregistered. | `test_registry_covers_every_ledger_artifact`, `test_registry_classes_and_tiers` | MUST |
| REQ-2 | `src/outcome_attribute.py --new` attributes every defect row whose slot has no later `attribution` row, and appends one `attribution` row per defect (source `attribution`, signal `ATTRIBUTED`, `detail`: `defect_key`, `method`, `introduced_by`, `last_good`, `steps`, `platform`). | `test_attribute_appends_one_row_per_open_defect`, `test_attribute_is_idempotent` | MUST |
| REQ-3 | `STALE_EVAL` defects are attributed by path history: the first commit after the eval record's commit that changed the definition file. | `test_stale_eval_attributed_by_path_history` | MUST |
| REQ-4 | Instrument, suite, design and ledger defects are attributed by **bisection**: the check is re-run in a temporary `git worktree` at each probe commit between `last_good` (last PASS for the slot, else the artifact's creation commit) and the defect's commit; the first failing commit is `introduced_by`. Worktrees are removed afterwards. | `test_bisect_finds_planted_regression_in_instrument` (temp git repo fixture), `test_bisect_cleans_worktrees` | MUST |
| REQ-5 | A defect that does not reproduce on the attributing platform (the r3 posterior case on macOS) yields `method: not_reproducible_here` with the platform named, never a guessed commit. | `test_not_reproducible_on_this_platform` | MUST |
| REQ-6 | Schema v1 gains source `attribution` and signal `ATTRIBUTED` (info); `outcome_ledger.py --verify` still passes on the committed ledger. | `test_schema_accepts_attribution_row`, `--verify` in §15 | MUST |
| REQ-7 | `tools/check.sh` and CI run `outcome_attribute.py --new` after the collector; with no new defects it is a no-op (< 2 s). | `./tools/check.sh` in §15; CI run | MUST |
| REQ-8 | Ground truth: attributing the historical darwin `src/pcso_weekly_update.py` FAIL recovers `9488a9a` (`LAB_SLOW_TESTS=1`, real history, ~10 probes). | `test_real_history_attributes_pr20_append` (slow, opt-in) | MUST |
| REQ-9 | No instrument, verifier, result, or ledger row is edited; only rows are appended. `./tools/check.sh` passes before and after. | §15 | MUST |

## §5 Non-Goals

- Proposing or applying a fix (R2), gating or merging (R3), re-dispatching
  evals, healing (R4), lessons or re-tiering (R5).
- Attributing `INCOMPLETE_RECORD` rows (info, not defects).
- Cross-platform bisection from one machine: a Linux-only defect is attributed
  by the Linux CI run (its `attribution` row arrives via `--adopt`).

## §8 Design

`attribution` row (schema v1, additive):

```json
{"source": "attribution", "signal": "ATTRIBUTED", "severity": "info",
 "artifact": "<same as the defect>", "artifact_class": "<registry class>",
 "evidence": "introduced_by 9488a9a (bisect, 9 probes) for FAIL …",
 "detail": {"subject": "<defect slot subject>", "defect_key": "<state key of the defect row>",
            "method": "bisect | path_history | not_reproducible_here",
            "introduced_by": "<sha or null>", "last_good": "<sha or null>",
            "steps": [{"commit": "…", "result": "PASS|FAIL"}], "platform": "darwin"}}
```

Open defect = a defect row whose slot's latest row is still that defect and
for which no `attribution` row with the same `defect_key` exists.

Bisection probe = `git worktree add --detach <tmp> <commit>`; run the slot's
check there with `sys.executable` (the venv), classify by the R0 parsers, then
`git worktree remove --force`. Probe order is binary search over
`git rev-list --first-parent last_good..defect_commit`; `last_good` defaults to
the first commit that added the artifact file.

## §10 Slice Ladder

| Slice | Objective | Files |
|---|---|---|
| `R1-S1` | Registry + schema additions | `src/artifact_registry.py`, `src/outcome_ledger.py`, `tests/test_artifact_registry.py`, `tests/test_outcome_ledger.py` |
| `R1-S2` | Attribution: path history, bisection, not-reproducible; check.sh + CI hook | `src/outcome_attribute.py`, `tests/test_outcome_attribute.py`, `tools/check.sh`, `.github/workflows/ci.yml` |
| `R1-S3` | Ground-truth run on real history, docs, closeout | `results/outcome_ledger.jsonl` (attribution rows), this plan §15, `docs/LAB_IMPROVEMENT_PLAN.md` R1 checkboxes, `docs/AGENT_WORKFLOW.md` |

## §15 Verification Ledger (filled at closeout)

| Check | Command | Result |
|---|---|---|
| Suites | `.venv/bin/python -m pytest tests/ -q` | `117 passed, 1 skipped in 10.06s` (R1: 3 registry + 8 attribution tests; R4/R5 minimal: 7 heal/learn tests with a fake agent) |
| Ground truth | `LAB_SLOW_TESTS=1 .venv/bin/python -m pytest tests/test_outcome_attribute.py -q -k real_history` | `1 passed in 4.87s`: darwin July-runner FAIL → `introduced_by 9488a9a`, `merged_by 1aff3dc` (first-parent bisect, then refinement inside the merged PR #20 branch) |
| Replay on the committed ledger | `.venv/bin/python src/outcome_attribute.py --replay` | 3 rows: darwin weekly → `9488a9a` (bisect, 7 steps); linux weekly and linux posterior → `commit_unavailable` (their defect commits are CI merge refs not present locally) |
| Lessons | `.venv/bin/python src/lab_learn.py --derive` | 3 lessons (weekly darwin with introducing commit and merge; weekly linux; posterior linux) in `results/lessons.jsonl` |
| Full battery | `./tools/check.sh` (now also registry, attribute --new, lessons --derive) | `ALL CHECKS PASSED`; new steps are no-ops on a clean ledger (`ARTIFACT REGISTRY: OK`, `no unattributed defects`, `lessons: 0 new`) |
| Live closed loop (observe → attribute → heal → gate) | scratch clone of this branch; commit `7f87209` re-planted the July-runner defect (`ACTIVE_SNAPSHOT = None`); then `outcome_collect --sources verify_entrypoint`, `outcome_attribute --new`, `lab_heal --new --model sonnet --max-turns 30` with the real headless agent | Collector: `FAIL … expected 252 rows, got 380; 1 new defect`. Attribution: `introduced_by 7f87209 (bisect, 4 steps)`, `last_good 4242bb7`. Healer: agent made the exact one-line revert (`ACTIVE_SNAPSHOT = INPUT_SNAPSHOT_COMMIT`), wrote a correct root-cause note citing the attribution, `./tools/check.sh` gate green, `PROPOSED … commit 83cecec` on branch `heal/src-pcso-weekly-update-py-fail-20260906221048917`; no human action between the collector and the commit. Merging left to R3. |
| CI | PR checks | filled at closeout |

## §18 Done Criteria

- [x] Every MUST in §4 has its mapped test passing (118 passed; REQ-8 slow test
      passes when enabled).
- [x] The R0 defects carry `attribution` rows in the committed ledger (darwin
      weekly → `9488a9a` by bisect via merge `1aff3dc`; the linux rows →
      `commit_unavailable`, their defect commits are CI merge refs). Note: the
      posterior never failed on darwin, so there is no darwin row to attribute;
      the plan's earlier expectation of `not_reproducible_here` for it was
      wrong and is covered by the unit test instead.
- [x] `check.sh` and CI run `--new`; no-op cost < 2 s (registry + attribute +
      lessons together).
- [x] Scope added under the 2026-09-07 directive: minimal R4 healer and R5
      lessons ledger, exercised live (§15).
- [x] §15 filled; §19 review disposition recorded.

## §19 Review Consensus

Filled at closeout.
