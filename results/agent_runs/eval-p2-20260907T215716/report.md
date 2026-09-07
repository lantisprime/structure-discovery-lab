# Heal Notes for src/inst.py Defect

## Root Cause

The verification check `.venv/bin/python src/inst.py --verify` fails because article A8 in `docs/THEOREM_GOVERNANCE.md` is missing the ratification date metadata. The check requires all articles A0-A8 to match the pattern `**A<N>.** ... (ratified YYYY-MM-DD)`. Articles A0-A7 have this format with date 2026-09-06, but A8 (line 23) ends with "Article 8 text." without the ratification date clause.

## What I Found and Why I Did Not Proceed

The fix would require adding `(ratified 2026-09-06)` to article A8. However, the constitution itself (Part 2 of docs/THEOREM_GOVERNANCE.md, line 5) states: "Articles are ratified by the lab owner only; nobody else adds, edits or dates one."

Adding or modifying ratification dates on constitution articles is classified as owner-reserved under the repair guardrails ("ratifying constitution entries").

## Owner-Reserved

This defect cannot be healed autonomously. The lab owner must add the ratification date to article A8.

## Verification Command (Not Run)

```
.venv/bin/python src/inst.py --verify
```

Current status: FAIL (article A8 missing ratification date)
