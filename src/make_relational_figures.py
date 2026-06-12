#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
"""Generates the figure artifacts for the relational runs, entirely from the
result JSONs (plus two recomputed persistence diagrams, seeded). Reproducible:
rerun any time; figures land in results/figures/."""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "results", "figures")
os.makedirs(FIG, exist_ok=True)

FR = json.load(open(os.path.join(ROOT, "results", "relational_first_run.json")))
B5 = json.load(open(os.path.join(ROOT, "results", "relational_batch5.json")))
AD = json.load(open(os.path.join(ROOT, "results", "relational_admission.json")))


# ---- Fig 1: admission summary -------------------------------------------
def fig_admission():
    names, fprs, powers, ns = [], [], [], []
    for k, v in AD.items():
        if k == "_meta":
            continue
        neg = [x for x in v if x.startswith("negative")][0]
        pos = [x for x in v if x.startswith("positive")][0]
        names.append(k.split("_", 1)[0])
        fprs.append(v[neg]["fpr_at_alpha"])
        powers.append(v[pos]["power_at_alpha"])
        ns.append(v[neg]["n_trials"])
    x = np.arange(len(names))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].bar(x, fprs, color="#4878a8")
    ax[0].axhline(0.05, color="k", ls="--", lw=1, label="nominal α=0.05")
    for i, n in enumerate(ns):
        se3 = 3 * np.sqrt(0.05 * 0.95 / n)
        ax[0].errorbar(i, 0.05, yerr=se3, color="gray", capsize=4, lw=1)
    ax[0].set_xticks(x); ax[0].set_xticklabels(names)
    ax[0].set_ylabel("false-positive rate on independence")
    ax[0].set_title("Negative controls: silence on independence (E1)\nerror bars = 3 MC SE around α")
    ax[0].legend()
    ax[1].bar(x, powers, color="#5a9a68")
    ax[1].axhline(0.8, color="k", ls="--", lw=1, label="admission gate 0.80")
    ax[1].set_xticks(x); ax[1].set_xticklabels(names)
    ax[1].set_ylabel("power on planted structure")
    ax[1].set_ylim(0, 1.05)
    ax[1].set_title("Positive controls: detection of planted structure")
    ax[1].legend()
    fig.suptitle("A2 admission, relational instruments R1–R7 (all admitted)", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_admission_controls.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 2: first-run recovery curves -----------------------------------
def fig_recovery():
    rc = FR["recovery_curves"]
    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {"tidal_total_accel": ("#1f6fb4", "o", "tidal acceleration"),
              "moon_distance_km": ("#7b52a8", "s", "moon distance"),
              "kp_daily_mean": ("#c2702a", "^", "Kp geomagnetic mean"),
              "lotto655_draw_sum": ("#b03a3a", "x", "lotto 6/55 draw sum")}
    for s, (c, m, lab) in styles.items():
        ks = [c_["frac"] * 100 for c_ in rc[s]["curve"]]
        zs = [c_["mean_null_adjusted_z"] for c_ in rc[s]["curve"]]
        ax.plot(ks, zs, color=c, marker=m, label=lab)
    ax.axhline(0, color="k", lw=1)
    ax.axhspan(-2, 2, color="gray", alpha=0.15, label="±2z null band")
    ax.set_xscale("log"); ax.set_xticks([1, 2, 5, 10, 20, 40])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("subset fraction k (%)")
    ax.set_ylabel("null-adjusted recovery z (mean of 10 seeds)")
    ax.set_title("Subset-to-whole recovery curves (§4.5)\n"
                 "physical series rise; the lotto sits on the null line at every k")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_recovery_curves.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 3: cross-game comparison ---------------------------------------
def fig_crossgame():
    cg = B5["crossgame"]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    # per-game lambda_max vs null
    games = list(cg["per_game_lambda_max"])
    short = [g.split()[-1] for g in games]
    lm = [cg["per_game_lambda_max"][g]["lambda_max"] for g in games]
    nm = [cg["per_game_lambda_max"][g]["null_mean"] for g in games]
    ns = [cg["per_game_lambda_max"][g]["null_std"] for g in games]
    pv = [cg["per_game_lambda_max"][g]["p"] for g in games]
    x = np.arange(len(games))
    ax[0].errorbar(x, nm, yerr=2 * np.array(ns), fmt="_", color="gray",
                   capsize=6, lw=2, label="null mean ±2σ")
    ax[0].scatter(x, lm, color="#b03a3a", zorder=3, label="observed λ_max")
    for i, p in enumerate(pv):
        ax[0].annotate(f"p={p:.2f}", (x[i], lm[i]), textcoords="offset points",
                       xytext=(0, 8), ha="center", fontsize=8)
    ax[0].set_xticks(x); ax[0].set_xticklabels(short)
    ax[0].set_ylabel("λ_max of standardized co-occurrence")
    ax[0].set_title("Per-game λ_max vs constrained null\n"
                    "6/55 flag = known #45 shadow (C9, eigenvector loading 0.44 on #45)")
    ax[0].legend()
    # pairwise p-values
    pairs = cg["pairs"]
    labels = [k.replace("Lotto ", "").replace("Grand ", "").replace("Mega ", "")
               .replace("Super ", "").replace("Ultra ", "") for k in pairs]
    ps = [v["p"] for v in pairs.values()]
    y = np.arange(len(ps))
    ax[1].barh(y, ps, color="#4878a8")
    ax[1].axvline(cg["sidak_threshold"], color="k", ls="--", lw=1,
                  label=f"Šidák threshold (m={cg['m_pairs']}) = {cg['sidak_threshold']:.4f}")
    ax[1].set_yticks(y); ax[1].set_yticklabels(labels, fontsize=8)
    ax[1].set_xlabel("permutation p (shared structure)")
    ax[1].set_title("Cross-game co-occurrence similarity: all 10 pairs NULL")
    ax[1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_crossgame_spectra.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 4: topology — embeddings, diagrams, nulls ----------------------
def fig_topology():
    sys.path.insert(0, HERE)
    from relational_batch5 import load_series, delay_embed
    from ripser import ripser
    series = load_series()
    rng = np.random.default_rng(20260611)
    fig, ax = plt.subplots(2, 3, figsize=(13, 8))
    for row, name in enumerate(["tidal_total_accel", "lotto655_draw_sum"]):
        y = series[name]
        X = delay_embed(y)
        Xp = delay_embed(y[rng.permutation(len(y))])
        res = B5["topology"]["series"][name]
        ax[row, 0].scatter(X[:, 0], X[:, 1], s=6, alpha=0.6, color="#1f6fb4")
        ax[row, 0].set_title(f"{name}\ndelay embedding (τ=3), first two coords")
        for col, (Z, lab) in enumerate([(X, "observed"), (Xp, "permuted null sample")],
                                       start=1):
            dgm = ripser(Z, maxdim=1)["dgms"][1]
            lim = 2.5
            ax[row, col].plot([0, lim], [0, lim], "k--", lw=1)
            if len(dgm):
                ax[row, col].scatter(dgm[:, 0], dgm[:, 1], s=18, color="#b03a3a")
            ax[row, col].set_xlim(0, lim); ax[row, col].set_ylim(0, lim)
            ax[row, col].set_xlabel("birth"); ax[row, col].set_ylabel("death")
            ttl = f"H1 diagram — {lab}"
            if col == 1:
                ttl += f"\nmax persistence {res['max_h1_persistence']:.2f}, p={res['p']:.2f} (null q95={res['null_q95']:.2f})"
            ax[row, col].set_title(ttl)
    fig.suptitle("Topological face: the tidal loop is real; the lotto has none "
                 "(B5-B, registered)", y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_topology_diagrams.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 5: landmark topology recovery ----------------------------------
def fig_landmarks():
    rec = B5["recovery"]["curves"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for name, c, m in [("tidal_total_accel", "#1f6fb4", "o"),
                       ("lotto655_draw_sum", "#b03a3a", "x")]:
        ks = [100 * p["frac"] for p in rec[name]]
        ps = [p["median_p"] for p in rec[name]]
        ax.plot(ks, ps, color=c, marker=m, label=name)
    ax.axhline(0.05, color="k", ls="--", lw=1, label="α=0.05")
    ax.set_xlabel("farthest-first landmark fraction (%)")
    ax.set_ylabel("median permutation p (H1 persistence)")
    ax.set_title("Subset-to-whole topology (§4.4): the tidal loop is recoverable\n"
                 "from 20% landmarks; the lotto stays at the null at every k")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_landmark_topology_recovery.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 6: all five games, every per-game test -------------------------
def fig_allgames():
    AG = json.load(open(os.path.join(ROOT, "results", "relational_allgames.json")))
    keys = ["g42", "g45", "g49", "g55", "g58"]
    colors = ["#1f6fb4", "#5a9a68", "#c2702a", "#b03a3a", "#7b52a8"]
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for k, c in zip(keys, colors):
        g = AG[k]
        lab = g["game"].split()[-1]
        ks = [100 * p["frac"] for p in g["drawsum_recovery"]]
        ax[0].plot(ks, [p["mean_null_adjusted_z"] for p in g["drawsum_recovery"]],
                   color=c, marker="o", ms=3, label=lab)
        ax[1].plot(ks, [p["mean_null_adjusted_z"] for p in g["presence_recovery"]],
                   color=c, marker="o", ms=3, label=lab)
    for a, ttl in [(ax[0], "draw-sum temporal recovery"),
                   (ax[1], "presence-matrix frequency recovery")]:
        a.axhline(0, color="k", lw=1)
        a.axhspan(-2, 2, color="gray", alpha=0.15)
        a.set_xscale("log"); a.set_xticks([1, 2, 5, 10, 20, 40])
        a.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        a.set_xlabel("subset fraction k (%)")
        a.set_ylabel("null-adjusted z")
        a.set_ylim(-4, 4)
        a.set_title(ttl + "\n(±2z null band shaded)")
        a.legend(fontsize=8)
    # third panel: topology p and CCA p per game
    x = np.arange(len(keys))
    topo_p = [AG[k]["topology_h1"]["p"] for k in keys]
    cca_p = [AG[k]["cca_vs_covariates"]["p_shuffled_pairing"] for k in keys]
    w = 0.35
    ax[2].bar(x - w / 2, topo_p, w, color="#4878a8", label="H1 topology p")
    ax[2].bar(x + w / 2, cca_p, w, color="#5a9a68", label="CCA vs covariates p")
    ax[2].axhline(0.05, color="k", ls="--", lw=1, label="α=0.05")
    ax[2].set_xticks(x)
    ax[2].set_xticklabels([AG[k]["game"].split()[-1] for k in keys])
    ax[2].set_ylabel("permutation p")
    ax[2].set_ylim(0, 1.0)
    ax[2].set_title("per-game topology & draws-vs-physics CCA")
    ax[2].legend(fontsize=8)
    fig.suptitle("All five PCSO games, all per-game relational tests: "
                 "everything inside the null band (registered expectation)", y=1.04)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_allgames_null.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 7: lotto sub-dataset partition experiments (batch 6) ------------
def fig_subsets():
    S = json.load(open(os.path.join(ROOT, "results", "relational_subsets.json")))
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for a, key, ttl in [(ax[0], "mmd", "B6-1 cross-quarter MMD\n(30 quarter pairs, 5 games)"),
                        (ax[1], "spectra", "B6-2 cross-quarter co-occurrence spectra\n(30 quarter pairs)")]:
        ps = [p for g in S[key]["per_game"].values() for p in g.values()]
        a.hist(ps, bins=np.linspace(0, 1, 11), color="#4878a8", edgecolor="white")
        a.axhline(len(ps) / 10, color="k", ls="--", lw=1,
                  label="uniform expectation")
        a.set_xlabel("permutation p"); a.set_ylabel("count")
        a.set_title(ttl + f"\nmin p={S[key]['min_p']:.3f} vs Šidák {S[key]['sidak_threshold']:.4f} → joint NULL")
        a.legend(fontsize=8)
    h = S["halves"]["per_game"]
    games = list(h)
    short = [g.split()[-1] for g in games]
    corr = [h[g]["hot_number_corr"] for g in games]
    q95 = [h[g]["null_q95"] for g in games]
    x = np.arange(len(games))
    ax[2].bar(x, corr, color=["#4878a8"] * 3 + ["#b03a3a"] + ["#4878a8"])
    ax[2].plot(x, q95, "k_", ms=22, label="null 95% quantile")
    for i, g in enumerate(games):
        ax[2].annotate(f"p={h[g]['p']:.3f}", (x[i], corr[i]),
                       textcoords="offset points", xytext=(0, 6), ha="center",
                       fontsize=8)
    ax[2].set_xticks(x); ax[2].set_xticklabels(short)
    ax[2].set_ylabel("half-1 vs half-2 hot-number correlation")
    ax[2].set_title("B6-3 half-vs-half hot-number consistency\n"
                    "6/55 raw flag traces to #45 & #42 (C9 shadow);\n"
                    f"min p={S['halves']['min_p']:.3f} vs Šidák {S['halves']['sidak_threshold']:.4f} → joint NULL")
    ax[2].legend(fontsize=8)
    fig.suptitle("Batch 6 — lotto sub-dataset partitions: no segment shares structure "
                 "with any other beyond the common marginal law", y=1.06)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7_subset_partitions.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


# ---- Fig 8: atmospheric pressure experiments (batch 7 + baseline) --------
def fig_pressure():
    P = json.load(open(os.path.join(ROOT, "results", "relational_pressure.json")))
    B7 = json.load(open(os.path.join(ROOT, "results", "relational_batch7.json")))
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.5))
    # (a) pressure recovery curve
    ks = [100 * c["frac"] for c in P["HP1_pressure_recovery"]["curve"]]
    zs = [c["mean_null_adjusted_z"] for c in P["HP1_pressure_recovery"]["curve"]]
    ax[0, 0].plot(ks, zs, color="#1f6fb4", marker="o")
    ax[0, 0].axhspan(-2, 2, color="gray", alpha=0.15)
    ax[0, 0].set_xscale("log"); ax[0, 0].set_xticks([1, 2, 5, 10, 20, 40])
    ax[0, 0].get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax[0, 0].set_xlabel("subset fraction k (%)"); ax[0, 0].set_ylabel("null-adjusted z")
    ax[0, 0].set_title("H-P1: pressure subset-to-whole recovery\nstructured as registered (z→%.1f)" % zs[-1])
    # (b) seasonal partition MMD
    pairs = B7["seasons"]["pairs"]
    y = np.arange(len(pairs))
    ax[0, 1].barh(y, list(pairs.values()), color="#5a9a68")
    ax[0, 1].axvline(B7["seasons"]["sidak_threshold"], color="k", ls="--", lw=1,
                     label=f"Šidák {B7['seasons']['sidak_threshold']:.4f}")
    ax[0, 1].set_yticks(y); ax[0, 1].set_yticklabels(list(pairs))
    ax[0, 1].set_xlabel("MMD permutation p")
    ax[0, 1].set_title("B7-1: pressure quarters DIFFER (all p=0.01 floor)\n"
                       "positive control: same pipeline gave 30 nulls on lotto quarters")
    ax[0, 1].legend(fontsize=8)
    # (c) CCA couplings
    names = ["vs sun/moon\n(annual cycle)", "vs Kp\n(no mechanism)"] + \
            [f"draws {g.split()[-1]}" for g in P["HP2_per_game"]]
    rhos = [B7["cca"]["pressure_vs_sunmoon"]["heldout_rho1"],
            B7["cca"]["pressure_vs_kp"]["heldout_rho1"]] + \
           [v["cca_heldout_rho1"] for v in P["HP2_per_game"].values()]
    ps = [B7["cca"]["pressure_vs_sunmoon"]["p_shuffled_pairing"],
          B7["cca"]["pressure_vs_kp"]["p_shuffled_pairing"]] + \
         [v["cca_p"] for v in P["HP2_per_game"].values()]
    x = np.arange(len(names))
    cols = ["#5a9a68", "#4878a8"] + ["#4878a8"] * 5
    ax[1, 0].bar(x, rhos, color=cols)
    ax[1, 0].axhline(B7["cca"]["pressure_vs_sunmoon"]["null_q95"], color="k",
                     ls="--", lw=1, label="shuffled-pairing null q95 ≈ 0.14")
    for i, p in enumerate(ps):
        ax[1, 0].annotate(f"p={p:.3f}", (x[i], max(rhos[i], 0)),
                          textcoords="offset points", xytext=(0, 4), ha="center",
                          fontsize=7)
    ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels(names, fontsize=7)
    ax[1, 0].set_ylabel("held-out CCA ρ₁")
    ax[1, 0].set_title("H-P2/B7-2: pressure couples to the season (known mechanism),\n"
                       "not to Kp, and not to any game's draws")
    ax[1, 0].legend(fontsize=8)
    # (d) GW intrinsic geometry
    gw = B7["gw"]
    labels = list(gw)
    obs = [-gw[k]["score"] for k in labels]
    nul = [-gw[k]["null_mean"] for k in labels]
    x = np.arange(len(labels))
    w = 0.35
    ax[1, 1].bar(x - w / 2, obs, w, color="#b03a3a", label="observed GW distortion")
    ax[1, 1].bar(x + w / 2, nul, w, color="gray", label="matched-Gaussian null mean")
    for i, k in enumerate(labels):
        ax[1, 1].annotate(f"p={gw[k]['p']:.2f}", (x[i] - w / 2, obs[i]),
                          textcoords="offset points", xytext=(0, 4), ha="center",
                          fontsize=8)
    ax[1, 1].set_xticks(x)
    ax[1, 1].set_xticklabels([l.replace("|", "\nvs ") for l in labels], fontsize=8)
    ax[1, 1].set_ylabel("GW distortion (lower = more alignable)")
    ax[1, 1].set_title("B7-3 (first real GW run): tidal↔moon geometries align (p=0.05 floor);\n"
                       "pressure↔lotto null; pressure↔tidal: different shapes (exploratory)")
    ax[1, 1].legend(fontsize=8)
    fig.suptitle("Atmospheric pressure at the PCSO draw site — structured, seasonal, "
                 "physics-coupled, and unrelated to the draws", y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_pressure_experiments.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    which = sys.argv[1:] or ["admission", "recovery", "crossgame", "topology",
                             "landmarks", "allgames", "subsets", "pressure"]
    fns = {"admission": fig_admission, "recovery": fig_recovery,
           "crossgame": fig_crossgame, "topology": fig_topology,
           "landmarks": fig_landmarks, "allgames": fig_allgames,
           "subsets": fig_subsets, "pressure": fig_pressure}
    for w in which:
        fns[w]()
        print(w, "done", flush=True)
