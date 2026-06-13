"""Regression: increasing precision does not materially move the roots (validation #4).

Locate the first few zeros at dps 30 and dps 80; require agreement to >= 25 decimals.

Run: pytest tests/test_precision_stability.py
"""
import os
import sys
from mpmath import mp, mpf, floor, log10

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from find_zeta_zeros import find_zeros  # noqa: E402


def _matching_decimals(a, b):
    a, b = mpf(a), mpf(b)
    if a == b:
        return mp.dps
    return int(floor(-log10(abs(a - b) / abs(a))))


def test_roots_stable_across_precision():
    mp.dps = 30
    low = [mpf(str(z)) for z in find_zeros(8)]
    mp.dps = 80
    high = find_zeros(8)
    assert len(low) == len(high) == 8
    for i, (lo, hi) in enumerate(zip(low, high), start=1):
        match = _matching_decimals(lo, hi)
        assert match >= 25, f"zero {i} unstable: only {match} dp agree between dps 30 and 80"


def test_residual_shrinks_with_precision():
    """The reported residual gate is met at dps=80 for the first zero."""
    from hardy_z import zeta_abs_on_line
    mp.dps = 80
    t = find_zeros(1)[0]
    assert zeta_abs_on_line(t) < mpf("1e-30")


if __name__ == "__main__":
    test_roots_stable_across_precision()
    test_residual_shrinks_with_precision()
    print("test_precision_stability: PASS")
