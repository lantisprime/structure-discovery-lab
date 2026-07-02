#!/usr/bin/env python3
"""AUDIT G-5 / Playbook Algorithm H-2: measured equivalence classes.

Produces results/families.json — the canonical family registry. NOTE
(adversarial review M-D): consumption by the ledgers/design verifier is a
DESIGNED-NOT-YET-WIRED integration; until the verifier reads this file, the
registry is documentation with provenance, not an enforced gate. Two parts:

  (a) MEASURED null correlations between per-game scalar statistics that
      share raw data, estimated on shared synthetic H0 draw-years
      (constrained 6-of-P generator). This executes the "H-protocol
      measurement" that ADMISSION_RELATIONAL left 'provisional' — in
      particular lambda_max vs graphon-B1 (the #45 re-shadowing risk, C9)
      and both vs half-corr / presence-completion skill.
      SCOPE (review M-D): measured at T=155, P=55 only. Correlations under
      H0 are not generically (T,P)-invariant; consumption at other configs
      requires re-measurement or a declared invariance argument.
  (b) DECLARED memberships for instruments whose statistics do not reduce
      to a shared scalar on one game (cross-game spectra, TDA, CCA, MMD,
      eq family) — carried from ADMISSION_RELATIONAL with status flags.

Merge rule (playbook H-2): |spearman rho| >= 0.90 under H0 -> same family;
0.5 <= |rho| < 0.90 -> reported structural coupling, separate families.
"""
import json
import os
import sys

import numpy as np
from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

from relational_batch5 import GameSpec, cooccurrence, uniform_draws, std_spectrum  # noqa: E402
from graphon_cooccurrence import indicators, stats_pair                            # noqa: E402
from relational_admission import soft_impute                                       # noqa: E402

SEED = 20260702
N_SIM = 200
T, P = 155, 55
RHO_MERGE, RHO_REPORT = 0.90, 0.50


def half_corr(draws, P):
    """Hot-number split correlation (batch6 halves statistic)."""
    h = len(draws) // 2
    c1 = np.bincount(draws[:h].ravel() - 1, minlength=P)
    c2 = np.bincount(draws[h:].ravel() - 1, minlength=P)
    return float(np.corrcoef(c1, c2)[0, 1])


def presence_skill(draws, P, mask):
    M = np.zeros((len(draws), P))
    for i, r in enumerate(draws):
        M[i, r - 1] = 1.0
    L, col_mean = soft_impute(M, mask)
    rm = np.sqrt(np.mean((L[~mask] - M[~mask]) ** 2))
    rb = np.sqrt(np.mean((col_mean[None, :].repeat(len(M), 0)[~mask]
                          - M[~mask]) ** 2))
    return float(rb - rm)


def measure():
    rng = np.random.default_rng(SEED)
    gs = GameSpec(rng, T, P, "H2-measure")           # calibrates mu/sd stream
    mask = rng.uniform(size=(T, P)) < 0.6            # frozen design variable
    S = {"lambda_max": [], "graphon_b1": [], "half_corr": [],
         "presence_skill": []}
    for _ in range(N_SIM):
        d = uniform_draws(rng, T, P)                 # 1-indexed
        S["lambda_max"].append(
            std_spectrum(cooccurrence(d, P), gs.mu, gs.sd)[1])
        S["graphon_b1"].append(stats_pair(indicators(d - 1, P), P)[0])
        S["half_corr"].append(half_corr(d, P))
        S["presence_skill"].append(presence_skill(d, P, mask))
    names = list(S)
    R = np.ones((len(names), len(names)))
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            R[i, j] = R[j, i] = st.spearmanr(S[names[i]], S[names[j]])[0]
    return names, R


def components(names, R, thr):
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i < j and abs(R[i, j]) >= thr:
                parent[find(b)] = find(a)
    out = {}
    for n in names:
        out.setdefault(find(n), []).append(n)
    return list(out.values())


def main():
    names, R = measure()
    comps = components(names, R, RHO_MERGE)
    couplings = [{"pair": [names[i], names[j]],
                  "spearman_rho_h0": round(float(R[i, j]), 3)}
                 for i in range(len(names)) for j in range(i + 1, len(names))
                 if RHO_REPORT <= abs(R[i, j])]
    fam = {
        "version": 1, "date": "2026-07-02", "seed": SEED, "n_sim": N_SIM,
        "generator": "constrained 6-of-55 uniform, T=155",
        "scope": {"measured_at": {"T": 155, "P": 55},
                  "valid_for_other_configs": "requires re-measurement or a "
                  "declared invariance argument (review M-D)"},
        "merge_rule": {"rho_merge": RHO_MERGE, "rho_report": RHO_REPORT},
        "measured_matrix": {"names": names,
                            "spearman": [[round(float(x), 3) for x in row]
                                         for row in R]},
        "measured_components": comps,
        "reported_couplings": couplings,
        "families": {
            # ledger family_id -> class + provenance
            "hit-count-cooc": {"members": ["lambda-max", "graphon-b1-attribution"],
                               "class": "within-game-cooccurrence",
                               "status": "measured@T155P55 (rho=0.988)"},
            "hit-count-temporal": {"members": ["half-corr"],
                                   "class": "hit-count-temporal",
                                   "status": "measured@T155P55; couplings to "
                                             "lambda_max/B1 0.46-0.49 (N=200, "
                                             "SE~0.06) — below merge, near "
                                             "report threshold"},
            "recovery": {"members": ["knn-recovery", "matrix-completion"],
                         "class": "subset-to-whole",
                         "status": "declared; only matrix-completion's "
                                   "statistic proxied in this run — "
                                   "knn-recovery NOT measured (review M-D)"},
            "two-sample": {"members": ["mmd"], "class": "distributional",
                           "status": "declared (no shared scalar on one game)"},
            "graph": {"members": ["cooc-spectra"], "class": "cross-game-spectra",
                      "status": "declared; R5-vs-hit-count-cooc coupling — the "
                                "audit G-5 headline risk — remains UNMEASURED "
                                "(cross-game statistic has no shared scalar on "
                                "one game; needs a dedicated H-protocol run); "
                                "flags must row-trace meanwhile"},
            "tda": {"members": ["delay-embed-H1"], "class": "topological",
                    "status": "declared ({R2,R4} constitutional class)"},
            "cca": {"members": ["cca-covariates", "cca-pressure",
                                "cca-split-0.5", "cca-split-0.6", "cca-split-0.7"],
                    "class": "latent-sharing",
                    "status": "declared; splits are nested/dependent"},
            "eq.tidal-manila.harmonic": {
                "members": ["null-equation-generator",
                            "frozen-equation-confirmation"],
                "class": "equation_discovery",
                "status": "charged via registrations (m=10 cumulative)"},
        },
        "consumption_rules": [
            "multiplicity ledger family_id MUST appear in this registry",
            "Sidak m = number of families engaged in a registered run",
            "two same-family rejections = ONE flag; row-trace (S-6) mandatory",
            "rerun this script when any instrument or its statistic changes",
        ],
    }
    path = os.path.join(ROOT, "results", "families.json")
    json.dump(fam, open(path, "w"), indent=2)
    print("components at rho>=0.90:", comps)
    print("reported couplings:", json.dumps(couplings, indent=1))
    print("written", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
