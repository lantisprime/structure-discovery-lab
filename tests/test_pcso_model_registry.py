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


def test_run_registered_boundary_and_fresh_statistics():
    """Registered-window accounting (design review, required change 1): rows dated <=
    REGISTERED_AFTER (the boundary date itself included) only condition the models; the first
    registered draw's E equals q(S)/p0(S), and M after k registered draws follows
    M_t = L_t (M_{t-1} + 1/(t(t+1))) from M_0 = 0."""
    P, C = 9, math.comb(9, 6)
    pre = [("2026-09-21", P, (1, 2, 3, 4, 5, 6)),
           ("2026-09-23", P, (2, 3, 4, 5, 6, 7))]          # boundary date: still conditioning only
    reg = [("2026-09-24", P, (1, 2, 3, 4, 5, 7)),
           ("2026-09-26", P, (3, 4, 5, 6, 7, 8))]
    m1 = R.TiltGrid(0, "linear")
    res = R.run_registered([m1], pre + reg)
    r = res["tilt_linear"]
    assert r["n"] == 2 and len(r["overlaps"]) == 2
    assert not np.allclose(m1.ll, 0.0)                      # conditioning changed the model
    m2 = R.TiltGrid(0, "linear")
    for _, _, S in pre:                                     # identical conditioning, no scoring
        m2.predict(P)
        m2.update(P, S)
    L, E, M = [], [], []
    for t, (_, _, S) in enumerate(reg, start=1):
        law = m2.predict(P)
        L.append(math.exp(law.logq(S) + math.log(C)))
        E.append((E[-1] if E else 1.0) * L[-1])
        M.append(L[-1] * ((M[-1] if M else 0.0) + 1.0 / (t * (t + 1))))
        m2.update(P, S)
    assert abs(r["E_final"] - E[-1]) < 1e-10
    assert abs(r["E_max"] - max([1.0] + E)) < 1e-10         # E starts at 1
    assert abs(r["M_max"] - max(M)) < 1e-10
    # Exactly one registered draw: E = q(S)/p0(S) = L_1 and M = L_1 * 1/2.
    r3 = R.run_registered([R.TiltGrid(0, "linear")], pre + reg[:1])["tilt_linear"]
    m4 = R.TiltGrid(0, "linear")
    for _, _, S in pre:
        m4.predict(P)
        m4.update(P, S)
    L1 = math.exp(m4.predict(P).logq(reg[0][2]) + math.log(C))
    assert abs(r3["E_final"] - L1) < 1e-12 and abs(r3["E_max"] - L1) < 1e-12
    assert abs(r3["M_max"] - 0.5 * L1) < 1e-12
    # The ensemble reports its own per-component cumulative log-evidence (from the laws it scored).
    ens = R.Ensemble([R.Uniform(), R.TiltGrid(0, "linear")])
    comp = R.run_registered([ens], pre + reg)["ensemble"]["component_log_evidence"]
    assert abs(comp["uniform"]["log_E_final"]) < 1e-12      # uniform increments are exactly 1
    assert comp["tilt_linear"]["log_E_final"] != 0.0


def test_censored_median():
    """Censoring-aware median (design review, required change 3): -1 = +infinity; lower median of
    the full list; "not_reached_by_horizon" when that is infinite."""
    assert R.censored_median([5, 7, -1], 100) == 7
    assert R.censored_median([5, -1, -1], 100) == "not_reached_by_horizon"
    assert R.censored_median([10, 4, 8, 6], 100) == 6       # all crossing: ordinary lower median
    assert R.censored_median([9, 3, 5], 100) == 5


def test_fixed_share_loss_bound_on_uniform_streams():
    """C3 (theorem, conservative form): -log E_T <= 0.685304 + 0.0010005*T for CP-NEST against the
    uniform comparator level, on random uniform streams at P = 42."""
    P = 42
    for s in range(20):
        rng = np.random.default_rng([20260923, s])
        cp = R.CPNest(seed=s, M=32)
        log_e = 0.0
        for _ in range(200):
            S = R.sample_cp(rng, np.zeros(P))
            log_e += cp.predict(P).logq(S) + math.log(math.comb(P, 6))
            cp.update(P, S)
        assert -log_e <= 0.685304 + 0.0010005 * 200, s


def test_tilt_high31_nondegenerate_and_deterministic_at_42():
    """Design review item 6: the high31 feature vanishes at P = 9; at P = 42 it is nondegenerate
    (inclusion not uniform, sums to 6), and predict() is bit-deterministic given seed and history."""
    F = R.features(42)
    assert len(set(F[1].tolist())) > 1                      # phi_2 = 1[i > 31] nonconstant at P = 42
    a, b = R.TiltGrid(1, "high31"), R.TiltGrid(1, "high31")
    rng = np.random.default_rng(11)
    hist = [tuple(sorted(rng.choice(42, 6, replace=False) + 1)) for _ in range(6)]
    for S in hist:
        la, lb = a.predict(42), b.predict(42)
        assert np.array_equal(la.logw, lb.logw) and np.array_equal(la.a, lb.a)
        assert abs(la.inclusion().sum() - 6.0) < 1e-9
        assert np.ptp(la.inclusion()) > 1e-8                # nondegenerate: inclusion not uniform
        a.update(42, S)
        b.update(42, S)
