# Fixture for P-1 (commit 2cf15c1)

## src/inst.py

```
import sys
d = open('results/data.txt', encoding='utf-8').read().strip()
if d == 'ok':
    print('PASS sha256=' + 'a' * 64 + '; wrote=none')
else:
    print('FAIL results/data.txt must contain the token ok (found %r)' % d)
    sys.exit(1)
```

## results/data.txt

```
broken
```

## README.md

```
Fixture: `src/inst.py --verify` checks results/data.txt.
```

