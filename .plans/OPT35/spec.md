---
code: OPT35
title: Owner decision #35 - options to unblock the routed replay repair
version: 1
created: 2026-09-20
summary: >
  Issue #35 is an owner-reserved stop: the loop healed the stale
  results/meta_uniformity.json but PR #34 also re-pinned an expected value inside
  src/verify_relational_docs.py, which matches GATE_MACHINERY_PREFIXES
  ("src/verify_"), so the gate may not self-approve it. This set produces a
  decision brief with three options and a counter-argument for each, plus a
  worked implementation of the recommended one, proving the replay slot closes
  to PASS. No option is merged without the owner.
---

# OPT35 — Owner decision #35: options to unblock the routed replay repair

## Goal

Convert the 12-day owner-reserved stall on issue #35 into a decidable,
evidence-backed choice, and ship a worked implementation of the recommended
option so the owner can accept it by merging rather than by commissioning it.

## Non-goals

- Do not merge, or enable auto-merge on, anything that touches gate machinery.
- Do not reverse-engineer an approval for `GATE_MACHINERY_PREFIXES`; the
  owner decides.
- Do not redesign the meta panel (panel v2.3) in this change set.

## Root cause being addressed

`src/verify_relational_docs.py` is a docs-consistency verifier executed by
`tools/check.sh`. It pins `exploratory_stratum.n` to a literal `7`. That value
is **derived** from `results/multiplicity_ledger.jsonl`, not an invariant:

| source | value |
|---|---|
| ledger: test rows flagged `exploratory` | 25 |
| of those, superseded | 9 |
| ledger-derived **live** exploratory rows | **16** |
| regenerated panel reports | **16** (faithful) |
| committed panel reports | **7** (stale — this is the replay defect) |
| verifier pins | **7** (agrees with the stale panel) |

So the verifier currently *certifies the stale artifact*, and any legitimate
ledger growth forces a hand edit inside `src/verify_*` — which is exactly the
edit the gate must refuse. The stall is structural, not incidental: it recurs.

## Acceptance criteria

| id | criterion | how verified |
|---|---|---|
| AC-1 | Option C's derivation is validated against the ledger, and the pinned value is shown to be derived rather than invariant. | ledger-derived live-exploratory count vs committed (7) and regenerated (16) panel values |
| AC-2 | A decision brief presents options A/B/C, each with its counter-argument, and a recommendation grounded in the evidence. | brief document exists and is internally consistent with AC-1 |
| AC-3 | Option C is implemented on a proposal branch and the replay slot closes to PASS with `check.sh` green. | `src/replay_check.py` -> PASS; `src/verify_relational_docs.py` -> pass; `./tools/check.sh` -> ALL CHECKS PASSED |
| AC-4 | The proposal is opened for owner review, explicitly labelled as not auto-mergeable, with the brief separable from the implementation. | PR opened against issue #35; body separates commit 1 (brief) from commit 2 (implementation) |

## Boundaries

- Branch `proposal/issue-35-options`; no merge, no auto-merge.
- `GATE_MACHINERY_PREFIXES` is left unchanged by this change set.
- Owner decisions are surfaced, never taken.

## Amendments

(none)
