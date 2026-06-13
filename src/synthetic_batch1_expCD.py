"""Synthetic Batch 1, Experiments C (era half-life) and D (instrument power map).

Per docs/REGISTRATION_SYNTHETIC_BATCH1_CD.md (git 69d39e2,
sha256 380cc263da70e124..., approved by Cha 2026-06-13 with amendments 1-5).
Synthetic data only; no real lottery data is touched. Instrument identity is
shared with Experiment A by importing A's stats3 / p_mc verbatim.

C  (era half-life): tau in {25,50,100,200,400,800,inf}; n_e=400, n_c=200; R=200.
   delta0 = A's r=0.8 single-ball process (hot ball 17). Exploration detector =
   any of {I1 chi2, I2 max-dev, I3 graphon} at Sidak a'. Multi-fire (amend 2):
   carry the smallest-exploration-p instrument (ties I2>I1>I3) to ONE alpha=0.05
   confirmation re-test on continuation draws. S(tau) (amend 3) = survive/fired
   with an M5 guard at denominator<20. I4 = half_deviation_corr persistence over
   the full n_e+n_c span. Validity (amend 1): S(inf) must match the carried
   instrument's standalone alpha=0.05 power at n_c (fresh r=0.8 reference) within
   a 2-SE band and exceed the fair-continuation false-survival.
D  (power map): c in {0,1,2,4,8,16}, nested registered ball sets (amend 4),
   total mass = A's r=0.4 cell, n=800, R=200. Per-instrument power vs c at Sidak
   a'. c=0 FPR<=0.05. c=1 must match A's r=0.4/n=800 within a 2-SE band (amend 5).

Usage:  python synthetic_batch1_expCD.py C
        python synthetic_batch1_expCD.py D
Output: results/synthetic_batch1_expCD.json   Checkpoint: ..._expCD_CHECKPOINT.md
"""
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.discrete_draws import fast_draws, presence, half_deviation_corr
from core.stats import sidak
from domains import synthetic_lottery as sl
from synthetic_batch1_expA import stats3, p_mc, P0   # shared instrument identity

P, K, R, BALL = 55, 2000, 200, 17
ALPHA, M = 0.05, 3
APRIME = sidak(ALPHA, M)
MASTER = sl.MASTER_SEED

# C
NE, NC = 400, 200
TAUS = [25, 50, 100, 200, 400, 800, None]          # None == infinity (no decay)
R08 = 0.80                                          # delta0 = A's r=0.8 cell
ORDER = {1: 0, 0: 1, 2: 2}                          # tie-break: I2 > I1 > I3

# D
CS = [0, 1, 2, 4, 8, 16]
BALL_SETS = {                                       # nested, registered (amend 4)
    0: [],
    1: [17],
    2: [17, 38],
    4: [17, 38, 9, 46],
    8: [17, 38, 9, 46, 3, 22, 31, 52],
    16: [17, 38, 9, 46, 3, 22, 31, 52, 7, 14, 25, 33, 41, 48, 54, 11],
}
CMASS_R = 0.40                                      # total mass = A's r=0.4 cell

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "synthetic_batch1_expCD.json")
CKPT = os.path.join(HERE, "..", "results", "synthetic_batch1_expCD_CHECKPOINT.md")
AJSON = os.path.join(HERE, "..", "results", "synthetic_batch1_expA.json")


def ckpt(line):
    with open(CKPT, "a") as f:
        f.write(line + "\n")


def load_out():
    if os.path.exists(OUT):
        return json.load(open(OUT))
    return {"meta": {"P": P, "K": K, "R": R, "ball": BALL, "alpha": ALPHA,
                     "m": M, "alpha_prime": APRIME, "master_seed": MASTER,
                     "registration": "REGISTRATION_SYNTHETIC_BATCH1_CD.md "
                                     "(git 69d39e2, sha256 380cc263da70e124)",
                     "seed_scheme": "C: rng=default_rng(MASTER*10**6+300000+"
                                    "tau_index); D: +400000+c. nulls +999000+tag"},
            "C": {}, "D": {}}


def save(out):
    json.dump(out, open(OUT, "w"), indent=1)


# ------------------------------------------------------------------ C helpers

def detect(draws, null3):
    """Exploration family: per-instrument p, fired mask, raw stats."""
    s = stats3(draws)
    p = np.array([p_mc(s[j], null3[:, j]) for j in range(3)])
    return p, p <= APRIME, s


def carried_instrument(p, fired):
    """Smallest exploration p among fired; ties broken I2>I1>I3 (amend 2)."""
    cand = [j for j in range(3) if fired[j]]
    return min(cand, key=lambda j: (p[j], ORDER[j]))


def run_protocol(rng, spec, null_e, null_c):
    """One replicate: exploration detect -> carried confirmation re-test.
    Returns (any_fired, carried_or_-1, survived_bool, expl_draws, conf_draws)."""
    expl = sl.biased_draws(rng, NE, spec, t0=0)
    conf = sl.biased_draws(rng, NC, spec, t0=NE)        # continue decay clock
    p, fired, _ = detect(expl, null_e)
    if not fired.any():
        return False, -1, False, expl, conf
    j = carried_instrument(p, fired)
    sc = stats3(conf)
    survived = p_mc(sc[j], null_c[:, j]) <= ALPHA
    return True, j, survived, expl, conf


def run_C():
    out = load_out()
    t0 = time.time()
    # nulls (fair / uniform)
    re = np.random.default_rng(MASTER * 10**6 + 999000 + NE)
    rc = np.random.default_rng(MASTER * 10**6 + 999000 + NC)
    ri = np.random.default_rng(MASTER * 10**6 + 999000 + NE + NC)
    null_e = np.array([stats3(fast_draws(re, NE, P)) for _ in range(K)])
    null_c = np.array([stats3(fast_draws(rc, NC, P)) for _ in range(K)])
    null_i4 = np.array([half_deviation_corr(presence(fast_draws(ri, NE + NC, P), P), P)
                        for _ in range(K)])
    spec0 = sl.single_ball_spec(P, BALL, R08 * P0)       # no-decay r=0.8

    # symmetric calibration: fair-continuation control (zero bias)
    rngf = np.random.default_rng(MASTER * 10**6 + 300000 + 777)
    f_fired = f_surv = 0
    for _ in range(R):
        a, j, s, _, _ = run_protocol(rngf, sl.fair_spec(P), null_e, null_c)
        f_fired += a
        f_surv += (a and s)
    fair_fpr = f_fired / R
    fair_false_surv = (f_surv / f_fired) if f_fired else None

    # reference: carried-instrument standalone alpha=0.05 power at n_c, fresh r=0.8
    rngr = np.random.default_rng(MASTER * 10**6 + 300000 + 888)
    ref_hits = np.zeros((R, 3), bool)
    for rep in range(R):
        sc = stats3(sl.biased_draws(rngr, NC, spec0, t0=0))
        ref_hits[rep] = [p_mc(sc[j], null_c[:, j]) <= ALPHA for j in range(3)]
    ref_power = ref_hits.mean(0)                         # per-instrument

    out["C"] = {"null_n_e": NE, "null_n_c": NC, "delta0_r": R08,
                "fair_control": {"explore_fpr": fair_fpr,
                                 "confirm_false_survival": fair_false_surv,
                                 "n_fired": int(f_fired)},
                "ref_power_nc_r08_alpha05": {"I1": float(ref_power[0]),
                                             "I2": float(ref_power[1]),
                                             "I3": float(ref_power[2])},
                "cells": {}}

    for ti, tau in enumerate(TAUS):
        rng = np.random.default_rng(MASTER * 10**6 + 300000 + ti)
        spec = sl.with_decay(spec0, tau)
        n_fired = n_surv = 0
        carried_cnt = [0, 0, 0]
        i4_hits = 0
        for _ in range(R):
            a, j, s, expl, conf = run_protocol(rng, spec, null_e, null_c)
            if a:
                n_fired += 1
                carried_cnt[j] += 1
                n_surv += int(s)
            Z = presence(np.vstack([expl, conf]), P)
            i4_hits += int(p_mc(half_deviation_corr(Z, P), null_i4) <= ALPHA)
        S = (n_surv / n_fired) if n_fired >= 20 else None
        out["C"]["cells"][("inf" if tau is None else str(tau))] = {
            "tau": ("inf" if tau is None else tau),
            "explore_power": n_fired / R,
            "n_fired": n_fired, "n_survive": n_surv,
            "S": S, "S_guarded": (S is not None),
            "carried_counts": {"I1": carried_cnt[0], "I2": carried_cnt[1],
                               "I3": carried_cnt[2]},
            "I4_persistence_power": i4_hits / R}

    # tau_min = smallest FINITE tau with denom>=20 and S>=0.8
    tau_min = None
    for tau in [t for t in TAUS if t is not None]:
        c = out["C"]["cells"][str(tau)]
        if c["S_guarded"] and c["S"] is not None and c["S"] >= 0.8:
            tau_min = tau
            break

    # validity control at tau=inf (amend 1)
    inf = out["C"]["cells"]["inf"]
    S_inf = inf["S"]
    cc = inf["carried_counts"]
    tot = max(cc["I1"] + cc["I2"] + cc["I3"], 1)
    mix = (cc["I1"] * ref_power[0] + cc["I2"] * ref_power[1]
           + cc["I3"] * ref_power[2]) / tot               # carried-weighted ref
    def se2(pa, pb, na=R, nb=R):
        ph = (pa + pb) / 2
        return 2 * (ph * (1 - ph) * (1 / na + 1 / nb)) ** 0.5
    match_ref = (S_inf is not None) and abs(S_inf - mix) <= se2(S_inf, mix)
    above_null = (S_inf is not None) and (fair_false_surv is not None) and \
                 (S_inf - fair_false_surv) > se2(S_inf, fair_false_surv)
    out["C"]["tau_min"] = tau_min
    out["C"]["validity_tau_inf"] = {
        "S_inf": S_inf, "carried_weighted_ref": float(mix),
        "match_ref_within_2se": bool(match_ref),
        "fair_false_survival": fair_false_surv,
        "above_null_2se": bool(above_null),
        "PASS": bool(match_ref and above_null)}
    save(out)
    ckpt(f"[done] expC tau-grid (R={R},K={K}) {time.time()-t0:.0f}s | "
         f"tau_min={tau_min} | validity_inf "
         f"PASS={out['C']['validity_tau_inf']['PASS']}")
    print(json.dumps(out["C"], indent=1))


# ------------------------------------------------------------------ D

def spec_for_c(c):
    if c == 0:
        return sl.fair_spec(P)
    if c == 1:
        return sl.single_ball_spec(P, BALL, CMASS_R * P0)
    return sl.multi_ball_spec(P, BALL_SETS[c], CMASS_R * P0)   # per-ball = total/c


def run_D():
    out = load_out()
    t0 = time.time()
    rng0 = np.random.default_rng(MASTER * 10**6 + 999000 + 800)
    null_d = np.array([stats3(fast_draws(rng0, 800, P)) for _ in range(K)])
    A = json.load(open(AJSON))["cells"]["800"]["0.4"]          # reference cell
    a_pow = [A["power_I1"], A["power_I2"], A["power_I3"]]

    out["D"] = {"n": 800, "mass_r": CMASS_R, "ball_sets": BALL_SETS,
                "A_ref_r0.4_n800": {"I1": a_pow[0], "I2": a_pow[1],
                                    "I3": a_pow[2]}, "cells": {}}
    for c in CS:
        rng = np.random.default_rng(MASTER * 10**6 + 400000 + c)
        spec = spec_for_c(c)
        dhat = sl.realized_delta(spec, K=200_000) if c > 0 else np.zeros(P)
        hits = np.zeros((R, 3), bool)
        for rep in range(R):
            s = stats3(sl.biased_draws(rng, 800, spec))
            hits[rep] = [p_mc(s[j], null_d[:, j]) <= APRIME for j in range(3)]
        pw = hits.mean(0)
        out["D"]["cells"][str(c)] = {
            "c": c, "balls": BALL_SETS[c],
            "power_I1": float(pw[0]), "power_I2": float(pw[1]),
            "power_I3": float(pw[2]),
            "max_realized_delta": float(np.abs(dhat).max())}

    # c=0 FPR control + c=1 consistency vs A (2-SE band, amend 5)
    c0 = out["D"]["cells"]["0"]
    fpr_ok = all(c0[f"power_I{j+1}"] <= 0.05 for j in range(3))
    c1 = out["D"]["cells"]["1"]
    def se2(pa, pb):
        ph = (pa + pb) / 2
        return 2 * (ph * (1 - ph) * (2.0 / R)) ** 0.5
    band = {f"I{j+1}": {"p_D": c1[f"power_I{j+1}"], "p_A": a_pow[j],
                        "diff": abs(c1[f"power_I{j+1}"] - a_pow[j]),
                        "tol_2se": se2(c1[f"power_I{j+1}"], a_pow[j]),
                        "PASS": abs(c1[f"power_I{j+1}"] - a_pow[j])
                        <= se2(c1[f"power_I{j+1}"], a_pow[j])}
            for j in range(3)}
    out["D"]["validity"] = {
        "c0_fpr_ok": bool(fpr_ok),
        "c0_fpr": {f"I{j+1}": c0[f"power_I{j+1}"] for j in range(3)},
        "c1_consistency": band,
        "PASS": bool(fpr_ok and all(b["PASS"] for b in band.values()))}
    save(out)
    ckpt(f"[done] expD c-grid {{0..16}} (R={R},K={K}) {time.time()-t0:.0f}s | "
         f"validity PASS={out['D']['validity']['PASS']}")
    print(json.dumps(out["D"], indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "C":
        run_C()
    elif cmd == "D":
        run_D()
    else:
        print("usage: python synthetic_batch1_expCD.py [C|D]")
