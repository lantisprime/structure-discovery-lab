#!/usr/bin/env python3
"""Exploratory MLX float32 NULL/POWER simulations; the registered CPU path is unchanged.

Draw generation and schedule-only constants use NumPy float64. Predictive likelihoods,
posterior means and model weights use batched MLX float32 on the GPU. Evidence and the
weighted SR detector are accumulated on the host in float64 from those increments.
No registered-window conditioning is implied: these simulations start at the prior.

Example: python src/pcso_mlx_sim.py --null-streams 10000 --models cp_nest tilt_linear
Power: add --theta1 0.05 --m 128 (the registry's production predictive sample count).
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
from datetime import date

import numpy as np
import pcso_model_registry as reg

try:
    import mlx.core as mx
except ImportError:
    mx = None

ROOT = Path(__file__).resolve().parents[1]
K, ALPHA = reg.K, reg.ALPHA
MODELS = ("uniform", "tilt_high31", "tilt_linear", "pair_parity", "cp_nest")
PORTED = MODELS[1:]
CPU_ONLY = {"dirichlet_cp_a100": "adaptive Gamma importance sampler not ported",
            "ensemble": "requires the unported Dirichlet component and its own random inputs"}


def cp_streams(schedule, n, rng, theta1=0.0):
    """Exact conditional-Poisson sampling using reg.sample_cp's float64 suffix recurrence.

    Vectorization changes RNG consumption, not the sampling law. Streams have shape (N,T,6).
    """
    if n <= 0 or not schedule or not math.isfinite(theta1):
        raise ValueError("positive stream count, nonempty schedule and finite theta1 required")
    out = np.zeros((n, len(schedule), K), dtype=np.int32)
    rows = np.arange(n)
    cache = {}
    for t, (_, P) in enumerate(schedule):
        if P not in cache:
            w = np.exp(theta1 * reg.features(P)[0])
            suf = np.zeros((P + 1, K + 1))
            suf[P, 0] = 1.0
            for j in range(P - 1, -1, -1):
                suf[j] = suf[j + 1]
                suf[j, 1:] += w[j] * suf[j + 1, :-1]
            cache[P] = w, suf
        w, suf = cache[P]
        left = np.full(n, K)
        for j in range(P):
            p = w[j] * suf[j + 1, np.maximum(left - 1, 0)] / suf[j, left]
            take = (left > 0) & (rng.random(n) < p)
            out[rows[take], t, K - left[take]] = j + 1
            left -= take
        if np.any(left):
            raise RuntimeError(f"incomplete conditional-Poisson draw at row {t}")
    return out


class _ZFQueue:
    """Replay identical Gaussian inputs through the unmodified CPU model."""
    def __init__(self, seq):
        self.seq = iter(seq)

    def standard_normal(self, size):
        queued = np.asarray(next(self.seq), dtype=float)
        assert queued.shape == tuple(size), (queued.shape, size)
        return queued


def cpu_model(name, seed=0, M=32):
    if name == "cp_nest":
        return reg.CPNest(seed=seed, M=M)
    return {"uniform": reg.Uniform, "tilt_linear": lambda: reg.TiltGrid(0, "linear"),
            "tilt_high31": lambda: reg.TiltGrid(1, "high31"), "pair_parity": reg.ParityPair}[name]()


def cpu_log_evidence(name, draws, schedule, M=32, seed=0, zf_seq=None, summary=False):
    le = np.empty(draws.shape[:2])
    v0 = np.empty(len(draws)) if name == "cp_nest" else None
    for r in range(len(draws)):
        model = cpu_model(name, seed + r, M)
        if zf_seq is not None:
            model.rng = _ZFQueue(zf_seq[r])
        for t, (_, P) in enumerate(schedule):
            S = draws[r, t]
            le[r, t] = model.predict(P).logq(S) + math.log(math.comb(P, K))
            model.update(P, S)
        if v0 is not None:
            v0[r] = model.v[0]
    if summary:
        result = evidence_summary(le)
        if v0 is not None:
            result["v0_final"] = v0
        return result
    return le


def evidence_summary(le):
    """Same evidence and SR recurrences as reg.run, with log-space SR for stability."""
    le64 = np.asarray(le, dtype=np.float64)
    cumulative = np.cumsum(le64, axis=1)
    sup = np.maximum(cumulative.max(axis=1), 0)
    hit = cumulative >= math.log(1 / ALPHA)
    crossing = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, -1)
    sr = np.full(len(le), -np.inf)
    sr_max = sr.copy()
    for t in range(le.shape[1]):
        sr = le64[:, t] + np.logaddexp(sr, -math.log((t + 1) * (t + 2)))
        sr_max = np.maximum(sr_max, sr)
    return {"le": le, "sup": sup, "final_log_e": cumulative[:, -1],
            "crossing": crossing, "log_sr_max": sr_max}


def binomial_ci(k, n, confidence=0.95):
    """Two-sided exact Clopper-Pearson; reg.clopper_pearson_lower is one-sided."""
    from scipy.stats import beta
    tail = (1 - confidence) / 2
    return [float(beta.ppf(tail, k, n - k + 1)) if k else 0.0,
            float(beta.ppf(1 - tail, k + 1, n - k)) if k < n else 1.0]


def crossing_summary(result, horizon):
    n = len(result["sup"])
    k = int((result["sup"] >= math.log(1 / ALPHA)).sum())
    sr_k = int((result["log_sr_max"] >= math.log(1 / ALPHA)).sum())
    return {"n_streams": n, "n_crossed": k, "fraction_crossed": k / n,
            "crossing_ci_95": binomial_ci(k, n), "evidence_alpha": ALPHA,
            "sup_log_e_quantiles": dict(zip(("0.5", "0.9", "0.99"),
                                            np.quantile(result["sup"], [0.5, 0.9, 0.99]).tolist())),
            "sr_n_crossed": sr_k, "sr_crossing_ci_95": binomial_ci(sr_k, n),
            "horizon": horizon,
            "median_draws_to_cross_censored": reg.censored_median(result["crossing"], horizon)}


def compare_null(cpu_sup, cpu_sr, gpu, alpha=0.05):
    """Two-sample checks are discrepancy screens, not proof of equal distributions."""
    from scipy.stats import fisher_exact, ks_2samp
    ks = ks_2samp(np.round(cpu_sup, 5), np.round(gpu["sup"], 5))
    c = int((np.asarray(cpu_sup) >= math.log(1 / ALPHA)).sum())
    g = int((gpu["sup"] >= math.log(1 / ALPHA)).sum())
    fisher = fisher_exact([[c, len(cpu_sup) - c], [g, len(gpu["sup"]) - g]])
    sr_ks = ks_2samp(np.round(cpu_sr, 5), np.round(gpu["log_sr_max"], 5))
    return {"test_alpha": alpha, "ks_log_resolution": 1e-5, "ks_statistic": float(ks.statistic), "ks_p": float(ks.pvalue),
            "crossing_fisher_p": float(fisher.pvalue), "cpu_crossings": c, "mlx_crossings": g,
            "cpu_n": len(cpu_sup), "mlx_n": len(gpu["sup"]),
            "cpu_crossing_ci_95": binomial_ci(c, len(cpu_sup)),
            "mlx_crossing_ci_95": binomial_ci(g, len(gpu["sup"])),
            "sr_ks_statistic": float(sr_ks.statistic), "sr_ks_p": float(sr_ks.pvalue),
            "ks_critical_D_approx": math.sqrt(-0.5 * math.log(alpha / 2)) *
                math.sqrt(1 / len(cpu_sup) + 1 / len(gpu["sup"])),
            "screen_scope": "gross screen only; critical D is a rejection threshold, not 80% power MDE",
            "verdict": ("discrepancy detected" if min(ks.pvalue, sr_ks.pvalue, fisher.pvalue) < alpha
                        else "warning: marginal screen" if min(ks.pvalue, sr_ks.pvalue, fisher.pvalue) < 2 * alpha
                        else "no gross discrepancy detected")}



def _cpu_null_job(job):
    name, seed, r, schedule, M = job
    rows = reg.synthetic(np.random.default_rng([seed, 100, r]), schedule)
    result = reg.run([cpu_model(name, seed + 1000 + r, M)], rows,
                     warmup=10**9, track_sup=True)[name]
    return result["sup"], math.log(result["sr_max"])


def cpu_null(name, n, schedule, seed=20260923, M=32, workers=8):
    """Unmodified CPU synthetic + run harness, for every model and M."""
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(name, seed, r, schedule, M) for r in range(n)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        values = list(pool.map(_cpu_null_job, jobs, chunksize=max(1, n // (workers * 4))))
    values = np.asarray(values)
    return {"sup": values[:, 0], "log_sr_max": values[:, 1]}

def _esp(w):
    """Elementary symmetric polynomials, independently across all leading dimensions."""
    # The 6*P dependent recurrence operations dominate CP-NEST evaluation cost.
    cols = [mx.ones(w.shape[:-1])] + [mx.zeros(w.shape[:-1]) for _ in range(K)]
    for i in range(w.shape[-1]):
        for k in range(K, 0, -1):
            cols[k] = cols[k] + w[..., i] * cols[k - 1]
    return mx.stack(cols, axis=-1)


def _contract(x, matrix):
    """x @ matrix with a pinned left-to-right accumulation over at most six terms.

    Avoids device/shape-dependent matrix multiplication reduction order.
    """
    out = x[..., 0:1] * matrix[..., 0, :]
    for j in range(1, x.shape[-1]):
        out = out + x[..., j:j + 1] * matrix[..., j, :]
    return out


def _normalized_esp6(w):
    """e_6(w)/C(P,6) without forming the large, rounded integer C(P,6).

    At prefix n, a_k=e_k/C(n,k). The recurrence a_k += (k/n)*
    (w_n*a_(k-1)-a_k) preserves a_k=1 exactly for unit weights.
    """
    cols = [mx.ones(w.shape[:-1])] + [mx.zeros(w.shape[:-1]) for _ in range(K)]
    for i in range(w.shape[-1]):
        for k in range(min(K, i + 1), 0, -1):
            cols[k] = cols[k] + (k / (i + 1)) * (w[..., i] * cols[k - 1] - cols[k])
    return cols[K]


def _log_mean_ratio(logr, weights):
    """Log weighted mean ratio; use log1p near one to avoid cancellation.

    |delta| < 0.5 keeps 1+delta away from zero; logsumexp handles other values.
    """
    delta = mx.sum(weights * mx.expm1(logr), axis=-1)
    ordinary = mx.logsumexp(mx.log(weights) + logr, axis=-1)
    return mx.where(mx.abs(delta) < 0.5, mx.log1p(delta), ordinary)


def _cp_constants(schedule):
    """Data-independent precision is shared by all streams; factor once in float64 on CPU.

    Padded level d has nonzero coordinates 0..d-1. L is chol(inv(Lambda)) and the
    Gaussian transform is z @ L.T; the update is grad @ inv(Lambda_new).
    """
    D = reg.CPNest.D
    precision = {d: np.eye(d) / reg.CPNest.TAU**2 for d in range(1, D + 1)}
    features = {P: reg.features(P) for _, P in schedule}
    fisher = {P: K * (P - K) / (P - 1) * (F @ F.T) / P for P, F in features.items()}
    factors, inverses = [], []
    for _, P in schedule:
        chol, inv = np.zeros((D, D, D)), np.zeros((D, D, D))
        for d in range(1, D + 1):
            chol[d - 1, :d, :d] = np.linalg.cholesky(np.linalg.inv(precision[d])).T
            precision[d] += fisher[P][:d, :d]
            inv[d - 1, :d, :d] = np.linalg.inv(precision[d])
        factors.append(chol)
        inverses.append(inv)
    return features, np.array(factors), np.array(inverses)


def _mlx_cp(draws, schedule, M, seed, chunk, zf_seq):
    R, T = draws.shape[:2]
    features, chol, inv = _cp_constants(schedule)
    F = {P: mx.array(f, mx.float32) for P, f in features.items()}
    chol, inv = mx.array(chol, mx.float32), mx.array(inv, mx.float32)
    mask = mx.array(np.tril(np.ones((6, 6))), mx.float32)
    prior = 2.0 ** -np.arange(7)
    prior /= prior.sum()

    def step(mu, v, zf, idx, feat, factor, inverse):
        # factor stores L.T, correcting the draft's transposed Gaussian contraction.
        z = _contract(zf[:, None, :, :], factor[None, :, None, :, :])
        theta = mx.concatenate([mu[:, :, None, :] + z, mu[:, :, None, :] - z], axis=2)
        logw = _contract(theta, feat)
        norm = mx.log(_normalized_esp6(mx.exp(logw)))
        obs = mx.sum(mx.take(feat.T, idx, axis=0), axis=1)
        logr = mx.sum(theta * obs[:, None, None, :], axis=-1) - norm
        level = _log_mean_ratio(logr, mx.full((M,), 1 / M))
        level = mx.concatenate([mx.zeros((mu.shape[0], 1)), level], axis=1)
        le = _log_mean_ratio(level, v)
        # Normalize relative likelihoods directly. log(v) -> softmax introduced
        # a systematic GPU roundoff term on every fixed-share update.
        updated = v + v * mx.expm1(level)
        v = (1 - reg.CPNest.RHO) * (updated / mx.sum(updated, axis=1, keepdims=True)) + reg.CPNest.RHO / 7
        w = mx.exp(_contract(mu, feat))
        E = _esp(w)
        em = mx.ones_like(w)
        for k in range(1, K):
            em = E[..., k:k + 1] - w * em
        pi = w * em / E[..., K:K + 1]
        expected = mx.stack([mx.sum(pi * feat[j], axis=-1) for j in range(6)], axis=-1)
        grad = (obs[:, None, :] - expected) * mask
        mu = mu + _contract(grad, inverse[None, :, :, :])
        return mu, v, le

    step = mx.compile(step)
    le_out, v0 = np.empty((R, T), np.float32), np.empty(R, np.float32)
    for start in range(0, R, chunk):
        end = min(start + chunk, R)
        n = end - start
        mu = mx.zeros((n, 6, 6))
        v = mx.broadcast_to(mx.array(prior, mx.float32), (n, 7))
        idx = mx.array(draws[start:end] - 1)
        key = mx.random.key(seed + start)
        for t, (_, P) in enumerate(schedule):
            if zf_seq is None:
                key, subkey = mx.random.split(key)
                z = mx.random.normal((n, M // 2, 6), key=subkey)
            else:
                z = mx.array(zf_seq[start:end, t], mx.float32)
            mu, v, le = step(mu, v, z, idx[:, t], F[P], chol[t], inv[t])
            # Force each step: no unbounded lazy graph or retained predictive tensors.
            mx.eval(mu, v, le)
            le_out[start:end, t] = np.array(le)
        v0[start:end] = np.array(v[:, 0])
    return {**evidence_summary(le_out), "v0_final": v0}


def _mlx_grid(name, draws, schedule, chunk):
    R, T = draws.shape[:2]
    cache = {}
    parity = reg.ParityPair() if name == "pair_parity" else None
    for _, P in schedule:
        if P in cache:
            continue
        if name == "pair_parity":
            g, _, logz = parity._pool(P)
            table = np.outer(g, reg.THETA)
        else:
            f = reg.features(P)[0 if name == "tilt_linear" else 1]
            table = np.outer(f, reg.THETA)
            logz = np.log(reg.esp(np.exp(table.T))[:, K])
        # Subtract the common uniform log-probability before casting to float32.
        cache[P] = (mx.array(table, mx.float32),
                    mx.array(logz - math.log(math.comb(P, K)), mx.float32))
    prior = mx.array(reg.LOG_PRIOR, mx.float32)

    def step(ll, observed, table, logz):
        values = mx.take(table, observed, axis=0)
        score = values if name == "pair_parity" else mx.sum(values, axis=1)
        lr = score - logz
        lp = prior + ll
        lp = lp - mx.logsumexp(lp, axis=1, keepdims=True)
        le = _log_mean_ratio(lr, mx.exp(lp))
        ll = ll + lr
        ll = ll - mx.max(ll, axis=1, keepdims=True)
        return ll, le

    step = mx.compile(step)
    le_out = np.empty((R, T), np.float32)
    observed = (draws % 2).sum(axis=2).astype(np.int32) if name == "pair_parity" else draws - 1
    for start in range(0, R, chunk):
        end = min(start + chunk, R)
        ll = mx.zeros((end - start, len(reg.THETA)))
        obs = mx.array(observed[start:end])
        for t, (_, P) in enumerate(schedule):
            ll, le = step(ll, obs[:, t], *cache[P])
            mx.eval(ll, le)
            le_out[start:end, t] = np.array(le)
    return evidence_summary(le_out)


def mlx_log_evidence(name, draws, schedule, M=32, seed=0, chunk=500, zf_seq=None, device=None):
    """Evaluate supplied streams; supplied zf_seq has shape (N,T,M/2,6).

    Random simulations are reproducible for fixed seed AND chunk size. M must be even;
    NULL uses M=32 and POWER must use the production M=128.
    """
    if mx is None:
        raise RuntimeError("mlx is not installed; run on an Apple GPU with MLX")
    if name not in MODELS:
        raise ValueError(f"unsupported model: {name}")
    if M < 2 or M % 2 or chunk <= 0:
        raise ValueError("M must be even and >= 2; chunk must be positive")
    draws = np.asarray(draws)
    if draws.ndim != 3 or draws.shape[1:] != (len(schedule), K) or not len(draws) or not schedule:
        raise ValueError("draws must have nonempty shape (streams, len(schedule), 6)")
    pools = np.array([P for _, P in schedule])
    if (not np.issubdtype(draws.dtype, np.integer) or np.any(draws < 1)
            or np.any(draws > pools[None, :, None]) or np.any(np.diff(np.sort(draws, axis=2)) == 0)):
        raise ValueError("each draw must contain six distinct integer balls within its pool")
    if zf_seq is not None and np.shape(zf_seq) != (len(draws), len(schedule), M // 2, 6):
        raise ValueError("zf_seq must have shape (streams, draws, M/2, 6)")
    if name == "uniform":
        # Analytic reference only: no GPU computation.
        return evidence_summary(np.zeros(draws.shape[:2], np.float32))
    if device not in (None, "gpu", "cpu"):
        raise ValueError("device must be gpu, cpu or None")
    with mx.stream(getattr(mx, device)) if device is not None else nullcontext():
        if name == "cp_nest":
            return _mlx_cp(draws, schedule, M, seed, chunk, zf_seq)
        return _mlx_grid(name, draws, schedule, chunk)


def metadata(seed, schedule, M, chunk, device=None):
    from importlib.metadata import version
    sha = os.environ.get("PCSO_GIT_SHA")
    if not sha:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        sha = p.stdout.strip() if p.returncode == 0 else "unavailable"
    return {"status": "exploratory, not registered",
            "device": "unavailable" if mx is None else str(getattr(mx, device) if device else mx.default_device()),
            "device_info": mx.device_info() if mx is not None else None,
            "dtype": "float32", "mlx_version": version("mlx") if mx is not None else None,
            "seed": seed, "git_sha": sha, "M": M, "chunk": chunk,
            "schedule_draws": len(schedule),
            "schedule_sha256": hashlib.sha256(json.dumps(schedule, separators=(",", ":")).encode()).hexdigest(),
            "schedule_pool_counts": {str(P): sum(Q == P for _, Q in schedule) for P in sorted({P for _, P in schedule})},
            "initialization": "prior (not conditioned registered-window power)",
            "host_float64": "draw sampler, schedule constants, evidence/SR accumulation",
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                              for p in ("src/pcso_mlx_sim.py", "src/pcso_model_registry.py")}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--null-streams", type=int, default=10000)
    ap.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "exploratory" /
                    f"pcso_mlx_null_calibration_{date.today().isoformat()}.json")
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--m", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--device", choices=("gpu", "cpu"), default="gpu")
    ap.add_argument("--max-draws", type=int, default=0, help="0 uses the entire real-data schedule")
    ap.add_argument("--theta1", type=float, default=0.0, help="nonzero selects planted linear-tilt POWER")
    args = ap.parse_args(argv)
    if mx is None:
        ap.error("mlx is not installed; run on the MLX machine")
    M = args.m if args.m is not None else (128 if args.theta1 else 32)
    if (args.null_streams <= 0 or args.chunk <= 0 or args.max_draws < 0 or M < 2 or M % 2
            or not math.isfinite(args.theta1)):
        ap.error("positive streams/chunk, nonnegative max-draws, even M >= 2, finite theta1 required")
    if args.theta1 and M != 128:
        ap.error("POWER uses production M=128")
    schedule = [(d, P) for d, P, _ in reg.load()]
    if args.max_draws:
        schedule = schedule[:args.max_draws]
    start = time.perf_counter()
    draws = cp_streams(schedule, args.null_streams, np.random.default_rng(args.seed), args.theta1)
    draw_s = time.perf_counter() - start
    out = {"_meta": metadata(args.seed, schedule, M, args.chunk, args.device), "cpu_only": CPU_ONLY,
           "simulation": "power" if args.theta1 else "null", "theta1": args.theta1,
           "draw_generation_s": draw_s, "models": {}}
    for name in args.models:
        start = time.perf_counter()
        res = mlx_log_evidence(name, draws, schedule, M=M, seed=args.seed, chunk=args.chunk, device=args.device)
        out["models"][name] = {"evaluation_s": time.perf_counter() - start,
                               "implementation": "analytic reference (no GPU computation)" if name == "uniform" else "MLX",
                               **crossing_summary(res, len(schedule))}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
        print(name, json.dumps(out["models"][name]), flush=True)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
