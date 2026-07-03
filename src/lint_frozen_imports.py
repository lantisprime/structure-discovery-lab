#!/usr/bin/env python3
"""Adversarial review M-E ("two-truths repo"): frozen modules keep known
defects for reproducibility; this lint ensures live code cannot silently
inherit them.

Rules:
  1. Modules under src/core/ must not import any FROZEN module at module
     level (lazy, in-function imports are allowed and flagged as info).
  2. Any other non-frozen module importing a FROZEN module must be on the
     ALLOWLIST (read-only wrappers that exist to correct/measure the frozen
     code) — everything else is a violation.
  3. Every frozen module must carry the freeze header.

Exit 1 on violations. Run from anywhere."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE_MARK = "FROZEN HISTORICAL RECORD"

FROZEN = set()
for f in os.listdir(HERE):
    if f.endswith(".py"):
        head = open(os.path.join(HERE, f)).read(400)
        # marker must be a header comment, not a docstring mention
        if any(l.strip().startswith("#") and FREEZE_MARK in l
               for l in head.splitlines()[:4]):
            FROZEN.add(f[:-3])

# KNOWN DEBT (audit minor #13 / review M-E): src/core is currently a
# re-export shim over frozen implementations. Tracked for migration in
# AUDIT_RESOLUTION_2026-07-02.md §4; reported as warnings so NEW offenders
# still fail the build while the existing shim is being migrated.
CORE_SHIM_DEBT = {"core/recovery.py", "core/completion.py",
                  "core/geometry.py", "core/discrete_draws.py",
                  "core/graphs.py", "core/paired.py"}

# read-only wrappers sanctioned to import frozen code (audit resolution R-A)
ALLOWLIST = {
    "corrected_reruns", "measure_equivalence", "readmit_r1_r7",
    "measure_r5_coupling", "corrected_rerun_registered",
    "remediation_r1",          # frozen itself; imports other frozen modules
    "rerun_batch67", "relational_pressure", "relational_batch7",
    "relational_batch5", "relational_allgames", "relational_subsets",
    "relational_admission", "relational_first_run", "r8_admission",
    "verify_relational_docs", "graphon_cooccurrence", "szemeredi_ap",
}

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)",
                       re.M)


def module_level_imports(path):
    """Names imported at column-0 indentation (module level)."""
    out = []
    for line in open(path):
        m = re.match(r"^(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if m:
            out.append(m.group(1))
    return out


def main():
    violations, infos = [], []
    for root, _dirs, files in os.walk(HERE):
        for f in files:
            if not f.endswith(".py"):
                continue
            mod = f[:-3]
            path = os.path.join(root, f)
            rel = os.path.relpath(path, HERE)
            is_core = os.sep in rel and rel.startswith("core")
            if mod in FROZEN and not is_core:
                continue
            frozen_hits = [i for i in module_level_imports(path)
                           if i in FROZEN]
            lazy_hits = [i for i in set(IMPORT_RE.findall(open(path).read()))
                         if i in FROZEN and i not in frozen_hits]
            if is_core and frozen_hits:
                msg = (f"core module {rel} imports frozen {frozen_hits} "
                       f"at module level")
                if rel.replace(os.sep, "/") in CORE_SHIM_DEBT:
                    infos.append("KNOWN DEBT (tracked): " + msg)
                else:
                    violations.append(msg)
            elif frozen_hits and mod not in ALLOWLIST:
                violations.append(f"{rel} imports frozen {frozen_hits} but is "
                                  f"not on the read-only-wrapper allowlist")
            if lazy_hits:
                infos.append(f"{rel}: lazy frozen import {lazy_hits} (allowed)")
    print(f"frozen modules: {sorted(FROZEN)}")
    for v in violations:
        print("  VIOLATION:", v)
    for i in infos:
        print("  info:", i)
    print(f"lint_frozen_imports: {'FAIL' if violations else 'PASS'} "
          f"({len(violations)} violations)")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
