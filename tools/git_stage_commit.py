#!/usr/bin/env python3
"""Preview and commit exactly owner-selected lab paths without shell interpolation."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"[0-9a-f]{64}")
MAX_PATHS = 200
ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "CLAUDE.md",
    "PCSO_Lotto_Analysis_Mar-Jun_2026.xlsx",
    "README.md",
    "Start Lab Console.command",
    "admin_onboarding.html",
    "lotto_picker.html",
    "requirements.txt",
    "pyproject.toml",
    "uv.lock",
}
ROOT_DIRS = {
    ".github",
    "agents",
    "datasets",
    "docs",
    "evals",
    "results",
    "riemann-zero-lab",
    "src",
    "tools",
    "webapp",
}


class CloseoutError(ValueError):
    pass


def _git(
    root: Path,
    *args: str,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess:
    run = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=root,
        capture_output=True,
        check=False,
        input=input_bytes,
    )
    if check and run.returncode != 0:
        detail = run.stderr.decode("utf-8", "replace").strip()
        raise CloseoutError(detail or f"git {' '.join(args)} failed")
    return run


def _nul_paths(root: Path, *args: str) -> set[str]:
    output = _git(root, *args).stdout
    return {
        item.decode("utf-8", "surrogateescape")
        for item in output.split(b"\0")
        if item
    }


def _normalize_path(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise CloseoutError(
            "paths must be a list of 1-200 unique repository-relative strings"
        )
    if "\0" in value or "\\" in value:
        raise CloseoutError(f"path is not an approved lab artifact: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise CloseoutError(f"path is not an approved lab artifact: {value}")
    if len(path.parts) == 1:
        allowed = value in ROOT_FILES
    else:
        allowed = path.parts[0] in ROOT_DIRS
    if not allowed:
        raise CloseoutError(f"path is not an approved lab artifact: {value}")
    return value


def _index_oid(root: Path, path: str) -> str | None:
    run = _git(root, "rev-parse", "--verify", f":{path}", check=False)
    if run.returncode != 0:
        return None
    return run.stdout.decode().strip()


def _worktree_oid(root: Path, path: str) -> str | None:
    target = root / path
    if not target.exists() and not target.is_symlink():
        return None
    if target.is_symlink():
        return _git(
            root,
            "hash-object",
            "--stdin",
            input_bytes=os.fsencode(os.readlink(target)),
        ).stdout.decode().strip()
    return _git(
        root,
        "hash-object",
        "--no-filters",
        "--",
        path,
    ).stdout.decode().strip()


def changed_snapshot(root: Path = ROOT) -> dict[str, object]:
    root = Path(
        _git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()
    ).resolve()
    head = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    unstaged = _nul_paths(
        root, "diff", "--name-only", "--no-renames", "-z", "--"
    )
    staged = _nul_paths(
        root, "diff", "--cached", "--name-only", "--no-renames", "-z", "--"
    )
    untracked = _nul_paths(
        root, "ls-files", "--others", "--exclude-standard", "-z", "--"
    )
    changes = []
    for path in sorted(unstaged | staged | untracked):
        rejection = None
        try:
            _normalize_path(path)
        except CloseoutError as exc:
            rejection = str(exc)
        changes.append(
            {
                "path": path,
                "staged": path in staged,
                "unstaged": path in unstaged,
                "untracked": path in untracked,
                "worktree_oid": _worktree_oid(root, path),
                "index_oid": _index_oid(root, path),
                "allowed": rejection is None,
                "rejection": rejection,
            }
        )
    body = {"root": str(root), "head": head, "changes": changes}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "token": hashlib.sha256(encoded).hexdigest()}


def _validated_paths(paths: object) -> list[str]:
    if not isinstance(paths, list) or not 1 <= len(paths) <= MAX_PATHS:
        raise CloseoutError(
            "paths must be a list of 1-200 unique repository-relative strings"
        )
    normalized = [_normalize_path(path) for path in paths]
    if len(set(normalized)) != len(normalized):
        raise CloseoutError(
            "paths must be a list of 1-200 unique repository-relative strings"
        )
    return normalized


def commit_selected(
    root: Path,
    message: str,
    paths: object,
    preview_token: str,
) -> dict[str, object]:
    if not isinstance(message, str) or not 5 <= len(message.strip()) <= 400:
        raise CloseoutError("commit message: 5-400 characters")
    selected = _validated_paths(paths)
    if not isinstance(preview_token, str) or not TOKEN_RE.fullmatch(preview_token):
        raise CloseoutError("closeout preview token is missing or malformed")
    snapshot = changed_snapshot(root)
    if not hmac.compare_digest(snapshot["token"], preview_token):
        raise CloseoutError("closeout preview is stale; refresh paths before committing")
    records = {item["path"]: item for item in snapshot["changes"]}
    for path in selected:
        if path not in records:
            raise CloseoutError(f"path is not currently changed: {path}")
        if not records[path]["allowed"]:
            raise CloseoutError(records[path]["rejection"])
    staged_before = {path for path, row in records.items() if row["staged"]}
    outside = sorted(staged_before - set(selected))
    if outside:
        raise CloseoutError(
            f"unapproved paths are already staged: {', '.join(outside)}"
        )
    _git(root, "add", "-A", "--", *selected)
    staged_after = _nul_paths(
        root,
        "diff",
        "--cached",
        "--name-only",
        "--no-renames",
        "-z",
        "--",
    )
    if staged_after != set(selected):
        raise CloseoutError("staged path set differs from approved selection")
    for path in selected:
        if _index_oid(root, path) != records[path]["worktree_oid"]:
            raise CloseoutError(f"selected path changed during staging: {path}")
    _git(root, "commit", "-m", message.strip())
    commit = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    return {"commit": commit, "paths": sorted(selected)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-json", action="store_true")
    parser.add_argument("--message")
    parser.add_argument("--paths-json")
    parser.add_argument("--preview-token")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_json:
        print(json.dumps(changed_snapshot(ROOT), sort_keys=True))
        return
    try:
        paths = json.loads(args.paths_json) if args.paths_json is not None else None
        result = commit_selected(ROOT, args.message, paths, args.preview_token)
    except (CloseoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"closeout blocked: {exc}") from exc
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
