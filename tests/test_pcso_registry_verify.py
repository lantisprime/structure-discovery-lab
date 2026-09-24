"""CLI regressions using committed, tiny input/harness fixtures in temporary Git repos."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "src/pcso_model_registry.py"
CSV = "datasets/pcso-lotto/data_draws_1yr.csv"
ARTIFACT = "results/pcso_model_leaderboard_2026-09-23.json"
MANIFEST = "results/pcso_model_leaderboard_provenance.json"
ARGV = [SCRIPT, "--seed", "20260923", "--run-date", "2026-09-23",
        "--null-sims", "1", "--power-sims", "1"]
DATA = ("Game,Date,N1,N2,N3,N4,N5,N6\n"
        "Lotto 6/42,2026-09-21,1,2,3,4,5,6\n"
        "Lotto 6/42,2026-09-23,2,3,4,5,6,7\n"
        "Lotto 6/42,2026-09-24,3,4,5,6,7,8\n")
# Fixture repos must not inherit the developer's Git config (signing, hooks, templates).
GIT_ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
# Matches the pin line of both the historical (95bc845) and the current harness.
PIN_LINE = re.compile(r'^INPUT_SNAPSHOT_COMMIT = "[0-9a-f]{7,40}"$', re.MULTILINE)


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, env=GIT_ENV).decode().strip()


def pinned(source, pin):
    source, count = PIN_LINE.subn(f'INPUT_SNAPSHOT_COMMIT = "{pin}"', source)
    assert count == 1, "harness pin line changed; update the fixture"
    return source


def commit(repo):
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Registry test", "-c", "user.email=registry@example.invalid",
        "commit", "-qm", "fixture")
    return git(repo, "rev-parse", "HEAD")


def cli(repo, verify=False):
    with tempfile.TemporaryDirectory(prefix="pcso-replay-test-") as td:
        result = subprocess.run([sys.executable, *ARGV, *(["--verify"] if verify else [])],
                                cwd=repo, capture_output=True, text=True, timeout=60,
                                env=dict(GIT_ENV, TMPDIR=td, PYTHONDONTWRITEBYTECODE="1"))
        assert not list(Path(td).glob("pcso-registry-replay-*")), "replay left temporary files"
        return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="session")
def template():
    with tempfile.TemporaryDirectory(prefix="pcso-registry-fixture-") as td:
        repo = Path(td)
        git(repo, "init", "-q")
        for directory in ("src", "datasets/pcso-lotto", "results"):
            (repo / directory).mkdir(parents=True)
        (repo / CSV).write_text(DATA)
        pin = commit(repo)
        old = git(ROOT, "show", "95bc845:" + SCRIPT) + "\n"
        (repo / SCRIPT).write_text(pinned(old, pin))
        harness = commit(repo)
        result = cli(repo)
        assert result.returncode == 0, result.stdout + result.stderr
        payload = (repo / ARTIFACT).read_bytes()
        entry = {"artifact_sha256": sha(payload), "harness_commit": harness,
                 "input_blob": git(repo, "rev-parse", "HEAD:" + CSV),
                 "input_sha256": sha((repo / CSV).read_bytes()), "argv": ARGV}
        (repo / MANIFEST).write_text(json.dumps({ARTIFACT: entry}, indent=2) + "\n")
        # The current implementation and the recorded harness are different commits.
        (repo / SCRIPT).write_text(pinned((ROOT / SCRIPT).read_text(), pin))
        commit(repo)
        yield repo


@pytest.fixture
def repo(template):
    with tempfile.TemporaryDirectory(prefix="pcso-registry-case-") as td:
        path = Path(td) / "repo"
        shutil.copytree(template, path)
        yield path


def manifest(repo):
    return json.loads((repo / MANIFEST).read_text())


def save_manifest(repo, entries):
    (repo / MANIFEST).write_text(json.dumps(entries, indent=2) + "\n")


@pytest.mark.parametrize("change", ["append_after", "append_before", "append_boundary", "edit"])
def test_historical_verify_ignores_live_csv_and_current_models(repo, change):
    text = DATA
    if change == "edit":
        text = text.replace("1,2,3,4,5,6", "1,2,3,4,5,9")
    else:
        date = {"append_after": "2026-09-25", "append_before": "2026-09-22",
                "append_boundary": "2026-09-23"}[change]
        text += f"Lotto 6/42,{date},4,5,6,7,8,9\n"
    (repo / CSV).write_text(text)
    script = repo / SCRIPT
    script.write_text(script.read_text().replace("def roster(seed):",
                      'def roster(seed):\n    raise AssertionError("current models must not run")'))
    before = {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    result = cli(repo, verify=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS sha256={sha(before[Path(ARTIFACT)])}; wrote=none" in result.stdout
    assert {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("failure, message", [
    ("tamper", "VERIFY MISMATCH"),
    ("manifest_hash", "VERIFY MISMATCH"),
    ("absent_entry", "absent from provenance manifest"),
    ("absent_manifest", "provenance manifest"),
    ("missing_commit", "recorded harness commit"),
    ("missing_blob", "recorded input blob"),
    ("input_hash", "recorded input sha256 mismatch"),
    ("replay_payload", "VERIFY MISMATCH"),
])
def test_verify_fails_closed(repo, failure, message):
    entries = manifest(repo)
    entry = entries[ARTIFACT]
    if failure == "tamper":
        with (repo / ARTIFACT).open("ab") as f:
            f.write(b" ")
    elif failure == "absent_entry":
        entries.clear()
    elif failure == "missing_commit":
        entry["harness_commit"] = "0" * 40
    elif failure == "missing_blob":
        entry["input_blob"] = "0" * 40
    elif failure == "input_hash":
        entry["input_sha256"] = "0" * 64
    elif failure == "manifest_hash":
        entry["artifact_sha256"] = "0" * 64
    elif failure == "replay_payload":
        entry["argv"][2] = "17"
    save_manifest(repo, entries)
    if failure == "absent_manifest":
        (repo / MANIFEST).unlink()
    before = (repo / ARTIFACT).read_bytes()
    result = cli(repo, verify=True)
    assert result.returncode != 0
    assert message in result.stdout + result.stderr
    assert (repo / ARTIFACT).read_bytes() == before


@pytest.mark.parametrize("change", ["append_before", "append_boundary", "edit", "delete"])
def test_write_rejects_conditioning_drift(repo, change):
    if change == "edit":
        data = DATA.replace("1,2,3,4,5,6", "1,2,3,4,5,9")
    elif change == "delete":
        data = DATA.replace("Lotto 6/42,2026-09-21,1,2,3,4,5,6\n", "")
    else:
        date = "2026-09-22" if change == "append_before" else "2026-09-23"
        data = DATA + f"Lotto 6/42,{date},4,5,6,7,8,9\n"
    (repo / CSV).write_text(data)
    commit(repo)  # Isolate the pin guard from the dirty-input guard.
    before = [(repo / p).read_bytes() for p in (ARTIFACT, MANIFEST)]
    result = cli(repo)
    assert result.returncode != 0
    assert "conditioning rows differ" in result.stdout + result.stderr
    assert [(repo / p).read_bytes() for p in (ARTIFACT, MANIFEST)] == before


@pytest.mark.parametrize("path, staged", [(SCRIPT, False), (SCRIPT, True),
                                         (CSV, False), (CSV, True)])
def test_write_rejects_inputs_differing_from_head(repo, path, staged):
    with (repo / path).open("a") as f:
        f.write("\n" if path == CSV else "\n# dirty harness\n")
    if staged:
        git(repo, "add", path)
    before = [(repo / p).read_bytes() for p in (ARTIFACT, MANIFEST)]
    result = cli(repo)
    assert result.returncode != 0
    assert f"{path} differs from HEAD" in result.stdout + result.stderr
    assert [(repo / p).read_bytes() for p in (ARTIFACT, MANIFEST)] == before


def current_payload(repo):
    """Payload the current harness writes for the fixture input, produced in a scratch copy.
    It differs from the 95bc845 fixture artifact (the _meta input_snapshot_note was reworded)."""
    with tempfile.TemporaryDirectory(prefix="pcso-registry-expected-") as td:
        scratch = Path(td) / "repo"
        shutil.copytree(repo, scratch)
        result = cli(scratch)
        assert result.returncode == 0, result.stdout + result.stderr
        return (scratch / ARTIFACT).read_bytes()


@pytest.mark.parametrize("existing_manifest", [True, False])
def test_write_preserves_payload_and_records_replayable_provenance(repo, existing_manifest):
    historical = json.loads((repo / ARTIFACT).read_bytes())
    before = current_payload(repo)
    current = json.loads(before)
    del historical["_meta"]["input_snapshot_note"]
    del current["_meta"]["input_snapshot_note"]
    assert current == historical
    harness = git(repo, "rev-parse", "HEAD")
    if not existing_manifest:
        (repo / MANIFEST).unlink()
    result = cli(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (repo / ARTIFACT).read_bytes() == before
    entry = manifest(repo)[ARTIFACT]
    assert entry == {"artifact_sha256": sha(before), "harness_commit": harness,
                     "input_blob": git(repo, "rev-parse", "HEAD:" + CSV),
                     "input_sha256": sha((repo / CSV).read_bytes()), "argv": ARGV}
    # A future HEAD must not affect validation inside an archived, newer harness.
    (repo / CSV).write_text(DATA + "Lotto 6/42,2026-09-25,4,5,6,7,8,9\n")
    commit(repo)
    result = cli(repo, verify=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS sha256={sha(before)}; wrote=none" in result.stdout


def test_live_write_ignores_replay_environment(repo, monkeypatch):
    monkeypatch.setenv("_PCSO_REGISTRY_REPLAY_COMMIT", manifest(repo)[ARTIFACT]["harness_commit"])
    result = cli(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert manifest(repo)[ARTIFACT]["harness_commit"] == git(repo, "rev-parse", "HEAD")
