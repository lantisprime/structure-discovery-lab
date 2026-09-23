"""Exact checks of the low-dimensional tilt evidence process (src/pcso_lowdim_eprocess.py):
f_theta is a probability law on 6-sets, the mixture predictive is too (so every Lambda_t has
unit mean under uniform draws — the martingale property Ville's inequality needs), and the
exact law of m = #{i > cut} matches enumeration."""
import importlib.util
import itertools
import math
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
spec = importlib.util.spec_from_file_location("lowdim", os.path.join(REPO, "src", "pcso_lowdim_eprocess.py"))
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

P_SMALL, CUT = 10, 6


def _sets():
    return list(itertools.combinations(range(1, P_SMALL + 1), L.K))


def _g_split():
    return L.standardise((np.arange(1, P_SMALL + 1) > CUT).astype(float))


def test_f_theta_is_a_probability_law():
    for g in (L.g_index(P_SMALL), _g_split()):
        A = L.Alt(g)
        tot = np.zeros(len(L.THETA))
        for S in _sets():
            tot += np.exp(A.log_f(float(g[np.array(S) - 1].sum())))
        assert np.allclose(tot, 1.0, atol=1e-10)


def test_mixture_predictive_has_unit_mean_under_uniform():
    g = L.g_index(P_SMALL)
    A = L.Alt(g)
    rng = np.random.default_rng(0)
    lp = L.log_prior() + rng.normal(0, 3, len(L.THETA))       # any predictable posterior
    lp -= L.lse(lp)
    p0 = 1 / math.comb(P_SMALL, L.K)
    mean_lambda = sum(p0 * math.exp(float(L.lse(lp + A.log_f(float(g[np.array(S) - 1].sum())))) - A.log_p0)
                      for S in _sets())
    assert abs(mean_lambda - 1.0) < 1e-10


def test_m_law_matches_enumeration():
    g = _g_split()
    A = L.Alt(g)
    j = 120                                                   # theta = +0.2
    exact = np.zeros(L.K + 1)
    for S in _sets():
        exact[sum(1 for v in S if v > CUT)] += math.exp(A.log_f(float(g[np.array(S) - 1].sum()))[j])
    assert np.allclose(L.m_probs(P_SMALL, float(L.THETA[j]), g, cut=CUT), exact, atol=1e-12)
