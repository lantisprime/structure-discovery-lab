#!/usr/bin/env python3
"""Tests for install.py — unit tests for its pure helpers plus integration
tests of the wizard's non-interactive flows against a synthetic mini-lab.

Run: python3 -m pytest tests/test_installer.py -q
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_install():
    spec = importlib.util.spec_from_file_location(
        "install", os.path.join(REPO, "install.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


install = load_install()


# ------------------------------------------------------------ unit tests
def test_read_requirements_strips_comments(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("# full lab runtime\nnumpy>=1.24  # ubiquitous\n\n"
                   "scipy>=1.10\n# trailing comment\n")
    assert install.read_requirements(str(req)) == ["numpy>=1.24",
                                                   "scipy>=1.10"]


def test_count_jsonl_skips_comments_and_blanks(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text('# header\n{"a":1}\n\n{"b":2}\n')
    assert install.count_jsonl(str(p)) == 2
    assert install.count_jsonl(str(tmp_path / "missing.jsonl")) is None


def test_frozen_scripts_detected_in_real_repo():
    frozen = install.frozen_scripts()
    assert len(frozen) >= 20, "the lab ships ~22 frozen historical scripts"
    assert "relational_batch5.py" in frozen


def test_obfuscated_key_round_trips_through_server(tmp_path, monkeypatch):
    """The installer must write keys in EXACTLY the console's at-rest format:
    decode with webapp/server.py's own _deobf against the same salt."""
    monkeypatch.setattr(install, "WEBAPP", str(tmp_path))
    token = install.obfuscate_key("sk-test-roundtrip-123")
    assert token.startswith("enc1:")
    sys.path.insert(0, os.path.join(REPO, "webapp"))
    try:
        import server
        monkeypatch.setattr(server, "SALT_FILE",
                            os.path.join(str(tmp_path), ".keysalt"))
        assert server._deobf(token) == "sk-test-roundtrip-123"
    finally:
        sys.path.pop(0)
    salt = os.path.join(str(tmp_path), ".keysalt")
    assert oct(os.stat(salt).st_mode & 0o777) == "0o600"


def test_snapshot_hash_format(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("hello")
    monkeypatch.setattr(install, "ROOT", str(tmp_path))
    import io
    buf = io.StringIO()
    install.snapshot_hashes(buf)
    lines = buf.getvalue().strip().splitlines()
    assert lines == ["2cf24dba5fb0a30e  ./docs/a.md"]  # sha256('hello')[:16]


# ----------------------------------------------------- integration tests
def make_mini_lab(root):
    """Small synthetic lab with the same skeleton install.py relies on."""
    for d in ("src", "webapp", "results/agent_runs", "datasets/_TEMPLATE",
              "datasets/toy-data", "tools"):
        os.makedirs(os.path.join(root, d))
    stub = "#!/usr/bin/env python3\nraise SystemExit(0)\n"
    open(os.path.join(root, "src", "lint_frozen_imports.py"), "w").write(stub)
    open(os.path.join(root, "webapp", "test_lab_deps.py"), "w").write(stub)
    open(os.path.join(root, "requirements.txt"), "w").write("")  # no pip work
    open(os.path.join(root, "datasets", "_TEMPLATE", "DATASET.md"),
         "w").write("template card\n")
    open(os.path.join(root, "datasets", "toy-data", "DATASET.md"),
         "w").write("toy card\n")
    res = os.path.join(root, "results")
    open(os.path.join(res, "run_ledger.jsonl"), "w").write(
        '{"run_id": "r1", "date": "2026-01-01", "script": "src/x.py", '
        '"output": "results/x.json"}\n')
    open(os.path.join(res, "multiplicity_ledger.jsonl"), "w").write("")
    open(os.path.join(res, "commitment_ledger.txt"), "w").write(
        "# Commitment ledger — append-only.\n")
    open(os.path.join(res, "admission_log.txt"), "w").write("")
    open(os.path.join(res, "old_result.json"), "w").write("{}")
    shutil.copy(os.path.join(REPO, "install.py"),
                os.path.join(root, "install.py"))


def run_installer(root, *flags):
    return subprocess.run(
        [sys.executable, "install.py", "--yes", "--env", "system",
         "--riemann", "no", *flags],
        cwd=root, capture_output=True, text=True)


def test_keep_everything_changes_nothing(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = run_installer(root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not os.path.exists(os.path.join(root, "archive"))
    assert os.path.exists(os.path.join(root, "datasets", "toy-data"))
    led = open(os.path.join(root, "results", "run_ledger.jsonl")).read()
    assert '"run_id": "r1"' in led, "keep mode must not touch the ledger"


def test_clean_ledger_archives_never_deletes(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = run_installer(root, "--ledger", "clean")
    assert r.returncode == 0, r.stdout + r.stderr
    arch = os.path.join(root, "archive")
    sub = os.listdir(arch)[0]
    old = open(os.path.join(arch, sub, "results",
                            "run_ledger.jsonl")).read()
    assert '"run_id": "r1"' in old, "history must survive in the archive"
    assert open(os.path.join(arch, sub, "results",
                             "old_result.json")).read() == "{}"
    fresh = open(os.path.join(root, "results", "run_ledger.jsonl")).read()
    assert fresh == "", "fresh ledger must be empty"
    commit = open(os.path.join(root, "results",
                               "commitment_ledger.txt")).read()
    assert "append-only" in commit and "install.py" in commit
    assert "  ./install.py" in commit, "fresh snapshot must hash the tree"


def test_clean_datasets_keeps_template(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = run_installer(root, "--datasets", "clean", "--ledger", "clean")
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.listdir(os.path.join(root, "datasets")) == ["_TEMPLATE"]
    arch = os.path.join(root, "archive")
    sub = os.listdir(arch)[0]
    assert os.path.exists(os.path.join(arch, sub, "datasets", "toy-data",
                                       "DATASET.md"))
    # ordering: the fresh commitment snapshot must NOT list archived datasets
    commit = open(os.path.join(root, "results",
                               "commitment_ledger.txt")).read()
    assert "./datasets/toy-data" not in commit
    assert "./datasets/_TEMPLATE/DATASET.md" in commit


def test_keyless_provider_configures_roles(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = run_installer(root, "--provider", "ollama")
    assert r.returncode == 0, r.stdout + r.stderr
    cfg = json.load(open(os.path.join(root, "webapp", "config.local.json")))
    assert cfg["settings"]["active_provider"] == "ollama"
    roles = cfg["settings"]["agent_roles"]
    assert {r_ for r_ in roles} == {"analyst", "executor", "reviewer",
                                    "companion"}
    assert all(roles[x]["provider"] == "ollama" for x in roles)
    mode = os.stat(os.path.join(root, "webapp",
                                "config.local.json")).st_mode & 0o777
    assert oct(mode) == "0o600"


def test_provider_key_from_env_is_obfuscated(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    env = dict(os.environ, LAB_LLM_API_KEY="sk-env-secret-42")
    r = subprocess.run(
        [sys.executable, "install.py", "--yes", "--env", "system",
         "--riemann", "no", "--provider", "anthropic"],
        cwd=root, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    raw = open(os.path.join(root, "webapp", "config.local.json")).read()
    assert "sk-env-secret-42" not in raw, "keys must never rest in plaintext"
    cfg = json.loads(raw)
    assert cfg["api_keys"]["PROVIDER_ANTHROPIC_KEY"].startswith("enc1:")


def test_dry_run_changes_nothing(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    before = sorted(os.listdir(root))
    r = subprocess.run(
        [sys.executable, "install.py", "--dry-run", "--ledger", "clean",
         "--datasets", "clean"],
        cwd=root, capture_output=True, text=True)
    assert r.returncode == 0
    assert "--dry-run: nothing was changed" in r.stdout
    assert sorted(os.listdir(root)) == before
    assert not os.path.exists(os.path.join(root, "archive"))


def test_gitignore_gains_archive_and_venv(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    open(os.path.join(root, ".gitignore"), "w").write("*.pyc")  # no newline
    run_installer(root)
    gi = open(os.path.join(root, ".gitignore")).read()
    assert ".venv/" in gi and "archive/" in gi
    assert "*.pyc\n" in gi, "existing entry must survive with newline intact"


def test_real_repo_dry_run():
    r = subprocess.run([sys.executable, "install.py", "--dry-run"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "frozen historical scripts" in r.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


def test_restore_swaps_archive_back(tmp_path):
    """--restore must undo a clean start: archived history returns, the
    displaced fresh state is itself archived (nothing deleted)."""
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = run_installer(root, "--ledger", "clean", "--datasets", "clean")
    assert r.returncode == 0
    first_arch = os.path.join("archive", os.listdir(
        os.path.join(root, "archive"))[0])
    r = subprocess.run([sys.executable, "install.py", "--restore",
                        first_arch], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    led = open(os.path.join(root, "results", "run_ledger.jsonl")).read()
    assert '"run_id": "r1"' in led, "history must be back after restore"
    assert os.path.isdir(os.path.join(root, "datasets", "toy-data"))
    archives = sorted(os.listdir(os.path.join(root, "archive")))
    assert len(archives) == 2, "displaced fresh state must be archived too"


def test_restore_rejects_bogus_archive(tmp_path):
    root = str(tmp_path / "lab")
    make_mini_lab(root)
    r = subprocess.run([sys.executable, "install.py", "--restore",
                        "archive/nope"], cwd=root,
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "not found" in r.stderr + r.stdout
