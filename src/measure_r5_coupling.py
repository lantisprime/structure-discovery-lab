#!/usr/bin/env python3
"""H-protocol measurement: R5 cross-game spectra vs hit-count-cooc (λ_max).

Closes the audit G-5 headline gap ("R5-vs-graphon/MP coupling — the
#45-reshadowing risk — still unmeasured"; families.json 'graph' entry).

Question: under H0, is the R5 pair statistic (−L2 distance between two
games' standardized top-10 co-occurrence spectra) correlated with the
member games' within-game λ_max? If strongly, a within-game co-occurrence
anomaly (the #45 class) mechanically re-fires the cross-game instrument —
the C9 scenario — and the two families must merge or every R5 flag must
row-trace against the cooccurrence family.

Design (Algorithm H-2 pattern): N_SIM shared synthetic H0 batteries of all
5 games (real per-game T and P); per battery compute per-game λ_max and all
10 R5 pair statistics; Spearman correlations:
  (a) pair-stat vs λ_max of each member game (pooled over 10 pairs);
  (b) pair-stat vs max(λ_max of members) — the flag-relevant functional;
  (c) per-game 'presence' aggregate: min pair-stat involving g vs λ_max(g).
Also a DIRECT re-shadow probe: inject a planted pair-affinity excess (one
hot ball pair boosted in one game, #45-style) at 3 strengths and measure
how often R5 pairs involving that game go extreme while H0 calibration for
the OTHER pairs is preserved.

Scope: measured at real (T,P) per game; same caveat as families.json.
Output: results/r5_coupling_measurement.json
"""
import json
import os
import sys

import numpy as np
from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

from relational_batch5 import (GameSpec, uniform_draws, spec_distance,  # noqa: E402
                               load_games)

SEED = 20260712
N_SIM = 200
INJECT_TRIALS = 60


def battery(rng, specs):
    draws = {g: uniform_draws(rng, gs.T, gs.P) for g, gs in specs.items()}
    return stats_of(draws, specs)


def stats_of(draws, specs):
    spec, lmax = {}, {}
    for g, gs in specs.items():
        s, l = gs.spectrum(draws[g])
        spec[g], lmax[g] = s, l
    games = list(specs)
    pair = {}
    for i, a in enumerate(games):
        for b in games[i + 1:]:
            pair[f"{a}|{b}"] = -spec_distance(spec[a], spec[b])
    return lmax, pair


def inject_pair_affinity(rng, gs, boost):
    """#45-style excess: draws where a designated hot pair co-occurs with
    probability inflated by `boost` (rejection-boosting)."""
    hot = (1, 2)     # arbitrary designated pair (relabeling symmetry under H0)
    out = np.empty((gs.T, 6), dtype=int)
    for t in range(gs.T):
        d = np.sort(rng.choice(gs.P, size=6, replace=False)) + 1
        if rng.random() < boost:
            d = np.unique(np.concatenate([np.array(hot),
                                          rng.choice(gs.P, size=6,
                                                     replace=False) + 1]))[:6]
            while len(d) < 6:
                extra = rng.integers(1, gs.P + 1)
                if extra not in d:
                    d = np.sort(np.append(d, extra))
        out[t] = np.sort(d)[:6]
    return out


def main():
    rng = np.random.default_rng(SEED)
    real = load_games()
    specs = {g: GameSpec(rng, len(nums), P, g) for g, (nums, P) in real.items()}
    games = list(specs)

    # ---- (a-c) H0 coupling ------------------------------------------------
    L, PAIRS = [], []
    for _ in range(N_SIM):
        lmax, pair = battery(rng, specs)
        L.append(lmax)
        PAIRS.append(pair)
    pooled_stat, pooled_lmax_a, pooled_lmax_max = [], [], []
    for lmax, pair in zip(L, PAIRS):
        for k, v in pair.items():
            a, b = k.split("|")
            pooled_stat.append(v)
            pooled_lmax_a.append(lmax[a])
            pooled_lmax_max.append(max(lmax[a], lmax[b]))
    rho_member = float(st.spearmanr(pooled_stat, pooled_lmax_a)[0])
    rho_max = float(st.spearmanr(pooled_stat, pooled_lmax_max)[0])
    per_game_presence = {}
    for g in games:
        pres = [min(v for k, v in pair.items() if g in k) for pair in PAIRS]
        lm = [lmax[g] for lmax in L]
        per_game_presence[g] = round(float(st.spearmanr(pres, lm)[0]), 3)

    # ---- direct re-shadow probe --------------------------------------------
    target = "Grand Lotto 6/55"
    null_pairs = {k: sorted(p[k] for p in PAIRS) for k in PAIRS[0]}

    def pair_pct(k, v):
        arr = null_pairs[k]
        return (1 + sum(x >= v for x in arr)) / (len(arr) + 1)   # upper-tail p

    probe = {}
    for boost in (0.0, 0.15, 0.35):
        hits_target, hits_other, lmax_ps = 0, 0, []
        for _ in range(INJECT_TRIALS):
            draws = {g: uniform_draws(rng, gs.T, gs.P)
                     for g, gs in specs.items()}
            draws[target] = inject_pair_affinity(rng, specs[target], boost)
            lmax, pair = stats_of(draws, specs)
            lmax_null = sorted(l[target] for l in L)
            lmax_ps.append((1 + sum(x >= lmax[target] for x in lmax_null))
                           / (len(lmax_null) + 1))
            for k, v in pair.items():
                p = pair_pct(k, v)
                if p <= 0.05:
                    if target in k:
                        hits_target += 1
                    else:
                        hits_other += 1
        probe[f"boost_{boost}"] = {
            "lambda_max_median_p": float(np.median(lmax_ps)),
            "r5_target_pair_flag_rate": round(hits_target / (INJECT_TRIALS * 4), 3),
            "r5_other_pair_flag_rate": round(hits_other / (INJECT_TRIALS * 6), 3)}

    out = {"seed": SEED, "n_sim": N_SIM, "inject_trials": INJECT_TRIALS,
           "scope": "real per-game (T,P); same caveat as families.json",
           "h0_coupling": {
               "spearman_pairstat_vs_member_lmax": round(rho_member, 3),
               "spearman_pairstat_vs_max_member_lmax": round(rho_max, 3),
               "per_game_presence_vs_lmax": per_game_presence},
           "reshadow_probe_655_planted_pair_affinity": probe,
           "interpretation_rule": ("|rho| >= 0.90 -> merge families; "
                                   "0.5-0.9 -> reported coupling + mandatory "
                                   "row-trace; < 0.5 AND probe target-rate ~ "
                                   "other-rate -> independent")}
    path = os.path.join(ROOT, "results", "r5_coupling_measurement.json")
    json.dump(out, open(path, "w"), indent=2)
    print(json.dumps(out["h0_coupling"], indent=1))
    print(json.dumps(out["reshadow_probe_655_planted_pair_affinity"], indent=1))
    print("written", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
