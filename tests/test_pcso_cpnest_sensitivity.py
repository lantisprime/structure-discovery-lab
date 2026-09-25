"""Sensitivity runner contract checks; synthetic tables never execute the study."""
from dataclasses import asdict
import json
import math
from pathlib import Path
import shlex
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pcso_cpnest_sensitivity as run

sim, reg = run.sim, run.reg
requires_mlx = pytest.mark.skipif(sim.mx is None, reason="MLX unavailable; requires Apple GPU")
SCHEDULE = [(f"sim-{i:04d}", [42, 45, 49, 55, 58][i % 5]) for i in range(40)]


@pytest.mark.parametrize("arm,theta", [("null", 0.0), ("power", .025), ("power", .05), ("power", .1)])
def test_per_stream_seeding(arm, theta):
    first = run.generate_draws(SCHEDULE[:4], arm, theta, 0, 10)
    second = run.generate_draws(SCHEDULE[:4], arm, theta, 7, 12)
    np.testing.assert_array_equal(first[7:10], second[:3])
    a, index = run.arm_index(arm, theta)
    rng = np.random.default_rng(np.random.SeedSequence([20260923, a, index, 7]))
    expected = [S for _, _, S in reg.synthetic(rng, SCHEDULE[:4], theta)]
    np.testing.assert_array_equal(first[7], expected)
    z1 = run.generate_normals(4, 32, 0, 10)
    z2 = run.generate_normals(4, 32, 7, 12)
    np.testing.assert_array_equal(z1[7:10], z2[:3])
    expected_z = np.random.default_rng(np.random.SeedSequence([20260923, 1, 32, 7])).standard_normal((4, 16, 6))
    np.testing.assert_array_equal(z2[0], expected_z.astype(np.float32))


@pytest.mark.parametrize("backend", ["cpu", pytest.param("mlx", marks=requires_mlx)])
def test_shard_and_chunk_invariance(backend):
    cell = run.Cell(.2, .01, "uniform", 32)
    schedule = SCHEDULE[:8]

    def evaluate(lo, hi, chunk):
        return run.evaluate(cell, run.generate_draws(schedule, "null", 0, lo, hi), schedule,
                            run.generate_normals(len(schedule), 32, lo, hi), backend, chunk)

    whole = evaluate(0, 6, 2)
    other_chunk = evaluate(0, 6, 3)
    parts = [evaluate(0, 2, 3), evaluate(2, 6, 3)]
    for k in whole:
        np.testing.assert_array_equal(whole[k], other_chunk[k], err_msg=k)
        np.testing.assert_array_equal(whole[k], np.concatenate([p[k] for p in parts]), err_msg=k)


@requires_mlx
@pytest.mark.parametrize("with_normals", [True, False])
def test_defaults_bitwise_unchanged(with_normals):
    draws = run.generate_draws(SCHEDULE[:8], "null", 0, 0, 3)
    normals = run.generate_normals(8, 128, 0, 3) if with_normals else None
    kwargs = dict(M=128, zf_seq=normals, seed=2, chunk=2, device="gpu")
    default = sim.mlx_log_evidence("cp_nest", draws, SCHEDULE[:8], **kwargs)
    explicit = sim.mlx_log_evidence("cp_nest", draws, SCHEDULE[:8], **kwargs,
                                    tau=reg.CPNest.TAU, rho=reg.CPNest.RHO,
                                    v0=2.0 ** -np.arange(7))
    for key in default:
        assert default[key].dtype == explicit[key].dtype
        assert default[key].tobytes() == explicit[key].tobytes()


@requires_mlx
@pytest.mark.parametrize("M,expected", [
    (32, "d31f6e0f6206f539fc2f305a409a8d2f71ecca6bef8afecd1740fa786a765a41"),
    (128, "06fb16c01f9b97c6f0068b1b8e1d748af7f9d1435654532468350891f80e8f6c"),
])
def test_defaults_match_archived_m5_artifacts(M, expected):
    # SHA256 of canonical JSON for devices.gpu.values in the archived
    # results/exploratory/pcso_mlx_matched_cp_nest_m{32,128}.json (MLX 0.32.2).
    schedule = [row for row in run.pinned_schedule()[0] if row[0] <= "2026-09-20"]
    draws = sim.cp_streams(schedule, 16, np.random.default_rng(20260925))
    assert run.digest(draws.tobytes()) == "561d31323e5d8ef0f3fd4a917786b75bf87854080c97e528ebeaecb8ee021a7d"
    normals = np.random.default_rng(20260926).standard_normal((16, 994, M // 2, 6)).astype(np.float32)
    result = sim.mlx_log_evidence("cp_nest", draws, schedule, M=M, zf_seq=normals, chunk=16, device="gpu")
    values = {k: result[k].tolist() for k in ("sup", "final_log_e", "log_sr_max", "crossing", "v0_final")}
    assert run.digest(run.json_bytes(values)) == expected


@requires_mlx
def test_nondefault_cpu_mlx_agreement():
    cell = run.Cell(.2, .01, "uniform", 32)
    draws = run.generate_draws(SCHEDULE, "power", .05, 0, 3)
    normals = run.generate_normals(40, 32, 0, 3)
    cpu = run.evaluate(cell, draws, SCHEDULE, normals, "cpu", 2)
    gpu = run.evaluate(cell, draws, SCHEDULE, normals, "mlx", 3)
    for key in ("le", "sup", "final_log_e", "v0_final", "log_sr_max", "n2_excess"):
        np.testing.assert_allclose(cpu[key], gpu[key], rtol=0, atol=1e-4)
    assert np.max(np.abs(np.cumsum(cpu["le"], axis=1) - np.cumsum(gpu["le"], axis=1, dtype=float))) <= 1e-4
    np.testing.assert_array_equal(cpu["crossing"], gpu["crossing"])


def test_cpu_registered_defaults():
    draws = run.generate_draws(SCHEDULE[:5], "null", 0, 0, 2)
    normals = run.generate_normals(5, 128, 0, 2)
    actual = run.evaluate(run.REGISTERED, draws, SCHEDULE[:5], normals, "cpu")
    expected = sim.cpu_log_evidence("cp_nest", draws, SCHEDULE[:5], M=128, zf_seq=normals, summary=True)
    for k in expected:
        np.testing.assert_array_equal(actual[k], expected[k])


@pytest.mark.parametrize("rho,v00", [(0, 1 / 7), (.01, 1 / 7), (.001, 64 / 127)])
def test_n2_hand_values(rho, v00):
    intercept = math.log(1 / v00)
    slope = math.log(1 / (1 - 6 * rho / 7))
    bound = intercept + np.arange(3) * slope
    cumulative = np.array([-bound + [.2, .1, .3], -bound + [0, -.004, .01]])
    np.testing.assert_allclose(run.n2_excess(cumulative, rho, v00), [-.1, .004], atol=1e-14)
    if rho == 0:
        assert slope == 0 and intercept == math.log(7)
    # A draw-1 violation cannot be hidden by an extra mixing step.
    assert run.n2_excess(np.array([[-intercept - .002]]), rho, v00)[0] == pytest.approx(.002)


def test_n2_cpu_streams():
    cell = run.Cell(.2, .01, "uniform", 32)
    result = run.evaluate(cell, run.generate_draws(SCHEDULE, "null", 0, 0, 3), SCHEDULE,
                          run.generate_normals(40, 32, 0, 3))
    assert np.all(result["n2_excess"] < 0)


def row(cell, sp2=100, sp1=.8, ep2=100, ep1=.8, gate=True):
    return {"cell": asdict(cell), "gate": gate, "selection": {"P2": sp2, "P1": sp1},
            "evaluation": {"P2": ep2, "P1": ep1}}


@pytest.mark.parametrize("rp2,rp1,label", [(125, .75, "ROBUST"), (126, .8, "SENSITIVE"),
                                           (100, .749, "SENSITIVE"), (run.NOT_REACHED, .8, "SENSITIVE")])
def test_verdict_branches(rp2, rp1, label):
    best = run.Cell(.01, 0)
    rows = [row(run.REGISTERED, sp2=200, ep2=rp2, ep1=rp1), row(best)]
    decision = run.verdict(rows)
    assert decision["B"] == asdict(best)
    assert decision["verdict"] == label


def test_verdict_uninformative_and_infinity_order():
    best = run.Cell(.01, 0)
    rows = [row(run.REGISTERED, sp2=run.NOT_REACHED), row(best, ep2=run.NOT_REACHED)]
    assert run.verdict(rows)["verdict"] == "UNINFORMATIVE"
    assert run.verdict(rows)["B"] == asdict(best)
    rows[1]["selection"]["P2"] = run.NOT_REACHED
    assert run.verdict(rows)["B"] == asdict(run.REGISTERED)
    assert math.inf <= 1.25 * math.inf


@pytest.mark.parametrize("winner,loser", [
    (run.REGISTERED, run.Cell(.01, 0)),
    (run.Cell(.01, .01), run.Cell(.025, 0)),
    (run.Cell(.01, 0), run.Cell(.01, .001)),
    (run.Cell(v0="uniform"), run.Cell(M=32)),
    (run.REGISTERED, run.Cell(v0="uniform")),
])
def test_tie_order(winner, loser):
    rows = [row(loser), row(winner)]
    if run.REGISTERED not in (winner, loser):
        rows.append(row(run.REGISTERED, sp2=300))
    assert run.verdict(rows)["B"] == asdict(winner)
    # The last tie axis is tested directly: other axes include registration priority.
    geom, uniform = row(run.Cell(.01, 0)), row(run.Cell(.01, 0, "uniform"))
    assert run.selection_key(geom) < run.selection_key(uniform)


def test_p1_precedes_registration_and_registered_can_be_B():
    other = run.Cell(.01, 0)
    assert run.verdict([row(run.REGISTERED), row(other, sp1=.9)])["B"] == asdict(other)
    decision = run.verdict([row(run.REGISTERED), row(other)])
    assert decision["B"] == asdict(run.REGISTERED) and decision["verdict"] == "ROBUST"
    assert run.verdict([row(run.REGISTERED), row(other, gate=False)])["verdict"] == "DEFECT"
    rows = [row(run.REGISTERED, sp2=300), row(run.Cell(M=512)), row(run.Cell(M=32))]
    assert run.verdict(rows)["B"] == asdict(run.Cell(M=32))
    assert run.verdict(list(reversed(rows)))["B"] == asdict(run.Cell(M=32))


def test_n1_bonferroni_and_gate(monkeypatch):
    calls = []
    original = reg.clopper_pearson_lower

    def lower(k, n, alpha=.05):
        calls.append(alpha)
        return original(k, n, alpha)

    monkeypatch.setattr(reg, "clopper_pearson_lower", lower)
    data = {"sup": np.zeros(100), "n2_excess": np.full(100, -.2),
            "final_log_e": np.full(100, -.5), "v0_final": np.full(100, .5),
            "log_sr_max": np.zeros(100)}
    assert run.null_measures(data)["gate"]
    assert calls == [.05 / 18]
    data["n2_excess"][0] = .001
    assert run.null_measures(data)["gate"]
    data["n2_excess"][0] = .00101
    assert not run.null_measures(data)["gate"]
    data["n2_excess"][:] = 0
    data["sup"][:] = math.log(100)
    assert not run.null_measures(data)["gate"]


def test_p_measures_and_paired_bootstrap():
    a = np.array([10, 20, -1, -1])
    assert run.p_measures(a)["P2"] == 20
    assert run.p_measures(a)["P1"] == .5
    assert run.p_measures(np.array([10, -1, -1, -1]))["P2"] == run.NOT_REACHED
    result = run.paired_ratio(np.arange(1, 21) * 2, np.arange(1, 21))
    assert result["ratio"] == 2 and result["ci_95"] == [2, 2]
    assert result["resamples"] == 2000
    assert result == run.paired_ratio(np.arange(1, 21) * 2, np.arange(1, 21))
    undefined = run.paired_ratio([-1, -1], [-1, -1])
    assert undefined["ratio"] == "undefined" and undefined["ci_95"] is None
    assert undefined["undefined_resamples"] == 2000
    assert run.paired_ratio([-1, -1], [10, 10])["ci_95"] == ["infinity", "infinity"]
    assert run.paired_ratio([10, 10], [-1, -1])["ratio"] == 0


def test_pin_and_check64_contract():
    schedule, meta = run.pinned_schedule()
    assert len(schedule) == 1001
    assert meta["schedule_sha256"] == run.SCHEDULE_SHA256
    assert len(set(run.GRID)) == 18
    assert [n for _, _, _, n in run.CHECKS.values()] == [200, 200, 200, 200, 100, 200]
    assert run.CHECKS["registered_power"][1:3] == ("power", .05)
    assert run.CHECKS["m512_null"][0].M == 512
    assert not run.needs_cpu(run.REGISTERED, "null", [])
    assert run.needs_cpu(run.Cell(M=32), "null", ["uniform_null"])
    assert run.needs_cpu(run.Cell(M=512), "power", ["m512_null"])
    assert run.needs_cpu(run.Cell(M=32), "power", ["registered_null"])


def test_schedule_rejects_drift(tmp_path, monkeypatch):
    path = tmp_path / "draws.csv"
    path.write_bytes(reg.DRAWS.read_bytes().replace(b"2026-09-23", b"2026-09-22"))
    monkeypatch.setattr(reg, "DRAWS", path)
    with pytest.raises(ValueError, match="schedule differs"):
        run.pinned_schedule()


def test_cache_sharing_and_tamper_detection(tmp_path, monkeypatch):
    schedule = SCHEDULE[:3]
    common = {"schedule_sha256": "test"}
    first, _ = run.cache_draws(tmp_path, schedule, "null", 0, 0, 3, common)
    second, _ = run.cache_draws(tmp_path, schedule, "null", 0, 2, 4, common)
    np.testing.assert_array_equal(first[2], second[0])
    monkeypatch.setattr(run, "generate_draws", lambda *a: pytest.fail("cached stream regenerated"))
    run.cache_draws(tmp_path, schedule, "null", 0, 0, 3, common)
    path = tmp_path / "data/null/t3/s00000.npz"
    values, meta = run.read_npz(path)
    values["draws"][0, 0] = 999
    run.save_npz(path, values, meta)
    with pytest.raises(ValueError, match="corrupt"):
        run.cache_draws(tmp_path, schedule, "null", 0, 0, 1, common)


def test_comparator_runs_once(tmp_path, monkeypatch):
    schedule = SCHEDULE[:3]
    draws = run.generate_draws(schedule, "power", .05, 0, 2)
    common = {"schedule_sha256": "test"}
    run.comparator(tmp_path, draws, schedule, .05, 0, "cpu", common)
    monkeypatch.setattr(sim, "cpu_log_evidence", lambda *a, **k: pytest.fail("comparator repeated"))
    run.comparator(tmp_path, draws, schedule, .05, 0, "cpu", common)
    changed = draws.copy()
    changed[0, 0, 0] += 1
    with pytest.raises(ValueError, match="stale comparator"):
        run.comparator(tmp_path, changed, schedule, .05, 0, "cpu", common)


def test_comparator_hit_requires_matching_backend(tmp_path, monkeypatch):
    # An entry the MLX path wrote records its environment; a CPU run must not reuse it.
    schedule = SCHEDULE[:3]
    draws = run.generate_draws(schedule, "power", .05, 0, 1)
    common = {"schedule_sha256": "test"}
    original = run.environment
    monkeypatch.setattr(run, "environment", lambda backend: {"backend": "mlx", "dtype": "float32"})
    run.comparator(tmp_path, draws, schedule, .05, 0, "cpu", common)
    monkeypatch.setattr(run, "environment", original)
    with pytest.raises(ValueError, match="stale comparator"):
        run.comparator(tmp_path, draws, schedule, .05, 0, "cpu", common)


def test_coverage_rejects_missing_overlapping_and_corrupt():
    piece = ({"x": np.array([1, 2])}, {"lo": 0, "hi": 2})
    np.testing.assert_array_equal(run.coverage([piece], 2, ("x",))["x"], [1, 2])
    with pytest.raises(ValueError, match="incomplete"):
        run.coverage([piece], 3, ("x",))
    with pytest.raises(ValueError, match="overlapping"):
        run.coverage([piece, piece], 2, ("x",))
    with pytest.raises(ValueError, match="invalid shard"):
        run.coverage([({"x": np.array([np.nan, 0])}, piece[1])], 2, ("x",))
    with pytest.raises(ValueError, match="provenance"):
        run.validate_meta({"code_sha256": "old"}, {"code_sha256": "new"})


def test_pairing_checks_global_stream_hashes():
    paired = {}
    meta = {"lo": 7, "hi": 9, "arm": "power", "theta1": .05,
            "draws_sha256": {"7": "same", "8": "original"}}
    run.validate_pairing(meta, paired)
    run.validate_pairing({**meta, "hi": 8, "draws_sha256": {"7": "same"}}, paired)
    with pytest.raises(ValueError, match="pairing mismatch"):
        run.validate_pairing({**meta, "draws_sha256": {"7": "same", "8": "different"}}, paired)
    with pytest.raises(ValueError, match="incomplete per-stream"):
        run.validate_pairing({**meta, "draws_sha256": {"7": "same"}}, {})


@pytest.mark.parametrize("crossing", [[0, -1], [3004], [1.5], [float("nan")], []])
def test_rejects_invalid_crossing(crossing):
    with pytest.raises(ValueError, match="crossing must"):
        run.p_measures(crossing)


def test_checks64_coverage_and_failure(tmp_path):
    common = {"code_sha256": "test"}
    with pytest.raises(ValueError, match="incomplete"):
        run.validated_checks(tmp_path, common)
    for name, (cell, arm, theta, n) in run.CHECKS.items():
        run.save_npz(tmp_path / "checks" / name / "synthetic.npz",
                     {"max_abs_delta_log_e": np.full(n, .002 if name == "m512_null" else .0001)},
                     {**common, "kind": "check64", "check": name, "cell": asdict(cell), "arm": arm,
                      "theta1": theta, "T": 1001 if arm == "null" else 3003, "lo": 0, "hi": n})
    checks, failed = run.validated_checks(tmp_path, common)
    assert failed == ["m512_null"]
    assert checks["registered_power"]["n"] == 200


def test_check64_checks_cumulative_evidence_and_records_failure(tmp_path, monkeypatch):
    schedule = [("synthetic", 42)] * 1001
    monkeypatch.setattr(run, "pinned_schedule", lambda: (schedule, {"schedule_sha256": "test"}))
    monkeypatch.setattr(run, "environment", lambda backend: {"backend": backend})
    monkeypatch.setattr(run, "cache_draws", lambda *a: (np.zeros((1, 1001, 6), dtype=int), {"0": "test"}))

    def evaluate(cell, draws, schedule, normals, backend, chunk):
        assert cell == run.REGISTERED and normals.shape == (1, 1001, 64, 6)
        return {"le": np.full((1, 1001), 2e-6 if backend == "mlx" else 0)}

    monkeypatch.setattr(run, "evaluate", evaluate)
    assert run.main(["check64", "--check", "registered_null", "--lo", "0", "--hi", "1",
                     "--cache", str(tmp_path)]) == 2
    values, meta = run.read_npz(tmp_path / "checks/registered_null/00000-00001.npz")
    assert not meta["passed"]
    assert values["max_abs_delta_log_e"][0] == pytest.approx(.002002)


def test_aggregate_split_samples_and_defect_stop(monkeypatch, tmp_path):
    cells = (run.REGISTERED, run.Cell(.01, 0))
    monkeypatch.setattr(run, "GRID", cells)
    monkeypatch.setattr(run, "validated_checks", lambda *a: ({}, []))
    failed_gate = False

    def collect(cache, cell, arm, theta, backend, common, paired=None):
        if arm == "null":
            return {"sup": np.zeros(10), "n2_excess": np.full(10, .01 if failed_gate else -.1),
                    "final_log_e": np.zeros(10), "v0_final": np.ones(10), "log_sr_max": np.zeros(10)}, {}
        # Selection favors the other cell; its evaluation is deliberately worse.
        a, b = (200, 100) if cell == run.REGISTERED else (100, 200)
        return {"crossing": np.r_[np.full(1000, a), np.full(1000, b)]}, {}

    monkeypatch.setattr(run, "collect_cell", collect)
    monkeypatch.setattr(run, "collect_comparator", lambda *a: (np.full(2000, 100), {}))
    result = run.aggregate(tmp_path, {})
    assert result["verdict"] == "ROBUST"
    assert result["decision"]["B"] == asdict(cells[1])
    assert result["decision"]["evaluation_registered"]["P2"] == 100
    assert result["decision"]["evaluation_B"]["P2"] == 200
    assert result["decision"]["evaluation_P2_reg_over_B"]["ratio"] == .5
    json.dumps(result, allow_nan=False)
    failed_gate = True
    monkeypatch.setattr(run, "collect_comparator", lambda *a: pytest.fail("power after defect"))
    result = run.aggregate(tmp_path, {})
    assert result["verdict"] == "DEFECT" and not result["accepted"]
    assert all("power" not in row for row in result["cells"])


@pytest.mark.parametrize("args", [
    ["cell", "--arm", "null", "--lo", "0", "--hi", "20001"],
    ["cell", "--arm", "null", "--lo", "0", "--hi", "1", "--tau", ".3"],
    ["cell", "--arm", "power", "--lo", "0", "--hi", "1"],
    ["check64", "--check", "registered_null", "--lo", "0", "--hi", "201"],
])
def test_cli_rejects_invalid_jobs(args):
    with pytest.raises(SystemExit) as exc:
        run.main(args)
    assert exc.value.code == 2


def test_cli_data_cell_cpu_smoke(tmp_path, monkeypatch):
    # A real, tiny CLI workflow; full schedule loading is separately checked above.
    monkeypatch.setattr(run, "pinned_schedule", lambda: (SCHEDULE, {"schedule_sha256": "smoke"}))
    args = ["--cache", str(tmp_path), "--arm", "power", "--theta1", ".05",
            "--lo", "7", "--hi", "8", "--max-draws", "3"]
    assert run.main(["data", *args]) == 0
    assert run.main(["cell", *args, "--backend", "cpu", "--m", "32"]) == 0
    paths = list((tmp_path / "cells").rglob("*.npz"))
    assert len(paths) == 1
    values, meta = run.read_npz(paths[0])
    assert set(values) == set(run.SUMMARY_KEYS)
    assert meta["lo"] == 7 and meta["T"] == 3
    assert meta["cell"]["M"] == 32
    assert list((tmp_path / "comparators").rglob("*.npz"))
    with pytest.raises(ValueError, match="provenance"):
        run.collect_cell(tmp_path, run.Cell(M=32), "power", .05, "cpu", run.provenance({"schedule_sha256": "smoke"}))


def test_cli_cell_accepts_ranges_beyond_the_old_fixed_caps(tmp_path, monkeypatch):
    # The 295 s process-group supervisor bounds every call, so no fixed shard cap remains.
    monkeypatch.setattr(run, "pinned_schedule", lambda: (SCHEDULE, {"schedule_sha256": "smoke"}))
    monkeypatch.setattr(run, "evaluate", lambda *a: {k: np.zeros(53) for k in run.SUMMARY_KEYS})
    assert run.main(["cell", "--cache", str(tmp_path), "--arm", "null", "--lo", "0", "--hi", "53",
                     "--backend", "cpu", "--m", "32"]) == 0
    values, meta = run.read_npz(next((tmp_path / "cells").rglob("*.npz")))
    assert meta["lo"] == 0 and meta["hi"] == 53
    assert set(values) == set(run.SUMMARY_KEYS)


@pytest.mark.parametrize("kwargs", [{"tau": 0}, {"tau": float("nan")}, {"rho": -.01},
                                    {"rho": 1.1}, {"v0": [1, 2]}, {"v0": [0] * 7}])
def test_cp_parameter_validation(kwargs):
    with pytest.raises(ValueError):
        sim.cp_prior(**kwargs)


def test_power_guard_opt_in():
    sim.validate_power_m(128, .05)
    for M in (32, 512):
        with pytest.raises(ValueError, match="production M=128"):
            sim.validate_power_m(M, .05)
        sim.validate_power_m(M, .05, sensitivity=True)
    with pytest.raises(ValueError, match="production M=128"):
        sim.validate_power_m(64, .05, sensitivity=True)


@pytest.mark.parametrize("flag", ["--null-shard", "--power-shard", "--check-shard"])
def test_plan_rejects_nonpositive_shards(flag):
    argv = ["plan", "--null-shard", "10", "--power-shard", "10", "--check-shard", "10"]
    argv[argv.index(flag) + 1] = "0"
    with pytest.raises(SystemExit) as exc:
        run.main(argv)
    assert exc.value.code == 2


def test_plan_tiles_every_arm_and_orders_grid_cells(capsys):
    null_shard, power_shard, check_shard = 700, 500, 64
    assert run.main(["plan", "--null-shard", "700", "--power-shard", "500", "--check-shard", "64"]) == 0
    lines = capsys.readouterr().out.splitlines()
    check_limit = {name: n for name, (_, _, _, n) in run.CHECKS.items()}
    spans, limits, data_order, cell_keys = {}, {}, [], []
    for line in lines:
        argv = shlex.split(line)
        assert argv[:2] == ["python", "tools/pcso_cpnest_sensitivity.py"]
        command, flags = argv[2], dict(zip(argv[3::2], argv[4::2]))
        if command == "check64":
            key, limit = ("check64", flags["--check"]), check_limit[flags["--check"]]
        else:
            limit = run.NULL_N if flags["--arm"] == "null" else run.POWER_N
            key = (command, flags["--arm"], flags.get("--theta1"))
            if command == "data":
                if not data_order or data_order[-1] != key:
                    data_order.append(key)
                key = None
            else:
                assert flags["--backend"] == "mlx"
                cell = run.Cell(float(flags["--tau"]), float(flags["--rho"]), flags["--v0"], int(flags["--m"]))
                assert cell in run.GRID
                cell_keys.append((flags["--tau"], flags["--rho"], flags["--v0"], flags["--m"],
                                  flags["--arm"], flags.get("--theta1")))
                key = (*key, cell.key)
        if key is not None:
            spans.setdefault(key, []).append((int(flags["--lo"]), int(flags["--hi"])))
            assert limits.setdefault(key, limit) == limit
    # Data shards come first: null arm, then each theta1.
    assert data_order == [("data", "null", None)] + [("data", "power", f"{t:g}") for t in run.THETAS]
    # Every declared check is planned, within its own stream limit.
    assert {k[1] for k in spans if k[0] == "check64"} == set(run.CHECKS)
    assert len(cell_keys) == 18 * (math.ceil(run.NULL_N / null_shard) + 3 * math.ceil(run.POWER_N / power_shard))
    # Cells follow GRID order; within each cell the null arm then power theta1 ascending,
    # each arm tiled into ceil(limit/shard) consecutive shards.
    expected_cells = [(f"{c.tau:g}", f"{c.rho:g}", c.v0, str(c.M), arm, None if arm == "null" else f"{t:g}")
                      for c in run.GRID
                      for arm, t, limit, shard in (("null", None, run.NULL_N, null_shard),
                                                   ("power", .025, run.POWER_N, power_shard),
                                                   ("power", .05, run.POWER_N, power_shard),
                                                   ("power", .1, run.POWER_N, power_shard))
                      for _ in range(math.ceil(limit / shard))]
    assert cell_keys == expected_cells
    # Ranges tile [0, limit) exactly: adjacent, ordered, no gap or overlap.
    for key, pieces in spans.items():
        position = 0
        for lo, hi in sorted(pieces):
            assert lo == position < hi
            position = hi
        assert position == limits[key]
