"""Synthetic Batch 1, Experiment A — detectability frontier.

Per docs/REGISTRATION_SYNTHETIC_BATCH1.md. Single hot ball 17 in 6-of-55;
relative excess r in {0.05,...,0.8} (+ r=0 negative control, instrument
validity only); n in {100,...,3200}; R=200 replicates/cell.

Detection rule (registered): any of m=3 counted tests at Sidak alpha'.
  I1 chi2 per-ball counts | I2 max per-ball count deviation (A2 pattern)
  I3 graphon co-occurrence spectral norm (B1)
All p-values +1-corrected MC vs K=2000 nulls per n.

Usage:  python synthetic_batch1_expA.py run <n> [<n> ...]   (resumable per n)
        python synthetic_batch1_expA.py theory               (delta-hat, n_min)
Checkpoint: results/synthetic_batch1_expA_CHECKPOINT.md
Output:     results/synthetic_batch1_expA.json
"""
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.discrete_draws import fast_draws
from core.stats import sidak
from domains import synthetic_lottery as sl

P, K, R, BALL = 55, 2000, 200, 17
RS = [0.0, 0.05, 0.10, 0.20, 0.40, 0.80]   # r=0 is the negative control
NS = [100, 200, 400, 800, 1600, 3200]
ALPHA, M = 0.05, 3
MASTER = sl.MASTER_SEED
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "synthetic_batch1_expA.json")
CKPT = os.path.join(HERE, "..", "results", "synthetic_batch1_expA_CHECKPOINT.md")

P0 = 6.0 / P


def spec_for(r):
    return sl.single_ball_spec(P, BALL, r * P0)


def stats3(draws):
    """(chi2, maxdev, b1) on a T x 6 draw matrix."""
    T = len(draws)
    cnt = np.bincount(draws.ravel() - 1, minlength=P).astype(float)
    e = T * P0
    chi2 = float(((cnt - e) ** 2 / e).sum())
    maxdev = float(np.abs(cnt - e).max())
    Z = np.zeros((T, P))
    Z[np.arange(T)[:, None], draws - 1] = 1.0
    C = Z.T @ Z
    c = T * 30.0 / (P * (P - 1))
    A = C - c
    np.fill_diagonal(A, 0.0)
    b1 = float(np.abs(np.linalg.eigvalsh(A)).max())
    return chi2, maxdev, b1


def p_mc(obs, null):
    """+1-corrected upper-tail MC p (Phipson-Smyth)."""
    return (np.sum(null >= obs) + 1.0) / (len(null) + 1.0)


def load_out():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return {"meta": {"P": P, "K": K, "R": R, "ball": BALL, "rs": RS, "ns": NS,
                     "alpha": ALPHA, "m": M, "alpha_prime": sidak(ALPHA, M),
                     "master_seed": MASTER,
                     "seed_scheme": "cell rng = default_rng(MASTER*10**6 + "
                                    "cell_index); cell_index enumerates "
                                    "(n,r) over NS x RS; null rng per n = "
                                    "default_rng(MASTER*10**6 + 999000 + n)"},
            "cells": {}, "theory": {}}


def ckpt(line):
    with open(CKPT, "a") as f:
        f.write(line + "\n")


def run_n(n):
    out = load_out()
    aprime = out["meta"]["alpha_prime"]
    t0 = time.time()
    rng0 = np.random.default_rng(MASTER * 10**6 + 999000 + n)
    null = np.array([stats3(fast_draws(rng0, n, P)) for _ in range(K)])
    out["cells"].setdefault(str(n), {})
    for ri, r in enumerate(RS):
        cell_index = NS.index(n) * len(RS) + ri
        rng = np.random.default_rng(MASTER * 10**6 + cell_index)
        spec = spec_for(r) if r > 0 else sl.fair_spec(P)
        hits = np.zeros((R, 3), bool)
        for rep in range(R):
            s = stats3(sl.biased_draws(rng, n, spec))
            hits[rep] = [p_mc(s[j], null[:, j]) <= aprime for j in range(3)]
        out["cells"][str(n)][str(r)] = {
            "power_I1": float(hits[:, 0].mean()),
            "power_I2": float(hits[:, 1].mean()),
            "power_I3": float(hits[:, 2].mean()),
            "power_any": float(hits.any(axis=1).mean()),
            "cell_index": cell_index}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    ckpt(f"[done] expA n={n} (K={K} nulls, {len(RS)} r-cells x R={R}) "
         f"{time.time()-t0:.0f}s -> {os.path.basename(OUT)}")


def lam_star(df, aprime, beta=0.20):
    """Noncentrality lambda for a power-(1-beta) df-frontier: smallest lam such
    that a noncentral chi2_df(lam) variate exceeds the central chi2_df upper-
    alpha' critical value with probability 1-beta. Used for the dense-bias
    (omnibus chi2, df = P-1) envelope; the df=1 oracle uses the Wald (z+z)^2
    approximation instead (see `zsum2`)."""
    from scipy.stats import chi2, ncx2
    from scipy.optimize import brentq
    crit = chi2.ppf(1 - aprime, df)
    return float(brentq(lambda lam: ncx2.sf(crit, df, lam) - (1 - beta),
                        1e-9, 1e4))


def theory():
    from scipy.stats import norm
    out = load_out()
    aprime = out["meta"]["alpha_prime"]
    # one-draw presence covariance under 6-of-55 w/o replacement
    p2 = 30.0 / (P * (P - 1))
    S = np.full((P, P), p2 - P0 ** 2)
    np.fill_diagonal(S, P0 * (1 - P0))
    Sp = np.linalg.pinv(S)
    zsum2 = (norm.ppf(1 - aprime) + norm.ppf(0.80)) ** 2   # 1-df oracle (Wald)
    for r in RS:
        if r == 0:
            continue
        d = sl.realized_delta(spec_for(r), K=200_000)
        lam1 = float(d @ Sp @ d)
        out["theory"][str(r)] = {
            "realized_hot_delta": float(d[BALL - 1]),
            "nominal_eps": r * P0, "lambda1": lam1,
            "n_min_theory": float(zsum2 / lam1)}
    # empirical n_min: log-n interpolation of power_any through 0.80
    for r in RS:
        if r == 0:
            continue
        pw = [(n, out["cells"][str(n)][str(r)]["power_any"])
              for n in NS if str(n) in out["cells"]]
        emp = None
        for (n1, w1), (n2, w2) in zip(pw, pw[1:]):
            if w1 < 0.8 <= w2:
                f = (0.8 - w1) / (w2 - w1)
                emp = float(np.exp(np.log(n1) + f * (np.log(n2) - np.log(n1))))
                break
        if emp is None and pw and pw[0][1] >= 0.8:
            emp = float(pw[0][0])  # already above 0.8 at smallest n
        out["theory"][str(r)]["n_min_empirical"] = emp
    # Derived frontiers (now computed in-code; previously added out-of-band).
    #  df54  : dense-bias omnibus chi2 envelope, exact ncx2 inversion over P-1 df
    #  sparse: single-ball max-deviation scan, per-ball z-test Bonferroni over 2P
    lam54 = lam_star(P - 1, aprime)
    zss_scan = (norm.ppf(1 - aprime / (2 * P)) + norm.ppf(0.80)) ** 2
    for r in RS:
        if r == 0:
            continue
        t = out["theory"][str(r)]
        t["n_min_theory_df54"] = float(lam54 / t["lambda1"])
        t["n_min_theory_sparse_scan"] = float(
            zss_scan * P0 * (1 - P0) / t["realized_hot_delta"] ** 2)
    out["theory"]["_lambda_star"] = {
        "df1": zsum2, "df54": lam54,
        "note": "df-corrected frontier n_min = lambda*(df,alpha',beta=0.2)/ "
                "(delta' Sigma0+ delta); lambda* from noncentral chi2 inversion"}
    out["theory"]["_sparse_scan"] = {
        "z_sum_sq": zss_scan,
        "formula": "n_min ~ (z_{1-alpha'/(2P)} + z_{1-beta})^2 * p0(1-p0) / "
                   "eps^2 (single-ball scan)"}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    ckpt("[done] expA theory: realized delta-hat, Sigma0 pinv frontier, "
         "empirical n_min interpolation, df54 + sparse-scan frontiers (in-code)")
    for r, t in out["theory"].items():
        print(r, {k: (round(v, 1) if isinstance(v, float) and v > 1 else v)
                  for k, v in (t.items() if isinstance(t, dict) else [])})


if __name__ == "__main__":
    if sys.argv[1] == "run":
        for n in sys.argv[2:]:
            run_n(int(n))
    elif sys.argv[1] == "theory":
        theory()
