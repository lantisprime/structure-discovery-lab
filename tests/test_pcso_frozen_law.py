"""Serialization and reference evaluation checks for frozen PCSO laws."""
import copy
from itertools import combinations
import math
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_sparse_switch as SS
from pcso_frozen_law import decode, encode, freeze, inclusion, logq, score_bounds, top6


@pytest.fixture
def small(monkeypatch):
    monkeypatch.setattr(SS, "POOLS", (8, 9, 10, 11, 12))


def _small_graphs():
    from pcso_sparse_switch import CPSparseSwitch

    P = 8
    law_a = R.Law(np.random.default_rng(1).normal(0, .3, (3, P)), np.array([.5, .3, .2]))
    laws = [law_a,
            R.MixLaw([law_a, R.Uniform().predict(P)], np.array([.7, .3])),
            R.ParityPair().predict(P),
            CPSparseSwitch().predict(P)]
    return [(law, P) for law in laws]


def _check_exhaustive(law, P):
    graph_bytes = encode(freeze(law, P))
    graph = decode(graph_bytes)
    assert encode(decode(graph_bytes)) == graph_bytes
    lo, hi = score_bounds(graph)
    values = []
    for S in combinations(range(1, P + 1), 6):
        frozen_logq = logq(graph, S)
        assert abs(frozen_logq - law.logq(S)) <= 1e-12
        values.append(frozen_logq)
        assert lo - 1e-12 <= frozen_logq + math.log(math.comb(P, 6)) <= hi + 1e-12
    assert abs(math.fsum(math.exp(x) for x in values) - 1) <= 1e-12
    frozen_pi = inclusion(graph)
    assert np.max(np.abs(frozen_pi - law.inclusion())) <= 1e-12
    assert abs(frozen_pi.sum() - 6) <= 1e-9
    assert top6(graph) == law.top6()
    return graph_bytes


def test_small_pools_exhaustive(small):
    for law, P in _small_graphs():
        _check_exhaustive(law, P)


@pytest.fixture(scope="module")
def real_frozen():
    import pcso_registered_predictions as PR

    models = PR.roster()
    PR.walk(models, R.load(), "9999-12-31")
    return models


def test_real_laws_random_subsets_and_bounds(real_frozen):
    pools = (42, 45, 49, 55, 58)
    encoded_sizes = []
    for P in pools:
        rng = np.random.default_rng(P)
        subsets = [tuple(sorted(int(x) for x in rng.choice(P, 6, replace=False) + 1))
                   for _ in range(25)]
        for model in real_frozen:
            law = copy.deepcopy(model).predict(P)
            blob = encode(freeze(law, P))
            encoded_sizes.append(len(blob))
            graph = decode(blob)
            assert encode(decode(encode(graph))) == encode(graph)
            lo, hi = score_bounds(graph)
            for S in subsets:
                actual = logq(graph, S)
                assert abs(actual - law.logq(S)) <= 1e-12
                d_value = actual + math.log(math.comb(P, 6))
                assert lo - 1e-12 <= d_value <= hi + 1e-12
            assert top6(graph) == law.top6()
    total = sum(encoded_sizes)
    print(f"TOTAL_ENCODED_BYTES={total}")
    assert total < 200_000_000
