"""Serialization and reference evaluation checks for frozen PCSO laws."""
import copy
from itertools import combinations
import math
from pathlib import Path
import sys
import time

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_sparse_switch as SS
from pcso_frozen_law import (D_interval, certified_mass, decode, encode, freeze, inclusion,
                             logq, score_bounds, top6, validate)
import pcso_frozen_law as FL


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


def _check_exhaustive(law, P, check_ticket=True):
    graph_bytes = encode(freeze(law, P))
    graph = decode(graph_bytes)
    assert encode(decode(graph_bytes)) == graph_bytes
    mass = certified_mass(graph)
    lo, hi = score_bounds(graph)
    values = []
    subsets = list(combinations(range(1, P + 1), 6))
    raw = []
    for S in subsets:
        frozen_logq = logq(graph, S)
        assert abs(frozen_logq - law.logq(S)) <= 1e-12
        values.append(frozen_logq)
        raw.append(math.exp(frozen_logq))
        d_value = frozen_logq + math.log(math.comb(P, 6))
        if not lo <= d_value <= hi:
            dlo, dhi = D_interval(graph, S)
            assert lo <= dlo <= dhi <= hi
    assert abs(math.fsum(math.exp(x) for x in values) - 1) <= 1e-12
    frozen_pi = inclusion(graph)
    raw = np.asarray(raw)
    brute_pi = np.array([sum(raw[j] for j, S in enumerate(subsets) if i in S) / raw.sum()
                         for i in range(1, P + 1)])
    assert np.max(np.abs(frozen_pi - brute_pi)) <= 1e-12
    assert np.max(np.abs(frozen_pi - law.inclusion())) <= 1e-12
    assert abs(frozen_pi.sum() - 6) <= 1e-9
    if check_ticket:
        assert top6(graph) == FL.ticket_from_inclusion(brute_pi)
    return graph_bytes


def test_small_pools_exhaustive(small):
    for law, P in _small_graphs():
        _check_exhaustive(law, P)


def test_small_law_inclusion_bruteforce_all_pools(small):
    from pcso_sparse_switch import CPSparseSwitch

    for P in SS.POOLS:
        law = R.Law(np.random.default_rng(P).normal(0, .3, (3, P)), np.array([.5, .3, .2]))
        laws = [law, R.MixLaw([law, R.Uniform().predict(P)], np.array([.7, .3])),
                R.ParityPair().predict(P), CPSparseSwitch().predict(P)]
        for candidate in laws:
            _check_exhaustive(candidate, P, check_ticket=False)


def test_certified_mass_small_laws(small):
    widths = []
    for law, P in _small_graphs():
        graph = FL._decode_arrays(__import__("json").loads(encode(freeze(law, P))))
        validate(graph)
        lo, hi = certified_mass(graph)
        widths.append(hi - lo)
        assert 1 - 1e-12 <= lo <= hi <= 1 + 1e-12
    print(f"MAX_SMALL_CERTIFIED_MASS_WIDTH={max(widths):.17g}")


def test_certified_mass_preserves_outward_enclosure(small):
    graph = freeze(R.Law(np.zeros((1, 8)), np.array([1.])), 8)
    graph["a"][0] = 1 + 5e-13
    lo, hi = certified_mass(graph)
    assert lo > 1
    assert 1 - 1e-12 <= lo <= hi <= 1 + 1e-12
    decoded = decode(encode(graph))
    assert decoded["a"][0] == graph["a"][0]


@pytest.fixture(scope="module")
def real_frozen():
    import pcso_registered_predictions as PR

    models = PR.roster()
    PR.walk(models, R.load(), "9999-12-31")
    return models


def _canonical_native_logq(law, S):
    """C4 oracle: remove each parity child's native posterior scale."""
    if isinstance(law, R.ParityLaw):
        return law.logq(S) - FL._lse(law.lp)
    if isinstance(law, R.MixLaw):
        return FL._lse([math.log(float(v)) + _canonical_native_logq(child, S)
                        for v, child in zip(law.v, law.laws) if v > 0])
    return law.logq(S)


def test_real_laws_random_subsets_and_bounds(real_frozen):
    pools = (42, 45, 49, 55, 58)
    encoded_sizes = []
    mass_widths = []
    largest_real = (0, 0.0, "", "", 0)
    max_inclusion_difference = 0.0
    top6_differences = []
    for P in pools:
        rng = np.random.default_rng(P)
        subsets = [tuple(sorted(int(x) for x in rng.choice(P, 6, replace=False) + 1))
                   for _ in range(25)]
        for model in real_frozen:
            law = copy.deepcopy(model).predict(P)
            blob = encode(freeze(law, P))
            encoded_sizes.append(len(blob))
            graph = FL._decode_arrays(__import__("json").loads(blob))
            validate(graph)
            start = time.perf_counter()
            mass_lo, mass_hi = certified_mass(graph)
            elapsed = time.perf_counter() - start
            mass_widths.append(mass_hi - mass_lo)
            assert 1 - 1e-12 <= mass_lo <= mass_hi <= 1 + 1e-12
            if len(blob) > largest_real[0]:
                largest_real = (len(blob), elapsed, graph["type"], model.name, P)
            restored = FL._decode_arrays(__import__("json").loads(encode(graph)))
            validate(restored)
            assert encode(restored) == encode(graph)
            mass_mid = (mass_lo + mass_hi) / 2
            lo, hi = score_bounds(graph)
            for S in subsets:
                actual = logq(graph, S)
                assert abs(actual - _canonical_native_logq(law, S)) <= 1e-12
                d_value = actual - math.log(mass_mid) + math.log(math.comb(P, 6))
                if not lo <= d_value <= hi:
                    dlo, dhi = D_interval(graph, S)
                    assert lo <= dlo <= dhi <= hi
            pi = inclusion(graph)
            difference = float(np.max(np.abs(pi - law.inclusion())))
            max_inclusion_difference = max(max_inclusion_difference, difference)
            frozen_ticket, native_ticket = top6(graph), law.top6()
            if frozen_ticket != native_ticket:
                # Allowed only when both are maximum-inclusion sets under the committed tie rule.
                fv = sorted(pi[t - 1] for t in frozen_ticket)
                nv = sorted(pi[t - 1] for t in native_ticket)
                tied = all(abs(a - b) <= FL.TIE_RTOL * max(a, b) for a, b in zip(fv, nv))
                top6_differences.append((model.name, P, frozen_ticket, native_ticket, tied))
    total = sum(encoded_sizes)
    print(f"TOTAL_ENCODED_BYTES={total}")
    print(f"MAX_REAL_CERTIFIED_MASS_WIDTH={max(mass_widths):.17g}")
    print(f"LARGEST_REAL_CERTIFIED_MASS_SECONDS={largest_real[1]:.9f}")
    print(f"LARGEST_REAL_LAW={largest_real[2]}:{largest_real[3]}:P{largest_real[4]}")
    print(f"MAX_REAL_INCLUSION_DIFFERENCE={max_inclusion_difference:.17g}")
    print(f"REAL_TOP6_DIFFERENCES={top6_differences}")
    assert total < 200_000_000
    assert max_inclusion_difference <= 1e-9
    assert all(tied for *_, tied in top6_differences)


def test_cp_inclusion_large_common_offset():
    # Astra R5-A: log(a) must be added after 6*shift - loge6 cancels.
    s = 1e15
    rows = np.array([[s - 0.375] * 4 + [s] * 4, [s] * 4 + [s - 1] * 4])
    graph = {"type": "cp", "P": 8, "logw": rows,
             "a": np.array([0.5787180591146428, 0.4212819408853572]),
             "loge6": np.array([6 * s + 2, 6 * s + 1])}
    graph = decode(encode(graph))
    pi = inclusion(graph)
    np.testing.assert_allclose(pi[:4], 0.7479230711508856, rtol=0, atol=1e-12)
    np.testing.assert_allclose(pi[4:], 0.7520769288491144, rtol=0, atol=1e-12)
    assert top6(graph) == [1, 2, 5, 6, 7, 8]


def test_ticket_exact_ties_favour_lower_numbers():
    # pair_parity is odd/even symmetric when Po == Pe (E[m] = 3): every inclusion is 6/P.
    assert top6(freeze(R.ParityPair().predict(42), 42)) == [1, 2, 3, 4, 5, 6]
    # identical log-weights above 31 are exact ties.
    row = np.where(np.arange(1, 43) > 31, .3, 0.)[None, :]
    assert top6(freeze(R.Law(row, np.ones(1)), 42)) == [32, 33, 34, 35, 36, 37]


@pytest.mark.parametrize("shift", [9.19e-12, 0.25, -0.25])
@pytest.mark.parametrize("mixed", [False, True])
def test_parity_snapshot_normalization(shift, mixed):
    import mpmath as mp

    P = 9
    parity = R.ParityPair().predict(P)
    parity.lp = parity.lp + shift
    before = parity.lp.copy()
    assert abs(FL._lse(before)) > 1e-12
    law = (R.MixLaw([R.Uniform().predict(P), parity], np.array([.6, .4]))
           if mixed else parity)
    graph = decode(encode(freeze(law, P)))
    np.testing.assert_array_equal(parity.lp, before)
    child = graph["children"][1] if mixed else graph
    assert abs(FL._lse(child["lp"])) <= 1e-12
    assert not np.shares_memory(child["lp"], parity.lp)
    blob = encode(graph)
    assert encode(decode(blob)) == blob
    mass = certified_mass(graph)
    bounds = score_bounds(graph)
    subsets = list(combinations(range(1, P + 1), 6))
    with mp.workdps(50):
        raw = [mp.exp(_high_precision_logq(graph, S)) for S in subsets]
        total = sum(raw)
        assert mp.mpf(mass[0]) <= total <= mp.mpf(mass[1])
        assert 1 - mp.mpf("1e-12") <= mass[0] <= mass[1] <= 1 + mp.mpf("1e-12")
        brute_pi = np.array([float(sum(r for S, r in zip(subsets, raw) if i in S) / total)
                             for i in range(1, P + 1)])
        for S, r in zip(subsets, raw):
            exact = mp.log(r / total) + mp.log(math.comb(P, 6))
            dlo, dhi = D_interval(graph, S)
            assert mp.mpf(dlo) <= exact <= mp.mpf(dhi)
            assert mp.mpf(bounds[0]) <= exact <= mp.mpf(bounds[1])
            assert dhi - dlo <= 1e-12
            assert abs(logq(graph, S) - _canonical_native_logq(law, S)) <= 1e-12
    np.testing.assert_allclose(inclusion(graph), brute_pi, rtol=0, atol=1e-12)
    assert top6(graph) == FL.ticket_from_inclusion(brute_pi)


@pytest.mark.parametrize("P", [42, 58])
@pytest.mark.parametrize("shift", [9.19e-12, 0.25])
def test_parity_snapshot_symmetric_ticket(P, shift):
    law = R.ParityPair().predict(P)
    law.lp = law.lp + shift
    graph = decode(encode(freeze(law, P)))
    pi = inclusion(graph)
    np.testing.assert_allclose(pi, np.full(P, 6 / P), rtol=1e-12, atol=0)
    assert pi.min() >= (1 - FL.TIE_RTOL) * pi.max()
    assert top6(graph) == [1, 2, 3, 4, 5, 6]


def test_parity_snapshot_quality_gates_and_cache():
    law = R.ParityPair().predict(9)
    law.lp[::2] = -math.inf
    graph = decode(encode(freeze(law, 9)))
    assert np.all(np.isneginf(graph["lp"][::2]))
    for value in (np.nan, math.inf, -math.inf):
        bad = copy.deepcopy(graph)
        bad["lp"][:] = value
        with pytest.raises(ValueError):
            validate(bad)
    bad = copy.deepcopy(graph)
    bad["lp"] += 1e-6
    with pytest.raises(ValueError, match="exp\\(lp\\) must sum to 1"):
        validate(bad)
    first = certified_mass(graph)
    graph["lp"] += 5e-13
    validate(graph)
    second = certified_mass(graph)
    assert second[0] > first[1] + 4e-13
    graph["logZ"] -= 4e-12
    validate(graph)
    third = certified_mass(graph)
    assert third[0] > second[1] + 3e-12
    with pytest.raises(ValueError, match="law mass not certified"):
        decode(encode(graph))


def test_sparse_support_rows_are_canonical(small):
    graph = freeze(SS.CPSparseSwitch().predict(8), 8)
    expert_index = next(i for i, e in enumerate(graph["experts"]) if e["k"] == 2)
    expert = graph["experts"][expert_index]
    two = next((i for i, row in enumerate(expert["supports"]) if len(set(map(int, row))) == 2), None)
    assert two is not None
    bad = copy.deepcopy(graph)
    bad["experts"][expert_index]["supports"][two] = [0, 0]
    with pytest.raises(ValueError, match="strictly increasing"):
        validate(bad)
    bad = copy.deepcopy(graph)
    bad["experts"][expert_index]["supports"][1] = bad["experts"][expert_index]["supports"][0]
    with pytest.raises(ValueError, match="strictly increasing|unique"):
        validate(bad)


def test_parity_rejects_wrong_registered_statistic():
    graph = freeze(R.ParityPair().predict(8), 8)
    graph["g"][0] = 2000
    with pytest.raises(ValueError, match="g does not match"):
        decode(encode(graph))


def test_decode_requires_certified_normalization(small):
    underflow = freeze(R.Law(np.full((1, 8), -124.5), np.array([1.])), 8)
    with pytest.raises(ValueError):
        decode(encode(underflow))
    graph = freeze(R.Uniform().predict(8), 8)
    graph["loge6"][0] -= 9e-11
    with pytest.raises(ValueError, match="law mass not certified"):
        decode(encode(graph))


def test_referee_r3_inclusion_ticket_and_cp_extremes():
    law = R.Law(np.array([[0.] * 4 + [1.] * 4, [1.] * 4 + [0.] * 4]), np.array([.5, .5]))
    graph = freeze(law, 8)
    graph["loge6"] += np.array([-9e-11, 9e-11])
    graph = decode(encode(graph))
    subsets = list(combinations(range(1, 9), 6))
    raw = np.array([math.exp(logq(graph, subset)) for subset in subsets])
    brute_pi = np.array([sum(raw[j] for j, subset in enumerate(subsets) if i in subset) / raw.sum()
                         for i in range(1, 9)])
    brute_ticket = R.top6(brute_pi)
    assert brute_ticket == [1, 2, 5, 6, 7, 8]
    assert top6(graph) == brute_ticket
    print(f"R3_A_COUNTEREXAMPLE_TICKET_BRUTE={brute_ticket} INCLUSION={top6(graph)}")

    extreme = freeze(R.Law(np.array([[50.] + [0.] * 57]), np.ones(1)), 58)
    pi = inclusion(extreme)
    assert np.all((0 <= pi) & (pi <= 1))
    assert abs(pi.sum() - 6) <= 1e-9
    assert pi[0] > .999


def test_exact_sparse_mass_gate():
    graph = {"type": "sparse", "P": 58, "logoutside": 9.984117289975799e-13,
             "logC": math.log(math.comb(58, 6)), "experts": []}
    with pytest.raises(ValueError, match="law mass not certified"):
        decode(encode(graph))


def test_subnormal_cp_cached_normalizer_validation():
    graph = freeze(R.Law(np.array([[0.] + [-145.] * 7]), np.ones(1)), 8)
    graph["loge6"][0] = -721.9554775622765
    graph = decode(encode(graph))
    pi = inclusion(graph)
    subsets = list(combinations(range(1, 9), 6))
    lograw = np.array([logq(graph, subset) for subset in subsets])
    raw = np.exp(lograw - lograw.max())
    brute_pi = np.array([sum(raw[j] for j, subset in enumerate(subsets) if i in subset) / raw.sum()
                         for i in range(1, 9)])
    assert np.all(np.isfinite(pi)) and np.all((0 <= pi) & (pi <= 1))
    assert abs(pi.sum() - 6) <= 1e-9
    assert np.max(np.abs(pi - brute_pi)) <= 1e-12
    assert top6(graph) == FL.ticket_from_inclusion(brute_pi)


def test_sparse_inclusion_uses_stored_logz_ratio(small):
    # Start from a frozen native CPSparseSwitch graph, then reduce its k=1 expert to
    # the referee's two active theta rows and ball-8 support; this keeps the native schema.
    graph = freeze(SS.CPSparseSwitch().predict(8), 8)
    expert = next(item for item in graph["experts"] if item["k"] == 1)
    for item in graph["experts"]:
        item["logweights"][:] = -math.inf
    expert["theta"][:] = 0
    expert["theta"][0, 0] = 1
    expert["theta"][1, 0] = -1
    terms = np.column_stack((np.full(len(expert["theta"]), math.log(7)),
                             expert["theta"][:, 0] + math.log(21)))
    outside_terms = np.column_stack((np.full(len(expert["theta"]), math.log(6)),
                                     expert["theta"][:, 0] + math.log(15)))
    logz = np.logaddexp(terms[:, 0], terms[:, 1])
    expert["logz_ratio"][:] = logz - math.log(math.comb(8, 6))
    expert["outside"][:] = np.exp(np.logaddexp(outside_terms[:, 0], outside_terms[:, 1]) - logz)
    expert["correction"][:, 0] = np.exp(expert["theta"][:, 0] + math.log(21) - logz) - expert["outside"]
    expert["logweights"][:] = -math.inf
    outside_mass = 1e-13
    wp, wm = .6155292893150024 * (1 - outside_mass), .38447071068499755 * (1 - outside_mass)
    expert["logweights"][0, 7] = math.log(wp)
    expert["logweights"][1, 7] = math.log(wm)
    graph["logoutside"] = math.log(outside_mass)
    expert["logz_ratio"][0] -= 4e-11
    expert["logz_ratio"][1] += 4e-11 * wp / wm
    graph = decode(encode(graph))
    subsets = list(combinations(range(1, 9), 6))
    raw = np.array([math.exp(logq(graph, subset)) for subset in subsets])
    brute_pi = np.array([sum(raw[j] for j, subset in enumerate(subsets) if i in subset) / raw.sum()
                         for i in range(1, 9)])
    assert np.max(np.abs(inclusion(graph) - brute_pi)) <= 1e-12
    assert top6(graph) == FL.ticket_from_inclusion(brute_pi) == [1, 2, 3, 4, 5, 8]


def test_freeze_rejects_negative_native_weights():
    rows = np.zeros((2, 8))
    with pytest.raises(ValueError, match="weights must be finite and nonnegative"):
        freeze(R.Law(rows, np.array([1 + 1e-13, -1e-13])), 8)
    laws = [R.Law(np.zeros((1, 8)), np.ones(1)), R.Law(np.ones((1, 8)), np.ones(1))]
    with pytest.raises(ValueError, match="weights must be finite and nonnegative"):
        freeze(R.MixLaw(laws, np.array([1.1, -.1])), 8)
    bad_law = R.Law(rows, np.ones(2))
    bad_law.a[0] = np.nan
    with pytest.raises(ValueError, match="weights must be finite and nonnegative"):
        freeze(bad_law, 8)
    bad_mix = R.MixLaw(laws, np.array([.5, .5]))
    bad_mix.v[0] = np.inf
    with pytest.raises(ValueError, match="weights must be finite and nonnegative"):
        freeze(bad_mix, 8)


def test_zero_weight_components_are_omitted():
    law = R.Law(np.array([[0.] * 8, [1.] * 8]), np.array([1., 0.]))
    graph = freeze(law, 8)
    assert graph["logw"].shape == (1, 8)
    assert graph["a"].shape == (1,)
    validate(graph)
    mix = R.MixLaw([R.Law(np.zeros((1, 8)), np.ones(1)),
                    R.Law(np.ones((1, 8)), np.ones(1))], np.array([1., 0.]))
    mixed = freeze(mix, 8)
    assert mixed["v"].shape == (1,)
    assert len(mixed["children"]) == 1
    bad = {"type": "cp", "P": 8, "logw": np.zeros((2, 8)),
           "a": np.array([1., 0.]), "loge6": np.full(2, math.log(math.comb(8, 6)))}
    with pytest.raises(ValueError, match="zero-weight components"):
        validate(bad)
    bad_mix = {"type": "mix", "P": 8, "v": np.array([1., 0.]),
               "children": [freeze(R.Law(np.zeros((1, 8)), np.ones(1)), 8),
                            freeze(R.Law(np.zeros((1, 8)), np.ones(1)), 8)]}
    with pytest.raises(ValueError, match="zero-weight components"):
        validate(bad_mix)


def test_scalar_sparse_array_round_trip(small):
    graph = freeze(SS.CPSparseSwitch().predict(8), 8)
    old = float(graph["logoutside"])
    factor = -math.log1p(-math.exp(old))
    graph["logoutside"] = np.array(-math.inf)
    for expert in graph["experts"]:
        expert["logweights"] += factor
    blob = encode(graph)
    assert encode(decode(blob)) == blob


def test_parity_interval_endpoint_selection_counterexample(small):
    import mpmath as mp

    model = R.ParityPair()
    g, logcnt, logz = model._pool(8)
    theta = np.asarray(R.THETA, dtype=float)
    i0 = int(np.argmin(np.abs(theta)))
    i1 = int(np.argmin(np.abs(theta - .005)))
    weights = np.zeros(len(theta))
    weights[i0], weights[i1] = 1 - 1e-13, 1e-13
    lp = np.full(len(theta), -math.inf)
    lp[weights > 0] = np.log(weights[weights > 0] / weights.sum())
    graph = {"type": "parity", "P": 8, "lp": lp, "theta": theta,
             "g": np.asarray(g), "logcnt": np.asarray(logcnt), "logZ": np.asarray(logz)}
    validate(graph)
    S = (1, 2, 3, 4, 5, 6)
    lo, hi = score_bounds(graph, _validated=True)
    with mp.workdps(50):
        exact = _high_precision_D(graph, S)
        assert mp.mpf(lo) <= exact <= mp.mpf(hi)
        print(f"N4_D={mp.nstr(exact, 18)} N4_LO={lo:.17g} N4_HI={hi:.17g}")


def test_iv_precision_independence(small):
    import mpmath as mp

    graphs = [freeze(R.Law(np.random.default_rng(seed).normal(0, .3, (1, 8)), np.array([1.])), 8)
              for seed in range(20)]
    S = (2, 3, 4, 5, 6, 8)
    defaults = (mp.mp.prec, mp.iv.prec)
    try:
        masses = [certified_mass(g) for g in graphs]
        baseline = [(score_bounds(g), D_interval(g, S), m)
                    for g, m in zip(graphs, masses)]
        mp.mp.prec = 20
        mp.iv.prec = 20
        altered = [(score_bounds(g), D_interval(g, S), m)
                   for g, m in zip(graphs, masses)]
        assert altered == baseline
        with mp.workdps(50):
            for g, (_, (lo, hi), (mlo, mhi)) in zip(graphs, altered):
                exact = _high_precision_D(g, S)
                assert mp.mpf(lo) <= exact <= mp.mpf(hi)
                assert 1 - 1e-12 <= mlo <= mhi <= 1 + 1e-12
        assert (mp.mp.prec, mp.iv.prec) == (20, 20)
    finally:
        mp.mp.prec, mp.iv.prec = defaults


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


def _high_precision_log_mass(graph):
    import mpmath as mp
    assert graph["P"] <= 12, "high-precision mass enumeration is only for small pools"
    with mp.workdps(50):
        subsets = combinations(range(1, graph["P"] + 1), 6)
        logrs = [_high_precision_logq(graph, subset) for subset in subsets]
        peak = max(logrs)
        return peak + mp.log(sum(mp.exp(x - peak) for x in logrs))


def _high_precision_D(graph, S, log_mass=None):
    import mpmath as mp
    assert graph["P"] <= 12, "high-precision mass enumeration is only for small pools"
    with mp.workdps(50):
        if log_mass is None:
            log_mass = _high_precision_log_mass(graph)
        return (_high_precision_logq(graph, S) - log_mass
                + mp.log(math.comb(graph["P"], 6)))


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
        mass = certified_mass(graph, _validated=True)
        bounds = score_bounds(graph, _validated=True)
        log_mass = _high_precision_log_mass(graph)
        for S in combinations(range(1, P + 1), 6):
            exact = _high_precision_D(graph, S, log_mass)
            assert mp.mpf(bounds[0]) <= exact <= mp.mpf(bounds[1])
            dlo, dhi = D_interval(graph, S, _validated=True)
            assert mp.mpf(dlo) <= exact <= mp.mpf(dhi), (type(law).__name__, S, exact, dlo, dhi, mass)
            assert dhi - dlo <= 1e-12
            assert abs(logq(graph, S) + math.log(math.comb(P, 6)) - float(exact)) <= 1e-12
        if P == 8:
            dlo, dhi = D_interval(graph, explicit)
            exact = _high_precision_D(graph, explicit, log_mass)
            assert mp.mpf(dlo) <= exact <= mp.mpf(dhi)


def test_certified_decisions_use_exact_normalization(small):
    import mpmath as mp

    graph = freeze(R.Law(np.random.default_rng(17).normal(0, .4, (2, 8)),
                         np.array([.4, .6])), 8)
    S = (1, 2, 3, 4, 5, 8)
    mass = certified_mass(graph)
    expected = _high_precision_D(graph, S)
    d0 = D_interval(graph, S)
    d1 = D_interval(graph, S)
    b0 = score_bounds(graph)
    b1 = score_bounds(graph)
    assert d1[0] <= expected <= d1[1]
    assert d0[0] <= expected <= d0[1]
    assert b0 == b1
    import inspect
    assert "mass" not in inspect.signature(score_bounds).parameters
    assert "mass" not in inspect.signature(D_interval).parameters
    assert inspect.cleandoc(FL.logq.__doc__) == (
        "Raw formula value log r(S). The committed law is q = r/M (amendment 2, C1);\n"
        "decode's mass gate keeps |log M| <= ~1e-12; certified decisions use D_interval/score_bounds.")


def test_fast_cp_mass_matches_interval_reference():
    rng = np.random.default_rng(89)
    cases = [(8, .01), (42, 1.0), (58, 20.0)]
    for index in range(50):
        P, scale = cases[index % len(cases)]
        graph = freeze(R.Law(rng.normal(0, scale, (1, P)), np.array([1.])), P)
        validate(graph)
        fast = FL._certified_mass_cp_fast(graph)
        reference = FL._certified_mass_cp_reference(graph)
        fast_lo, fast_hi = FL._outward(fast, True), FL._outward(fast, False)
        ref_lo, ref_hi = FL._outward(reference, True), FL._outward(reference, False)
        assert fast_lo <= (ref_lo + ref_hi) / 2 <= fast_hi
        assert (fast_hi - fast_lo) / max(abs(fast_lo), abs(fast_hi)) <= 1e-12


def test_certified_mass_cache_is_bound_to_graph_contents(small):
    graph = freeze(R.Law(np.random.default_rng(23).normal(0, .2, (1, 8)), np.array([1.])), 8)
    first = certified_mass(graph)
    graph["loge6"][0] -= 9e-11
    second = certified_mass(graph)
    assert second != first
    assert second[0] > first[0] + 8e-11
    assert second[1] > first[1] + 8e-11
