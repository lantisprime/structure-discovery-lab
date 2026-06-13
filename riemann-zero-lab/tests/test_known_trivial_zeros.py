"""Regression: the trivial zeros of zeta are at s = -2, -4, -6, ... (validation #1).

Run: pytest tests/test_known_trivial_zeros.py   (or: python tests/test_known_trivial_zeros.py)
"""
import os
import sys
from mpmath import mp, mpf, zeta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def test_trivial_zeros_are_zero():
    mp.dps = 60
    for k in range(1, 11):                 # s = -2, -4, ..., -20
        s = -2 * k
        assert abs(zeta(s)) < mpf("1e-45"), f"zeta({s}) not ~0: {zeta(s)}"


def test_negative_odd_and_offsets_are_not_zero():
    """Sanity: nearby non-trivial-even points are NOT zeros (guards a vacuous test)."""
    mp.dps = 60
    for s in (-1, -3, -5, -2.5, -4.5):
        assert abs(zeta(s)) > mpf("1e-3"), f"zeta({s}) unexpectedly ~0"


def test_zeta_minus_one_value():
    """zeta(-1) = -1/12 (a known special value, not a zero)."""
    mp.dps = 50
    assert abs(zeta(-1) - mpf(-1) / 12) < mpf("1e-45")


if __name__ == "__main__":
    test_trivial_zeros_are_zero()
    test_negative_odd_and_offsets_are_not_zero()
    test_zeta_minus_one_value()
    print("test_known_trivial_zeros: PASS")
