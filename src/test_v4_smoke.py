#!/usr/bin/env python3
"""Persisted smoke/validation tests for eq_selection_v4 (adversarial review
M4: these results were previously cited in AUDIT_RESOLUTION without an
artifact). Synthetic data only; writes results/v4_smoke.json.

Includes the independent reviewer's stronger checks: profile-CI coverage at
nominal level (200 reps) and residual-scan calibration under AR(1) H0."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import eq_selection_v4 as v4  # noqa: E402

SEED = 20260705
out = {}
rng = np.random.default_rng(SEED)
t = np.arange(300, dtype=float)
y = (2 * np.cos(2 * np.pi * t / 27.5) + 0.5 * np.cos(2 * np.pi * t / 31.8)
     + rng.normal(0, 1, 300))

# selection: pure held-out NLL, no complexity veto
recs = {"A": {"nll_val": 10.0, "complexity": 5},
        "B": {"nll_val": 9.8, "complexity": 19}}
out["select_family_pure_nll"] = v4.select_family(recs)
assert out["select_family_pure_nll"] == "B"

# adjudication + budget arithmetic (brute-force check of b_required)
a10 = v4.corrected_alpha(0.05, 10)
bb = v4.b_required(a10)
assert 1 / (bb + 1) <= a10 / 2 and 1 / bb > a10 / 2   # minimal B, exactly
out["alpha_m10"] = a10
out["b_required_m10"] = bb
out["adjudicate_v2B_B200"] = v4.adjudicate(0.009950248756218905, 0.05, 8, 200)
out["adjudicate_v2B_B399"] = v4.adjudicate(0.009950248756218905, 0.05, 8, 399)
assert out["adjudicate_v2B_B399"] == "FAIL_corrected"

# residual scan: detects planted line; silent after pre-whitening
r1 = v4.residual_scan_mc(t, y, [], rng, B=199)
r2 = v4.residual_scan_mc(t, y, [1 / 27.5, 1 / 31.8], rng, B=199)
out["scan_planted_line_p"] = r1["p"]
out["scan_prewhitened_p"] = r2["p"]
assert r1["p"] < 0.01 and r2["p"] > 0.05

# residual scan calibration under AR(1) H0 (reviewer's check)
def ar1(rng, n, phi=0.5):
    e = rng.normal(size=n); x = np.empty(n); x[0] = e[0]
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x
ps = [v4.residual_scan_mc(t, ar1(rng, 300), [], rng, B=99)["p"]
      for _ in range(100)]
out["scan_ar1_h0_frac_le_05"] = float(np.mean(np.array(ps) <= 0.05))
assert out["scan_ar1_h0_frac_le_05"] <= 0.08     # calibrated-to-conservative

# profile CI: coverage at nominal level (reviewer's check, 200 reps).
# Dedicated stream so coverage is reproducible independent of the blocks
# above; acceptance band = nominal 0.95 minus 3 binomial SE (0.904).
rng_ci = np.random.default_rng(SEED + 1)
cover = 0
for _ in range(200):
    yy = 2 * np.cos(2 * np.pi * t / 27.5) + rng_ci.normal(0, 1, 300)
    ci = v4.profile_ci_omega(t, yy, [1 / 27.4], 0)
    cover += ci["ci"][0] <= 1 / 27.5 <= ci["ci"][1]
out["profile_ci_coverage_200reps"] = cover / 200
assert out["profile_ci_coverage_200reps"] >= 0.95 - 3 * (0.95 * 0.05 / 200) ** .5

# baselines: both directions, constructed deterministically —
# frozen beating both baselines passes; frozen worse than the textbook
# baseline fails (the discrimination confirm1 lacked)
base = {"B0_climatology": np.full(300, y.mean()),
        "B1_textbook_apriori": 2 * np.cos(2 * np.pi * t / 27.555)}
b1_rmse = float(np.sqrt(np.mean((y - base["B1_textbook_apriori"]) ** 2)))
out["baseline_pass_when_better"] = bool(
    v4.beat_baselines(b1_rmse * 0.9, y, base)["passes"])
out["baseline_fail_when_worse"] = bool(
    not v4.beat_baselines(b1_rmse * 1.1, y, base)["passes"])
assert out["baseline_pass_when_better"] and out["baseline_fail_when_worse"]
assert v4.confirmation_label(True, independent_source=False) == \
    "MECHANISM_CONSISTENT"
out["same_source_label_cap"] = "MECHANISM_CONSISTENT"

out["seed"] = SEED
path = os.path.join(ROOT, "results", "v4_smoke.json")
json.dump(out, open(path, "w"), indent=2)
print(json.dumps(out, indent=1))
print("ALL V4 SMOKE TESTS PASS ->", os.path.relpath(path, ROOT))
