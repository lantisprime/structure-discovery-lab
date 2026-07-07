#!/usr/bin/env python3
"""Mechanical integrity verifier for the lab's four-level ledger system.

Complements the existing verifiers (design_verifier, verify_relational_docs,
lint_frozen_imports) with the one thing none of them check: that the ledgers
themselves are internally consistent and still match the artifacts on disk.

Checks (FAIL = integrity violation, exit 1; WARN = informational drift):
  run ledger          every row parses; run_ids unique; required fields
                      present; referenced scripts exist; recorded
                      output_sha256 hashes match the files on disk
  multiplicity ledger every row parses; row_type valid; test rows carry the
                      schema-v2 fields with sane values (raw_p in [0,1],
                      p_floor consistent with m_perm); run_ids cross-
                      reference the run ledger
  commitment ledger   append-only text format intact (16-hex + path rows)
  admission log       recognizable instrument-admission lines
  riemann sub-ledger  riemann-zero-lab/results/run_ledger.jsonl parses,
                      unique run_ids

Run:  python3 src/verify_ledger_integrity.py            (from repo root)
      python3 src/verify_ledger_integrity.py --quiet    (summary only)
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RESULTS = os.path.join(ROOT, "results")

FAILS, WARNS, PASSES = [], [], []
QUIET = "--quiet" in sys.argv


def ok(msg):
    PASSES.append(msg)
    if not QUIET:
        print(f"  PASS  {msg}")


def warn(msg):
    WARNS.append(msg)
    print(f"  WARN  {msg}")


def fail(msg):
    FAILS.append(msg)
    print(f"  FAIL  {msg}")


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load_jsonl(path):
    rows, bad = [], 0
    for i, line in enumerate(open(path), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append((i, json.loads(line)))
        except json.JSONDecodeError:
            bad += 1
            fail(f"{os.path.relpath(path, ROOT)}:{i} is not valid JSON")
    return rows, bad


# ------------------------------------------------------------- run ledger
def check_run_ledger():
    path = os.path.join(RESULTS, "run_ledger.jsonl")
    if not os.path.exists(path):
        fail("results/run_ledger.jsonl missing")
        return set()
    rows, _ = load_jsonl(path)
    if not rows:
        ok("run ledger: present, empty (fresh install)")
        return set()
    ids = [r.get("run_id") for _, r in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        fail(f"run ledger: duplicate run_ids {sorted(dupes)} "
             "(append-only invariant violated)")
    else:
        ok(f"run ledger: {len(rows)} rows, run_ids unique")

    missing_fields = 0
    missing_scripts, missing_outputs, sha_mismatch, sha_checked = [], [], [], 0
    for ln, r in rows:
        for fld in ("run_id", "date", "script", "output"):
            if fld not in r:
                missing_fields += 1
                fail(f"run ledger:{ln} missing required field '{fld}'")
        # script may be compound: "src/a.py + _b.py (annotation)" — bare
        # filenames are siblings of the first full path in the row
        script = re.sub(r"\([^)]*\)", "", r.get("script", "")).strip()
        parts = [s.strip() for s in script.split("+") if s.strip()]
        base_dir = os.path.dirname(parts[0]) if parts else ""
        for s in parts:
            cand = s if "/" in s else os.path.join(base_dir, s)
            if not os.path.exists(os.path.join(ROOT, cand)):
                missing_scripts.append(f"{r.get('run_id')}: {s}")
        shas = r.get("output_sha256") or {}
        for rel, recorded in shas.items():
            p = os.path.join(ROOT, rel)
            if recorded is None:
                continue
            if not os.path.exists(p):
                missing_outputs.append(f"{r.get('run_id')}: {rel}")
                continue
            sha_checked += 1
            actual = sha16(p)
            if actual != recorded:
                sha_mismatch.append(f"{r.get('run_id')}: {rel} "
                                    f"recorded {recorded} != disk {actual}")
    if missing_scripts:
        warn(f"run ledger: {len(missing_scripts)} referenced scripts absent "
             f"({'; '.join(missing_scripts[:3])} …)")
    else:
        ok("run ledger: every referenced script exists")
    if missing_outputs:
        warn(f"run ledger: {len(missing_outputs)} recorded outputs absent "
             f"from results/ ({'; '.join(missing_outputs[:3])} …)")
    if sha_mismatch:
        for m in sha_mismatch:
            fail(f"run ledger: output hash mismatch — {m}")
    elif sha_checked:
        ok(f"run ledger: all {sha_checked} recorded output sha256s match disk")
    return set(ids)


# ---------------------------------------------------- multiplicity ledger
def check_multiplicity(run_ids):
    path = os.path.join(RESULTS, "multiplicity_ledger.jsonl")
    if not os.path.exists(path):
        fail("results/multiplicity_ledger.jsonl missing")
        return
    rows, _ = load_jsonl(path)
    if not rows:
        ok("multiplicity ledger: present, empty (fresh install)")
        return
    tests = [(ln, r) for ln, r in rows if r.get("row_type") == "test"]
    charges = [(ln, r) for ln, r in rows
               if r.get("row_type") == "family_charge"]
    other = len(rows) - len(tests) - len(charges)
    if other:
        fail(f"multiplicity ledger: {other} rows with unknown row_type "
             "(schema v2 expects 'test' | 'family_charge')")
    else:
        ok(f"multiplicity ledger: {len(tests)} test rows + "
           f"{len(charges)} family-charge rows, all schema-v2 typed")

    bad_p, bad_floor, unknown_runs, gate_rows = [], [], set(), 0
    for ln, r in tests:
        p = r.get("raw_p")
        if p is None:
            # gate-based rows (equation confirmations) carry no p-value —
            # legitimate per the audit G-5 reconciliation note
            gate_rows += 1
            if not (r.get("gate_based") or
                    "equation" in str(r.get("claim_type", ""))):
                bad_p.append(ln)
        elif not (isinstance(p, (int, float)) and 0 <= p <= 1):
            bad_p.append(ln)
        m_perm, floor = r.get("m_perm"), r.get("p_floor")
        if isinstance(m_perm, int) and m_perm > 0 and \
                isinstance(floor, (int, float)):
            expected = 1.0 / (m_perm + 1)
            if abs(floor - expected) > max(0.005, expected * 0.5):
                bad_floor.append(f"line {ln}: p_floor {floor} vs "
                                 f"1/(m_perm+1)={expected:.4f}")
        rid = r.get("run_id")
        if rid and run_ids and rid not in run_ids:
            unknown_runs.add(rid)
    if bad_p:
        fail(f"multiplicity ledger: raw_p invalid on lines {bad_p[:5]} "
             "(must be in [0,1], or null only on gate-based rows)")
    else:
        ok("multiplicity ledger: every test raw_p in [0,1]"
           + (f" ({gate_rows} gate-based rows without p, as registered)"
              if gate_rows else ""))
    if bad_floor:
        warn(f"multiplicity ledger: {len(bad_floor)} p_floor values "
             f"inconsistent with m_perm ({bad_floor[0]} …)")
    else:
        ok("multiplicity ledger: p_floor consistent with m_perm everywhere")
    if unknown_runs:
        warn("multiplicity ledger: run_ids not present in run ledger: "
             f"{sorted(unknown_runs)}")
    else:
        ok("multiplicity ledger: every test run_id exists in the run ledger")


# ------------------------------------------------------ commitment ledger
def check_commitment():
    path = os.path.join(RESULTS, "commitment_ledger.txt")
    if not os.path.exists(path):
        fail("results/commitment_ledger.txt missing")
        return
    n_rows = n_headers = 0
    bad = []
    # rows are '<sha16>  ./path'; the blind-eval commitment chain also uses
    # bare paths and '[SEALED] path' rows — all are legitimate
    row_re = re.compile(r"^[0-9a-f]{16}\s+(\[SEALED\]\s+)?\.?/?\S")
    for i, line in enumerate(open(path), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("#"):
            n_headers += 1
            continue
        if row_re.match(line):
            n_rows += 1
        else:
            bad.append(i)
    if bad:
        fail(f"commitment ledger: malformed rows at lines {bad[:5]} "
             "(expected '<sha256-16>  ./path')")
    else:
        ok(f"commitment ledger: {n_rows} hash rows, {n_headers} header/"
           "annotation lines, format intact")


# ----------------------------------------------------------- admission log
def check_admission():
    path = os.path.join(RESULTS, "admission_log.txt")
    if not os.path.exists(path):
        fail("results/admission_log.txt missing")
        return
    lines = [l.strip() for l in open(path) if l.strip()]
    if not lines:
        ok("admission log: present, empty (fresh install)")
        return
    pat = re.compile(r"^\w+.*:\s*\{.*\}\s*\(\d+(\.\d+)?s\)$")
    bad = [l for l in lines if not pat.match(l)]
    if bad:
        warn(f"admission log: {len(bad)} lines in unexpected format "
             f"(first: {bad[0][:70]!r})")
    else:
        ok(f"admission log: {len(lines)} instrument-admission lines, "
           "format intact")


# --------------------------------------------------------- riemann ledger
def check_riemann():
    path = os.path.join(ROOT, "riemann-zero-lab", "results",
                        "run_ledger.jsonl")
    if not os.path.exists(path):
        return  # module optional
    rows, _ = load_jsonl(path)
    ids = [r.get("run_id") for _, r in rows]
    if len(ids) != len(set(ids)):
        fail("riemann run ledger: duplicate run_ids")
    else:
        ok(f"riemann run ledger: {len(rows)} rows, run_ids unique")


def main():
    print("Ledger integrity verifier")
    print("=" * 60)
    run_ids = check_run_ledger()
    check_multiplicity(run_ids)
    check_commitment()
    check_admission()
    check_riemann()
    print("=" * 60)
    print(f"{len(PASSES)} pass · {len(WARNS)} warn · {len(FAILS)} fail")
    if FAILS:
        print("LEDGER INTEGRITY: FAIL")
        sys.exit(1)
    print("LEDGER INTEGRITY: OK" + (" (with warnings)" if WARNS else ""))


if __name__ == "__main__":
    main()
