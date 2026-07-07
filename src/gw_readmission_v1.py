#!/usr/bin/env python3
"""GW (R2) readmission calibration v1 — coupling-label-permutation null.

Registered: docs/REGISTRATION_GW_READMISSION_V1.md (committed to the
commitment ledger BEFORE this script ran; approval trail in
docs/PROPOSAL_GW_NULL_REDESIGN.md). Synthetic calibration only — no real
data is loaded and no multiplicity is charged. Deterministic: fixed seeds,
no wall-clock in the output; two runs must be byte-identical.

The statistic machinery replicates src/relational_admission.py R2 verbatim
(that module is a FROZEN HISTORICAL RECORD and must not be imported by new
experiments — lint_frozen_imports): exact POT GW, square loss, mean-scaled
Euclidean distance matrices, uniform measures, p = (1 + #{null >= obs})/(m+1).

Run:  python3 src/gw_readmission_v1.py [--out results/gw_readmission_v1.json]
"""
import argparse
import json
import os

import numpy as np
import ot
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

ALPHA = 0.05
N = 200          # points per cloud (registered)
M_PERM = 99      # permutations -> p_floor 0.01 (registered)
H0_TRIALS = 300  # gate 1/2 trials (registered)
POWER_TRIALS = 50
NOISE_GRID = [0.1, 0.2, 0.3, 0.5]
SEED_BASE = 20260707


# ---- statistic: verbatim replica of frozen relational_admission.py R2 ----
def gw_distortion(A, B):
    CA = np.sqrt(np.sum((A[:, None] - A[None, :]) ** 2, axis=-1))
    CB = np.sqrt(np.sum((B[:, None] - B[None, :]) ** 2, axis=-1))
    CA /= CA.mean()
    CB /= CB.mean()
    p = np.ones(len(A)) / len(A)
    q = np.ones(len(B)) / len(B)
    return ot.gromov.gromov_wasserstein2(CA, CB, p, q, "square_loss")


def p_perm(obs, nulls):
    nulls = np.asarray(nulls, dtype=float)
    return (1.0 + np.sum(nulls >= obs)) / (len(nulls) + 1.0)


def circle_cloud(rng, n, noise, dim):
    t = rng.uniform(0, 2 * np.pi, n)
    P = np.c_[np.cos(t), np.sin(t)] + noise * rng.normal(size=(n, 2))
    if dim > 2:
        P = np.c_[P, np.zeros((n, dim - 2))] @ rng_rotation(rng, dim)
    return P


def rng_rotation(rng, d):
    Q, _ = np.linalg.qr(rng.normal(size=(d, d)))
    return Q


# ------------- registered null: coupling-label permutation ---------------
def pad_to(A, d):
    """Zero-pad columns to dimension d — an isometry of A's distance matrix."""
    if A.shape[1] < d:
        A = np.c_[A, np.zeros((len(A), d - A.shape[1]))]
    return A


def gw_pvalue_labelperm(A, B, rng, m=M_PERM):
    d = max(A.shape[1], B.shape[1])
    Z = np.vstack([pad_to(A, d), pad_to(B, d)])
    n = len(A)
    obs = -gw_distortion(Z[:n], Z[n:])
    nulls = []
    for _ in range(m):
        idx = rng.permutation(len(Z))
        nulls.append(-gw_distortion(Z[idx[:n]], Z[idx[n:]]))
    return p_perm(obs, nulls)


# ------------------------------------------------------------------ gates
def gate_fpr_uniformity():
    rng = np.random.default_rng(SEED_BASE + 0)
    pvals = []
    for _ in range(H0_TRIALS):
        A = rng.normal(size=(N, 3))
        B = rng.normal(size=(N, 3))
        pvals.append(gw_pvalue_labelperm(A, B, rng))
    pvals = np.asarray(pvals)
    fpr = float(np.mean(pvals <= ALPHA))
    fpr_ok = 0.028 <= fpr <= 0.078                     # registered band
    ks = stats.kstest(pvals, "uniform")
    # lattice chi^2 across the 100 attainable levels k/100, k=1..100
    counts = np.bincount(np.rint(pvals * (M_PERM + 1)).astype(int),
                         minlength=M_PERM + 2)[1:M_PERM + 2]
    chi = stats.chisquare(counts)
    return {
        "n_trials": H0_TRIALS, "fpr_at_alpha": fpr, "fpr_ok": bool(fpr_ok),
        "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
        "lattice_chi2_p": float(chi.pvalue),
        "p_uniformity_ok": bool(ks.pvalue >= 0.01 and chi.pvalue >= 0.01),
    }


def gate_power():
    curve = {}
    for i, noise in enumerate(NOISE_GRID):
        rng = np.random.default_rng(SEED_BASE + 1000 + i)
        pvals = []
        for _ in range(POWER_TRIALS):
            A = circle_cloud(rng, N, noise, 2)
            B = circle_cloud(rng, N, noise, 3)
            pvals.append(gw_pvalue_labelperm(A, B, rng))
        curve[str(noise)] = float(np.mean(np.asarray(pvals) <= ALPHA))
    return {"n_trials_per_point": POWER_TRIALS, "curve_power_at_alpha": curve,
            "frozen_m1_reference": {"0.1": 0.95, "0.5": 0.15},
            "power_ok": bool(curve["0.1"] >= 0.85)}       # registered rule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/gw_readmission_v1.json")
    args = ap.parse_args()

    g12 = gate_fpr_uniformity()
    g3 = gate_power()
    if g12["p_uniformity_ok"] and g12["fpr_ok"] and g3["power_ok"]:
        verdict = "READMIT_CANDIDATE"
    elif g12["p_uniformity_ok"] and g12["fpr_ok"]:
        verdict = "CALIBRATED_BUT_POWERLESS"
    else:
        verdict = "NULL_STILL_MISCALIBRATED"

    out = {
        "_meta": {
            "run_id": "gw_readmission_v1",
            "registration": "docs/REGISTRATION_GW_READMISSION_V1.md",
            "approval": "docs/PROPOSAL_GW_NULL_REDESIGN.md (lab owner, "
                        "2026-07-07)",
            "null_under_test": "coupling-label permutation (pooled 2n rows, "
                               "permuted, split n/n; 2-D cloud zero-padded "
                               "— isometric)",
            "statistic": "verbatim replica of frozen relational_admission R2 "
                         "gw_distortion; p_perm (+1)-corrected",
            "params": {"n": N, "d": 3, "m_perm": M_PERM,
                       "h0_trials": H0_TRIALS,
                       "power_trials": POWER_TRIALS,
                       "noise_grid": NOISE_GRID,
                       "seed_scheme": f"{SEED_BASE}+0 (H0), "
                                      f"{SEED_BASE}+1000+i (power grid)"},
            "multiplicity_charge": 0,
            "deterministic": True,
        },
        "gate1_2_fpr_uniformity": g12,
        "gate3_power": g3,
        "verdict": verdict,
    }
    path = os.path.join(ROOT, args.out)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"verdict": verdict,
                      "fpr": g12["fpr_at_alpha"],
                      "ks_p": round(g12["ks_p"], 4),
                      "lattice_chi2_p": round(g12["lattice_chi2_p"], 4),
                      "power": g3["curve_power_at_alpha"]}, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
