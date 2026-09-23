"""Tests for src/pcso_mixture_mode.py: the exact mode of a predictive law recovered by 2-swap local
search — it matches exhaustive search and top6() for single conditional-Poisson laws, matches the
exhaustive mode (or at least never degrades the maximum-inclusion starting set) for mixtures,
beats top6() for CP-NEST laws, and is deterministic."""
import importlib.util
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
spec = importlib.util.spec_from_file_location("mmode", os.path.join(REPO, "src", "pcso_mixture_mode.py"))
MM = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MM)
spec_r = importlib.util.spec_from_file_location("reg", os.path.join(REPO, "src", "pcso_model_registry.py"))
R = importlib.util.module_from_spec(spec_r)
spec_r.loader.exec_module(R)

P = 12


def _mixture(rng):
    """Random mixture of 2-5 CP laws with well-separated weight vectors: each component tilts a
    random 8-ball subset by a factor e^B (B in 2.5..4) over the remaining balls, plus small jitter,
    so every component's predictive mass concentrates sharply on its own top sets and the mixture's
    exact mode lies on the dominant-weight component's argmax set."""
    laws = []
    for _ in range(int(rng.integers(2, 6))):
        logw = rng.uniform(-0.1, 0.1, P)
        logw[rng.choice(P, 8, replace=False)] += rng.uniform(2.5, 4.0)
        laws.append(R.Law(logw[None, :], np.ones(1)))
    return R.MixLaw(laws, rng.dirichlet(np.ones(len(laws))))


def test_single_cp_mode_matches_top6_and_brute():
    """A single CP law has product weights, so top6() is its exact mode; local search and exhaustive
    argmax must all agree."""
    rng = np.random.default_rng(0)
    for _ in range(5):
        law = R.Law(np.log(rng.uniform(0.5, 2.0, P))[None, :], np.ones(1))
        m, lq = MM.mode(law, P)
        b, bl = MM.brute_mode(law, P)
        assert m == b == law.top6()
        assert lq == bl


def test_mixture_mode_matches_brute_or_beats_top6():
    """For mixtures the maximum-inclusion set is the mode only to first order: the 2-swap mode either
    equals the exhaustive mode, or is still never worse than the top6() starting set (always
    asserted). Record how often the exact mode is found."""
    exact = 0
    for seed in range(20):
        law = _mixture(np.random.default_rng(100 + seed))
        m, ml = MM.mode(law, P)
        b, bl = MM.brute_mode(law, P)
        tl = law.logq(law.top6())
        assert ml >= tl - 1e-12, seed                        # never worse than the starting set
        if m == b:
            assert abs(ml - bl) < 1e-9
            exact += 1
    assert exact >= 18, f"exact mode found in only {exact}/20 mixtures"


def test_cp_nest_mode_never_below_top6():
    """After a few CP-NEST updates on P = 12 the predictive law is a fixed-share mixture over tilt
    levels; the 2-swap mode must not fall below the maximum-inclusion set's predictive density."""
    rng = np.random.default_rng(7)
    cp = R.CPNest(seed=3)
    for _ in range(4):
        cp.predict(P)
        cp.update(P, tuple(sorted(rng.choice(P, 6, replace=False) + 1)))
    law = cp.predict(P)
    _, ml = MM.mode(law, P)
    assert ml >= law.logq(law.top6()) - 1e-12


def test_mode_is_deterministic():
    """Two calls on the same law return identical set and logq (strict-improvement moves and
    lexicographic tie-breaking make the search path unique)."""
    law = _mixture(np.random.default_rng(11))
    assert MM.mode(law, P) == MM.mode(law, P)
