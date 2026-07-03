#!/usr/bin/env python3
"""Executor for docs/REGISTRATION_CORRECTED_RERUN.md.

GATE: refuses to run unless the registration is approved (approval line
filled) — the HUMAN-GATE is enforced in code, not prose.

Runs the three corrected instruments with the REGISTERED fresh seed
(20260711; the 2026-07-02 shadow used 20260702 — disclosed in §0), at the
registered m values. Two-run rule: invoke twice; JSONs must be
byte-identical. Output: results/corrected_rerun_r1.json
"""
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

REG = os.path.join(ROOT, "docs", "REGISTRATION_CORRECTED_RERUN.md")
OUT = os.path.join(ROOT, "results", "corrected_rerun_r1.json")
SEED = 20260711


def approval_gate():
    txt = open(REG).read()
    m = re.search(r"approved_by_human:\s*([^\s_].*?)\s{2,}|approved_by_human:\s*(\S[^\n]*)", txt)
    line = next((l for l in txt.splitlines() if "approved_by_human" in l), "")
    filled = line.split(":", 1)[1].strip().strip("_ ").replace("date", "")
    if not filled:
        raise SystemExit("HUMAN-GATE: registration not approved "
                         "(approved_by_human line is blank) — refusing to run")
    if "DRAFT — awaiting HUMAN-GATE approval" in txt:
        raise SystemExit("HUMAN-GATE: registration still marked DRAFT — "
                         "update the status line after approval")
    return filled


def main():
    who = approval_gate()
    import corrected_reruns as cr
    # registered seed and m values override the shadow-run constants
    cr.SEED = SEED
    res = {"_meta": {"registration": "docs/REGISTRATION_CORRECTED_RERUN.md",
                     "seed": SEED, "approved_by": who,
                     "prior_look": "audit_shadow_2026-07-02 (disclosed, §0)"}}
    res["presence_mc"] = cr.run_presence_mc_v2(m_null=399)
    res["cca_std"] = cr.run_cca_std_shadow()          # uses cr.SEED internally
    res["attribution_655_ex45"] = cr.attribute_v2("Grand Lotto 6/55", 45,
                                                  K=999)
    json.dump(res, open(OUT, "w"), indent=2)
    print("written", os.path.relpath(OUT, ROOT))
    print("REMINDERS: run twice (byte-identical); ledger the p's (row_type "
          "test, not exploratory); append run-ledger row corrected_rerun_r1; "
          "rerun design_verifier + verify_relational_docs + meta panel.")


if __name__ == "__main__":
    main()
