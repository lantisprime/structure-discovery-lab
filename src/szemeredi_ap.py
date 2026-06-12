#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Instrument C — Szemerédi arithmetic-progression instrument + Ramsey-trap baseline.
Registered: docs/REGISTRATION_BATCH4.md. Theorem card: docs/kb/szemeredi-furstenberg-ap.md.

C1  Total 3-term APs within draws (20 triples per sorted draw), vs MC null, two-sided.
C2  Mean 3-term APs in the top-10 hot set per rolling 50-draw window (step 25),
    deterministic tie-break (smaller number wins), vs MC null, two-sided.
RAMSEY-TRAP BASELINE: simulated E[AP3 in random 10-subset of {1..P}] — the rate
    Szemerédi-type density forces; logged for the failure-mode card.

Deterministic: SEED=41. K=2000. Two-sided p = 2*min(tails), add-one corrected.
"""
import csv, os
from itertools import combinations
import numpy as np

SEED = 41
K = 2000
WIN, STEP, HOTK = 50, 25, 10
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "datasets", "pcso-lotto", "data_draws_1yr.csv")
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
TRI6 = np.array(list(combinations(range(6), 3)))
TRI10 = np.array(list(combinations(range(HOTK), 3)))

def load():
    games = {g: [] for g in POOL}
    with open(DATA) as f:
        for row in csv.DictReader(f):
            games[row["Game"]].append([int(row[f"N{i}"]) for i in range(1, 7)])
    return {g: np.array(v) for g, v in games.items()}

def ap3_rows(sorted_rows, tri):
    a = sorted_rows[:, tri[:, 0]]; b = sorted_rows[:, tri[:, 1]]; c = sorted_rows[:, tri[:, 2]]
    return (a + c == 2 * b).sum(axis=1)

def c1_stat(draws):
    return int(ap3_rows(np.sort(draws, axis=1), TRI6).sum())

def hot_set(window, P):
    cnt = np.bincount(window.ravel() - 1, minlength=P)
    order = np.lexsort((np.arange(P), -cnt))      # deterministic tie-break
    return np.sort(order[:HOTK] + 1)

def c2_stat(draws, P):
    vals = []
    for s in range(0, len(draws) - WIN + 1, STEP):
        hs = hot_set(draws[s:s + WIN], P)
        vals.append(int(ap3_rows(hs[None, :], TRI10)[0]))
    return float(np.mean(vals))

def two_sided(null, obs):
    lo = (np.sum(null <= obs) + 1) / (len(null) + 1)
    hi = (np.sum(null >= obs) + 1) / (len(null) + 1)
    return min(1.0, 2 * min(lo, hi))

def analyze(name, draws, rng, label=""):
    T, P = len(draws), POOL[name]
    o1, o2 = c1_stat(draws), c2_stat(draws, P)
    n1 = np.empty(K); n2 = np.empty(K)
    for j in range(K):
        m = rng.random((T, P)).argsort(axis=1)[:, :6] + 1
        n1[j] = c1_stat(m); n2[j] = c2_stat(m, P)
    p1, p2 = two_sided(n1, o1), two_sided(n2, o2)
    print(f"{label}{name:18s} C1={o1:4d} null[{n1.mean():6.1f}±{n1.std():4.1f}] p={p1:.4f} | "
          f"C2={o2:4.2f} null[{n2.mean():4.2f}±{n2.std():4.2f}] p={p2:.4f}")
    return p1, p2, n2.mean()

def main():
    rng = np.random.default_rng(SEED)
    games = load()
    print(f"INSTRUMENT C — Szemerédi AP. K={K}, SEED={SEED}, win={WIN}/step={STEP}/hot={HOTK}\n")
    print("— Ramsey-trap baseline: E[AP3 in random 10-subset of {1..P}] —")
    for g, P in POOL.items():
        sets = rng.random((4000, P)).argsort(axis=1)[:, :HOTK] + 1
        base = ap3_rows(np.sort(sets, axis=1), TRI10).mean()
        print(f"  P={P}: {base:.2f} three-term APs forced by density alone")
    print("\n— Null-trial admission (synthetic H0 year; must be silent at p>0.0025) —")
    ok = True
    for g, d in games.items():
        synth = rng.random((len(d), POOL[g])).argsort(axis=1)[:, :6] + 1
        p1, p2, _ = analyze(g, synth, rng, label="[H0] ")
        ok &= p1 > 0.0025 and p2 > 0.0025
    print(f"Admission: {'PASS' if ok else 'FAIL — instrument rejected'}\n")
    if not ok:
        return
    print("— Real data —")
    fired = []
    for g, d in games.items():
        p1, p2, _ = analyze(g, d, rng)
        if p1 < 0.0025: fired.append((g, "C1", p1))
        if p2 < 0.0025: fired.append((g, "C2", p2))
    print("\nVERDICT C: " + (f"fired: {fired} — check against registration."
          if fired else "AP abundance exactly at the theorem-forced rate in all games; "
          "any 'hot numbers form a progression' claim is the Ramsey trap."))

if __name__ == "__main__":
    main()
