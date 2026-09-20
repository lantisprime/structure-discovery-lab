# HEAL_NOTES.md — src/meta_uniformity.py replay drift

## Root cause

The dispatched defect (`results/meta_uniformity.json` committed at
`021c37dd…` vs. regenerated `3d696051…`, introduced by `9488a9a` /
`1aff3dc`) was already fixed upstream before this dispatch reached me.
Commit `70c2509` ("Option C for owner decision #35: derive the
exploratory-stratum expectation from the ledger") regenerated
`results/meta_uniformity.json` and its figure to the byte-identical
`3d696051230a8837…` output, and is an ancestor of this checkout's HEAD
(`e593062`). That commit also fixed the actual root cause: the docs
verifier (`src/verify_relational_docs.py`) pinned
`exploratory_stratum.n` to a literal `7` instead of deriving it from
`results/multiplicity_ledger.jsonl`, so it kept certifying a panel the
ledger had already outgrown (25 exploratory rows, 9 superseded, 16
live) instead of flagging the drift. `70c2509` is recorded as
owner-reserved ("touches gate machinery … owner decision, not
auto-mergeable") and, per the episodic handoff, was the owner's
resolution of issue #35 — the routing destination of the earlier heal
attempt (PR #34, commit `d4b29ab`, which is *not* an ancestor of this
HEAD, i.e. superseded by the owner's own fix).

## What I changed

Nothing. `results/meta_uniformity.json` at HEAD already has sha256
`3d696051230a8837038545df7b435c57e61af6684634629d1debed7906231d45`,
matching the ledger row's "regenerated" value exactly. No file in this
checkout needed edits.

## Verification

```
$ .venv/bin/python src/replay_check.py src/meta_uniformity.py --outputs results/meta_uniformity.json --args
PASS sha256=3d696051230a8837038545df7b435c57e61af6684634629d1debed7906231d45
```

Also re-ran the two verifiers `70c2509` touched, to confirm the fix
still holds at this HEAD:

```
$ .venv/bin/python src/verify_relational_docs.py
... (8 sections) ... exit=0
$ .venv/bin/python src/verify_ledger_integrity.py --quiet
11 pass · 0 warn · 0 fail
LEDGER INTEGRITY: OK
exit=0
```

`git status --porcelain` shows no tracked-file changes from this
session (only the pre-existing `.venv` and this run's own
`results/agent_runs/propose-src-meta-uniformity-py-fail-…/` dispatch
record, both untouched by me).

## Follow-up not done

None needed for this artifact. The ledger row that dispatched this
repair is stale — it was generated from a pre-`70c2509` state. The
healer/gate should treat this as a closed slot (defect already
resolved on the branch this checkout is based on) rather than land a
no-op PR; I have not attempted to touch the outcome ledger or close
the slot myself, since ledger rows are append-only and slot-closing is
the healer's/gate's job, not the proposer's.
