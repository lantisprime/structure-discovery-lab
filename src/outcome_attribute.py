#!/usr/bin/env python3
"""Outcome attribution (R1-S2): for each defect row in the outcome ledger,
find the commit that introduced it and append one `attribution` row.

    python3 src/outcome_attribute.py --new       # open defects only (check.sh / CI; no-op when none)
    python3 src/outcome_attribute.py --replay    # every defect row lacking an attribution, closed or open
    python3 src/outcome_attribute.py --dry-run   # with either: print, append nothing

Methods:
    path_history         STALE_EVAL: first commit after the eval record's commit that changed the definition
    bisect               instrument / suite / design / ledger defects: re-run the check in a temporary git
                         worktree at probe commits between last_good and the defect's commit (binary search,
                         first-parent); a merge commit is refined into the merged branch's introducing commit.
                         A `replay` drift is probed with the lab's src/replay_check.py (absolute path) against
                         the probe commit's artefact, so the answer is the commit that changed an input
                         without regenerating, even before the checker existed
    not_reproducible_here  the check passes at the defect's commit on this platform (e.g. a Linux-only failure
                         attributed from macOS) -- the platform is named, no commit is guessed
    commit_unavailable   the defect's commit (e.g. a CI merge ref) is not in this clone
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402
import outcome_collect as OC  # noqa: E402
import artifact_registry as AR  # noqa: E402

PY = sys.executable
PROBE_TIMEOUT = 900


# ------------------------------------------------------------------ git ----

def git(root, *args, check=False):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=120)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip() if p.returncode == 0 else None


def resolve(root, ref):
    return git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")


def artifact_paths(artifact):
    """Git paths behind a ledger artifact: a suite name such as
    'webapp/test_server.py+test_routing.py' maps to its files."""
    suites = dict(OC.PYTEST_SUITES)
    return list(suites[artifact]) if artifact in suites else [artifact]


def creation_commit(root, rel):
    """Oldest commit that added any path behind the artifact."""
    best = None
    for p in artifact_paths(rel):
        out = git(root, "log", "--diff-filter=A", "--format=%H %ct", "--", p)
        if not out:
            continue
        sha, ct = out.splitlines()[-1].split()
        if best is None or int(ct) < best[1]:
            best = (sha, int(ct))
    return best[0] if best else None


def rev_range(root, good, bad, first_parent=True):
    args = ["rev-list", "--reverse"] + (["--first-parent"] if first_parent else []) + [f"{good}..{bad}"]
    out = git(root, *args)
    return out.splitlines() if out else []


class Worktree:
    def __init__(self, root, commit):
        self.root, self.commit = root, commit
        self.path = tempfile.mkdtemp(prefix="lab-probe-")

    def __enter__(self):
        os.rmdir(self.path)
        git(self.root, "worktree", "add", "--detach", "--quiet", self.path, self.commit, check=True)
        return self.path

    def __exit__(self, *exc):
        git(self.root, "worktree", "remove", "--force", self.path)
        git(self.root, "worktree", "prune")


# --------------------------------------------------------------- checks ----

def check_command(row):
    """argv (relative to a checkout) that reproduces the defect row's check."""
    src, artifact, detail = row["source"], row["artifact"], row["detail"]
    if src == "verify_entrypoint":
        return [PY, artifact, *detail.get("args", ["--verify"])]
    if src == "pytest":
        paths = dict(OC.PYTEST_SUITES).get(artifact)
        return [PY, "-m", "pytest", *paths, "-q"] if paths else None
    if src == "design_verifier":
        return [PY, "src/design_verifier.py"]
    if src == "ledger_integrity":
        return [PY, "src/verify_ledger_integrity.py", "--quiet"]
    if src == "replay":
        outputs = detail.get("outputs") or OC.replay_outputs(artifact)
        outputs = list(outputs.keys()) if isinstance(outputs, dict) else list(outputs)
        if not outputs:
            return None
        # The checker is the lab's own, by absolute path: the check runs in any
        # checkout (a probe worktree at a commit before the checker existed, the
        # healer's worktree, the R3 gate's), always against that checkout's artefact.
        return [PY, os.path.join(OC.ROOT, OC.REPLAY_CHECK), artifact, "--outputs", *outputs,
                "--args", *detail.get("args", [])]
    return None


def run_check_at(root, commit, argv):
    """'PASS' | 'FAIL' | 'ERROR' for argv run inside a worktree at commit."""
    with Worktree(root, commit) as wt:
        artifact = argv[2] if argv[1].endswith(OC.REPLAY_CHECK) else argv[1]
        if not os.path.exists(os.path.join(wt, artifact)) and not artifact.startswith("-"):
            return "ERROR"  # the artifact does not exist at this commit
        try:
            p = subprocess.run(argv, cwd=wt, capture_output=True, text=True, timeout=PROBE_TIMEOUT)
        except subprocess.TimeoutExpired:
            return "ERROR"
    return "PASS" if p.returncode == 0 else "FAIL"


def bisect(commits, probe):
    """First commit in `commits` (oldest..newest, assumed monotonic) for which
    probe(commit) != 'PASS'. An ERROR probe (worktree hiccup, timeout, artifact
    absent) is retried once; a persistent ERROR is recorded as skipped and
    treated as not-PASS, so the answer can only be conservative (no later than
    the true commit) and is flagged `ambiguous` when it rests on a skipped
    probe. Returns (commit or None, steps, skipped)."""
    steps, skipped, lo, hi, first_bad = [], [], 0, len(commits) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        t0 = time.time()
        res = probe(commits[mid])
        if res == "ERROR":
            res = probe(commits[mid])
            if res == "ERROR":
                skipped.append(commits[mid][:7])
        steps.append({"commit": commits[mid][:7], "result": res, "seconds": round(time.time() - t0, 1)})
        if res == "PASS":
            lo = mid + 1
        else:
            first_bad, hi = commits[mid], mid - 1
    return first_bad, steps, skipped


# ------------------------------------------------------------ attribute ----

def last_good_commit(rows, defect):
    """Commit of the latest PASS row for the defect's slot before the defect."""
    slot = OL.slot(defect)
    good = None
    for r in rows:
        if r is defect:
            break
        if OL.slot(r) == slot and r["signal"] == "PASS":
            good = r["commit"]
    return good


def attribute_stale_eval(root, defect):
    rec = defect["detail"].get("record_commit")
    artifact = defect["artifact"]
    if rec and resolve(root, rec):
        out = git(root, "log", "--format=%H", f"{rec}..HEAD", "--", artifact)
        commits = out.splitlines() if out else []
        introduced = commits[-1] if commits else None
        return {"method": "path_history", "introduced_by": introduced and introduced[:7],
                "last_good": rec, "steps": [{"changes_since_record": len(commits)}]}
    out = git(root, "log", "-1", "--format=%H", "--", artifact)
    return {"method": "path_history", "introduced_by": out and out[:7], "last_good": None,
            "steps": [{"note": "record commit unavailable; latest change to the definition"}]}


def attribute_by_bisect(root, rows, defect, probe=None):
    argv = check_command(defect)
    if argv is None:
        return {"method": "no_check", "introduced_by": None, "last_good": None, "steps": []}
    bad = resolve(root, defect["commit"])
    if bad is None:
        return {"method": "commit_unavailable", "introduced_by": None, "last_good": None,
                "steps": [{"note": f"{defect['commit']} is not in this clone (CI merge ref?)"}]}
    probe = probe or (lambda c: run_check_at(root, c, argv))
    t0 = time.time()
    at_bad = probe(bad)
    steps = [{"commit": bad[:7], "result": at_bad, "seconds": round(time.time() - t0, 1)}]
    if at_bad == "PASS":
        return {"method": "not_reproducible_here", "introduced_by": None, "last_good": None, "steps": steps}
    good = last_good_commit(rows, defect)
    good = resolve(root, good) if good else None
    if good is None:
        good = creation_commit(root, defect["artifact"])
    if good is None:
        return {"method": "bisect", "introduced_by": None, "last_good": None,
                "steps": steps + [{"note": "no last-good bound: artifact never PASSed and has no creation commit"}]}
    commits = rev_range(root, good, bad)
    first_bad, more, skipped = bisect(commits, probe)
    steps += more
    if first_bad is None:  # everything after good passes?? then the bad commit itself
        first_bad = bad
    merged_by = None
    if git(root, "rev-parse", "--verify", "--quiet", f"{first_bad}^2"):
        merged_by = first_bad
        inner = rev_range(root, f"{first_bad}^1", f"{first_bad}^2", first_parent=False)
        refined, more, skipped2 = bisect(inner, probe)
        steps += more
        skipped += skipped2
        if refined:
            first_bad = refined
    out = {"method": "bisect", "introduced_by": first_bad[:7], "last_good": good[:7], "steps": steps}
    if merged_by:
        out["merged_by"] = merged_by[:7]
    if skipped:
        out["skipped"] = skipped
        out["ambiguous"] = first_bad[:7] in skipped
    return out


def attribute(root, rows, defect, probe=None):
    if defect["signal"] == "STALE_EVAL":
        return attribute_stale_eval(root, defect)
    return attribute_by_bisect(root, rows, defect, probe)


# --------------------------------------------------------------- driver ----

def attributed_keys(rows):
    """(defect_key, defect_commit) pairs already attributed. Keyed per
    OCCURRENCE, not per state: the same failure recurring at a later commit
    (a regression after a fix) is a new defect with its own introducing commit."""
    return {(r["detail"].get("defect_key"), r["detail"].get("defect_commit"))
            for r in rows if r["source"] == "attribution"}


def open_defects(rows):
    """Defect rows that are the latest state of their slot (still open),
    whether or not they have been attributed or healed."""
    latest = {}
    for r in rows:
        if r["source"] in ("attribution", "heal"):
            continue
        latest[OL.slot(r)] = r
    return [r for r in latest.values() if r["severity"] == "defect"]


def unattributed(rows, replay=False):
    done = attributed_keys(rows)
    pool = [r for r in rows if r["severity"] == "defect"] if replay else open_defects(rows)
    return [r for r in pool if ("|".join(OL.state_key(r)), r["commit"]) not in done]


def attribution_row(ctx, defect, result, registry):
    entry = AR.classify(defect["artifact"], registry) or {"class": defect["artifact_class"]}
    key = "|".join(OL.state_key(defect))
    intro = result.get("introduced_by")
    evidence = (f"introduced_by {intro} ({result['method']}, {len(result['steps'])} step(s))"
                if intro else f"{result['method']} ({len(result['steps'])} step(s))")
    evidence += f" for {defect['signal']} {defect['source']} {defect['artifact']} [{defect['detail'].get('subject', '')}]"
    detail = {"subject": defect["detail"].get("subject", ""), "defect_key": key,
              "defect_commit": defect["commit"], "platform": sys.platform, **result}
    return ctx.row("attribution", defect["artifact"], entry["class"], "ATTRIBUTED",
                   evidence[:OL.EVIDENCE_MAX], detail)


def run(ledger, root=ROOT, replay=False, dry_run=False, probe=None, out=sys.stdout):
    rows = OL.read_rows(ledger)
    todo = unattributed(rows, replay)
    if not todo:
        print("attribution: no unattributed defects", file=out)
        return []
    registry = AR.build_registry(root)
    ctx = OC.Ctx(root, rows)
    new_rows = []
    for d in todo:
        res = attribute(root, rows, d, probe)
        r = attribution_row(ctx, d, res, registry)
        print(f"{r['signal']:17s} {r['source']:17s} {r['artifact']}  {r['evidence']}", file=out)
        new_rows.append(r)
    appended = [] if dry_run else OL.append_rows(ledger, new_rows)
    print(f"attribution: {len(new_rows)} defect(s) attributed; "
          f"{'dry-run, nothing appended' if dry_run else f'{len(appended)} row(s) appended to {ledger}'}", file=out)
    return appended if not dry_run else new_rows


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new", action="store_true")
    g.add_argument("--replay", action="store_true")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    ledger = OL.ledger_path(a.ledger)
    if OL.verify_ledger(ledger):
        print("refusing to append to an invalid ledger")
        return 2
    run(ledger, replay=a.replay, dry_run=a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
