#!/usr/bin/env python3
"""CPU float64 evaluation of registration pcso.sparse.seq1, claims S1--S5.

The lead must commitment-hash this script before the full study. --streams changes
replication counts only, never horizons or criteria. Timings go to stderr; the
JSON artifact is byte-deterministic for fixed inputs, claims, counts and run date,
including across worker counts. No registered model or harness is modified.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import sys
import time

# Each process owns one stream. Prevent nested BLAS parallelism on the 18-core host.
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_variable] = "1"

import numpy as np

import pcso_model_registry as registry
import pcso_sparse_switch as sparse

ROOT = Path(__file__).resolve().parents[1]
SEED_BASE = 20260923 + 5000
CLAIMS = ("S1", "S2", "S3", "S3b", "S4", "S5")
BALANCED_POOLS = (42, 45, 49, 55, 58)
HORIZON = 1000
THRESHOLD = 100.0
TOLERANCE = 1e-9
DEFAULT_STREAMS = {"S1": 400, "S2": 400, "S3": 100, "S3b": 100, "S4": 400, "S5": 100}

INTERPRETATIONS = [
    "Section 5 is a fresh-start study: every simulated stream and the real-draw S2 stream "
    "start with a new CPSparseSwitch, E=1, M=0 and pooled t=1, without Section 3 warmup.",
    "The real schedule is exactly the ordered (date, P) projection of registry.load() rows "
    "dated <= REGISTERED_AFTER; the same conditioning rows form the real-draw S2 stream.",
    "Stream index s is zero-based and restarts at 0 in each claim/cell (common random "
    "numbers across cells). Its draw RNG is default_rng(20260923+5000+s). The single "
    "10,000-draw S2 stream uses fixed s=400 and repeats the real schedule cyclically.",
    "S2 evaluates all S1 streams even when S1 is omitted from --claims. When both are "
    "selected, those streams and their bound checks are computed once and reused.",
    "--streams overrides each replicated batch/cell, including S2's S1 dependency; "
    "it never shortens a horizon or removes the one long or one real S2 stream. "
    "An overridden run is marked as an override, not a registered full study.",
    "Balanced means round-robin (42,45,49,55,58), beginning with 42, for 1,000 pooled "
    "draws. S3, S3b and S4 monitor every pooled prefix through draw 1,000 (200 draws "
    "of each game), including the final round's draws after an affected game's 200th draw.",
    "Each planted stream selects one uniform support without replacement before any "
    "draw. The sampled coordinate order assigns the theta vector; that support stays "
    "fixed. Other games and inactive periods are uniform. Planted draws call "
    "registry.sample_cp with zero log-weights off the support.",
    "S3 and S3b use fresh registry.CPNest(seed=SEED_BASE+s, M=128) and "
    "registry.DirichletCP(a=100.0, samples=2000, seed=SEED_BASE+s). Each comparator "
    "has its own RNG, separate from the draw RNG, and scores the identical draw sequence.",
    "In S3 and S4, SE is the empirical binomial standard error sqrt(p_hat*(1-p_hat)/N) "
    "of the sparse model's crossing fraction. No clipping, continuity correction, "
    "paired-difference SE or multiple-cell adjustment changes the registered criteria.",
    "S3b has 16 cells: for each P in {45,58}, equal positive theta in {0.25,0.5} "
    "at each k in {1,2}; k=2 mixed signs (0.25,-0.25) and (0.5,-0.5); and k=2 "
    "unequal magnitudes (0.5,0.25) and (0.5,-0.25). Each cell has 100 streams by "
    "default, the S3 horizon and both comparators; it has no pass criterion.",
    "S4 uses the S3 balanced horizon and a uniform fixed support in each stream. "
    "bw_second_moment returns E0[W^2], not power; the BW power bound is "
    "min(1, 0.01 + 0.5*sqrt(max(0, E0[W^2]-1))), matching the plan's 2.24% example.",
    "S5 uses the same balanced 1,000-draw schedule because no separate horizon or "
    "schedule is specified. Draws are one-based: deviation is active for 200 <= t < 700, "
    "on one uniformly chosen coordinate of P=45 with theta=1; all other draws are uniform.",
    "S5 uses Lemma 1's exact expert-sequence probability: initial prior 1/2; "
    "transition after t is (1-rho_t)*I[same expert]+rho_t*prior(next expert), "
    "rho_t=1-exp(-tau(t)). Thus switches precede draws 200 and 700 (rho_199 and "
    "rho_699); same-expert transitions include resampling the same expert. At every "
    "T, log(E_comparator_T)-log(E_T) <= -log(path_prior_T) is checked.",
    "S5 detection is the first t >= 200 with E_t >= 100, with delay t-200 in pooled "
    "draws (zero if already above threshold at onset); E is not reset. Detection "
    "remains observable after offset through t=1,000. Non-detections are encoded -1 "
    "and passed to registry.censored_median with delay horizon 800.",
    "S2 and S5 check every nonempty prefix with absolute tolerance 1e-9 nats. "
    "Slack means RHS-LHS; both maximum and minimum slack and maximum excess "
    "(LHS-RHS, positive means violation before tolerance) are reported.",
    "Crossing uses >=100, including the initial E_0=1 in its supremum. All models "
    "continue through the full horizon. Scientific criteria are reported unchanged "
    "even for smoke counts; failed criteria do not make the CLI execution fail.",
    "Worker count and observed wall times are excluded from deterministic JSON. "
    "Timings and ideal 18-worker full-count projections are printed to stderr; "
    "S1 owns shared null-stream time when selected together with S2.",
]


def stream_rng(s):
    return np.random.default_rng(SEED_BASE + s)


def balanced_schedule():
    return tuple((f"pooled-{t:04d}", BALANCED_POOLS[(t - 1) % 5])
                 for t in range(1, HORIZON + 1))


def conditioning_rows():
    rows = tuple((d, P, tuple(S)) for d, P, S in registry.load()
                 if d <= registry.REGISTERED_AFTER)
    if not rows:
        raise ValueError("the conditioning schedule is empty")
    return rows


def draw_subset(rng, P, support=(), theta=()):
    if not support:
        return tuple(sorted(int(i) + 1 for i in rng.choice(P, registry.K, replace=False)))
    logw = np.zeros(P, dtype=np.float64)
    logw[np.asarray(support) - 1] = theta
    return registry.sample_cp(rng, logw)


@dataclass
class Evidence:
    t: int = 0
    log_e: float = 0.0
    log_m: float = -math.inf
    log_e_max: float = 0.0
    log_m_max: float = -math.inf
    first_crossing: int = -1

    def advance(self, increment):
        self.t += 1
        self.log_e += increment
        # Deliberately identical arithmetic to registry.run_registered.
        self.log_m = increment + float(np.logaddexp(
            self.log_m, math.log(1.0 / (self.t * (self.t + 1)))))
        self.log_e_max = max(self.log_e_max, self.log_e)
        self.log_m_max = max(self.log_m_max, self.log_m)
        if self.first_crossing < 0 and self.log_e >= math.log(THRESHOLD):
            self.first_crossing = self.t

    def result(self):
        return {"log_E_final": self.log_e, "log_E_max": self.log_e_max,
                "log_M_max": self.log_m_max, "first_crossing": self.first_crossing,
                "crossed_E": self.log_e_max >= math.log(THRESHOLD),
                "crossed_M": self.log_m_max >= math.log(THRESHOLD)}


class BoundCheck:
    def __init__(self):
        self.n = self.violations = 0
        self.max_slack = self.max_excess = -math.inf
        self.worst_t = self.first_violation = None

    def observe(self, lhs, rhs, t):
        if not (math.isfinite(lhs) and math.isfinite(rhs)):
            raise ValueError(f"non-finite bound input at T={t}")
        excess = lhs - rhs
        self.n += 1
        self.max_slack = max(self.max_slack, -excess)
        if excess > self.max_excess:
            self.max_excess, self.worst_t = excess, t
        if excess > TOLERANCE:
            self.violations += 1
            if self.first_violation is None:
                self.first_violation = t

    def result(self):
        return {"prefixes_checked": self.n, "violations": self.violations,
                "max_slack_nats": self.max_slack, "min_slack_nats": -self.max_excess,
                "max_excess_nats": self.max_excess, "worst_T": self.worst_t,
                "first_violation_T": self.first_violation, "pass": self.violations == 0}


def uniform_loss_bounds(horizon):
    # Prediction at T precedes switching update T: only tau(1), ..., tau(T-1).
    return math.log(2) + np.concatenate((np.zeros(1, dtype=np.float64),
        np.cumsum([sparse._tau(t) for t in range(1, horizon)], dtype=np.float64)))


def path_loss_bounds(horizon, P, k, onset=200, offset=700):
    """-log prior(expert sequence), marginalizing self-resampling transitions.

    Koolen & de Rooij (2013), Lemma 1, eq. (6): https://arxiv.org/pdf/1311.6536
    The expert is uniform, then the specified sparse expert, then uniform.
    """
    logprior = {False: -math.log(2), True: sparse._log_prior(P, k)}
    active = lambda t: onset <= t < offset
    cost = -logprior[active(1)]
    out = [cost]
    for t in range(1, horizon):
        tau = sparse._tau(t)
        log_reset = math.log(-math.expm1(-tau)) + logprior[active(t + 1)]
        log_transition = (float(np.logaddexp(-tau, log_reset))
                          if active(t) == active(t + 1) else log_reset)
        cost -= log_transition
        out.append(cost)
    return np.asarray(out, dtype=np.float64)


@dataclass(frozen=True)
class StreamTask:
    s: int
    schedule: tuple
    P: int | None = None
    theta: tuple = ()
    comparators: bool = False
    tracking: bool = False
    real_rows: tuple | None = None


def evaluate_stream(task):
    """One fresh stream; its RNG/state never depend on process identity or order."""
    rng = stream_rng(task.s)
    support = (() if not task.theta else
               tuple(int(i) + 1 for i in rng.choice(task.P, len(task.theta), replace=False)))
    models = [sparse.CPSparseSwitch()]
    if task.comparators:
        models.extend((registry.CPNest(seed=SEED_BASE + task.s, M=128),
                       registry.DirichletCP(a=100.0, samples=2000, seed=SEED_BASE + task.s)))
    evidence = {m.name: Evidence() for m in models}
    horizon = len(task.schedule)
    uniform_bounds, uniform_check = uniform_loss_bounds(horizon), BoundCheck()
    path_bounds = path_loss_bounds(horizon, task.P, len(task.theta)) if task.tracking else None
    path_check, comparator_log_e, delay = BoundCheck(), 0.0, -1
    # Exact partition of the fixed comparator, independent of the sparse mixture.
    if task.tracking:
        logw = np.zeros((1, task.P), dtype=np.float64)
        logw[0, np.asarray(support) - 1] = task.theta
        comparator = registry.Law(logw, np.ones(1, dtype=np.float64))
    log_comb = {P: math.log(math.comb(P, registry.K)) for _, P in task.schedule}
    draw_hash = hashlib.sha256()
    for t, (_, P) in enumerate(task.schedule, 1):
        active = P == task.P and (not task.tracking or 200 <= t < 700)
        S = (task.real_rows[t - 1][2] if task.real_rows is not None else
             draw_subset(rng, P, support if active else (), task.theta if active else ()))
        draw_hash.update(bytes((P, *S)))
        for model in models:
            increment = model.predict(P).logq(S) + log_comb[P]
            if not math.isfinite(increment):
                raise ValueError(f"non-finite score for {model.name}, s={task.s}, T={t}")
            evidence[model.name].advance(increment)
            model.update(P, S)
        log_e = evidence[sparse.CPSparseSwitch.name].log_e
        uniform_check.observe(-log_e, float(uniform_bounds[t - 1]), t)
        if task.tracking:
            if active:
                comparator_log_e += comparator.logq(S) + log_comb[P]
            path_check.observe(comparator_log_e - log_e, float(path_bounds[t - 1]), t)
            if t >= 200 and delay < 0 and log_e >= math.log(THRESHOLD):
                delay = t - 200
    result = {"s": None if task.real_rows is not None else task.s,
              "seed": None if task.real_rows is not None else SEED_BASE + task.s,
              "draws": horizon, "draws_sha256": draw_hash.hexdigest(),
              "support": list(support), "models": {k: v.result() for k, v in evidence.items()},
              "uniform_bound": uniform_check.result()}
    if task.tracking:
        result.update(path_bound=path_check.result(), detection_delay=delay,
                      comparator_log_E_final=comparator_log_e,
                      path_bound_final_nats=float(path_bounds[-1]))
    return result


def _timed_stream(task):
    start = time.perf_counter()
    result = evaluate_stream(task)
    return result, time.perf_counter() - start


def fraction_summary(records, model, statistic="crossed_E"):
    n = len(records)
    count = sum(r["models"][model][statistic] for r in records)
    p = count / n
    return {"streams": n, "crossings": count, "fraction": p,
            "SE": math.sqrt(p * (1 - p) / n)}


def bound_summary(records, field):
    checks = [r[field] for r in records]
    worst = max(range(len(checks)), key=lambda i: checks[i]["max_excess_nats"])
    return {"streams": len(records),
            "prefixes_checked": sum(c["prefixes_checked"] for c in checks),
            "violations": sum(c["violations"] for c in checks),
            "max_slack_nats": max(c["max_slack_nats"] for c in checks),
            "min_slack_nats": min(c["min_slack_nats"] for c in checks),
            "max_excess_nats": checks[worst]["max_excess_nats"],
            "worst_stream_s": records[worst]["s"], "worst_T": checks[worst]["worst_T"],
            "pass": all(c["pass"] for c in checks)}


def cells_for(claim):
    if claim == "S3b":
        vectors = [(theta,) * k for k in (1, 2) for theta in (0.25, 0.5)]
        vectors += [(0.25, -0.25), (0.5, -0.5), (0.5, 0.25), (0.5, -0.25)]
        return [(P, v) for P in (45, 58) for v in vectors]
    theta = math.log(1.1) if claim == "S4" else 1.0
    return [(P, (theta,) * k) for k in (1, 2) for P in (45, 58)]


def power_cell(claim, P, theta, records):
    summaries = {name: fraction_summary(records, name) for name in records[0]["models"]}
    result = {"P": P, "k": len(theta), "theta": list(theta), "pooled_draws": HORIZON,
              "affected_game_draws": 200, "models": summaries, "stream_results": records}
    estimate = summaries[sparse.CPSparseSwitch.name]
    p, se = estimate["fraction"], estimate["SE"]
    if claim == "S3":
        bound = sparse.crossing_lower_bound(P, len(theta), 1.0, 200, pooled_T=HORIZON)
        criteria = {"fraction_ge_lower_bound_minus_2SE": p >= bound - 2 * se,
                    "strictly_above_cp_nest": p > summaries["cp_nest"]["fraction"],
                    "strictly_above_dirichlet_cp_a100": p > summaries["dirichlet_cp_a100"]["fraction"]}
        result.update(exact_crossing_lower_bound=bound, lower_bound_minus_2SE=bound - 2 * se,
                      criteria=criteria, **{"pass": all(criteria.values())})
    elif claim == "S4":
        second = sparse.bw_second_moment(P, len(theta), math.log(1.1), 200)
        bound = min(1.0, 0.01 + 0.5 * math.sqrt(max(0.0, second - 1)))
        passed = p <= bound + 2 * se
        result.update(second_moment=second, bw_power_bound=bound, bound_plus_2SE=bound + 2 * se,
                      criteria={"fraction_le_BW_bound_plus_2SE": passed}, **{"pass": passed})
    else:
        result["status"] = "reported_only"
    return result


def json_bytes(result):
    return (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def run_study(rows, claims, streams, workers, run_date):
    schedule = tuple((d, P) for d, P, _ in rows)
    balanced = balanced_schedule()
    counts = {c: streams if streams is not None else DEFAULT_STREAMS[c] for c in CLAIMS}
    files = (Path(__file__), Path(sparse.__file__), Path(registry.__file__))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    output = {"_meta": {
        "registration": "pcso.sparse.seq1", "registered_after": registry.REGISTERED_AFTER,
        "run_date": run_date, "claims": list(claims), "streams_override": streams,
        "run_kind": "stream_count_override" if streams is not None else "registered_counts",
        "backend": "CPU", "dtype": "float64", "numeric_threads_per_worker": 1,
        "seeds": {"formula": "20260923 + 5000 + s", "base": SEED_BASE,
                  "replicated_s": {c: [0, counts[c] - 1] for c in claims},
                  "S2_null_dependency_s": [0, counts["S1"] - 1] if "S2" in claims else None,
                  "S2_long_s": 400 if "S2" in claims else None},
        "schedule_length": len(schedule), "schedule_sha256": hashlib.sha256(json_bytes(schedule)).hexdigest(),
        "conditioning_rows_sha256": hashlib.sha256(json_bytes(rows)).hexdigest(),
        "input_snapshot_commit": registry.INPUT_SNAPSHOT_COMMIT,
        "sha256": hashes, "threshold": THRESHOLD, "bound_tolerance_nats": TOLERANCE,
        "interpretations": INTERPRETATIONS,
    }}
    timings = {}
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
        def batch(tasks, full_count):
            start = time.perf_counter()
            pairs = list(executor.map(_timed_stream, tasks, chunksize=1))
            durations = [d for _, d in pairs]
            timing = {"wall_seconds": time.perf_counter() - start,
                      "stream_seconds": math.fsum(durations), "streams_evaluated": len(pairs),
                      "projected_full_seconds_18_workers": max(
                          max(durations), math.fsum(durations) * full_count / len(pairs) / 18)}
            return [r for r, _ in pairs], timing

        null_records = None
        if "S1" in claims or "S2" in claims:
            null_records, timing = batch([StreamTask(s, schedule) for s in range(counts["S1"])], 400)
            owner = "S1" if "S1" in claims else "S2_null_dependency"
            timings[owner] = timing
            print(json.dumps({"claim": owner, **timing}), file=sys.stderr, flush=True)
        for claim in claims:
            if claim == "S1":
                E = fraction_summary(null_records, sparse.CPSparseSwitch.name)
                M = fraction_summary(null_records, sparse.CPSparseSwitch.name, "crossed_M")
                criteria = {"fraction_sup_E_ge_100_le_0.02": E["fraction"] <= 0.02,
                            "fraction_sup_M_ge_100_le_0.02": M["fraction"] <= 0.02}
                output[claim] = {"E": E, "M": M, "criteria": criteria,
                                 "pass": all(criteria.values()), "stream_results": null_records}
                continue
            if claim == "S2":
                long_schedule = tuple(schedule[i % len(schedule)] for i in range(10_000))
                records, timing = batch([StreamTask(400, long_schedule),
                                         StreamTask(0, schedule, real_rows=rows)], 2)
                groups = {"S1_streams": bound_summary(null_records, "uniform_bound"),
                          "long_uniform": bound_summary(records[:1], "uniform_bound"),
                          "real_draws": bound_summary(records[1:], "uniform_bound")}
                output[claim] = {"bound": "-log E_T <= log(2) + sum_{1 <= t < T} tau(t)",
                                 "groups": groups, "all_streams": bound_summary(null_records + records, "uniform_bound"),
                                 "criteria": {k: v["pass"] for k, v in groups.items()},
                                 "pass": all(v["pass"] for v in groups.values()), "stream_results": records}
                if "S1" not in claims:
                    output[claim]["S1_stream_results"] = null_records
            elif claim in ("S3", "S3b", "S4"):
                cells = cells_for(claim)
                n = counts[claim]
                tasks = [StreamTask(s, balanced, P=P, theta=theta, comparators=claim != "S4")
                         for P, theta in cells for s in range(n)]
                records, timing = batch(tasks, DEFAULT_STREAMS[claim] * len(cells))
                results = [power_cell(claim, P, theta, records[i * n:(i + 1) * n])
                           for i, (P, theta) in enumerate(cells)]
                output[claim] = {"cells": results}
                if claim != "S3b":
                    output[claim]["pass"] = all(c["pass"] for c in results)
                else:
                    output[claim]["status"] = "reported_only"
            else:
                records, timing = batch([StreamTask(s, balanced, P=45, theta=(1.0,), tracking=True)
                                         for s in range(counts[claim])], 100)
                check = bound_summary(records, "path_bound")
                delays = [r["detection_delay"] for r in records]
                output[claim] = {"P": 45, "k": 1, "theta": [1.0], "onset": 200, "offset": 700,
                                 "pooled_draws": HORIZON, "path_bound": check,
                                 "criteria": {"Lemma_1_at_every_prefix": check["pass"]}, "pass": check["pass"],
                                 "median_detection_delay_pooled_draws": registry.censored_median(delays, 800),
                                 "detected_streams": sum(d >= 0 for d in delays),
                                 "censored_streams": sum(d < 0 for d in delays), "stream_results": records}
            timings[claim] = timing
            print(json.dumps({"claim": claim, **timing}), file=sys.stderr, flush=True)
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != hashes[p.name] for p in files):
        raise ValueError("source files changed during study; refusing to write")
    return output, timings


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def parse_claims(value):
    chosen = value.split(",")
    if any(c not in CLAIMS for c in chosen) or len(set(chosen)) != len(chosen):
        raise argparse.ArgumentTypeError("use distinct comma-separated claims from " + ",".join(CLAIMS))
    return tuple(c for c in CLAIMS if c in chosen)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=parse_claims, default=CLAIMS)
    parser.add_argument("--streams", type=positive_int, help="replicates per cell; horizons stay registered")
    parser.add_argument("--workers", type=positive_int, default=min(18, os.cpu_count() or 1))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--run-date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)
    rows = conditioning_rows()
    result, _ = run_study(rows, args.claims, args.streams, args.workers, args.run_date.isoformat())
    dst = args.out or ROOT / "results" / f"pcso_sparse_study_{args.run_date.isoformat()}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    payload = json_bytes(result)
    dst.write_bytes(payload)
    print(f"wrote {dst} sha256={hashlib.sha256(payload).hexdigest()}")


if __name__ == "__main__":
    main()
