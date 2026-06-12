#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""
Batch 5 relational experiments — run only AFTER docs/REGISTRATION_BATCH5.md.

B5-A: cross-game co-occurrence spectral comparison (R5), constrained nulls (A1),
      with a shape-matched negative control (Phase 0 gate).
B5-B: delay-embedding topology (R4): existence of H1 loops vs permutation null,
      and farthest-first landmark recovery curves (§4.4).

Stages (CLI args): shapegate, crossgame, topology, recovery
Output: results/relational_batch5.json (merged per stage).
"""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_batch5.json")
SEED = 20260611

GAME_P = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
          "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}


def p_perm(obs, nulls):
    nulls = np.asarray(nulls, dtype=float)
    return float((1 + np.sum(nulls >= obs)) / (len(nulls) + 1))


# ----------------------------------------------------------- B5-A machinery
def cooccurrence(draws, P):
    """draws: (T,6) int array 1..P -> PxP co-occurrence count matrix."""
    C = np.zeros((P, P))
    for row in draws:
        idx = row - 1
        for i in range(6):
            for j in range(i + 1, 6):
                C[idx[i], idx[j]] += 1
                C[idx[j], idx[i]] += 1
    return C


def uniform_draws(rng, T, P):
    return np.array([np.sort(rng.choice(P, size=6, replace=False)) + 1
                     for _ in range(T)])


def null_moments(rng, T, P, m=200):
    """Cell-wise null mean/std of co-occurrence counts under 6-of-P uniform."""
    samples = np.array([cooccurrence(uniform_draws(rng, T, P), P) for _ in range(m)])
    return samples.mean(0), samples.std(0) + 1e-12


def std_spectrum(C, mu, sd, k=10):
    Z = (C - mu) / sd
    np.fill_diagonal(Z, 0.0)
    lam = np.linalg.eigvalsh(Z)
    return np.sort(lam)[::-1][:k], float(np.max(lam))


def spec_distance(s1, s2):
    return float(np.linalg.norm(s1 - s2))


class GameSpec:
    """Caches null moments and per-game standardized spectra."""

    def __init__(self, rng, T, P, name):
        self.T, self.P, self.name = T, P, name
        self.mu, self.sd = null_moments(rng, T, P)

    def spectrum(self, draws):
        return std_spectrum(cooccurrence(draws, self.P), self.mu, self.sd)


def pair_test(rng, gsA, drawsA, gsB, drawsB, m=99):
    """Score = -spectral distance; null = independent uniform pairs."""
    sA, _ = gsA.spectrum(drawsA)
    sB, _ = gsB.spectrum(drawsB)
    obs = -spec_distance(sA, sB)
    nulls = []
    for _ in range(m):
        nA, _ = gsA.spectrum(uniform_draws(rng, gsA.T, gsA.P))
        nB, _ = gsB.spectrum(uniform_draws(rng, gsB.T, gsB.P))
        nulls.append(-spec_distance(nA, nB))
    return obs, nulls


def load_games():
    d = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    out = {}
    for g, P in GAME_P.items():
        rows = d[d["Game"] == g].sort_values("Date")
        out[g] = (rows[[f"N{i}" for i in range(1, 7)]].to_numpy(int), P)
    return out


def run_shapegate():
    """Phase 0 negative control at the real shape: uniform-vs-uniform pairs at the
    6/55-vs-6/45 shape must be calibrated."""
    rng = np.random.default_rng(SEED + 50)
    gsA = GameSpec(rng, 156, 55, "synthetic 6/55 shape")
    gsB = GameSpec(rng, 156, 45, "synthetic 6/45 shape")
    pvals = []
    for _ in range(40):
        A = uniform_draws(rng, gsA.T, gsA.P)
        B = uniform_draws(rng, gsB.T, gsB.P)
        obs, nulls = pair_test(rng, gsA, A, gsB, B, m=49)
        pvals.append(p_perm(obs, nulls))
    from scipy import stats
    pvals = np.asarray(pvals)
    ks = stats.kstest(pvals, "uniform")
    return {"n_trials": 40, "m_null": 49,
            "fpr_at_alpha": float(np.mean(pvals <= 0.05)),
            "ks_p": float(ks.pvalue),
            "gate_passed": bool(abs(np.mean(pvals <= 0.05) - 0.05) <= 3 * np.sqrt(0.05 * 0.95 / 40)
                                and ks.pvalue > 0.01)}


def run_crossgame():
    rng = np.random.default_rng(SEED + 51)
    games = load_games()
    specs = {g: GameSpec(rng, len(draws), P, g) for g, (draws, P) in games.items()}
    per_game = {}
    for g, (draws, P) in games.items():
        _, lmax = specs[g].spectrum(draws)
        # per-game lambda_max z against its own null spectra
        null_lmax = [std_spectrum(cooccurrence(uniform_draws(rng, len(draws), P), P),
                                  specs[g].mu, specs[g].sd)[1] for _ in range(99)]
        per_game[g] = {"lambda_max": lmax,
                       "p": p_perm(lmax, null_lmax),
                       "null_mean": float(np.mean(null_lmax)),
                       "null_std": float(np.std(null_lmax))}
    pairs = {}
    names = list(games)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            obs, nulls = pair_test(rng, specs[a], games[a][0], specs[b], games[b][0])
            pairs[f"{a} | {b}"] = {"score": obs, "p": p_perm(obs, nulls),
                                   "null_mean": float(np.mean(nulls)),
                                   "null_q05": float(np.quantile(nulls, 0.05))}
    m = len(pairs)
    sidak = 1 - (1 - 0.05) ** (1 / m)
    minp = min(v["p"] for v in pairs.values())
    return {"per_game_lambda_max": per_game, "pairs": pairs,
            "m_pairs": m, "sidak_threshold": sidak, "min_pair_p": minp,
            "joint_verdict_null": bool(minp > sidak)}


# ----------------------------------------------------------- B5-B machinery
def delay_embed(y, tau=3, dim=3):
    n = len(y) - (dim - 1) * tau
    return np.column_stack([y[i * tau:i * tau + n] for i in range(dim)])


def max_h1(X):
    from ripser import ripser
    dgm = ripser(X, maxdim=1)["dgms"][1]
    return 0.0 if len(dgm) == 0 else float(np.max(dgm[:, 1] - dgm[:, 0]))


def load_series():
    tid = pd.read_csv(os.path.join(ROOT, "datasets/tidal-manila/tidal_derived.csv"))
    sm = pd.read_csv(os.path.join(ROOT, "datasets/jpl-horizons-sun-moon/sun_moon_daily.csv"))
    kp = pd.read_csv(os.path.join(ROOT, "datasets/gfz-kp-geomagnetic/kp_daily.csv"))
    dr = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    dr = dr[dr["Game"] == "Grand Lotto 6/55"].sort_values("Date")
    s = {"tidal_total_accel": tid["Total tidal accel (g)"].to_numpy(float),
         "moon_distance_km": sm["Moon Dist (km)"].to_numpy(float),
         "kp_daily_mean": kp["Kp_daily_mean"].to_numpy(float),
         "lotto655_draw_sum": dr[[f"N{i}" for i in range(1, 7)]].to_numpy(float).sum(1)}
    return {k: (v - v.mean()) / v.std() for k, v in s.items()}


def run_topology():
    rng = np.random.default_rng(SEED + 52)
    series = load_series()
    out = {}
    for name, y in series.items():
        X = delay_embed(y)
        obs = max_h1(X)
        nulls = [max_h1(delay_embed(y[rng.permutation(len(y))])) for _ in range(99)]
        out[name] = {"max_h1_persistence": obs, "p": p_perm(obs, nulls),
                     "null_mean": float(np.mean(nulls)),
                     "null_q95": float(np.quantile(nulls, 0.95)),
                     "n_embedded": int(len(X))}
    return {"tau": 3, "dim": 3, "m_null": 99, "series": out}


def farthest_first(X, k, seed=0):
    rng = np.random.default_rng(seed)
    idx = [int(rng.integers(len(X)))]
    d = np.linalg.norm(X - X[idx[0]], axis=1)
    for _ in range(k - 1):
        nxt = int(np.argmax(d))
        idx.append(nxt)
        d = np.minimum(d, np.linalg.norm(X - X[nxt], axis=1))
    return np.array(idx)


def run_recovery(names=("tidal_total_accel", "lotto655_draw_sum")):
    rng = np.random.default_rng(SEED + 53)
    series = load_series()
    out = {}
    for name in names:
        y = series[name]
        X = delay_embed(y)
        curve = []
        for frac in [0.05, 0.10, 0.20, 0.40]:
            k = max(8, int(round(frac * len(X))))
            ps = []
            for r in range(10):
                L = X[farthest_first(X, k, seed=r)]
                obs = max_h1(L)
                nulls = []
                for _ in range(49):
                    yp = y[rng.permutation(len(y))]
                    Xp = delay_embed(yp)
                    nulls.append(max_h1(Xp[farthest_first(Xp, k, seed=r)]))
                ps.append(p_perm(obs, nulls))
            curve.append({"frac": frac, "k_landmarks": k,
                          "median_p": float(np.median(ps)),
                          "frac_p_le_05": float(np.mean(np.array(ps) <= 0.05))})
        out[name] = curve
    return {"selector": "farthest-first", "m_null": 49, "repeats": 10,
            "curves": out}


STAGES = {"shapegate": run_shapegate, "crossgame": run_crossgame,
          "topology": run_topology,
          "recovery_tidal": lambda: run_recovery(("tidal_total_accel",)),
          "recovery_lotto": lambda: run_recovery(("lotto655_draw_sum",))}


def main():
    stages = sys.argv[1:] or list(STAGES)
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "registration": "docs/REGISTRATION_BATCH5.md"}
    for st in stages:
        res = STAGES[st]()
        if st.startswith("recovery"):
            merged = results.get("recovery", {"selector": "farthest-first",
                                              "m_null": 49, "repeats": 10,
                                              "curves": {}})
            merged["curves"].update(res["curves"])
            results["recovery"] = merged
        else:
            results[st] = res
        print(st, "done", flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
