"""Independent reproducibility check for Synthetic Batch 1, Experiment A.

Recomputes every *derived* frontier field stored in
results/synthetic_batch1_expA.json from first principles — the registered
constants and the realized delta-hat — WITHOUT importing the run script's
theory(), so it is a genuine cross-check rather than a tautology. Asserts that
the stored 1-df oracle, df-(P-1) omnibus, and sparse-scan frontier values agree
with this independent recomputation.

This exists because the df54 / sparse-scan fields were originally added
out-of-band; this script (plus the now-patched theory()) makes them
reproducible from source. See docs/RESULTS_SYNTHETIC_BATCH1.md
"Registration deviations".

Usage:  python verify_synthetic_batch1.py        # prints table, exits 0/1
Exit code 0 = all fields reproduce within tolerance; 1 = mismatch.
"""
import json, os, sys

import numpy as np
from scipy.stats import norm, chi2, ncx2
from scipy.optimize import brentq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domains import synthetic_lottery as sl

HERE = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(HERE, "..", "results", "synthetic_batch1_expA.json")

# tolerances: ncx2 inversion is solver-dependent in its last digits, so compare
# relatively rather than for byte-equality.
RTOL_NMIN, RTOL_LAM = 1e-6, 1e-6


def lam_star(df, aprime, beta=0.20):
    crit = chi2.ppf(1 - aprime, df)
    return float(brentq(lambda lam: ncx2.sf(crit, df, lam) - (1 - beta),
                        1e-9, 1e4))


def sigma0_pinv(P):
    p0 = 6.0 / P
    p2 = 30.0 / (P * (P - 1))
    S = np.full((P, P), p2 - p0 ** 2)
    np.fill_diagonal(S, p0 * (1 - p0))
    return np.linalg.pinv(S)


def main():
    d = json.load(open(JSON))
    meta = d["meta"]
    P, BALL = meta["P"], meta["ball"]
    aprime = meta["alpha_prime"]
    p0 = 6.0 / P
    Sp = sigma0_pinv(P)

    zsum2 = (norm.ppf(1 - aprime) + norm.ppf(0.80)) ** 2          # 1-df Wald
    lam54 = lam_star(P - 1, aprime)                              # omnibus df=P-1
    zss = (norm.ppf(1 - aprime / (2 * P)) + norm.ppf(0.80)) ** 2  # sparse scan

    rows, ok = [], True

    def chk(label, got, exp, rtol):
        nonlocal ok
        if exp is None:
            return
        rel = abs(got - exp) / max(abs(exp), 1e-12)
        passed = rel <= rtol
        ok = ok and passed
        rows.append((label, exp, got, rel, "PASS" if passed else "FAIL"))

    # block-level prefactors
    ls = d["theory"].get("_lambda_star", {})
    ss = d["theory"].get("_sparse_scan", {})
    chk("_lambda_star.df1", zsum2, ls.get("df1"), RTOL_LAM)
    chk("_lambda_star.df54", lam54, ls.get("df54"), RTOL_LAM)
    chk("_sparse_scan.z_sum_sq", zss, ss.get("z_sum_sq"), RTOL_LAM)

    # per-r frontiers, recomputed from a fresh realized delta-hat
    for r in [0.05, 0.10, 0.20, 0.40, 0.80]:
        key = str(r)
        if key not in d["theory"]:
            continue
        t = d["theory"][key]
        spec = sl.single_ball_spec(P, BALL, r * p0)
        dh = sl.realized_delta(spec, K=200_000)          # deterministic (MASTER_SEED)
        lam1 = float(dh @ Sp @ dh)
        d_hot = float(dh[BALL - 1])
        chk(f"r={r} lambda1", lam1, t.get("lambda1"), RTOL_NMIN)
        chk(f"r={r} realized_hot_delta", d_hot, t.get("realized_hot_delta"), RTOL_NMIN)
        chk(f"r={r} n_min_theory(1df)", zsum2 / lam1, t.get("n_min_theory"), RTOL_NMIN)
        chk(f"r={r} n_min_theory_df54", lam54 / lam1, t.get("n_min_theory_df54"), RTOL_NMIN)
        chk(f"r={r} n_min_sparse_scan", zss * p0 * (1 - p0) / d_hot ** 2,
            t.get("n_min_theory_sparse_scan"), RTOL_NMIN)

    w = max(len(r[0]) for r in rows)
    print(f"{'field'.ljust(w)}  {'stored':>16}  {'recomputed':>16}  {'rel':>10}  status")
    for label, exp, got, rel, status in rows:
        print(f"{label.ljust(w)}  {exp:16.6f}  {got:16.6f}  {rel:10.2e}  {status}")
    print(f"\n{'ALL FIELDS REPRODUCE' if ok else 'MISMATCH DETECTED'} "
          f"({sum(r[4]=='PASS' for r in rows)}/{len(rows)} within rtol={RTOL_NMIN})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
