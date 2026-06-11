#!/usr/bin/env python3
"""
Pressure covariate run (registered in DATASET.md §6 / RESULTS_PRESSURE.md).

Registered expectations, declared before execution:
  H-P1  The pressure series itself is structured: subset-to-whole recovery curve
        rises above the within-series permutation null (autocorrelated weather).
  H-P2  Draw outcomes do not couple to pressure: per-game date-paired held-out
        CCA (draw features vs [P_mean, P_min, P_max, P_range]) is null under the
        shuffled-pairing null, all five games. Additionally a simple permutation
        test of corr(draw sum, P_mean) per game is null.

Output: results/relational_pressure.json
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_pressure.json")
SEED = 20260611

import sys
sys.path.insert(0, HERE)
from relational_first_run import recovery_point, ridge_cca_heldout, SUBSET_FRACS, REPEATS

GAMES = ["Lotto 6/42", "Mega Lotto 6/45", "Super Lotto 6/49",
         "Grand Lotto 6/55", "Ultra Lotto 6/58"]


def main():
    rng = np.random.default_rng(SEED + 70)
    pr = pd.read_csv(os.path.join(ROOT, "datasets/openmeteo-pressure-manila/pressure_daily.csv"))
    pr["P_range"] = pr["P_msl_max_hPa"] - pr["P_msl_min_hPa"]

    # H-P1: recovery curve of the pressure series
    y = pr["P_msl_mean_hPa"].to_numpy(float)
    y = (y - y.mean()) / y.std()
    curve = []
    for frac in SUBSET_FRACS:
        ps, zs = [], []
        for _ in range(REPEATS):
            p, z = recovery_point(y, frac, rng)
            ps.append(p); zs.append(z)
        curve.append({"frac": frac, "median_p": float(np.median(ps)),
                      "mean_null_adjusted_z": float(np.mean(zs))})

    # H-P2: per-game coupling tests
    draws = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    per_game = {}
    for g in GAMES:
        rows = draws[draws["Game"] == g].sort_values("Date")
        nums = rows[[f"N{i}" for i in range(1, 7)]].to_numpy(float)
        srt = np.sort(nums, axis=1)
        feats = pd.DataFrame({"Date": rows["Date"].to_numpy(),
                              "sum": nums.sum(1), "min": srt[:, 0],
                              "max": srt[:, -1], "range": srt[:, -1] - srt[:, 0],
                              "odd": (nums.astype(int) % 2).sum(1),
                              "gap": np.diff(srt, axis=1).mean(1)})
        paired = feats.merge(pr, on="Date").sort_values("Date")
        X = paired[["sum", "min", "max", "range", "odd", "gap"]].to_numpy(float)
        Y = paired[["P_msl_mean_hPa", "P_msl_min_hPa", "P_msl_max_hPa",
                    "P_range"]].to_numpy(float)
        cca = ridge_cca_heldout(X, Y, rng)
        # scalar check: corr(draw sum, P_mean), shuffled-pairing null
        s = paired["sum"].to_numpy(float); pm = paired["P_msl_mean_hPa"].to_numpy(float)
        obs = float(np.corrcoef(s, pm)[0, 1])
        nulls = [abs(np.corrcoef(s, pm[rng.permutation(len(pm))])[0, 1])
                 for _ in range(199)]
        p_scalar = float((1 + np.sum(np.asarray(nulls) >= abs(obs))) / 200)
        per_game[g] = {"n_paired": int(len(paired)),
                       "cca_heldout_rho1": cca["heldout_rho1"],
                       "cca_p": cca["p_shuffled_pairing"],
                       "corr_sum_pressure": obs, "p_scalar": p_scalar}

    m = len(per_game)
    sidak = 1 - 0.95 ** (1 / m)
    min_cca = min(v["cca_p"] for v in per_game.values())
    results = {"_meta": {"date": "2026-06-11", "seed": SEED + 70,
                         "registered": ["H-P1 pressure structured",
                                        "H-P2 draws-vs-pressure null x5"]},
               "HP1_pressure_recovery": {"n": int(len(y)), "curve": curve},
               "HP2_per_game": per_game,
               "HP2_min_cca_p": float(min_cca),
               "HP2_sidak": float(sidak),
               "HP2_joint_null": bool(min_cca > sidak)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)
    for k, v in per_game.items():
        print(k, v)
    print("HP1 tail z:", [c["mean_null_adjusted_z"] for c in curve][-3:])
    print("DONE")


if __name__ == "__main__":
    main()
