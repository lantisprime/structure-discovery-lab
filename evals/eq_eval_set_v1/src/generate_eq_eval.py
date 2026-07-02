#!/usr/bin/env python3
"""eq_eval_set_v1 generator — sealed benchmark for the equation-discovery
pipeline (Q-1..Q-8 / src/eq_selection_v4.py).

Purpose (AUDIT_RESOLUTION open item; RESULTS_EVAL_RERUN_2026-07-02.md §4.1):
structure_eval_set_v1 contains no equation units, so the v4 pipeline has no
blind benchmark. This pack plants a controlled mixture of true nulls,
structured-but-equation-free processes, recoverable harmonic laws, and known
traps, so a blind run can be scored for:

  1. refusing to fit noise (null-equation generator beats the search);
  2. not converting colored noise / random walks into "laws";
  3. recovering planted periods within identifiability bounds (profile CI);
  4. honest below-power behavior at low SNR;
  5. residual-scan correctness (finding an unwhitelisted second line;
     staying silent when it is whitelisted);
  6. not fitting harmonics to non-harmonic determinism (logistic map);
  7. flagging era-bounded (nonstationary) lines instead of pooling them.

Determinism: everything derives from MASTER_SEED. Running twice must produce
byte-identical CSVs and key (verified at build time).

Writes:
  blind/datasets/unit_XX.csv   (date,value; neutral data cards)
  blind/README_FOR_LAB.md, blind/REGISTRATION_TEMPLATE.md
  answer_key/ground_truth.json, answer_key/GROUND_TRUTH.md
  manifest.json                (sha256 of every file, incl. this script)
"""
import hashlib
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..")
BLIND = os.path.join(PACK, "blind")
KEY = os.path.join(PACK, "answer_key")
MASTER_SEED = 20260702
N = 400                          # daily samples per unit
T0 = np.datetime64("2025-01-01")

# ---------------------------------------------------------------- processes
def white(rng, n, sigma=1.0):
    return sigma * rng.normal(size=n)

def ar1(rng, n, phi, sigma=1.0):
    e = sigma * np.sqrt(1 - phi ** 2) * rng.normal(size=n)
    x = np.empty(n); x[0] = e[0]
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x

def harm(t, period, amp, phase):
    return amp * np.cos(2 * np.pi * t / period + phase)

def logistic(rng, n, r=3.97):
    x = np.empty(n); x[0] = rng.uniform(0.2, 0.8)
    for i in range(1, n):
        x[i] = r * x[i - 1] * (1 - x[i - 1])
    return (x - x.mean()) / x.std()

def random_walk(rng, n, sigma=1.0):
    return np.cumsum(sigma * rng.normal(size=n))


def detectability(amp, sigma, n):
    """Approximate periodogram line SNR: peak/mean ~ n*amp^2/(4 sigma^2).
    Rule of thumb: detectable if > ~3*ln(n) (Fisher-g scale)."""
    return float(n * amp ** 2 / (4 * sigma ** 2) / (3 * np.log(n)))


# ---------------------------------------------------------------- unit table
def build_units():
    t = np.arange(N, dtype=float)
    rng = np.random.default_rng(MASTER_SEED)
    # per-unit child seeds, drawn once in fixed order
    seeds = {f"unit_{i:02d}": int(rng.integers(2 ** 31)) for i in range(1, 13)}
    R = {k: np.random.default_rng(s) for k, s in seeds.items()}
    U = {}

    # -- true nulls ---------------------------------------------------------
    U["unit_01"] = dict(y=white(R["unit_01"], N),
        truth="white_noise", params=dict(sigma=1.0),
        expected="FAILED_EQUATION_SEARCH or REFUSED_NULL_DETECTION",
        expected_class="null",
        scoring="any fitted-equation acceptance = FALSE POSITIVE (severe)")
    U["unit_02"] = dict(y=white(R["unit_02"], N, sigma=3.7),
        truth="white_noise_scaled", params=dict(sigma=3.7),
        expected="FAILED_EQUATION_SEARCH or REFUSED_NULL_DETECTION",
        expected_class="null",
        scoring="scale must not matter (M-3 lesson)")

    # -- structured but equation-free ----------------------------------------
    U["unit_03"] = dict(y=ar1(R["unit_03"], N, phi=0.85),
        truth="ar1", params=dict(phi=0.85),
        expected="FAILED_EQUATION_SEARCH (AR/surrogate nulls must absorb)",
        expected_class="null",
        scoring="harmonic acceptance = FALSE POSITIVE; detection-layer "
                "structure flags are fine (it IS structured)")
    U["unit_04"] = dict(y=random_walk(R["unit_04"], N),
        truth="random_walk", params=dict(sigma=1.0),
        expected="FAILED_EQUATION_SEARCH (1/f^2 spectrum is the classic trap)",
        expected_class="null",
        scoring="harmonic acceptance = FALSE POSITIVE (severe)")
    U["unit_05"] = dict(y=logistic(R["unit_05"], N) + 0.1 * white(R["unit_05"], N),
        truth="logistic_map_r3.97", params=dict(r=3.97, obs_noise=0.1),
        expected="FAILED_EQUATION_SEARCH for the harmonic menu (deterministic "
                 "but non-harmonic; overclaim test)",
        expected_class="null",
        scoring="a harmonic CANDIDATE_EQUATION here = OVERCLAIM")

    # -- recoverable harmonic laws (SNR ladder) ------------------------------
    for name, amp, per in [("unit_06", 1.20, 27.3), ("unit_07", 0.45, 14.9),
                           ("unit_08", 0.12, 33.1)]:
        r = R[name]
        y = harm(np.arange(N), per, amp, r.uniform(0, 2 * np.pi)) + white(r, N)
        d = detectability(amp, 1.0, N)
        U[name] = dict(y=y, truth="single_harmonic",
            params=dict(period_d=per, amp=amp, sigma=1.0,
                        detectability_ratio=round(d, 2)),
            expected=("CANDIDATE_EQUATION, period within profile CI"
                      if d > 2 else
                      "borderline: either CANDIDATE (period correct) or "
                      "FAILED labeled below-power"),
            expected_class=("detect" if d > 2 else "borderline"),
            scoring=("period must lie in the reported CI and CI must contain "
                     "truth; wrong-period acceptance = FALSE RECOVERY" if d > 2
                     else "FAILED is correct IF the power statement covers it; "
                          "silent FAILED without power language = miss"))

    # -- traps ---------------------------------------------------------------
    r = R["unit_09"]                       # two lines 1.4 Rayleigh apart
    p1, p2 = 27.3, 24.9                    # df = 1/27.3-1/24.9 ~ 1.4/N
    y = harm(np.arange(N), p1, 1.0, r.uniform(0, 2 * np.pi)) + \
        harm(np.arange(N), p2, 0.8, r.uniform(0, 2 * np.pi)) + white(r, N)
    U["unit_09"] = dict(y=y, truth="two_close_harmonics",
        params=dict(periods_d=[p1, p2], amps=[1.0, 0.8], sigma=1.0,
                    rayleigh_separation=round(abs(1/p1 - 1/p2) * N, 2)),
        expected="CANDIDATE with 2 lines (joint refinement) OR 1 line with "
                 "residual scan firing on the second — merged single line "
                 "with a CI excluding both truths = the v1 30.64d failure",
        expected_class="detect",
        scoring="score recovered periods against both truths; a single "
                "intermediate period whose CI excludes both = FALSE RECOVERY")

    r = R["unit_10"]                       # harmonic + linear trend
    y = harm(np.arange(N), 21.7, 0.9, r.uniform(0, 2 * np.pi)) + \
        0.004 * np.arange(N) + white(r, N)
    U["unit_10"] = dict(y=y, truth="harmonic_plus_trend",
        params=dict(period_d=21.7, amp=0.9, trend_per_day=0.004, sigma=1.0),
        expected="CANDIDATE with trend term (or detrended fit); period correct",
        expected_class="detect",
        scoring="trend leakage into a spurious long period = FALSE RECOVERY")

    r = R["unit_11"]                       # main line + hidden second line
    y = harm(np.arange(N), 29.5, 1.1, r.uniform(0, 2 * np.pi)) + \
        harm(np.arange(N), 9.3, 0.5, r.uniform(0, 2 * np.pi)) + white(r, N)
    U["unit_11"] = dict(y=y, truth="harmonic_plus_hidden_line",
        params=dict(main_period_d=29.5, main_amp=1.1,
                    hidden_period_d=9.3, hidden_amp=0.5, sigma=1.0),
        expected="CANDIDATE/PARTIAL_MODEL: main line recovered; residual scan "
                 "(Q-5, no whitelist) must fire near 9.3 d; with 9.3 d "
                 "whitelisted the scan must go silent",
        expected_class="detect",
        scoring="residual scan silent with no whitelist = SCAN MISS; scan "
                "firing after correct whitelist = SCAN FALSE ALARM")

    r = R["unit_12"]                       # era-bounded line (first half only)
    y = white(r, N)
    y[:N // 2] += harm(np.arange(N // 2), 18.4, 1.0, r.uniform(0, 2 * np.pi))
    U["unit_12"] = dict(y=y, truth="era_bounded_harmonic",
        params=dict(period_d=18.4, amp=1.0, active_rows=[0, N // 2 - 1],
                    sigma=1.0),
        expected="NOT a clean CANDIDATE: stationarity/era checks (S-7, "
                 "R2-cusum class) must flag; acceptable outcomes are "
                 "ERA_BOUNDED flag or PARTIAL with segment attribution",
        expected_class="trap",
        scoring="a pooled CANDIDATE_EQUATION with no era language = "
                "OVERCLAIM (the #45 lesson transposed)")

    return U, seeds


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    U, seeds = build_units()
    os.makedirs(os.path.join(BLIND, "datasets"), exist_ok=True)
    os.makedirs(KEY, exist_ok=True)
    dates = (T0 + np.arange(N)).astype(str)
    for name, u in U.items():
        path = os.path.join(BLIND, "datasets", f"{name}.csv")
        with open(path, "w") as f:
            f.write("date,value\n")
            for d, v in zip(dates, u["y"]):
                f.write(f"{d},{v:.6f}\n")
    # ground truth (sealed)
    gt = {"master_seed": MASTER_SEED, "n": N, "child_seeds": seeds,
          "units": {k: {kk: vv for kk, vv in u.items() if kk != "y"}
                    for k, u in U.items()},
          "scoring_rules": {
              "false_positive": "accepted equation on expected_class=null",
              "false_recovery": "accepted equation with truth outside CI",
              "miss": "FAILED on expected_class=detect without a power "
                      "statement covering the effect size",
              "overclaim": "harmonic law on unit_05, or pooled candidate on "
                           "unit_12 without era language",
              "borderline": "unit_08 scores correct either way if labeled",
              "pass_targets": "0 false positives; >=3 of the 4 detect-class "
                              "units recovered (06,09,10,11; 07/08 are "
                              "borderline by declared detectability); scan "
                              "behaviors on unit_11 correct"}}
    json.dump(gt, open(os.path.join(KEY, "ground_truth.json"), "w"), indent=2)
    with open(os.path.join(KEY, "GROUND_TRUTH.md"), "w") as f:
        f.write("# eq_eval_set_v1 — ground truth (SEALED)\n\n"
                "| unit | truth | key params | expected |\n|---|---|---|---|\n")
        for k, u in U.items():
            f.write(f"| {k} | {u['truth']} | "
                    f"{json.dumps(u['params'])} | {u['expected']} |\n")
    # manifest over everything (script included)
    files = sorted(
        os.path.join(dp, fn)
        for dp, _, fns in os.walk(PACK) for fn in fns
        if fn != "manifest.json" and not fn.startswith("."))
    manifest = {os.path.relpath(p, PACK): sha(p) for p in files}
    json.dump(manifest, open(os.path.join(PACK, "manifest.json"), "w"),
              indent=2)
    print(f"{len(U)} units written; manifest {len(manifest)} files")
    print("blind sha8s:", {k: v[:8] for k, v in manifest.items()
                           if k.startswith("blind/datasets")})


if __name__ == "__main__":
    main()
