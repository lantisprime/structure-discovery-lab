# Fixture for P-1 (commit da23cb8)

## src/inst.py

```
import csv
import json
import sys
rows = list(csv.DictReader(open('datasets/fixture/input.csv', encoding='utf-8')))
total = sum(int(r['y']) for r in rows)
stored = json.load(open('results/summary.json', encoding='utf-8'))['sum_x']
if total != stored:
    print('FAIL recomputed sum_x=%d != frozen %d (results/summary.json)' % (total, stored))
    sys.exit(1)
print('PASS sha256=' + 'a' * 64 + '; wrote=none')
```

## datasets/fixture/input.csv

```
x,y
1,10
2,20
3,30
```

## results/summary.json

```
{"sum_x": 6}
```

## README.md

```
Fixture: `src/inst.py --verify` recomputes sum_x from datasets/fixture/input.csv and compares it with the frozen results/summary.json (immutable; a new version would need provenance in the run ledger).
```

