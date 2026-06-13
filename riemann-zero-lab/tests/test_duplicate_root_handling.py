"""Regression: no duplicate / out-of-order roots; the min-separation guard works (validation #5).

Run: pytest tests/test_duplicate_root_handling.py
"""
import os
import sys
import pytest
from mpmath import mp, mpf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import find_zeta_zeros as fz  # noqa: E402


def test_found_roots_strictly_increasing_and_separated():
    mp.dps = 50
    roots = fz.find_zeros(25)
    assert len(roots) == 25
    for a, b in zip(roots, roots[1:]):
        assert b > a, "roots not strictly increasing"
        assert (b - a) > fz.MIN_SEP, f"roots within MIN_SEP: {a}, {b}"
    # first-zero spacing sanity: consecutive zeta zeros are never closer than ~0.5 this low
    gaps = [float(b - a) for a, b in zip(roots, roots[1:])]
    assert min(gaps) > 0.5


def test_no_duplicates_in_index_set():
    mp.dps = 40
    roots = fz.find_zeros(25)
    as_strings = {str(r) for r in roots}
    assert len(as_strings) == len(roots), "duplicate ordinate produced"


def test_guard_rejects_too_close_root(monkeypatch):
    """If refinement ever returned a root within MIN_SEP of the previous, find_zeros raises.

    Simulate by forcing _refine to return a value collapsed onto the last accepted root.
    """
    mp.dps = 40
    real_refine = fz._refine
    state = {"calls": 0, "last": None}

    def fake_refine(a, b):
        r = real_refine(a, b)
        state["calls"] += 1
        if state["calls"] == 2 and state["last"] is not None:
            return state["last"] + fz.MIN_SEP / 10   # within the guard band
        state["last"] = r
        return r

    monkeypatch.setattr(fz, "_refine", fake_refine)
    with pytest.raises(RuntimeError):
        fz.find_zeros(5)


if __name__ == "__main__":
    test_found_roots_strictly_increasing_and_separated()
    test_no_duplicates_in_index_set()
    print("test_duplicate_root_handling: PASS (run via pytest for the monkeypatch guard test)")
