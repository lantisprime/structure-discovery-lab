"""spacing_analysis.py -- unfolded nearest-neighbour spacing of zeta zeros vs GUE & Poisson.

Secondary task (registered, DESCRIPTIVE / EXPLORATORY -- not a confirmatory test at N~200,
low height). KB: zeta-zero-spacing.md, random-matrix-gue.md.

Steps:
  1. unfold ordinates: w_n = Ntilde(gamma_n) = theta(gamma_n)/pi + 1  (unit mean spacing).
  2. nearest-neighbour spacings s_n = w_{n+1} - w_n  (mean ~ 1 by construction).
  3. compare empirical CDF to:
       - Poisson (no repulsion):  F(s) = 1 - exp(-s),  P(s<0.5)=0.3935
       - GUE Wigner surmise (beta=2): p(s)=(32/pi^2) s^2 exp(-4 s^2/pi),
         closed-form CDF F(s)=erf(2s/sqrt(pi)) - (4s/pi) exp(-4 s^2/pi),  P(s<0.5)=0.0402
  4. one-sample KS statistic D to each, with asymptotic p-value (caveated: consecutive
     spacings are weakly dependent, so p is indicative only).

The headline discriminator is P(s<0.5): Poisson ~0.39 vs GUE ~0.04. No "confirms GUE" claim
is made -- only "GUE-like repulsion, not Poisson, at this resolution" (Article A4).

Usage: python spacing_analysis.py [--in results/zeta_zeros_batch1.json]
"""
import os
import sys
import json
import math
import argparse
from mpmath import mp, mpf
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hardy_z import N_smooth  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "..", "results", "zeta_zeros_batch1.json")
DEFAULT_OUT = os.path.join(HERE, "..", "results", "zeta_zero_spacing_batch1.json")


def poisson_cdf(s):
    return 1.0 - math.exp(-s)


def gue_cdf(s):
    """Closed-form CDF of the GUE (beta=2) Wigner surmise, normalized to unit mean."""
    return math.erf(2.0 * s / math.sqrt(math.pi)) - (4.0 * s / math.pi) * math.exp(-4.0 * s * s / math.pi)


def ks_statistic(samples, cdf):
    """One-sample two-sided Kolmogorov-Smirnov D against a theoretical cdf."""
    xs = np.sort(np.asarray(samples, dtype=float))
    m = len(xs)
    F = np.array([cdf(x) for x in xs])
    i = np.arange(1, m + 1)
    d_plus = np.max(i / m - F)
    d_minus = np.max(F - (i - 1) / m)
    return float(max(d_plus, d_minus))


def ks_pvalue(D, m):
    """Asymptotic KS p-value Q(lambda), lambda=(sqrt m + 0.12 + 0.11/sqrt m) D."""
    lam = (math.sqrt(m) + 0.12 + 0.11 / math.sqrt(m)) * D
    if lam < 1e-9:
        return 1.0
    s = 0.0
    for k in range(1, 101):
        s += (-1) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
    return float(max(0.0, min(1.0, 2.0 * s)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=DEFAULT_IN)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--dps", type=int, default=50)
    args = ap.parse_args()
    mp.dps = args.dps

    with open(args.inp) as f:
        payload = json.load(f)
    ordinates = [mpf(r["t_imag"]) for r in payload["zeros"]]

    # (1) unfold, (2) spacings
    w = [N_smooth(t) for t in ordinates]
    spac = [float(w[i + 1] - w[i]) for i in range(len(w) - 1)]
    spac_arr = np.asarray(spac, dtype=float)
    m = len(spac_arr)

    # (3)-(4) comparisons
    d_gue = ks_statistic(spac_arr, gue_cdf)
    d_poi = ks_statistic(spac_arr, poisson_cdf)
    frac_small_emp = float(np.mean(spac_arr < 0.5))

    report = {
        "module": "riemann-zero-lab",
        "status": "DESCRIPTIVE / EXPLORATORY (N~200, low height t<=%.1f; not confirmatory)"
                  % float(ordinates[-1]),
        "n_zeros": len(ordinates),
        "n_spacings": m,
        "unfolding": "w_n = theta(gamma_n)/pi + 1 (Riemann-von Mangoldt smooth count)",
        "mean_spacing": round(float(np.mean(spac_arr)), 6),
        "std_spacing": round(float(np.std(spac_arr, ddof=1)), 6),
        "min_spacing": round(float(np.min(spac_arr)), 6),
        "max_spacing": round(float(np.max(spac_arr)), 6),
        "frac_below_0.5": {
            "empirical": round(frac_small_emp, 4),
            "GUE_pred": round(gue_cdf(0.5), 4),
            "Poisson_pred": round(poisson_cdf(0.5), 4),
        },
        "ks_vs_GUE": {"D": round(d_gue, 4), "p_indicative": round(ks_pvalue(d_gue, m), 4)},
        "ks_vs_Poisson": {"D": round(d_poi, 4), "p_indicative": round(ks_pvalue(d_poi, m), 4)},
        "histogram": _histogram(spac_arr),
        "verdict": _verdict(d_gue, d_poi, frac_small_emp),
        "caveats": [
            "Asymptotic GUE law; at low height the empirical repulsion is biased weaker.",
            "Consecutive spacings are weakly dependent => KS p-values are indicative only.",
            "Endpoint spacings truncated; N-1 spacings reported.",
            "A 'fails to reject Poisson' would be a power statement, not evidence of no "
            "repulsion (Article A4).",
        ],
    }
    out = os.path.abspath(args.out)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    print(f"spacings: {m} | mean={report['mean_spacing']} | "
          f"P(s<0.5) emp={frac_small_emp:.3f} GUE={gue_cdf(0.5):.3f} Poi={poisson_cdf(0.5):.3f}")
    print(f"KS D: GUE={d_gue:.4f}  Poisson={d_poi:.4f} | verdict: {report['verdict']}")
    print(f"wrote -> {out}")


def _histogram(s, edges=None):
    if edges is None:
        edges = [i * 0.25 for i in range(0, 13)]  # 0..3 in 0.25 bins
    counts, _ = np.histogram(s, bins=edges)
    return {"edges": edges, "counts": [int(c) for c in counts]}


def _verdict(d_gue, d_poi, frac_small):
    closer = "GUE" if d_gue < d_poi else "Poisson"
    return (f"empirical spacing is closer to {closer} (KS); small-gap fraction "
            f"{frac_small:.3f} {'supports' if frac_small < 0.2 else 'does not clearly support'} "
            f"level repulsion. Descriptive only.")


if __name__ == "__main__":
    main()
