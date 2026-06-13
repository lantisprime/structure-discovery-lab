"""argument_principle_check.py -- "no zero missed" count cross-check (validation #6).

Two independent counts of non-trivial zeros up to a height, neither of which uses the
sign-change search:

  (A) Riemann-von Mangoldt analytic count  N(T) = theta(T)/pi + 1 + S(T).
  (B) Contour argument principle           Nc = (1/2pi i) oint zeta'/zeta ds  around a
      rectangle enclosing the critical strip 0<Re<1 up to height T0 -- counts zeros
      (with multiplicity) strictly inside, anywhere in the strip (on OR off the line).

(A) is compared to the number of located zeros; (B) on a modest sub-range gives a strip
count that, equal to the on-line count there, certifies no zero was missed *in that strip up
to T0* -- a finite verification, explicitly NOT a proof of RH (see kb/riemann-hypothesis).

Usage: python argument_principle_check.py [--in results/zeta_zeros_batch1.json]
       [--t0 31.0]   # contour height for the strip check (default encloses first 4 zeros)
"""
import os
import sys
import json
import argparse
from mpmath import mp, mpf, mpc, zeta, quad, pi, nstr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hardy_z import N_exact_formula, nzeros  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "..", "results", "zeta_zeros_batch1.json")
DEFAULT_OUT = os.path.join(HERE, "..", "results", "zeta_zero_count_batch1.json")


def logderiv(s):
    """zeta'(s)/zeta(s) via mpmath (zeta with derivative=1)."""
    return zeta(s, 1, derivative=1) / zeta(s)


def contour_count(T0, a=mpf("0.0"), b=mpf("1.0"), y0=mpf("0.5")):
    """(1/2pi i) oint zeta'/zeta ds around rectangle [a,b] x [y0,T0].

    No zeros lie on Re=0 or Re=1 (PNT) and the bottom edge y0 sits below the first zero,
    so the contour encloses exactly the non-trivial zeros with y0 < Im < T0.
    """
    # four directed edges of the rectangle (counter-clockwise)
    bottom = quad(lambda x: logderiv(mpc(x, y0)), [a, b])              # left->right
    right = quad(lambda y: logderiv(mpc(b, y)) * 1j, [y0, T0])         # bottom->top
    top = quad(lambda x: logderiv(mpc(x, T0)), [b, a])                 # right->left
    left = quad(lambda y: logderiv(mpc(a, y)) * 1j, [T0, y0])          # top->bottom
    total = bottom + right + top + left
    return total / (2j * pi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=DEFAULT_IN)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--t0", type=float, default=31.0,
                    help="contour height for the strip check (default ~first 4 zeros)")
    args = ap.parse_args()

    with open(args.inp) as f:
        payload = json.load(f)
    records = payload["zeros"]

    # (A) analytic N(T) vs located count, at the full height
    mp.dps = 30
    t_last = mpf(records[-1]["t_imag"])
    T = t_last + mpf("0.5")
    n_formula = N_exact_formula(T)
    n_round = int(round(float(n_formula)))
    n_mpmath = int(nzeros(T))
    located = len(records)
    count_match = (n_round == located == n_mpmath)

    # (B) contour argument principle on the sub-range [0, T0]
    mp.dps = 25
    T0 = mpf(str(args.t0))
    located_below_T0 = sum(1 for r in records if mpf(r["t_imag"]) < T0)
    Nc = contour_count(T0)
    Nc_real = float(Nc.real)
    Nc_round = int(round(Nc_real))
    contour_match = (Nc_round == located_below_T0)

    report = {
        "module": "riemann-zero-lab",
        "analytic_count": {
            "T": nstr(T, 12),
            "N_formula": nstr(n_formula, 10),
            "N_formula_round": n_round,
            "nzeros_mpmath": n_mpmath,
            "located": located,
            "match": bool(count_match),
        },
        "contour_argument_principle": {
            "T0": float(args.t0),
            "integral": f"{Nc_real:.6f} + {float(Nc.imag):.2e}i",
            "Nc_round": Nc_round,
            "located_below_T0": located_below_T0,
            "match": bool(contour_match),
            "note": "counts zeros in the whole strip 0<Re<1 up to T0; equal to the on-line "
                    "count here => no zero missed in this strip up to T0 (finite check, not RH).",
        },
        "overall_pass": bool(count_match and contour_match),
    }
    out = os.path.abspath(args.out)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    print(f"(A) located {located} vs N(T)={n_round} vs nzeros={n_mpmath} -> {count_match}")
    print(f"(B) contour Nc={Nc_round} vs located<{args.t0}={located_below_T0} -> {contour_match}")
    print(f"OVERALL: {'PASS' if report['overall_pass'] else 'FAIL'} -> {out}")
    sys.exit(0 if report["overall_pass"] else 1)


if __name__ == "__main__":
    main()
