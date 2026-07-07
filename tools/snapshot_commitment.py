#!/usr/bin/env python3
"""Append a commitment snapshot to results/commitment_ledger.txt.

The commitment ledger is the lab's in-sandbox commitment device: SHA-256
(16-hex prefix) of every doc/script/dataset file, hashed BEFORE run scripts
execute (THEOREM_GOVERNANCE). Historically each snapshot was assembled by
hand; this tool makes it one command — strictly APPEND-ONLY, existing lines
are never rewritten.

Usage (from repo root):
    python3 tools/snapshot_commitment.py "Registration EQ_TIDAL_V4"
    python3 tools/snapshot_commitment.py "label" --dry-run   # print, don't append

What gets hashed: everything except VCS/venv/archive/cache dirs, results/
(hash outputs individually in run rows instead), and machine-local secrets
(webapp/.keysalt, webapp/config.local.json — keys must never enter the
ledger). The snapshot only appends rows whose (path, hash) pair changed
since the previous snapshot, so repeated snapshots stay small.
"""
import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
LEDGER = os.path.join(ROOT, "results", "commitment_ledger.txt")

SKIP_DIRS = {".git", ".venv", "archive", "__pycache__", ".pytest_cache",
             ".episodic-memory", "results", "joblogs", "node_modules"}
SKIP_FILES = {".keysalt", "config.local.json", ".DS_Store"}


def tree_hashes():
    rows = {}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f in SKIP_FILES:
                continue
            p = os.path.join(base, f)
            rel = "./" + os.path.relpath(p, ROOT)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
            rows[rel] = h
    return rows


def previous_hashes():
    """Last recorded hash per path across ALL prior snapshots (later rows
    supersede earlier ones)."""
    prev = {}
    if not os.path.exists(LEDGER):
        return prev
    for line in open(LEDGER):
        line = line.strip()
        if not line or line.startswith("#") or "[SEALED]" in line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and len(parts[0]) == 16:
            path = parts[1].strip()
            if not path.startswith("./"):
                path = "./" + path.lstrip("/")
            prev[path] = parts[0]
    return prev


def main():
    ap = argparse.ArgumentParser(
        description="Append a commitment snapshot (append-only).")
    ap.add_argument("label", help="what this snapshot commits, e.g. "
                                  "'Registration EQ_TIDAL_V4'")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the snapshot instead of appending")
    ap.add_argument("--full", action="store_true",
                    help="record every file, not just changes since the "
                         "previous snapshot")
    args = ap.parse_args()

    if not os.path.exists(LEDGER):
        sys.exit("results/commitment_ledger.txt not found — run from the "
                 "repo root (or run install.py first).")

    current = tree_hashes()
    prev = previous_hashes()
    changed = (current if args.full else
               {p: h for p, h in current.items() if prev.get(p) != h})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Hash-chain: each snapshot commits to the ENTIRE ledger state that
    # preceded it, so any retroactive edit to earlier lines breaks every
    # later snapshot's chain (verified by src/verify_ledger_integrity.py).
    if not args.dry_run:
        with open(LEDGER, "rb+") as f:
            raw = f.read()
            if raw and not raw.endswith(b"\n"):
                f.write(b"\n")
    chain_prev = hashlib.sha256(open(LEDGER, "rb").read()).hexdigest()

    header = (f"# Snapshot {now} — {args.label}\n"
              f"# chain-prev: {chain_prev}\n"
              f"# ({len(changed)} changed of {len(current)} tracked files; "
              "hashed BEFORE any run script executes)\n")
    body = "".join(f"{h}  {p}\n" for p, h in sorted(changed.items()))

    if args.dry_run:
        sys.stdout.write(header + body)
        print(f"# --dry-run: nothing appended ({len(changed)} rows)")
        return
    with open(LEDGER, "a") as f:
        f.write(header + body)
    anchor = hashlib.sha256(open(LEDGER, "rb").read()).hexdigest()
    print(f"appended snapshot '{args.label}': {len(changed)} rows "
          f"({len(current)} files tracked) -> results/commitment_ledger.txt")
    print(f"ledger digest after append (anchor this in your git commit "
          f"message/tag):\n  {anchor}")


if __name__ == "__main__":
    main()
