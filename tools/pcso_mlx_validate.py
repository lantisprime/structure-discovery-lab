"""Matched arithmetic validation; exact registered CPU models, shared draws and float32 Gaussians.

Run one model/job per <=300 s supervisor. The 400-stream jobs use eight CPU workers.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pcso_mlx_sim as sim

# Fixed before observing full-horizon errors. Difference is always MLX minus CPU.
BOUNDS = {'sup': {'mean_abs': 1e-4, 'q99_abs': 3e-4, 'max_abs': 1e-3},
          'final_log_e': {'mean_abs': 1e-4, 'q99_abs': 3e-4, 'max_abs': 1e-3},
          'v0_final': {'mean_abs': 1e-5, 'q99_abs': 3e-5, 'max_abs': 1e-4}}


def difference(cpu, mlx):
    delta = np.asarray(mlx, dtype=float) - cpu
    return {'mean': float(delta.mean()), 'mean_abs': float(np.abs(delta).mean()),
            'q99_abs': float(np.quantile(np.abs(delta), .99)),
            'max_abs': float(np.abs(delta).max())}


def paired_metrics(cpu, mlx):
    return {key: difference(cpu[key], mlx[key]) for key in BOUNDS if key in cpu}


def assert_paired(metrics):
    for key, measured in metrics.items():
        for stat, bound in BOUNDS[key].items():
            assert measured[stat] <= bound, (key, stat, measured[stat], bound)


def drift_metrics(cpu_le, mlx_le, target=994):
    delta = np.asarray(mlx_le, dtype=float) - cpu_le
    cumulative = np.cumsum(delta, axis=1)
    t = np.arange(1, delta.shape[1] + 1)
    centered = t - t.mean()
    slope = cumulative @ centered / (centered @ centered)
    intercept = cumulative.mean(axis=1) - slope * t.mean()
    inc_slope = delta @ centered / (centered @ centered)
    return {'max_abs_delta_le_t': float(np.abs(delta).max()),
            'max_abs_cumulative_delta': float(np.abs(cumulative).max()),
            'mean_ols_slope_delta_le_vs_t': float(inc_slope.mean()),
            'ols_slopes_cumulative_delta_vs_t': slope.tolist(),
            'mean_ols_slope_cumulative_delta_vs_t': float(slope.mean()),
            'max_abs_ols_slope_cumulative_delta_vs_t': float(np.abs(slope).max()),
            'extrapolated_994_bound': float(np.max(np.abs(intercept) + target * np.abs(slope))),
            'bound_definition': 'max_stream(|OLS intercept| + 994*|OLS slope|), cumulative MLX-CPU nats',
            'target_horizon': target}


def assert_drift(metrics, cpu, mlx):
    assert metrics['max_abs_delta_le_t'] <= 1e-5, metrics
    assert metrics['extrapolated_994_bound'] < 1e-4, metrics
    assert np.max(np.abs(mlx['sup'] - cpu['sup'])) <= 1e-3


def _cpu_job(job):
    name, draws, schedule, M, zf = job
    return sim.cpu_log_evidence(name, draws, schedule, M=M, zf_seq=zf, summary=True)


def matched(name, schedule, n=16, M=32, seed=20260925, theta1=0.0, devices=('gpu',), workers=8):
    draws = sim.cp_streams(schedule, n, np.random.default_rng(seed), theta1)
    zf = (np.random.default_rng(seed + 1).standard_normal((n, len(schedule), M // 2, 6)).astype(np.float32)
          if name == 'cp_nest' else None)
    groups = np.array_split(np.arange(n), min(workers, n))
    jobs = [(name, draws[g], schedule, M, None if zf is None else zf[g].astype(np.float64)) for g in groups]
    if workers == 1:
        values = list(map(_cpu_job, jobs))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            values = list(pool.map(_cpu_job, jobs))
    cpu = {key: np.concatenate([r[key] for r in values]) for key in values[0]}
    results = {dev: sim.mlx_log_evidence(name, draws, schedule, M=M, zf_seq=zf,
                                       chunk=n, device=dev) for dev in devices}
    return cpu, results, {'draws_sha256': hashlib.sha256(draws.tobytes()).hexdigest(),
                          'zf_float32_sha256': None if zf is None else hashlib.sha256(zf.tobytes()).hexdigest()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', choices=sim.PORTED, required=True)
    ap.add_argument('--streams', type=int, default=400)
    ap.add_argument('--m', type=int, default=32)
    ap.add_argument('--theta1', type=float, default=0)
    ap.add_argument('--seed', type=int, default=20260925)
    ap.add_argument('--devices', nargs='+', choices=('gpu', 'cpu'), default=['gpu'])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--check-drift', action='store_true', help='assert the 16-64 stream matched drift bounds')
    args = ap.parse_args()
    schedule = [(d, P) for d, P, _ in sim.reg.load() if d <= '2026-09-20']
    assert len(schedule) == 994, len(schedule)
    if args.theta1:
        assert args.m == 128
    cpu, results, inputs = matched(args.model, schedule, args.streams, args.m, args.seed,
                                   args.theta1, args.devices)
    out = {'_meta': sim.metadata(args.seed, schedule, args.m, args.streams, args.devices[0]),
           'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'model': args.model, 'n_streams': args.streams, 'theta1': args.theta1,
           'simulation': 'power' if args.theta1 else 'null', 'inputs': inputs,
           'drift_asserted': args.check_drift,
           'gaussians': 'CPU: zf.astype(float32).astype(float64); MLX: same float32 values',
           'bounds': BOUNDS, 'cpu': {}, 'devices': {}}
    keys = ('sup', 'final_log_e', 'log_sr_max', 'crossing', 'v0_final')
    out['cpu'] = {k: cpu[k].tolist() for k in keys if k in cpu}
    out['cpu']['summary'] = sim.crossing_summary(cpu, len(schedule))
    for dev, res in results.items():
        out['devices'][dev] = {'paired': paired_metrics(cpu, res), 'drift': drift_metrics(cpu['le'], res['le']),
            'summary': sim.crossing_summary(res, len(schedule)),
            'values': {k: res[k].tolist() for k in keys if k in res}}
    if set(results) == {'cpu', 'gpu'}:
        out['gpu_minus_mlx_cpu'] = {**paired_metrics(results['cpu'], results['gpu']),
                                  'le': difference(results['cpu']['le'], results['gpu']['le'])}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    for dev, res in results.items():
        assert_paired(out['devices'][dev]['paired'])
        if args.check_drift:
            assert_drift(out['devices'][dev]['drift'], cpu, res)
    print(json.dumps({k: {'paired': v['paired'], 'drift': v['drift']} for k, v in out['devices'].items()}), flush=True)


if __name__ == '__main__':
    main()
