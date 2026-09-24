"""Exact conformance and finite-sample bounds for the sparse switching model."""
import hashlib
import itertools
import math
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_sparse_switch as M


@pytest.fixture
def small(monkeypatch):
    # Keep all five game-prior masses, replacing only the pool sizes.
    monkeypatch.setattr(M, "POOLS", (8, 9, 10, 11, 12))
    return M.CPSparseSwitch()


def subsets(P):
    return list(itertools.combinations(range(1, P + 1), 6))


def tau(t):
    return 1 / math.log(t + math.e - 1) - 1 / math.log(t + math.e)


def switching_cost(T):
    return sum(tau(t) for t in range(1, T))


def condition(model):
    for P, S in [(8, (1, 2, 3, 4, 5, 6)), (9, (2, 3, 4, 5, 6, 7)),
                 (8, (1, 2, 3, 4, 5, 7)), (10, (1, 3, 5, 7, 9, 10))]:
        model.update(P, S)


@pytest.mark.parametrize("P", [8, 9, 10])
@pytest.mark.parametrize("updated", [False, True])
def test_exact_normalization(small, P, updated):
    if updated:
        condition(small)
    law = small.predict(P)
    assert math.fsum(math.exp(law.logq(S)) for S in subsets(P)) == pytest.approx(1, rel=0, abs=1e-12)


@pytest.mark.parametrize("P", [8, 9, 10])
def test_inclusion_matches_enumeration(small, P):
    condition(small)
    law = small.predict(P)
    exact = np.zeros(P)
    for S in subsets(P):
        exact[np.array(S) - 1] += math.exp(law.logq(S))
    np.testing.assert_allclose(law.inclusion(), exact, rtol=0, atol=1e-12)
    assert law.inclusion().sum() == pytest.approx(6, rel=0, abs=1e-12)
    assert law.top6() == R.top6(exact)


def test_predict_is_a_snapshot_and_uses_only_past(small):
    condition(small)
    law = small.predict(8)
    draws = subsets(8)
    before = np.array([law.logq(S) for S in draws])
    pi, selected = law.inclusion(), law.top6()
    repeated = small.predict(8)
    np.testing.assert_array_equal(before, [repeated.logq(S) for S in draws])
    small.update(8, draws[-1])
    small.update(9, draws[0])
    np.testing.assert_array_equal(before, [law.logq(S) for S in draws])
    np.testing.assert_array_equal(pi, law.inclusion())
    assert selected == law.top6()
    assert not np.allclose(before, [small.predict(8).logq(S) for S in draws])


def dense_reference():
    """Independent, exhaustive expert partitions; dense arrays exist only in tests."""
    groups, priors, offset = {}, [0.5], 1
    grid = (-1, -0.5, -0.25, 0.25, 0.5, 1)
    for P in M.POOLS:
        weights, prior = [], []
        for k, pk in [(1, 2 / 3), (2, 1 / 3)]:
            for A in itertools.combinations(range(P), k):
                for theta in itertools.product(grid, repeat=k):
                    row = np.zeros(P)
                    row[list(A)] = theta
                    weights.append(row)
                    prior.append(0.1 * pk / (math.comb(P, k) * 6**k))
        logw = np.array(weights)
        draws = np.array(subsets(P)) - 1
        unnormalized = np.exp(logw[:, draws].sum(axis=2))
        probs = unnormalized / unnormalized.sum(axis=1, keepdims=True)
        groups[P] = (slice(offset, offset + len(prior)), draws, probs)
        priors.extend(prior)
        offset += len(prior)
    return groups, np.array(priors)


def test_prior_and_pooled_updates_match_dense_reference(small):
    groups, prior = dense_reference()
    v = prior.copy()
    # Return to a game after many inactive updates to exercise deferred sharing.
    schedule = [8, 9, 10, 11, 12] + [8] * 15 + [12, 9, 10, 11, 8]
    for t, P in enumerate(schedule, 1):
        sl, draws, probs = groups[P]
        law = small.predict(P)
        q = v[sl] @ probs + (v.sum() - v[sl].sum()) / math.comb(P, 6)
        actual = np.array([math.exp(law.logq(S + 1)) for S in draws])
        np.testing.assert_allclose(actual, q, rtol=2e-13, atol=1e-15)
        pi = np.zeros(P)
        for draw, probability in zip(draws, q):
            pi[draw] += probability
        np.testing.assert_allclose(law.inclusion(), pi, rtol=0, atol=2e-13)
        idx = (t * 11) % len(draws)
        likelihood = np.full(len(v), 1 / math.comb(P, 6))
        likelihood[sl] = probs[:, idx]
        v *= likelihood
        v /= v.sum()
        rho = -math.expm1(-tau(t))
        v = (1 - rho) * v + rho * prior
        small.update(P, draws[idx] + 1)
        assert math.exp(small.log_uniform) == pytest.approx(v[0], rel=0, abs=2e-14)
    small.reset()
    assert small.t == 0
    assert math.exp(small.log_uniform) == pytest.approx(0.5)
    assert small.predict(9).inclusion() == pytest.approx(np.full(9, 6 / 9))


def test_long_inactive_and_unseen_games_match_dense_reference(small):
    groups, prior = dense_reference()
    v = prior.copy()
    log_e = cost = 0.0
    # Absolute log error <= 1e-10 means relative weight/probability error
    # approximately <= 1e-10. Allow float64 accumulation over 10,003 updates,
    # including cancellation in the independent reference's tau differences.
    # Inclusions use the same relative tolerance with no absolute error floor.
    tol = 1e-10

    def advance(P, idx=0):
        nonlocal v, log_e, cost
        sl, draws, probs = groups[P]
        S = draws[idx] + 1
        log_e += small.predict(P).logq(S) + math.log(math.comb(P, 6))
        # cost includes only switches preceding the current prediction.
        assert log_e >= -math.log(2) - cost - tol
        likelihood = np.full(len(v), 1 / math.comb(P, 6))
        likelihood[sl] = probs[:, idx]
        v *= likelihood
        v /= v.sum()
        switch = tau(small.t + 1)
        rho = -math.expm1(-switch)
        v = (1 - rho) * v + rho * prior
        small.update(P, S)
        cost += switch

    def assert_matches(P):
        np.testing.assert_allclose(small.log_uniform, np.log(v[0]), rtol=0, atol=tol)
        for Q, (sl, _, _) in groups.items():
            game = small._games[Q]
            # Dense order is support, then theta; sparse matrices are transposed.
            weights = np.concatenate([a.T.ravel() for a in game.log_weights()])
            np.testing.assert_allclose(weights, np.log(v[sl]), rtol=0, atol=tol)
            np.testing.assert_allclose(game.mass, np.log(v[sl].sum()), rtol=0, atol=tol)
        sl, draws, probs = groups[P]
        q = v[sl] @ probs + (v.sum() - v[sl].sum()) / math.comb(P, 6)
        law = small.predict(P)
        indices = [0, len(draws) // 2, len(draws) - 1]
        np.testing.assert_allclose([law.logq(draws[i] + 1) for i in indices],
                                   np.log(q[indices]), rtol=0, atol=tol)
        pi = np.zeros(P)
        for draw, probability in zip(draws, q):
            pi[draw] += probability
        np.testing.assert_allclose(law.inclusion(), pi, rtol=tol, atol=0)

    advance(8)
    for _ in range(10_000):
        advance(9)  # Repeated (1, ..., 6) is informative, unlike null draws.
    # A: return to a trained game; B: first observation of an unseen game.
    for P in (8, 10):
        assert_matches(P)
        advance(P, -1)
        assert_matches(P)
    assert small.t == 10_003


@pytest.mark.parametrize("adversarial", [False, True])
@pytest.mark.parametrize("seed", [7, 19, 31])
def test_pathwise_uniform_comparator_bound(small, adversarial, seed):
    rng = np.random.default_rng(seed)
    log_e = cost = 0.0
    for t in range(1, 301):
        P = M.POOLS[int(rng.integers(5))]
        S = tuple(range(1, 7)) if adversarial else tuple(rng.choice(P, 6, replace=False) + 1)
        log_e += small.predict(P).logq(S) + math.log(math.comb(P, 6))
        assert log_e >= -math.log(2) - cost - 1e-12
        small.update(P, S)
        cost += tau(t)


def test_null_collapse_on_2000_real_pool_draws():
    model = M.CPSparseSwitch()
    rng = np.random.default_rng(20260923)
    log_e = cost = 0.0
    for t in range(1, 2001):
        P = M.POOLS[(t - 1) % 5]
        S = tuple(rng.choice(P, 6, replace=False) + 1)
        log_e += model.predict(P).logq(S) + math.log(math.comb(P, 6))
        assert -log_e <= math.log(2) + cost + 1e-11
        model.update(P, S)
        cost += tau(t)
    assert all(model.log_uniform > a.max()
               for game in model._games.values() for a in game.log_weights())


def test_crossing_lower_bound_lead_value_and_cutoff():
    P, n, theta = 45, 200, 1.0
    p = 6 / P
    z = 1 - p + p * math.exp(theta)
    cost = -math.log(0.1 * (2 / 3) / (P * 6))
    cutoff = math.ceil((math.log(100) + cost + switching_cost(1000) + n * math.log(z)) / theta)
    assert cutoff == 56
    assert switching_cost(1000) == pytest.approx(0.85527, rel=0, abs=5e-6)
    tilted = p * math.exp(theta) / z
    exact = math.fsum(math.comb(n, h) * tilted**h * (1 - tilted)**(n - h)
                      for h in range(cutoff, n + 1))
    assert M.crossing_lower_bound(P, 1, theta, n) == pytest.approx(exact, rel=0, abs=1e-12)
    assert exact == pytest.approx(0.7024, rel=0, abs=5e-5)


@pytest.mark.parametrize("k,theta", [(1, -1.0), (2, 1.0), (2, -0.5)])
def test_crossing_lower_bound_matches_enumerated_hit_sequences(k, theta):
    P, n, T = 9, 3, 7
    hits = np.array([len(set(S) & set(range(1, k + 1))) for S in subsets(P)])
    raw = np.exp(theta * hits)
    probabilities = raw / raw.sum()
    z = raw.mean()
    prior = 0.1 * {1: 2 / 3, 2: 1 / 3}[k] / (math.comb(P, k) * 6**k)
    threshold = prior * math.exp(-switching_cost(T))
    exact = 0.0
    pmf = [probabilities[hits == h].sum() for h in range(k + 1)]
    for hs in itertools.product(range(k + 1), repeat=n):
        if theta * sum(hs) - n * math.log(z) >= math.log(threshold) - math.log(prior) + switching_cost(T):
            exact += math.prod(pmf[h] for h in hs)
    assert M.crossing_lower_bound(P, k, theta, n, threshold=threshold, pooled_T=T) == pytest.approx(exact, rel=0, abs=1e-12)


@pytest.mark.parametrize("k,theta", [(3, 1.0), (1, 0.1)])
def test_crossing_bound_requires_an_expert_in_the_dictionary(k, theta):
    with pytest.raises(ValueError, match="approved grid"):
        M.crossing_lower_bound(45, k, theta, 200)


def test_bw_second_moment_lead_value():
    assert M.bw_second_moment(45, 1, math.log(1.1), 200) - 1 == pytest.approx(0.0006167, rel=0, abs=5e-8)


@pytest.mark.parametrize("k", [1, 2])
def test_bw_second_moment_matches_enumeration(k):
    P, delta, n = 8, math.log(1.3), 2
    draws = subsets(P)
    ratios = []
    for A in itertools.combinations(range(1, P + 1), k):
        raw = np.array([math.exp(delta * len(set(A) & set(S))) for S in draws])
        ratios.append(raw / raw.mean())
    ratios = np.array(ratios)
    evidence = ratios.T @ ratios / len(ratios)
    exact = np.mean(evidence**2)
    assert M.bw_second_moment(P, k, delta, n) == pytest.approx(exact, rel=0, abs=1e-12)
    assert M.bw_second_moment(P, k, 0.0, 200) == pytest.approx(1, rel=0, abs=1e-12)
    assert M.bw_second_moment(P, k, delta, 0) == pytest.approx(1, rel=0, abs=1e-12)


def test_harness_run_compatibility(small):
    rows = [("2026-09-24", 8, S) for S in subsets(8)[:8]]
    result = R.run([small], rows, warmup=0, track_sup=True)["cp_sparse_switch"]
    assert len(result["wf"]) == len(rows)
    assert math.isfinite(result["log_e_full"])
    assert small.theory and small.dim == 2


def test_registered_harness_is_untouched():
    # Content pin of the registered harness as of the 2026-09-24 conditioning-pin update; a
    # deliberate harness change must update this hash together with the commitment ledger.
    digest = hashlib.sha256((ROOT / "src" / "pcso_model_registry.py").read_bytes()).hexdigest()
    assert digest == "71949e97e5791fe9783f6d24e52a1bc863f4ad22bb2186cc59720791c5aff7a1"
