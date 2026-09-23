#!/usr/bin/env python3
"""Low-dimensional tilt evidence process for the PCSO draws — registration
docs/REGISTRATION_PCSO_LOWDIM_TILT.md (sequential test on draws after the registration date;
everything before it is exploratory).

Theory (docs/RESULTS_PCSO_PICKER_THEOREM_2026-09-23.md):
* Bayes-mixture learning cost (Rissanen 1986; Clarke & Barron 1990): a prequential evidence
  process against a d-parameter alternative has E[log M_T] = T KL - (d/2) log T + O(1). The lab's
  product-weight alternative has d = P - 1 = 41..57, which needs ~7,400-9,900 draws per game to
  detect a 10% RMS weight deviation; a d = 1 alternative needs ~300. This script tests d = 1.
* Alternatives (fixed a priori): ball weights w_i(theta) = exp(theta g(i)), 6-sets drawn with
  f_theta(S) = prod_{i in S} w_i / e_6(w) (the lab's product-weight / conditional-Poisson form),
  with g standardised to mean 0 and sd 1 over the pool so theta is the RMS log-weight deviation:
    high31: g ~ 1[i > 31]   (the exploratory over-draw of numbers above 31, RESULTS §3)
    index:  g ~ i           (monotone in the ball number)
  theta is shared by the five games (one mechanism hypothesis, 5x the draws), prior
  N(0, 0.1^2) on a 161-point grid over [-0.4, 0.4].
* Evidence process (arXiv:2210.01948 §3.2.2 mixture method): Lambda_t = q_t(S_t) / p0(S_t),
  q_t(S) = sum_theta pi_{t-1}(theta) f_theta(S), p0 = 1/C(P,6). Each M^a_t = prod Lambda is a
  nonnegative martingale with unit mean under uniform draws; the registered statistic is the
  average M_t = (M^high31_t + M^index_t)/2, again an e-process (§2.9), so Ville gives
  P(sup_t M_t >= 1/alpha) <= alpha with alpha = 0.01. Exact: no Monte Carlo inside the process.

Reads  datasets/pcso-lotto/data_draws_1yr.csv
Writes results/pcso_lowdim_eprocess_<run_date>.json  (byte-deterministic for a given seed)
Usage: python3 src/pcso_lowdim_eprocess.py [--run-date 2026-09-21] [--verify]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "datasets" / "pcso-lotto" / "data_draws_1yr.csv"
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
K = 6
REGISTERED_AFTER = "2026-09-23"   # registration date: draws dated after it are the registered test
FREEZE = "2026-06-10"             # exploration/confirmation boundary (DATASET.md §6)
ALPHA = 0.01
THETA = np.linspace(-0.4, 0.4, 161)
PRIOR_SD = 0.1


def standardise(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / x.std()


def g_high(P: int, cut: int = 31) -> np.ndarray:
    return standardise((np.arange(1, P + 1) > cut).astype(float))


def g_index(P: int) -> np.ndarray:
    return standardise(np.arange(1, P + 1, dtype=float))


ALTERNATIVES = {"high31": g_high, "index": g_index}


def log_e(w: np.ndarray, k: int = K) -> np.ndarray:
    """log e_k(w) for each row of w (n x P), by the elementary-symmetric recurrence."""
    E = np.zeros((w.shape[0], k + 1))
    E[:, 0] = 1.0
    for i in range(w.shape[1]):
        E[:, 1:] = E[:, 1:] + w[:, i:i + 1] * E[:, :-1]
    return np.log(E[:, k])


class Alt:
    """One alternative for one pool: log f_theta(S) = theta * sum_{i in S} g_i - log e_6(exp(theta g))."""

    def __init__(self, g: np.ndarray):
        self.g = g
        self.logz = log_e(np.exp(np.outer(THETA, g)))           # (grid,)
        self.log_p0 = -math.log(math.comb(len(g), K))

    def log_f(self, gsum):
        """log f_theta(S) for every grid theta; gsum scalar or (n,) -> (grid,) or (n, grid)."""
        return np.multiply.outer(gsum, THETA) - self.logz


def log_prior() -> np.ndarray:
    lp = -0.5 * (THETA / PRIOR_SD) ** 2
    return lp - np.logaddexp.reduce(lp)


def lse(a, axis=-1):
    m = np.max(a, axis=axis, keepdims=True)
    return (m + np.log(np.sum(np.exp(a - m), axis=axis, keepdims=True))).squeeze(axis)


def run(seq, cond=()):
    """Prequential evidence over seq = [(date, game, sorted tuple)], posterior first conditioned on
    cond (same format, not scored). Returns per-alternative and averaged evidence summaries."""
    alts = {a: {P: Alt(fn(P)) for P in set(POOL.values())} for a, fn in ALTERNATIVES.items()}
    out = {}
    logM = {}
    for a in ALTERNATIVES:
        lp = log_prior()
        for _, game, S in cond:
            A = alts[a][POOL[game]]
            lp = lp + A.log_f(float(A.g[np.array(S) - 1].sum()))
            lp -= lse(lp)
        path = []
        lm = 0.0
        for _, game, S in seq:
            A = alts[a][POOL[game]]
            lf = A.log_f(float(A.g[np.array(S) - 1].sum()))
            lm += float(lse(lp + lf)) - A.log_p0
            path.append(lm)
            lp = lp + lf
            lp -= lse(lp)
        logM[a] = np.array(path)
        post = np.exp(lp)
        out[a] = {"final_e": round(math.exp(lm), 6), "max_e": round(float(np.exp(max(path + [0.0]))), 6),
                  "theta_posterior_mean": round(float(np.sum(post * THETA)), 5),
                  "theta_posterior_sd": round(float(np.sqrt(np.sum(post * THETA ** 2) - np.sum(post * THETA) ** 2)), 5)}
    avg = 0.5 * (np.exp(logM["high31"]) + np.exp(logM["index"])) if len(seq) else np.array([1.0])
    out["registered_statistic_average"] = {"draws": len(seq), "final_e": round(float(avg[-1]), 6),
                                           "max_e": round(float(max(1.0, avg.max())), 6),
                                           "crossed_1_over_alpha": bool(avg.max() >= 1 / ALPHA)}
    return out


def m_probs(P: int, theta: float, g: np.ndarray, cut: int = 31) -> np.ndarray:
    """Exact law of m = #{i in S: i > cut} under f_theta when g is constant within {<= cut} and {> cut}."""
    H = P - cut
    wH, wL = math.exp(theta * g[-1]), math.exp(theta * g[0])
    p = np.array([math.comb(H, m) * math.comb(P - H, K - m) * wH ** m * wL ** (K - m) for m in range(K + 1)])
    return p / p.sum()


def simulate(rng, nsim: int, horizon: int, theta_true: float):
    """Pooled draws cycling through the five games; theta_true tilts the high31 direction (exact:
    sample m from its law, then m high and 6-m low balls uniformly). Returns sup of the averaged
    process per replicate and the first crossing time (or -1)."""
    pools = list(POOL.values())
    alts = {a: {P: Alt(fn(P)) for P in pools} for a, fn in ALTERNATIVES.items()}
    lp = {a: np.tile(log_prior(), (nsim, 1)) for a in ALTERNATIVES}
    lm = {a: np.zeros(nsim) for a in ALTERNATIVES}
    sup = np.ones(nsim)
    first = np.full(nsim, -1)
    for t in range(horizon):
        P = pools[t % len(pools)]
        g = g_high(P)
        m = rng.choice(K + 1, size=nsim, p=m_probs(P, theta_true, g))
        # m high balls and 6-m low balls, uniformly within each class: only sum_{i in S} g_i enters
        # the process, so draw the per-class sums from random permutations' prefix sums.
        # The same permutations serve both alternatives, so both score the same 6-set.
        rows = np.arange(nsim)
        perm_hi = np.argsort(rng.random((nsim, P - 31)), 1)
        perm_lo = np.argsort(rng.random((nsim, 31)), 1)
        gsum = {}
        for a in ALTERNATIVES:
            ga = alts[a][P].g
            chi = np.concatenate([np.zeros((nsim, 1)), np.cumsum(ga[31:][perm_hi], 1)], 1)
            clo = np.concatenate([np.zeros((nsim, 1)), np.cumsum(ga[:31][perm_lo], 1)], 1)
            gsum[a] = chi[rows, m] + clo[rows, K - m]
        for a in ALTERNATIVES:
            A = alts[a][P]
            lf = A.log_f(gsum[a])                                             # (nsim, grid)
            lm[a] += lse(lp[a] + lf) - A.log_p0
            lp[a] = lp[a] + lf
            lp[a] -= lse(lp[a])[:, None]
        cur = 0.5 * (np.exp(lm["high31"]) + np.exp(lm["index"]))
        sup = np.maximum(sup, cur)
        first[(first < 0) & (cur >= 1 / ALPHA)] = t + 1
    return sup, first


def load():
    rows = []
    for r in csv.DictReader(io.StringIO(DRAWS.read_bytes().decode("utf-8-sig"))):
        if r["Game"] in POOL:
            rows.append((r["Date"], r["Game"], tuple(sorted(int(r[f"N{i}"]) for i in range(1, 7)))))
    return sorted(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--run-date", default="2026-09-21")
    ap.add_argument("--null-sims", type=int, default=4000)
    ap.add_argument("--power-sims", type=int, default=100)
    ap.add_argument("--horizon", type=int, default=2400)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    rows = load()
    pre = [r for r in rows if r[0] <= FREEZE]
    post = [r for r in rows if FREEZE < r[0] <= REGISTERED_AFTER]
    reg = [r for r in rows if r[0] > REGISTERED_AFTER]
    rng = np.random.default_rng(args.seed)
    sup0, _ = simulate(rng, args.null_sims, args.horizon, 0.0)
    power = {}
    for th in (0.05, 0.10):
        _, first = simulate(rng, args.power_sims, args.horizon, th)
        hit = first[first > 0]
        power[f"theta_{th:.2f}"] = {"fraction_crossed_by_horizon": round(float(np.mean(first > 0)), 4),
                                    "median_pooled_draws_to_cross": (int(np.median(hit)) if len(hit) else None)}
    out = {"_meta": {"schema_version": 1, "script": "src/pcso_lowdim_eprocess.py", "run_date": args.run_date,
                     "seed": args.seed, "registration": "docs/REGISTRATION_PCSO_LOWDIM_TILT.md",
                     "registered_after": REGISTERED_AFTER, "freeze": FREEZE, "alpha": ALPHA,
                     "threshold_1_over_alpha": 1 / ALPHA, "theta_grid": [float(THETA[0]), float(THETA[-1]), len(THETA)],
                     "prior": f"N(0, {PRIOR_SD}^2) on the grid, shared across games",
                     "alternatives": {"high31": "g ~ 1[i > 31], standardised", "index": "g ~ i, standardised"},
                     "input_sha256": {str(DRAWS.relative_to(ROOT)): hashlib.sha256(DRAWS.read_bytes()).hexdigest()}},
           "registered_test": run(reg, pre + post),
           "exploratory": {"full_history_from_prior": run(rows),
                           "post_freeze_given_pre_freeze": run(post, pre),
                           "note": "high31 was motivated by these draws (RESULTS §3): exploratory values here cannot confirm"},
           "null_check_uniform_draws": {"replicates": args.null_sims, "pooled_draws": args.horizon,
                                        "fraction_sup_ge_1_over_alpha": round(float(np.mean(sup0 >= 1 / ALPHA)), 4),
                                        "ville_bound": ALPHA, "median_sup": round(float(np.median(sup0)), 4)},
           "power_high31_tilt": {"replicates": args.power_sims, "pooled_draws_horizon": args.horizon, **power}}
    payload = (json.dumps(out, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    dst = ROOT / "results" / f"pcso_lowdim_eprocess_{args.run_date}.json"
    if args.verify:
        if dst.read_bytes() != payload:
            raise SystemExit(f"VERIFY MISMATCH: {dst}")
        print(f"PASS sha256={hashlib.sha256(payload).hexdigest()}; wrote=none")
        return
    dst.write_bytes(payload)
    print(f"wrote {dst.relative_to(ROOT)} sha256={hashlib.sha256(payload).hexdigest()}")
    print(json.dumps({k: out[k] for k in ("registered_test", "exploratory", "null_check_uniform_draws", "power_high31_tilt")}, indent=1))


if __name__ == "__main__":
    main()
