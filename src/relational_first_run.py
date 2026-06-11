#!/usr/bin/env python3
"""
First registered relational run (CROSS_DATASET_FRAMEWORK §4-§5 protocols).

Registered expectations (declared BEFORE execution, per A6):
  H-R1  Subset-to-whole recovery curves RISE above the matched temporal null for
        the three physical series (tidal accel, moon distance, Kp mean) — they
        are smooth/autocorrelated.
  H-R2  The lotto draw-sum series and the lotto presence matrix sit ON the null
        line at every subset fraction (the i.i.d. control / entropy-floor
        prediction, E8).
  H-R3  Date-paired CCA between 6/55 draw features and physical covariates is
        NULL under the shuffled-pairing null (replicates ledger row 2 with the
        relational instrument).
  H-R4  Date-paired CCA between tidal acceleration and sun/moon ephemerides is
        STRONGLY POSITIVE (known mechanism: tidal accel is derived from those
        distances) — the real-data positive control.

Nulls: within-series value permutation (preserves marginal, destroys temporal
structure) for recovery curves; the constrained 6-of-P uniform generator for
the presence matrix (A1); shuffled held-out pairing for CCA. p-values use the
Phipson-Smyth +1 correction. Seeded, deterministic.

Output: results/relational_first_run.json
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_first_run.json")

SUBSET_FRACS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.40]
REPEATS = 10
M_NULL = 49
SEED = 20260611


# ---------------------------------------------------------------- loading
def load_series():
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))
    dr = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    dr = dr[dr["Game"] == "Grand Lotto 6/55"].copy().sort_values("Date")
    nums = dr[[f"N{i}" for i in range(1, 7)]].to_numpy()
    series = {
        "tidal_total_accel": tid["Total tidal accel (g)"].to_numpy(float),
        "moon_distance_km": sm["Moon Dist (km)"].to_numpy(float),
        "kp_daily_mean": kp["Kp_daily_mean"].to_numpy(float),
        "lotto655_draw_sum": nums.sum(axis=1).astype(float),
    }
    # declared preprocessing: standardize each series (scale-free scores;
    # avoids epsilon swamping at the tidal series' 1e-15 physical scale)
    series = {k: (v - v.mean()) / v.std() for k, v in series.items()}
    return series, nums, tid, sm, kp, dr


# ------------------------------------------- subset-to-whole on a series
def knn_time_predict(t_S, y_S, t_H, k=2):
    """k-NN (inverse-distance weighted) regression on the time index.
    Learns nothing but temporal smoothness — exactly the claimed structure."""
    preds = np.empty(len(t_H))
    for i, t in enumerate(t_H):
        d = np.abs(t_S - t).astype(float)
        idx = np.argsort(d)[:k]
        w = 1.0 / (d[idx] + 1.0)
        preds[i] = np.sum(w * y_S[idx]) / np.sum(w)
    return preds


def recovery_point(y, frac, rng, m=M_NULL):
    n = len(y)
    t = np.arange(n)
    k = max(3, int(round(frac * n)))
    S = np.sort(rng.choice(n, size=k, replace=False))
    H = np.setdiff1d(t, S)
    rmse = lambda yy: float(np.sqrt(np.mean(
        (knn_time_predict(S, yy[S], H) - yy[H]) ** 2)))
    obs = -rmse(y)
    nulls = [-rmse(y[rng.permutation(n)]) for _ in range(m)]
    nulls = np.asarray(nulls)
    p = (1 + np.sum(nulls >= obs)) / (m + 1)
    z = (obs - nulls.mean()) / (nulls.std() + 1e-12)
    return p, z


def run_recovery_curves(series):
    rng = np.random.default_rng(SEED)
    out = {}
    for name, y in series.items():
        curve = []
        for frac in SUBSET_FRACS:
            ps, zs = [], []
            for _ in range(REPEATS):
                p, z = recovery_point(y, frac, rng)
                ps.append(p); zs.append(z)
            curve.append({"frac": frac,
                          "median_p": float(np.median(ps)),
                          "frac_p_le_05": float(np.mean(np.array(ps) <= 0.05)),
                          "mean_null_adjusted_z": float(np.mean(zs))})
        out[name] = {"n": int(len(y)), "curve": curve,
                     "null": "within-series value permutation",
                     "model": "k-NN(2) on time index", "repeats": REPEATS}
    return out


# --------------------------------- lotto presence-matrix frequency recovery
def draw_uniform(rng, n_draws, P=55):
    M = np.zeros((n_draws, P), dtype=bool)
    for i in range(n_draws):
        M[i, rng.choice(P, size=6, replace=False)] = True
    return M


def presence_loglik(M):
    """Subset-to-whole: estimate per-number probs from S, score held-out
    draws' mean log-likelihood. Skill = lift over the uniform baseline."""
    return M


def presence_point(M, frac, rng, m=199):
    n, P = M.shape

    def skill(Mat, S, H):
        probs = (Mat[S].sum(0) + 1.0) / (len(S) * 6 + P)   # Laplace smoothing
        probs = probs / probs.sum() * 6                     # expected 6 per draw
        ll = np.log(np.clip(probs, 1e-9, 1))[None, :] * Mat[H]
        return float(ll.sum(1).mean()) - float(
            np.log(6.0 / P) * 6)                            # lift vs uniform

    k = max(3, int(round(frac * n)))
    S = rng.choice(n, size=k, replace=False)
    H = np.setdiff1d(np.arange(n), S)
    obs = skill(M, S, H)
    nulls = []
    for _ in range(m):                                      # constrained generator (A1)
        Mn = draw_uniform(rng, n, P)
        nulls.append(skill(Mn, S, H))
    nulls = np.asarray(nulls)
    p = (1 + np.sum(nulls >= obs)) / (m + 1)
    z = (obs - nulls.mean()) / (nulls.std() + 1e-12)
    return p, z


def run_presence_recovery(nums, P=55):
    rng = np.random.default_rng(SEED + 1)
    M = np.zeros((len(nums), P), dtype=bool)
    for i, row in enumerate(nums):
        M[i, row - 1] = True
    curve = []
    for frac in SUBSET_FRACS:
        ps, zs = [], []
        for _ in range(REPEATS):
            p, z = presence_point(M, frac, rng)
            ps.append(p); zs.append(z)
        curve.append({"frac": frac, "median_p": float(np.median(ps)),
                      "frac_p_le_05": float(np.mean(np.array(ps) <= 0.05)),
                      "mean_null_adjusted_z": float(np.mean(zs))})
    return {"n_draws": int(len(nums)), "curve": curve,
            "null": "6-of-55 uniform constrained generator (A1)",
            "model": "Laplace-smoothed per-number frequencies from S",
            "note": "C9: includes the known #45 era rows; trace-to-rows applies to any flag"}


# ------------------------------------------------- date-paired CCA tests
def draw_features(dr):
    nums = dr[[f"N{i}" for i in range(1, 7)]].to_numpy(float)
    srt = np.sort(nums, axis=1)
    return pd.DataFrame({
        "Date": dr["Date"].to_numpy(),
        "sum": nums.sum(1), "min": srt[:, 0], "max": srt[:, -1],
        "range": srt[:, -1] - srt[:, 0],
        "odd_count": (nums.astype(int) % 2).sum(1),
        "mean_gap": np.diff(srt, axis=1).mean(1),
    })


def ridge_cca_heldout(X, Y, rng, m=199, train_frac=0.6, gamma=0.1):
    n = len(X)
    ntr = int(train_frac * n)
    Xtr, Ytr, Xte, Yte = X[:ntr], Y[:ntr], X[ntr:], Y[ntr:]   # time-ordered split (A5)

    def whiten(Mtr):
        C = np.cov(Mtr.T) + gamma * np.eye(Mtr.shape[1])
        w, V = np.linalg.eigh(C)
        return V @ np.diag(w ** -0.5) @ V.T

    Wx, Wy = whiten(Xtr), whiten(Ytr)
    Cxy = (Xtr - Xtr.mean(0)).T @ (Ytr - Ytr.mean(0)) / ntr
    U, s, Vt = np.linalg.svd(Wx @ Cxy @ Wy)
    u = (Xte - Xtr.mean(0)) @ (Wx @ U[:, 0])
    v = (Yte - Ytr.mean(0)) @ (Wy @ Vt[0])
    obs = float(np.corrcoef(u, v)[0, 1])
    nulls = [float(np.corrcoef(u, v[rng.permutation(len(v))])[0, 1])
             for _ in range(m)]
    nulls = np.asarray(nulls)
    p = (1 + np.sum(nulls >= obs)) / (m + 1)
    return {"heldout_rho1": obs, "p_shuffled_pairing": float(p),
            "null_mean": float(nulls.mean()), "null_q95": float(np.quantile(nulls, 0.95)),
            "n_train": ntr, "n_test": int(n - ntr), "m_perm": m}


def run_cca_tests(tid, sm, kp, dr):
    rng = np.random.default_rng(SEED + 2)
    df = draw_features(dr)
    tid_c = tid[["Date", "Lunar tidal accel (g)", "Solar tidal accel (g)",
                 "Total tidal accel (g)"]]
    sm_c = sm[["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)",
               "Moon Alt (deg)", "Sun Alt (deg)"]]
    kp_c = kp[["Date", "Kp_daily_mean", "Kp_daily_max"]]
    cov = tid_c.merge(sm_c, on="Date").merge(kp_c, on="Date")
    cov_cols = ["Total tidal accel (g)", "Moon Dist (km)", "Moon Illum (0-1)",
                "Sun Dist (km)", "Kp_daily_mean", "Kp_daily_max"]
    paired = df.merge(cov, on="Date").sort_values("Date")
    X = paired[["sum", "min", "max", "range", "odd_count", "mean_gap"]].to_numpy(float)
    Y = paired[cov_cols].to_numpy(float)
    res_draws = ridge_cca_heldout(X, Y, rng)
    res_draws["pairing"] = "6/55 draw features vs physical covariates, by date"

    # real-data positive control: tidal accel features vs sun/moon ephemerides
    both = tid_c.merge(sm_c, on="Date").sort_values("Date")
    Xt = both[["Lunar tidal accel (g)", "Solar tidal accel (g)",
               "Total tidal accel (g)"]].to_numpy(float)
    Yt = both[["Moon Dist (km)", "Sun Dist (km)", "Moon Illum (0-1)",
               "Moon Alt (deg)", "Sun Alt (deg)"]].to_numpy(float)
    res_tidal = ridge_cca_heldout(Xt, Yt, rng)
    res_tidal["pairing"] = "tidal accelerations vs sun/moon ephemerides, by date (known mechanism)"
    return {"H_R3_draws_vs_covariates": res_draws,
            "H_R4_tidal_vs_ephemerides_positive_control": res_tidal}


# -------------------------------------------------------------------- main
def main():
    import sys
    stages = sys.argv[1:] or ["curves", "presence", "cca"]
    series, nums, tid, sm, kp, dr = load_series()
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "registered_expectations": ["H-R1 physical series beat null",
                                                    "H-R2 lotto flat on null line",
                                                    "H-R3 draws-vs-covariates null",
                                                    "H-R4 tidal-vs-ephemerides positive"],
                        "subset_fracs": SUBSET_FRACS}
    if "curves" in stages:
        results["recovery_curves"] = run_recovery_curves(series)
        print("recovery curves done", flush=True)
    if "presence" in stages:
        results["lotto655_presence_recovery"] = run_presence_recovery(nums)
        print("presence recovery done", flush=True)
    if "cca" in stages:
        results["paired_cca"] = run_cca_tests(tid, sm, kp, dr)
        print("cca done", flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
