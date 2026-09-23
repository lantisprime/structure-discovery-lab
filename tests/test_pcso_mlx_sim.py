"""Arithmetic equivalence is primary; independent KS/Fisher tests are gross screens."""
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pcso_mlx_sim as sim

reg = sim.reg
requires_mlx = pytest.mark.skipif(sim.mx is None, reason="MLX unavailable; requires Apple GPU")
SCHEDULE = [(f"sim-{i:04d}", [42, 45, 49, 55, 58][i % 5]) for i in range(120)]


def record(key, value):
    print(key, json.dumps(value), flush=True)
    path = os.environ.get("PCSO_MLX_EQUIV_REPORT")
    if path:
        path = Path(path)
        data = json.loads(path.read_text()) if path.exists() else {}
        data[key] = value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")


def test_replayed_gaussians_match_cpu():
    draws = sim.cp_streams(SCHEDULE[:8], 1, np.random.default_rng(2))
    zf = np.random.default_rng(7).standard_normal((1, 8, 16, 6))
    plain = sim.cpu_log_evidence("cp_nest", draws, SCHEDULE[:8], seed=7)
    replay = sim.cpu_log_evidence("cp_nest", draws, SCHEDULE[:8], zf_seq=zf)
    np.testing.assert_array_equal(plain, replay)


def test_draws_and_accounting_match_registry():
    schedule = SCHEDULE[:12]
    draws = sim.cp_streams(schedule, 1, np.random.default_rng(4), theta1=0.1)
    assert np.all(np.diff(draws, axis=2) > 0)
    for name in sim.MODELS:
        le = sim.cpu_log_evidence(name, draws, schedule, seed=9)
        result = sim.evidence_summary(le)
        rows = [(d, P, tuple(S)) for (d, P), S in zip(schedule, draws[0])]
        ref = reg.run([sim.cpu_model(name, seed=9)], rows, warmup=10**9, track_sup=True)[name]
        assert result["sup"][0] == pytest.approx(ref["sup"], abs=1e-12)
        assert result["log_sr_max"][0] == pytest.approx(math.log(ref["sr_max"]), abs=1e-12)
    le = np.array([[0., 5., -1.], [-1., -1., -1.], [1000., 0., 0.]])
    result = sim.evidence_summary(le)
    np.testing.assert_array_equal(result["crossing"], [2, -1, 1])
    np.testing.assert_array_equal(result["sup"], [5., 0., 1000.])
    assert np.isfinite(result["log_sr_max"]).all()


@requires_mlx
@pytest.mark.parametrize("name", sim.MODELS)
def test_deterministic(name):
    draws = sim.cp_streams(SCHEDULE, 3, np.random.default_rng(11), theta1=0.1)
    zf = np.random.default_rng(12).standard_normal((3, len(SCHEDULE), 16, 6))
    cpu = sim.cpu_log_evidence(name, draws, SCHEDULE, zf_seq=zf.astype(np.float32).astype(np.float64))
    gpu = sim.mlx_log_evidence(name, draws, SCHEDULE, zf_seq=zf, chunk=2)["le"]
    error = np.abs(cpu - gpu)
    nz = np.abs(cpu) > 1e-12
    report = {"max_scaled_relative_error": float((error / np.maximum(1, np.abs(cpu))).max()),
              "max_absolute_error": float(error.max()),
              "max_unfloored_relative_error": float((error[nz] / np.abs(cpu[nz])).max()) if nz.any() else 0,
              "rtol": 1e-4, "atol": 1e-5, "n_streams": 3, "horizon": len(SCHEDULE), "M": 32}
    record("deterministic_" + name, report)
    assert report["max_scaled_relative_error"] <= 1e-4
    np.testing.assert_allclose(gpu, cpu, rtol=1e-4, atol=1e-5)


@requires_mlx
def test_production_power_and_chunking():
    schedule = SCHEDULE[:25]
    draws = sim.cp_streams(schedule, 3, np.random.default_rng(13), theta1=0.1)
    zf = np.random.default_rng(14).standard_normal((3, len(schedule), 64, 6))
    cpu = sim.cpu_log_evidence("cp_nest", draws, schedule, M=128, zf_seq=zf.astype(np.float32).astype(np.float64))
    gpu = sim.mlx_log_evidence("cp_nest", draws, schedule, M=128, zf_seq=zf, chunk=2)
    np.testing.assert_allclose(gpu["le"], cpu, rtol=1e-4, atol=1e-5)
    short = sim.mlx_log_evidence("cp_nest", draws[:, :10], schedule[:10], M=128,
                                 zf_seq=zf[:, :10], chunk=3)
    np.testing.assert_allclose(short["le"], gpu["le"][:, :10], atol=2e-6, rtol=1e-4)
    record("production_M128", {"max_scaled_relative_error": float(np.max(
        np.abs(cpu - gpu["le"]) / np.maximum(1, np.abs(cpu))))})


@requires_mlx
@pytest.mark.parametrize("name", sim.MODELS)
def test_statistical_null(name):
    schedule = SCHEDULE[:100]
    cpu = sim.cpu_null(name, 400, schedule, seed=20260923, workers=8)
    draws = sim.cp_streams(schedule, 2000, np.random.default_rng(20260924))
    gpu = sim.mlx_log_evidence(name, draws, schedule, seed=20260924)
    report = sim.compare_null(cpu["sup"], cpu["log_sr_max"], gpu)
    record("statistical_" + name, report)
    assert report["ks_p"] >= 0.05
    assert report["sr_ks_p"] >= 0.05
    assert report["crossing_fisher_p"] >= 0.05
    # A lower confidence endpoint above 0.01 would contradict null error control.
    assert report["mlx_crossing_ci_95"][0] <= sim.ALPHA


@requires_mlx
def test_validation_and_cli(tmp_path):
    draws = sim.cp_streams(SCHEDULE[:2], 1, np.random.default_rng(0))
    for kw in ({"M": 3}, {"chunk": 0}, {"device": "invalid"}, {"zf_seq": np.zeros((1, 2, 1, 6))}):
        with pytest.raises(ValueError):
            sim.mlx_log_evidence("cp_nest", draws, SCHEDULE[:2], **kw)
    invalid = draws.copy()
    invalid[0, 0, 1] = invalid[0, 0, 0]
    with pytest.raises(ValueError, match="distinct"):
        sim.mlx_log_evidence("uniform", invalid, SCHEDULE[:2])
    out = tmp_path / "power.json"
    sim.main(["--null-streams", "2", "--models", "tilt_high31", "pair_parity", "--max-draws", "4",
              "--theta1", "0.05", "--device", "cpu", "--out", str(out)])
    data = json.loads(out.read_text())
    assert data["_meta"]["status"] == "exploratory, not registered"
    assert data["_meta"]["dtype"] == "float32"
    assert data["_meta"]["M"] == 128
    assert "cpu" in data["_meta"]["device"]
    assert data["simulation"] == "power"
    assert set(data["models"]) == {"tilt_high31", "pair_parity"}


def test_metadata_without_mlx(monkeypatch):
    monkeypatch.setattr(sim, "mx", None)
    meta = sim.metadata(1, SCHEDULE, 32, 16)
    assert meta["device"] == "unavailable"
    assert meta["device_info"] is None
    assert meta["mlx_version"] is None
    assert meta["schedule_draws"] == 120
    assert "schedule" not in meta


def test_sampler_rejects_incomplete_rows():
    class NeverTake:
        def random(self, n):
            return np.ones(n)
    with np.errstate(invalid="ignore", divide="ignore"):
        with pytest.raises(RuntimeError, match="incomplete"):
            sim.cp_streams(SCHEDULE[:1], 2, NeverTake())


def test_queue_rejects_transposed_shapes():
    with pytest.raises(AssertionError):
        sim._ZFQueue([np.zeros((6, 16))]).standard_normal((16, 6))


def test_sr_only_discrepancy_changes_verdict():
    sup = np.zeros(100)
    report = sim.compare_null(sup, np.zeros(100), {"sup": sup, "log_sr_max": np.ones(100)})
    assert report["ks_p"] == 1
    assert report["sr_ks_p"] < .05
    assert report["verdict"] == "discrepancy detected"


def test_crossing_summary_names_real_horizon():
    result = sim.evidence_summary(np.zeros((2, 994)))
    assert sim.crossing_summary(result, 994)["horizon"] == 994


@requires_mlx
@pytest.mark.parametrize("name,M", [(n, 32) for n in sim.PORTED] + [("cp_nest", 128)])
def test_full_horizon_matched(name, M):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    from pcso_mlx_validate import matched, paired_metrics, assert_paired, drift_metrics, assert_drift
    schedule = [(d, P) for d, P, _ in reg.load() if d <= "2026-09-20"]
    assert len(schedule) == 994
    assert sim.metadata(0, schedule, M, 16)["schedule_sha256"] == "7ca585656595199a76a78c4834eed7aa1a0defa536df73c3f78351bd159db9cb"
    default = sim.mx.default_device()
    cpu, results, inputs = matched(name, schedule, n=16, M=M, devices=("gpu", "cpu"))
    assert sim.mx.default_device() == default
    for device, result in results.items():
        paired = paired_metrics(cpu, result)
        drift = drift_metrics(cpu["le"], result["le"])
        record(f"full_{name}_m{M}_{device}", {"paired": paired, "drift": drift, "inputs": inputs})
        assert_paired(paired)
        assert_drift(drift, cpu, result)


@requires_mlx
def test_contract_accumulation_order():
    x = np.array([[1e8, 1, -1e8, 3]], dtype=np.float32)
    matrix = np.ones((4, 2), dtype=np.float32)
    expected = x[:, :1] * matrix[0]
    for j in range(1, 4):
        expected = expected + x[:, j:j+1] * matrix[j]
    for device in (sim.mx.cpu, sim.mx.gpu):
        with sim.mx.stream(device):
            actual = sim._contract(sim.mx.array(x), sim.mx.array(matrix))
            np.testing.assert_array_equal(np.array(actual), expected)


@requires_mlx
def test_normalized_esp_matches_reference():
    for device in (sim.mx.cpu, sim.mx.gpu):
        with sim.mx.stream(device):
            for P in (42, 45, 49, 55, 58):
                ones = sim._normalized_esp6(sim.mx.ones((2, P)))
                np.testing.assert_array_equal(np.array(ones), np.ones(2))
                w = np.exp(np.random.default_rng(P).normal(0, .2, (4, P))).astype(np.float32)
                ref = reg.esp(w.astype(float))[:, 6] / math.comb(P, 6)
                np.testing.assert_allclose(np.array(sim._normalized_esp6(sim.mx.array(w))), ref,
                                           rtol=1e-6, atol=1e-7)
