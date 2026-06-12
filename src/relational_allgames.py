#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""
All-games extension (registered amendment to batch 5, same date): every per-game
relational test runs identically on all five PCSO games — 6/42, 6/45, 6/49,
6/55, 6/58 — not only 6/55.

Per game:
  - draw-sum subset-to-whole recovery curve (k-NN(2) on time index,
    within-series permutation null; identical to the first-run protocol)
  - presence-matrix frequency recovery (6-of-P constrained generator null, A1)
  - delay-embedding H1 topology existence test (tau=3, dim=3, permutation null)
  - date-paired CCA vs physical covariates (shuffled held-out pairing)

Registered expectation (declared before running, same as H-R2/H-R3): ALL of it
null for ALL five games. Any flag is traced to rows (C9) before reporting.

Stage args: one per game key (g42, g45, g49, g55, g58).
Output: results/relational_allgames.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_allgames.json")
SEED = 20260611

sys.path.insert(0, HERE)
from relational_first_run import (recovery_point, presence_point,
                                  ridge_cca_heldout, SUBSET_FRACS, REPEATS)
from relational_batch5 import delay_embed, max_h1, p_perm

GAMES = {"g42": ("Lotto 6/42", 42), "g45": ("Mega Lotto 6/45", 45),
         "g49": ("Super Lotto 6/49", 49), "g55": ("Grand Lotto 6/55", 55),
         "g58": ("Ultra Lotto 6/58", 58)}


def load(game_name):
    d = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    rows = d[d["Game"] == game_name].sort_values("Date")
    nums = rows[[f"N{i}" for i in range(1, 7)]].to_numpy(int)
    return rows, nums


def covariates():
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))
    tid_c = tid[["Date", "Total tidal accel (g)"]]
    sm_c = sm[["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)"]]
    kp_c = kp[["Date", "Kp_daily_mean", "Kp_daily_max"]]
    return tid_c.merge(sm_c, on="Date").merge(kp_c, on="Date")


def run_game(key):
    game_name, P = GAMES[key]
    rows, nums = load(game_name)
    rng = np.random.default_rng(SEED + hash(key) % 1000)

    # 1) draw-sum recovery curve
    y = nums.sum(1).astype(float)
    y = (y - y.mean()) / y.std()
    curve = []
    for frac in SUBSET_FRACS:
        ps, zs = [], []
        for _ in range(REPEATS):
            p, z = recovery_point(y, frac, rng)
            ps.append(p); zs.append(z)
        curve.append({"frac": frac, "median_p": float(np.median(ps)),
                      "mean_null_adjusted_z": float(np.mean(zs))})

    # 2) presence recovery
    M = np.zeros((len(nums), P), dtype=bool)
    for i, r in enumerate(nums):
        M[i, r - 1] = True
    pres = []
    for frac in SUBSET_FRACS:
        ps, zs = [], []
        for _ in range(REPEATS):
            p, z = presence_point(M, frac, rng)
            ps.append(p); zs.append(z)
        pres.append({"frac": frac, "median_p": float(np.median(ps)),
                     "mean_null_adjusted_z": float(np.mean(zs))})

    # 3) topology existence
    X = delay_embed(y)
    obs = max_h1(X)
    nulls = [max_h1(delay_embed(y[rng.permutation(len(y))])) for _ in range(99)]
    topo = {"max_h1_persistence": obs, "p": p_perm(obs, nulls),
            "null_q95": float(np.quantile(nulls, 0.95))}

    # 4) CCA vs covariates
    srt = np.sort(nums, axis=1)
    feats = pd.DataFrame({"Date": rows["Date"].to_numpy(),
                          "sum": nums.sum(1), "min": srt[:, 0], "max": srt[:, -1],
                          "range": srt[:, -1] - srt[:, 0],
                          "odd": (nums % 2).sum(1),
                          "gap": np.diff(srt, axis=1).mean(1)})
    paired = feats.merge(covariates(), on="Date").sort_values("Date")
    Xc = paired[["sum", "min", "max", "range", "odd", "gap"]].to_numpy(float)
    Yc = paired[["Total tidal accel (g)", "Moon Dist (km)", "Moon Illum (0-1)",
                 "Sun Dist (km)", "Kp_daily_mean", "Kp_daily_max"]].to_numpy(float)
    cca = ridge_cca_heldout(Xc, Yc, rng)

    return {"game": game_name, "P": P, "n_draws": int(len(nums)),
            "drawsum_recovery": curve, "presence_recovery": pres,
            "topology_h1": topo, "cca_vs_covariates": cca,
            "note": "presence null = 6-of-P constrained generator (A1), m=199"}


def main():
    stages = sys.argv[1:] or list(GAMES)
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed_scheme": f"{SEED}+hash(game)%1000",
                        "registered_expectation": "all tests null for all five games",
                        "protocol": "amendment to REGISTRATION_BATCH5.md, all-games symmetry"}
    for st in stages:
        results[st] = run_game(st)
        print(st, "done", flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
