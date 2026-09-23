"""Conformance tests for src/pcso_model_registry.py: every registered model's predictive law is a
normalized distribution on 6-sets after arbitrary past draws (the property that makes its evidence
process valid), inclusion probabilities sum to 6, and the exact conditional-Poisson sampler draws
from f_w."""
import importlib.util
import itertools
import math
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
spec = importlib.util.spec_from_file_location("reg", os.path.join(REPO, "src", "pcso_model_registry.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

P = 9


def _models():
    return [R.Uniform(), R.DirichletCP(samples=64, seed=1), R.TiltGrid(0, "linear"), R.ParityPair(), R.CPNest(seed=2),
            R.Ensemble([R.Uniform(), R.TiltGrid(0, "linear"), R.ParityPair(), R.CPNest(seed=3)])]


def test_predictive_law_is_a_function_of_seed_and_past_only():
    """Predictability gate (design review, Kimi K3, item 2): predict() never sees S_t, and two copies
    with the same seed and history emit bit-identical laws."""
    rng = np.random.default_rng(5)
    hist = [tuple(sorted(rng.choice(P, 6, replace=False) + 1)) for _ in range(8)]
    a, b = R.CPNest(seed=9, M=16), R.CPNest(seed=9, M=16)
    for S in hist:
        la, lb = a.predict(P), b.predict(P)
        assert np.array_equal(la.logw, lb.logw) and np.array_equal(la.a, lb.a)
        a.update(P, S)
        b.update(P, S)


def test_inclusion_matches_enumeration():
    w = np.random.default_rng(6).uniform(0.5, 2.0, 10)
    law = R.Law(np.log(w)[None, :], np.ones(1))
    exact = np.zeros(10)
    for S in itertools.combinations(range(1, 11), 6):
        p = math.exp(law.logq(S))
        for i in S:
            exact[i - 1] += p
    assert np.allclose(law.inclusion(), exact, atol=1e-12)


def test_sr_recursion_equals_weighted_sum_of_restarted_processes():
    rng = np.random.default_rng(3)
    L = rng.uniform(0.3, 2.0, 40)
    M = 0.0
    for t, l in enumerate(L, start=1):
        M = l * (M + 1.0 / (t * (t + 1)))
        brute = sum(np.prod(L[j - 1:t]) / (j * (j + 1)) for j in range(1, t + 1))
        assert abs(M - brute) < 1e-12 * max(1.0, brute)


def test_confidence_sequence_is_nested_and_contains_map():
    m = R.TiltGrid(0, "linear")
    rng = np.random.default_rng(4)
    for _ in range(50):
        m.predict(P)
        m.update(P, tuple(sorted(rng.choice(P, 6, replace=False) + 1)))
    c95, c99 = m.cs(0.05), m.cs(0.01)
    assert c99[0] <= c95[0] <= c95[1] <= c99[1]
    theta_map = float(R.THETA[np.argmax(m.lp)])
    assert c95[0] <= theta_map <= c95[1]


def test_every_model_predicts_a_normalized_law():
    rng = np.random.default_rng(0)
    history = [tuple(sorted(rng.choice(P, 6, replace=False) + 1)) for _ in range(12)]
    for m in _models():
        for S in history:
            m.predict(P)
            m.update(P, S)
        law = m.predict(P)
        total = sum(math.exp(law.logq(S)) for S in itertools.combinations(range(1, P + 1), 6))
        assert abs(total - 1.0) < 1e-10, m.name
        assert abs(law.inclusion().sum() - 6.0) < 1e-9, m.name


def test_sampler_matches_conditional_poisson_law():
    rng = np.random.default_rng(1)
    logw = np.log(np.array([1.0, 1.4, 0.7, 1.1, 0.9, 1.3, 0.8]))
    law = R.Law(logw[None, :], np.ones(1))
    sets = list(itertools.combinations(range(1, 8), 6))
    exact = np.array([math.exp(law.logq(S)) for S in sets])
    n = 40000
    freq = np.zeros(len(sets))
    for _ in range(n):
        freq[sets.index(R.sample_cp(rng, logw))] += 1
    assert np.max(np.abs(freq / n - exact)) < 0.01
