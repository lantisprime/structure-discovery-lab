#!/usr/bin/env python3
"""Eval-set rerun r2 (2026-07-02) — CLAUDE.md trigger after the audit
remediation (AUDIT_RESOLUTION_2026-07-02.md): methodology changed (core
infrastructure rewritten, corrected instruments introduced), so the blind
eval battery is re-executed BEFORE the next verdict-bearing publication.

Two modes, neither touches the frozen Jun-11 artifact (results/blind_eval.json):

  regression : the registered battery EXACTLY as run on 2026-06-11 (same
               seed 20260611, same instruments) -> results/blind_eval_r2.json.
               Purpose: prove the core/stats rewrite and ledger work changed
               nothing (p-for-p match against the frozen artifact).
  corrected  : same battery, but the two CCA stages use the audit M-3
               standardized CCA (train-moment z-scoring before whitening)
               -> results/blind_eval_r2_corrected.json. Same seed, so any
               difference is attributable to the fix alone.

Usage: run_blind_eval_r2.py <regression|corrected> <stage> [stage...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(LAB, "src"))

import run_blind_eval as rb  # noqa: E402

mode = sys.argv[1]
assert mode in ("regression", "corrected"), mode
rb.OUT = os.path.join(LAB, "results",
                      "blind_eval_r2.json" if mode == "regression"
                      else "blind_eval_r2_corrected.json")

if mode == "corrected":
    # audit M-3: standardized ridge CCA replaces the unit-sensitive one in
    # the two CCA stages; everything else identical.
    from corrected_reruns import ridge_cca_heldout_std
    rb.ridge_cca_heldout = ridge_cca_heldout_std

sys.argv = [sys.argv[0]] + sys.argv[2:]
rb.main()
