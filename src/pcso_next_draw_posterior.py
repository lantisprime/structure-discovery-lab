#!/usr/bin/env python3
"""Next-draw posterior predictive under the product-weight (conditional Poisson) model — G0 exploratory.

Model (codex review 2026-09-06, results/codex_review_2026-09-06.md §1): balls carry weights w in the
simplex; a 6-set S is drawn with probability f_w(S) = prod_{i in S} w_i / e_6(w), where e_6 is the 6th
elementary symmetric polynomial. Likelihood of T draws with ball counts c: prod_i w_i^{c_i} / e_6(w)^T.
Prior w ~ Dirichlet(a,...,a) with a FIXED (not chosen from the data). Posterior expectations are
computed by importance sampling from Dirichlet(a + c) with weights z(w)^{-T}, z(w) = e_6(Pw)/C(P,6).

Reports per game: maximum-predictive 6-set (six largest counts; ties listed), its multiplier
R_D(S) = C(P,6) * E[f_w(S) | D] with a 95% credible interval on R_w(S) = C(P,6) f_w(S); the same for
the bottom six, the hot six of the last 50 draws and the last draw's six; the Bayes factor uniform:tilted
BF_01(a) for a in {10, 100, 1000}; P(max_i |pi_i/(6/P) - 1| > 0.10 | D, M1); the model-averaged
multiplier R_mix = 1 + (R - 1)/(1 + BF_01); and an exact order-1 overlap test between consecutive draws.

Reads  datasets/pcso-lotto/data_draws_1yr.csv
Writes results/pcso_next_draw_posterior_<run_date>.json   (byte-deterministic for a given seed)
Usage: python3 src/pcso_next_draw_posterior.py [--seed 20260906] [--samples 200000] [--verify]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from math import lgamma
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "datasets" / "pcso-lotto" / "data_draws_1yr.csv"
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49, "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
K = 6


def esp(w, k=K):
    """elementary symmetric polynomials e_0..e_k of each row of w (n x P) -> (n x (k+1))."""
    n, P = w.shape
    E = np.zeros((n, k + 1))
    E[:, 0] = 1.0
    for i in range(P):
        wi = w[:, i:i + 1]
        E[:, 1:] = E[:, 1:] + wi * E[:, :-1]
    return E


def esp_minus(w, E, k=K):
    """e_{k-1}(w_{-i}) for every i, via e_j(w_{-i}) = e_j(w) - w_i e_{j-1}(w_{-i}). Returns (n x P)."""
    n, P = w.shape
    out = np.zeros((n, P))
    for i in range(P):
        wi = w[:, i]
        em = np.ones(n)          # e_0(w_{-i})
        for j in range(1, k):    # need e_{k-1}
            em = E[:, j] - wi * em
        out[:, i] = em
    return out


def wquant(x, wts, q):
    o = np.argsort(x)
    cw = np.cumsum(wts[o]) / wts.sum()
    return float(x[o][np.searchsorted(cw, q)])


def overlap_test(draws, P):
    """exact two-sided test of sum_t |S_t ∩ S_{t-1}| against the convolution of hypergeometric(P,6,6) overlaps."""
    T = len(draws)
    obs = sum(len(set(draws[i]) & set(draws[i + 1])) for i in range(T - 1))
    C = math.comb(P, K)
    h = np.array([math.comb(K, k) * math.comb(P - K, K - k) / C for k in range(K + 1)])
    dist = np.array([1.0])
    for _ in range(T - 1):
        dist = np.convolve(dist, h)
    mean = (T - 1) * 36 / P
    dev = abs(obs - mean)
    p = float(dist[np.abs(np.arange(len(dist)) - mean) >= dev - 1e-12].sum())
    return {"observed_total_overlap": obs, "expected": round(mean, 3), "exact_two_sided_p": round(p, 6)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--run-date", default="2026-09-06")
    ap.add_argument("--samples", type=int, default=200000)
    ap.add_argument("--prior", type=float, default=100.0)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    by = defaultdict(list)
    with open(DRAWS, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            by[r["Game"]].append((r["Date"], [int(r[f"N{i}"]) for i in range(1, 7)]))
    out = {}
    for g in sorted(by):
        P = POOL[g]
        rows = sorted(by[g])
        draws = [d for _, d in rows]
        T = len(draws)
        cnt = Counter(v for d in draws for v in d)
        c = np.array([cnt[v] for v in range(1, P + 1)], dtype=float)
        C = math.comb(P, K)
        logC = math.log(C)

        def posterior(a, n):
            w = rng.gamma(a + c, 1.0, size=(n, P))
            w /= w.sum(1, keepdims=True)
            E = esp(w)
            logz = np.log(E[:, K]) + K * math.log(P) - logC          # log z(w) = log e_6(Pw) - log C
            logwt = -T * logz
            lw = logwt - logwt.max()
            wt = np.exp(lw)
            wt /= wt.sum()
            ess = 1.0 / np.sum(wt ** 2)
            logA = K * T * math.log(P) + lgamma(P * a) - lgamma(P * a + K * T) + float(np.sum([lgamma(a + ci) - lgamma(a) for ci in c]))
            log_bf10 = logA + (np.log(np.mean(np.exp(lw))) + logwt.max())
            return w, E, wt, ess, log_bf10

        w, E, wt, ess, log_bf10 = posterior(args.prior, args.samples)
        bf01 = {str(int(args.prior)): float(np.exp(-log_bf10))}
        for a2 in (10.0, 1000.0):
            _, _, _, _, lb = posterior(a2, args.samples // 4)
            bf01[str(int(a2))] = float(np.exp(-lb))
        # inclusion probabilities pi_i = w_i e_5(w_-i)/e_6(w)
        e5m = esp_minus(w, E)
        pi = w * e5m / E[:, K:K + 1]
        dev = np.max(np.abs(pi / (K / P) - 1.0), axis=1)
        p_e10 = float(np.sum(wt * (dev > 0.10)))
        pi_mean = (wt[:, None] * pi).sum(0)

        def R_of(S):
            idx = np.array([v - 1 for v in S])
            Rw = C * np.prod(w[:, idx], axis=1) / E[:, K]
            mean = float(np.sum(wt * Rw))
            return {"set": sorted(S), "R_posterior_mean": round(mean, 4),
                    "R_95_cri": [round(wquant(Rw, wt, 0.025), 4), round(wquant(Rw, wt, 0.975), 4)],
                    "predictive_probability": mean / C, "uniform_probability": 1.0 / C,
                    "R_model_averaged": round(1 + (mean - 1) / (1 + bf01[str(int(args.prior))]), 4)}

        order = sorted(range(1, P + 1), key=lambda v: (-c[v - 1], v))
        top = order[:K]
        kth = c[order[K - 1] - 1]
        ties = [v for v in range(1, P + 1) if c[v - 1] == kth and v not in top]
        bottom = sorted(order[-K:])
        c50 = Counter(v for d in draws[-50:] for v in d)
        hot50 = sorted(sorted(range(1, P + 1), key=lambda v: (-c50[v], v))[:K])
        last = sorted(draws[-1])
        out[g] = {
            "draws": T, "last_draw": rows[-1][0], "pool": P, "prior_concentration": args.prior,
            "importance_sampling": {"samples": args.samples, "effective_sample_size": round(float(ess), 1)},
            "bayes_factor_uniform_over_tilted": {k: round(v, 4) for k, v in bf01.items()},
            "p_any_ball_inclusion_deviates_over_10pct_given_M1": round(p_e10, 6),
            "p_any_ball_inclusion_deviates_over_10pct_equal_model_odds": round(p_e10 / (1 + bf01[str(int(args.prior))]), 4),
            "inclusion_probability_posterior_mean_range": [round(float(pi_mean.min()), 5), round(float(pi_mean.max()), 5)],
            "uniform_inclusion": round(K / P, 5),
            "maximum_predictive_set": {**R_of(top), "count_ties_for_sixth_place": ties},
            "bottom_six": R_of(bottom), "hot_six_last_50": R_of(hot50), "last_draw_six": R_of(last),
            "order1_overlap_test": overlap_test(draws, P),
        }
    result = {"_meta": {"schema_version": 1, "script": "src/pcso_next_draw_posterior.py", "run_date": args.run_date, "seed": args.seed,
                        "model": "product-weight (conditional Poisson) 6-without-replacement; Dirichlet(a) prior with a fixed a priori; importance sampling from Dirichlet(a+c) with weights z(w)^-T",
                        "registration": "docs/RESULTS_PCSO_REFRESH_2026-09-06.md §8 (G0 exploratory; codex review results/codex_review_2026-09-06.md §1-3)",
                        "input_sha256": {str(DRAWS.relative_to(ROOT)): hashlib.sha256(DRAWS.read_bytes()).hexdigest()},
                        "note": "Under the uniform model every history-based rule has R=1 exactly; R_model_averaged folds in BF_01 at equal prior model odds"},
              "games": out}
    payload = (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    dst = ROOT / "results" / f"pcso_next_draw_posterior_{args.run_date}.json"
    if args.verify:
        if dst.read_bytes() != payload:
            raise SystemExit(f"VERIFY MISMATCH: {dst}")
        print(f"PASS sha256={hashlib.sha256(payload).hexdigest()}; wrote=none")
        return
    dst.write_bytes(payload)
    print(f"wrote {dst} sha256={hashlib.sha256(payload).hexdigest()}")
    for g, r in out.items():
        m = r["maximum_predictive_set"]
        print(f"{g:18s} top {m['set']} R={m['R_posterior_mean']} CrI={m['R_95_cri']} R_mix={m['R_model_averaged']}  BF01={r['bayes_factor_uniform_over_tilted']}  overlap p={r['order1_overlap_test']['exact_two_sided_p']}")


if __name__ == "__main__":
    main()
