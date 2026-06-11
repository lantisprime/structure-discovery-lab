#!/usr/bin/env python3
"""Implements the three gaps from the independent LLM review (Jun 11, 2026):
R1  Row-level source-audit table  -> data_draws_1yr_audited.csv
R2  Payout-relevant walk-forward backtest (0-6 match distribution, prize-weighted)
R3  Rolling-window bias persistence (4 windows, cross-window correlation)
"""
import csv, math, random
from collections import Counter, defaultdict
random.seed(11)
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

rows = []
for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
    if r and r[0] in POOLS: rows.append((r[0], r[1], [int(x) for x in r[2:8]]))
rows.sort(key=lambda x: (x[0], x[1]))

# ---------- R1: row-level audit ----------
OFFICIAL = {("Ultra Lotto 6/58","2026-06-07"),("Ultra Lotto 6/58","2026-06-09"),
            ("Super Lotto 6/49","2026-06-07"),("Super Lotto 6/49","2026-06-09"),
            ("Lotto 6/42","2026-06-09"),("Grand Lotto 6/55","2026-06-08"),
            ("Grand Lotto 6/55","2026-06-10"),("Mega Lotto 6/45","2026-06-08"),
            ("Mega Lotto 6/45","2026-06-10")}
BULK = {"Lotto 6/42":("2026-04-25","2026-06-09"),"Mega Lotto 6/45":("2026-04-22","2026-06-05"),
        "Super Lotto 6/49":("2026-04-23","2026-06-07"),"Grand Lotto 6/55":("2026-04-22","2026-06-06"),
        "Ultra Lotto 6/58":("2026-04-24","2026-06-07")}
SPOT = {("Super Lotto 6/49","2026-03-22"),("Super Lotto 6/49","2026-03-24"),
        ("Grand Lotto 6/55","2025-06-16"),("Grand Lotto 6/55","2025-09-24"),
        ("Super Lotto 6/49","2025-11-11"),("Mega Lotto 6/45","2025-12-24"),
        ("Grand Lotto 6/55","2026-03-09"),("Lotto 6/42","2026-03-05")}
counts = Counter()
with open("datasets/pcso-lotto/data_draws_1yr_audited.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["Game","Date","N1","N2","N3","N4","N5","N6","Source1","Source2","Status"])
    for g, d, nums in rows:
        if (g,d) in OFFICIAL:                          st, s2 = "official_verified", "pcso.gov.ph"
        elif BULK[g][0] <= d <= BULK[g][1]:            st, s2 = "two_source_verified", "pcsodraw.com"
        elif (g,d) in SPOT:                            st, s2 = "two_source_verified(spot)", "pcsodraw/winners"
        else:                                          st, s2 = "single_source_only", ""
        counts[st] += 1
        w.writerow([g, d, *nums, "lottopcso.com", s2, st])
print("R1 audit table -> data_draws_1yr_audited.csv")
for k, v in sorted(counts.items()): print(f"   {k:28s}{v:4d} rows ({v/len(rows):.0%})")

# ---------- R2: payout-relevant backtest ----------
print("\nR2 payout-relevant walk-forward backtest (Markov top-6 model vs hypergeometric baseline)")
PRIZES = {"Lotto 6/42":(20,800,24000),"Mega Lotto 6/45":(30,1000,32000),
          "Super Lotto 6/49":(50,1200,56000),"Grand Lotto 6/55":(60,3000,200000),
          "Ultra Lotto 6/58":(100,4000,280000)}  # 3-,4-,5-match (jackpot excluded)
def fit_predict(seq, P, upto):
    inin=Counter(); intot=Counter(); outin=Counter(); outtot=Counter()
    for a,b in zip(seq[:upto], seq[1:upto]):
        for i in range(1,P+1):
            if i in a: intot[i]+=1; inin[i]+= i in b
            else: outtot[i]+=1; outin[i]+= i in b
    last = seq[upto-1]
    sc = {i: ((inin[i]+2*6/P)/(intot[i]+2) if i in last else (outin[i]+2*6/P)/(outtot[i]+2))
          for i in range(1,P+1)}
    return sorted(sc, key=sc.get, reverse=True)[:6]
def hyper_pmf(k, P):
    return math.comb(6,k)*math.comb(P-6,6-k)/math.comb(P,6)
tot_pay_m = tot_pay_e = 0.0
agg_obs = Counter(); agg_exp = defaultdict(float)
for g, P in POOLS.items():
    seq = [set(n) for _, __, n in [r for r in rows if r[0]==g]]
    seq = [set(n) for gg, d, n in rows if gg == g]
    m3 = 0; n = 0; pay = 0.0
    for t in range(30, len(seq)):
        pred = set(fit_predict(seq, P, t)); k = len(pred & seq[t]); n += 1
        agg_obs[k] += 1
        if k >= 3: m3 += 1; pay += PRIZES[g][min(k,5)-3]
    e3 = n*sum(hyper_pmf(k,P) for k in (3,4,5,6))
    epay = n*sum(hyper_pmf(k,P)*PRIZES[g][min(k,5)-3] for k in (3,4,5))
    for k in range(7): agg_exp[k] += n*hyper_pmf(k,P)
    tot_pay_m += pay; tot_pay_e += epay
    print(f"   {g:18s} 3+ matches: {m3:2d} obs vs {e3:5.2f} exp | payout PHP {pay:7.0f} vs {epay:7.0f} exp")
print("   match-count distribution (all games):",
      {k: f"{agg_obs[k]}/{agg_exp[k]:.1f}" for k in range(5)})
print(f"   TOTAL prize-relevant payout: model PHP {tot_pay_m:.0f} vs random expectation PHP {tot_pay_e:.0f}")

# ---------- R3: rolling-window persistence ----------
print("\nR3 rolling-window bias persistence (4 windows; mean cross-window correlation of per-number deviation)")
NSIM = 500
for g, P in POOLS.items():
    seq = [n for gg, d, n in rows if gg == g]
    def crosscorr(s):
        q = len(s)//4; wins = [s[i*q:(i+1)*q] for i in range(4)]
        vecs = []
        for wdr in wins:
            e = len(wdr)*6/P
            c = Counter(x for dd in wdr for x in dd)
            vecs.append([c.get(i,0)-e for i in range(1,P+1)])
        cors = []
        for i in range(4):
            for j in range(i+1,4):
                a, b = vecs[i], vecs[j]
                sa = math.sqrt(sum(x*x for x in a)); sb = math.sqrt(sum(x*x for x in b))
                cors.append(sum(x*y for x,y in zip(a,b))/(sa*sb))
        return sum(cors)/len(cors)
    obs = crosscorr(seq)
    null = [crosscorr([random.sample(range(1,P+1),6) for _ in range(len(seq))]) for _ in range(NSIM)]
    p = sum(1 for v in null if v >= obs)/NSIM
    # the #45 trace for 6/55
    extra = ""
    if g == "Grand Lotto 6/55":
        q = len(seq)//4
        ratios = [sum(1 for dd in seq[i*q:(i+1)*q] if 45 in dd)/(q*6/P) for i in range(4)]
        extra = "  | #45 bias-ratio by window: " + " ".join(f"{r:.2f}" for r in ratios)
    print(f"   {g:18s} mean cross-window r={obs:+.3f}  p={p:.3f}{extra}")
