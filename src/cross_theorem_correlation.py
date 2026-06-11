#!/usr/bin/env python3
"""Cross-theorem correlation: structure invisible to any single instrument.

Idea: each prior analysis assigns every ball a per-ball signal from a different
mathematical domain. Under H0 (i.i.d. uniform), these signals are mutually
uninformative noise. A latent physical bias couples them: e.g. a heavy ball is
simultaneously (a) over-frequent, (b) sticky, (c) spectrally energetic,
(d) loaded on the leading RMT eigenvector, (e) short-gapped. Single-axis tests
can all be sub-threshold while the CROSS-AXIS correlation is large.

Per-ball features (per game):
  F1 frequency z-score                 (chi-square family / LLN)
  F2 stickiness delta_i = P(in|in)-P(in|out)   (Markov chain)
  F3 presence-series spectral peak     (Wiener-Khinchin)
  F4 |loading| on leading eigenvector  (random matrix theory)
  F5 recurrence-gap variance z         (renewal theory)

Statistic: max |Pearson r| over the 10 feature pairs, per game.
Calibration: full Monte Carlo of the constrained null ensemble (the features
share raw data, so their null correlations are NOT zero — MC absorbs that).
Family: 5 games, threshold p < 0.01.
"""
import csv, math, random
import numpy as np

random.seed(7); np.random.seed(7)
NSIM = 400
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
NAMES = ["F1 freq", "F2 stick", "F3 spec", "F4 RMT", "F5 gapvar"]

def presence(draws, P):
    X = np.zeros((len(draws), P))
    for t, d in enumerate(draws):
        for n in d: X[t, n - 1] = 1
    return X

def features(X):
    T, P = X.shape
    f1 = (X.sum(0) - T * 6 / P) / math.sqrt(T * 6 / P)
    prev, nxt = X[:-1], X[1:]
    in_tot = prev.sum(0); out_tot = (1 - prev).sum(0)
    f2 = (prev * nxt).sum(0) / np.maximum(in_tot, 1) - ((1 - prev) * nxt).sum(0) / np.maximum(out_tot, 1)
    Z = X - X.mean(0)
    spec = np.abs(np.fft.rfft(Z, axis=0)[1:T // 2]) ** 2
    f3 = spec.max(0) / np.maximum(spec.sum(0), 1e-12)
    C = np.corrcoef(Z.T + 1e-12 * np.random.randn(P, T))
    w = np.linalg.eigh(C)[1][:, -1]
    f4 = np.abs(w)
    f5 = np.zeros(P)
    for i in range(P):
        idx = np.flatnonzero(X[:, i])
        gaps = np.diff(idx)
        f5[i] = gaps.var() if len(gaps) > 2 else 0.0
    return np.vstack([f1, f2, f3, f4, f5])

def maxcorr(F):
    R = np.corrcoef(F)
    iu = np.triu_indices(len(F), 1)
    k = np.argmax(np.abs(R[iu]))
    return abs(R[iu][k]), (iu[0][k], iu[1][k]), R

def load():
    out = {g: [] for g in POOLS}
    for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], [int(x) for x in r[2:8]]))
    return {g: [s for _, s in sorted(v)] for g, v in out.items()}

if __name__ == "__main__":
    data = load()
    print(f"CROSS-THEOREM CORRELATION DETECTOR — MC calibrated, NSIM={NSIM}, threshold p<0.01\n")
    print(f"{'game':18s}{'max|r| obs':>11s}{'pair':>22s}{'null med':>9s}{'MC p':>7s}")
    for g, P in POOLS.items():
        draws = data[g]; T = len(draws)
        obs, (a, b), R = maxcorr(features(presence(draws, P)))
        null = []
        for _ in range(NSIM):
            sim = [random.sample(range(1, P + 1), 6) for _ in range(T)]
            null.append(maxcorr(features(presence(sim, P)))[0])
        null.sort()
        p = sum(1 for v in null if v >= obs) / NSIM
        print(f"{g:18s}{obs:11.3f}{NAMES[a]+' x '+NAMES[b]:>22s}{null[NSIM//2]:9.3f}{p:7.3f}")
        if p < 0.01:
            print("   full correlation matrix:")
            for nm, row in zip(NAMES, R):
                print("   " + nm + " " + "  ".join(f"{v:+.2f}" for v in row))
    print("\nReading: 'max|r| obs' is the strongest coupling between two theorem-domains'")
    print("per-ball signals; MC p compares it to the same statistic on synthetic years")
    print("(null correlations are nonzero by construction - features share raw data).")
