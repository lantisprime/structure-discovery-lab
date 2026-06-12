#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Overlooked power-law family sweep — five scaling laws not previously tested.

P1  ZIPF: frequency vs rank, f(r) ~ r^-s. Zipfian systems (language, cities): s~1.
    i.i.d. uniform: s ~ 0 (flat ranks, slope from sampling noise only). MC-calibrated.
P2  TAYLOR'S LAW: per-number windowed counts, Var ~ Mean^b across numbers.
    b=2 clustered/multiplicative, b=1 Poisson-like, binomial i.i.d.: b~1 with
    Var = Mean*(1-6/P). MC-calibrated slope.
P3  FIRST-DIGIT LAW: drawn numbers' leading digits vs (a) Benford log10(1+1/d) and
    (b) the EXACT uniform-on-1..P law. Chi-square distance to each; the data should
    reject Benford and match the exact law.
P4  LEVY FLIGHTS: step lengths |mean_t+1 - mean_t|; Levy: power-law tail (alpha<2,
    infinite variance); i.i.d.: ~Gaussian-difference tail. CSN+Vuong vs exponential.
P5  COUPON COLLECTOR: draws to observe all P numbers; exact-ish expectation
    E = (P/6)*H_P approx; observed vs MC null distribution.
"""
import csv, math, random
from collections import defaultdict, Counter
import numpy as np
random.seed(21); np.random.seed(21)
NSIM = 600
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
rows = defaultdict(list)
for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
    if r and r[0] in POOLS: rows[r[0]].append((r[1], [int(x) for x in r[2:8]]))
draws = {g: [d for _, d in sorted(v)] for g, v in rows.items()}

def zipf_slope(ds, P):
    c = Counter(n for d in ds for n in d)
    f = sorted((c.get(i, 0) for i in range(1, P+1)), reverse=True)
    x = np.log(np.arange(1, P+1)); y = np.log(np.array(f) + 0.5)
    return -np.polyfit(x, y, 1)[0]

def taylor_b(ds, P, W=26):
    nb = len(ds)//W
    counts = np.zeros((P, nb))
    for w in range(nb):
        c = Counter(n for d in ds[w*W:(w+1)*W] for n in d)
        for i in range(1, P+1): counts[i-1, w] = c.get(i, 0)
    M, V = counts.mean(1), counts.var(1)
    ok = M > 0
    return np.polyfit(np.log(M[ok]), np.log(V[ok] + 1e-9), 1)[0]

print("P1 ZIPF rank-frequency slope (Zipfian s~1; i.i.d. s~0+noise)")
for g, P in POOLS.items():
    obs = zipf_slope(draws[g], P)
    null = [zipf_slope([random.sample(range(1,P+1),6) for _ in range(len(draws[g]))], P) for _ in range(NSIM)]
    mu = np.mean(null); p = np.mean([abs(v-mu) >= abs(obs-mu) for v in null])
    print(f"  {g:18s} s={obs:.3f}  null={mu:.3f}  p={p:.3f}")

print("\nP2 TAYLOR'S LAW exponent b (clustered b~2; Poisson b~1; i.i.d.-binomial ~1)")
for g, P in POOLS.items():
    obs = taylor_b(draws[g], P)
    null = [taylor_b([random.sample(range(1,P+1),6) for _ in range(len(draws[g]))], P) for _ in range(NSIM)]
    mu = np.mean(null); p = np.mean([abs(v-mu) >= abs(obs-mu) for v in null])
    print(f"  {g:18s} b={obs:+.3f}  null={mu:+.3f}  p={p:.3f}")

print("\nP3 FIRST-DIGIT LAW (pooled drawn numbers): chi2 distance to Benford vs exact uniform law")
digits = Counter(int(str(n)[0]) for g in POOLS for d in draws[g] for n in d)
N = sum(digits.values())
benford = {d: math.log10(1+1/d) for d in range(1,10)}
exact = Counter()
for g, P in POOLS.items():
    cnt = 6*len(draws[g])
    perP = Counter(int(str(n)[0]) for n in range(1, P+1))
    for d, k in perP.items(): exact[d] += cnt * k / P
chi_b = sum((digits[d] - N*benford[d])**2/(N*benford[d]) for d in range(1,10))
chi_u = sum((digits[d] - exact[d])**2/exact[d] for d in range(1,10))
print(f"  chi2 vs Benford = {chi_b:8.1f}  (df=8, decisively rejected)" if chi_b > 26 else f"  chi2 vs Benford = {chi_b:.1f}")
print(f"  chi2 vs exact uniform-derived law = {chi_u:8.1f}  ({'consistent' if chi_u < 15.5 else 'rejected'})")

print("\nP4 LEVY-FLIGHT test on step lengths |Δmean| (CSN alpha + Vuong vs exponential)")
steps = []
for g in POOLS:
    x = [sum(d)/6 for d in draws[g]]
    steps += [abs(b-a) for a, b in zip(x, x[1:]) if abs(b-a) > 0]
xs = np.array(steps); xmin = np.quantile(xs, 0.5)
tail = xs[xs >= xmin]
alpha = 1 + len(tail)/np.sum(np.log(tail/xmin))
lp = np.sum(np.log((alpha-1)/xmin) - alpha*np.log(tail/xmin))
lam = 1/np.mean(tail - xmin)
le = np.sum(np.log(lam) - lam*(tail - xmin))
pts = (np.log((alpha-1)/xmin) - alpha*np.log(tail/xmin)) - (np.log(lam) - lam*(tail-xmin))
V = math.sqrt(len(tail))*pts.mean()/pts.std()
print(f"  n_tail={len(tail)}, alpha-hat={alpha:.2f} (Levy needs alpha<3 AND PL win); Vuong z={V:+.2f}"
      f" -> {'POWER LAW' if V>2 else 'exponential-family (no Levy flights)'}")

print("\nP5 COUPON COLLECTOR: draws to see all P numbers (observed vs MC null)")
for g, P in POOLS.items():
    seen = set(); obs_t = None
    for t, d in enumerate(draws[g], 1):
        seen |= set(d)
        if len(seen) == P: obs_t = t; break
    null = []
    for _ in range(NSIM):
        s = set(); t = 0
        while len(s) < P:
            t += 1; s |= set(random.sample(range(1,P+1),6))
        null.append(t)
    null.sort(); lo, hi = null[int(0.025*NSIM)], null[int(0.975*NSIM)]
    print(f"  {g:18s} observed={obs_t}  null median={null[NSIM//2]}  95% CI [{lo},{hi}]"
          f"  {'OK' if obs_t and lo<=obs_t<=hi else 'outside'}")
