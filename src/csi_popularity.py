#!/usr/bin/env python3
"""Conscious-selection index (CSI): a decision-layer instrument for jackpot-sharing risk.

Governance: docs/kb/conscious-selection-popularity.md (Part-3 card, INDEX row 28).
This script is the card's Step 4 (null trial) and Step 6 (first run, dual report) in
one deterministic file. It never touches the detection layer: the draw process is
taken as i.i.d. uniform (the lab's standing verdict) and the question asked here is
about PLAYER behaviour — does the drawn combination's popularity proxy predict how
many bets shared the official jackpot?

Reads  datasets/pcso-lotto/data_official_draws_jackpots.csv (pcso.gov.ph, official)
Writes results/csi_popularity_<run_date>.json  (byte-deterministic for a given seed)

Usage: python3 src/csi_popularity.py [--seed 20260906] [--run-date 2026-09-06]
       [--null-trials 500] [--perms 19999] [--verify]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "datasets" / "pcso-lotto" / "data_official_draws_jackpots.csv"
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

# --------------------------------------------------------------------------- the index
# Literature-motivated proxies (weights are declared, not fitted; see the card):
#   birthday numbers <=31 (Cook & Clotfelter 1993; Simon 1998; Papachristou & Karamanis 1998)
#   calendar numbers <=12 and "lucky" digits (Roger & Broihanne 2007: FR most popular 7,12,9,13,11,5;
#   Polin, Ben-Isaac & Aharon 2021: IL most popular 1, 9) and visual/arithmetic patterns
#   (Halpern & Devereaux 1989; PCSO 2022-10-01 6/55 draw 9-18-27-36-45-54 split 433 ways).
LUCKY = frozenset({1, 3, 5, 7, 9, 11, 12, 13})
WEIGHTS = {"birthday": 0.30, "calendar": 0.10, "lucky": 0.10, "ap6": 0.50, "ap5": 0.20,
           "run4": 0.30, "run3": 0.10, "gcd": 0.35, "lastdigit": 0.30, "parity": 0.05}


def csi(ticket, pool):
    """Conscious-selection index in [0, 1]; higher = more likely to be shared with other bettors."""
    s = sorted(int(v) for v in ticket)
    score = 0.0
    b = sum(1 for v in s if v <= 31) / 6
    eb = min(31, pool) / pool
    score += WEIGHTS["birthday"] * max(0.0, (b - eb) / (1 - eb))
    c = sum(1 for v in s if v <= 12) / 6
    ec = 12 / pool
    score += WEIGHTS["calendar"] * max(0.0, (c - ec) / (1 - ec))
    lk = sum(1 for v in s if v in LUCKY) / 6
    el = len(LUCKY) / pool
    score += WEIGHTS["lucky"] * max(0.0, (lk - el) / (1 - el))
    d = [s[i + 1] - s[i] for i in range(5)]
    if len(set(d)) == 1:
        score += WEIGHTS["ap6"]
    elif any(d[i] == d[i + 1] == d[i + 2] == d[i + 3] for i in range(2)):
        score += WEIGHTS["ap5"]
    run = maxrun = 1
    for x in d:
        run = run + 1 if x == 1 else 1
        maxrun = max(maxrun, run)
    if maxrun >= 4:
        score += WEIGHTS["run4"]
    elif maxrun == 3:
        score += WEIGHTS["run3"]
    g = 0
    for v in s:
        g = math.gcd(g, v)
    if g >= 2:
        score += WEIGHTS["gcd"]
    if len({v % 10 for v in s}) == 1:
        score += WEIGHTS["lastdigit"]
    if all(v % 2 == 0 for v in s) or all(v % 2 == 1 for v in s):
        score += WEIGHTS["parity"]
    return min(1.0, score)


# JS parity vectors: the web picker implements the same function; both must agree on these.
PARITY_VECTORS = [
    ((9, 18, 27, 36, 45, 54), 55), ((1, 2, 3, 4, 5, 6), 42), ((3, 7, 11, 13, 21, 27), 45),
    ((32, 38, 39, 40, 41, 43), 49), ((2, 12, 22, 32, 42, 52), 58), ((5, 14, 23, 33, 44, 57), 58),
    ((1, 16, 25, 26, 43, 58), 58), ((10, 20, 30, 40, 50, 55), 55),
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_official():
    by_game = defaultdict(list)
    with open(OFFICIAL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by_game[r["Game"]].append((r["Date"], [int(r[f"N{i}"]) for i in range(1, 7)],
                                       float(r["Jackpot"]), int(r["Winners"])))
    for g in by_game:
        by_game[g].sort()
    return by_game


def rank(a):
    order = sorted(range(len(a)), key=lambda i: a[i])
    r = [0.0] * len(a)
    i = 0
    while i < len(order):   # average ranks for ties
        j = i
        while j + 1 < len(order) and a[order[j + 1]] == a[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0


def within_game_standardize(x, glist):
    """z-score CSI inside each game. Pool size drives both the CSI level (a 6/42 ticket is mostly <=31 by
    construction) and the win rate (1/C(42,6) is 27x 1/C(58,6)); pooling raw CSI across games would
    make winner draws look 'popular' for no behavioural reason (caught by the Step-4 null trial)."""
    by = defaultdict(list)
    for v, g in zip(x, glist):
        by[g].append(v)
    mu = {g: sum(v) / len(v) for g, v in by.items()}
    sd = {g: math.sqrt(sum((a - mu[g]) ** 2 for a in v) / max(len(v) - 1, 1)) or 1.0 for g, v in by.items()}
    return [(v - mu[g]) / sd[g] for v, g in zip(x, glist)]


def within_game_rank(x, glist):
    """rank of CSI inside each game, scaled to (0,1) so every game contributes the same distribution."""
    by = defaultdict(list)
    for i, g in enumerate(glist):
        by[g].append(i)
    out = [0.0] * len(x)
    for g, idx in by.items():
        r = rank([x[i] for i in idx])
        for j, i in enumerate(idx):
            out[i] = (r[j] + 0.5) / len(idx)
    return out


def stats(zx, rx, y):
    """T1 = mean standardized CSI of winner draws minus winner-less draws; T2 = rank correlation of the
    within-game CSI rank with the winning-bet count. Both are exactly 0 in expectation under the null."""
    w = [a for a, b in zip(zx, y) if b > 0]
    nw = [a for a, b in zip(zx, y) if b == 0]
    t1 = (sum(w) / len(w) - sum(nw) / len(nw)) if w and nw else 0.0
    t2 = pearson(rx, rank(y))
    return t1, t2


def shuffle_within(rng, y, groups):
    """permute the winner counts inside each game (stratified permutation)."""
    out = list(y)
    for idx in groups:
        vals = [y[i] for i in idx]
        rng.shuffle(vals)
        for j, i in enumerate(idx):
            out[i] = vals[j]
    return out


def poisson_glm(X, y):
    """winners ~ Poisson(exp(X beta)) by IRLS; X includes game intercepts. Returns beta, se, dispersion."""
    n, p = len(y), len(X[0])
    beta = [0.0] * p
    for _ in range(100):
        mu = [math.exp(sum(b * v for b, v in zip(beta, row))) for row in X]
        A = [[sum(mu[i] * X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
        g = [sum((y[i] - mu[i]) * X[i][a] for i in range(n)) for a in range(p)]
        step = solve(A, g)
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-10:
            break
    mu = [math.exp(sum(b * v for b, v in zip(beta, row))) for row in X]
    A = [[sum(mu[i] * X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    cov = invert(A)
    se = [math.sqrt(max(cov[a][a], 0.0)) for a in range(p)]
    disp = sum((y[i] - mu[i]) ** 2 / mu[i] for i in range(n)) / (n - p)
    return beta, se, disp


def invert(m):
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(a[r][c]))
        if abs(a[piv][c]) < 1e-300:
            raise ZeroDivisionError("singular design matrix")
        a[c], a[piv] = a[piv], a[c]
        f = a[c][c]
        a[c] = [v / f for v in a[c]]
        for r in range(n):
            if r != c and a[r][c] != 0.0:
                fr = a[r][c]
                a[r] = [v - fr * w for v, w in zip(a[r], a[c])]
    return [row[n:] for row in a]


def solve(A, b):
    inv = invert(A)
    return [sum(inv[i][j] * b[j] for j in range(len(b))) for i in range(len(b))]


def poisson_draw(rng, lam):
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--run-date", default="2026-09-06")
    ap.add_argument("--null-trials", type=int, default=500)
    ap.add_argument("--perms", type=int, default=19999)
    ap.add_argument("--power-trials", type=int, default=500)
    ap.add_argument("--verify", action="store_true", help="recompute and byte-compare, write nothing")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    by_game = load_official()
    games = sorted(by_game)
    x, y, z, glist = [], [], [], []
    for g in games:
        for d, nums, J, w in by_game[g]:
            x.append(csi(nums, POOL[g])); y.append(w); z.append(math.log(J)); glist.append(g)
    n = len(x)
    groups = [[i for i in range(n) if glist[i] == g] for g in games]
    gmean_logJ = {g: sum(z[i] for i in idx) / len(idx) for g, idx in zip(games, groups)}
    zc = [z[i] - gmean_logJ[glist[i]] for i in range(n)]      # log jackpot centred within game (sales proxy)
    rate = {g: sum(w for _, _, _, w in by_game[g]) / len(by_game[g]) for g in games}
    zx = within_game_standardize(x, glist)
    rx = within_game_rank(x, glist)

    # ---- Step 4: null trial on simulated H0 data of the real shape (uniform draws, winners independent of CSI)
    null_t1, null_t2, null_chi = [], [], []
    for _ in range(args.null_trials):
        xs, ys = [], []
        chi = 0.0
        for g in games:
            P = POOL[g]
            counts = [0] * (P + 1)
            for _row in by_game[g]:
                t = rng.sample(range(1, P + 1), 6)
                for v in t:
                    counts[v] += 1
                xs.append(csi(t, P)); ys.append(poisson_draw(rng, rate[g]))
            e = len(by_game[g]) * 6 / P
            chi += sum((counts[v] - e) ** 2 / e for v in range(1, P + 1))   # C3: the lab's frequency statistic on the same draws
        t1, t2 = stats(within_game_standardize(xs, glist), within_game_rank(xs, glist), ys)
        null_t1.append(t1); null_t2.append(t2); null_chi.append(chi)
    def summ(v):
        m = sum(v) / len(v); sd = math.sqrt(sum((a - m) ** 2 for a in v) / (len(v) - 1))
        return {"mean": round(m, 5), "sd": round(sd, 5), "min": round(min(v), 5), "max": round(max(v), 5), "distinct": len(set(round(a, 6) for a in v))}
    null_trial = {"trials": args.null_trials, "T1_meandiff": summ(null_t1), "T2_rankcorr": summ(null_t2),
                  "c3_null_correlation_with_chi_square": {"T1": round(pearson(rank(null_t1), rank(null_chi)), 4),
                                                          "T2": round(pearson(rank(null_t2), rank(null_chi)), 4),
                                                          "merge_rule": "|rho| > 0.9 would merge into a hit-count family (results/families.json)"},
                  "non_degenerate": len(set(null_t1)) > args.null_trials // 2 and len(set(null_t2)) > args.null_trials // 2,
                  "location_matches_theory": abs(sum(null_t1) / len(null_t1)) < 3 * (summ(null_t1)["sd"] / math.sqrt(args.null_trials)) and
                                             abs(sum(null_t2) / len(null_t2)) < 3 * (summ(null_t2)["sd"] / math.sqrt(args.null_trials))}

    # ---- Step 6: first run on real data, stratified permutation p (winners shuffled within game; add-one, lattice m=perms)
    obs_t1, obs_t2 = stats(zx, rx, y)
    c1 = c2 = 0
    for _ in range(args.perms):
        yp = shuffle_within(rng, y, groups)
        t1, t2 = stats(zx, rx, yp)
        c1 += abs(t1) >= abs(obs_t1) - 1e-15
        c2 += abs(t2) >= abs(obs_t2) - 1e-15
    p1 = (c1 + 1) / (args.perms + 1); p2 = (c2 + 1) / (args.perms + 1)
    # Poisson GLM with game fixed effects: winners ~ game + z_csi + logJ(centred within game)
    X = [[1.0 if glist[i] == g else 0.0 for g in games] + [zx[i], zc[i]] for i in range(n)]
    beta, se, disp = poisson_glm(X, y)
    b_csi, se_csi, b_j, se_j = beta[-2], se[-2], beta[-1], se[-1]
    # within-game tertiles of CSI, pooled
    tert_idx = {"low": [], "mid": [], "high": []}
    for idx in groups:
        xs_sorted = sorted(x[i] for i in idx)
        q1, q2 = xs_sorted[len(idx) // 3], xs_sorted[2 * len(idx) // 3]
        for i in idx:
            tert_idx["low" if x[i] <= q1 else "mid" if x[i] <= q2 else "high"].append(i)
    def band(idx):
        return {"draws": len(idx), "share_with_winner": round(sum(1 for i in idx if y[i] > 0) / len(idx), 4),
                "mean_winning_bets": round(sum(y[i] for i in idx) / len(idx), 4)}
    tertiles = {k: band(v) for k, v in tert_idx.items()}
    # ---- power statement: alternative = observed GLM slope on standardized CSI, at Šidák alpha for m=2
    alpha = 1 - (1 - 0.05) ** 0.5
    crit = sorted(abs(v) for v in null_t1)[int((1 - alpha) * len(null_t1)) - 1]
    hits = 0
    for _ in range(args.power_trials):
        ys = [poisson_draw(rng, rate[glist[i]] * math.exp(b_csi * zx[i])) for i in range(n)]
        hits += abs(stats(zx, rx, ys)[0]) >= crit
    power = hits / args.power_trials
    zhi = sum(zx[i] for i in tert_idx["high"]) / len(tert_idx["high"])
    zlo = sum(zx[i] for i in tert_idx["low"]) / len(tert_idx["low"])
    # reference quantiles of CSI under uniform sampling, per pool (picker threshold constants)
    ref = {}
    for g in games:
        P = POOL[g]; r2 = random.Random(args.seed + P)
        vals = sorted(csi(r2.sample(range(1, P + 1), 6), P) for _ in range(20000))
        ref[g] = {"q40": round(vals[int(0.4 * len(vals))], 4), "q50": round(vals[len(vals) // 2], 4),
                  "q90": round(vals[int(0.9 * len(vals))], 4), "mean": round(sum(vals) / len(vals), 4)}
    result = {
        "_meta": {"schema_version": 1, "script": "src/csi_popularity.py", "run_date": args.run_date, "seed": args.seed,
                  "seed_scheme": "single random.Random(seed) stream: null trial -> permutations -> power; per-pool reference streams seed+P",
                  "registration": "docs/kb/conscious-selection-popularity.md (Part-3 onboarding; EXPLORATORY, G0)",
                  "input_sha256": {str(OFFICIAL.relative_to(ROOT)): sha256(OFFICIAL)},
                  "null_simulator": "draws: random.sample(range(1,P+1),6) per draw; winners: Poisson(per-game observed mean) independent of the combination",
                  "stratification": "CSI standardized and ranked WITHIN game; permutations shuffle winners within game; GLM has game fixed effects (pool size confounds CSI level and win rate — see step4_null_trial)",
                  "weights": WEIGHTS, "lucky_set": sorted(LUCKY),
                  "parity_vectors": [{"ticket": list(t), "pool": P, "csi": round(csi(t, P), 6)} for t, P in PARITY_VECTORS]},
        "data": {"n_draws": n, "per_game": {g: len(by_game[g]) for g in games}, "draws_with_winner": sum(1 for v in y if v > 0),
                 "total_winning_bets": sum(y), "date_range": [min(d for g in games for d, *_ in by_game[g]), max(d for g in games for d, *_ in by_game[g])]},
        "step4_null_trial": null_trial,
        "step6_first_run": {
            "T1_meandiff": {"observed": round(obs_t1, 6), "null_mean": null_trial["T1_meandiff"]["mean"], "null_sd": null_trial["T1_meandiff"]["sd"],
                            "z_vs_null_trial": round((obs_t1 - null_trial["T1_meandiff"]["mean"]) / null_trial["T1_meandiff"]["sd"], 2),
                            "perm_p_two_sided": p1, "m_perm": args.perms, "p_floor": 1 / (args.perms + 1)},
            "T2_rankcorr": {"observed": round(obs_t2, 6), "null_mean": null_trial["T2_rankcorr"]["mean"], "null_sd": null_trial["T2_rankcorr"]["sd"],
                            "z_vs_null_trial": round((obs_t2 - null_trial["T2_rankcorr"]["mean"]) / null_trial["T2_rankcorr"]["sd"], 2),
                            "perm_p_two_sided": p2, "m_perm": args.perms, "p_floor": 1 / (args.perms + 1)},
            "poisson_glm_descriptive": {"model": "winners ~ game fixed effects + z_csi(within game) + log jackpot (centred within game)",
                                        "beta_z_csi": round(b_csi, 4), "se_z_csi": round(se_csi, 4), "wald_z_csi": round(b_csi / se_csi, 2),
                                        "beta_log_jackpot": round(b_j, 4), "se_log_jackpot": round(se_j, 4), "dispersion": round(disp, 3),
                                        "sharing_multiplier_top_vs_bottom_tertile": round(math.exp(b_csi * (zhi - zlo)), 2)},
            "csi_tertiles_within_game": tertiles,
            "multi_winner_draws": [{"game": g, "date": d, "numbers": nums, "winning_bets": w, "csi": round(csi(nums, POOL[g]), 4)}
                                   for g in games for d, nums, J, w in by_game[g] if w > 1],
            "family": {"family_id": "payout-sharing", "within_run_m": 2, "sidak_alpha": round(alpha, 5), "grade": "G0 exploratory (weights declared before this run; no confirmation set yet)"},
            "power": {"alternative": "Poisson slope = observed beta_csi", "alpha": round(alpha, 5), "trials": args.power_trials, "power_T1": power},
            "caveats": ["'Winners' are winning standard bets per PCSO: one bettor holding k identical bets counts k times",
                        "Only jackpot-tier sharing is observable; Category II/III pool sharing is not published per draw",
                        "CSI weights are literature proxies for other lotteries; PCSO play-slip position effects are unmeasured",
                        "One year of draws, 77 winner events: effect size is the top-tertile contrast, not a calibrated per-combination model"]},
        "csi_uniform_reference": ref,
    }
    payload = (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    out = ROOT / "results" / f"csi_popularity_{args.run_date}.json"
    if args.verify:
        existing = out.read_bytes()
        digest = hashlib.sha256(existing).hexdigest()
        if existing != payload:
            raise SystemExit(f"VERIFY MISMATCH: regenerated bytes differ from {out}")
        print(f"PASS sha256={digest}; n={n}; T1 p={p1}; T2 p={p2}; wrote=none")
        return
    out.write_bytes(payload)
    print(f"wrote {out} sha256={hashlib.sha256(payload).hexdigest()}")
    print(f"n={n} winners={sum(1 for v in y if v > 0)}  T1={obs_t1:.4f} p={p1}  T2={obs_t2:.4f} p={p2}  beta_z_csi={b_csi:.3f}±{se_csi:.3f}  power={power:.2f}")
    print("null trial:", json.dumps(null_trial))
    print("tertiles:", json.dumps(tertiles))


if __name__ == "__main__":
    main()
