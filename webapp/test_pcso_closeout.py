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

CANONICAL_RESULT_SHA256 = (
    "11c8af729f0353a83f130253100dadb5f"
    "b3413d49cceec11fa031d64daf054a4"
)

BREAK_BYTE = "--break-byte-compare" in sys.argv
BREAK_ATOMIC = "--break-atomic-write" in sys.argv
for flag in ("--break-byte-compare", "--break-atomic-write"):
    if flag in sys.argv:
        sys.argv.remove(flag)

if BREAK_BYTE:
    pcso.verify_existing_result = (
        lambda output, payload: hashlib.sha256(payload).hexdigest()
    )
if BREAK_ATOMIC:
    pcso.atomic_write = lambda output, payload: output.write_bytes(payload[:-1])


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
        self.assertEqual(before, after)
        result = ROOT / "results" / "pcso_confirmation_2026-07-08.json"
        self.assertEqual(
            hashlib.sha256(result.read_bytes()).hexdigest(),
            CANONICAL_RESULT_SHA256,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
