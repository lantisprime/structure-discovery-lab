#!/usr/bin/env python3
"""Picker calibration: selection-bias correction of the ticket multipliers (EVALUATION_PROTOCOL H5)
and the model weight pi_1 from held-out predictive evidence — G0 exploratory.

Theory.
1. Selection inflation (order statistics). Ticket A is the six largest ball counts and ticket B
   ranks 7-12, each scored by R(S) = C(P,6) E[f_w(S) | D] on the SAME data used to select it.
   Under the uniform model M0 every history-based rule has true R = 1, yet the reported R of a
   count-selected set is > 1: to first order R_null ~ exp(sigma_c s_6 / (a + c_bar)), s_6 the
   expected sum of the top six of P standard normals. H5 makes the raw value inadmissible: report
   log R_obs - E_0[log R] with a Monte Carlo interval. Here E_0 is estimated by re-running the
   predictor of src/pcso_next_draw_posterior.py (a = 100, importance sampling) on NSIM uniform
   histories of the same length; the selection-corrected multiplier is
   R_c = exp(log R_obs - E_0[log R]) and the one-sided null tail p = P_0(R >= R_obs). The log-space
   correction divides by the geometric mean of R under M0 (the convention for a multiplier).
2. Model weight (predictive likelihood). The prequential evidence of the SAME model that R_c is
   computed under (a = 100, exact product-weight posterior by importance sampling) on the
   post-freeze draws: e = prod_t q_t(S_t)/p0(S_t), q_t(S) = E_{w ~ p(w | D_<t)}[f_w(S)]. Each q_t
   is a self-normalised mixture of normalised f_w, drawn before S_t is used, so e is a valid
   evidence value under M0 whatever the Monte Carlo error. With equal model odds at the freeze,
   pi_1 = e / (1 + e), and the picker's multiplier becomes R_eff = pi_0 + pi_1 R_c. (Referee
   GLM 5.3, 2026-09-23: the v2 monitor's mixture-over-a pseudo-posterior evidence is kept for
   comparison only, because it belongs to a different M1.)

Reads  datasets/pcso-lotto/data_draws_1yr.csv (rows up to each game's last_draw in the posterior JSON),
       results/pcso_next_draw_posterior_<run_date>.json, results/pcso_eprocess_monitor_v2_<run_date>.json
Writes results/pcso_picker_calibration_<run_date>.json  (byte-deterministic for a given seed)
Usage: python3 src/pcso_picker_calibration.py [--run-date 2026-09-21] [--nsim 200] [--samples 20000] [--verify]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np

from pcso_next_draw_posterior import K, esp

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "datasets" / "pcso-lotto" / "data_draws_1yr.csv"
PRIOR_A = 100.0          # the predictor's fixed a-priori concentration (pcso_next_draw_posterior.py)
FREEZE = "2026-06-10"    # exploration/confirmation boundary (DATASET.md §6)


def heldout_evidence(rng, draws: list[list[int]], dates: list[str], P: int, samples: int) -> float:
    """log e = sum over post-freeze draws of log[q_t(S_t) / p0], q_t from the exact a = 100 posterior on D_<t."""
    C = math.comb(P, K)
    log_e = 0.0
    for t in range(len(draws)):
        if dates[t] <= FREEZE:
            continue
        c = np.bincount(np.array(draws[:t]).ravel() - 1, minlength=P).astype(float)
        w = rng.gamma(PRIOR_A + c, 1.0, size=(samples, P))
        w /= w.sum(1, keepdims=True)
        E = esp(w)
        logwt = -t * (np.log(E[:, K]) + K * math.log(P) - math.log(C))
        wt = np.exp(logwt - logwt.max())
        wt /= wt.sum()
        idx = np.array(draws[t]) - 1
        log_e += math.log(float(np.sum(wt * np.prod(w[:, idx], axis=1) / E[:, K])) * C)
    return log_e


def null_log_R(rng, P: int, T: int, nsim: int, samples: int) -> tuple[np.ndarray, np.ndarray]:
    """log R of the count-selected ticket A (ranks 1-6) and B (ranks 7-12) on nsim uniform histories."""
    C = math.comb(P, K)
    la, lb = np.empty(nsim), np.empty(nsim)
    for s in range(nsim):
        picks = np.argsort(rng.random((T, P)), axis=1)[:, :K]          # T uniform 6-subsets
        c = np.bincount(picks.ravel(), minlength=P).astype(float)
        w = rng.gamma(PRIOR_A + c, 1.0, size=(samples, P))
        w /= w.sum(1, keepdims=True)
        E = esp(w)
        logwt = -T * (np.log(E[:, K]) + K * math.log(P) - math.log(C))
        wt = np.exp(logwt - logwt.max())
        wt /= wt.sum()
        order = np.lexsort((np.arange(P), -c))                           # same tie rule as the predictor
        for idx, dst in ((order[:K], la), (order[K:2 * K], lb)):
            dst[s] = math.log(float(np.sum(wt * C * np.prod(w[:, idx], axis=1) / E[:, K])))
    return la, lb


def corrected(R_obs: float, lr: np.ndarray, pi1: float) -> dict:
    m, se = float(lr.mean()), float(lr.std(ddof=1) / math.sqrt(len(lr)))
    d = math.log(R_obs) - m
    Rc = math.exp(d)
    return {"R_reported": R_obs,
            "null_mean_log_R": round(m, 5), "null_mean_log_R_mc_se": round(se, 5),
            "null_R_5_95": [round(float(np.exp(np.quantile(lr, 0.05))), 4), round(float(np.exp(np.quantile(lr, 0.95))), 4)],
            "log_R_minus_null_mean": round(d, 5),
            "log_R_minus_null_mean_95_mc": [round(d - 1.96 * se, 5), round(d + 1.96 * se, 5)],
            "R_selection_corrected": round(Rc, 4),
            "null_tail_p_R_ge_observed": round((1 + int(np.sum(lr >= math.log(R_obs)))) / (len(lr) + 1), 4),
            "R_eff": round((1 - pi1) + pi1 * Rc, 4)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--run-date", default="2026-09-21")
    ap.add_argument("--nsim", type=int, default=1000)
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    post_p = ROOT / "results" / f"pcso_next_draw_posterior_{args.run_date}.json"
    mon_p = ROOT / "results" / f"pcso_eprocess_monitor_v2_{args.run_date}.json"
    post, mon = json.loads(post_p.read_text()), json.loads(mon_p.read_text())
    by = {}
    for row in csv.DictReader(io.StringIO(DRAWS.read_bytes().decode("utf-8-sig"))):
        by.setdefault(row["Game"], []).append((row["Date"], [int(row[f"N{i}"]) for i in range(1, 7)]))
    used = []                                   # rows up to each game's last_draw: append-only growth cannot change the output
    rng = np.random.default_rng(args.seed)
    games = {}
    for g in sorted(post["games"]):
        r = post["games"][g]
        P, T = r["pool"], r["draws"]
        rows = sorted(x for x in by[g] if x[0] <= r["last_draw"])
        if len(rows) != T:
            raise SystemExit(f"{g}: {len(rows)} draws up to {r['last_draw']}, posterior JSON has {T}")
        used += [f"{g},{d},{'-'.join(map(str, s))}" for d, s in rows]
        log_e = heldout_evidence(rng, [s for _, s in rows], [d for d, _ in rows], P, args.samples)
        e = math.exp(log_e)
        pi1 = e / (1.0 + e)
        la, lb = null_log_R(rng, P, T, args.nsim, args.samples)
        games[g] = {"pool": P, "draws": T,
                    "heldout_draws": sum(1 for d, _ in rows if d > FREEZE),
                    "heldout_evidence_e_exact_a100": round(e, 4),
                    "heldout_evidence_e_v2_mixture_for_comparison": float(mon["games"][g]["confirmation_set"]["mixture_final"]),
                    "pi1_tilted_model": round(pi1, 4),
                    "ticket_A": {"set": r["maximum_predictive_set"]["set"],
                                 **corrected(r["maximum_predictive_set"]["R_posterior_mean"], la, pi1)},
                    "ticket_B": {"set": r["second_disjoint_set_ranks_7_12"]["set"],
                                 **corrected(r["second_disjoint_set_ranks_7_12"]["R_posterior_mean"], lb, pi1)}}
    out = {"_meta": {"schema_version": 1, "script": "src/pcso_picker_calibration.py", "run_date": args.run_date,
                     "seed": args.seed, "nsim": args.nsim, "samples": args.samples, "prior_concentration": PRIOR_A,
                     "rule": "EVALUATION_PROTOCOL.md H5 (estimator-bias subtraction) + prequential model weight",
                     "pi1_definition": "e/(1+e), e = post-freeze prequential evidence of the exact a=100 product-weight posterior (equal model odds at the 2026-06-10 freeze)",
                     "R_eff_definition": "pi0 + pi1 * R_selection_corrected; P(win) = R_eff / C(P,6)",
                     "R_c_convention": "log-space: R_obs divided by the geometric mean of R under M0",
                     "input_sha256": {**{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in (post_p, mon_p)},
                                      "draw_rows_used": hashlib.sha256("\n".join(used).encode()).hexdigest()},
                     "grade": "G0 exploratory"},
           "games": games}
    payload = (json.dumps(out, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    dst = ROOT / "results" / f"pcso_picker_calibration_{args.run_date}.json"
    if args.verify:
        if dst.read_bytes() != payload:
            raise SystemExit(f"VERIFY MISMATCH: {dst}")
        print(f"PASS sha256={hashlib.sha256(payload).hexdigest()}; wrote=none")
        return
    dst.write_bytes(payload)
    print(f"wrote {dst.relative_to(ROOT)} sha256={hashlib.sha256(payload).hexdigest()}")
    for g, r in games.items():
        a = r["ticket_A"]
        print(f"{g:18s} R={a['R_reported']} null E[R]~{math.exp(a['null_mean_log_R']):.3f} "
              f"Rc={a['R_selection_corrected']} p={a['null_tail_p_R_ge_observed']} pi1={r['pi1_tilted_model']} R_eff={a['R_eff']}")


if __name__ == "__main__":
    main()
