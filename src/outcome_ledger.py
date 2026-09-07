#!/usr/bin/env python3
"""Outcome ledger (R0 of Milestone R, LAB_IMPROVEMENT_PLAN v1.3).

One append-only JSONL file, `results/outcome_ledger.jsonl` by default, that
every defect-signal source writes to through `src/outcome_collect.py`.
Schema v1 is documented in docs/plans/LAB_RSI_R0_IMPLEMENTATION_PLAN.md §8.1.

Library:
    validate_row(row)            -> None, raises ValueError naming the field
    state_key(row)               -> (source, artifact, signal, detail_hash)
    append_rows(path, rows)      -> rows actually appended (dedup by state key)
    verify_ledger(path)          -> list of problems (empty == OK)
    read_rows(path)              -> list of dict

CLI:
    python3 src/outcome_ledger.py --verify [--ledger PATH]   exit 0 OK / 1 bad

The ledger path can also be set with LAB_OUTCOME_LEDGER=<path>.
"""

import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAULT_LEDGER = os.path.join("results", "outcome_ledger.jsonl")

SCHEMA_VERSION = 1
SOURCES = ("agent_eval", "design_verifier", "ledger_integrity",
           "verify_entrypoint", "pytest", "collector",
           "attribution",            # R1: who/what introduced a defect
           "heal",                   # R4: a repair was proposed (PR) or rejected by the healer's own gate
           "gate")                   # R3: a proposal was merged, rejected, or routed to the owner
ARTIFACT_CLASSES = ("agent", "instrument", "ledger", "design", "suite", "collector",
                    "theorem_card", "adapter_manifest")
SIGNALS = ("PASS", "FAIL", "WARN", "INCOMPLETE_RECORD", "STALE_EVAL", "ERROR",
           "ATTRIBUTED",             # R1: info row naming introduced_by
           "PROPOSED", "REJECTED",   # R4: healer outcome for one defect (info; the defect row stays)
           "MERGED", "ROUTED")       # R3: gate outcome (REJECTED is shared); info, the defect row stays
DEFECT_SIGNALS = ("FAIL", "STALE_EVAL", "ERROR")
SEVERITIES = ("info", "defect")
EVIDENCE_MAX = 300
REQUIRED = ("schema_version", "ts", "source", "artifact", "artifact_class",
            "signal", "severity", "evidence", "detail", "commit", "executor")


def ledger_path(explicit=None):
    """Resolve the ledger path: explicit arg, then env, then the default."""
    p = explicit or os.environ.get("LAB_OUTCOME_LEDGER") or DEFAULT_LEDGER
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def severity_for(signal):
    return "defect" if signal in DEFECT_SIGNALS else "info"


# Provenance fields inside `detail` that describe HOW the observation was
# made, not WHAT was observed; they never make a row a new state.
NON_STATE_DETAIL_KEYS = frozenset({"record_commit", "at_eval_from_prior_row"})


def detail_hash(detail):
    state = {k: v for k, v in detail.items() if k not in NON_STATE_DETAIL_KEYS}
    canon = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def validate_row(row):
    if not isinstance(row, dict):
        raise ValueError("row: not an object")
    for k in REQUIRED:
        if k not in row:
            raise ValueError(f"{k}: missing")
    if row["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version: {row['schema_version']!r} != {SCHEMA_VERSION}")
    ts = row["ts"]
    if not (isinstance(ts, str) and len(ts) == 20 and ts.endswith("Z")
            and ts[4] == "-" and ts[7] == "-" and ts[10] == "T" and ts[13] == ":" and ts[16] == ":"):
        raise ValueError(f"ts: {ts!r} is not YYYY-MM-DDTHH:MM:SSZ")
    if row["source"] not in SOURCES:
        raise ValueError(f"source: {row['source']!r} not in {SOURCES}")
    if not isinstance(row["artifact"], str) or not row["artifact"]:
        raise ValueError("artifact: empty")
    if row["artifact_class"] not in ARTIFACT_CLASSES:
        raise ValueError(f"artifact_class: {row['artifact_class']!r} not in {ARTIFACT_CLASSES}")
    if row["signal"] not in SIGNALS:
        raise ValueError(f"signal: {row['signal']!r} not in {SIGNALS}")
    if row["severity"] not in SEVERITIES:
        raise ValueError(f"severity: {row['severity']!r} not in {SEVERITIES}")
    if row["severity"] != severity_for(row["signal"]):
        raise ValueError(f"severity: {row['severity']!r} inconsistent with signal {row['signal']!r}")
    ev = row["evidence"]
    if not isinstance(ev, str) or len(ev) > EVIDENCE_MAX:
        raise ValueError(f"evidence: not a string of <= {EVIDENCE_MAX} chars")
    if not isinstance(row["detail"], dict):
        raise ValueError("detail: not an object")
    if not isinstance(row["commit"], str) or not row["commit"]:
        raise ValueError("commit: empty")
    if not isinstance(row["executor"], str) or not row["executor"]:
        raise ValueError("executor: empty")


def make_row(source, artifact, artifact_class, signal, evidence, detail,
             ts, commit, executor):
    row = {"schema_version": SCHEMA_VERSION, "ts": ts, "source": source,
           "artifact": artifact, "artifact_class": artifact_class,
           "signal": signal, "severity": severity_for(signal),
           "evidence": evidence[:EVIDENCE_MAX], "detail": detail,
           "commit": commit, "executor": executor}
    validate_row(row)
    return row


def state_key(row):
    return (row["source"], row["artifact"], row["signal"], detail_hash(row["detail"]))


def read_rows(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "rb") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip(b"\n")
            if not line:
                continue
            try:
                rows.append(json.loads(line.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise ValueError(f"line {n}: not JSON ({e})")
    return rows


def slot(row):
    """Dedup slot: (source, artifact, detail.subject). `subject` lets one
    artifact carry several independent observations (e.g. evals V-1, V-2,
    V-3 of one agent definition) without thrashing each other."""
    return (row["source"], row["artifact"], str(row["detail"].get("subject", "")))


def latest_keys(rows):
    """Latest state key per slot, in ledger order."""
    latest = {}
    for r in rows:
        latest[slot(r)] = state_key(r)
    return latest


def append_rows(path, rows):
    """Append rows whose state differs from the latest row for the same
    (source, artifact). Full-file atomic replace: the new file begins with the
    prior bytes unchanged. Returns the rows actually appended."""
    for r in rows:
        validate_row(r)
    prior = b""
    if os.path.exists(path):
        with open(path, "rb") as fh:
            prior = fh.read()
    latest = latest_keys(read_rows(path))
    appended = []
    for r in rows:
        k = state_key(r)
        if latest.get(slot(r)) == k:
            continue
        latest[slot(r)] = k
        appended.append(r)
    if not appended:
        return []
    if prior and not prior.endswith(b"\n"):
        prior += b"\n"
    new = b"".join(json.dumps(r, sort_keys=True, ensure_ascii=True).encode("utf-8") + b"\n"
                   for r in appended)
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".outcome_ledger.", dir=d)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(prior + new)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return appended


def verify_ledger(path):
    problems = []
    try:
        rows = read_rows(path)
    except ValueError as e:
        return [str(e)]
    last_ts = ""
    for n, r in enumerate(rows, 1):
        try:
            validate_row(r)
        except ValueError as e:
            problems.append(f"row {n}: {e}")
            continue
        if r["ts"] < last_ts:
            problems.append(f"row {n}: ts {r['ts']} earlier than previous {last_ts}")
        last_ts = r["ts"]
    return problems


def main(argv):
    if "--verify" not in argv:
        print(__doc__)
        return 2
    path = None
    if "--ledger" in argv:
        path = argv[argv.index("--ledger") + 1]
    path = ledger_path(path)
    problems = verify_ledger(path)
    n = len(read_rows(path)) if not problems else "?"
    if problems:
        for p in problems:
            print("  FAIL ", p)
        print(f"OUTCOME LEDGER: FAIL ({len(problems)} problem(s)) {path}")
        return 1
    print(f"OUTCOME LEDGER: OK ({n} rows) {os.path.relpath(path, ROOT) if path.startswith(ROOT) else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
