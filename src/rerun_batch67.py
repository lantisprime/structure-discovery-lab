#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application).
"""Batch 6+7 rerun under remediated methodology (run id: batch67_r2).
Registration: docs/REGISTRATION_BATCH6_7_RERUN.md (hash 2709deedb274f0f6,
committed pre-run). Built on src/core + src/domains/pcso_lotto.
Stages: b6_mmd, b6_spectra_<g42|g45|g49|g55|g58>, b6_halves,
        b7_seasons, b7_cca, b7_gw
Output: results/rerun_batch67.json (merged per stage)."""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "rerun_batch67.json")
SEED = 20260611

sys.path.insert(0, HERE)
from core import (p_perm, mmd_pvalue, fast_draws, presence, cooccurrence,
                  std_spectrum, ridge_cca_heldout, gw_test, embed_series, sidak)
from domains import pcso_lotto as dom

GAMES = dom.DRAW_ENSEMBLES
KEYS = {"Lotto 6/42": "g42", "Mega Lotto 6/45": "g45", "Super Lotto 6/49": "g49",
        "Grand Lotto 6/55": "g55", "Ultra Lotto 6/58": "g58"}


def features(nums):
    srt = np.sort(nums, axis=1)
    F = np.column_stack([nums.sum(1), srt[:, 0], srt[:, -1],
                         srt[:, -1] - srt[:, 0], (nums % 2).sum(1),
                         np.diff(srt, axis=1).mean(1)]).astype(float)
    return (F - F.mean(0)) / (F.std(0) + 1e-12)


def quarters(n):
    cuts = [0, n // 4, n // 2, 3 * n // 4, n]
    return [(cuts[i], cuts[i + 1]) for i in range(4)]


def run_b6_mmd():
    rng = np.random.default_rng(SEED + 300)
    out, allp = {}, []
    for g in GAMES:
        nums, _ = dom.load_draws(g)
        F = features(nums)
        qs = quarters(len(F))
        pairs = {}
        for i in range(4):
            for j in range(i + 1, 4):
                a, b = qs[i], qs[j]
                p = mmd_pvalue(F[a[0]:a[1]], F[b[0]:b[1]], rng, m=1199)
                pairs[f"Q{i+1}|Q{j+1}"] = float(p)
                allp.append(p)
        out[g] = pairs
    a = sidak(0.05, 30)
    return {"per_game": out, "m_perm": 1199, "min_p": float(min(allp)),
            "sidak_threshold": float(a),
            "joint_verdict_null": bool(min(allp) > a)}


class QuarterSpec:
    """Null moments for co-occurrence at quarter shape, via fast generator."""

    def __init__(self, rng, T, P, msim=200):
        S = np.array([cooccurrence(fast_draws(rng, T, P), P) for _ in range(msim)])
        self.mu, self.sd = S.mean(0), S.std(0) + 1e-12
        self.T, self.P = T, P

    def spec(self, draws):
        return std_spectrum(cooccurrence(draws, self.P), self.mu, self.sd)[0]


def run_b6_spectra(game):
    rng = np.random.default_rng(SEED + 310 + ord(KEYS[game][1]))
    nums, _ = dom.load_draws(game)
    P = GAMES[game]
    qs = quarters(len(nums))
    T = qs[0][1] - qs[0][0]
    spec = QuarterSpec(rng, T, P)
    pairs = {}
    for i in range(4):
        for j in range(i + 1, 4):
            A = nums[qs[i][0]:qs[i][0] + T]
            B = nums[qs[j][0]:qs[j][0] + T]
            obs = -float(np.linalg.norm(spec.spec(A) - spec.spec(B)))
            nulls = [-float(np.linalg.norm(spec.spec(fast_draws(rng, T, P)) -
                                           spec.spec(fast_draws(rng, T, P))))
                     for _ in range(1199)]
            pairs[f"Q{i+1}|Q{j+1}"] = p_perm(obs, nulls)
    return {game: pairs}


def run_b6_halves():
    rng = np.random.default_rng(SEED + 320)
    out = {}
    for g, P in GAMES.items():
        row = {}
        for regime, kw in [("all", {}), ("ex_suspicious", {"exclude_suspicious": True}),
                           ("verified_only", {"verified_only": True})]:
            nums, _ = dom.load_draws(g, **kw)
            if len(nums) < 20:
                row[regime] = {"n": int(len(nums)), "note": "too few rows"}
                continue
            n = len(nums); h = n // 2

            def dev(Z):
                return Z.sum(0) - len(Z) * 6 / P
            obs = float(np.corrcoef(dev(presence(nums[:h], P)),
                                    dev(presence(nums[h:], P)))[0, 1])
            nulls = [float(np.corrcoef(dev(presence(fast_draws(rng, h, P), P)),
                                       dev(presence(fast_draws(rng, n - h, P), P)))[0, 1])
                     for _ in range(199)]
            row[regime] = {"n": n, "corr": round(obs, 3),
                           "p": round(p_perm(obs, nulls), 3)}
        out[g] = row
    a = sidak(0.05, 5)
    minp = min(v["all"]["p"] for v in out.values())
    return {"per_game": out, "m_perm": 199, "sidak_threshold": float(a),
            "min_p_all_rows": float(minp),
            "joint_verdict_null": bool(minp > a)}


def _pressure():
    pr = pd.read_csv(os.path.join(ROOT,
                     "datasets/openmeteo-pressure-manila/pressure_daily.csv"))
    pr["P_range"] = pr["P_msl_max_hPa"] - pr["P_msl_min_hPa"]
    return pr


PCOLS = ["P_msl_mean_hPa", "P_msl_min_hPa", "P_msl_max_hPa", "P_range"]


def run_b7_seasons():
    rng = np.random.default_rng(SEED + 330)
    pr = _pressure()
    F = pr[PCOLS].to_numpy(float)
    F = (F - F.mean(0)) / F.std(0)
    n = len(F)
    cuts = [0, n // 4, n // 2, 3 * n // 4, n]
    pairs = {}
    for i in range(4):
        for j in range(i + 1, 4):
            pairs[f"Q{i+1}|Q{j+1}"] = float(
                mmd_pvalue(F[cuts[i]:cuts[i + 1]], F[cuts[j]:cuts[j + 1]],
                           rng, m=399))
    a = sidak(0.05, 6)
    return {"pairs": pairs, "m_perm": 399, "sidak_threshold": float(a),
            "n_corrected_rejections": int(sum(p <= a for p in pairs.values()))}


def run_b7_cca():
    rng = np.random.default_rng(SEED + 331)
    pr = _pressure()
    sm = pd.read_csv(os.path.join(ROOT,
                     "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))[
        ["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)",
         "Sun Alt (deg)"]]
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))[
        ["Date", "Kp_daily_mean", "Kp_daily_max"]]
    out = {}
    for tag, other, cols in [("pressure_vs_sunmoon", sm,
                              ["Moon Dist (km)", "Moon Illum (0-1)",
                               "Sun Dist (km)", "Sun Alt (deg)"]),
                             ("pressure_vs_kp", kp,
                              ["Kp_daily_mean", "Kp_daily_max"])]:
        m = pr.merge(other, on="Date").sort_values("Date")
        X = m[PCOLS].to_numpy(float)
        Y = m[cols].to_numpy(float)
        splits = {}
        for tf in [0.5, 0.6, 0.7]:
            r = ridge_cca_heldout(X, Y, rng, m=199, train_frac=tf)
            splits[str(tf)] = {"rho1": round(r["heldout_rho1"], 3),
                               "p": round(r["p_shuffled_pairing"], 3)}
        ps = [s["p"] for s in splits.values()]
        out[tag] = {"splits": splits, "median_p": float(np.median(ps))}
    a = sidak(0.05, 2)
    return {"tests": out, "m_perm": 199, "sidak_threshold": float(a),
            "decision": "median p across splits vs threshold"}


def run_b7_gw():
    rng = np.random.default_rng(SEED + 332)
    pr = _pressure()
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT,
                     "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    nums, _ = dom.load_draws("Grand Lotto 6/55")
    E = {"pressure": embed_series(pr["P_msl_mean_hPa"].to_numpy(float)),
         "tidal": embed_series(tid["Total tidal accel (g)"].to_numpy(float)),
         "moon": embed_series(sm["Moon Dist (km)"].to_numpy(float)),
         "drawsum_655": embed_series(nums.sum(1).astype(float))}
    out = {}
    for a, b in [("tidal", "moon"), ("pressure", "drawsum_655"),
                 ("pressure", "tidal")]:
        out[f"{a}|{b}"] = gw_test(rng, E[a], E[b], m=99)
    return {"pairs": out, "m_perm": 99,
            "status": "G0 EXPLORATORY ONLY — instrument demoted (REMEDIATION_LOG M2); "
                      "no corrected claims attach to these numbers"}


STAGES = {"b6_mmd": run_b6_mmd, "b6_halves": run_b6_halves,
          "b7_seasons": run_b7_seasons, "b7_cca": run_b7_cca,
          "b7_gw": run_b7_gw}
for _g, _k in KEYS.items():
    STAGES[f"b6_spectra_{_k}"] = (lambda g: (lambda: run_b6_spectra(g)))(_g)


def main():
    stages = sys.argv[1:]
    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT))
    results["_meta"] = {"run_id": "batch67_r2", "date": "2026-06-11",
                        "seed": SEED,
                        "registration": "docs/REGISTRATION_BATCH6_7_RERUN.md "
                                        "(hash 2709deedb274f0f6, pre-run)",
                        "architecture": "src/core + src/domains (sanitized)"}
    for st in stages:
        res = STAGES[st]()
        if st.startswith("b6_spectra_"):
            acc = results.get("b6_spectra", {"per_game": {}, "m_perm": 1199})
            acc["per_game"].update(res)
            allp = [p for g in acc["per_game"].values() for p in g.values()]
            a = sidak(0.05, 30)
            acc.update({"min_p_so_far": float(min(allp)),
                        "sidak_threshold": float(a),
                        "joint_verdict_null_so_far": bool(min(allp) > a),
                        "n_games_done": len(acc["per_game"])})
            results["b6_spectra"] = acc
        else:
            results[st] = res
        print(st, "done", flush=True)
        json.dump(results, open(OUT, "w"), indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
