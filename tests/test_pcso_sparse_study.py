"""Small, fast conformance checks for the registered study runner."""
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
import math
import multiprocessing
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_sparse_study as study
import pcso_sparse_switch as M

SMALL_POOLS = (8, 9, 10, 11, 12)


@pytest.fixture
def small(monkeypatch):
    monkeypatch.setattr(M, "POOLS", SMALL_POOLS)


def small_worker(s):
    # Spawn does not inherit monkeypatches: install only the test pool dictionary
    # in each process. Production models and simulation RNGs are otherwise intact.
    original = M.POOLS
    M.POOLS = SMALL_POOLS
    try:
        schedule = tuple(("test", P) for P in SMALL_POOLS * 2)
        task = study.StreamTask(s, schedule, P=9, theta=(0.5, -0.25), comparators=True)
        return study.evaluate_stream(task)
    finally:
        M.POOLS = original


def test_stream_seeds_and_results_reproducible_across_worker_counts():
    for s in range(4):
        expected = np.random.default_rng(20260923 + 5000 + s).random(12)
        np.testing.assert_array_equal(study.stream_rng(s).random(12), expected)
    reference = [small_worker(s) for s in range(4)]
    for workers in (1, 4):
        with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            actual = list(pool.map(small_worker, range(4)))
        assert study.json_bytes(actual) == study.json_bytes(reference)
    assert len({r["draws_sha256"] for r in reference}) == 4


def test_complete_json_is_byte_identical_across_worker_counts():
    # A very short real-pool schedule exercises actual runner orchestration and
    # provenance, not only the stream worker. Timing/worker fields must stay out.
    rows = (("2026-09-23", 45, (1, 2, 3, 4, 5, 6)),)
    serial, _ = study.run_study(rows, ("S1",), 2, 1, "2026-09-24")
    parallel, _ = study.run_study(rows, ("S1",), 2, 2, "2026-09-24")
    assert study.json_bytes(serial) == study.json_bytes(parallel)
    assert serial["_meta"]["schedule_length"] == 1
    assert serial["_meta"]["run_kind"] == "stream_count_override"


def test_s2_detects_injected_intermediate_violation_and_uses_correct_clock():
    bounds = study.uniform_loss_bounds(20)
    for T, rhs in enumerate(bounds, 1):
        expected = math.log(2) + sum(M._tau(t) for t in range(1, T))
        assert rhs == pytest.approx(expected, rel=0, abs=2e-15)
    check = study.BoundCheck()
    for T, rhs in enumerate(bounds, 1):
        excess = 2e-9 if T == 7 else -0.01
        check.observe(float(rhs) + excess, float(rhs), T)
    result = check.result()
    assert not result["pass"]
    assert result["violations"] == 1
    assert result["first_violation_T"] == result["worst_T"] == 7
    assert result["max_excess_nats"] == pytest.approx(2e-9, rel=0, abs=1e-15)
    tolerance = study.BoundCheck()
    tolerance.observe(bounds[0] + 0.5e-9, bounds[0], 1)
    assert tolerance.result()["pass"]


def test_balanced_schedule_has_exactly_200_draws_of_every_game():
    schedule = study.balanced_schedule()
    assert len(schedule) == 1000
    assert tuple(P for _, P in schedule[:5]) == (42, 45, 49, 55, 58)
    for P in (42, 45, 49, 55, 58):
        assert sum(Q == P for _, Q in schedule) == 200
    assert sum(P == 45 and 200 <= t < 700 for t, (_, P) in enumerate(schedule, 1)) == 100


@pytest.mark.parametrize("support,theta", [((2,), (1.0,)), ((2, 7), (0.5, -0.25))])
def test_planted_sampler_inclusion_matches_small_pool_enumeration(support, theta):
    P, n = 8, 12000
    subsets = np.asarray(list(combinations(range(1, P + 1), 6)))
    logw = np.zeros(P)
    logw[np.asarray(support) - 1] = theta
    probabilities = np.exp(logw[subsets - 1].sum(axis=1))
    probabilities /= probabilities.sum()
    expected = np.zeros(P)
    for subset, probability in zip(subsets, probabilities):
        expected[subset - 1] += probability
    rng, counts = study.stream_rng(17), np.zeros(P)
    for _ in range(n):
        S = study.draw_subset(rng, P, support, theta)
        assert len(set(S)) == 6 and min(S) >= 1 and max(S) <= P
        counts[np.asarray(S) - 1] += 1
    assert np.all(np.abs(counts / n - expected) <= 5 * np.sqrt(expected * (1 - expected) / n))


def test_sr_recursion_matches_registered_harness_on_identical_sequence(small):
    rng = study.stream_rng(5)
    rows = [("2026-09-24", P, study.draw_subset(rng, P)) for P in SMALL_POOLS * 4]
    model, evidence = M.CPSparseSwitch(), study.Evidence()
    increments = []
    for _, P, S in rows:
        increment = model.predict(P).logq(S) + math.log(math.comb(P, 6))
        increments.append(increment)
        evidence.advance(increment)
        model.update(P, S)
        t = len(increments)
        explicit = math.fsum(math.exp(math.fsum(increments[j:])) / ((j + 1) * (j + 2))
                             for j in range(t))
        assert math.exp(evidence.log_m) == pytest.approx(explicit, rel=2e-14)
    registered = R.run_registered([M.CPSparseSwitch()], rows)[M.CPSparseSwitch.name]
    assert registered["log_E_final"] == round(evidence.log_e, 6)
    assert registered["log_E_max"] == round(evidence.log_e_max, 6)
    assert registered["log_M_max"] == round(evidence.log_m_max, 6)
    assert registered["M_max"] == math.exp(evidence.log_m_max)
    assert registered["n"] == evidence.t


def test_conditioning_schedule_preserves_load_order_and_cutoff(monkeypatch):
    rows = [("2026-09-23", 58, (1, 2, 3, 4, 5, 6)),
            ("2026-09-23", 45, (2, 3, 4, 5, 6, 7)),
            ("2026-09-24", 42, (1, 2, 3, 4, 5, 6))]
    monkeypatch.setattr(R, "load", lambda: rows)
    assert study.conditioning_rows() == tuple(rows[:2])
    monkeypatch.setattr(R, "load", lambda: rows[2:])
    with pytest.raises(ValueError, match="empty"):
        study.conditioning_rows()


def test_s5_exact_path_prior_and_switch_indexing():
    horizon, onset, offset, P = 10, 3, 7, 8
    # Independent product over the actual HMM expert transition probabilities.
    active = [onset <= t < offset for t in range(1, horizon + 1)]
    prior = {False: 0.5, True: 0.1 * (2 / 3) / (P * 6)}
    probability = prior[active[0]]
    expected = [-math.log(probability)]
    for t in range(1, horizon):
        tau = 1 / math.log(t + math.e - 1) - 1 / math.log(t + math.e)
        rho = 1 - math.exp(-tau)
        probability *= (1 - rho) * (active[t - 1] == active[t]) + rho * prior[active[t]]
        expected.append(-math.log(probability))
    np.testing.assert_allclose(study.path_loss_bounds(horizon, P, 1, onset, offset), expected,
                               rtol=0, atol=1e-13)


def test_tracking_checks_all_prefixes_and_bound_failures_are_observable(small, monkeypatch):
    schedule = tuple(("test", SMALL_POOLS[t % 5]) for t in range(1000))
    task = study.StreamTask(0, schedule, P=9, theta=(1.0,), tracking=True)
    result = study.evaluate_stream(task)
    assert result["path_bound"]["pass"]
    assert result["path_bound"]["prefixes_checked"] == 1000
    assert result["uniform_bound"]["pass"]
    original = study.path_loss_bounds

    def injected(*args, **kwargs):
        bounds = original(*args, **kwargs)
        bounds[499] = -1e6
        return bounds

    monkeypatch.setattr(study, "path_loss_bounds", injected)
    result = study.evaluate_stream(task)
    assert result["path_bound"]["violations"] == 1
    assert result["path_bound"]["first_violation_T"] == 500


def records_with_crossings(sparse_hits, nest_hits=0, dirichlet_hits=0, n=10):
    return [{"models": {name: {"crossed_E": i < hits} for name, hits in (
        ("cp_sparse_switch", sparse_hits), ("cp_nest", nest_hits), ("dirichlet_cp_a100", dirichlet_hits))}}
        for i in range(n)]


def test_power_criteria_strict_comparisons_and_bw_conversion():
    tied = study.power_cell("S3", 45, (1.0,), records_with_crossings(8, 8, 7))
    assert tied["criteria"]["fraction_ge_lower_bound_minus_2SE"]
    assert not tied["criteria"]["strictly_above_cp_nest"]
    assert not tied["pass"]
    weak = study.power_cell("S4", 45, (math.log(1.1),), records_with_crossings(0))
    assert weak["bw_power_bound"] == pytest.approx(0.0224167, abs=1e-6)
    assert weak["pass"]
    failure = study.power_cell("S4", 45, (math.log(1.1),), records_with_crossings(10))
    assert not failure["pass"]
    secondary = study.power_cell("S3b", 45, (0.5, -0.25), records_with_crossings(0))
    assert "pass" not in secondary and secondary["status"] == "reported_only"
    assert len(study.cells_for("S3b")) == 16


@pytest.mark.parametrize("args", [ ["--streams", "0"], ["--workers", "-1"],
                                  ["--claims", "S6"], ["--claims", "S1,S1"],
                                  ["--claims", ""], ["--run-date", "not-a-date"] ])
def test_invalid_cli_input_rejected_before_loading_data(args, monkeypatch):
    monkeypatch.setattr(study, "conditioning_rows", lambda: pytest.fail("unexpected data read"))
    with pytest.raises(SystemExit) as exc:
        study.main(args)
    assert exc.value.code == 2
