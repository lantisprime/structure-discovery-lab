"""Synthetic registered-window accounting and deterministic CLI verification."""
from datetime import date, timedelta
import hashlib
import math
from pathlib import Path
import json
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R
import pcso_sparse_registered as runner
import pcso_sparse_switch as M


@pytest.fixture(autouse=True)
def small(monkeypatch):
    # Keep all five game-prior masses, as in test_pcso_sparse_switch.small.
    monkeypatch.setattr(M, "POOLS", (8, 9, 10, 11, 12))


@pytest.fixture
def rows():
    # Same-date game-name order need not be numeric pool order. Preserve it.
    conditioning = [
        ("2026-09-22", 11, (1, 2, 3, 4, 5, 6)),
        ("2026-09-22", 8, (1, 2, 3, 4, 5, 7)),
        ("2026-09-23", 9, (2, 3, 4, 5, 6, 7)),
        ("2026-09-23", 10, (1, 3, 5, 7, 9, 10)),
    ]
    rng = np.random.default_rng(20260924)
    registered = [
        ((date(2026, 9, 24) + timedelta(days=i // 3)).isoformat(), P,
         tuple(sorted(int(x) for x in rng.choice(P, 6, replace=False) + 1)))
        for i, P in enumerate([11, 8, 9, 10, 12, 8, 9, 10, 11, 12, 8, 9])
    ]
    return conditioning + registered


def test_clock_restarts_before_first_prediction_and_retains_weights(monkeypatch, rows):
    expected, fresh = M.CPSparseSwitch(), M.CPSparseSwitch()
    for d, P, S in rows:
        if d <= runner.REGISTRATION_DATE:
            expected.update(P, S)
    assert expected.t == 4
    original_run = R.run_registered
    prediction_clocks = []

    def forbidden_reset(self):
        pytest.fail("reset() discards the conditioning weights")

    def inspect_run(models, registered_rows):
        assert len(models) == 1
        model = models[0]
        assert model.t == 0
        assert registered_rows == rows[4:]
        assert model.log_uniform == expected.log_uniform
        for P in M.POOLS:
            actual_game, expected_game = model._games[P], expected._games[P]
            assert (actual_game.scale, actual_game.inject, actual_game.mass) == (
                expected_game.scale, expected_game.inject, expected_game.mass)
            for actual, wanted in zip(actual_game.log_weights(), expected_game.log_weights()):
                np.testing.assert_array_equal(actual, wanted)
        assert not np.allclose(model.predict(8).inclusion(), fresh.predict(8).inclusion())
        original_predict = model.predict

        def inspect_predict(P):
            prediction_clocks.append(model.t)
            return original_predict(P)

        monkeypatch.setattr(model, "predict", inspect_predict)
        result = original_run(models, registered_rows)
        assert model.t == len(registered_rows)
        return result

    monkeypatch.setattr(M.CPSparseSwitch, "reset", forbidden_reset)
    monkeypatch.setattr(R, "run_registered", inspect_run)
    runner.score(rows)
    assert prediction_clocks[0] == 0


def test_boundary_date_is_conditioning_only(rows):
    result = runner.score(rows)
    assert result["_meta"]["n_conditioning"] == 4
    assert result["_meta"]["last_conditioning_date"] == "2026-09-23"
    assert result["registered"]["n"] == len(rows) - 4
    assert [P for P, _ in result["registered"]["overlaps"]] == [P for _, P, _ in rows[4:]]


def test_evidence_and_detector_match_independent_manual_loop(rows):
    model = M.CPSparseSwitch()
    for _, P, S in rows[:4]:
        model.update(P, S)
    model.t = 0
    log_e, log_e_max = 0.0, 0.0
    log_m = log_m_max = -math.inf
    for t, (_, P, S) in enumerate(rows[4:], start=1):
        increment = model.predict(P).logq(S) + math.log(math.comb(P, 6))
        log_e += increment
        log_e_max = max(log_e_max, log_e)
        # Independent scalar recurrence, without run_registered or np.logaddexp.
        log_m = increment + math.log(math.exp(log_m) + 1 / (t * (t + 1)))
        log_m_max = max(log_m_max, log_m)
        model.update(P, S)
        actual = runner.score(rows[:4 + t])["registered"]
        assert actual["n"] == t
        assert actual["log_E_final"] == round(log_e, 6)
        assert actual["log_E_max"] == round(log_e_max, 6)
        assert actual["log_M_max"] == round(log_m_max, 6)
        assert actual["E_final"] == pytest.approx(math.exp(log_e), rel=1e-12)
        assert actual["E_max"] == pytest.approx(math.exp(log_e_max), rel=1e-12)
        assert actual["M_max"] == pytest.approx(math.exp(log_m_max), rel=1e-12)


@pytest.mark.parametrize("n_conditioning", [0, 4])
def test_no_registered_rows(rows, n_conditioning):
    result = runner.score(rows[:n_conditioning])
    assert result["_meta"]["n_conditioning"] == n_conditioning
    assert result["_meta"]["last_conditioning_date"] == (
        "2026-09-23" if n_conditioning else None)
    assert result["registered"] == {
        "n": 0, "E_final": 1.0, "E_max": 1.0, "M_max": 0.0,
        "log_E_final": 0.0, "log_E_max": 0.0, "log_M_max": None, "overlaps": [],
    }
    assert not any(result["decision"].values())


def test_registration_date_mismatch_fails(monkeypatch, rows):
    monkeypatch.setattr(R, "REGISTERED_AFTER", "2026-09-22")
    with pytest.raises(ValueError, match="REGISTERED_AFTER"):
        runner.score(rows)


@pytest.mark.parametrize("E_max,M_max,decisions", [
    (99.999, 99.999, (False, False, False)),
    (100.0, 0.0, (True, False, False)),
    (1.0, 100.0, (False, True, False)),
    (199.999, 199.999, (True, True, False)),
    (200.0, 0.0, (True, False, True)),
    (1.0, 200.0, (False, True, True)),
])
def test_decision_thresholds_use_running_maxima(monkeypatch, E_max, M_max, decisions):
    entry = {"E_final": 0.5, "E_max": E_max, "M_max": M_max}
    monkeypatch.setattr(R, "run_registered", lambda models, rows: {models[0].name: entry})
    result = runner.score([])
    assert result["registered"] is entry
    assert result["decision"] == dict(zip(
        ("evidence_rejection", "change_alarm", "combined"), decisions))


@pytest.fixture
def cli(monkeypatch, tmp_path, rows):
    monkeypatch.setattr(runner, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(R, "load", lambda: rows)
    return ["--run-date", "2026-09-24"], tmp_path / "pcso_sparse_registered_2026-09-24.json"


def test_cli_payload_provenance_and_verify_detects_one_byte_change(cli, capsys):
    argv, dst = cli
    runner.main(argv)
    before = dst.read_bytes()
    result = json.loads(before)
    meta = result["_meta"]
    assert before == (json.dumps(result, sort_keys=True, indent=1) + "\n").encode("utf-8")
    assert meta["schema_version"] == 1
    assert meta["script"] == "src/pcso_sparse_registered.py"
    assert meta["registration"] == "docs/REGISTRATION_PCSO_SPARSE_SWITCH.md"
    assert meta["registration_date"] == runner.REGISTRATION_DATE == R.REGISTERED_AFTER
    assert meta["run_date"] == "2026-09-24"
    assert meta["input_snapshot_commit"] == R.INPUT_SNAPSHOT_COMMIT
    assert meta["input_sha256"] == {
        "datasets/pcso-lotto/data_draws_1yr.csv": hashlib.sha256(R.DRAWS.read_bytes()).hexdigest()}
    assert meta["code_sha256"] == {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ("src/pcso_sparse_switch.py", "src/pcso_model_registry.py",
                     "src/pcso_sparse_registered.py")}
    assert meta["alpha"] == 0.01
    assert meta["thresholds"] == {"E": 100, "M": 100}
    assert meta["combined_alpha"] == {"E": 0.005, "M": 0.005}
    assert meta["combined_thresholds"] == {"E": 200, "M": 200}
    assert "0.005/0.005" in meta["note"]
    capsys.readouterr()
    stat = dst.stat()
    runner.main(argv + ["--verify"])
    assert capsys.readouterr().out == f"PASS sha256={hashlib.sha256(before).hexdigest()}\n"
    assert dst.read_bytes() == before
    assert dst.stat().st_mtime_ns == stat.st_mtime_ns
    # A one-byte replacement leaves valid JSON but must fail exact comparison.
    changed = before[:-1] + b" "
    dst.write_bytes(changed)
    stat = dst.stat()
    with pytest.raises(SystemExit, match="VERIFY FAIL"):
        runner.main(argv + ["--verify"])
    assert dst.read_bytes() == changed
    assert dst.stat().st_mtime_ns == stat.st_mtime_ns
    assert list(dst.parent.iterdir()) == [dst]


def test_cli_refuses_overwrite(cli):
    argv, dst = cli
    dst.write_bytes(b"existing artifact\n")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        runner.main(argv)
    assert dst.read_bytes() == b"existing artifact\n"


def test_cli_verify_missing_file_writes_nothing(cli):
    argv, dst = cli
    with pytest.raises(SystemExit):
        runner.main(argv + ["--verify"])
    assert list(dst.parent.iterdir()) == []


def test_cli_mismatch_fails_before_loading(cli, monkeypatch):
    argv, dst = cli
    monkeypatch.setattr(R, "REGISTERED_AFTER", "2026-09-24")
    monkeypatch.setattr(R, "load", lambda: pytest.fail("must reject the date before loading"))
    with pytest.raises(SystemExit, match="REGISTERED_AFTER"):
        runner.main(argv)
    assert not dst.exists()


def test_cli_propagates_conditioning_drift_without_writing(cli, monkeypatch):
    argv, dst = cli

    def drift():
        raise ValueError("live conditioning rows differ from INPUT_SNAPSHOT_COMMIT")

    monkeypatch.setattr(R, "load", drift)
    with pytest.raises(SystemExit, match="conditioning rows differ"):
        runner.main(argv)
    assert not dst.exists()


@pytest.mark.parametrize("argv", [[], ["--run-date", "2026-9-24"],
                                  ["--run-date", "2026-02-30"],
                                  ["--run-date", "20260924"]])
def test_cli_requires_iso_calendar_date(cli, monkeypatch, argv):
    monkeypatch.setattr(R, "load", lambda: pytest.fail("invalid CLI must not load rows"))
    with pytest.raises(SystemExit) as exc:
        runner.main(argv)
    assert exc.value.code == 2
    assert not cli[1].exists()
