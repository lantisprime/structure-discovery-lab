from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_registered_predictions as RP
from pcso_signshare import AMPS, C7, POOLS, SIGNS, SignShareFilter


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
            assert abs(np.exp(law.logq(S)) - explicit) <= 1e-12


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
    rows = R.load()
    per = RP.walk([SignShareFilter()], rows, "2026-08-26")
    assert len(per["signshare_seq1"]) == 66


def test_real_conditioning_marginals():
    rows = R.load()
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
    rows = R.load()
    f = SignShareFilter()
    start = time.perf_counter()
    for _, P, S in rows:
        f.predict(P)
        f.update(P, S)
    elapsed = (time.perf_counter() - start) / len(rows)
    print(f"T7 seconds/draw: {elapsed:.9f}")
