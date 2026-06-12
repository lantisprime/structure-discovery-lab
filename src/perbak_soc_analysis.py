#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Per Bak / self-organized criticality (SOC) signatures in the draw sequence.

SOC systems (Bak-Tang-Wiesenfeld sandpile, earthquakes, granular piles) emit:
  S1  1/f noise: periodogram I(f) ~ f^-alpha with alpha ~ 1   (white noise: alpha=0)
  S2  power-law avalanches: P(size s) ~ s^-tau, heavy tail    (i.i.d.: geometric tail)
  S3  long-range memory: Hurst exponent H > 0.5 (R/S analysis) (i.i.d.: H ~ 0.5)

Series under test: z-scored draw means per game. "Avalanche" = run of consecutive
above-median draws (its size is geometric under i.i.d.). All statistics calibrated
against the exact constrained null (6-without-replacement) by Monte Carlo.
Exploratory family m = 3 x 5 = 15; threshold p < 0.0033.
"""
import csv, math, random
import numpy as np
random.seed(4); np.random.seed(4)
NSIM = 800
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load():
    out = {g: [] for g in POOLS}
    for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], [int(x) for x in r[2:8]]))
    return {g: np.array([sum(d)/6 for _, d in sorted(v)]) for g, v in out.items()}

def spectral_slope(x):
    x = (x - x.mean()) / x.std()
    I = np.abs(np.fft.rfft(x)[1:len(x)//2])**2
    f = np.arange(1, len(I)+1)
    A = np.vstack([np.log(f), np.ones(len(f))]).T
    return -np.linalg.lstsq(A, np.log(I + 1e-12), rcond=None)[0][0]  # alpha

def max_avalanche(x):
    med = np.median(x); best = run = 0
    for v in x:
        run = run + 1 if v > med else 0
        best = max(best, run)
    return best

def hurst(x):
    x = (x - x.mean()) / x.std()
    ns, rs = [], []
    for w in (8, 16, 32, 64):
        vals = []
        for i in range(0, len(x) - w + 1, w):
            seg = x[i:i+w]; dev = np.cumsum(seg - seg.mean())
            R = dev.max() - dev.min(); S = seg.std()
            if S > 0: vals.append(R / S)
        ns.append(math.log(w)); rs.append(math.log(np.mean(vals)))
    A = np.vstack([ns, np.ones(4)]).T
    return np.linalg.lstsq(A, rs, rcond=None)[0][0]  # H

if __name__ == "__main__":
    data = load()
    print(f"PER BAK / SOC SIGNATURE SCAN — NSIM={NSIM}, family m=15, threshold p<0.0033")
    print("SOC expects: alpha~1, heavy avalanche tail, H>0.5. i.i.d. expects: alpha~0, geometric, H~0.5\n")
    print(f"{'game':18s}{'alpha (1/f)':>12s}{'p':>7s}{'max aval.':>10s}{'p':>7s}{'Hurst H':>9s}{'p':>7s}")
    for g, P in POOLS.items():
        x = data[g]; nd = len(x)
        def sim():
            return np.array([sum(random.sample(range(1, P+1), 6))/6 for _ in range(nd)])
        sims = [sim() for _ in range(NSIM)]
        rows = []
        for fn, obs_v in ((spectral_slope, spectral_slope(x)),
                          (max_avalanche, max_avalanche(x)),
                          (hurst, hurst(x))):
            null = [fn(s) for s in sims]
            mu = sum(null)/len(null)
            p = sum(1 for v in null if abs(v-mu) >= abs(obs_v-mu))/NSIM  # two-sided
            rows.append((obs_v, p))
        print(f"{g:18s}{rows[0][0]:12.3f}{rows[0][1]:7.3f}{rows[1][0]:10d}{rows[1][1]:7.3f}"
              f"{rows[2][0]:9.3f}{rows[2][1]:7.3f}")
