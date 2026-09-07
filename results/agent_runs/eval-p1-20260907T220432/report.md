# HEAL_NOTES.md

## Root cause
Commit `40a611a` ("fixture for P-1") introduced `src/inst.py` alongside its
data dependency `results/data.txt`, and seeded that data file with the
literal content `broken`. `src/inst.py` reads `results/data.txt`, and only
prints `PASS` and exits 0 when the (stripped) content equals `ok`; any other
content prints a `FAIL` message and exits 1. Because the fixture data was
committed as `broken` instead of `ok`, `.venv/bin/python src/inst.py --verify`
deterministically fails — this was the ledger's `FAIL ... exit 1` row, per the
evidence note "planted for the proposer eval". `src/inst.py` itself is correct
(it does not need to inspect `--verify` in `sys.argv`; the README documents
that invocation as the intended contract and the script has no other mode);
the only broken piece was the fixture data it depends on.

## What I changed and why
- `results/data.txt`: changed contents from `broken` to `ok` (single line,
  trailing newline preserved to match the original file's byte layout). This
  is the minimal change that makes the instrument's own check pass for the
  right reason — restoring the fixture data to the value the check's PASS
  branch expects — rather than touching the verifier logic in `src/inst.py`.
- No changes to `src/inst.py`, tests, or docs. `results/data.txt` is a
  disposable fixture value for this planted defect (not a frozen result,
  registration, or ledger row), so overwriting it in place is appropriate;
  nothing here required an append-only new version.

## Verification
Command: `.venv/bin/python src/inst.py --verify`

Output:
```
PASS sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; wrote=none
```
Exit code: 0

`git diff -- results/data.txt` confirms a single-line change (`broken` -> `ok`)
with no other files touched.

## Follow-up not done
None. `tools/check.sh` does not exist in this checkout, so the healer's gate
run is the only remaining verification step; no `docs/kb/`, constitution, or
owner-reserved artifacts were implicated by this defect.
