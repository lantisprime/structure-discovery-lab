#!/usr/bin/env python3
"""Pure Markov-chain model of PCSO draws (no hypothesis testing).

Fits the chain, reports its parameters, makes next-draw predictions, and
backtests them through the year. Whatever the chain learns, we use as-is.

Model: for each ball i, a 2-state presence chain with per-ball estimated
  a_i = P(i in D_t | i in D_{t-1})   (repeat prob)
  b_i = P(i in D_t | i not in D_{t-1})
Next-draw score of ball i = a_i if i was in the last draw else b_i.
Prediction = top-6 scores. Also: tercile 3-state chain (transition matrix,
stationary dist, relaxation time) and top successor pairs P(j at t | i at t-1).
"""
import csv, math
from collections import Counter, defaultdict

POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load():
    out = {g: [] for g in POOLS}
    for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], frozenset(int(x) for x in r[2:8])))
    return {g: [s for _, s in sorted(v)] for g, v in out.items()}

def fit(seq, P, upto=None):
    """Per-ball transition estimates, smoothed toward the memoryless rate 6/P."""
    s = seq[:upto] if upto else seq
    inin = Counter(); intot = Counter(); outin = Counter(); outtot = Counter()
    for a, b in zip(s, s[1:]):
        for i in range(1, P + 1):
            if i in a: intot[i] += 1; inin[i] += i in b
            else:      outtot[i] += 1; outin[i] += i in b
    # smoothing centered at the memoryless rate 6/P (2 pseudo-observations),
    # NOT at 0.5: (x+1)/(n+2) biased P(repeat) upward with small n (code review fix)
    a = {i: (inin[i] + 2 * 6 / P) / (intot[i] + 2) for i in range(1, P + 1)}
    bb = {i: (outin[i] + 2 * 6 / P) / (outtot[i] + 2) for i in range(1, P + 1)}
    return a, bb

def predict(seq, P, upto):
    a, b = fit(seq, P, upto)
    last = seq[upto - 1]
    score = {i: (a[i] if i in last else b[i]) for i in range(1, P + 1)}
    return sorted(score, key=score.get, reverse=True)[:6]

if __name__ == "__main__":
    data = load()
    print("=" * 78)
    print("PURE MARKOV CHAIN MODEL — fitted on 776 draws (Jun 2025 - Jun 2026)")
    print("=" * 78)
    for g, P in POOLS.items():
        seq = data[g]; nd = len(seq)
        a, b = fit(seq, P)
        am = sum(a.values()) / P; bm = sum(b.values()) / P
        print(f"\n--- {g} ({nd} draws) ---")
        print(f"mean P(repeat)={am:.4f}  mean P(enter)={bm:.4f}  memoryless value={6/P:.4f}")
        # tercile chain
        means = [sum(s) / 6 for s in seq]
        srt = sorted(means); lo, hi = srt[nd//3], srt[2*nd//3]
        st = [0 if m < lo else (2 if m > hi else 1) for m in means]
        T = [[0.0] * 3 for _ in range(3)]
        for x, y in zip(st, st[1:]): T[x][y] += 1
        T = [[c / sum(row) for c in row] for row in T]
        print("tercile transition matrix (rows: from L/M/H):")
        for lab, row in zip("LMH", T):
            print(f"   {lab}: " + "  ".join(f"{v:.3f}" for v in row))
        import numpy as np
        ev = np.linalg.eigvals(np.array(T))
        l2 = sorted(abs(ev), reverse=True)[1]
        print(f"|lambda_2|={l2:.3f} -> relaxation time {1/(1-l2):.2f} draws (1.0 = instant forgetting)")
        # top successor pairs
        pair = Counter(); base = Counter()
        for x, y in zip(seq, seq[1:]):
            for i in x:
                base[i] += 1
                for j in y: pair[(i, j)] += 1
        top = sorted(((c / base[i], i, j, c) for (i, j), c in pair.items() if base[i] >= 12),
                     reverse=True)[:3]
        print("strongest successor links P(j next | i now): " +
              ", ".join(f"{i}->{j} {p:.2f} ({c}x)" for p, i, j, c in top))
        # the model's actual next-draw prediction
        print(f"MODEL PREDICTION for next draw: {sorted(predict(seq, P, nd))}")

    print("\n" + "=" * 78)
    print("BACKTEST: walk-forward, predict top-6 each draw from weeks 5+, count hits")
    print("=" * 78)
    tot_hits = tot_draws = 0
    for g, P in POOLS.items():
        seq = data[g]; hits = n = 0
        for t in range(30, len(seq)):
            hits += len(set(predict(seq, P, t)) & seq[t]); n += 1
        exp = n * 36 / P
        sd = math.sqrt(n * 36 / P * (1 - 6 / P) * (P - 6) / (P - 1))  # approx
        z = (hits - exp) / sd
        tot_hits += hits; tot_draws += n
        print(f"{g:18s} predictions={n:4d}  hits={hits:4d}  random expectation={exp:7.1f}  z={z:+.2f}")
    print(f"\nTOTAL: {tot_hits} hits across {tot_draws} predicted draws "
          f"(uniform guessing expects ~{sum((len(data[g])-30)*36/P for g, P in POOLS.items()):.0f})")
