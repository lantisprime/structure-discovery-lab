"""Regression: the finder recovers the first known non-trivial ordinates (validation #2, #3).

Two independent references:
  - hardcoded published ordinates gamma_1..gamma_10 (Odlyzko / LMFDB), matched to 15 dp;
  - mpmath.zetazero(n) (independent algorithm), matched to 40 dp.

Run: pytest tests/test_known_nontrivial_zeros.py
"""
import os
import sys
from mpmath import mp, mpf, floor, log10, zetazero

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from find_zeta_zeros import find_zeros  # noqa: E402

# Published first ten ordinates (30-digit references).
REF = [
    "14.134725141734693790457251983562",
    "21.022039638771554992628479593897",
    "25.010857580145688763213790992563",
    "30.424876125859513210311897530584",
    "32.935061587739189690662368964075",
    "37.586178158825671257217763480705",
    "40.918719012147495187398126914633",
    "43.327073280914999519496122165406",
    "48.005150881167159727942472749427",
    "49.773832477672302181916784678564",
]


def _matching_decimals(a, b):
    a, b = mpf(a), mpf(b)
    if a == b:
        return mp.dps
    return int(floor(-log10(abs(a - b) / abs(a))))


def test_first_zero_near_14_134725():
    mp.dps = 50
    z = find_zeros(1)[0]
    assert abs(z - mpf("14.134725141734693790")) < mpf("1e-15")


def test_first_ten_match_published_references():
    mp.dps = 60
    found = find_zeros(10)
    assert len(found) == 10
    for i, (f, r) in enumerate(zip(found, REF), start=1):
        assert _matching_decimals(f, r) >= 15, \
            f"zero {i}: {f} vs ref {r} (match {_matching_decimals(f, r)} dp)"


def test_first_ten_match_mpmath_zetazero():
    mp.dps = 60
    found = find_zeros(10)
    for i, f in enumerate(found, start=1):
        gamma = zetazero(i).imag
        assert _matching_decimals(f, gamma) >= 40, \
            f"zero {i}: finder vs zetazero match only {_matching_decimals(f, gamma)} dp"


if __name__ == "__main__":
    test_first_zero_near_14_134725()
    test_first_ten_match_published_references()
    test_first_ten_match_mpmath_zetazero()
    print("test_known_nontrivial_zeros: PASS")
