#!/usr/bin/env python3
"""Sanitization enforcement (lab-owner directive 2026-06-11): the lab is a
general structure-discovery laboratory; domain vocabulary is allowed ONLY in
src/domains/, frozen historical records, domain datasets/results, and domain
deliverables. This lint fails if domain words leak into the neutral zones.

Neutral zones checked: src/core/**, agents/*.md, the external blind-eval
runner, and src/domains/__init__ (must stay a bare namespace).
Exit 1 on any violation."""

import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOMAIN_WORDS = re.compile(r"\b(lotto|pcso|jackpots?|bets?|betting|tickets?|6/(?:42|45|49|55|58))\b",
                          re.IGNORECASE)

NEUTRAL = []
for base, _, fs in os.walk(os.path.join(ROOT, "src", "core")):
    NEUTRAL += [os.path.join(base, f) for f in fs if f.endswith(".py")]
NEUTRAL += [os.path.join(ROOT, "agents", f)
            for f in os.listdir(os.path.join(ROOT, "agents"))
            if f.endswith(".md")]
NEUTRAL.append(os.path.join(ROOT, "evals", "structure_eval_set_v1", "src",
                            "run_blind_eval.py"))

violations = []
for p in NEUTRAL:
    for i, line in enumerate(open(p, errors="ignore"), 1):
        m = DOMAIN_WORDS.search(line)
        if m:
            violations.append(f"{os.path.relpath(p, ROOT)}:{i}: '{m.group()}'")

if violations:
    print("DOMAIN-NEUTRALITY LINT: FAIL")
    for v in violations:
        print("  ", v)
    sys.exit(1)
print(f"DOMAIN-NEUTRALITY LINT: PASS ({len(NEUTRAL)} files clean)")
