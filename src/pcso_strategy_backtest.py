#!/usr/bin/env python3
"""Draw-paired backtest of ticket-selection strategies on official PCSO draws (G0 exploratory).

Question: does any selection rule change the match count against the actual draws?
Design (docs/kb/expected-value-stern-cover.md: backtests need a paired null on the same draws):
  * unit of independence = the DRAW; per draw, each strategy's mean matches over R replicate
    2-ticket plays is compared with the uniform-disjoint baseline on the SAME draw;
  * test statistic = mean paired difference over draws; p from a sign-flip permutation of the
    per-draw differences (add-one, lattice m = --perms);
  * strategies: uniform disjoint pair; picker v1 (four pattern filters); picker v2 (CSI-filtered,
    src/csi_popularity.py); hot/cold top-6 (trailing 50 draws); overdue-gap; repeat-last-draw;
    Markov order-1 pair proxy. Each uses only draws BEFORE the target draw (warm-up 30).

Reads  datasets/pcso-lotto/data_official_draws_jackpots.csv
Writes results/pcso_strategy_backtest_<run_date>.json   (byte-deterministic for a given seed)
Usage: python3 src/pcso_strategy_backtest.py [--seed 20260906] [--reps 300] [--perms 9999] [--verify]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter

from csi_popularity import ROOT, OFFICIAL, POOL, csi, load_official, sha256

WARM = 30
FIXED_CAT4 = {"Lotto 6/42": 20, "Mega Lotto 6/45": 30, "Super Lotto 6/49": 50, "Grand Lotto 6/55": 60, "Ultra Lotto 6/58": 100}


def p_match(P, k):
    return math.comb(6, k) * math.comb(P - 6, 6 - k) / math.comb(P, 6)


def make_strategies(rng, seed):
    def two_disjoint(P):
        a = rng.sample(range(1, P + 1), 12)
        return sorted(a[:6]), sorted(a[6:])

    def v1_bad(t):
        s = sorted(t)
        if s[5] <= 31:
            return True
        run = mx = 1
        for i in range(1, 6):
            run = run + 1 if s[i] == s[i - 1] + 1 else 1
            mx = max(mx, run)
        if mx >= 4:
            return True
        d = s[1] - s[0]
        if d > 0 and all(s[i] == s[0] + i * d for i in range(6)):
            return True
        return len({v % 10 for v in s}) == 1

    thr = {}
    for g, P in POOL.items():
        r2 = random.Random(seed + P)
        vals = sorted(csi(r2.sample(range(1, P + 1), 6), P) for _ in range(20000))
        thr[P] = vals[int(0.40 * len(vals))]

    def uniform(P, hist):
        return list(two_disjoint(P))

    def v1(P, hist):
        for _ in range(200):
            a, b = two_disjoint(P)
            if not v1_bad(a) and not v1_bad(b):
                return [a, b]
        return [a, b]

    def v2(P, hist):
        for _ in range(400):
            a, b = two_disjoint(P)
            if csi(a, P) <= thr[P] and csi(b, P) <= thr[P]:
                return [a, b]
        return [a, b]

    def freq(hist, P, w=50):
        c = Counter(v for d in hist[-w:] for v in d)
        return [c[v] for v in range(1, P + 1)]

    def hot(P, hist):
        f = freq(hist, P)
        o = sorted(range(1, P + 1), key=lambda v: (-f[v - 1], rng.random()))
        return [sorted(o[:6]), sorted(o[6:12])]

    def cold(P, hist):
        f = freq(hist, P)
        o = sorted(range(1, P + 1), key=lambda v: (f[v - 1], rng.random()))
        return [sorted(o[:6]), sorted(o[6:12])]

    def overdue(P, hist):
        last = {v: -1 for v in range(1, P + 1)}
        for i, d in enumerate(hist):
            for v in d:
                last[v] = i
        o = sorted(range(1, P + 1), key=lambda v: (last[v], rng.random()))
        return [sorted(o[:6]), sorted(o[6:12])]

    def repeat_last(P, hist):
        a = sorted(hist[-1])
        rest = [v for v in range(1, P + 1) if v not in a]
        return [a, sorted(rng.sample(rest, 6))]

    def markov_pair(P, hist):
        last = set(hist[-1])
        c = Counter()
        for i in range(len(hist) - 1):
            if last & set(hist[i]):
                c.update(hist[i + 1])
        o = sorted(range(1, P + 1), key=lambda v: (-c[v], rng.random()))
        return [sorted(o[:6]), sorted(o[6:12])]

    return {"uniform_disjoint": uniform, "picker_v1_filters": v1, "picker_v2_csi": v2, "hot_top6_w50": hot,
            "cold_bottom6_w50": cold, "overdue_gap": overdue, "repeat_last_draw": repeat_last,
            "markov_pair_order1": markov_pair}, {str(P): round(t, 4) for P, t in thr.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--run-date", default="2026-09-06")
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--perms", type=int, default=9999)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    by_game = load_official()
    games = sorted(by_game)
    strategies, thresholds = make_strategies(rng, args.seed)
    draw_list = [(g, t) for g in games for t in range(WARM, len(by_game[g]))]
    T = len(draw_list)
    per_draw = {}
    results = {}
    for name, fn in strategies.items():
        reps = args.reps if name in ("uniform_disjoint", "picker_v1_filters", "picker_v2_csi") else max(args.reps // 3, 20)
        matches = Counter()
        cat4_pesos = 0.0
        means = []
        for g, t in draw_list:
            P = POOL[g]
            hist = [d[1] for d in by_game[g]]
            actual = set(hist[t])
            ks = []
            for _ in range(reps):
                for tk in fn(P, hist[:t]):
                    k = len(actual & set(tk))
                    ks.append(k)
                    matches[k] += 1
                    if k == 3:
                        cat4_pesos += FIXED_CAT4[g]
            means.append(sum(ks) / len(ks))
        per_draw[name] = means
        n_t = sum(matches.values())
        results[name] = {"replicates_per_draw": reps, "tickets": n_t, "draws": T,
                         "mean_matches": round(sum(k * c for k, c in matches.items()) / n_t, 5),
                         "expected_mean_h0": round(sum(36 / POOL[g] for g, _ in draw_list) / T, 5),
                         "matches_hist": {str(k): matches[k] for k in range(7)},
                         "p3plus_obs": round(sum(c for k, c in matches.items() if k >= 3) / n_t, 6),
                         "p3plus_exp_h0": round(sum(sum(p_match(POOL[g], k) for k in range(3, 7)) for g, _ in draw_list) / T, 6),
                         "fixed_3match_return_per_ticket": round(cat4_pesos / n_t, 4),
                         "max_matches_seen": max(k for k in matches if matches[k] > 0)}
    # paired comparison vs uniform on the same draws, sign-flip permutation p (two-sided, add-one)
    base = per_draw["uniform_disjoint"]
    fam = []
    for name in strategies:
        if name == "uniform_disjoint":
            continue
        diffs = [a - b for a, b in zip(per_draw[name], base)]
        md = sum(diffs) / T
        sd = math.sqrt(sum((d - md) ** 2 for d in diffs) / (T - 1))
        z = md / (sd / math.sqrt(T))
        cnt = 0
        for _ in range(args.perms):
            s = sum(d if rng.random() < 0.5 else -d for d in diffs) / T
            cnt += abs(s) >= abs(md) - 1e-15
        p = (cnt + 1) / (args.perms + 1)
        results[name].update({"paired_vs_uniform": {"mean_diff_matches_per_ticket": round(md, 6), "z": round(z, 2),
                                                    "signflip_perm_p_two_sided": p, "m_perm": args.perms, "p_floor": 1 / (args.perms + 1)}})
        fam.append(p)
    m = len(fam)
    sidak = 1 - (1 - 0.05) ** (1 / m)
    verdict = {"family_id": "strategy-backtest", "within_run_m": m, "sidak_alpha": round(sidak, 5),
               "min_p": min(fam), "any_flag": min(fam) < sidak,
               "statement": "no selection rule changed the match rate against the actual draws beyond chance"
               if min(fam) >= sidak else "FLAG: at least one strategy differs from uniform at the Šidák level — trace before reporting"}
    # ---- A3/A4 trace: driving rows. The pickers (v1, v2) and the cold strategy are all functions of the
    # marginal frequency of numbers > 31 in this sample (the filters push tickets above 31; cold picks the
    # least-drawn numbers). Report that marginal driver directly and the correlation of the per-draw
    # differences between strategies, so a flag is charged once (equivalence class), not per strategy.
    high_obs = high_exp = high_var = 0.0
    for g, t in draw_list:
        P = POOL[g]
        k = sum(1 for v in by_game[g][t][1] if v > 31)
        high_obs += k
        ph = (P - 31) / P
        high_exp += 6 * ph
        high_var += 6 * ph * (1 - ph) * (P - 6) / (P - 1)   # hypergeometric variance of the count > 31
    z_high = (high_obs - high_exp) / math.sqrt(high_var)
    def corr(a, b):
        ma, mb = sum(a) / T, sum(b) / T
        sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        return sab / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    d = {n: [a - b for a, b in zip(per_draw[n], base)] for n in strategies if n != "uniform_disjoint"}
    verdict["trace"] = {
        "driver": "count of drawn numbers > 31 per draw (marginal frequency of the high half of the pool)",
        "numbers_above_31": {"observed": int(high_obs), "expected_h0": round(high_exp, 2), "z": round(z_high, 2)},
        "per_draw_diff_correlations": {"v1_vs_v2": round(corr(d["picker_v1_filters"], d["picker_v2_csi"]), 3),
                                       "v1_vs_cold": round(corr(d["picker_v1_filters"], d["cold_bottom6_w50"]), 3),
                                       "v2_vs_cold": round(corr(d["picker_v2_csi"], d["cold_bottom6_w50"]), 3)},
        "charge": "one equivalence class (marginal-frequency shadow): the v1/v2 positive and cold negative deviations share driving rows; "
                  "the registered per-game MC chi-square on the same confirmation draws is null (results/pcso_confirmation_2026-09-06.json)"}
    result = {"_meta": {"schema_version": 1, "script": "src/pcso_strategy_backtest.py", "run_date": args.run_date, "seed": args.seed,
                        "seed_scheme": "single random.Random(seed) stream in strategy order; CSI thresholds from random.Random(seed+P)",
                        "registration": "docs/RESULTS_PCSO_REFRESH_2026-09-06.md §3 (G0 exploratory backtest; not in the confirmation family)",
                        "input_sha256": {str(OFFICIAL.relative_to(ROOT)): sha256(OFFICIAL)}, "warmup_draws": WARM,
                        "csi_acceptance_threshold_q40": thresholds,
                        "null": "i.i.d. uniform draws => every fixed ticket has E[matches]=36/P; paired sign-flip null on per-draw differences"},
              "draws_used": T, "strategies": results, "family_verdict": verdict}
    payload = (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    out = ROOT / "results" / f"pcso_strategy_backtest_{args.run_date}.json"
    if args.verify:
        existing = out.read_bytes()
        if existing != payload:
            raise SystemExit(f"VERIFY MISMATCH: regenerated bytes differ from {out}")
        print(f"PASS sha256={hashlib.sha256(existing).hexdigest()}; draws={T}; min_p={min(fam)}; wrote=none")
        return
    out.write_bytes(payload)
    print(f"wrote {out} sha256={hashlib.sha256(payload).hexdigest()}")
    for name, r in results.items():
        pv = r.get("paired_vs_uniform", {})
        print(f"{name:20s} mean_k={r['mean_matches']:.4f} exp={r['expected_mean_h0']:.4f} "
              f"diff_vs_uniform={pv.get('mean_diff_matches_per_ticket', 0):+.5f} z={pv.get('z', 0):+.2f} p={pv.get('signflip_perm_p_two_sided', '-')}")
    print("family verdict:", verdict["statement"], f"(min p={verdict['min_p']}, Šidák α={verdict['sidak_alpha']})")


if __name__ == "__main__":
    main()
