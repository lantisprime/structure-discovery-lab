#!/usr/bin/env python3
"""v2: Robust sequential inference layer for the PCSO prediction pipeline — mixture-prior
prequential evidence process, plus an e-detector for draw-mechanism drift.

Scientific basis (latest arXiv research applied to the lab's documented weaknesses):
1. Ramdas, Grunwald, Vovk, Shafer, "Game-Theoretic Statistics and Safe Anytime-Valid Inference",
   arXiv:2210.01948 —
   * §3.2.2-3.2.4 (mixture method; Grünwald-De Heide-Koolen REGROW): when the alternative is
     uncertain, spread it with a fixed a-priori mixture R; the prequential predictive density
     under R is a proper probability model on sequences and its likelihood ratio vs the null is
     a nonnegative martingale (a Bayes-factor process, §3.2.3) — log-optimal in the worst-case
     growth-rate sense. Averaging accumulated e-processes (§2.9) is the companion robustifier.
   * §2.5 Ville's inequality: P(sup_t E_t >= 1/alpha) <= alpha — anytime-valid type-I error
     control at every monitoring instant.
   * §5.7 (Shin-Ramdas-Rinaldo e-detectors): D_t = sum of e-processes restarted at successive
     times is an e-detector; stopping at threshold 1/alpha has expected false-alarm run length
     >= 1/alpha — sequential changepoint detection with proven control.
2. Lab motivation (docs/RESULTS_PCSO_REFRESH_2026-09-06.md §8): the BF_01 direction reverses
   between a=10 (lean M0) and a=100 (lean M1) — the single-concentration inference layer was
   prior-sensitive. Here the predictive prior is R = uniform over a in {10, 30, 100, 300, 1000},
   fixed a priori (§6.4 discipline: never selected after seeing outcomes). The mixture removes
   single-concentration sensitivity by construction: the evidence process grows whenever ANY
   component of the alternative fits, and no component is discarded post hoc.

Role in the prediction pipeline: the self-correction/inference layer. The mixture evidence
process is the sequential quantity that determines, with valid error control at every monitoring
instant, when the model-averaged predictor is justified in shifting weight from the uniform
model M0 toward the tilted model M1; the e-detector watches for changes in the draw mechanism.
It does not alter the ticket generator.

Reads  datasets/pcso-lotto/data_draws_1yr.csv
Writes results/pcso_eprocess_monitor_v2_2026-09-06.json  (byte-deterministic for a given seed)
Usage: python3 src/pcso_eprocess_monitor_v2.py [--seed 20260906] [--samples 4000] [--verify]
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
FREEZE = "2026-06-10"
ALPHA_FAMILY = 0.05 / 9                       # within-look level of the registered m=9 family
GRID = [10.0, 30.0, 100.0, 300.0, 1000.0]     # fixed a priori, equal mixture weights
RESTART_EVERY = 13                            # e-detector restart cadence (~monthly per game)


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


def mixture_ratio(draw: frozenset[int], P: int, counts: np.ndarray, rng, samples: int) -> float:
    """Mixture-prior predictive likelihood ratio Lambda_t = q_R(D_t)/p0 for one draw, where
    q_R(S) = (1/|GRID|) sum_a E_{w ~ Dir(a + counts)}[ f_w(S) ]  (mixture method, sec 3.2.2)."""
    p0 = 1.0 / comb(P, K)
    q = 0.0
    for a in GRID:
        W = rng.dirichlet(counts + a, size=samples)
        prod_w = np.ones(samples)
        for ball in draw:
            prod_w *= W[:, ball - 1]
        q += float(np.mean(prod_w / esp6(W)))
    return (q / len(GRID)) / p0


def run_mix(draws, P, start_counts, rng, samples):
    """Mixture-prior prequential evidence process over `draws` (predictive uses only past draws).
    Also reports the per-concentration component evidence values for transparency."""
    counts = start_counts.astype(float).copy()
    log_e, mx, per_a_log = 0.0, 1.0, np.zeros(len(GRID))
    per_a_max = np.ones(len(GRID))
    for _, S in draws:
        p0 = 1.0 / comb(P, K)
        q_a = np.zeros(len(GRID))
        for j, a in enumerate(GRID):
            W = rng.dirichlet(counts + a, size=samples)
            prod_w = np.ones(samples)
            for ball in S:
                prod_w *= W[:, ball - 1]
            q_a[j] = float(np.mean(prod_w / esp6(W)))
        lam_mix = float(q_a.mean()) / p0
        lam_a = q_a / p0
        log_e += np.log(max(lam_mix, 1e-300))
        per_a_log += np.log(np.maximum(lam_a, 1e-300))
        mx = max(mx, float(np.exp(min(log_e, 700.0))))
        per_a_max = np.maximum(per_a_max, np.exp(np.minimum(per_a_log, 700.0)))
        counts += np.bincount([b - 1 for b in S], minlength=P)
    T = len(draws)
    final = float(np.exp(min(log_e, 700.0))) if T else 1.0
    return {"draws": T,
            "per_concentration": {str(int(a)): {"final": (round(float(np.exp(min(per_a_log[i], 700.0))), 6) if T else 1.0),
                                                  "max": round(float(per_a_max[i]), 6)}
                                  for i, a in enumerate(GRID)},
            "mixture_final": round(final, 6), "mixture_max": round(mx, 6),
            "anytime_p": round(1.0 / mx, 8) if mx > 1 else 1.0}


def edetector(draws, P, start_counts, rng, samples):
    """Shin-Ramdas-Rinaldo e-detector (sec 5.7): D_t = sum of mixture e-processes restarted
    every RESTART_EVERY draws. Under a stationary null, the stopping rule tau* = inf{t: D_t >=
    1/alpha} has E[tau*] >= 1/alpha (false-alarm control); a true mechanism change forces D_t
    upward from the restarts that straddle the change."""
    thresh = 1.0 / ALPHA_FAMILY
    counts_runs: dict[int, np.ndarray] = {}
    val: dict[int, float] = {}
    D, dmax, stop_t = 0.0, 1.0, None
    for t in range(len(draws)):
        if t % RESTART_EVERY == 0:
            counts_runs[t] = start_counts.astype(float).copy()
            val[t] = 1.0
        S = draws[t][1]
        for s in list(counts_runs):
            lam = mixture_ratio(S, P, counts_runs[s], rng, samples)
            val[s] *= lam
            counts_runs[s] += np.bincount([b - 1 for b in S], minlength=P)
        D = sum(val.values())
        if D > dmax:
            dmax = D
        if stop_t is None and D >= thresh:
            stop_t = t + 1
    return {"restarts": len(counts_runs), "detector_final": round(D, 6),
            "detector_max": round(dmax, 6), "threshold_1_over_alpha": round(thresh, 1),
            "stop_at_family_alpha": stop_t,
            "expected_false_alarm_run_draws": round(thresh, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--samples", type=int, default=4000)
    ap.add_argument("--detector-samples", type=int, default=600)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    global VERIFY_SNAPSHOT
    VERIFY_SNAPSHOT = args.verify  # verify target is always the registered Sep-6 artifact

    rng = np.random.default_rng(args.seed)
    games = load_draws()
    out = {
        "_meta": {
            "schema_version": 2,
            "script": "src/pcso_eprocess_monitor_v2.py",
            "run_date": "2026-09-06",
            "seed": args.seed,
            "samples_per_draw": args.samples,
            "detector_samples_per_draw": args.detector_samples,
            "theory": "arXiv:2210.01948: mixture-prior prequential evidence process "
                      "(sec 3.2.2-3.2.4 mixture method / REGROW robustness) + "
                      "Shin-Ramdas-Rinaldo e-detector (sec 5.7); Ville anytime-valid type-I control",
            "null": "M0 simple uniform: p0(S) = 1/C(P,6) per draw, independent draws",
            "alternative": f"product-weight f_w(S)=prod w_i / e6(w), predictive prior "
                           f"R = uniform over Dir(a), a in {GRID}, fixed a priori",
            "motivation": "lab BF prior-sensitivity (docs/RESULTS_PCSO_REFRESH_2026-09-06.md sec 8): "
                          "mixture removes single-concentration sensitivity by construction",
            "registration": "exploratory addendum (r5) to docs/RESULTS_PCSO_REFRESH_2026-09-06.md; "
                            "NOT part of the frozen m=9 family; grid and weights fixed a priori",
            "alpha_family": ALPHA_FAMILY,
            "freeze": FREEZE,
            "input_sha256": hashlib.sha256(_draws_bytes()).hexdigest(),
        },
        "games": {},
        "combined": {},
    }
    log_mix = {"full": 0.0, "confirmation": 0.0}
    for g, draws in games.items():
        P = POOL[g]
        full = run_mix(draws, P, np.zeros(P), rng, args.samples)
        pre = np.zeros(P)
        for d, S in draws:
            if d <= FREEZE:
                for b in S:
                    pre[b - 1] += 1
        post = [(d, S) for d, S in draws if d > FREEZE]
        conf = run_mix(post, P, pre, rng, args.samples)
        det = edetector(post, P, pre, np.random.default_rng(args.seed + 1),
                         args.detector_samples)
        out["games"][g] = {"pool": P, "full_history": full, "confirmation_set": conf,
                           "e_detector": det}
        log_mix["full"] += np.log(max(full["mixture_final"], 1e-300))
        log_mix["confirmation"] += np.log(max(conf["mixture_final"], 1e-300))
        print(f"{g}: mix full e={full['mixture_final']:.3f} (max {full['mixture_max']:.3f}), "
              f"conf e={conf['mixture_final']:.3f} (max {conf['mixture_max']:.3f}), "
              f"detector max={det['detector_max']:.2f} (thresh {det['threshold_1_over_alpha']})")
    for key, lg in log_mix.items():
        # product of independent per-game mixture e-values (arXiv:2210.01948 sec 2.10)
        prod = float(np.exp(min(lg, 700.0)))
        out["combined"][key] = {"product_e_value": round(prod, 6),
                                "anytime_p": round(1.0 / prod, 8) if prod > 1 else 1.0}

    dest = ROOT / "results" / "pcso_eprocess_monitor_v2_2026-09-06.json"
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
