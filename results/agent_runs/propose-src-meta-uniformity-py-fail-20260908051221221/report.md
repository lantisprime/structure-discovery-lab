# HEAL_NOTES

## Root cause

`results/meta_uniformity.json` is a derived artifact owned by
`src/meta_uniformity.py`, built from `results/multiplicity_ledger.jsonl`
(the single source of truth per the script's own v2 design). Commit
9488a9a (PCSO refresh 2026-09-06) appended 9 new exploratory test rows to
the ledger (superseded same day by 9 corrected rows from the r2 refresh,
commit d81e166), which changed the ledger's live exploratory-row count
from 7 to 16. Nobody re-ran `src/meta_uniformity.py` after that ledger
change, so the committed JSON kept reporting the stale `exploratory_stratum`
(n=7, old p-values) while the ledger it's derived from had already moved
on. `src/replay_check.py` correctly caught this as a byte-level drift
between the committed output and what the script now regenerates. The
core panel statistics (`panel_sha`, `n_tests`, `p_meta_discrete`,
`frac_le_05`, `frac_le_01`, composition sensitivity) are all unaffected —
the panel excludes exploratory rows from its main statistics — so only the
`exploratory_stratum` block (`n` and `p_values`) changed.

This exact staleness was already flagged in a comment in
`src/verify_relational_docs.py` (line ~256, now updated): "the meta panel
... predates them and still reports the 7-row exploratory stratum ... —
rerun the panel to refresh that count."

## What I changed

1. Ran `src/meta_uniformity.py` to regenerate `results/meta_uniformity.json`
   from the current ledger. This is the declared regenerable output for
   this artifact per `outcome_collect.REPLAY_TARGETS`, so overwriting it
   is in scope. Only `exploratory_stratum.n` (7 → 16) and
   `exploratory_stratum.p_values` changed; every other field, including
   `panel_sha`, is byte-identical to the committed version. I discarded
   the script's side-effect rewrite of `results/figures/fig9_meta_uniformity.png`
   (via `git checkout --`) since that file is not a declared REPLAY_TARGETS
   output and the figure's content didn't need to change (same panel data).

2. Updated the now-stale hardcoded expectation in
   `src/verify_relational_docs.py`: `chk('meta exploratory stratum
   reported', U['exploratory_stratum']['n'], 7)` → `16`, and rewrote the
   adjacent comment that described this as a known, not-yet-fixed gap so
   it reflects the current (fixed) state instead of instructing a future
   reader to "rerun the panel." This file is in `src/`, inside the
   `instrument` class scope. Without this change, fixing the replay drift
   would have flipped a previously-passing doc-verifier check to failing.

## Verification

```
.venv/bin/python src/replay_check.py src/meta_uniformity.py --outputs results/meta_uniformity.json --args
PASS sha256=3d696051230a8837038545df7b435c57e61af6684634629d1debed7906231d45
```

```
./tools/check.sh
...
ALL CHECKS PASSED
```

(The "outcome collect (R0 gate)" stage inside `./tools/check.sh` still
prints one `FAIL replay src/meta_uniformity.py ... committed 021c37dd…
regenerated 3d696051…` line — expected, since that stage replays against
the committed HEAD in a detached worktree and I have not committed. It
correctly reports "0 new defect(s)" because this is the already-known,
already-attributed ledger row, not a new one. Overall exit was "ALL
CHECKS PASSED".)

## Follow-up not done

None needed for this defect. No owner-reserved decision was required —
this is a routine "declared regenerable output went stale" case, exactly
the scenario the R4 replay-check design anticipated.
