#!/usr/bin/env python3
"""Regression tests for deterministic, non-mutating PCSO closeout verification."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pcso_weekly_update as pcso  # noqa: E402
sys.path.insert(0, str(ROOT / "webapp"))
import server  # noqa: E402

CANONICAL_RESULT_SHA256 = (
    "11c8af729f0353a83f130253100dadb5f"
    "b3413d49cceec11fa031d64daf054a4"
)

BREAK_BYTE = "--break-byte-compare" in sys.argv
BREAK_ATOMIC = "--break-atomic-write" in sys.argv
BREAK_JOB = "--break-job-definition" in sys.argv
BREAK_SHELL = "--break-shell-free" in sys.argv
for flag in (
    "--break-byte-compare",
    "--break-atomic-write",
    "--break-job-definition",
    "--break-shell-free",
):
    if flag in sys.argv:
        sys.argv.remove(flag)

if BREAK_BYTE:
    pcso.verify_existing_result = (
        lambda output, payload: hashlib.sha256(payload).hexdigest()
    )
if BREAK_ATOMIC:
    pcso.atomic_write = lambda output, payload: output.write_bytes(payload[:-1])
if BREAK_JOB:
    server.JOB_DEFS.pop("pcso_weekly_verify", None)
if BREAK_SHELL:
    _real_job_argv = server.job_argv

    def _broken_job_argv(name, params):
        result = _real_job_argv(name, params)
        if name == "git_commit":
            return ["sh", "-c", "git add -A && git commit"]
        return result

    server.job_argv = _broken_job_argv


class TestPCSOCloseout(unittest.TestCase):
    def test_result_bytes_matches_canonical_encoder(self):
        value = {"sentinel": "PCSO_BYTE_SENTINEL", "n": 7}
        observed = pcso.result_bytes(value)
        expected = (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()
        self.assertEqual(observed, expected)

    def test_verify_accepts_exact_bytes_without_mutation(self):
        payload = b'{"sentinel":"PCSO_VERIFY_SENTINEL"}\n'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            output.write_bytes(payload)
            before = output.stat().st_mtime_ns
            digest = pcso.verify_existing_result(output, payload)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
            self.assertEqual(output.read_bytes(), payload)
            self.assertEqual(output.stat().st_mtime_ns, before)

    def test_verify_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            output.write_bytes(b'{"actual":1}\n')
            with self.assertRaisesRegex(ValueError, "verification mismatch"):
                pcso.verify_existing_result(output, b'{"expected":1}\n')
            self.assertEqual(output.read_bytes(), b'{"actual":1}\n')

    def test_verify_rejects_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "missing.json"
            with self.assertRaisesRegex(ValueError, "verification output missing"):
                pcso.verify_existing_result(output, b"{}\n")
            self.assertFalse(output.exists())

    def test_atomic_write_replaces_complete_payload(self):
        payload = b'{"sentinel":"PCSO_ATOMIC_SENTINEL"}\n'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            output.write_bytes(b"old-complete-bytes\n")
            pcso.atomic_write(output, payload)
            self.assertEqual(output.read_bytes(), payload)
            self.assertEqual(list(Path(directory).glob(".result.json.tmp-*")), [])

    def test_atomic_write_cleans_temp_on_replace_failure(self):
        payload = b'{"sentinel":"PCSO_REPLACE_FAILURE_SENTINEL"}\n'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            output.write_bytes(b"old-complete-bytes\n")
            with mock.patch.object(os, "replace", side_effect=OSError("sentinel replace")):
                with self.assertRaisesRegex(OSError, "sentinel replace"):
                    pcso.atomic_write(output, payload)
            self.assertEqual(output.read_bytes(), b"old-complete-bytes\n")
            self.assertEqual(list(Path(directory).glob(".result.json.tmp-*")), [])

    def test_cli_verify_reproduces_canonical_hash_without_git_change(self):
        status_cmd = ["git", "status", "--porcelain=v1", "-z"]
        before = subprocess.check_output(status_cmd, cwd=ROOT)
        run = subprocess.run(
            [sys.executable, str(ROOT / "src" / "pcso_weekly_update.py"), "--verify"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        after = subprocess.check_output(status_cmd, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(f"PASS sha256={CANONICAL_RESULT_SHA256}", run.stdout)
        self.assertIn("wrote=none", run.stdout)
        evidence_line = next(
            line for line in run.stdout.splitlines()
            if line.startswith("VERIFY_EVIDENCE ")
        )
        evidence = json.loads(evidence_line.removeprefix("VERIFY_EVIDENCE "))
        self.assertEqual(evidence["command_argv"][-1], "--verify")
        self.assertEqual(evidence["output_sha256"], CANONICAL_RESULT_SHA256)
        self.assertTrue(evidence["input_sha256"])
        self.assertEqual(evidence["exit_status"], 0)
        self.assertTrue(evidence["git_status_unchanged"])
        self.assertEqual(
            evidence["git_status_before_sha256"],
            evidence["git_status_after_sha256"],
        )
        self.assertEqual(before, after)
        result = ROOT / "results" / "pcso_confirmation_2026-07-08.json"
        self.assertEqual(
            hashlib.sha256(result.read_bytes()).hexdigest(),
            CANONICAL_RESULT_SHA256,
        )


class TestPCSOJob(unittest.TestCase):
    def test_pcso_job_registered(self):
        definition = server.JOB_DEFS["pcso_weekly_verify"]
        self.assertEqual(definition["cat"], "gates")
        self.assertEqual(definition["label"], "Verify PCSO weekly batch")

    def test_pcso_job_argv_exact(self):
        observed = server.job_argv("pcso_weekly_verify", {})
        self.assertEqual(
            observed,
            [server.PY, "src/pcso_weekly_update.py", "--verify"],
        )


class TestCloseoutJob(unittest.TestCase):
    def valid(self):
        return {
            "message": "commit selected sentinel",
            "paths": ["docs/SENTINEL A.md", "datasets/SENTINEL-B.csv"],
            "preview_token": "a" * 64,
        }

    def test_git_commit_requires_message_paths_token(self):
        for params in (
            {},
            {"message": "valid message", "paths": []},
            {
                "message": "valid message",
                "paths": ["docs/x"],
                "preview_token": "bad",
            },
        ):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    server.job_argv("git_commit", params)

    def test_git_commit_argv_is_shell_free(self):
        observed = server.job_argv("git_commit", self.valid())
        self.assertEqual(observed[0], server.PY)
        self.assertEqual(observed[1], "tools/git_stage_commit.py")
        self.assertNotIn("sh", observed)
        self.assertNotIn("-c", observed)
        self.assertEqual(
            json.loads(observed[observed.index("--paths-json") + 1]),
            self.valid()["paths"],
        )
        self.assertEqual(
            observed[observed.index("--preview-token") + 1],
            "a" * 64,
        )


class TestCloseoutSnapshot(unittest.TestCase):
    def test_closeout_snapshot_shape(self):
        observed = server.closeout_snapshot()
        self.assertIsInstance(observed["changes"], list)
        self.assertRegex(observed["token"], r"^[0-9a-f]{64}$")
        console = (ROOT / "webapp" / "static" / "console.html").read_text()
        classic = (ROOT / "webapp" / "static" / "index.html").read_text()
        for body in (console, classic):
            self.assertIn("preview_token", body)
            self.assertIn("params.paths", body)
        for stdout in ("not-json", "[]", '{"changes":[],"token":null}'):
            with self.subTest(stdout=stdout):
                run = mock.Mock(returncode=0, stdout=stdout, stderr="")
                with mock.patch.object(server.subprocess, "run", return_value=run):
                    failed = server.closeout_snapshot()
                self.assertEqual(failed["changes"], [])
                self.assertIsNone(failed["token"])
                self.assertIn("invalid shape", failed["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
