#!/usr/bin/env python3
"""
Batch 7 — atmospheric-pressure relational experiments.
Run only AFTER docs/REGISTRATION_BATCH7.md. Stages: seasons, cca, gwgate, gw.
Output: results/relational_batch7.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_batch7.json")
SEED = 20260611

sys.path.insert(0, HERE)
from relational_admission import mmd_pvalue
from relational_first_run import ridge_cca_heldout
from relational_batch5 import delay_embed, p_perm


def load():
    pr = pd.read_csv(os.path.join(ROOT, "datasets/openmeteo-pressure-manila/pressure_daily.csv"))
    pr["P_range"] = pr["P_msl_max_hPa"] - pr["P_msl_min_hPa"]
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))
    dr = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    dr = dr[dr["Game"] == "Grand Lotto 6/55"].sort_values("Date")
    return pr, tid, sm, kp, dr


PCOLS = ["P_msl_mean_hPa", "P_msl_min_hPa", "P_msl_max_hPa", "P_range"]


def run_seasons():
    rng = np.random.default_rng(SEED + 80)
    pr, *_ = load()
    F = pr[PCOLS].to_numpy(float)
    F = (F - F.mean(0)) / F.std(0)
    n = len(F)
    cuts = [0, n // 4, n // 2, 3 * n // 4, n]
    qd = [str(pr["Date"][cuts[i]]) for i in range(4)]
    pairs = {}
    for i in range(4):
        for j in range(i + 1, 4):
            # m=199 so the permutation floor (0.005) resolves below the
            # Sidak threshold (0.0085) -- m=99's floor of 0.01 cannot
            p = mmd_pvalue(F[cuts[i]:cuts[i + 1]], F[cuts[j]:cuts[j + 1]], rng, m=199)
            pairs[f"Q{i+1}|Q{j+1}"] = float(p)
    sidak = 1 - 0.95 ** (1 / 6)
    return {"pairs": pairs, "quarter_starts": qd, "sidak_threshold": float(sidak),
            "n_reject_corrected": int(sum(p <= sidak for p in pairs.values())),
            "note": "Q1 starts 2025-06-11 (wet); Q3 spans Nov-Mar (dry) per era registry"}


def run_cca():
    rng = np.random.default_rng(SEED + 81)
    pr, tid, sm, kp, _ = load()
    sm_c = sm[["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)",
               "Sun Alt (deg)"]]
    a = pr.merge(sm_c, on="Date").sort_values("Date")
    res_sun = ridge_cca_heldout(a[PCOLS].to_numpy(float),
                                a[["Moon Dist (km)", "Moon Illum (0-1)",
                                   "Sun Dist (km)", "Sun Alt (deg)"]].to_numpy(float), rng)
    b = pr.merge(kp[["Date", "Kp_daily_mean", "Kp_daily_max"]], on="Date").sort_values("Date")
    res_kp = ridge_cca_heldout(b[PCOLS].to_numpy(float),
                               b[["Kp_daily_mean", "Kp_daily_max"]].to_numpy(float), rng)
    return {"pressure_vs_sunmoon": res_sun, "pressure_vs_kp": res_kp}


def gw_distortion(A, B):
    import ot
    CA = np.sqrt(np.sum((A[:, None] - A[None, :]) ** 2, axis=-1))
    CB = np.sqrt(np.sum((B[:, None] - B[None, :]) ** 2, axis=-1))
    CA /= CA.mean(); CB /= CB.mean()
    p = np.ones(len(A)) / len(A); q = np.ones(len(B)) / len(B)
    return ot.gromov.gromov_wasserstein2(CA, CB, p, q, "square_loss")


def matched_gaussian(rng, B):
    mu = B.mean(0); C = np.cov(B.T) + 1e-9 * np.eye(B.shape[1])
    return rng.multivariate_normal(mu, C, size=len(B))


def gw_test(rng, A, B, m=19):
    obs = -gw_distortion(A, B)
    nulls = [-gw_distortion(A, matched_gaussian(rng, B)) for _ in range(m)]
    return {"score": float(obs), "p": p_perm(obs, nulls),
            "null_mean": float(np.mean(nulls))}


def sub120(X):
    idx = np.linspace(0, len(X) - 1, 120).astype(int)
    return X[idx]


def embed_series(y):
    y = (y - y.mean()) / y.std()
    return sub120(delay_embed(y))


def run_gwgate():
    from scipy import stats
    rng = np.random.default_rng(SEED + 82)
    pvals = []
    for _ in range(20):
        A = rng.normal(size=(120, 3)); B = rng.normal(size=(120, 3))
        pvals.append(gw_test(rng, A, B)["p"])
    pvals = np.asarray(pvals)
    ks = stats.kstest(pvals, "uniform")
    fpr = float(np.mean(pvals <= 0.05))
    return {"n_trials": 20, "shape": [120, 3], "fpr_at_alpha": fpr,
            "ks_p": float(ks.pvalue),
            "gate_passed": bool(fpr <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / 20)
                                and ks.pvalue > 0.01)}


def run_gw():
    rng = np.random.default_rng(SEED + 83)
    pr, tid, sm, kp, dr = load()
    E = {
        "pressure": embed_series(pr["P_msl_mean_hPa"].to_numpy(float)),
        "tidal": embed_series(tid["Total tidal accel (g)"].to_numpy(float)),
        "moon": embed_series(sm["Moon Dist (km)"].to_numpy(float)),
        "lotto655_sum": embed_series(
            dr[[f"N{i}" for i in range(1, 7)]].to_numpy(float).sum(1)),
    }
    out = {}
    for a, b, tag in [("pressure", "tidal", "exploratory"),
                      ("pressure", "lotto655_sum", "registered NULL"),
                      ("tidal", "moon", "registered POSITIVE (lunar mechanism)")]:
        out[f"{a}|{b}"] = {**gw_test(rng, E[a], E[b]), "registration": tag}
    return out


STAGES = {"seasons": run_seasons, "cca": run_cca, "gwgate": run_gwgate,
          "gw": run_gw}


def main():
    stages = sys.argv[1:] or list(STAGES)
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "registration": "docs/REGISTRATION_BATCH7.md"}
    for st in stages:
        results[st] = STAGES[st]()
        print(st, "done:", json.dumps(results[st])[:240], flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
