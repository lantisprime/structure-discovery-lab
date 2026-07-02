#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
"""M6 remediation: global meta-uniformity panel — v2 (audit fixes M-5, M-6).

v2 changes vs v1 (2026-07-02, AUDIT_CORRECTNESS_2026-07-02.md M-5):
  1. Panel is built from the multiplicity ledger (single source of truth),
     not from hand-picked result JSONs: live test rows only (no superseded,
     no family charges).
  2. Median-of-repeats entries EXCLUDED (knn-recovery rows carry median_p of
     10 repeats — Beta-concentrated near 0.5 under H0, not U(0,1)).
  3. Physical-series / equation rows excluded (lotto-side panel by design).
  4. Duplicate statistics (same method+dataset+filter re-run later) deduped,
     keeping the latest run.
  5. Reference distribution is the exact DISCRETE lattice null simulated with
     the panel's own m composition — not continuous uniform (add-one p-values
     on m=19..1199 lattices are stochastically >= U(0,1)).
  6. Output carries panel_sha; docs quoting panel numbers must cite it.
Caveat retained: panel entries are mutually dependent (same draws feed many
instruments); the meta p is DESCRIPTIVE, not a calibrated test.

Writes results/meta_uniformity.json + fig9."""

import hashlib
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SEED = 20260702
N_SIM = 2000
MEDIAN_BASED_METHODS = {"knn-recovery"}          # median of 10 repeat p-values
NON_LOTTO_RUN_PREFIXES = ("eq_",)                # physical-series equation runs
# adversarial review M5.1: the remediation presence-MC p's were produced by
# the col-permuted null that corrected_reruns' calibration control proved
# miscalibrated (mean H0 p = 0.925 vs 0.488 constrained). Non-uniform by
# construction -> excluded until the registered constrained-null rerun lands.
MISCALIBRATED = {("remediation", "matrix-completion")}
# review M5.2: dataset aliases defeat dedup ('6/55' vs 'Grand Lotto 6/55')
ALIASES = {"6/42": "Lotto 6/42", "6/45": "Mega Lotto 6/45",
           "6/49": "Super Lotto 6/49", "6/55": "Grand Lotto 6/55",
           "6/58": "Ultra Lotto 6/58"}


def collect(include_miscal=False, include_eq=False, keep_first=False):
    rows = [json.loads(l) for l in
            open(os.path.join(ROOT, "results", "multiplicity_ledger.jsonl"))]
    panel, exploratory = {}, []
    for r in rows:
        if r.get("row_type", "test") != "test" or "superseded_by" in r:
            continue
        if r.get("raw_p") is None or r.get("m_perm") is None:
            continue
        if r.get("exploratory"):          # reported as a separate stratum
            exploratory.append(r)         # (review M-C: the honesty meter
            continue                      # must not be blind to this class)
        if r["method"] in MEDIAN_BASED_METHODS:
            continue
        if not include_eq and r["run_id"].startswith(NON_LOTTO_RUN_PREFIXES):
            continue
        if not include_miscal and (r["run_id"], r["method"]) in MISCALIBRATED:
            continue
        ds = ALIASES.get(r["dataset"], r["dataset"])
        filt = "all_rows" if r["data_filter"] == "all" else r["data_filter"]
        key = (r["method"], ds, filt)
        if keep_first and key in panel:
            continue
        panel[key] = r                            # later run overwrites earlier
    return list(panel.values()), exploratory


def ks_stat(p):
    q = np.sort(p)
    n = len(q)
    grid = np.arange(1, n + 1) / n
    return float(max(np.max(grid - q), np.max(q - (np.arange(n)) / n)))


def main():
    rows, exploratory = collect()
    allp = np.array([r["raw_p"] for r in rows])
    ms = np.array([r["m_perm"] for r in rows])
    obs_ks = ks_stat(allp)
    obs_frac05 = float(np.mean(allp <= 0.05))
    obs_frac01 = float(np.mean(allp <= 0.01))

    # discrete lattice null with the panel's own m composition
    rng = np.random.default_rng(SEED)
    sim_ks, sim_f05, sim_f01 = [], [], []
    for _ in range(N_SIM):
        c = rng.integers(0, ms + 1)               # counts 0..m each
        p = (1 + c) / (ms + 1)
        sim_ks.append(ks_stat(p))
        sim_f05.append(np.mean(p <= 0.05))
        sim_f01.append(np.mean(p <= 0.01))
    sim_ks, sim_f05, sim_f01 = map(np.array, (sim_ks, sim_f05, sim_f01))
    p_meta = float((1 + np.sum(sim_ks >= obs_ks)) / (N_SIM + 1))

    key_list = sorted(f"{r['run_id']}|{r['dataset']}|{r['method']}|"
                      f"{r['data_filter']}|{r['raw_p']}" for r in rows)
    panel_sha = hashlib.sha256("\n".join(key_list).encode()).hexdigest()[:16]

    by_run = {}
    for r in rows:
        by_run[r["run_id"]] = by_run.get(r["run_id"], 0) + 1
    out = {"panel_version": 2, "panel_sha": panel_sha,
           "n_tests": int(len(allp)),
           "ks_stat": obs_ks,
           "p_meta_discrete": p_meta,
           "frac_le_05": obs_frac05, "frac_le_01": obs_frac01,
           "sim_frac_le_05_q05_q95": [float(np.quantile(sim_f05, .05)),
                                      float(np.quantile(sim_f05, .95))],
           "sim_frac_le_01_q05_q95": [float(np.quantile(sim_f01, .05)),
                                      float(np.quantile(sim_f01, .95))],
           "n_sim": N_SIM, "seed": SEED,
           "by_run_counts": by_run,
           "exclusions": {"median_based_methods": sorted(MEDIAN_BASED_METHODS),
                          "non_lotto_run_prefixes": list(NON_LOTTO_RUN_PREFIXES),
                          "miscalibrated_null_pending_rerun":
                              sorted(map(list, MISCALIBRATED)),
                          "superseded": True, "family_charges": True,
                          "gate_based": True},
           # review M-C: exploratory stratum reported alongside, never pooled
           "exploratory_stratum": {
               "n": len(exploratory),
               "p_values": sorted(round(r["raw_p"], 4) for r in exploratory),
               "note": "unregistered shadow-run p's; reported so the panel "
                       "is not blind to the exploratory class; not pooled"},
           "note": ("lotto-side real-data tests only; discrete-lattice reference; "
                    "entries dependent -> p_meta is descriptive")}

    # review m-1: composition sensitivity — the panel published under three
    # registered alternative compositions, so no single discretionary choice
    # governs the picture
    def quick(rows_alt):
        p = np.array([r["raw_p"] for r in rows_alt])
        return {"n": int(len(p)), "frac_le_05": round(float(np.mean(p <= .05)), 4)}
    out["composition_sensitivity"] = {
        "keep_first_dedup": quick(collect(keep_first=True)[0]),
        "eq_rows_included": quick(collect(include_eq=True)[0]),
        "miscalibrated_presence_included": quick(collect(include_miscal=True)[0]),
        "drop_655_lambda_max_family": quick(
            [r for r in rows if not (r["method"] == "lambda-max"
                                     and "6/55" in r["dataset"])])}
    json.dump(out, open(os.path.join(ROOT, "results", "meta_uniformity.json"),
                        "w"), indent=2)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(allp, bins=np.linspace(0, 1, 21), color="#4878a8",
               edgecolor="white")
    ax[0].axhline(len(allp) / 20, color="k", ls="--", lw=1,
                  label="uniform expectation")
    ax[0].set_xlabel("p-value"); ax[0].set_ylabel("count")
    ax[0].set_title(f"{len(allp)} lotto-side real-data p-values (panel v2)\n"
                    f"discrete-lattice meta p={p_meta:.3f}; "
                    f"{obs_frac05*100:.1f}% <= 0.05")
    ax[0].legend()
    qq = np.sort(allp)
    ax[1].plot(np.linspace(0, 1, len(qq)), qq, color="#b03a3a", label="observed")
    lo = np.sort(np.quantile(np.sort(np.array(
        [(1 + rng.integers(0, ms + 1)) / (ms + 1) for _ in range(200)]),
        axis=1), .05, axis=0))
    hi = np.sort(np.quantile(np.sort(np.array(
        [(1 + rng.integers(0, ms + 1)) / (ms + 1) for _ in range(200)]),
        axis=1), .95, axis=0))
    ax[1].fill_between(np.linspace(0, 1, len(qq)), lo, hi, alpha=.25,
                       color="gray", label="discrete null 5–95%")
    ax[1].plot([0, 1], [0, 1], "k--", lw=1)
    ax[1].set_xlabel("uniform quantile"); ax[1].set_ylabel("observed p quantile")
    ax[1].set_title("Q-Q vs discrete lattice null")
    ax[1].legend()
    fig.suptitle("M6: global multiplicity panel v2 (ledger-driven, "
                 "discrete-aware)", y=1.03)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results/figures/fig9_meta_uniformity.png"),
                dpi=150, bbox_inches="tight")
    print(json.dumps({k: out[k] for k in
                      ("panel_version", "panel_sha", "n_tests",
                       "p_meta_discrete", "frac_le_05", "frac_le_01")}, indent=1))


if __name__ == "__main__":
    main()
