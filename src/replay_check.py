#!/usr/bin/env python3
"""Replay check (R4 full): does a script reproduce its committed derived
artefact byte for byte?

    python3 src/replay_check.py src/meta_uniformity.py --outputs results/meta_uniformity.json [--args ...]

Runs the script in this checkout, compares each declared output with the
bytes the checkout held before the run, then puts the bytes back: the
declared outputs are restored from memory, a tracked file the script
dirtied (a figure written as a side effect) is restored with git, an
untracked file it created is removed. Not covered: a file already dirty
before the run that the script also rewrote, and an untracked file the
script deleted. Exit 0 and `PASS sha256=<output sha>` when
every output is reproduced; exit 1 and `FAIL <output> committed <sha> regenerated
<sha>` on drift; exit 2 and `ERROR ...` when the script fails.

The comparison is against the checkout's own copy, not `git show HEAD:`, so
the same command is the check everywhere the loop runs it: bisection
(worktree at a probe commit), the healer's gate (the proposer's uncommitted
regeneration is the candidate) and the R3 gate (worktree at the PR head).
`src/outcome_collect.py` runs it in a detached worktree at HEAD for the
`replay` source, where the checkout's copy is the committed one.
"""

import argparse
import hashlib
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PY = sys.executable


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def read_bytes(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def git_status(root):
    p = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=root,
                       capture_output=True, timeout=60)
    if p.returncode != 0:
        return None
    # -z: NUL-separated, paths unquoted; a rename entry is followed by its source path
    entries, out = p.stdout.decode("utf-8", "surrogateescape").split("\0"), set()
    i = 0
    while i < len(entries):
        e = entries[i]
        if e:
            out.add(e[3:])
            if e[0] in "RC":
                i += 1                         # skip the rename source entry
        i += 1
    return out


def restore(root, outputs, before, dirty_before, dirty_after):
    """Declared outputs back from memory (their directory recreated if the run
    removed it); tracked files the run dirtied restored with git; untracked files
    it created removed. Out of reach, by design: a file that was already dirty
    before the run and that the script also rewrote keeps the post-run bytes,
    and an untracked file the script deleted is not brought back."""
    failed = []
    for rel, b in before.items():
        path = os.path.join(root, rel)
        try:
            if b is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "wb") as fh:
                    fh.write(b)
        except OSError as e:
            failed.append(f"{rel}: {e}")
    if dirty_before is None or dirty_after is None:
        return failed
    for rel in sorted(dirty_after - dirty_before - set(outputs)):
        path = os.path.join(root, rel)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel], cwd=root,
                                 capture_output=True, timeout=60).returncode == 0
        if tracked:
            subprocess.run(["git", "checkout", "--", rel], cwd=root, capture_output=True, timeout=60)
        elif os.path.isfile(path):
            os.remove(path)
    return failed


def replay(root, script, args, outputs, timeout=900):
    """{"signal": PASS|FAIL|ERROR, "evidence": str, "exit": int,
        "outputs": {rel: {"committed": sha, "regenerated": sha, "same": bool}}}"""
    before = {rel: read_bytes(os.path.join(root, rel)) for rel in outputs}
    dirty_before = git_status(root)
    try:
        p = subprocess.run([PY, script, *args], cwd=root, capture_output=True, text=True, timeout=timeout)
        rc, err = p.returncode, p.stderr
    except subprocess.TimeoutExpired:
        rc, err = 124, "timed out"
    after = {rel: read_bytes(os.path.join(root, rel)) for rel in outputs}
    failed = restore(root, outputs, before, dirty_before, git_status(root))
    if failed:
        return {"signal": "ERROR", "evidence": "restore failed: " + "; ".join(failed), "exit": rc, "outputs": {}}
    outs = {}
    for rel in outputs:
        b, a = before[rel], after[rel]
        outs[rel] = {"committed": sha256(b) if b is not None else None,
                     "regenerated": sha256(a) if a is not None else None,
                     "same": b is not None and a is not None and b == a}
    if rc != 0:
        last_err = next((l.strip() for l in reversed(err.splitlines()) if l.strip()), f"exit {rc}")
        return {"signal": "ERROR", "evidence": f"{script} exit {rc}: {last_err}", "exit": rc, "outputs": outs}
    missing = [rel for rel, o in outs.items() if o["regenerated"] is None or o["committed"] is None]
    if missing:
        return {"signal": "ERROR", "evidence": f"output missing before or after the run: {', '.join(missing)}",
                "exit": rc, "outputs": outs}
    drifted = [rel for rel, o in outs.items() if not o["same"]]
    if drifted:
        rel = drifted[0]
        return {"signal": "FAIL", "evidence": f"{rel} drifted: committed {outs[rel]['committed'][:8]}… "
                                              f"regenerated {outs[rel]['regenerated'][:8]}…"
                                              + (f" (+{len(drifted) - 1} more)" if len(drifted) > 1 else ""),
                "exit": rc, "outputs": outs}
    return {"signal": "PASS", "evidence": "PASS sha256=" + outs[outputs[0]]["committed"], "exit": rc, "outputs": outs}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--outputs", nargs="+", required=True)
    ap.add_argument("--args", nargs="*", default=[])
    ap.add_argument("--root", default=os.getcwd(), help="checkout to run in (default: cwd)")
    a = ap.parse_args(argv)
    res = replay(a.root, a.script, a.args, a.outputs)
    if res["signal"] == "PASS":
        print(res["evidence"])
        return 0
    for rel, o in res["outputs"].items():
        print(f"{rel}: committed {o['committed']} regenerated {o['regenerated']} same={o['same']}")
    print(("FAIL " if res["signal"] == "FAIL" else "ERROR ") + res["evidence"])
    return 1 if res["signal"] == "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
