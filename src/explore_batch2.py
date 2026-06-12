#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Exploration batch 2 — five untouched structural angles, all MC-calibrated.

E1  DRAW-ORDER POSITION EFFECTS: N1..N6 is the physical exit order from the
    chamber. Under H0 the order is a uniform random permutation, so the mean
    ball value must not depend on exit position. Statistic: variance across
    positions of mean value; null by within-draw order shuffling.
E2  WEEKDAY/SLOT EFFECTS: each game draws on 3 weekdays (possibly different
    machine/crew/warm-up). Statistic: between-weekday variance of mean drawn
    number; null by weekday-label permutation.
E3  PAIR AFFINITY: do specific number PAIRS co-occur beyond chance (magnetic,
    sticky, adjacent-in-tray balls)? Statistic: max pair co-occurrence count;
    null by full i.i.d. simulation (handles look-elsewhere over all pairs).
E4  CROSS-GAME SAME-NIGHT COUPLING: different games draw in the same studio
    minutes apart. Statistic: total shared values across same-night game
    pairs; null by independent simulation.
E5  SCAN STATISTIC (Kulldorff-style): the maximum windowed hot-run of ANY
    number, ANY 30-draw window, ANY game — the formally correct version of
    "is the 6/55 #45 run remarkable?" with the full look-elsewhere correction.
"""
import csv, math, random
from collections import Counter, defaultdict

random.seed(99)
NSIM = 1000
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

rows = []
for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
    if r and r[0] in POOLS:
        rows.append((r[0], r[1], [int(x) for x in r[2:8]]))
rows.sort(key=lambda x: (x[0], x[1]))
bygame = defaultdict(list)
for g, d, nums in rows: bygame[g].append((d, nums))

def mcp(obs, null): return sum(1 for v in null if v >= obs) / len(null)

print(f"EXPLORATION BATCH 2 — {len(rows)} draws, NSIM={NSIM} (exploratory: flags go to the registry)\n")

# E1: exit-position effect
print("E1 exit-position effect (variance of per-position mean value)")
for g, P in POOLS.items():
    seqs = [nums for _, nums in bygame[g]]
    def posvar(ds):
        m = [sum(d[k] for d in ds) / len(ds) for k in range(6)]
        mu = sum(m) / 6
        return sum((x - mu) ** 2 for x in m)
    obs = posvar(seqs)
    null = []
    for _ in range(NSIM):
        sh = [random.sample(d, 6) for d in seqs]
        null.append(posvar(sh))
    print(f"  {g:18s} stat={obs:7.2f}  p={mcp(obs, null):.3f}")

# E2: weekday effect on mean drawn number
from datetime import date
print("E2 weekday effect (between-slot variance of mean drawn number)")
for g, P in POOLS.items():
    items = [(date.fromisoformat(d).weekday(), sum(n) / 6) for d, n in bygame[g]]
    def slotvar(it):
        groups = defaultdict(list)
        for w, m in it: groups[w].append(m)
        gm = [sum(v) / len(v) for v in groups.values()]
        mu = sum(gm) / len(gm)
        return sum((x - mu) ** 2 for x in gm)
    obs = slotvar(items)
    labels = [w for w, _ in items]; vals = [m for _, m in items]
    null = []
    for _ in range(NSIM):
        random.shuffle(vals)
        null.append(slotvar(list(zip(labels, vals))))
    print(f"  {g:18s} stat={obs:7.3f}  p={mcp(obs, null):.3f}")

# E3: pair affinity
print("E3 pair affinity (max co-occurrence count over all pairs)")
for g, P in POOLS.items():
    seqs = [nums for _, nums in bygame[g]]; nd = len(seqs)
    def maxpair(ds):
        pc = Counter()
        for d in ds:
            s = sorted(d)
            for i in range(6):
                for j in range(i + 1, 6): pc[(s[i], s[j])] += 1
        return max(pc.values())
    obs = maxpair(seqs)
    null = [maxpair([random.sample(range(1, P + 1), 6) for _ in range(nd)]) for _ in range(NSIM)]
    print(f"  {g:18s} max pair count={obs}  null median={sorted(null)[NSIM//2]}  p={mcp(obs, null):.3f}")

# E4: cross-game same-night coupling
print("E4 cross-game same-night value sharing")
bydate = defaultdict(list)
for g, d, nums in rows: bydate[d].append((g, set(nums)))
def share(bd):
    tot = 0
    for d, lst in bd.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)): tot += len(lst[i][1] & lst[j][1])
    return tot
obs = share(bydate)
null = []
for _ in range(NSIM):
    sim = {d: [(g, set(random.sample(range(1, POOLS[g] + 1), 6))) for g, _ in lst]
           for d, lst in bydate.items()}
    null.append(share(sim))
print(f"  total shared values={obs}  null median={sorted(null)[NSIM//2]}  p={mcp(obs, null):.3f}")

# E5: scan statistic — hottest (number, window) anywhere
print("E5 scan statistic: hottest 30-draw run of any number, any game (look-elsewhere corrected)")
W = 30
def scan(seqs, P):
    best = 0.0
    pres = [[0] * (len(seqs) + 1) for _ in range(P + 1)]
    for t, d in enumerate(seqs):
        for i in range(1, P + 1):
            pres[i][t + 1] = pres[i][t] + (i in d)
    e = W * 6 / P; sd = math.sqrt(e * (1 - 6 / P))
    for i in range(1, P + 1):
        for t in range(len(seqs) - W + 1):
            z = (pres[i][t + W] - pres[i][t] - e) / sd
            best = max(best, z)
    return best
obs_all, null_all = 0.0, [0.0] * NSIM
for g, P in POOLS.items():
    seqs = [set(nums) for _, nums in bygame[g]]
    obs_all = max(obs_all, scan(seqs, P))
    for k in range(NSIM):
        sim = [set(random.sample(range(1, P + 1), 6)) for _ in range(len(seqs))]
        null_all[k] = max(null_all[k], scan(sim, P))
p = sum(1 for v in null_all if v >= obs_all) / NSIM
print(f"  max windowed z = {obs_all:.2f}  null median = {sorted(null_all)[NSIM//2]:.2f}  global p = {p:.3f}")
