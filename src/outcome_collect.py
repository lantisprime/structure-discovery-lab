#!/usr/bin/env python3
"""Outcome collector (R0-S2). Runs every defect-signal source the lab already
has, turns each verdict into an outcome-ledger row, and appends the rows
through src/outcome_ledger.py (dedup by state). Never edits an instrument:
every source is wrapped, and the --verify entry points keep their no-write
contract.

    python3 src/outcome_collect.py --all [--gate] [--ledger PATH] [--dry-run]
    python3 src/outcome_collect.py --sources agent_eval,design_verifier

Sources: agent_eval, design_verifier, ledger_integrity, verify_entrypoint,
pytest, replay. Alias `fast` = the first three (seconds); `verify_entrypoint`,
`pytest` and `replay` take minutes.

replay (R4 full): every derived artefact declared in REPLAY_TARGETS is
regenerated in a temporary detached worktree at HEAD and byte-compared with
the committed version (PASS identical / FAIL drifted / ERROR script failed).
The working tree is never modified; src/replay_check.py is the same check for
one artefact in any checkout (bisection, healer gate, R3 gate).

--gate: exit 1 iff a NEW defect row was appended (its state key was absent
from the ledger before this run). Known open defects stay visible and do not
fail the gate; a later stage closes them.
"""

import argparse
import datetime as _dt
import getpass
import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import outcome_ledger as OL  # noqa: E402

PY = sys.executable

AGENT_FOR_PREFIX = {"V": "independent-verifier", "D": "data-reader",
                    "A": "structure-analyst", "O": "theorem-dataset-onboarder",
                    "R": "research-scout", "E": "docs-web-editor",
                    "Q": "equation-analyst", "X": "lab-orchestrator",
                    "P": "lab-proposer"}

VERIFY_ENTRYPOINTS = [
    ("src/pcso_monitoring_run.py",
     ["--manifest", "datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json", "--verify"]),
    ("src/csi_popularity.py", ["--verify"]),
    ("src/pcso_strategy_backtest.py", ["--verify"]),
    ("src/pcso_next_draw_posterior.py", ["--verify"]),
    ("src/pcso_weekly_update.py", ["--verify"]),
]

PYTEST_SUITES = [
    ("tests/", ["tests/"]),
    ("webapp/test_server.py+test_routing.py", ["webapp/test_server.py", "webapp/test_routing.py"]),
    ("riemann-zero-lab/tests", ["riemann-zero-lab/tests"]),
]

# Regenerable derived artefacts: (script, args, outputs). The single declaration
# behind the `replay` source (what to regenerate), the attributor's check
# command and the healer's / R3 gate's scope exemption (what a repair may
# overwrite under results/). Everything else under results/ stays immutable.
REPLAY_TARGETS = [
    ("src/meta_uniformity.py", [], ["results/meta_uniformity.json"]),
]
REPLAY_CHECK = "src/replay_check.py"

SUBPROCESS_TIMEOUT = 900


def replay_outputs(artifact):
    """Declared regenerable outputs of an artefact ([] when it declares none)."""
    return [o for script, _args, outs in REPLAY_TARGETS if script == artifact for o in outs]


# ---------------------------------------------------------------- context --

def now_ts():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(root, *args):
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def head_commit(root):
    return git(root, "rev-parse", "--short", "HEAD") or "unknown"


def executor_id():
    if os.environ.get("LAB_EXECUTOR"):
        return os.environ["LAB_EXECUTOR"]
    if os.environ.get("GITHUB_RUN_ID"):
        return f"github-actions:{os.environ['GITHUB_RUN_ID']}"
    try:
        user = getpass.getuser()
    except Exception:
        user = "unknown"
    return f"{user}@{socket.gethostname()}"


class Ctx:
    def __init__(self, root, prior_rows):
        self.root = root
        self.prior_rows = prior_rows
        self.commit = head_commit(root)
        self.executor = executor_id()

    def row(self, source, artifact, artifact_class, signal, evidence, detail):
        return OL.make_row(source, artifact, artifact_class, signal, evidence, detail,
                           now_ts(), self.commit, self.executor)


def run_cmd(root, argv):
    p = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)
    return p.returncode, p.stdout, p.stderr


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_agent_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def git_blob_sha256(root, commit, rel):
    """sha256 of <commit>:<rel> via git show; None when unavailable (shallow
    clone, path absent at that commit, no git)."""
    try:
        p = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=root,
                           capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return sha256_bytes(p.stdout) if p.returncode == 0 else None


def is_shallow(root):
    """A shallow clone (CI default) grafts history onto HEAD, so `git log`
    would attribute every record to HEAD and `git show HEAD:agents/x.md` would
    equal the working tree even when the definition changed -- staleness would
    be silently masked. Treat history as unavailable instead."""
    return git(root, "rev-parse", "--is-shallow-repository") == "true"


def record_commit(root, run_dir_rel):
    if is_shallow(root):
        return None
    out = git(root, "log", "--diff-filter=A", "--format=%h", "--", run_dir_rel)
    if not out:
        return None
    return out.splitlines()[-1]


# ---------------------------------------------------------------- sources --

def load_grader(root):
    spec = importlib.util.spec_from_file_location(
        "grade_agent_eval", os.path.join(root, "src", "grade_agent_eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DEFINITION_HASH_RE = re.compile(r"definition sha256: ([0-9a-f]{64})")


def record_definition_hash(run_dir):
    """The definition hash the R2 dispatcher wrote into the record's agent.txt
    (None for the 2026-06 records, which carry only an identity stamp)."""
    p = os.path.join(run_dir, "agent.txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        m = DEFINITION_HASH_RE.search(fh.read())
    return m.group(1) if m else None


def prior_at_eval_hash(ctx, artifact, subject):
    for r in reversed(ctx.prior_rows):
        if (r["source"] == "agent_eval" and r["artifact"] == artifact
                and r["detail"].get("subject") == subject
                and r["detail"].get("agent_sha256_at_eval")):
            return r["detail"]["agent_sha256_at_eval"]
    return None


def source_agent_eval(ctx):
    g = load_grader(ctx.root)
    rows = []
    # latest dated record per eval (a re-dispatch supersedes the 2026-06 floor)
    for eval_id, rel in g.record_dirs(ctx.root).items():
        prefix = eval_id.split("-")[0]
        agent = AGENT_FOR_PREFIX.get(prefix)
        artifact = f"agents/{agent}.md" if agent else rel
        run_dir = os.path.join(ctx.root, rel)
        detail = {"subject": eval_id, "record": rel}
        if not os.path.isdir(run_dir):
            rows.append(ctx.row("agent_eval", artifact, "agent", "INCOMPLETE_RECORD",
                                f"{eval_id}: NO_RECORD {rel}", detail))
            continue
        try:
            res = g.grade_one(eval_id, run_dir)
        except Exception as e:  # one bad record must not hide the others
            rows.append(ctx.row("agent_eval", artifact, "agent", "ERROR",
                                f"{eval_id}: grader raised {type(e).__name__}: {e}", detail))
            continue
        signal = res.get("grade") if res.get("grade") in OL.SIGNALS else "ERROR"
        detail.update({"checks": res.get("checks", {}),
                       "recorded_grade": res.get("recorded_grade")})
        if agent:
            agent_path = os.path.join(ctx.root, artifact)
            now_h = sha256_bytes(read_agent_bytes(agent_path)) if os.path.exists(agent_path) else None
            rc = record_commit(ctx.root, rel)
            at_eval = git_blob_sha256(ctx.root, rc, artifact) if rc else None
            fallback = False
            if at_eval is None:
                # a record not yet committed (dispatched this cycle, R2): the
                # dispatcher stamped the definition hash into its agent.txt
                at_eval = record_definition_hash(run_dir)
            if at_eval is None:
                at_eval = prior_at_eval_hash(ctx, artifact, eval_id)
                fallback = at_eval is not None
            detail.update({"agent_sha256_now": now_h, "agent_sha256_at_eval": at_eval,
                           "record_commit": rc, "at_eval_from_prior_row": fallback})
        rows.append(ctx.row("agent_eval", artifact, "agent", signal,
                            f"{eval_id}: {signal} (recorded {res.get('recorded_grade')}) {rel}", detail))
        if agent:
            rows.extend(stale_rows(ctx, artifact, eval_id, detail))
    return rows


def stale_rows(ctx, artifact, eval_id, detail):
    now_h, at_eval = detail.get("agent_sha256_now"), detail.get("agent_sha256_at_eval")
    sdetail = {"subject": f"{eval_id}:staleness", "agent_sha256_now": now_h,
               "agent_sha256_at_eval": at_eval, "record_commit": detail.get("record_commit")}
    if now_h is None or at_eval is None:
        return [ctx.row("agent_eval", artifact, "agent", "INCOMPLETE_RECORD",
                        f"{eval_id}: cannot compare definition with its eval record "
                        f"(now={bool(now_h)}, at_eval={bool(at_eval)})", sdetail)]
    if now_h != at_eval:
        return [ctx.row("agent_eval", artifact, "agent", "STALE_EVAL",
                        f"{eval_id}: {artifact} changed since eval record commit "
                        f"{detail.get('record_commit')}; no eval pass, no dispatch", sdetail)]
    # In sync. A staleness slot that was last seen as a defect is closed with a
    # PASS row (a fresh record re-dispatched for the changed definition); an
    # untouched slot stays silent, as before.
    prior = [r for r in ctx.prior_rows if OL.slot(r) == ("agent_eval", artifact, sdetail["subject"])]
    if prior and prior[-1]["severity"] == "defect":
        return [ctx.row("agent_eval", artifact, "agent", "PASS",
                        f"{eval_id}: {artifact} matches its eval record again "
                        f"({detail.get('record_commit')})", sdetail)]
    return []


DESIGN_RE = re.compile(r"design verifier: (PASS|FAIL)(.*)")


def source_design_verifier(ctx):
    rc, out, err = run_cmd(ctx.root, [PY, "src/design_verifier.py"])
    m = DESIGN_RE.search(out)
    artifact, cls = "results/multiplicity_ledger.jsonl", "design"
    if not m:
        return [ctx.row("design_verifier", artifact, cls, "ERROR",
                        f"no verdict line (exit {rc})", {"exit": rc})]
    signal = m.group(1)
    if (signal == "PASS") != (rc == 0):
        return [ctx.row("design_verifier", artifact, cls, "ERROR",
                        f"verdict {signal} contradicts exit {rc}", {"exit": rc})]
    violations = [l.strip() for l in out.splitlines() if l.strip().startswith("VIOLATION:")]
    return [ctx.row("design_verifier", artifact, cls, signal, m.group(0).strip(),
                    {"exit": rc, "violations": violations})]


LEDGER_RE = re.compile(r"LEDGER INTEGRITY: (OK|FAIL)")
COUNTS_RE = re.compile(r"(\d+) pass \S+ (\d+) warn \S+ (\d+) fail")


def source_ledger_integrity(ctx):
    rc, out, err = run_cmd(ctx.root, [PY, "src/verify_ledger_integrity.py", "--quiet"])
    artifact, cls = "results/run_ledger.jsonl", "ledger"
    m = LEDGER_RE.search(out)
    if not m:
        return [ctx.row("ledger_integrity", artifact, cls, "ERROR",
                        f"no verdict line (exit {rc})", {"exit": rc})]
    c = COUNTS_RE.search(out)
    counts = {"pass": int(c.group(1)), "warn": int(c.group(2)), "fail": int(c.group(3))} if c else {}
    if m.group(1) == "FAIL" or rc != 0:
        signal = "FAIL"
    elif counts.get("warn", 0) > 0:
        signal = "WARN"
    else:
        signal = "PASS"
    return [ctx.row("ledger_integrity", artifact, cls, signal, m.group(0), {"exit": rc, **counts})]


VERIFY_PASS_RE = re.compile(r"^PASS sha256=([0-9a-f]{64})", re.M)


def parse_verify_output(stdout, rc, stderr=""):
    """(signal, sha256, evidence) for a --verify entry point. When the script
    dies with an uncaught exception there is no PASS/FAIL line on stdout, so
    the evidence falls back to the last non-empty stderr line (the exception
    message), never to a bare exit code when something better exists."""
    m = VERIFY_PASS_RE.search(stdout)
    first = next((l for l in stdout.splitlines() if l.startswith(("PASS", "FAIL"))), "")
    last_err = next((l.strip() for l in reversed(stderr.splitlines()) if l.strip()), "")
    if m and rc == 0:
        return "PASS", m.group(1), first[:OL.EVIDENCE_MAX]
    if m and rc != 0:
        return "ERROR", m.group(1), f"PASS line but exit {rc}"
    if rc != 0:
        return "FAIL", None, (first or last_err or f"exit {rc}")[:OL.EVIDENCE_MAX]
    return "ERROR", None, "exit 0 without a PASS sha256 line"


def source_verify_entrypoint(ctx):
    rows = []
    for script, args in VERIFY_ENTRYPOINTS:
        try:
            rc, out, err = run_cmd(ctx.root, [PY, script, *args])
        except Exception as e:  # one hung/broken script must not hide the others
            rows.append(ctx.row("verify_entrypoint", script, "instrument", "ERROR",
                                f"{type(e).__name__}: {e}"[:OL.EVIDENCE_MAX], {"args": args}))
            continue
        signal, sha, evidence = parse_verify_output(out, rc, err)
        # subject = platform: byte-identity of a result is a per-platform
        # observation (the Ubuntu CI run first showed this), so each platform
        # is its own slot and macOS/Linux never overwrite each other's state.
        rows.append(ctx.row("verify_entrypoint", script, "instrument", signal, evidence,
                            {"subject": sys.platform, "exit": rc, "sha256": sha, "args": args}))
    return rows


def parse_pytest_summary(stdout):
    last = [l for l in stdout.splitlines() if "passed" in l or "failed" in l or "error" in l]
    line = last[-1] if last else ""
    passed = re.search(r"(\d+) passed", line)
    failed = re.search(r"(\d+) failed", line)
    errors = re.search(r"(\d+) error", line)
    return {"passed": int(passed.group(1)) if passed else 0,
            "failed": int(failed.group(1)) if failed else 0,
            "errors": int(errors.group(1)) if errors else 0}


def source_pytest(ctx):
    rows = []
    for name, paths in PYTEST_SUITES:
        try:
            rc, out, err = run_cmd(ctx.root, [PY, "-m", "pytest", *paths, "-q"])
        except Exception as e:
            rows.append(ctx.row("pytest", name, "suite", "ERROR",
                                f"{type(e).__name__}: {e}"[:OL.EVIDENCE_MAX], {}))
            continue
        s = parse_pytest_summary(out)
        signal = "PASS" if rc == 0 else "FAIL"
        rows.append(ctx.row("pytest", name, "suite", signal,
                            f"{s['passed']} passed, {s['failed']} failed, {s['errors']} errors (exit {rc})",
                            {"subject": sys.platform, "exit": rc, **s}))
    return rows


class DetachedWorktree:
    """Temporary detached git worktree at a commit; removed on exit."""

    def __init__(self, root, commit="HEAD"):
        self.root, self.commit = root, commit
        self.path = tempfile.mkdtemp(prefix="lab-replay-")

    def __enter__(self):
        os.rmdir(self.path)
        p = subprocess.run(["git", "worktree", "add", "--detach", "--quiet", self.path, self.commit],
                           cwd=self.root, capture_output=True, text=True, timeout=300)
        if p.returncode != 0:
            raise RuntimeError(f"worktree add failed: {p.stderr.strip()[-200:]}")
        return self.path

    def __exit__(self, *exc):
        git(self.root, "worktree", "remove", "--force", self.path)
        git(self.root, "worktree", "prune")


def source_replay(ctx):
    """One row per declared script: regenerate in a detached worktree at HEAD
    (the committed bytes are what the worktree holds before the run) and
    compare every declared output with what the script wrote."""
    import replay_check as RC
    rows = []
    for script, args, outputs in REPLAY_TARGETS:
        detail = {"subject": sys.platform, "args": list(args)}
        try:
            with DetachedWorktree(ctx.root) as wt:
                res = RC.replay(wt, script, args, outputs, timeout=SUBPROCESS_TIMEOUT)
        except Exception as e:  # one broken target must not hide the others
            rows.append(ctx.row("replay", script, "instrument", "ERROR",
                                f"{type(e).__name__}: {e}"[:OL.EVIDENCE_MAX], detail))
            continue
        detail.update({"exit": res["exit"], "outputs": res["outputs"]})
        rows.append(ctx.row("replay", script, "instrument", res["signal"], res["evidence"][:OL.EVIDENCE_MAX], detail))
    return rows


SOURCES = {"agent_eval": source_agent_eval,
           "design_verifier": source_design_verifier,
           "ledger_integrity": source_ledger_integrity,
           "verify_entrypoint": source_verify_entrypoint,
           "pytest": source_pytest,
           "replay": source_replay}
FAST = ("agent_eval", "design_verifier", "ledger_integrity")


# ---------------------------------------------------------------- driver --

def collect(names, root, prior_rows, registry=None):
    """Rows for the named sources. A source that raises yields one ERROR row
    from the collector itself instead of silence."""
    registry = registry or SOURCES
    ctx = Ctx(root, prior_rows)
    rows = []
    for name in names:
        fn = registry.get(name)
        if fn is None:
            rows.append(ctx.row("collector", "src/outcome_collect.py", "collector", "ERROR",
                                f"unknown source {name!r}", {"subject": name}))
            continue
        try:
            rows.extend(fn(ctx))
        except Exception as e:
            rows.append(ctx.row("collector", "src/outcome_collect.py", "collector", "ERROR",
                                f"source {name} raised {type(e).__name__}: {e}"[:OL.EVIDENCE_MAX],
                                {"subject": name, "trace": traceback.format_exc()[-1500:]}))
    return rows


def run(names, ledger, root=ROOT, gate=False, dry_run=False, registry=None, out=sys.stdout):
    """Collect, append, report. Returns (appended_rows, new_defects)."""
    prior = OL.read_rows(ledger)
    # "known" = the state each slot was in immediately before this run, not
    # every state ever seen: a defect that was closed and reappears is NEW.
    known = set(OL.latest_keys(prior).values())
    rows = collect(names, root, prior, registry)
    for r in rows:
        print(f"{r['signal']:17s} {r['source']:17s} {r['artifact']}  {r['evidence']}", file=out)
    appended = [] if dry_run else OL.append_rows(ledger, rows)
    if dry_run:
        appended_preview = [r for r in rows if OL.state_key(r) not in known]
        new_defects = [r for r in appended_preview if r["severity"] == "defect"]
        print(f"dry-run: {len(rows)} rows collected; {len(appended_preview)} would be appended; "
              f"{len(new_defects)} new defect(s)", file=out)
        return [], new_defects
    new_defects = [r for r in appended if r["severity"] == "defect" and OL.state_key(r) not in known]
    print(f"appended {len(appended)} of {len(rows)} rows to {ledger}; "
          f"{len(new_defects)} new defect(s)" + (" -- GATE FAIL" if gate and new_defects else ""), file=out)
    return appended, new_defects


def adopt(ledger, artifact_ledger, out=sys.stdout):
    """Merge rows observed elsewhere (a CI artifact ledger) into `ledger`.
    Dedup applies, so only genuinely new states land; their executor field
    keeps naming the CI run that observed them."""
    rows = OL.read_rows(artifact_ledger)
    problems = OL.verify_ledger(artifact_ledger)
    if problems:
        print("refusing to adopt an invalid ledger:", *problems, sep="\n  ", file=out)
        return None
    # Adopt each slot's LATEST state in the artifact, never its history: a CI
    # artifact is seeded from a committed ledger and replaying older states
    # would append stale FAIL/PASS transitions here.
    latest = {}
    for r in rows:
        latest[OL.slot(r)] = r
    rows = list(latest.values())
    # `ts` is the time a row entered THIS ledger (monotonic per file, REQ-1);
    # the observing run is still named by `executor`, and the state key does
    # not include ts, so re-stamping changes nothing the gate looks at.
    stamp = now_ts()
    for r in rows:
        r["ts"] = stamp
    appended = OL.append_rows(ledger, rows)
    for r in appended:
        print(f"adopted {r['signal']:17s} {r['source']:17s} {r['artifact']}  {r['evidence']}  [{r['executor']}]", file=out)
    print(f"adopted {len(appended)} of {len(rows)} rows from {artifact_ledger} into {ledger}", file=out)
    return appended


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", default="", help="comma list; alias fast")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--adopt", default=None, metavar="ARTIFACT_LEDGER",
                    help="merge rows from another ledger (e.g. a CI artifact) and exit")
    a = ap.parse_args(argv)
    if a.adopt:
        ledger = OL.ledger_path(a.ledger)
        if OL.verify_ledger(ledger):
            print("refusing to append to an invalid ledger")
            return 2
        return 0 if adopt(ledger, a.adopt) is not None else 2
    if a.all:
        names = list(SOURCES)
    else:
        names = [n for n in a.sources.split(",") if n]
        if "fast" in names:
            names = [n for n in names if n != "fast"] + list(FAST)
    if not names:
        ap.print_usage()
        return 2
    ledger = OL.ledger_path(a.ledger)
    problems = OL.verify_ledger(ledger)
    if problems:
        print("refusing to append to an invalid ledger:", *problems, sep="\n  ")
        return 2
    _, new_defects = run(names, ledger, gate=a.gate, dry_run=a.dry_run)
    return 1 if (a.gate and new_defects) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
