#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""
Remediation batch R1 — fixes for ADVERSARIAL_REVIEW.md findings C3, M1-M4, M7.
Registered protocol change (bias fix): NO outcome expectations are declared for
any discovery test below. Each test states claim type, null, and decision rule
only. Mechanism predictions appear ONLY in instrument-validity controls.

Stages: presence_mc, floors_lmax, floors_gw, gate_quarter, gate_gw,
        pc_r1, pc_r2r6, pc_r3, pc_r4, pc_r5, pc_r7, sensitivity, cca_splits
Output: results/remediation_r1.json (merged per stage)
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "remediation_r1.json")
SEED = 20260611

sys.path.insert(0, HERE)
from relational_admission import (mmd_pvalue, soft_impute, col_permuted,
                                  cca_trial, tda_trial, circle_cloud,
                                  nystrom_trial, swiss_roll, run_r2 as _unused,
                                  gw_distortion, matched_gaussian, p_perm as p_adm,
                                  sbm_graph, rewired, spectral_distance)
from relational_batch5 import (GameSpec, cooccurrence, uniform_draws, pair_test,
                               p_perm, std_spectrum, delay_embed)
from relational_batch7 import gw_test, embed_series
from relational_first_run import ridge_cca_heldout

GAMES = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}


def load_game(g, exclude_suspicious=False, verified_only=False):
    d = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    rows = d[d["Game"] == g].sort_values("Date")
    if exclude_suspicious:
        rows = rows[rows["Status"] != "suspicious_or_needs_review"]
    if verified_only:
        rows = rows[rows["Status"].isin(["two_source_verified", "official_verified",
                                         "two_source_verified(spot)"])]
    return rows[[f"N{i}" for i in range(1, 7)]].to_numpy(int)


# ---- C3: presence-matrix subset-to-whole, correct claim type (R7) ----------
def run_presence_mc():
    """Matrix completion on the binary presence matrix. Claim type:
    subset-to-whole reconstruction (framework §1.2 row 4). Nulls: (a) column-
    marginal baseline, (b) permuted-within-column matrix, same mask (m=29).
    Decision rule: p<=Sidak(m=5 games). No outcome expectation declared."""
    rng = np.random.default_rng(SEED + 90)
    out = {}
    for g, P in GAMES.items():
        nums = load_game(g)
        M = np.zeros((len(nums), P))
        for i, r in enumerate(nums):
            M[i, r - 1] = 1.0
        mask = rng.uniform(size=M.shape) < 0.6
        L, col_mean = soft_impute(M, mask)
        rmse_model = float(np.sqrt(np.mean((L[~mask] - M[~mask]) ** 2)))
        rmse_marg = float(np.sqrt(np.mean((col_mean[None, :].repeat(len(M), 0)[~mask]
                                           - M[~mask]) ** 2)))
        obs = rmse_marg - rmse_model            # skill over marginal baseline
        nulls = []
        for _ in range(199):
            Mn = col_permuted(M, rng)
            Ln, cmn = soft_impute(Mn, mask)
            rm = float(np.sqrt(np.mean((Ln[~mask] - Mn[~mask]) ** 2)))
            rb = float(np.sqrt(np.mean((cmn[None, :].repeat(len(Mn), 0)[~mask]
                                        - Mn[~mask]) ** 2)))
            nulls.append(rb - rm)
        out[g] = {"skill_over_marginal": obs, "p": p_perm(obs, nulls),
                  "rmse_model": rmse_model, "rmse_marginal": rmse_marg}
    minp = min(v["p"] for v in out.values())
    sidak = 1 - 0.95 ** (1 / 5)
    return {"per_game": out, "min_p": minp, "sidak": sidak,
            "joint_verdict_null": bool(minp > sidak),
            "claim_type": "subset-to-whole reconstruction (corrects review finding C3)",
            "m_null": 199, "observed_frac": 0.6}


# ---- M3: floor-compliant reruns --------------------------------------------
def run_floors_lmax():
    """Per-game lambda_max at m=399 (floor 0.0025 <= Sidak(m=5)/2 = 0.0051)."""
    rng = np.random.default_rng(SEED + 91)
    out = {}
    for g, P in GAMES.items():
        nums = load_game(g)
        gs = GameSpec(rng, len(nums), P, g)
        _, lmax = gs.spectrum(nums)
        nulls = [std_spectrum(cooccurrence(uniform_draws(rng, len(nums), P), P),
                              gs.mu, gs.sd)[1] for _ in range(999)]
        out[g] = {"lambda_max": lmax, "p": p_perm(lmax, nulls)}
    sidak = 1 - 0.95 ** (1 / 5)
    return {"per_game": out, "sidak": sidak, "m_null": 999,
            "floor": 1 / 1000,
            "n_corrected_rejections": int(sum(v["p"] <= sidak for v in out.values()))}


def run_floors_gw():
    """B7-3 GW pairs at m=99 (floor 0.01)."""
    rng = np.random.default_rng(SEED + 92)
    pr = pd.read_csv(os.path.join(ROOT, "datasets/openmeteo-pressure-manila/pressure_daily.csv"))
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    dr = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    dr = dr[dr["Game"] == "Grand Lotto 6/55"].sort_values("Date")
    E = {"pressure": embed_series(pr["P_msl_mean_hPa"].to_numpy(float)),
         "tidal": embed_series(tid["Total tidal accel (g)"].to_numpy(float)),
         "moon": embed_series(sm["Moon Dist (km)"].to_numpy(float)),
         "lotto655_sum": embed_series(dr[[f"N{i}" for i in range(1, 7)]]
                                      .to_numpy(float).sum(1))}
    out = {}
    for a, b in [("tidal", "moon"), ("pressure", "lotto655_sum"),
                 ("pressure", "tidal")]:
        out[f"{a}|{b}"] = gw_test(np.random.default_rng(SEED + 92), E[a], E[b], m=99)
    return {"pairs": out, "m_null": 99, "floor": 0.01}


# ---- M2: gates at n=200 -----------------------------------------------------
def run_gate_quarter(half):
    rng = np.random.default_rng(SEED + 93 + half)
    gs = GameSpec(rng, 39, 55, "quarter-shape")
    pvals = []
    for _ in range(100):
        A = uniform_draws(rng, 39, 55); B = uniform_draws(rng, 39, 55)
        obs, nulls = pair_test(rng, gs, A, gs, B, m=49)
        pvals.append(p_perm(obs, nulls))
    return pvals


def run_gate_gw(half):
    rng = np.random.default_rng(SEED + 95 + half)
    pvals = []
    for _ in range(100):
        A = rng.normal(size=(120, 3)); B = rng.normal(size=(120, 3))
        pvals.append(gw_test(rng, A, B, m=19)["p"])
    return pvals


def gate_summary(pvals):
    pvals = np.asarray(pvals)
    ks = stats.kstest(pvals, "uniform")
    n = len(pvals)
    fpr = float(np.mean(pvals <= 0.05))
    se3 = 3 * np.sqrt(0.05 * 0.95 / n)
    return {"n_trials": n, "fpr_at_alpha": fpr, "ks_p": float(ks.pvalue),
            "band_3se": round(se3, 4),
            "gate_passed": bool(abs(fpr - 0.05) <= se3 and ks.pvalue > 0.01)}


# ---- M1: frozen power curves (declared grids, instruments unchanged) -------
def run_pc_r1():
    rng = np.random.default_rng(SEED + 100)
    grid = {}
    for shift in [0.25, 0.5, 0.75, 1.0]:
        ps = []
        for _ in range(50):
            X = rng.normal(size=(80, 5))
            Y = rng.normal(size=(80, 5)); Y[:, 0] += shift
            ps.append(mmd_pvalue(X, Y, rng, m=99))
        grid[str(shift)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"family": "R1 MMD, n=80,d=5 (frozen)", "power_by_shift": grid}


def run_pc_r2r6():
    rng = np.random.default_rng(SEED + 101)
    g2 = {}
    for noise in [0.1, 0.3, 0.5]:
        ps = []
        for _ in range(20):
            A = circle_cloud(rng, 50, noise, 2); B = circle_cloud(rng, 50, noise, 3)
            obs = -gw_distortion(A, B)
            nulls = [-gw_distortion(A, matched_gaussian(rng, B)) for _ in range(19)]
            ps.append(p_adm(obs, nulls))
        g2[str(noise)] = float(np.mean(np.asarray(ps) <= 0.05))
    g6 = {}
    for noise in [0.05, 0.2, 0.5]:
        ps = [nystrom_trial(swiss_roll(rng, 150, noise=noise), rng)
              for _ in range(25)]
        g6[str(noise)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"R2_gw_power_by_circle_noise": g2,
            "R6_nystrom_power_by_swissroll_noise": g6}


def run_pc_r3():
    rng = np.random.default_rng(SEED + 102)
    grid = {}
    for noise in [0.7, 1.2, 1.8, 2.5]:
        ps = []
        for _ in range(50):
            z = rng.normal(size=(160, 3))
            X = z @ rng.normal(size=(3, 15)) + noise * rng.normal(size=(160, 15))
            Y = z @ rng.normal(size=(3, 15)) + noise * rng.normal(size=(160, 15))
            pv, _ = cca_trial(X, Y, rng)
            ps.append(pv)
        grid[str(noise)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"family": "R3 CCA (frozen)", "power_by_noise": grid}


def run_pc_r4():
    rng = np.random.default_rng(SEED + 103)
    grid = {}
    for noise in [0.15, 0.30, 0.50]:
        ps = [tda_trial(circle_cloud(rng, 100, noise, 2), rng) for _ in range(30)]
        grid[str(noise)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"family": "R4 TDA maxH1 (frozen)", "power_by_circle_noise": grid}


def run_pc_r5():
    rng = np.random.default_rng(SEED + 104)
    grid = {}
    for p_in in [0.10, 0.15, 0.20, 0.30]:
        ps = []
        for _ in range(25):
            GA = sbm_graph(rng, 120, p_in=p_in, p_out=0.02)
            GB = sbm_graph(rng, 100, p_in=p_in, p_out=0.02)
            obs = -spectral_distance(GA, GB)
            nulls = [-spectral_distance(GA, rewired(GB, rng)) for _ in range(19)]
            ps.append(p_adm(obs, nulls))
        grid[str(p_in)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"family": "R5 spectra bottom-12 (frozen), p_out=0.02",
            "power_by_p_in": grid}


def run_pc_r7():
    rng = np.random.default_rng(SEED + 105)
    from relational_admission import completion_trial
    grid = {}
    for noise in [0.1, 0.3, 0.6, 1.0]:
        ps = []
        for _ in range(25):
            M = (rng.normal(size=(60, 2)) @ rng.normal(size=(2, 40))
                 + noise * rng.normal(size=(60, 40)))
            ps.append(completion_trial(M, rng))
        grid[str(noise)] = float(np.mean(np.asarray(ps) <= 0.05))
    return {"family": "R7 SoftImpute rank2 (frozen)", "power_by_noise": grid}


# ---- M4: three-regime sensitivity ------------------------------------------
def half_corr(nums, P, rng, m=199):
    n = len(nums); h = n // 2

    def dev(dr, T):
        c = np.zeros(P)
        for r in dr:
            c[r - 1] += 1
        return c - T * 6.0 / P

    obs = float(np.corrcoef(dev(nums[:h], h), dev(nums[h:], n - h))[0, 1])
    nulls = [float(np.corrcoef(dev(uniform_draws(rng, h, P), h),
                               dev(uniform_draws(rng, n - h, P), n - h))[0, 1])
             for _ in range(m)]
    return obs, p_perm(obs, nulls), n


def run_sensitivity():
    rng = np.random.default_rng(SEED + 110)
    out = {}
    for g, P in GAMES.items():
        row = {}
        for regime, kw in [("all", {}), ("ex_suspicious", {"exclude_suspicious": True}),
                           ("verified_only", {"verified_only": True})]:
            nums = load_game(g, **kw)
            if len(nums) < 20:
                row[regime] = {"n": int(len(nums)), "note": "too few rows"}
                continue
            c, p, n = half_corr(nums, P, rng)
            row[regime] = {"n": n, "corr": round(c, 3), "p": round(p, 3)}
        out[g] = row
    # 6/55 lambda_max ex-suspicious at m=399
    nums = load_game("Grand Lotto 6/55", exclude_suspicious=True)
    gs = GameSpec(rng, len(nums), 55, "655 ex-suspicious")
    _, lmax = gs.spectrum(nums)
    nulls = [std_spectrum(cooccurrence(uniform_draws(rng, len(nums), 55), 55),
                          gs.mu, gs.sd)[1] for _ in range(999)]
    out["lambda_max_655_ex_suspicious"] = {"lambda_max": lmax,
                                           "p": p_perm(lmax, nulls), "m_null": 399}
    return out


# ---- M7: multi-split CCA -----------------------------------------------------
def run_cca_splits():
    rng = np.random.default_rng(SEED + 111)
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))[
        ["Date", "Total tidal accel (g)"]]
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))[
        ["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)"]]
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))[
        ["Date", "Kp_daily_mean", "Kp_daily_max"]]
    pr = pd.read_csv(os.path.join(ROOT, "datasets/openmeteo-pressure-manila/pressure_daily.csv"))
    pr["P_range"] = pr["P_msl_max_hPa"] - pr["P_msl_min_hPa"]
    cov = tid.merge(sm, on="Date").merge(kp, on="Date").merge(pr, on="Date")
    cov_cols = [c for c in cov.columns if c != "Date"]
    d = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    out = {}
    for g in GAMES:
        rows = d[d["Game"] == g].sort_values("Date")
        nums = rows[[f"N{i}" for i in range(1, 7)]].to_numpy(float)
        srt = np.sort(nums, axis=1)
        feats = pd.DataFrame({"Date": rows["Date"].to_numpy(),
                              "sum": nums.sum(1), "min": srt[:, 0], "max": srt[:, -1],
                              "range": srt[:, -1] - srt[:, 0],
                              "odd": (nums.astype(int) % 2).sum(1),
                              "gap": np.diff(srt, axis=1).mean(1)})
        paired = feats.merge(cov, on="Date").sort_values("Date")
        X = paired[["sum", "min", "max", "range", "odd", "gap"]].to_numpy(float)
        Y = paired[cov_cols].to_numpy(float)
        splits = {}
        for tf in [0.5, 0.6, 0.7]:
            r = ridge_cca_heldout(X, Y, rng, train_frac=tf)
            splits[str(tf)] = {"rho1": round(r["heldout_rho1"], 3),
                               "p": round(r["p_shuffled_pairing"], 3)}
        out[g] = splits
    return {"per_game": out, "covariates": "all 9 (tidal+sunmoon+kp+pressure)",
            "decision_rule": "median p across splits vs Sidak m=5"}


STAGES = {"presence_mc": run_presence_mc, "floors_lmax": run_floors_lmax,
          "floors_gw": run_floors_gw,
          "gate_quarter_a": lambda: run_gate_quarter(0),
          "gate_quarter_b": lambda: run_gate_quarter(1),
          "gate_gw_a": lambda: run_gate_gw(0), "gate_gw_b": lambda: run_gate_gw(1),
          "pc_r1": run_pc_r1, "pc_r2r6": run_pc_r2r6, "pc_r3": run_pc_r3,
          "pc_r4": run_pc_r4, "pc_r5": run_pc_r5, "pc_r7": run_pc_r7,
          "sensitivity": run_sensitivity, "cca_splits": run_cca_splits}


def main():
    stages = sys.argv[1:]
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "protocol": "expectation-free: claim type + null + decision rule only",
                        "fixes": "ADVERSARIAL_REVIEW C3, M1-M4, M7"}
    for st in stages:
        res = STAGES[st]()
        if st.startswith("gate_"):
            base = st.rsplit("_", 1)[0]
            acc = results.get(base, {"pvals": []})
            acc["pvals"] = acc.get("pvals", []) + res
            acc.update(gate_summary(acc["pvals"]))
            results[base] = acc
        else:
            results[st] = res
        print(st, "done", flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
