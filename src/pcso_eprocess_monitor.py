#!/usr/bin/env python3
"""Anytime-valid sequential monitor for PCSO draws: a prequential predictive-likelihood evidence
process testing the uniform-draw null M₀.

Theory (Ramdas, Grunwald, Vovk, Shafer, "Game-Theoretic Statistics and Safe Anytime-Valid
Inference", arXiv:2210.01948, Sections 1.2, 2.2, 2.5, 3.2.2-3.2.3), in statistical terms:
  Null M0 (simple): every 6-set S is drawn uniformly, p0(S) = 1/C(P,6), independent over draws.
  Alternative: product-weight model f_w(S) = prod_{i in S} w_i / e_6(w) with w ~ Dirichlet(a),
  a = 100 fixed a priori (the lab's declared prior; Section 6.4: the analysis plan is fixed
  before the data, never selected after seeing outcomes).
  Prequential step (eq. 3-5 + Section 3.2.3 mixture method), using only past draws:
      Lambda_t = q_t(D_t) / p0(D_t),  q_t(S) = E_{w ~ Dir(a + counts_{<t})}[ f_w(S) ]
  (posterior-predictive density ratio; equals a Bayes-factor process, hence a nonnegative
  martingale with unit expectation under M0).
  Evidence process M_t = prod_{s<=t} Lambda_s. Ville's inequality: P(sup_t M_t >= 1/alpha) <=
  alpha — a sequential test with anytime-valid type-I error control, valid at every monitoring
  instant, including the weekly looks that the fixed-look Bonferroni monitor of the registered
  m=9 family does not cover.

In the prediction pipeline this is the inference/self-correction layer: the earliest statistically
valid detection of a departure from uniformity is exactly when the model-averaged predictor is
justified in shifting weight toward M1. JSON schema legacy key names: "unit_bet" = Lambda_t,
"wealth" = M_t (kept for byte-stability of committed artifacts).

This monitor tests uniformity of the draw mechanism (a simple null), NOT full exchangeability
(Section 5.5: the latter admits no nontrivial evidence martingale in the data filtration).

Two evidence processes per game, both prequential (predictive uses only past draws):
  full         : over all canonical draws, prior Dir(a) alone (learning from scratch).
  confirmation : over draws after the 2026-06-10 freeze; the predictive density uses the posterior
                 given all pre-freeze data (prior a + pre-freeze counts). Complements the
                 registered m=9 confirmation-set monitoring family with sequential validity.

Reads  datasets/pcso-lotto/data_draws_1yr.csv
Writes results/pcso_eprocess_monitor_<run_date>.json   (byte-deterministic for a given seed)
Usage: python3 src/pcso_eprocess_monitor.py [--seed 20260906] [--samples 4000] [--verify]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "datasets" / "pcso-lotto" / "data_draws_1yr.csv"
# Registered-artifact state (commit 9488a9a, PCSO refresh 2026-09-06): the last
# commit that set the canonical CSV before it grew again. With --verify the
# input is read from this snapshot so append-only growth cannot break the
# byte-exact --verify of the committed 2026-09-06 artifacts (same pattern as
# pcso_weekly_update.INPUT_SNAPSHOT_COMMIT, bea5121). Live runs (no --verify)
# always read the working tree.
INPUT_SNAPSHOT_COMMIT = "9488a9a18cbdd0a2b1bdd7580a41e78192fbd91b"
VERIFY_SNAPSHOT = False


def _draws_bytes() -> bytes:
    if not VERIFY_SNAPSHOT:
        return DRAWS.read_bytes()
    import subprocess
    rel = DRAWS.resolve().relative_to(ROOT).as_posix()
    run = subprocess.run(["git", "show", f"{INPUT_SNAPSHOT_COMMIT}:{rel}"],
                         cwd=ROOT, capture_output=True, check=False)
    if run.returncode != 0:
        raise ValueError(f"{rel}: cannot read input snapshot {INPUT_SNAPSHOT_COMMIT[:7]}: "
                         f"{run.stderr.decode('utf-8', 'replace').strip()}")
    return run.stdout
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
K = 6
A = 100.0            # Dirichlet concentration, fixed a priori (matches pcso_next_draw_posterior.py)
FREEZE = "2026-06-10"  # confirmation-set cutoff of the registered m=9 family
ALPHA_FAMILY = 0.05 / 9  # within-look level of the registered family; Ville threshold = 1/alpha


def esp6(w: np.ndarray) -> np.ndarray:
    """e_6(w) for each row of w (n x P), by the Newton recurrence over columns."""
    n, P = w.shape
    e = np.zeros((n, K + 1))
    e[:, 0] = 1.0
    for i in range(P):
        wi = w[:, i:i + 1]
        e[:, 1:] = e[:, 1:] + wi * e[:, :-1]
    return e[:, K]


def load_draws() -> dict[str, list[tuple[str, frozenset[int]]]]:
    import csv, io
    games: dict[str, list[tuple[str, frozenset[int]]]] = {g: [] for g in POOL}
    for row in csv.DictReader(io.StringIO(_draws_bytes().decode("utf-8"))):
            g = row["Game"]
            if g not in POOL:
                continue
            nums = frozenset(int(row[f"N{i}"]) for i in range(1, 7))
            assert len(nums) == K
            games[g].append((row["Date"], nums))
    for g in games:
        games[g].sort(key=lambda x: x[0])
    return games


def eprocess(draws: list[tuple[str, frozenset[int]]], P: int, a: float,
             start_counts: np.ndarray, rng: np.random.Generator, samples: int):
    """Prequential predictive-likelihood evidence process over `draws`;
    start_counts = pseudo-counts from prior+history."""
    counts = start_counts.astype(float).copy()
    C = comb(P, K)
    wealth_log = 0.0
    rows: list[dict] = []
    max_wealth = 1.0
    for date, S in draws:
        alpha = counts + a                       # Dir(a) prior + past counts (a in every coordinate)
        W = rng.dirichlet(alpha, size=samples)   # (samples x P)
        prod_w = np.ones(samples)
        for ball in S:
            prod_w *= W[:, ball - 1]
        q = float(np.mean(prod_w / esp6(W)))     # predictive density of this draw under M1-mixture
        p0 = 1.0 / C
        bet = q / p0
        wealth_log += float(np.log(bet))
        wealth = float(np.exp(min(wealth_log, 700.0)))
        max_wealth = max(max_wealth, wealth)
        counts += np.bincount([b - 1 for b in S], minlength=P)
        rows.append({"date": date, "draw": sorted(S), "unit_bet": round(bet, 6),
                     "wealth": round(wealth, 6)})
    return {"draws": len(draws), "final_wealth": rows[-1]["wealth"] if rows else 1.0,
            "max_wealth": round(max_wealth, 6),
            "anytime_p": round(1.0 / max_wealth, 8) if max_wealth > 1 else 1.0,
            "mean_log_bet": round(wealth_log / max(1, len(draws)), 6), "trajectory": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--samples", type=int, default=4000)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    global VERIFY_SNAPSHOT
    VERIFY_SNAPSHOT = args.verify  # verify target is always the registered Sep-6 artifact

    rng = np.random.default_rng(args.seed)
    games = load_draws()
    out = {
        "_meta": {
            "schema_version": 1,
            "script": "src/pcso_eprocess_monitor.py",
            "run_date": "2026-09-06",
            "seed": args.seed,
            "samples_per_draw": args.samples,
            "theory": "Ramdas, Grunwald, Vovk, Shafer arXiv:2210.01948 (SAVI): prequential "
                      "Bayes-factor e-process; Ville's inequality P(sup M_t >= 1/alpha) <= alpha",
            "null": "M0 simple uniform: p0(S) = 1/C(P,6) per draw, independent draws",
            "alternative": f"product-weight f_w(S)=prod w_i / e6(w), w ~ Dirichlet({A}) fixed a priori",
            "registration": "exploratory addendum to docs/RESULTS_PCSO_REFRESH_2026-09-06.md (r4); "
                            "NOT part of the frozen m=9 family; prior fixed a priori per arXiv:2210.01948 sec 6.4",
            "ville_threshold_1_over_alpha": round(1.0 / ALPHA_FAMILY, 1),
            "alpha_family": ALPHA_FAMILY,
            "freeze": FREEZE,
            "input_sha256": hashlib.sha256(_draws_bytes()).hexdigest(),
        },
        "games": {},
        "combined": {},
    }
    combined_log = {"full": 0.0, "confirmation": 0.0}
    for g, draws in games.items():
        P = POOL[g]
        zeros = np.zeros(P)
        full = eprocess(draws, P, A, zeros, rng, args.samples)
        pre_dates = [d for d, _ in draws if d <= FREEZE]
        pre_counts = np.zeros(P)
        for d, S in draws:
            if d <= FREEZE:
                for b in S:
                    pre_counts[b - 1] += 1
        assert int(pre_counts.sum()) == K * len(pre_dates)
        post = [(d, s) for d, s in draws if d > FREEZE]
        conf = eprocess(post, P, A, pre_counts, rng, args.samples)
        out["games"][g] = {"pool": P, "full_history": full, "confirmation_set": conf}
        combined_log["full"] += np.log(max(full["final_wealth"], 1e-300))
        combined_log["confirmation"] += np.log(max(conf["final_wealth"], 1e-300))
        print(f"{g}: full e={full['final_wealth']:.3f} (max {full['max_wealth']:.3f}), "
              f"confirmation e={conf['final_wealth']:.3f} (max {conf['max_wealth']:.3f})")
    for key, lg in combined_log.items():
        prod = float(np.exp(min(lg, 700.0)))
        out["combined"][key] = {"product_e_value": round(prod, 6),
                                "anytime_p": round(1.0 / prod, 8) if prod > 1 else 1.0,
                                "note": "product of independent per-game e-values (arXiv:2210.01948 sec 2.10)"}

    dest = ROOT / "results" / "pcso_eprocess_monitor_2026-09-06.json"
    payload = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.verify:
        if dest.exists() and dest.read_text() == payload:
            print(f"PASS sha256={hashlib.sha256(payload.encode()).hexdigest()[:16]}; wrote=none")
        else:
            print("VERIFY FAILED: output differs from committed file")
            raise SystemExit(1)
    else:
        dest.write_text(payload)
        print(f"wrote {dest.relative_to(ROOT)} sha256="
              f"{hashlib.sha256(payload.encode()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
