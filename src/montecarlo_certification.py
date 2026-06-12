#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Monte Carlo ensemble certification.

Method (theorems: Law of Large Numbers -> MC estimates converge; CLT -> error
decays as 1/sqrt(K); Glivenko-Cantelli -> empirical null CDFs converge
uniformly): simulate K synthetic "years" from the ideal model (i.i.d. uniform
6-without-replacement), compute a battery of 10 diverse statistics on the real
year and on every synthetic year, and report the real year's percentile rank
within the ensemble for each statistic.

Decision logic: if the real data comes from the model, its percentile ranks
must look like draws from Uniform(0,1) — no pile-up near 0 or 1. Extreme ranks
(<0.005 or >0.995) flag structure; an overall pile-up flags model misfit even
without any single extreme.
"""
import csv, math, random
from collections import Counter

random.seed(2027)
K = 1500
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load():
    out = {g: [] for g in POOLS}
    for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], sorted(int(x) for x in r[2:8])))
    return {g: [s for _, s in sorted(v)] for g, v in out.items()}

def is_prime(n): return n > 1 and all(n % i for i in range(2, int(n**0.5) + 1))

def battery(seq, P):
    nd = len(seq)
    c = Counter(n for d in seq for n in d)
    exp = nd * 6 / P
    sums = [sum(d) for d in seq]
    msum = sum(sums) / nd
    # longest absence gap over all numbers
    last = {i: -1 for i in range(1, P + 1)}; gap = {i: 0 for i in range(1, P + 1)}
    for t, d in enumerate(seq):
        for i in d:
            gap[i] = max(gap[i], t - last[i]); last[i] = t
    for i in range(1, P + 1): gap[i] = max(gap[i], nd - last[i])
    return {
        "chi2 frequency":      sum((c.get(i, 0) - exp) ** 2 for i in range(1, P+1)) / exp,
        "mean overlap t,t+1":  sum(len(set(a) & set(b)) for a, b in zip(seq, seq[1:])) / (nd - 1),
        "total primes":        sum(is_prime(n) for d in seq for n in d),
        "draws w/ consecutive":sum(any(b - a == 1 for a, b in zip(d, d[1:])) for d in seq),
        "max number freq":     max(c.values()),
        "min number freq":     min(c.get(i, 0) for i in range(1, P + 1)),
        "mean draw sum":       msum,
        "var of draw sums":    sum((s - msum) ** 2 for s in sums) / nd,
        "mean spread max-min": sum(d[-1] - d[0] for d in seq) / nd,
        "max recurrence interval": max(gap.values()),  # interval between hits incl. boundaries
    }

if __name__ == "__main__":
    data = load()
    print(f"MONTE CARLO ENSEMBLE CERTIFICATION — K={K} synthetic years per game\n")
    ranks = []
    for g, P in POOLS.items():
        nd = len(data[g])
        obs = battery(data[g], P)
        sims = [battery([sorted(random.sample(range(1, P + 1), 6)) for _ in range(nd)], P)
                for _ in range(K)]
        print(f"--- {g} ---")
        for k, v in obs.items():
            null = sorted(s[k] for s in sims)
            r = (sum(1 for x in null if x < v) + 0.5 * sum(1 for x in null if x == v)) / K
            ranks.append(r)
            flag = "  <-- extreme" if r < 0.005 or r > 0.995 else ""
            print(f"  {k:22s} obs={v:9.3f}  null median={null[K//2]:9.3f}  rank={r:.3f}{flag}")
    # meta-test: ranks ~ U(0,1)? (statistics are correlated, so KS is indicative)
    ranks.sort(); n = len(ranks)
    D = max(max((i + 1) / n - r, r - i / n) for i, r in enumerate(ranks))
    ks_p = 2 * math.exp(-2 * n * D * D)  # asymptotic, indicative only
    print(f"\nMeta-test: {n} percentile ranks vs Uniform(0,1): KS D={D:.3f}, "
          f"indicative p~{min(1, ks_p):.2f}")
    print(f"Extreme ranks (<0.005 or >0.995): {sum(1 for r in ranks if r < 0.005 or r > 0.995)}"
          f" of {n} (expect ~{n * 0.01:.1f} by chance)")
