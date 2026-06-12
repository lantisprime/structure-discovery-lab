#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""
Batch 6 — lotto sub-dataset partition experiments (see REGISTRATION_BATCH6.md).

B6-1: cross-quarter MMD on draw features (pool-and-relabel null)
B6-2: cross-quarter co-occurrence spectra (constrained-uniform null + shape gate)
B6-3: half-vs-half hot-number consistency (constrained-uniform null)

Stages: gate, mmd, spectra, halves
Output: results/relational_subsets.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "results", "relational_subsets.json")
SEED = 20260611

sys.path.insert(0, HERE)
from relational_admission import mmd_pvalue
from relational_batch5 import (GameSpec, cooccurrence, uniform_draws,
                               pair_test, p_perm)

GAMES = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}


def load_all():
    d = pd.read_csv(os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv"))
    out = {}
    for g, P in GAMES.items():
        rows = d[d["Game"] == g].sort_values("Date")
        out[g] = (rows[[f"N{i}" for i in range(1, 7)]].to_numpy(int), P,
                  rows["Date"].tolist())
    return out


def features(nums):
    srt = np.sort(nums, axis=1)
    F = np.column_stack([nums.sum(1), srt[:, 0], srt[:, -1],
                         srt[:, -1] - srt[:, 0], (nums % 2).sum(1),
                         np.diff(srt, axis=1).mean(1)]).astype(float)
    return (F - F.mean(0)) / (F.std(0) + 1e-12)


def quarters(n):
    cuts = [0, n // 4, n // 2, 3 * n // 4, n]
    return [(cuts[i], cuts[i + 1]) for i in range(4)]


def run_gate():
    """Shape gate for B6-2 at the (39, 55) quarter shape."""
    rng = np.random.default_rng(SEED + 60)
    gs = GameSpec(rng, 39, 55, "quarter-shape 6/55")
    pvals = []
    for _ in range(40):
        A = uniform_draws(rng, 39, 55)
        B = uniform_draws(rng, 39, 55)
        obs, nulls = pair_test(rng, gs, A, gs, B, m=49)
        pvals.append(p_perm(obs, nulls))
    pvals = np.asarray(pvals)
    ks = stats.kstest(pvals, "uniform")
    fpr = float(np.mean(pvals <= 0.05))
    return {"n_trials": 40, "m_null": 49, "shape": [39, 55],
            "fpr_at_alpha": fpr, "ks_p": float(ks.pvalue),
            "gate_passed": bool(abs(fpr - 0.05) <= 3 * np.sqrt(0.05 * 0.95 / 40)
                                and ks.pvalue > 0.01)}


def run_mmd():
    rng = np.random.default_rng(SEED + 61)
    data = load_all()
    out = {}
    allp = []
    for g, (nums, P, dates) in data.items():
        F = features(nums)
        qs = quarters(len(F))
        pairs = {}
        for i in range(4):
            for j in range(i + 1, 4):
                a, b = qs[i], qs[j]
                p = mmd_pvalue(F[a[0]:a[1]], F[b[0]:b[1]], rng, m=99)
                pairs[f"Q{i+1}|Q{j+1}"] = float(p)
                allp.append(p)
        out[g] = pairs
    m = len(allp)
    sidak = 1 - 0.95 ** (1 / m)
    return {"per_game": out, "m_tests": m, "min_p": float(min(allp)),
            "sidak_threshold": float(sidak),
            "joint_verdict_null": bool(min(allp) > sidak),
            "representation": "6 draw features, standardized; RBF MMD, median heuristic, m=99"}


def run_spectra():
    rng = np.random.default_rng(SEED + 62)
    data = load_all()
    out = {}
    allp = []
    for g, (nums, P, dates) in data.items():
        qs = quarters(len(nums))
        T = qs[0][1] - qs[0][0]
        gs = GameSpec(rng, T, P, g)
        pairs = {}
        for i in range(4):
            for j in range(i + 1, 4):
                A = nums[qs[i][0]:qs[i][0] + T]
                B = nums[qs[j][0]:qs[j][0] + T]
                obs, nulls = pair_test(rng, gs, A, gs, B, m=99)
                p = p_perm(obs, nulls)
                pairs[f"Q{i+1}|Q{j+1}"] = float(p)
                allp.append(p)
        out[g] = pairs
    m = len(allp)
    sidak = 1 - 0.95 ** (1 / m)
    return {"per_game": out, "m_tests": m, "min_p": float(min(allp)),
            "sidak_threshold": float(sidak),
            "joint_verdict_null": bool(min(allp) > sidak)}


def run_halves():
    rng = np.random.default_rng(SEED + 63)
    data = load_all()
    out = {}
    for g, (nums, P, dates) in data.items():
        n = len(nums)
        h = n // 2

        def freq_dev(draws, T):
            cnt = np.zeros(P)
            for row in draws:
                cnt[row - 1] += 1
            return cnt - T * 6.0 / P

        d1 = freq_dev(nums[:h], h)
        d2 = freq_dev(nums[h:], n - h)
        obs = float(np.corrcoef(d1, d2)[0, 1])
        nulls = []
        for _ in range(199):
            n1 = freq_dev(uniform_draws(rng, h, P), h)
            n2 = freq_dev(uniform_draws(rng, n - h, P), n - h)
            nulls.append(float(np.corrcoef(n1, n2)[0, 1]))
        p = p_perm(obs, nulls)
        # C9 trace: top contributing numbers to the observed correlation
        contrib = d1 * d2
        top = np.argsort(-contrib)[:3]
        out[g] = {"hot_number_corr": obs, "p": p,
                  "null_q95": float(np.quantile(nulls, 0.95)),
                  "boundary_date": dates[h],
                  "top_contributors": [[int(t + 1), float(round(contrib[t], 1))]
                                       for t in top]}
    m = len(out)
    sidak = 1 - 0.95 ** (1 / m)
    minp = min(v["p"] for v in out.values())
    return {"per_game": out, "m_tests": m, "min_p": float(minp),
            "sidak_threshold": float(sidak),
            "joint_verdict_null": bool(minp > sidak), "m_null": 199}


STAGES = {"gate": run_gate, "mmd": run_mmd, "spectra": run_spectra,
          "halves": run_halves}


def main():
    stages = sys.argv[1:] or list(STAGES)
    results = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            results = json.load(f)
    results["_meta"] = {"date": "2026-06-11", "seed": SEED,
                        "registration": "docs/REGISTRATION_BATCH6.md"}
    for st in stages:
        results[st] = STAGES[st]()
        print(st, "done", flush=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(results, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
