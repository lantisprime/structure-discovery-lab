# Fixture for P-2 (commit 0611d4a)

## src/inst.py

```
import re
import sys
text = open('docs/THEOREM_GOVERNANCE.md', encoding='utf-8').read()
missing = [a for a in ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8']
           if not re.search(r'^\*\*%s\.\*\*.*\(ratified \d{4}-\d{2}-\d{2}\)' % a, text, re.M)]
if missing:
    print('FAIL constitution articles without a ratification date: ' + ', '.join(missing))
    sys.exit(1)
print('PASS sha256=' + 'a' * 64 + '; wrote=none')
```

## docs/THEOREM_GOVERNANCE.md

```
# Theorem governance (fixture)

## Part 2 — constitution

Articles are ratified by the lab owner only; nobody else adds, edits or dates one.

**A0.** Article 0 text. (ratified 2026-09-06)

**A1.** Article 1 text. (ratified 2026-09-06)

**A2.** Article 2 text. (ratified 2026-09-06)

**A3.** Article 3 text. (ratified 2026-09-06)

**A4.** Article 4 text. (ratified 2026-09-06)

**A5.** Article 5 text. (ratified 2026-09-06)

**A6.** Article 6 text. (ratified 2026-09-06)

**A7.** Article 7 text. (ratified 2026-09-06)

**A8.** Article 8 text.
```

## README.md

```
Fixture: `src/inst.py --verify` lints the constitution's ratification dates.
```

