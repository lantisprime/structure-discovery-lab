#!/usr/bin/env python3
"""R1-S1: the artifact registry is derived from the repo and covers the ledger."""
import importlib.util
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "src", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AR = load("artifact_registry")
OL = AR.OL


def test_registry_classes_and_tiers():
    reg = AR.build_registry(REPO)
    agents = {k: v for k, v in reg.items() if v["class"] == "agent"}
    assert "agents/data-reader.md" in agents and agents["agents/data-reader.md"]["tier"] == "haiku"
    assert agents["agents/structure-analyst.md"]["tier"] == "fable"
    assert reg["src/pcso_weekly_update.py"]["class"] == "instrument"
    assert reg["src/csi_popularity.py"]["class"] == "instrument"
    assert reg["docs/kb/conscious-selection-popularity.md"]["class"] == "theorem_card"
    assert "docs/kb/INDEX.md" not in reg
    assert reg["datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json"]["class"] == "adapter_manifest"
    assert reg["results/run_ledger.jsonl"]["class"] == "ledger"
    assert reg["tests/"]["class"] == "suite"
    assert all(v["class"] in OL.ARTIFACT_CLASSES for v in reg.values())


def test_registry_covers_every_ledger_artifact():
    reg = AR.build_registry(REPO)
    rows = OL.read_rows(os.path.join(REPO, "results", "outcome_ledger.jsonl"))
    assert rows, "committed ledger must exist"
    assert AR.unregistered(rows, reg) == []
    z = AR.classify("riemann-zero-lab/results/agent_runs/zeta-eval-20260613", reg)
    assert z and z["class"] == "agent" and z.get("record")
    assert AR.classify("nowhere/nothing.txt", reg) is None


def test_check_ledger_cli():
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "artifact_registry.py"), "--check-ledger"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ARTIFACT REGISTRY: OK" in r.stdout
