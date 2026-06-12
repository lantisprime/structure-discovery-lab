#!/usr/bin/env python3
"""R8 admission suite — lag-max cross-correlation (phase-invariant pairs).
Card: docs/kb/lagmax-crosscorrelation.md. Motivated by blind-eval FN-4.

FROZEN DESIGN (declared before any trial is run; no post-hoc tuning):
  statistic  T = max_{d in [-8..8]} |corr(x, roll(y, d))|  (circular)
  null       roll y by a uniform random offset with |offset| in [16, n-16]
             (outside the declared lag window; preserves autocorrelation,
             destroys cross-alignment); Phipson-Smyth +1; m = 199
  negative   independent AR(1) pairs, phi = 0.6, n = 200; 200 trials
             gates: |FPR - 0.05| <= 3*SE  AND  lattice chi^2 p > 0.01
  positive   common sine cycle (period 23) with RANDOM phase offset between
             the two series + Gaussian noise, n = 200; 100 trials per level
             gating level: noise sigma = 1.0 (power >= 0.8 required)
             power-curve levels (informational): sigma = 0.5, 2.0
  benchmark  post-hoc instrument-development check on the SOLVED blind set's
             S1|S2 pair (truth known: shared phase-indeterminate cycle missed
             by same-time Spearman). Labeled NOT-A-DISCOVERY.

Output: results/r8_admission.json
"""

import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "r8_admission.json")
SEED = 20260611
LAGS = range(-8, 9)
M = 199


def z(v):
    return (v - v.mean()) / (v.std() + 1e-12)


def lagmax_T(x, y):
    n = len(x)
    return max(abs(float(np.dot(x, np.roll(y, d))) / n) for d in LAGS)


def lagmax_p(x, y, rng, m=M):
    x, y = z(np.asarray(x, float)), z(np.asarray(y, float))
    n = len(x)
    obs = lagmax_T(x, y)
    nulls = []
    for _ in range(m):
        off = int(rng.integers(16, n - 16))
        if rng.random() < 0.5:
            off = -off
        nulls.append(lagmax_T(x, np.roll(y, off)))
    return (1 + sum(t >= obs for t in nulls)) / (m + 1)


def ar1(rng, n, phi=0.6):
    e = rng.normal(size=n)
    out = np.empty(n)
    out[0] = e[0]
    for i in range(1, n):
        out[i] = phi * out[i - 1] + e[i]
    return out


def run_negative(rng, trials=200):
    ps = np.array([lagmax_p(ar1(rng, 200), ar1(rng, 200), rng)
                   for _ in range(trials)])
    fpr = float(np.mean(ps <= 0.05))
    se3 = 3 * np.sqrt(0.05 * 0.95 / trials)
    # HARNESS FIX (not instrument tuning): 20 bins so expected count = 10
    # per bin; the original 200-cell version had expected 1/cell, where the
    # chi-square approximation is invalid (the lab's own C1 lesson).
    cnts, _ = np.histogram(ps, bins=np.linspace(0, 1, 21))
    exp = trials / 20.0
    chi2 = float((((cnts - exp) ** 2) / exp).sum())
    chi2_p = float(1 - stats.chi2.cdf(chi2, 19))
    return {"n_trials": trials, "fpr_at_alpha": fpr, "band_3se": round(se3, 4),
            "lattice_chi2_p": round(chi2_p, 4),
            "passed": bool(abs(fpr - 0.05) <= se3 and chi2_p > 0.01)}


def common_cycle_pair(rng, n, sigma):
    t = np.arange(n)
    phase = rng.uniform(0, 2 * np.pi)
    x = np.sin(2 * np.pi * t / 23.0) + sigma * rng.normal(size=n)
    y = np.sin(2 * np.pi * t / 23.0 + phase) + sigma * rng.normal(size=n)
    return x, y


def run_positive(rng, sigma, trials=100):
    ps = np.array([lagmax_p(*common_cycle_pair(rng, 200, sigma), rng)
                   for _ in range(trials)])
    return {"sigma": sigma, "n_trials": trials,
            "power_at_alpha": float(np.mean(ps <= 0.05)),
            "median_p": float(np.median(ps))}


def run_benchmark_posthoc():
    """NOT A DISCOVERY: instrument-development check on the solved blind set."""
    import pandas as pd
    rng = np.random.default_rng(SEED + 401)
    w = pd.read_csv(os.path.join(ROOT, "evals/structure_eval_set_v1/blind/"
                                       "datasets/series/series_wide.csv"))
    out = {}
    for a, b in [("S1", "S2"), ("S3", "S4")]:   # S1|S2 truth=related; S3|S4 truth=null
        out[f"{a}|{b}"] = round(lagmax_p(w[a].to_numpy(float),
                                         w[b].to_numpy(float), rng), 4)
    return {"pairs": out,
            "label": "POST-HOC instrument-development check on SOLVED benchmark "
                     "(answer key already unsealed) — not a discovery, not "
                     "counted in any ledger or accuracy figure"}


def main():
    which = sys.argv[1:] or ["negative", "positive", "benchmark"]
    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT))
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "design": "FROZEN pre-run (see module docstring)",
                        "card": "docs/kb/lagmax-crosscorrelation.md"}
    rng = np.random.default_rng(SEED + 400)
    if "negative" in which:
        results["negative_E1_independent_AR1"] = run_negative(rng)
        print("negative done", flush=True)
    if "positive" in which:
        results["positive_gate_sigma1.0"] = run_positive(rng, 1.0)
        results["powercurve_sigma0.5"] = run_positive(rng, 0.5)
        results["powercurve_sigma2.0"] = run_positive(rng, 2.0)
        print("positive done", flush=True)
    if "benchmark" in which:
        results["benchmark_posthoc"] = run_benchmark_posthoc()
        print("benchmark done", flush=True)
    neg = results.get("negative_E1_independent_AR1", {})
    pos = results.get("positive_gate_sigma1.0", {})
    if neg and pos:
        results["admission"] = {
            "negative_passed": neg["passed"],
            "power_ok": pos["power_at_alpha"] >= 0.8,
            "ADMITTED": bool(neg["passed"] and pos["power_at_alpha"] >= 0.8)}
    json.dump(results, open(OUT, "w"), indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
