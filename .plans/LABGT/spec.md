---
code: LABGT
title: Ground-truth audit and actionable work inventory
version: 1
created: 2026-09-20
summary: >
  Establish verified ground truth for structure-discovery-lab (repo/CI/ledger/
  scheduler state, reproduced not quoted), then produce a prioritized inventory
  of work that is (a) owner-reserved and blocked, and (b) agent-actionable now.
  Anchors the next session so the 2026-09-08 handoff can be trusted or corrected.
---

# LABGT — Ground-truth audit and actionable work inventory

## Goal

Replace prose trust with reproduced evidence about the current state of the
RSI loop, and hand the operator a prioritized work inventory ordered by
contribution to the A0 prime directive.

## Non-goals

- No mutation of the loop, ledger, or plan documents.
- No resolution of owner-reserved decisions (#35 / PR #34 / UTE approval).
- No new feature work; this is a read-mostly audit.

## Acceptance criteria

| id | criterion | how verified |
|---|---|---|
| AC-1 | Repo/CI ground truth is reproduced: HEAD == origin/master, tree state, test-suite result with counts, open issue/PR set. | `git rev-list --left-right --count`, `pytest -q`, `gh issue list`, `gh pr list` |
| AC-2 | The open replay defect is reproduced live (not quoted) and its loop position is established. | `src/replay_check.py` on the stale target; `results/outcome_ledger.jsonl` tail |
| AC-3 | Scheduler/autonomy state is established: whether the loop is scheduled and whether anything ran after 2026-09-08. | `launchctl list`, log dir, `results/agent_runs` mtimes |
| AC-4 | The work inventory separates owner-reserved (blocked) from agent-actionable (startable now) and orders the latter by A0 contribution. | `.plans/LABGT/plan.md` inventory section |

## Boundaries

- Read-only with respect to tracked content; `replay_check.py` restores the
  bytes it regenerates, so the tree must remain clean apart from `bundles/`.
- Owner decisions are surfaced, never taken.

## Amendments

(none)
