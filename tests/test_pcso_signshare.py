from pathlib import Path
import math
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_registered_predictions as RP
from pcso_signshare import AMPS, C7, POOLS, SIGNS, SignShareFilter


ROWS_0925 = [r for r in R.load() if r[0] <= "2026-09-25"]


def _draw(rng, P):
    return tuple(sorted(int(x) for x in rng.choice(np.arange(1, P + 1), 6, replace=False)))


def test_prior_normalization_and_50_synthetic_updates():
    f = SignShareFilter()
    assert abs(f.w.sum() - 1) <= 1e-15
    rng = np.random.default_rng(0)
    for i in range(50):
        P = POOLS[i % len(POOLS)]
        f.update(P, _draw(rng, P))
        assert abs(f.w.sum() - 1) <= 1e-15


def test_collapse_matches_explicit_336_state_mixture():
    f = SignShareFilter()
    rng = np.random.default_rng(0)
    for i in range(10):
        P = POOLS[i % len(POOLS)]
        f.update(P, _draw(rng, P))
    for P in POOLS:
        law = f.predict(P)
        for _ in range(3):
            S = _draw(rng, P)
            idx = np.asarray(S) - 1
            emissions = np.empty((3, 16, 7))
            for h in range(3):
                for s in range(16):
                    for a in range(7):
                        c = AMPS[a] * SIGNS[s][POOLS.index(P)]
                        emissions[h, s, a] = np.exp(
                            f.logw_c[P][c][idx].sum() - f.loge6_c[P][c]
                        )
            explicit = float(np.sum(f.w * emissions))
            assert abs(law.logq(S) - math.log(explicit)) <= 1e-12


def test_transition_power_matches_iteration():
    f = SignShareFilter()
    rng = np.random.default_rng(12)
    w = rng.random((3, 16, 7))
    w /= w.sum()
    for j in range(1, 7):
        iterated = w.copy()
        for _ in range(j):
            iterated = f._transition_power(iterated, 1)
        assert np.max(np.abs(f._transition_power(w, j) - iterated)) <= 1e-15


def test_predict_batch_one_matches_predict_and_preserves_state():
    f = SignShareFilter()
    rng = np.random.default_rng(22)
    for i in range(4):
        P = POOLS[i]
        f.update(P, _draw(rng, P))
    before = f.w.copy()
    for P in POOLS:
        a, b = f.predict(P), f.predict_batch(P, 1)
        np.testing.assert_allclose(a.logw, b.logw, rtol=0, atol=1e-15)
        np.testing.assert_allclose(a.a, b.a, rtol=0, atol=1e-15)
    np.testing.assert_array_equal(f.w, before)


def test_walk_has_no_lookahead_and_returns_registered_window():
    rows = ROWS_0925
    per = RP.walk([SignShareFilter()], rows, "2026-08-26")
    assert len(per["signshare_seq1"]) == 66
    changed = list(rows)
    d, P, S = changed[-1]
    alternate = tuple(range(1, 7)) if tuple(range(1, 7)) != S else tuple(range(2, 8))
    assert len(alternate) == 6 and alternate != S and max(alternate) <= P
    changed[-1] = (d, P, alternate)
    original = RP.walk([SignShareFilter()], rows, "2026-08-26")["signshare_seq1"]
    modified = RP.walk([SignShareFilter()], changed, "2026-08-26")["signshare_seq1"]
    assert original[:-1] == modified[:-1]
    assert original[-1]["ticket"] == modified[-1]["ticket"]


def test_real_conditioning_marginals():
    rows = ROWS_0925
    assert len(rows) == 1005
    f = SignShareFilter()
    for _, P, S in rows:
        f.predict(P)
        f.update(P, S)
    m = f.marginals()
    print("T6 hazard:", tuple(round(float(x), 6) for x in m["hazard"]))
    print("T6 sign_all_positive:", round(float(m["sign_all_positive"]), 6))
    np.testing.assert_allclose(m["hazard"], (0.741231, 0.163964, 0.094805), atol=1e-6, rtol=0)
    assert abs(m["sign_all_positive"] - 0.712036) <= 1e-6
    assert abs(f.w.sum() - 1) <= 1e-12


def test_real_data_predict_update_benchmark():
    rows = ROWS_0925
    f = SignShareFilter()
    start = time.perf_counter()
    for _, P, S in rows:
        f.predict(P)
        f.update(P, S)
    elapsed = (time.perf_counter() - start) / len(rows)
    print(f"T7 seconds/draw: {elapsed:.9f}")


def test_invalid_inputs_raise_value_error():
    f = SignShareFilter()
    P, S = POOLS[0], (1, 2, 3, 4, 5, 6)
    for j in (0, 1.0, True):
        try:
            f.predict_batch(P, j)
        except ValueError:
            pass
        else:
            raise AssertionError(f"predict_batch accepted j={j!r}")
    for j in (-1, 0.5):
        try:
            f._transition_power(f.w, j)
        except ValueError:
            pass
        else:
            raise AssertionError(f"_transition_power accepted j={j!r}")
    for bad in ((1, 2, 3, 4, 5), (1, 2, 3, 4, 5, 5),
                (0, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, P + 1),
                (1, 2, 3, 4, 5, 6.0), (1, 2, 3, 4, 5, True)):
        try:
            f.update(P, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"update accepted S={bad!r}")
    try:
        f.predict(43)
    except ValueError:
        pass
    else:
        raise AssertionError("predict accepted an unregistered pool")


def test_missing_emission_and_batch_horizons():
    f = SignShareFilter()
    w = f.w.copy()
    missing = SignShareFilter()
    missing.update(POOLS[0], None)
    np.testing.assert_array_equal(missing.w, f._transition_power(w, 1))
    advanced = SignShareFilter()
    advanced.advance(1)
    np.testing.assert_array_equal(missing.w, advanced.w)
    P = POOLS[0]
    for j in range(1, 7):
        batch = f.predict_batch(P, j)
        shifted = SignShareFilter()
        shifted.w = f.w.copy()
        shifted.advance(j - 1)
        expected = shifted.predict(P)
        np.testing.assert_allclose(batch.logw, expected.logw, rtol=0, atol=1e-15)
        np.testing.assert_allclose(batch.a, expected.a, rtol=0, atol=1e-15)


def test_delayed_observation_replay():
    rng = np.random.default_rng(5)
    events = [(POOLS[i % len(POOLS)], _draw(rng, POOLS[i % len(POOLS)])) for i in range(20)]
    a, b = SignShareFilter(), SignShareFilter()
    for P, S in events:
        a.update(P, S)
    for P, S in events[:10]:
        b.update(P, S)
    ckpt = b.checkpoint()
    b.update(events[10][0], None)
    for P, S in events[11:]:
        b.update(P, S)
    b.replay(ckpt, events[10:])
    np.testing.assert_array_equal(b.w, a.w)
    wrong = SignShareFilter()
    for P, S in events:
        wrong.update(P, S)
    wrong.update(*events[10])
    diff = float(np.max(np.abs(wrong.w - a.w)))
    print(f"T10 wrong-time max abs diff: {diff:.17g}")
    assert diff > 1e-12


def test_transition_power_matches_independent_dense_matrix():
    T = np.zeros((336, 336))
    pi = np.asarray((0.10, 0.09, 0.09, 0.27, 0.27, 0.09, 0.09))
    hazards = (0.0, 1 / 256, 1 / 1024)
    for h in range(3):
        for s in range(16):
            for a in range(7):
                source = np.ravel_multi_index((h, s, a), (3, 16, 7))
                for ap in range(7):
                    target = np.ravel_multi_index((h, s, ap), (3, 16, 7))
                    # Column-vector convention: T[ new state, old state ].
                    T[target, source] = ((1 - hazards[h]) * (a == ap)
                                         + hazards[h] * pi[ap])
    f = SignShareFilter()
    w = f.w.copy()
    for j in (1, 7, 100, 6030):
        diff = float(np.max(np.abs(np.linalg.matrix_power(T, j) @ w.ravel()
                                   - f._transition_power(w, j).ravel())))
        if j == 6030:
            print(f"T11 j=6030 max abs diff: {diff:.17g}")
        assert diff <= 1e-13


def test_long_horizon_normalization():
    rng = np.random.default_rng(7)
    f = SignShareFilter()
    for i in range(6030):
        P = POOLS[i % len(POOLS)]
        f.update(P, None if (i + 1) % 50 == 0 else _draw(rng, P))
    assert abs(float(f.w.sum()) - 1.0) <= 1e-12
    assert np.all(f.w >= 0)
