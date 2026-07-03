#!/usr/bin/env python3
"""External-review finding C (new): a DESIGN verifier, complementing the
numeric verifier (verify_relational_docs.py). Checks logic, not transcription:

  1. claim_type -> null/method compatibility (declared mapping)
  2. permutation-floor rule: p_floor <= alpha_corrected/2 per family
  3. hit-count statistics must carry data-regime sensitivity entries
  4. schema validity per row_type (ledger schema v2); gate_based restricted
     to a method whitelist; exploratory rows must reference a G0 run-ledger
     entry (adversarial review M2: both flags were abusable escape hatches)
  5. run-ledger <-> test-ledger reconciliation, PER RUN and total (G-3)
  6. p-lattice consistency: raw_p*(m_perm+1) must be an integer — an add-one
     Monte Carlo p must lie on its own lattice (adversarial review B1: this
     check catches wrong recorded m, as it would have caught the 399/999
     ledger corruption)

Reads results/multiplicity_ledger.jsonl (schema v2: row_type = test |
family_charge; audit fix C-1 2026-07-02) and results/run_ledger.jsonl.
Writes results/design_verifier_report.json.
Exit code 1 on violations (warnings do not fail the build)."""

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

# claim type -> methods that are valid evidence for it (design map)
VALID = {
    "distributional": {"mmd"},
    "cross-dataset-similarity": {"cooc-spectra"},
    "subset-to-whole": {"matrix-completion", "knn-recovery"},
    "latent-sharing": {"cca-covariates", "cca-pressure"} |
                      {f"cca-split-{t}" for t in ("0.5", "0.6", "0.7")},
    "scalar-correlation": {"corr-sum-pressure"},
    "topological": {"delay-embed-H1"},
    "frequency-bias-generalization": {"half-corr"},
    "within-game-cooccurrence": {"lambda-max", "graphon-b1-attribution"},
    # audit C-1: equation claims were previously outside the design gate
    "equation_discovery": {"null-equation-generator",
                           "frozen-equation-confirmation"},
}
# hit-count families require data-regime sensitivity rows (audit G-2: was an
# exact-match set that never fired against hit-count-temporal/-cooc)
SENSITIVITY_PREFIX = "hit-count"
TEST_KEYS = {"run_id", "dataset", "claim_type", "method", "family_id",
             "within_run_m", "row_type"}
CHARGE_KEYS = {"family_id", "m_delta", "claim_type", "reason",
               "registration", "date", "row_type"}
# only these methods may carry gate_based (no p-value) rows
GATE_BASED_METHODS = {"frozen-equation-confirmation"}
# median-of-repeats rows live between lattice points (median of 10 repeats);
# exempt from the lattice check, and excluded from the meta panel for the
# same reason (Beta-concentrated, not U(0,1))
MEDIAN_BASED_METHODS = {"knn-recovery"}
# runs predating a rule get warnings, not violations
HISTORICAL = {"firstrun", "batch5", "allgames", "batch6", "pressure"}
ALPHA = 0.05


def load_rows(path):
    rows = [json.loads(l) for l in open(path)]
    for r in rows:  # v1 back-compat: infer row_type
        r.setdefault("row_type",
                     "family_charge" if "m_delta" in r else "test")
    return rows


def main():
    rows = load_rows(os.path.join(ROOT, "results", "multiplicity_ledger.jsonl"))
    violations, warnings = [], []

    # -- check 4: schema validity ------------------------------------------
    for i, r in enumerate(rows):
        need = TEST_KEYS if r["row_type"] == "test" else CHARGE_KEYS
        missing = need - set(r)
        if missing:
            violations.append(f"schema: row {i+1} ({r['row_type']}) missing "
                              f"{sorted(missing)}")
        if r["row_type"] == "test" and not r.get("gate_based"):
            for k in ("raw_p", "m_perm", "p_floor"):
                if r.get(k) is None:
                    violations.append(f"schema: row {i+1} test row has null {k} "
                                      f"without gate_based flag")
        if r.get("gate_based") and r.get("method") not in GATE_BASED_METHODS:
            violations.append(f"gate_based abuse: row {i+1} method "
                              f"'{r.get('method')}' may not opt out of p/floor "
                              f"scrutiny (whitelist: {sorted(GATE_BASED_METHODS)})")
        if r["row_type"] == "family_charge" and \
                not os.path.exists(os.path.join(ROOT, r.get("registration", ""))):
            violations.append(f"charge row references missing registration "
                              f"{r.get('registration')}")
        # check 6: p-lattice consistency (add-one p must lie on its lattice)
        if r["row_type"] == "test" and r.get("raw_p") is not None \
                and r.get("m_perm") is not None \
                and r.get("method") not in MEDIAN_BASED_METHODS:
            p_full = r.get("raw_p_full", r["raw_p"])
            k = p_full * (r["m_perm"] + 1)
            # 4-dp rounding of raw_p allows |k - round(k)| up to (m+1)*5e-5
            tol = max(1e-6, (r["m_perm"] + 1) * 5.1e-5) \
                if "raw_p_full" not in r else 1e-6
            if abs(k - round(k)) > tol:
                violations.append(
                    f"p-lattice: {r['run_id']}/{r['dataset']}/{r['method']}: "
                    f"raw_p {p_full} not on the m={r['m_perm']} add-one lattice "
                    f"(p*(m+1)={k:.3f}) — recorded m is likely wrong")

    tests = [r for r in rows if r["row_type"] == "test"]
    # live = counts toward global m: not superseded, not exploratory-only
    live = [r for r in tests
            if "superseded_by" not in r and not r.get("exploratory")]

    # -- check 1: claim/method map -----------------------------------------
    fams = defaultdict(list)
    for r in tests:
        fams[(r["run_id"], r["family_id"])].append(r)
        if r["method"] not in VALID.get(r["claim_type"], set()):
            violations.append(
                f"claim/method mismatch: {r['run_id']}/{r['dataset']}: "
                f"{r['method']} cited for claim '{r['claim_type']}'")

    # -- check 2: floor rule -----------------------------------------------
    for (run, fam), rs in fams.items():
        m_family = max(r["within_run_m"] for r in rs)
        corrected = 1 - (1 - ALPHA) ** (1 / m_family)
        for r in rs:
            if r.get("gate_based") or r.get("p_floor") is None:
                continue
            if r["p_floor"] > corrected / 2:
                msg = (f"floor rule: {run}/{r['dataset']}/{r['method']}: "
                       f"p_floor {r['p_floor']} > corrected/2 "
                       f"({corrected/2:.4f}) at family m={m_family}")
                (warnings if run in HISTORICAL else violations).append(msg)

    # -- check 3: sensitivity regimes (prefix match; audit G-2) ------------
    # Regimes are only *defined* where the audited dataset has quarantined
    # rows; requiring 3 regimes for games with zero suspicious rows would be
    # a no-op filter. Derive the affected games from the data itself.
    suspicious_games = set()
    csv = os.path.join(ROOT, "datasets/pcso-lotto/data_draws_1yr_audited.csv")
    if os.path.exists(csv):
        import csv as _csv
        with open(csv) as f:
            for row in _csv.DictReader(f):
                if row.get("Status") == "suspicious_or_needs_review":
                    suspicious_games.add(row["Game"])
    regimes = defaultdict(set)
    for r in live:
        if r["family_id"].startswith(SENSITIVITY_PREFIX):
            regimes[(r["run_id"], r["method"])].add(r["data_filter"])
    DEFAULT_FILTERS = {"all_rows", "all"}     # review minor: batch67_r2 uses 'all'
    for (run, method), have in regimes.items():
        group_hits_suspicious = any(
            g.split()[-1] in r["dataset"]  # e.g. "6/55" in "Grand Lotto 6/55"
            for g in suspicious_games for r in live
            if r["run_id"] == run and r["method"] == method)
        if group_hits_suspicious and not (have - DEFAULT_FILTERS):
            msg = (f"sensitivity missing for hit-count stat ({run}, {method}): "
                   f"only {have} though quarantined rows exist")
            (warnings if run in HISTORICAL else violations).append(msg)

    # -- check 7: family-registry consumption (review M-D: families.json was
    # documentation-not-gate until this check existed) ----------------------
    fam_path = os.path.join(ROOT, "results", "families.json")
    if os.path.exists(fam_path):
        registry = set(json.load(open(fam_path))["families"])
        for fid in {r["family_id"] for r in tests}:
            if fid not in registry:
                violations.append(f"family registry: ledger family_id '{fid}' "
                                  f"not in results/families.json")
    else:
        warnings.append("families.json missing — family registry unenforced")

    # -- check 5: run-ledger reconciliation (audit G-3) ---------------------
    rl_path = os.path.join(ROOT, "results", "run_ledger.jsonl")
    recon = None
    if os.path.exists(rl_path):
        rl = [json.loads(l) for l in open(rl_path)]
        declared = sum(r.get("real_data_tests", 0) for r in rl)
        recon = {"run_ledger_declared": declared, "test_rows": len(tests)}
        if declared != len(tests):
            violations.append(f"reconciliation: run ledger declares {declared} "
                              f"real-data tests, test-ledger has {len(tests)}")
        by_run = defaultdict(int)
        for r in tests:
            by_run[r["run_id"]] += 1
        rl_by_run = {x["run_id"]: x for x in rl}
        # PER-RUN reconciliation (review M2: total-only was dodgeable)
        for run, cnt in by_run.items():
            if run not in rl_by_run:
                violations.append(f"reconciliation: test rows for '{run}' "
                                  f"but no run-ledger entry")
            elif rl_by_run[run].get("real_data_tests", 0) != cnt:
                violations.append(
                    f"reconciliation: run '{run}' declares "
                    f"{rl_by_run[run].get('real_data_tests')} tests, "
                    f"ledger has {cnt}")
        # exploratory rows must reference a G0-graded run-ledger entry (M2)
        for r in tests:
            if r.get("exploratory"):
                entry = rl_by_run.get(r["run_id"])
                if not entry or not str(entry.get("grade", "")).startswith("G0"):
                    violations.append(
                        f"exploratory abuse: row {r['run_id']}/{r['dataset']} "
                        f"exploratory without a G0 run-ledger entry")

    report = {"n_ledger_rows": len(rows), "n_test_rows": len(tests),
              "n_live_test_rows": len(live),
              "n_charge_rows": len(rows) - len(tests),
              "reconciliation": recon,
              "violations": violations, "warnings": warnings,
              "design_map_families": {k: sorted(v) for k, v in VALID.items()},
              "verdict": "PASS" if not violations else "FAIL"}
    json.dump(report, open(os.path.join(ROOT, "results",
                                        "design_verifier_report.json"), "w"),
              indent=2)
    print(f"design verifier: {report['verdict']} | "
          f"{len(violations)} violations, {len(warnings)} warnings | "
          f"{len(tests)} test rows ({len(live)} live), "
          f"{len(rows)-len(tests)} charge rows")
    for v in violations[:10]:
        print("  VIOLATION:", v)
    for w in warnings[:10]:
        print("  warning:", w)
    sys.exit(0 if not violations else 1)


if __name__ == "__main__":
    main()
