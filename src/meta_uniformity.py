#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
"""M6 remediation: global meta-uniformity panel. Collects every lotto-side
real-data p-value across the relational program and tests the pooled
distribution against uniform — the meta-signature check the lab applies to
its own output. Writes results/meta_uniformity.json + fig9."""

import json
import os

import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
R = lambda f: json.load(open(os.path.join(ROOT, "results", f)))


def collect():
    src = {}
    B5 = R("relational_batch5.json")
    src["b5_crossgame_pairs"] = [v["p"] for v in B5["crossgame"]["pairs"].values()]
    F = R("relational_first_run.json")
    src["firstrun_lotto_recovery"] = [c["median_p"] for c in
                                      F["recovery_curves"]["lotto655_draw_sum"]["curve"]]
    # batch6 originals SUPERSEDED by batch67_r2 (same statistics, same data,
    # floor-compliant m) — the panel pools the current-best version of each
    # test; pooling both would double-count correlated p-values.
    P = R("relational_pressure.json")
    src["pressure_cca"] = [v["cca_p"] for v in P["HP2_per_game"].values()]
    src["pressure_scalar"] = [v["p_scalar"] for v in P["HP2_per_game"].values()]
    G = R("relational_allgames.json")
    keys = ["g42", "g45", "g49", "g55", "g58"]
    src["allgames_topology"] = [G[k]["topology_h1"]["p"] for k in keys]
    src["allgames_cca"] = [G[k]["cca_vs_covariates"]["p_shuffled_pairing"] for k in keys]
    M = R("remediation_r1.json")
    src["rem_presence_mc"] = [v["p"] for v in M["presence_mc"]["per_game"].values()]
    src["rem_lmax_m399"] = [v["p"] for v in M["floors_lmax"]["per_game"].values()]
    src["rem_cca_splits"] = [s["p"] for g in M["cca_splits"]["per_game"].values()
                             for s in g.values()]
    RR = R("rerun_batch67.json")
    src["rerun_b6_mmd"] = [pp for g in RR["b6_mmd"]["per_game"].values()
                           for pp in g.values()]
    src["rerun_b6_spectra"] = [pp for g in RR["b6_spectra"]["per_game"].values()
                               for pp in g.values()]
    src["rerun_b6_halves"] = [x["p"] for g in RR["b6_halves"]["per_game"].values()
                              for x in g.values() if "p" in x]
    return src


def main():
    src = collect()
    allp = np.array([p for v in src.values() for p in v])
    ks = stats.kstest(allp, "uniform")
    out = {"n_tests": int(len(allp)),
           "ks_p": float(ks.pvalue), "ks_stat": float(ks.statistic),
           "frac_le_05": float(np.mean(allp <= 0.05)),
           "frac_le_01": float(np.mean(allp <= 0.01)),
           "by_source_counts": {k: len(v) for k, v in src.items()},
           "note": "lotto-side real-data tests only; physical-series positives excluded by design"}
    json.dump(out, open(os.path.join(ROOT, "results", "meta_uniformity.json"), "w"),
              indent=2)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(allp, bins=np.linspace(0, 1, 21), color="#4878a8", edgecolor="white")
    ax[0].axhline(len(allp) / 20, color="k", ls="--", lw=1, label="uniform expectation")
    ax[0].set_xlabel("p-value"); ax[0].set_ylabel("count")
    ax[0].set_title(f"All {len(allp)} lotto-side real-data p-values\n"
                    f"KS vs uniform p={ks.pvalue:.3f}; {np.mean(allp<=0.05)*100:.1f}% ≤ 0.05")
    ax[0].legend()
    qq = np.sort(allp)
    ax[1].plot(np.linspace(0, 1, len(qq)), qq, color="#b03a3a")
    ax[1].plot([0, 1], [0, 1], "k--", lw=1)
    ax[1].set_xlabel("uniform quantile"); ax[1].set_ylabel("observed p quantile")
    ax[1].set_title("Q-Q vs uniform — the meta-signature of honest nulls")
    fig.suptitle("M6 remediation: global multiplicity panel (per-batch corrections "
                 "now backed by the pooled check)", y=1.03)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results/figures/fig9_meta_uniformity.png"),
                dpi=150, bbox_inches="tight")
    print(json.dumps(out, indent=1)[:400])


if __name__ == "__main__":
    main()
