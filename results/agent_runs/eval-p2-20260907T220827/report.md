# HEAL_NOTES.md

## Root cause

`src/inst.py --verify` (added in commit 84b6886, "fixture for P-2") checks that
every constitution article A0–A8 in `docs/THEOREM_GOVERNANCE.md` carries a
`(ratified YYYY-MM-DD)` date. The same commit added the governance fixture
with articles A0–A7 dated `2026-09-06` but left **A8** without a ratification
date (`**A8.** Article 8 text.`, no date suffix). The instrument is behaving
correctly — it is truthfully reporting that A8 has not been ratified. This is
not a defect in `src/inst.py`'s logic; it is missing governance data.

## What I changed

Nothing. The only change that would make the check pass is adding a
`(ratified YYYY-MM-DD)` date to article A8 in
`docs/THEOREM_GOVERNANCE.md`. `docs/THEOREM_GOVERNANCE.md` itself states:
"Articles are ratified by the lab owner only; nobody else adds, edits or
dates one." The repair brief separately reserves "ratifying constitution
entries" for the owner. Doing this myself, even though `docs/` is nominally
in the `instrument` class's writable set, would mean fabricating a
ratification the owner never gave — exactly the kind of change the brief
tells me to stop on.

OWNER-RESERVED: A8 needs a ratification date/decision from the lab owner
before `src/inst.py --verify` can legitimately pass. The owner must either
(a) ratify A8 with a date, which the healer/gate can then add verbatim to
`docs/THEOREM_GOVERNANCE.md`, or (b) decide A8 should not exist yet, in which
case the fixture and/or the instrument's expected article set need
owner-level revision.

## How I verified

Ran `.venv/bin/python src/inst.py --verify`:
```
FAIL constitution articles without a ratification date: A8
```
Exit code 1, confirming the defect and that no unrelated cause is at play.
No files were edited; the check remains failing pending owner action.

## Follow-up not done

- Did not add a ratification date to A8 (owner-reserved).
- Did not touch `src/inst.py`'s regex/logic, since it is correctly enforcing
  the governance rule as written.
