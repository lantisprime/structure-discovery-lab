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
from pcso_frozen_law import D_interval, decode, encode, freeze, inclusion, logq, score_bounds, top6, validate


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
        d_value = frozen_logq + math.log(math.comb(P, 6))
        if not lo <= d_value <= hi:
            dlo, dhi = D_interval(graph, S)
            assert lo <= dlo <= dhi <= hi
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
                if not lo <= d_value <= hi:
                    dlo, dhi = D_interval(graph, S)
                    assert lo <= dlo <= dhi <= hi
            assert top6(graph) == law.top6()
    total = sum(encoded_sizes)
    print(f"TOTAL_ENCODED_BYTES={total}")
    assert total < 200_000_000


def test_snapshot_isolation(small):
    for law, P in _small_graphs():
        frozen = freeze(law, P)
        before = encode(frozen)
        if isinstance(law, R.Law):
            law.logw[0, 0] += 1
            law.a[0] *= .5
        elif isinstance(law, SS.SparseLaw):
            law.experts[0].theta[0, 0] += 1
        else:
            continue
        assert encode(frozen) == before


def test_encoding_dtypes_and_json_constants():
    from pcso_frozen_law import _decode_arrays, _encode_arrays

    vals = np.array([1, 255, 65535], dtype=">u2")
    encoded = _encode_arrays(vals)
    assert encoded["dtype"] == "<u2"
    restored = _decode_arrays(encoded)
    assert restored.dtype == np.dtype("<u2")
    np.testing.assert_array_equal(restored, vals)
    with pytest.raises(TypeError):
        _encode_arrays(np.array([1], dtype=np.int64))
    with pytest.raises(ValueError):
        decode(b'{"type":"cp","P":8,"logw":NaN}')
    with pytest.raises(ValueError):
        decode(b'{"type":"cp","P":8,"logw":-Infinity}')


def test_validator_rejects_malformed_graphs(small):
    valid = freeze(R.Law(np.zeros((3, 8)), np.array([.2, .3, .5])), 8)
    bad = copy.deepcopy(valid)
    bad["a"] = np.array([.5, .5, 1.0])
    with pytest.raises(ValueError, match="a must"):
        validate(bad)
    bad = copy.deepcopy(valid)
    bad["loge6"][0] += 1e-6
    with pytest.raises(ValueError, match="loge6"):
        validate(bad)
    mix = freeze(R.MixLaw([R.Law(np.zeros((1, 8)), np.array([1.])),
                           R.Law(np.zeros((1, 9)), np.array([1.]))], np.array([.5, .5])), 8)
    with pytest.raises(ValueError, match="share"):
        validate(mix)
    for subset in ((1, 1, 2, 3, 4, 5), (0, 1, 2, 3, 4, 5),
                   (1, 2, 3, 4, 5), (1, 2, 3, 4, 5, 6, 7), (1, 2, 3, 4, 5, 6.0)):
        with pytest.raises(ValueError):
            logq(valid, subset)
    sparse = freeze(SS.CPSparseSwitch().predict(8), 8)
    sparse["experts"][0]["supports"][0, 0] = 8
    with pytest.raises(ValueError, match="support index"):
        validate(sparse)
    sparse = freeze(SS.CPSparseSwitch().predict(8), 8)
    sparse["experts"][0]["logweights"] += math.log(2)
    with pytest.raises(ValueError, match="mass"):
        validate(sparse)


def test_zero_mass_and_nonfinite_scores(small):
    row = np.array([[700., -700., 0, 0, 0, 0, 0, 0],
                    [-700., 700., 0, 0, 0, 0, 0, 0]])
    law = R.Law(row, np.array([1., 0.]))
    graph = freeze(law, 8)
    single = freeze(R.Law(row[:1].copy(), np.array([1.])), 8)
    S = (1, 3, 4, 5, 6, 7)
    assert logq(graph, S) == logq(single, S)
    child = {"type": "cp", "P": 8, "logw": np.full((1, 8), np.nan),
             "a": np.array([1.]), "loge6": np.array([0.])}
    mixed = {"type": "mix", "P": 8, "v": np.array([1., 0.]),
             "children": [single, child]}
    assert math.isfinite(logq(mixed, S, _validated=True))
    assert logq(mixed, S, _validated=True) == logq(single, S)
    all_zero = {"type": "cp", "P": 8, "logw": np.zeros((2, 8)),
                "a": np.array([.5, .5]), "loge6": np.array([0., 0.])}
    all_zero["logw"][:] = -math.inf
    all_zero["loge6"][:] = 0
    assert logq(all_zero, S, _validated=True) == -math.inf
    with pytest.raises(ValueError, match="finite endpoints"):
        score_bounds(all_zero, _validated=True)


def _high_precision_D(graph, S):
    import mpmath as mp

    def exact_float(x):
        return mp.mpf(float(x))

    kind = graph["type"]
    if kind == "cp":
        vals = [mp.log(exact_float(a)) + sum(exact_float(row[i - 1]) for i in S)
                - exact_float(e6) for row, a, e6 in zip(graph["logw"], graph["a"], graph["loge6"]) if a > 0]
        peak = max(vals)
        lq = peak + mp.log(sum(mp.exp(x - peak) for x in vals))
    elif kind == "mix":
        vals = [mp.log(exact_float(v)) + _high_precision_logq(child, S)
                for v, child in zip(graph["v"], graph["children"]) if v > 0]
        peak = max(vals)
        lq = peak + mp.log(sum(mp.exp(x - peak) for x in vals))
    else:
        lq = _high_precision_logq(graph, S)
    return lq + mp.log(math.comb(graph["P"], 6))


def _high_precision_logq(graph, S):
    import mpmath as mp

    ef = lambda x: mp.mpf(float(x))
    if graph["type"] == "cp":
        vals = [mp.log(ef(a)) + sum(ef(row[i - 1]) for i in S) - ef(e6)
                for row, a, e6 in zip(graph["logw"], graph["a"], graph["loge6"]) if a > 0]
        peak = max(vals)
        return peak + mp.log(sum(mp.exp(x - peak) for x in vals))
    if graph["type"] == "mix":
        vals = [mp.log(ef(v)) + _high_precision_logq(child, S)
                for v, child in zip(graph["v"], graph["children"]) if v > 0]
        peak = max(vals)
        return peak + mp.log(sum(mp.exp(x - peak) for x in vals))
    if graph["type"] == "parity":
        m = sum(i % 2 == 1 for i in S)
        vals = [ef(lp) + ef(theta) * ef(graph["g"][m]) - ef(z)
                for lp, theta, z in zip(graph["lp"], graph["theta"], graph["logZ"])]
        peak = max(vals)
        return peak + mp.log(sum(mp.exp(x - peak) for x in vals))
    if graph["type"] == "sparse":
        terms = []
        for ex in graph["experts"]:
            for row, weightrow, z in zip(ex["theta"], ex["logweights"], ex["logz_ratio"]):
                for supports, lw in zip(ex["supports"], weightrow):
                    if np.isneginf(lw):
                        continue
                    terms.append(ef(lw) + sum(ef(t) for t, ball in zip(row, supports) if int(ball) + 1 in S) - ef(z))
        terms.append(ef(graph["logoutside"]))
        peak = max(terms)
        return peak + mp.log(sum(mp.exp(x - peak) for x in terms)) - ef(graph["logC"])


def test_certified_enclosures_exhaustive(small):
    import mpmath as mp

    mp.mp.dps = 50
    laws = _small_graphs()
    laws.extend((R.Law(np.random.default_rng(seed).normal(0, .3, (1, 8)), np.array([1.])), 8)
                for seed in range(200))
    explicit = (2, 3, 4, 5, 6, 8)
    for law, P in laws:
        graph = freeze(law, P)
        validate(graph)
        bounds = score_bounds(graph, _validated=True)
        for S in combinations(range(1, P + 1), 6):
            exact = _high_precision_D(graph, S)
            assert mp.mpf(bounds[0]) <= exact <= mp.mpf(bounds[1])
            dlo, dhi = D_interval(graph, S, _validated=True)
            assert mp.mpf(dlo) <= exact <= mp.mpf(dhi)
            assert dhi - dlo <= 1e-12
            assert abs(logq(graph, S) + math.log(math.comb(P, 6)) - float(exact)) <= 1e-12
            float_d = logq(graph, S) + math.log(math.comb(P, 6))
            assert dlo - 1e-12 <= float_d <= dhi + 1e-12
        if P == 8:
            dlo, dhi = D_interval(graph, explicit)
            exact = _high_precision_D(graph, explicit)
            assert mp.mpf(dlo) <= exact <= mp.mpf(dhi)
