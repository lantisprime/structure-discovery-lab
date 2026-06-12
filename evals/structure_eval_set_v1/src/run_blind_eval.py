#!/usr/bin/env python3
"""Blind methodology eval — runs the registered battery (REGISTRATION_BLINDEVAL.md)
on the blind datasets. Answer key sealed. Expectation-free. Seed 20260611.
Stages: draws_marg, draws_mem, draws_stat, draws_subset_<S>, draws_cross,
        draws_sensor, sensors, series_rec, series_tda, series_pair,
        series_seg, clouds, graphs, matrices
Output: <labroot>/results/blind_eval.json (merged)."""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.join(HERE, "..")
LAB = os.path.join(EVAL, "..", "..")
BLIND = os.path.join(EVAL, "blind", "datasets")
OUT = os.path.join(LAB, "results", "blind_eval.json")
SEED = 20260611

sys.path.insert(0, os.path.join(LAB, "src"))
from core import (mmd_pvalue, soft_impute, lap_spectrum, rewired, p_perm,
                  delay_embed, max_h1, gw_test, ridge_cca_heldout,
                  recovery_point)


def draws():
    d = pd.read_csv(os.path.join(BLIND, "draws/draws_all.csv"))
    out = {}
    for s in "ABCDE":
        rows = d[d.stream_id == s].sort_values("date")
        out[s] = rows[[f"n{i}" for i in range(1, 7)]].to_numpy(int)
    return out, 60


from core import fast_draws, presence


def features(nums):
    srt = np.sort(nums, axis=1)
    F = np.column_stack([nums.sum(1), srt[:, 0], srt[:, -1],
                         srt[:, -1] - srt[:, 0], (nums % 2).sum(1),
                         np.diff(srt, axis=1).mean(1)]).astype(float)
    return (F - F.mean(0)) / (F.std(0) + 1e-12)


from core import chi2_counts


def run_draws_marg():
    D, P = draws()
    rng = np.random.default_rng(SEED + 200)
    out = {}
    for s, nums in D.items():
        obs = chi2_counts(presence(nums, P), P)
        nulls = [chi2_counts(presence(fast_draws(rng, len(nums), P), P), P)
                 for _ in range(399)]
        out[s] = {"chi2": round(obs, 1), "p": p_perm(obs, nulls)}
    return out


def run_draws_mem():
    D, P = draws()
    rng = np.random.default_rng(SEED + 201)
    out = {}

    def overlap(Z):
        return float((Z[:-1] & Z[1:]).sum() / (len(Z) - 1))
    for s, nums in D.items():
        obs = overlap(presence(nums, P))
        nulls = np.asarray([overlap(presence(fast_draws(rng, len(nums), P), P))
                            for _ in range(399)])
        dev = abs(obs - nulls.mean())               # two-sided
        p = (1 + np.sum(np.abs(nulls - nulls.mean()) >= dev)) / 400
        out[s] = {"mean_overlap": round(obs, 3),
                  "null_mean": round(float(nulls.mean()), 3), "p": float(p)}
    return out


def run_draws_stat():
    D, P = draws()
    rng = np.random.default_rng(SEED + 202)
    out = {}

    def dev(Z):
        return Z.sum(0) - len(Z) * 6 / P
    for s, nums in D.items():
        n = len(nums); h = n // 2
        Z = presence(nums, P)
        obs = float(np.corrcoef(dev(Z[:h]), dev(Z[h:]))[0, 1])
        nulls = [float(np.corrcoef(dev(presence(fast_draws(rng, h, P), P)),
                                   dev(presence(fast_draws(rng, n - h, P), P)))[0, 1])
                 for _ in range(399)]
        out[s] = {"half_corr": round(obs, 3), "p": p_perm(obs, nulls)}
    return out


def run_draws_subset(stream):
    D, P = draws()
    rng = np.random.default_rng(SEED + 203 + ord(stream))
    y = D[stream].sum(1).astype(float)
    y = (y - y.mean()) / y.std()
    curve = []
    for frac in [0.05, 0.10, 0.20, 0.40]:
        ps = []
        for _ in range(10):
            p, z = recovery_point(y, frac, rng, m=199)
            ps.append(p)
        curve.append({"frac": frac, "median_p": float(np.median(ps))})
    return {stream: curve}


def run_draws_cross():
    D, P = draws()
    rng = np.random.default_rng(SEED + 210)
    F = {s: features(n) for s, n in D.items()}
    out = {}
    ss = "ABCDE"
    for i in range(5):
        for j in range(i + 1, 5):
            r = ridge_cca_heldout(F[ss[i]], F[ss[j]], rng, m=799)
            out[f"{ss[i]}|{ss[j]}"] = {"rho1": round(r["heldout_rho1"], 3),
                                       "p": r["p_shuffled_pairing"]}
    return out


def run_draws_sensor():
    D, P = draws()
    sen = pd.read_csv(os.path.join(BLIND, "sensors/sensor_panel.csv"))
    Y = sen[[f"sensor_0{i}" for i in range(1, 5)]].to_numpy(float)
    rng = np.random.default_rng(SEED + 211)
    out = {}
    for s, nums in D.items():
        r = ridge_cca_heldout(features(nums), Y, rng, m=399)
        out[s] = {"rho1": round(r["heldout_rho1"], 3), "p": r["p_shuffled_pairing"]}
    return out


def run_sensors():
    sen = pd.read_csv(os.path.join(BLIND, "sensors/sensor_panel.csv"))
    rng = np.random.default_rng(SEED + 212)
    out = {}
    for c in [f"sensor_0{i}" for i in range(1, 5)]:
        y = sen[c].to_numpy(float)
        y = (y - y.mean()) / y.std()
        ps = []
        for _ in range(10):
            p, z = recovery_point(y, 0.20, rng, m=199)
            ps.append(p)
        out[c] = {"recovery_median_p_k20": float(np.median(ps))}
    return out


from core import fast_recovery_point


def run_series_rec():
    w = pd.read_csv(os.path.join(BLIND, "series/series_wide.csv"))
    rng = np.random.default_rng(SEED + 220)
    out = {}
    for c in ["S1", "S2", "S3", "S4"]:
        y = w[c].to_numpy(float)
        y = (y - y.mean()) / y.std()
        curve = []
        for frac in [0.05, 0.10, 0.20, 0.40]:
            ps = [fast_recovery_point(y, frac, rng, m=199) for _ in range(10)]
            curve.append({"frac": frac, "median_p": float(np.median(ps))})
        out[c] = curve
    return out


def run_series_tda(cols=("S1", "S2", "S3", "S4")):
    # Amendment (compute, declared): embedding subsampled to 250 points
    # (every-kth); m=199 (floor 0.005 <= Sidak(4)/2 = 0.0063, compliant).
    w = pd.read_csv(os.path.join(BLIND, "series/series_wide.csv"))
    rng = np.random.default_rng(SEED + 221)
    out = {}

    def emb(y):
        X = delay_embed(y)
        return X[np.linspace(0, len(X) - 1, 250).astype(int)]
    for c in cols:
        y = w[c].to_numpy(float)
        y = (y - y.mean()) / y.std()
        obs = max_h1(emb(y))
        nulls = [max_h1(emb(y[rng.permutation(len(y))])) for _ in range(199)]
        out[c] = {"max_h1": round(obs, 3),
                  "null_q95": round(float(np.quantile(nulls, 0.95)), 3),
                  "p": p_perm(obs, nulls)}
    return out


def run_series_pair():
    from scipy import stats as st
    w = pd.read_csv(os.path.join(BLIND, "series/series_wide.csv"))
    out = {}
    cols = ["S1", "S2", "S3", "S4"]
    n = len(w)
    shifts = list(range(26, n - 26))
    for i in range(4):
        for j in range(i + 1, 4):
            a = w[cols[i]].to_numpy(float); b = w[cols[j]].to_numpy(float)
            obs = abs(st.spearmanr(a, b).statistic)
            nulls = [abs(st.spearmanr(a, np.roll(b, d)).statistic)
                     for d in shifts]
            p = (1 + sum(x >= obs for x in nulls)) / (len(shifts) + 1)
            out[f"{cols[i]}|{cols[j]}"] = {"abs_spearman": round(float(obs), 3),
                                           "p": round(float(p), 4)}
    return out


def run_series_seg():
    w = pd.read_csv(os.path.join(BLIND, "series/series_wide.csv"))
    rng = np.random.default_rng(SEED + 223)
    out = {}
    for c in ["S1", "S2", "S3", "S4"]:
        y = w[c].to_numpy(float)
        F = np.column_stack([y, np.abs(np.r_[0, np.diff(y)])])
        F = (F - F.mean(0)) / (F.std(0) + 1e-12)
        n = len(F); cuts = [0, n // 4, n // 2, 3 * n // 4, n]
        ps = {}
        for i in range(4):
            for j in range(i + 1, 4):
                p = mmd_pvalue(F[cuts[i]:cuts[i + 1]], F[cuts[j]:cuts[j + 1]],
                               rng, m=399)
                ps[f"Q{i+1}|Q{j+1}"] = float(p)
        out[c] = {"pairs": ps, "min_p": min(ps.values()),
                  "sidak_m6": 1 - 0.95 ** (1 / 6)}
    return out


def load_cloud(name):
    df = pd.read_csv(os.path.join(BLIND, f"clouds/cloud_{name}.csv"))
    cols = [c for c in df.columns if c.lower() not in ("index", "id", "unnamed: 0")]
    X = df[cols].to_numpy(float)
    return (X - X.mean(0)) / (X.std(0) + 1e-12)


def run_clouds():
    rng = np.random.default_rng(SEED + 230)
    out = {"tda": {}, "gw_exploratory_G0": {}}
    clouds = {n: load_cloud(n) for n in ["X", "Y", "Z"]}
    for n, X in clouds.items():
        sub = X[np.linspace(0, len(X) - 1, 200).astype(int)]
        obs = max_h1(sub)
        mu = sub.mean(0); C = np.cov(sub.T) + 1e-9 * np.eye(sub.shape[1])
        nulls = [max_h1(rng.multivariate_normal(mu, C, size=len(sub)))
                 for _ in range(399)]
        out["tda"][n] = {"max_h1": round(obs, 3),
                         "null_q95": round(float(np.quantile(nulls, 0.95)), 3),
                         "p": p_perm(obs, nulls)}
    for a, b in [("X", "Y"), ("X", "Z"), ("Y", "Z")]:
        A = clouds[a][np.linspace(0, 419, 120).astype(int)]
        B = clouds[b][np.linspace(0, 419, 120).astype(int)]
        out["gw_exploratory_G0"][f"{a}|{b}"] = gw_test(rng, A, B, m=99)
    return out


def load_graph(name):
    import networkx as nx
    e = pd.read_csv(os.path.join(BLIND, f"graphs/graph_{name}_edges.csv"))
    G = nx.Graph()
    G.add_edges_from(e[["source", "target"]].to_numpy(int).tolist())
    return G


def run_graphs():
    rng = np.random.default_rng(SEED + 240)
    out = {"community": {}, "pairs": {}}
    Gs = {n: load_graph(n) for n in ["A", "B", "C"]}
    for n, G in Gs.items():
        obs = -float(np.mean(lap_spectrum(G)))      # smaller bottom = community
        nulls = [-float(np.mean(lap_spectrum(rewired(G, rng))))
                 for _ in range(199)]
        out["community"][n] = {"mean_bottom12": round(-obs, 4),
                               "null_mean": round(-float(np.mean(nulls)), 4),
                               "p": p_perm(obs, nulls)}
    for a, b in [("A", "B"), ("A", "C"), ("B", "C")]:
        obs = -float(np.linalg.norm(lap_spectrum(Gs[a]) - lap_spectrum(Gs[b])))
        nulls = [-float(np.linalg.norm(lap_spectrum(Gs[a]) -
                                       lap_spectrum(rewired(Gs[b], rng))))
                 for _ in range(199)]
        out["pairs"][f"{a}|{b}"] = {"p": p_perm(obs, nulls)}
    return out


def run_matrices():
    rng = np.random.default_rng(SEED + 250)
    out = {}
    for m in ["M1", "M2"]:
        tr = pd.read_csv(os.path.join(BLIND, f"matrices/matrix_{m}_train_entries.csv"))
        te = pd.read_csv(os.path.join(BLIND, f"matrices/matrix_{m}_test_entries.csv"))
        R = int(max(tr.row.max(), te.row.max())) + 1
        C = int(max(tr.col.max(), te.col.max())) + 1
        M = np.zeros((R, C)); mask = np.zeros((R, C), bool)
        M[tr.row, tr.col] = tr.value; mask[tr.row, tr.col] = True

        def skill(Mfit, maskfit, te_rows, te_cols, te_vals):
            L, col_mean = soft_impute(Mfit, maskfit)
            rm = float(np.sqrt(np.mean((L[te_rows, te_cols] - te_vals) ** 2)))
            rb = float(np.sqrt(np.mean((col_mean[te_cols] - te_vals) ** 2)))
            return rb - rm, rm, rb
        obs, rm, rb = skill(M, mask, te.row.to_numpy(), te.col.to_numpy(),
                            te.value.to_numpy(float))
        nulls = []
        for _ in range(199):
            Mp = M.copy()
            for c in range(C):                       # permute within column among train
                idx = np.where(mask[:, c])[0]
                Mp[idx, c] = Mp[rng.permutation(idx), c]
            nulls.append(skill(Mp, mask, te.row.to_numpy(), te.col.to_numpy(),
                               te.value.to_numpy(float))[0])
        out[m] = {"skill": round(obs, 4), "rmse_model": round(rm, 4),
                  "rmse_baseline": round(rb, 4), "p": p_perm(obs, nulls)}
    return out


STAGES = {"draws_marg": run_draws_marg, "draws_mem": run_draws_mem,
          "draws_stat": run_draws_stat, "draws_cross": run_draws_cross,
          "draws_sensor": run_draws_sensor, "sensors": run_sensors,
          "series_rec": run_series_rec, "series_tda": run_series_tda,
          "series_pair": run_series_pair, "series_seg": run_series_seg,
          "clouds": run_clouds, "graphs": run_graphs, "matrices": run_matrices}
for _s in "ABCDE":
    STAGES[f"draws_subset_{_s}"] = (lambda s: (lambda: run_draws_subset(s)))(_s)
STAGES["series_tda_a"] = lambda: run_series_tda(("S1", "S2"))
STAGES["series_tda_b"] = lambda: run_series_tda(("S3", "S4"))


def main():
    stages = sys.argv[1:]
    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT))
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "registration": "REGISTRATION_BLINDEVAL.md (hash d66f66574e1638e9, committed pre-run)",
                        "sealed": "answer_key unread"}
    for st in stages:
        res = STAGES[st]()
        if st.startswith("draws_subset_"):
            acc = results.get("draws_subset", {})
            acc.update(res)
            results["draws_subset"] = acc
        elif st.startswith("series_tda_"):
            acc = results.get("series_tda", {})
            acc.update(res)
            results["series_tda"] = acc
        else:
            results[st] = res
        print(st, "done", flush=True)
        json.dump(results, open(OUT, "w"), indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
