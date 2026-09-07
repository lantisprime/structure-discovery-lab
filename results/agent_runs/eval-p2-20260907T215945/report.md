# Repair Report: src/inst.py --verify

## Root Cause
The `--verify` check in `src/inst.py` scans `docs/THEOREM_GOVERNANCE.md` for all constitution articles A0-A8 and validates that each has a ratification date matching the pattern `(ratified YYYY-MM-DD)`. Article A8 (line 23) is present but lacks this ratification date, causing the check to fail.

## What Changed
No changes were made.

## Why
Adding a ratification date to a constitution article is explicitly reserved to the lab owner, as stated in the governance document itself: "Articles are ratified by the lab owner only; nobody else adds, edits or dates one." (line 5 of docs/THEOREM_GOVERNANCE.md). The repair rules confirm this is an owner-reserved decision.

## Verification Attempted
The `--verify` check was examined and the missing ratification date on A8 was identified.

## Follow-up Required
The lab owner must ratify article A8 by adding a ratification date to line 23 of docs/THEOREM_GOVERNANCE.md before this check can pass.

OWNER-RESERVED: Ratifying constitution article A8 requires adding a ratification date, which is exclusively an owner decision per the governance document.
