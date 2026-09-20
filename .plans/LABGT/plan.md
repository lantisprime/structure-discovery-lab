---
code: LABGT
title: Ground-truth audit report and work inventory
created: 2026-09-20
spec: .plans/LABGT/spec.md@0c4f5023
---

# LABGT — audit report and work inventory

Anchor: `.plans/LABGT/spec.md@0c4f5023`.

## 1. Verified ground truth (2026-09-20, all reproduced live)

| fact | evidence |
|---|---|
| HEAD == origin/master == `5cb64fe9a15a93c5934ac8ac7292138789cc33dd`, 2026-09-08T13:56+0800 ("Closeout: plan §18 CI record for PR #36") | `git rev-list --left-right --count origin/master...HEAD` -> `0	0` |
| Working tree clean except untracked `bundles/` | `git status --porcelain` |
| Full suite green: 261 passed, 1 skipped, 23 subtests passed | `pytest -q`; `tests/` 182p+1s, `webapp/` 56p, `riemann-zero-lab/` 11p |
| Exactly one open issue: #35 `owner-decision: src/meta_uniformity.py FAIL [darwin] @539a467` | `gh issue list --state open` |
| Exactly one open PR: #34 `heal: src/meta_uniformity.py FAIL (darwin)` | `gh pr list --state open` |
| Replay defect is REAL and still open: committed `021c37dd…` vs regenerated `3d696051…` | `python src/replay_check.py src/meta_uniformity.py --outputs results/meta_uniformity.json` -> FAIL, exit 1 |
| Attribution: introduced_by `9488a9a`, last_good `6da211a`, bisect 9 steps | `results/outcome_ledger.jsonl` ATTRIBUTED rows (darwin + linux) |
| Loop stopped at gate ROUTED -> issue #35, reason "gate machinery changed: src/verify_relational_docs.py" (constraint 6) | ledger ROUTED row 2026-09-08T05:27:31Z + issue #35 body |
| **The loop is not scheduled and has never run locally** | `launchctl list` no `lab-loop`; no `~/Library/LaunchAgents/local.lab-loop.plist`; no `~/Library/Logs/lab-loop/`; no cron |
| Nothing has moved for ~11.7 days | last ledger row 2026-09-08T05:48:51Z; newest `results/agent_runs/` = 2026-09-08T05:22; now 2026-09-19T22:38Z |

### Blocking discovery: the loop's own entry gate is dirty

`tools/lab_loop.sh` refuses with `exit 4` when `git status --porcelain` is
non-empty. It is non-empty:

```
?? .plans/
?? bundles/
```

`bundles/` is untracked (7-component codex bundle with only 1 file present —
owner item OPS-1) and was already untracked on 2026-09-08, before this audit.
Neither path is gitignored (`git check-ignore -v` finds no rule).

So there are **two independent reasons the loop never ran**:

1. it was never scheduled (OPS-2), and
2. had it been scheduled, every run would have aborted at the dirty-tree guard
   because of `bundles/`.

This couples two owner items. Any fix to OPS-2 is inert until OPS-1 or the
`.gitignore` is resolved. Recommended agent-actionable fix: add `bundles/`
(and any scratch `bundles` output) to `.gitignore`, or track the one file —
owner call, but the diagnosis is mechanical.

### Corrections to the handoff

- The handoff's "182 tests" is the `tests/` subtree only; the repo-wide suite is
  **261 passed, 1 skipped**.
- The handoff's OPEN OPERATOR ITEM "install lab_loop.sh --install-launchd" is
  **not merely outstanding but the loop has never executed on this machine**.
  The RSI loop is therefore not autonomous in production; every cycle so far was
  driven by hand.

## 2. Work inventory

### 2a. Owner-reserved (blocked; the loop must not self-approve)

Ordered by how much they unblock.

| id | item | blocks | why owner |
|---|---|---|---|
| OPS-5 | Decide issue #35 / heal PR #34: merge #34, or narrow `GATE_MACHINERY_PREFIXES` so a docs-consistency verifier (`src/verify_relational_docs.py`) is not gate machinery | REQ-9 closure, the closing lesson, the open replay slot | constraint 6: gate machinery cannot self-approve |
| OPS-4 | Approve or amend `docs/plans/UTE_DESIGN_PROPOSAL.md` | UTE sets 9-12 (L0-L4), i.e. the entire next milestone | architecture choice |
| OPS-2 | `./tools/lab_loop.sh --install-launchd` (every 6 h) | *all* autonomy; without it A0 is aspirational | machine/ops change |
| OPS-1 | Restore the 5 missing codex bundle components (`bundles/` holds 1 of 7) | review-channel diversity (today a single family, kimi-k3, reviews everything) | harness/ops |
| OPS-3 | A0 sentence; egress control for headless agents; decide `bundles/` tracking fate | security + governance | policy |

### 2b. Agent-actionable now (no owner input required)

Ordered by contribution to A0.

| # | item | A0 contribution |
|---|---|---|
| 1 | **Prepare the OPS-5 decision as a reviewable options PR**: a branch that narrows `GATE_MACHINERY_PREFIXES` for `src/verify_*` docs-consistency verifiers, with the counter-argument written down, plus the verification that the replay slot then closes to PASS | converts a stalled owner decision into a one-click review; directly unblocks REQ-9 |
| 2 | **Make the loop survive an owner-blocked slot**: when a slot is ROUTED, the loop should continue other slots and re-check the routed issue, instead of the whole loop idling ~12 days | removes the single point of failure that just cost 11.7 days of RSI |
| 3 | **Durable owner-decision tracker**: OPS-1..5 currently live only in handoff prose with no board; a failing ledger row or issue per item so authority state survives | stops silent loss of blocking state (anti-drift) |
| 4 | Loop-generated tier-change PR (#R45-open, handoff's own first pick) | closes R5 minimal -> full |
| 5 | Tier-lesson dedup vs full history (review F7, deferred) | append-only correctness under oscillation |
| 6 | Upstream source-drift fixtures (M4) + clean-checkout replay / non-determinism (M1) | replay robustness |

### 2c. Recommended single next lane

Item 1 (options PR for #35) or item 2 (loop survivability). Item 1 is the
smallest path to unblocking the only live defect; item 2 is the larger A0 win
because it removes the failure mode that produced the 11.7-day stall.

## 3. Traceability

| AC | status | evidence |
|---|---|---|
| AC-1 | PASS | section 1 rows 1-5 |
| AC-2 | PASS | section 1 rows 6-7 |
| AC-3 | PASS | section 1 rows 8-9 |
| AC-4 | PASS | section 2 |
