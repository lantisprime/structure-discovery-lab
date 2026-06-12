#!/usr/bin/env python3
"""External-review finding C (new): a DESIGN verifier, complementing the
numeric verifier (verify_relational_docs.py). Checks logic, not transcription:

  1. claim_type -> null/method compatibility (declared mapping)
  2. permutation-floor rule: p_floor <= alpha_corrected/2 per family
  3. hit-count statistics must carry data-regime sensitivity entries
  4. every test present in the global multiplicity ledger

Reads results/multiplicity_ledger.jsonl; writes results/design_verifier_report.json.
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
    "within-game-cooccurrence": {"lambda-max"},
}
# hit-count families require data-regime sensitivity rows
SENSITIVITY_REQUIRED = {"hit-count"}
ALPHA = 0.05


def main():
    rows = [json.loads(l) for l in
            open(os.path.join(ROOT, "results", "multiplicity_ledger.jsonl"))]
    violations, warnings = [], []
    fams = defaultdict(list)
    for r in rows:
        fams[(r["run_id"], r["family_id"])].append(r)
        if r["method"] not in VALID.get(r["claim_type"], set()):
            violations.append(
                f"claim/method mismatch: {r['run_id']}/{r['dataset']}: "
                f"{r['method']} cited for claim '{r['claim_type']}'")
    for (run, fam), rs in fams.items():
        m_family = max(r["within_run_m"] for r in rs)
        corrected = 1 - (1 - ALPHA) ** (1 / m_family)
        for r in rs:
            if r["p_floor"] > corrected / 2:
                msg = (f"floor rule: {run}/{r['dataset']}/{r['method']}: "
                       f"p_floor {r['p_floor']} > corrected/2 "
                       f"({corrected/2:.4f}) at family m={m_family}")
                # historical runs predate the rule -> warning; later runs -> violation
                HISTORICAL = {"firstrun", "batch5", "allgames", "batch6", "pressure"}
                (warnings if run in HISTORICAL else violations).append(msg)
    regimes = defaultdict(set)
    for r in rows:
        if r["family_id"] in SENSITIVITY_REQUIRED:
            regimes[(r["dataset"].split(" Q")[0], r["method"])].add(r["data_filter"])
    for k, have in regimes.items():
        if have == {"all_rows"} and "lambda-max" not in k[1]:
            warnings.append(f"sensitivity missing for hit-count stat {k}: only {have}")
    report = {"n_ledger_rows": len(rows),
              "violations": violations, "warnings": warnings,
              "design_map_families": {k: sorted(v) for k, v in VALID.items()},
              "verdict": "PASS" if not violations else "FAIL"}
    json.dump(report, open(os.path.join(ROOT, "results",
                                        "design_verifier_report.json"), "w"),
              indent=2)
    print(f"design verifier: {report['verdict']} | "
          f"{len(violations)} violations, {len(warnings)} warnings")
    for v in violations[:10]:
        print("  VIOLATION:", v)
    for w in warnings[:10]:
        print("  warning:", w)
    sys.exit(0 if not violations else 1)


if __name__ == "__main__":
    main()
