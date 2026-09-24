"""Small, fast conformance checks for the registered study runner."""
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
import hashlib
import math
import multiprocessing
from pathlib import Path
import platform
import sys

import numpy as np
import pytest
import scipy

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
    meta = serial["_meta"]
    assert meta["environment"] == {
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "machine": platform.machine(), "platform": platform.platform(),
        "verification_scope": "within the recorded environment",
    }
    paths = ("src/pcso_sparse_study.py", "src/pcso_sparse_switch.py", "src/pcso_model_registry.py")
    assert meta["sha256"] == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    assert meta["seeds"]["comparator_formula"] == "numpy.random.SeedSequence([SEED_BASE, s, role_id])"
    assert meta["seeds"]["comparator_role_ids"] == {"cp_nest": 1, "dirichlet_cp_a100": 2}
    resolutions = meta["owner_resolutions_2026_09_24"]
    assert set(resolutions) == {f"O{i}" for i in range(1, 12)}
    assert "does not cover the conditioned operational model" in resolutions["O1"]
    for text in ("4-stream", "2026-09-24", "before these resolutions", "S1, S2, S4, S5 passed",
                 "S3 failed", "3/4 vs 3/4", "k=2, P=45"):
        assert text in resolutions["O11"]
    assert resolutions["O11"] in meta["interpretations"]
    assert "statistic at t=200 is >= 100" in meta["interpretations"][13]
    assert meta["bound_tolerance_nats"] == 1e-9


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
    vectors = {(0.25,), (0.5,), (0.25, 0.25), (0.5, 0.5),
               (0.25, -0.25), (0.5, -0.5), (0.5, 0.25), (0.5, -0.25)}
    assert set(study.cells_for("S3b")) == {(P, v) for P in (45, 58) for v in vectors}
    summary = study.fraction_summary(records_with_crossings(3), "cp_sparse_switch")
    assert summary["SE"] == math.sqrt(0.3 * 0.7 / 10)


@pytest.mark.parametrize("args", [ ["--streams", "0"], ["--workers", "-1"],
                                  ["--claims", "S6"], ["--claims", "S1,S1"],
                                  ["--claims", ""], ["--run-date", "not-a-date"] ])
def test_invalid_cli_input_rejected_before_loading_data(args, monkeypatch):
    monkeypatch.setattr(study, "conditioning_rows", lambda: pytest.fail("unexpected data read"))
    with pytest.raises(SystemExit) as exc:
        study.main(["--run-date", "2026-09-24", *args])
    assert exc.value.code == 2


def test_comparator_seed_initial_states_are_distinct_and_reproducible():
    for s in range(4):
        nest = R.CPNest(seed=study.comparator_seed(s, "cp_nest"), M=128)
        dirichlet = R.DirichletCP(seed=study.comparator_seed(s, "dirichlet_cp_a100"))
        states = [study.json_bytes(rng.bit_generator.state)
                  for rng in (study.stream_rng(s), nest.rng, dirichlet.rng)]
        assert len(set(states)) == 3
        for name, rng, role in (("cp_nest", nest.rng, 1), ("dirichlet_cp_a100", dirichlet.rng, 2)):
            expected = np.random.default_rng(np.random.SeedSequence([20260923 + 5000, s, role]))
            assert study.json_bytes(rng.bit_generator.state) == study.json_bytes(expected.bit_generator.state)
            repeated = np.random.default_rng(study.comparator_seed(s, name))
            np.testing.assert_array_equal(rng.random(12), repeated.random(12))


def test_all_models_score_and_update_identical_data_without_changing_draw_rng(small, monkeypatch):
    scored, updated, initial_states = {}, {}, {}
    for cls in (R.CPNest, R.DirichletCP):
        init = cls.__init__

        def recording_init(self, *args, original=init, **kwargs):
            original(self, *args, **kwargs)
            initial_states[self.name] = study.json_bytes(self.rng.bit_generator.state)

        monkeypatch.setattr(cls, "__init__", recording_init)
    for cls in (M.CPSparseSwitch, R.CPNest, R.DirichletCP):
        predict, update = cls.predict, cls.update

        def recording_predict(self, P, original=predict):
            law = original(self, P)
            name = self.name

            class RecordingLaw:
                def logq(self, S):
                    scored.setdefault(name, []).append((P, S))
                    return law.logq(S)

                def __getattr__(self, attr):
                    return getattr(law, attr)

            return RecordingLaw()

        def recording_update(self, P, S, original=update):
            updated.setdefault(self.name, []).append((P, S))
            original(self, P, S)

        monkeypatch.setattr(cls, "predict", recording_predict)
        monkeypatch.setattr(cls, "update", recording_update)
    schedule = tuple(("test", P) for P in SMALL_POOLS * 2)
    with_comparators = study.evaluate_stream(study.StreamTask(
        3, schedule, P=9, theta=(0.5, -0.25), comparators=True))
    for name in ("cp_nest", "dirichlet_cp_a100"):
        expected_rng = np.random.default_rng(study.comparator_seed(3, name))
        assert initial_states[name] == study.json_bytes(expected_rng.bit_generator.state)
    expected = scored[M.CPSparseSwitch.name]
    assert set(scored) == set(updated) == {"cp_sparse_switch", "cp_nest", "dirichlet_cp_a100"}
    assert len(expected) == len(schedule)
    assert all(rows == expected for rows in (*scored.values(), *updated.values()))
    alone = study.evaluate_stream(study.StreamTask(3, schedule, P=9, theta=(0.5, -0.25)))
    for key in ("draws_sha256", "support"):
        assert alone[key] == with_comparators[key]
    assert alone["models"][M.CPSparseSwitch.name] == with_comparators["models"][M.CPSparseSwitch.name]


@pytest.fixture
def inline_executor(monkeypatch):
    class InlineExecutor:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def map(self, fn, tasks, **kwargs):
            return map(fn, tasks)

    monkeypatch.setattr(study, "ProcessPoolExecutor", InlineExecutor)


def install_score_models(monkeypatch, increments):
    """Controlled likelihood increments, with the production evidence recursion."""
    instances = []
    for module, attr, name in ((M, "CPSparseSwitch", "cp_sparse_switch"),
                               (R, "CPNest", "cp_nest"),
                               (R, "DirichletCP", "dirichlet_cp_a100")):
        class Model:
            def __init__(self, **kwargs):
                self.t = 0
                self.rows = []
                instances.append(self)

            def predict(self, P):
                increment = increments.get(self.t + 1, 0.0)

                class Law:
                    def logq(self, S):
                        return increment - math.log(math.comb(P, 6))

                return Law()

            def update(self, P, S):
                self.t += 1
                self.rows.append((P, S))

        Model.name = name
        monkeypatch.setattr(module, attr, Model)
    return instances


@pytest.mark.parametrize("claim", ["S3", "S3b", "S4"])
@pytest.mark.parametrize("crossing", [997, 998, 1000, 1001])
def test_power_endpoint_excludes_crossing_at_998_for_p45(
        claim, crossing, monkeypatch, inline_executor):
    install_score_models(monkeypatch, {crossing: math.log(101)})
    monkeypatch.setattr(study, "draw_subset", lambda *args: (1, 2, 3, 4, 5, 6))
    seen_bounds = []
    original = M.crossing_lower_bound

    def record_bound(P, k, theta, n, *, pooled_T):
        seen_bounds.append((P, pooled_T))
        return original(P, k, theta, n, pooled_T=pooled_T)

    monkeypatch.setattr(M, "crossing_lower_bound", record_bound)
    output, _ = study.run_study((("2026-09-23", 45, (1, 2, 3, 4, 5, 6)),),
                               (claim,), 1, 1, "2026-09-24")
    for cell in output[claim]["cells"]:
        endpoint = 997 if cell["P"] == 45 else 1000
        assert cell["pooled_draws"] == endpoint
        assert cell["affected_game_draws"] == 200
        assert all(s["crossings"] == int(crossing <= endpoint) for s in cell["models"].values())
        record, = cell["stream_results"]
        assert record["draws"] == endpoint
        for model in record["models"].values():
            assert model["first_crossing"] == (crossing if crossing <= endpoint else -1)
    if claim == "S3":
        assert seen_bounds == [(45, 997), (58, 1000)] * 2
    if claim == "S3b":
        assert output[claim]["status"] == "reported_only" and "pass" not in output[claim]


def test_simulated_and_real_streams_start_fresh(monkeypatch):
    instances = install_score_models(monkeypatch, {1: math.log(2)})
    rows = (("2026-09-22", 45, (1, 2, 3, 4, 5, 6)),
            ("2026-09-23", 58, (2, 3, 4, 5, 6, 7)))
    schedule = tuple((d, P) for d, P, _ in rows)
    for real_rows in (None, rows):
        result = study.evaluate_stream(study.StreamTask(0, schedule, real_rows=real_rows))
        assert result["models"]["cp_sparse_switch"]["log_E_final"] == pytest.approx(math.log(2))
        assert result["uniform_bound"]["prefixes_checked"] == 2
    assert len(instances) == 2 and all(m.t == 2 for m in instances)
    assert instances[1].rows == [(P, S) for _, P, S in rows]


@pytest.fixture
def captured_tasks(monkeypatch, inline_executor):
    tasks = []

    def evaluate(task):
        tasks.append(task)
        check = study.BoundCheck()
        check.observe(0.0, 1.0, 1)
        return {"s": task.s, "uniform_bound": check.result(), "path_bound": check.result(),
                "detection_delay_E": (1, -1, -1)[task.s % 3],
                "detection_delay_M": (0, 50, -1)[task.s % 3],
                **records_with_crossings(0, n=1)[0]}

    monkeypatch.setattr(study, "evaluate_stream", evaluate)
    return tasks


def test_s2_long_stream_cycles_real_schedule_with_s400(captured_tasks):
    rows = (("2026-09-22", 58, (1, 2, 3, 4, 5, 6)),
            ("2026-09-23", 45, (2, 3, 4, 5, 6, 7)))
    output, _ = study.run_study(rows, ("S2",), 2, 1, "2026-09-24")
    assert len(captured_tasks) == 4
    null0, null1, long, real = captured_tasks
    schedule = tuple((d, P) for d, P, _ in rows)
    assert [null0.s, null1.s] == [0, 1]
    assert null0.schedule == null1.schedule == real.schedule == schedule
    assert long.s == 400 and long.schedule == schedule * 5000
    assert real.real_rows == rows
    assert output["_meta"]["seeds"]["S2_long_s"] == 400


@pytest.mark.parametrize("streams,per_cell", [(None, 400), (2, 2)])
def test_s4_runs_400_streams_per_cell_and_restarts_indices(streams, per_cell, captured_tasks):
    output, _ = study.run_study((("2026-09-23", 45, (1, 2, 3, 4, 5, 6)),),
                               ("S4",), streams, 1, "2026-09-24")
    assert len(captured_tasks) == 4 * per_cell
    for i, cell in enumerate(output["S4"]["cells"]):
        tasks = captured_tasks[i * per_cell:(i + 1) * per_cell]
        assert [t.s for t in tasks] == list(range(per_cell))
        assert all(t.P == cell["P"] and t.theta == tuple(cell["theta"]) for t in tasks)
        assert cell["models"]["cp_sparse_switch"]["streams"] == per_cell


@pytest.mark.parametrize("increments,expected", [
    ({1: math.log(400)}, (0, 0)),
    ({1: math.log(400), 200: math.log(1e-6), 205: math.log(1e6)}, (5, 5)),
    ({1: math.log(150), 700: math.log(2)}, (0, 500)),
    ({1: math.log(0.001), 200: math.log(300)}, (-1, 0)),
    ({1000: math.log(101)}, (800, 800)),
    ({}, (-1, -1)),
])
def test_s5_e_and_m_delays_use_current_statistic_without_reset(increments, expected, monkeypatch):
    install_score_models(monkeypatch, increments)
    monkeypatch.setattr(study, "draw_subset", lambda *args: (1, 2, 3, 4, 5, 6))
    result = study.evaluate_stream(study.StreamTask(
        0, study.balanced_schedule(), P=45, theta=(1.0,), tracking=True))
    assert (result["detection_delay_E"], result["detection_delay_M"]) == expected


def test_s5_schedule_uniform_support_and_activation(monkeypatch):
    install_score_models(monkeypatch, {})
    draws = []

    def sample(rng, P, support, theta):
        draws.append((P, support, theta))
        return (1, 2, 3, 4, 5, 6)

    monkeypatch.setattr(study, "draw_subset", sample)
    s = 17
    expected_support = tuple(int(i) + 1 for i in study.stream_rng(s).choice(45, 1, replace=False))
    result = study.evaluate_stream(study.StreamTask(
        s, study.balanced_schedule(), P=45, theta=(1.0,), tracking=True))
    assert result["support"] == list(expected_support)
    assert len(draws) == 1000
    for t, (P, support, theta) in enumerate(draws, 1):
        active = P == 45 and 200 <= t < 700
        assert support == (expected_support if active else ())
        assert theta == ((1.0,) if active else ())


def test_s5_reports_both_censored_medians_without_delay_criteria(captured_tasks):
    output, _ = study.run_study((("2026-09-23", 45, (1, 2, 3, 4, 5, 6)),),
                               ("S5",), 3, 1, "2026-09-24")
    s5 = output["S5"]
    assert s5["detection_delays"] == {
        "E": {"median_detection_delay_pooled_draws": "not_reached_by_horizon",
              "detected_streams": 1, "censored_streams": 2},
        "M": {"median_detection_delay_pooled_draws": 50,
              "detected_streams": 2, "censored_streams": 1},
    }
    assert s5["criteria"] == {"Lemma_1_at_every_prefix": True} and s5["pass"]
    assert all(t.schedule == study.balanced_schedule() and t.tracking for t in captured_tasks)


@pytest.mark.parametrize("value", ["20260924", "2026-W39-4", "2026-9-24", "2026-02-29",
                                    "2026-09-24T00:00:00", " 2026-09-24", "2026-09-24 "])
def test_cli_run_date_rejects_noncanonical_or_invalid_dates(value, monkeypatch):
    monkeypatch.setattr(study, "conditioning_rows", lambda: pytest.fail("unexpected data read"))
    with pytest.raises(SystemExit) as exc:
        study.main(["--run-date", value])
    assert exc.value.code == 2


def test_cli_run_date_required(monkeypatch):
    monkeypatch.setattr(study, "conditioning_rows", lambda: pytest.fail("unexpected data read"))
    with pytest.raises(SystemExit) as exc:
        study.main([])
    assert exc.value.code == 2


@pytest.mark.parametrize("value", ["2026-09-24", "2024-02-29"])
def test_cli_accepts_canonical_run_date_and_creates_output(value, tmp_path, monkeypatch):
    monkeypatch.setattr(study, "conditioning_rows", lambda: ())
    monkeypatch.setattr(study, "run_study", lambda rows, claims, streams, workers, run_date:
                        ({"run_date": run_date}, {}))
    dst = tmp_path / "study.json"
    study.main(["--run-date", value, "--out", str(dst)])
    assert dst.read_bytes() == study.json_bytes({"run_date": value})


def test_cli_refuses_existing_output_before_loading_data(tmp_path, monkeypatch):
    dst = tmp_path / "existing.json"
    dst.write_bytes(b"existing scientific record\n")
    monkeypatch.setattr(study, "conditioning_rows", lambda: pytest.fail("unexpected data read"))
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        study.main(["--run-date", "2026-09-24", "--out", str(dst)])
    assert dst.read_bytes() == b"existing scientific record\n"


def test_cli_exclusive_creation_refuses_output_created_during_run(tmp_path, monkeypatch):
    dst = tmp_path / "raced.json"
    monkeypatch.setattr(study, "conditioning_rows", lambda: ())

    def run(*args):
        dst.write_bytes(b"concurrent scientific record\n")
        return {"run_date": "2026-09-24"}, {}

    monkeypatch.setattr(study, "run_study", run)
    with pytest.raises(FileExistsError):
        study.main(["--run-date", "2026-09-24", "--out", str(dst)])
    assert dst.read_bytes() == b"concurrent scientific record\n"


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_json_refuses_nonfinite_numbers(value):
    with pytest.raises(ValueError):
        study.json_bytes({"value": value})
