#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Independent Markov-chain bias detection for PCSO lotto draws.

Tests for MEMORY in the draw sequence (i.i.d. uniform => memoryless).
Four pre-specified tests per game, T1 and T2 are monotone-equivalent statistics (identical p-values), so the
effective family is m = 3 x 5 games = 15; Bonferroni threshold p < 0.0033. Runs on data_draws_1yr.csv.

  T1  Consecutive-draw overlap: E[|D_t ∩ D_{t-1}|] = 36/P under i.i.d.
      (a sticky/repeating machine inflates this; "due-number" anti-bias deflates it)
  T2  Per-number 2-state presence chain: P(in|in) vs P(in|out), pooled.
      Stickiness delta = P(1->1) - P(0->1); 0 under i.i.d.
  T3  3-state chain on draw-mean terciles (Low/Mid/High): likelihood-ratio
      G-test of order-1 Markov vs order-0 (memoryless), MC-calibrated.
  T4  Second-largest eigenvalue modulus |lambda_2| of the tercile transition
      matrix: measures mixing time; ~0 under i.i.d., large => persistent regimes.

All p-values by Monte Carlo (draws simulated as 6-without-replacement), so no
asymptotic assumptions. Seeded for reproducibility.
"""
import csv, math, random
from collections import Counter

random.seed(2026)
NSIM = 4000
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load(path="datasets/pcso-lotto/data_draws_1yr.csv"):
    out = {g: [] for g in POOLS}
    for r in csv.reader(open(path)):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], frozenset(int(x) for x in r[2:8])))
    for g in out:
        out[g] = [s for _, s in sorted(out[g])]
    return out

def overlap_stat(seq):
    return sum(len(a & b) for a, b in zip(seq, seq[1:])) / (len(seq) - 1)

def stickiness(seq, P):
    in_in = in_total = out_in = out_total = 0
    for a, b in zip(seq, seq[1:]):
        for i in range(1, P + 1):
            if i in a:
                in_total += 1; in_in += i in b
            else:
                out_total += 1; out_in += i in b
    return in_in / in_total - out_in / out_total

def terciles(seq, P):
    means = [sum(s) / 6 for s in seq]
    lo, hi = sorted(means)[len(means)//3], sorted(means)[2*len(means)//3]
    return [0 if m < lo else (2 if m > hi else 1) for m in means]

def g_stat(states):
    n = len(states) - 1
    t = Counter(zip(states, states[1:]))
    row = Counter(states[:-1]); col = Counter(states[1:])
    g = 0.0
    for (a, b), o in t.items():
        e = row[a] * col[b] / n
        if o and e: g += 2 * o * math.log(o / e)
    return g

def lambda2(states, k=3):
    import numpy as np
    T = np.zeros((k, k))
    for a, b in zip(states, states[1:]): T[a, b] += 1
    T = T / T.sum(axis=1, keepdims=True)
    ev = sorted(abs(np.linalg.eigvals(T)), reverse=True)
    return ev[1]

def simulate(nd, P):
    return [frozenset(random.sample(range(1, P + 1), 6)) for _ in range(nd)]

def mc_p(obs, null, two_sided=True):
    if two_sided:
        mu = sum(null) / len(null)
        return sum(1 for v in null if abs(v - mu) >= abs(obs - mu)) / len(null)
    return sum(1 for v in null if v >= obs) / len(null)

if __name__ == "__main__":
    data = load()
    m = 15  # T1/T2 count once: monotone-equivalent statistics
    print(f"Markov-chain bias detection | {sum(len(v) for v in data.values())} draws | "
          f"MC sims={NSIM} | Bonferroni threshold p<{0.05/m:.4f} (m={m})\n")
    print(f"{'game':18s}{'test':34s}{'observed':>10s}{'null mean':>10s}{'MC p':>8s}")
    worst = []
    for g, P in POOLS.items():
        seq = data[g]; nd = len(seq)
        sims = [simulate(nd, P) for _ in range(NSIM)]
        tests = [
            ("T1 overlap (exp %.3f)" % (36/P), overlap_stat(seq), [overlap_stat(s) for s in sims], True),
            ("T2 stickiness P(1->1)-P(0->1)", stickiness(seq, P), [stickiness(s, P) for s in sims], True),
            ("T3 tercile order-1 G-test", g_stat(terciles(seq, P)), [g_stat(terciles(s, P)) for s in sims], False),
            ("T4 tercile |lambda_2|", lambda2(terciles(seq, P)), [lambda2(terciles(s, P)) for s in sims], False),
        ]
        for name, obs, null, ts in tests:
            p = mc_p(obs, null, ts)
            worst.append((p, g, name))
            print(f"{g:18s}{name:34s}{obs:10.4f}{sum(null)/len(null):10.4f}{p:8.3f}")
    worst.sort()
    print(f"\nSmallest p: {worst[0][0]:.3f} ({worst[0][1]}, {worst[0][2]})")
    print(f"Verdict: {'BIAS FLAG - replicate out-of-sample' if worst[0][0] < 0.05/m else 'no memory detected: consistent with memoryless i.i.d. draws'}")
