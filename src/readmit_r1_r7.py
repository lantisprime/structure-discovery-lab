#!/usr/bin/env python3
"""AUDIT G-4: re-admission of R1-R7 under the remediation-era standard that
r8_admission.py already meets and ADMISSION_RELATIONAL predates:

  - negative controls at n_trials = 200 (was 50-100 for R2/R4/R5/R6/R7)
  - null count m >= 39 everywhere (was 19 for R2/R5 -> floor = alpha, the
    M3 pathology; 39 -> floor 0.025 <= alpha/2)
  - lattice-aware chi-square uniformity on 20 bins (expected 10/bin), NOT
    continuous KS on lattice p-values (the M2 lesson)
  - SPLIT rng streams: rng_data generates synthetic data, rng_null drives
    permutations/regenerations (m6 finding, never fixed in the frozen file)
  - frozen design: this docstring + gate constants hashed before execution;
    both outcome branches declared: PASS -> re-admitted v2; FAIL -> the
    instrument drops to EXPLORATORY_ONLY (the GW precedent)

Instruments and effect sizes are UNCHANGED from ADMISSION_RELATIONAL (this
is a re-run under tighter gates, not a re-tune — M1 discipline).

Usage: python3 readmit_r1_r7.py [r1 r3 r7 ...] [--smoke]
       --smoke: n=25, m=39 mechanics check only (never citable)
Output: results/readmission_v2.json (merged per stage)
"""
import hashlib
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

from relational_admission import (mmd_pvalue, gw_distortion, matched_gaussian,  # noqa: E402
                                  circle_cloud, cca_trial, tda_trial,
                                  spectral_distance, rewired, sbm_graph,
                                  nystrom_trial, swiss_roll, completion_trial,
                                  p_perm)

SEED = 20260704
OUT = os.path.join(ROOT, "results", "readmission_v2.json")
ALPHA = 0.05
N_NEG, N_POS, M_NULL = 200, 100, 39
CHUNK_SECONDS = float(os.environ.get("READMIT_CHUNK_SECONDS", 30))


def gate_negative(ps, n, label, m):
    """Adversarial review B2 fix: the add-one lattice does NOT spread evenly
    over 20 equal bins (at m=39 a flat-expectation chi2 falsely fails an
    87%-calibrated instrument 87% of the time). Expected bin masses are
    computed from the exact lattice, and the chi2 p-value is Monte Carlo
    calibrated on that lattice. The FPR band is centered at the exact
    lattice value of P(p <= alpha), not at alpha."""
    rng = np.random.default_rng(SEED + 999)
    ps = np.asarray(ps)
    lattice = (1 + np.arange(m + 1)) / (m + 1)
    p0 = float(np.mean(lattice <= ALPHA))            # exact P(p<=alpha) | H0
    fpr = float(np.mean(ps <= ALPHA))
    se3 = 3 * np.sqrt(p0 * (1 - p0) / n)
    bins = np.linspace(0, 1, 21)
    exp = np.histogram(lattice, bins=bins)[0] * (n / (m + 1))
    keep = exp > 0

    def chi2_of(sample):
        cnts = np.histogram(sample, bins=bins)[0]
        return float((((cnts - exp)[keep] ** 2) / exp[keep]).sum())

    obs = chi2_of(ps)
    sims = [chi2_of(lattice[rng.integers(0, m + 1, size=n)])
            for _ in range(2000)]
    chi2_p = float((1 + sum(s >= obs for s in sims)) / 2001)
    return {"label": label, "n_trials": n, "fpr_at_alpha": fpr,
            "fpr_expected_lattice": round(p0, 4),
            "band_3se": round(se3, 4), "lattice_chi2_p_mc": round(chi2_p, 4),
            "passed": bool(abs(fpr - p0) <= se3 and chi2_p > 0.01)}


def gate_positive(ps, label):
    ps = np.asarray(ps)
    return {"label": label, "n_trials": len(ps),
            "power_at_alpha": float(np.mean(ps <= ALPHA)),
            "passed": bool(np.mean(ps <= ALPHA) >= 0.8)}


# ---- per-instrument trials: (rng_data, rng_null) -> p -----------------------
def r1_neg(rd, rn): return mmd_pvalue(rd.normal(size=(80, 5)),
                                      rd.normal(size=(80, 5)), rn, m=99)
def r1_pos(rd, rn):
    X = rd.normal(size=(80, 5)); Y = rd.normal(size=(80, 5)); Y[:, 0] += 1.0
    return mmd_pvalue(X, Y, rn, m=99)

def _gw_p(A, B, rn, m=M_NULL):
    obs = -gw_distortion(A, B)
    nulls = [-gw_distortion(A, matched_gaussian(rn, B)) for _ in range(m)]
    return p_perm(obs, nulls)
def r2_neg(rd, rn): return _gw_p(rd.normal(size=(50, 3)), rd.normal(size=(50, 3)), rn)
def r2_pos(rd, rn): return _gw_p(circle_cloud(rd, 50, 0.1, 2),
                                 circle_cloud(rd, 50, 0.1, 3), rn)

def r3_neg(rd, rn): return cca_trial(rd.normal(size=(160, 15)),
                                     rd.normal(size=(160, 15)), rn, m=99)[0]
def r3_pos(rd, rn):
    z = rd.normal(size=(160, 3))
    X = z @ rd.normal(size=(3, 15)) + 0.7 * rd.normal(size=(160, 15))
    Y = z @ rd.normal(size=(3, 15)) + 0.7 * rd.normal(size=(160, 15))
    return cca_trial(X, Y, rn, m=99)[0]

def r4_neg(rd, rn): return tda_trial(rd.normal(size=(100, 2)), rn, m=M_NULL)
def r4_pos(rd, rn): return tda_trial(circle_cloud(rd, 100, 0.15, 2), rn, m=M_NULL)

def _spec_p(GA, GB, rn, m=M_NULL):
    obs = -spectral_distance(GA, GB)
    nulls = [-spectral_distance(GA, rewired(GB, rn)) for _ in range(m)]
    return p_perm(obs, nulls)
def r5_neg(rd, rn):
    import networkx as nx
    GA = nx.gnp_random_graph(100, 0.06, seed=int(rd.integers(2**31)))
    GB = nx.gnp_random_graph(100, 0.06, seed=int(rd.integers(2**31)))
    return _spec_p(GA, GB, rn)
def r5_pos(rd, rn): return _spec_p(sbm_graph(rd, 120), sbm_graph(rd, 100), rn)

def r6_neg(rd, rn): return nystrom_trial(rd.normal(size=(150, 8)), rn, m=49)
def r6_pos(rd, rn): return nystrom_trial(swiss_roll(rd, 150), rn, m=49)

def r7_neg(rd, rn): return completion_trial(rd.normal(size=(60, 40)), rn, m=M_NULL)
def r7_pos(rd, rn):
    M = (rd.normal(size=(60, 2)) @ rd.normal(size=(2, 40))
         + 0.1 * rd.normal(size=(60, 40)))
    return completion_trial(M, rn, m=M_NULL)

REGISTRY = {
    # key: (name, neg_trial, pos_trial, m_of_trial)
    "r1": ("R1_mmd_energy", r1_neg, r1_pos, 99),
    "r2": ("R2_gromov_wasserstein", r2_neg, r2_pos, M_NULL),
    "r3": ("R3_cca_family", r3_neg, r3_pos, 99),
    "r4": ("R4_tda_persistence", r4_neg, r4_pos, M_NULL),
    "r5": ("R5_graph_matching_spectra", r5_neg, r5_pos, M_NULL),
    "r6": ("R6_coresets_landmarks_nystrom", r6_neg, r6_pos, 49),
    "r7": ("R7_matrix_completion", r7_neg, r7_pos, M_NULL),
}


def trial_streams(key, kind, i):
    """Per-trial independent seeded streams so execution can be chunked and
    resumed across processes with identical results to a monolithic run.
    (Sandbox execution detail; design — statistics, n, m, effects — unchanged.)"""
    off = list(REGISTRY).index(key)
    tag = 0 if kind == "neg" else 1
    return (np.random.default_rng((SEED, 10 + off, tag, i)),
            np.random.default_rng((SEED, 100 + off, tag, i)))


def run_chunk(key, kind, start, count, store):
    """Compute trials [start, start+count) for key/kind into store (list)."""
    _, fneg, fpos, _ = REGISTRY[key]
    f = fneg if kind == "neg" else fpos
    for i in range(start, start + count):
        rd, rn = trial_streams(key, kind, i)
        store.append(f(rd, rn))


def run_one(key, smoke=False, res=None):
    """Full run with resume: partial trial p's persist in the output JSON
    under '<name>_PARTIAL'; repeated invocations continue until n reached."""
    name, fneg, fpos, m_trial = REGISTRY[key]
    n_neg = 25 if smoke else N_NEG
    n_pos = 15 if smoke else N_POS
    if smoke:
        neg, pos = [], []
        run_chunk(key, "neg", 0, n_neg, neg)
        run_chunk(key, "pos", 0, n_pos, pos)
    else:
        part = (res or {}).get(name + "_PARTIAL", {"neg": [], "pos": []})
        neg, pos = part["neg"], part["pos"]
        import time
        t0 = time.time()
        while len(neg) < n_neg and time.time() - t0 < CHUNK_SECONDS:
            run_chunk(key, "neg", len(neg), 1, neg)
        while len(neg) >= n_neg and len(pos) < n_pos and \
                time.time() - t0 < CHUNK_SECONDS:
            run_chunk(key, "pos", len(pos), 1, pos)
        if res is not None:
            res[name + "_PARTIAL"] = {"neg": neg, "pos": pos}
        if len(neg) < n_neg or len(pos) < n_pos:
            return {"verdict": "IN_PROGRESS",
                    "done": {"neg": len(neg), "pos": len(pos)},
                    "of": {"neg": n_neg, "pos": n_pos}}
    g_neg = gate_negative(neg, n_neg, "negative control", m_trial)
    g_pos = gate_positive(pos, "positive control (declared effect)")
    verdict = ("SMOKE_ONLY" if smoke else
               "ADMITTED_V2" if g_neg["passed"] and g_pos["passed"] else
               "EXPLORATORY_ONLY")
    if res is not None and not smoke:
        res.pop(name + "_PARTIAL", None)
    return {"negative": g_neg, "positive": g_pos, "verdict": verdict,
            "m_null_min": M_NULL, "floor": round(1 / (M_NULL + 1), 4),
            "rng_streams": "split per-trial data/null streams (m6 fix; "
                           "chunk-resumable, seed-derived)"}


def main(argv):
    smoke = "--smoke" in argv
    keys = [a for a in argv if a in REGISTRY] or list(REGISTRY)
    design = {"seed": SEED, "alpha": ALPHA, "n_neg": N_NEG, "n_pos": N_POS,
              "m_null_min": M_NULL,
              "design_hash": hashlib.sha256(
                  open(__file__, "rb").read()).hexdigest()[:16]}
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    res["_design"] = design
    for k in keys:
        # smoke results live under a separate key so a later --smoke can
        # never overwrite a full-run verdict (adversarial review M3)
        out_key = REGISTRY[k][0] + ("_SMOKE" if smoke else "")
        if isinstance(res.get(out_key), dict) and \
                res[out_key].get("verdict") in ("ADMITTED_V2",
                                                "EXPLORATORY_ONLY"):
            print(f"== {out_key} already complete; skipping")
            continue
        print(f"== {out_key}")
        res[out_key] = run_one(k, smoke, res=res)
        json.dump(res, open(OUT, "w"), indent=2)
        print(json.dumps(res[out_key], indent=1)[:400])
    print("written", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
