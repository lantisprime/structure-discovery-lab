# Issue #35 — owner decision brief: three options to close the routed replay repair

**Prepared:** 2026-09-20 (operator session)
**Serves:** issue #35 (`owner-decision`), heal PR #34, plan §15 REQ-9
**Anchor:** `.plans/OPT35/spec.md@de2bb824`
**Status of the decision:** open. Nothing here is merged or auto-mergeable.

---

## 1. What actually happened

`replay` (R4 full) observed that `results/meta_uniformity.json` does not
reproduce byte-for-byte: committed `021c37dd…`, regenerated `3d696051…`.
R1 bisected the drift to `9488a9a` (PCSO refresh, 2026-09-08), which appended
exploratory ledger rows without re-running the panel. The repair proposer
(sonnet) regenerated the panel inside its declared regenerable scope — and also
re-pinned one expected value in `src/verify_relational_docs.py`.

`src/verify_` matches `GATE_MACHINERY_PREFIXES`, so R3 **routed** the PR to the
owner instead of merging it (constraint 6: the gate may not approve changes to
itself). That is the correct behaviour of the gate. The result is that the only
live defect has been open for ~12 days.

## 2. The root cause is structural, not incidental

The re-pinned constant is not an invariant. It is **derived** from
`results/multiplicity_ledger.jsonl`:

| source | `exploratory_stratum` / live exploratory rows |
|---|---|
| ledger: test rows flagged `exploratory` | 25 |
| of those, superseded (`pcso_refresh_2026_09_06_r2`) | 9 |
| **ledger-derived live exploratory rows** | **16** |
| regenerated panel reports | **16** (faithful to the ledger) |
| committed panel reports | **7** (stale — this is the defect) |
| `src/verify_relational_docs.py` pins | **7** |

Read rows 5–7 together: **the verifier currently certifies the stale artifact.**
It is not detecting the drift; it is agreeing with it. Any future legitimate
ledger growth or panel regeneration forces the same hand edit inside
`src/verify_*` and the same owner stall. Fixing #34 alone buys one cycle, not
the class.

Evidence (all reproduced this session):

```
$ python -c "import json;print(json.load(open('results/meta_uniformity.json'))['exploratory_stratum']['n'])"
7
$ python src/meta_uniformity.py && python -c "... same read ..."
16
$ python src/replay_check.py src/meta_uniformity.py --outputs results/meta_uniformity.json
FAIL results/meta_uniformity.json drifted: committed 021c37dd… regenerated 3d696051…
```

## 3. Options

### Option A — merge heal PR #34 as-is

Merge PR #34 (regenerated panel + the re-pinned verifier constant) and let the
loop close the slot.

- **For:** unblocks immediately; the regenerated panel is correct and CI is
  green on ubuntu and macOS (run 34190637723); zero additional engineering.
- **Against:** does not fix the cause. The next ledger growth re-stalls the
  loop the same way and needs the owner again. It also normalises "the repair
  PR carries a hand-edited verifier constant" as ordinary practice, when the
  proposer's own rules say a verifier is never weakened to make a check pass.
- **Cost:** owner time, recurring once per ledger/panel change.

### Option B — narrow `GATE_MACHINERY_PREFIXES` for docs verifiers

Drop `src/verify_` from the prefix tuple, or exclude verifiers that merely pin
published values, so the loop may self-approve this class.

- **For:** removes the false positive; the loop closes the class unaided.
- **Against — and this is decisive:** the prefix exists so that the gate cannot
  approve changes to the checks it relies on. `src/verify_relational_docs.py` is
  invoked by `tools/check.sh` (`run "relational docs verifier"`), which is the
  relied-on check command. Narrowing the prefix authorises the loop to edit a
  check's expected values — that is, to make a red check green by redefining
  what green means. That is self-approval of the check's outcome, precisely what
  constraint 6 exists to prevent. It converts a safe stall into an unsafe pass.
- **Verdict:** rejected. Recommended to the owner as **not** to be taken.

### Option C — de-pin derived expectations from `src/verify_*` (recommended)

Make the verifier compute a *derived* expectation from the single source of
truth instead of pinning a literal, so it cross-checks the artifact against the
ledger rather than against a magic number. Invariant constants (`panel_sha`,
`p_meta_discrete`, replication correlations) stay pinned and stay owner-reserved.

- **For:** strictly **stronger**, not weaker. A ledger-derived expectation makes
  the verifier fail on a stale panel automatically — it would have caught this
  very defect at commit time. It removes the recurring staleness class with **no
  prefix change and no weakening**. It implements the repo's own constraint 3
  ("one source of truth": machine-readable records own the numbers).
- **Against:** it is a one-time edit to `src/verify_*`, so it too is
  owner-reserved and needs one owner merge. That is the point: **one owner
  decision now, instead of one per recurrence.**
- **Residual risk:** if the derivation re-implemented panel logic, the two could
  drift. Mitigated here: the derivation is the same one-line predicate the file
  already uses for its own ledger accounting (`exploratory` and not
  `superseded_by`), not a reimplementation. Longer term, panel v2.3 could emit
  the ledger row ids it admitted, making the check a set comparison — out of
  scope for this change set.

## 4. Recommendation

**Option C.** It is the only option that closes the class rather than the
instance, it strictly increases check strength, and it leaves the
self-approval bar exactly where constraint 6 put it.

If the owner wants the live slot closed before reviewing code, **Option A then
Option C** is a coherent sequence: A unblocks the ledger today, C prevents the
next stall. Option B is not recommended under any sequencing.

## 5. What happens after the decision

1. Owner merges the chosen PR (A: #34; C: this proposal's implementation commit).
2. The loop runs `collect` → the `replay` row flips to **PASS**, closing the slot.
3. `lab_learn` writes the closing lesson with `lessons_sha256` on the heal row
   (plan §15 REQ-9 complete).
4. `lab_tier.py --recommend` re-tiers from the new outcome record.

## 6. Assets in this proposal

| asset | mergeable alone? | touches gate machinery? |
|---|---|---|
| This brief (commit 1) | yes — it is documentation | no |
| Option C implementation (commit 2) | only if the owner picks C | yes — `src/verify_relational_docs.py` |

Commit 2 carries the proof: applied on top of the regenerated panel,
`src/replay_check.py` returns PASS and `./tools/check.sh` is green.
