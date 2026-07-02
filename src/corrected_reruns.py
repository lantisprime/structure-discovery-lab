#!/usr/bin/env python3
"""Corrected implementations for AUDIT_CORRECTNESS_2026-07-02 findings
M-1, M-2, M-3, M-4 (+ metadata corrections), honoring the frozen-file policy:
the flagged files are FROZEN HISTORICAL RECORDs, so the corrected versions
live here and frozen modules are imported read-only.

Stages (each seeded, deterministic):
  m1_note        add-one p-value estimator + monotonicity verdict-impact note
  m2_presence    presence-matrix completion with CONSTRAINED 6-of-P nulls
                 (replaces col_permuted, which broke the row-sum invariant)
                 + side-by-side calibration control (old vs new null on
                 synthetic H0 data)
  m3_cca         ridge CCA with train-moment standardization (shadow rerun of
                 H_R3 / H_R4; exploratory — registered rerun still required)
  m4_attribution graphon attribution with the lead ball's row/col REMOVED
                 from the centered matrix and 6-of-(P-1) constrained nulls
                 (the frozen version injects a deterministic -c stripe and is
                 anticonservative toward "NEW structure")

Output: results/corrected_reruns_2026-07-02.json
Status: exploratory / audit-remediation evidence. Any promotion of these
numbers into published claims requires a registered rerun (see
docs/AUDIT_RESOLUTION_2026-07-02.md).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

from relational_admission import soft_impute                      # noqa: E402
from relational_batch5 import uniform_draws                       # noqa: E402
from graphon_cooccurrence import load as load_graphon, indicators, stats_pair  # noqa: E402
from remediation_r1 import load_game, GAMES                       # noqa: E402

SEED = 20260702
OUT = os.path.join(ROOT, "results", "corrected_reruns_2026-07-02.json")


# ---- M-1: the only allowed MC p-value ---------------------------------------
def mc_p_addone(obs, null, two_sided=True):
    """Phipson–Smyth add-one Monte Carlo p (replaces markov_analysis.mc_p,
    cross_theorem_correlation.py:84, powerlaw_sweep.py:51,58 — all of which
    compute c/m and can return an invalid p=0)."""
    null = list(null)
    m = len(null)
    if two_sided:
        mu = sum(null) / m
        c = sum(1 for v in null if abs(v - mu) >= abs(obs - mu))
    else:
        c = sum(1 for v in null if v >= obs)
    return (1 + c) / (1 + m)


M1_NOTE = {
    "estimator": "p = (1 + #{null >= obs}) / (1 + m)",
    "replaces": ["markov_analysis.mc_p (NSIM=4000)",
                 "cross_theorem_correlation.py:84 (NSIM=400)",
                 "powerlaw_sweep.py:51,58 (NSIM=600)"],
    "verdict_impact": (
        "add-one is strictly monotone increasing in p (p' = (c+1)/(m+1) > c/m); "
        "it can only weaken evidence, never strengthen it. The frozen runs' "
        "minimum recorded p-values were all non-significant already "
        "(markov min 0.053 of 15 tests; cross-theorem 0.09-0.93; powerlaw "
        "min 0.017 reported n.s. vs its multiplicity), so no published verdict "
        "changes; the defect matters for FUTURE reuse of those instruments, "
        "which must import mc_p_addone from this module."),
}


# ---- M-2: presence-matrix completion, constrained null ----------------------
def presence_skill(M, mask):
    L, col_mean = soft_impute(M, mask)
    rmse_model = float(np.sqrt(np.mean((L[~mask] - M[~mask]) ** 2)))
    rmse_marg = float(np.sqrt(np.mean(
        (col_mean[None, :].repeat(len(M), 0)[~mask] - M[~mask]) ** 2)))
    return rmse_marg - rmse_model


def presence_matrix(nums, P):
    M = np.zeros((len(nums), P))
    for i, r in enumerate(nums):
        M[i, r - 1] = 1.0
    return M


def p_perm_addone(obs, nulls):
    return float((1 + np.sum(np.asarray(nulls) >= obs)) / (1 + len(nulls)))


def run_presence_mc_v2(m_null=199):
    """remediation_r1.run_presence_mc with the null ensemble corrected:
    null matrices are CONSTRAINED uniform 6-of-P draws (same hard row-sum-6
    invariant as the data), same frozen mask — not within-column permutations
    (which produce Poisson-binomial row sums, a different ensemble even
    under H0)."""
    rng = np.random.default_rng(SEED + 1)
    out = {}
    for g, P in GAMES.items():
        nums = load_game(g)
        M = presence_matrix(nums, P)
        mask = rng.uniform(size=M.shape) < 0.6          # frozen design variable
        obs = presence_skill(M, mask)
        nulls = [presence_skill(presence_matrix(
            uniform_draws(rng, len(nums), P), P), mask)   # already 1-indexed
            for _ in range(m_null)]
        out[g] = {"skill_over_marginal": obs, "p": p_perm_addone(obs, nulls)}
    minp = min(v["p"] for v in out.values())
    sidak = 1 - 0.95 ** (1 / 5)
    return {"per_game": out, "min_p": minp, "sidak": sidak,
            "joint_verdict_null": bool(minp > sidak),
            "m_null": m_null, "observed_frac": 0.6,
            "null": "constrained 6-of-P uniform, frozen mask (audit M-2)"}


def presence_calibration(n_trials=15, m_null=39, T=155, P=55):
    """Side-by-side calibration on synthetic H0 data: observed matrix is a
    constrained draw; p computed against (a) the corrected constrained null,
    (b) the old within-column-permutation null. Under H0 both should give
    ~U(0,1) p's; a shifted (b) demonstrates the false-positive channel."""
    from relational_admission import col_permuted
    rng = np.random.default_rng(SEED + 2)
    ps_new, ps_old = [], []
    for _ in range(n_trials):
        M = presence_matrix(uniform_draws(rng, T, P), P)
        mask = rng.uniform(size=M.shape) < 0.6
        obs = presence_skill(M, mask)
        nn = [presence_skill(presence_matrix(
            uniform_draws(rng, T, P), P), mask) for _ in range(m_null)]
        no = [presence_skill(col_permuted(M, rng), mask) for _ in range(m_null)]
        ps_new.append(p_perm_addone(obs, nn))
        ps_old.append(p_perm_addone(obs, no))
    return {"n_trials": n_trials, "m_null": m_null,
            "constrained_null_p": ps_new, "col_permuted_null_p": ps_old,
            "constrained_mean_p": float(np.mean(ps_new)),
            "col_permuted_mean_p": float(np.mean(ps_old)),
            "note": ("H0 observed vs both nulls; mean p far from 0.5 for the "
                     "old null = ensemble mismatch (audit M-2). Measured "
                     "direction is MASKING/conservative (mean p 0.925, not "
                     "small-p inflation): the old null overstates achievable "
                     "completion skill, so real structure would be hidden and "
                     "the meta panel fed non-uniform high p's")}


# ---- M-3: standardized ridge CCA ---------------------------------------------
def ridge_cca_heldout_std(X, Y, rng, m=199, train_frac=0.6, gamma=0.1):
    """relational_first_run.ridge_cca_heldout with the audit M-3 fix: every
    column of X and Y is z-scored with TRAIN-set moments before whitening, so
    gamma=0.1 is relative to unit variance and no covariate is annihilated by
    its physical units (Sun km ~1e16 variance vs tidal accel ~1e-15)."""
    n = len(X)
    ntr = int(train_frac * n)

    def std(A):
        mu, sd = A[:ntr].mean(0), A[:ntr].std(0)
        sd[sd == 0] = 1.0
        return (A - mu) / sd

    X, Y = std(np.asarray(X, float)), std(np.asarray(Y, float))
    Xtr, Ytr, Xte, Yte = X[:ntr], Y[:ntr], X[ntr:], Y[ntr:]

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
    nulls = np.asarray([float(np.corrcoef(u, v[rng.permutation(len(v))])[0, 1])
                        for _ in range(m)])
    return {"heldout_rho1": obs,
            "p_shuffled_pairing": float((1 + np.sum(nulls >= obs)) / (m + 1)),
            "null_q95": float(np.quantile(nulls, 0.95)),
            "n_train": ntr, "n_test": int(n - ntr), "m_perm": m,
            "standardized": True}


def run_cca_std_shadow():
    """Shadow rerun of H_R3 (draws vs covariates) and H_R4 (tidal vs
    ephemerides positive control) under the standardized CCA."""
    import pandas as pd
    from relational_first_run import draw_features
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))
    dr = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    dr = dr[dr["Game"] == "Grand Lotto 6/55"].sort_values("Date")
    rng = np.random.default_rng(SEED + 3)
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
    hr3 = ridge_cca_heldout_std(X, Y, rng)
    both = tid_c.merge(sm_c, on="Date").sort_values("Date")
    Xt = both[["Lunar tidal accel (g)", "Solar tidal accel (g)",
               "Total tidal accel (g)"]].to_numpy(float)
    Yt = both[["Moon Dist (km)", "Sun Dist (km)", "Moon Illum (0-1)",
               "Moon Alt (deg)", "Sun Alt (deg)"]].to_numpy(float)
    hr4 = ridge_cca_heldout_std(Xt, Yt, rng)
    return {"H_R3_draws_vs_covariates_std": hr3,
            "H_R4_tidal_vs_ephemerides_std": hr4,
            "note": ("shadow rerun; frozen v1 gave HR3 rho=0.110 p=0.17 (null) "
                     "and HR4 rho=0.9977 p=0.005 (mechanism); the fix targets "
                     "POWER for small-unit covariates, calibration was intact")}


# ---- M-4: graphon attribution, corrected ------------------------------------
def attribute_v2(name, lead_ball_1idx, K=999):
    """Corrected attribution re-test: does structure persist after removing
    the lead ball? Fixes vs frozen attribute():
      (a) the lead ball's row/col is REMOVED from the co-occurrence matrix
          (frozen version kept an all-zero column that the exact centering
          turned into a deterministic -c stripe, inflating the norm);
      (b) nulls are constrained 6-of-(P-1) draws on the REMAINING balls;
      (c) K=999 so the floor (0.001) <= threshold/2 (0.00125)."""
    rng = np.random.default_rng(SEED + 4)
    draws = load_graphon()[name]                 # 0-indexed
    from graphon_cooccurrence import POOL
    P = POOL[name]
    lead = lead_ball_1idx - 1
    mask = ~(draws == lead).any(axis=1)
    sub = draws[mask]
    # relabel remaining balls 0..P-2
    remap = np.full(P, -1)
    remap[np.setdiff1d(np.arange(P), [lead])] = np.arange(P - 1)
    sub2 = remap[sub]
    assert (sub2 >= 0).all()
    b1, _ = stats_pair(indicators(sub2, P - 1), P - 1)
    nulls = np.empty(K)
    for j in range(K):
        m = rng.random((len(sub2), P - 1)).argsort(axis=1)[:, :6]
        nulls[j], _ = stats_pair(indicators(m, P - 1), P - 1)
    p = float((1 + np.sum(nulls >= b1)) / (K + 1))
    return {"game": name, "lead_ball": lead_ball_1idx,
            "rows_removed": int(len(draws) - len(sub2)),
            "B1_after_removal": float(b1), "p": p, "K": K,
            "floor": round(1 / (K + 1), 4), "threshold": 0.0025,
            "verdict": ("fire persists: NEW structure" if p < 0.0025 else
                        "fire dissolves after lead-ball removal"),
            "caveat": ("consistent with same-driving-rows (C9) but does not "
                       "exclude reduced power at the smaller T; corroborated "
                       "independently by rho(lambda_max, B1)=0.988 under H0 "
                       "(families.json) — the two flags were one instrument"),
            "null": "constrained 6-of-(P-1) on remaining balls (audit M-4)"}


STAGES = {
    "m1_note": lambda: M1_NOTE,
    "m2_presence": run_presence_mc_v2,
    "m2_calibration": presence_calibration,
    "m3_cca": run_cca_std_shadow,
    "m4_attribution": lambda: attribute_v2("Grand Lotto 6/55", 45),
}


def main(stages):
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for s in stages:
        print(f"== {s}")
        res[s] = STAGES[s]()
        json.dump(res, open(OUT, "w"), indent=2)
        print(json.dumps(res[s], indent=1, default=str)[:600])
    print("written", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main(sys.argv[1:] or list(STAGES))
