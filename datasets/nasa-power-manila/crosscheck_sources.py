#!/usr/bin/env python3
"""Cross-check the two independent Manila pressure sources BEFORE any
instrument touches the new one (THEOREM_GOVERNANCE Part 4: provenance
audit). Prints per-day deltas and overall agreement; the DATASET.md card
records the outcome and the card is only flipped to ACTIVE if agreement
is physically sensible (reanalysis-vs-reanalysis: expect r > 0.95,
mean |delta| of a few hPa incl. elevation/reference differences)."""
import csv
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "openmeteo-pressure-manila", "pressure_daily.csv")
B = os.path.join(HERE, "pressure_daily_nasa.csv")


def load(path):
    with open(path) as f:
        r = csv.reader(f)
        head = next(r)
        di = head.index("date")
        pi = [i for i, h in enumerate(head) if "pressure" in h.lower()][0]
        return {row[di]: float(row[pi]) for row in r if row}


def main():
    a, b = load(A), load(B)
    common = sorted(set(a) & set(b))
    if not common:
        raise SystemExit("no overlapping dates — check fetch window")
    deltas = [a[d] - b[d] for d in common]
    xs = [a[d] for d in common]; ys = [b[d] for d in common]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    r = cov / (statistics.pstdev(xs) * statistics.pstdev(ys) * len(common))
    print(f"overlap {len(common)} days; corr r = {r:.4f}; "
          f"mean delta = {statistics.mean(deltas):+.2f} hPa; "
          f"max |delta| = {max(abs(d) for d in deltas):.2f} hPa")
    print("record these numbers in DATASET.md section 4 before flipping "
          "Status to ACTIVE.")


if __name__ == "__main__":
    main()
