#!/usr/bin/env python3
"""Repository-isolated behavioral tests for git_stage_commit.py."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "git_stage_commit", HERE / "git_stage_commit.py"
)
tool = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tool)

BREAK_STALE = "--break-stale-guard" in sys.argv
if BREAK_STALE:
    sys.argv.remove("--break-stale-guard")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


class GitRepoCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Closeout Test")
        git(self.root, "config", "user.email", "closeout@example.invalid")
        (self.root / "docs").mkdir()
        (self.root / "results").mkdir()
        (self.root / "datasets").mkdir()
        (self.root / "docs" / "base.md").write_text("base\n")
        (self.root / "results" / "base.json").write_text("{}\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")

    def tearDown(self):
        self.temporary.cleanup()

    def change(self, path: str, value: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)

    def test_preview_lists_states_and_token(self):
        clean = tool.changed_snapshot(self.root)
        self.assertEqual(clean["changes"], [])
        self.assertRegex(clean["token"], r"^[0-9a-f]{64}$")
        self.change("docs/base.md", "tracked sentinel\n")
        self.change("datasets/new.csv", "untracked sentinel\n")
        dirty = tool.changed_snapshot(self.root)
        rows = {row["path"]: row for row in dirty["changes"]}
        self.assertTrue(rows["docs/base.md"]["unstaged"])
        self.assertTrue(rows["datasets/new.csv"]["untracked"])
        self.assertNotEqual(clean["token"], dirty["token"])

    def test_commit_only_selected_paths(self):
        self.change("docs/base.md", "approved tracked sentinel\n")
        self.change("datasets/-selected file.csv", "approved new sentinel\n")
        self.change("results/unapproved.json", '{"unapproved":true}\n')
        snap = tool.changed_snapshot(self.root)
        result = tool.commit_selected(
            self.root,
            "commit selected sentinels",
            ["docs/base.md", "datasets/-selected file.csv"],
            snap["token"],
        )
        names = set(
            git(self.root, "show", "--pretty=", "--name-only", "HEAD").splitlines()
        )
        self.assertEqual(names, {"docs/base.md", "datasets/-selected file.csv"})
        self.assertEqual(
            result["paths"], ["datasets/-selected file.csv", "docs/base.md"]
        )
        self.assertIn(
            "results/unapproved.json", git(self.root, "status", "--porcelain")
        )

    def test_deletion_is_committed_when_selected(self):
        (self.root / "docs" / "base.md").unlink()
        snap = tool.changed_snapshot(self.root)
        tool.commit_selected(
            self.root,
            "commit selected deletion",
            ["docs/base.md"],
            snap["token"],
        )
        self.assertFalse((self.root / "docs" / "base.md").exists())
        self.assertEqual(
            git(self.root, "show", "--pretty=", "--name-status", "HEAD"),
            "D\tdocs/base.md",
        )

    def test_rejects_stale_preview(self):
        self.change("docs/base.md", "previewed sentinel\n")
        snap = tool.changed_snapshot(self.root)
        self.change("docs/base.md", "changed after preview sentinel\n")
        if BREAK_STALE:
            original_snapshot = tool.changed_snapshot
            original_index = tool._index_oid
            tool.changed_snapshot = lambda root: snap
            tool._index_oid = lambda root, path: snap["changes"][0]["worktree_oid"]
        try:
            with self.assertRaisesRegex(tool.CloseoutError, "preview is stale"):
                tool.commit_selected(
                    self.root,
                    "reject stale preview",
                    ["docs/base.md"],
                    snap["token"],
                )
        finally:
            if BREAK_STALE:
                tool.changed_snapshot = original_snapshot
                tool._index_oid = original_index

    def test_rejects_cross_repo_token(self):
        self.change("docs/base.md", "repo A sentinel\n")
        token_a = tool.changed_snapshot(self.root)["token"]
        with tempfile.TemporaryDirectory() as other_dir:
            other = Path(other_dir)
            git(other, "init", "-q")
            git(other, "config", "user.name", "Other Repo")
            git(other, "config", "user.email", "other@example.invalid")
            (other / "docs").mkdir()
            (other / "docs" / "base.md").write_text("other base\n")
            git(other, "add", "-A")
            git(other, "commit", "-qm", "base")
            (other / "docs" / "base.md").write_text("repo B sentinel\n")
            with self.assertRaisesRegex(tool.CloseoutError, "preview is stale"):
                tool.commit_selected(
                    other,
                    "reject repo splice",
                    ["docs/base.md"],
                    token_a,
                )

    def test_rejects_empty_duplicate_and_nonstring_paths(self):
        for value in (
            [],
            ["docs/base.md", "docs/base.md"],
            [7],
            "docs/base.md",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(tool.CloseoutError, "1-200 unique"):
                    tool._validated_paths(value)

    def test_rejects_traversal_and_disallowed_roots(self):
        bad = [
            "../secret",
            "/tmp/secret",
            "docs\\secret",
            ".git/config",
            ".DS_Store",
            ".claude/config.json",
            " webapp/server.py",
        ]
        for path in bad:
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    tool.CloseoutError, "approved lab artifact|1-200"
                ):
                    tool._normalize_path(path)

    def test_symlink_hashes_link_text_not_external_target(self):
        outside = self.root.parent / f"{self.root.name}-outside-sentinel"
        outside.write_text("external secret version one")
        link = self.root / "docs" / "external-link.md"
        os.symlink(outside, link)
        try:
            first = tool.changed_snapshot(self.root)
            row = next(
                item for item in first["changes"]
                if item["path"] == "docs/external-link.md"
            )
            expected = subprocess.check_output(
                ["git", "hash-object", "--stdin"],
                cwd=self.root,
                input=os.fsencode(os.readlink(link)),
            ).decode().strip()
            self.assertEqual(row["worktree_oid"], expected)
            outside.write_text("external secret version two")
            second = tool.changed_snapshot(self.root)
            self.assertEqual(first["token"], second["token"])
            tool.commit_selected(
                self.root,
                "commit symlink object only",
                ["docs/external-link.md"],
                second["token"],
            )
            stored = subprocess.check_output(
                ["git", "cat-file", "-p", "HEAD:docs/external-link.md"],
                cwd=self.root,
            )
            self.assertEqual(stored, os.fsencode(os.readlink(link)))
        finally:
            outside.unlink(missing_ok=True)

    def test_rejects_path_count_boundary(self):
        allowed = [f"docs/path-{index}.md" for index in range(200)]
        self.assertEqual(len(tool._validated_paths(allowed)), 200)
        with self.assertRaisesRegex(tool.CloseoutError, "1-200 unique"):
            tool._validated_paths(allowed + ["docs/path-200.md"])

    def test_rejects_pre_staged_unapproved(self):
        self.change("docs/base.md", "approved sentinel\n")
        self.change("results/base.json", '{"staged":"unapproved"}\n')
        git(self.root, "add", "results/base.json")
        snap = tool.changed_snapshot(self.root)
        with self.assertRaisesRegex(
            tool.CloseoutError, "unapproved paths are already staged"
        ):
            tool.commit_selected(
                self.root,
                "reject staged rider",
                ["docs/base.md"],
                snap["token"],
            )

    def test_detects_change_between_preview_and_stage(self):
        self.change("docs/base.md", "previewed race sentinel\n")
        snap = tool.changed_snapshot(self.root)
        original_git = tool._git
        changed = False

        def racing_git(root, *args, **kwargs):
            nonlocal changed
            if not changed and args[:3] == ("add", "-A", "--"):
                changed = True
                self.change("docs/base.md", "raced sentinel\n")
            return original_git(root, *args, **kwargs)

        with mock.patch.object(tool, "_git", side_effect=racing_git):
            with self.assertRaisesRegex(tool.CloseoutError, "changed during staging"):
                tool.commit_selected(
                    self.root,
                    "reject staging race",
                    ["docs/base.md"],
                    snap["token"],
                )
        self.assertEqual(git(self.root, "log", "-1", "--pretty=%s"), "base")

    def test_commit_message_is_literal_argument(self):
        self.change("docs/base.md", "message sentinel\n")
        snap = tool.changed_snapshot(self.root)
        for bad in ("1234", "x" * 401):
            with self.subTest(length=len(bad)):
                with self.assertRaisesRegex(tool.CloseoutError, "5-400"):
                    tool.commit_selected(
                        self.root,
                        bad,
                        ["docs/base.md"],
                        snap["token"],
                    )
        tool.commit_selected(
            self.root,
            "12345",
            ["docs/base.md"],
            snap["token"],
        )
        self.assertEqual(git(self.root, "log", "-1", "--pretty=%s"), "12345")
        self.change("docs/base.md", "400-character message sentinel\n")
        snap = tool.changed_snapshot(self.root)
        tool.commit_selected(
            self.root,
            "x" * 400,
            ["docs/base.md"],
            snap["token"],
        )
        self.assertEqual(
            git(self.root, "log", "-1", "--pretty=%s"), "x" * 400
        )
        self.change("docs/base.md", "literal message sentinel\n")
        snap = tool.changed_snapshot(self.root)
        message = "-literal $(touch SHOULD_NOT_EXIST) ; sentinel"
        tool.commit_selected(
            self.root,
            message,
            ["docs/base.md"],
            snap["token"],
        )
        self.assertEqual(git(self.root, "log", "-1", "--pretty=%s"), message)
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
