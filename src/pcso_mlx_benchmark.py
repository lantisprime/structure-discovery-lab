#!/usr/bin/env python3
"""One bounded, independently repeatable CPU/MLX NULL benchmark job.

Wall time includes sampling and harness/evaluation, CPU worker startup or GPU
compilation, and host summaries. Imports and JSON serialization are excluded.
Run each job under a 300-second process-group timeout on the M5.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pcso_mlx_sim as sim


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", choices=sim.MODELS, required=True)
    ap.add_argument("--backend", choices=("cpu", "mlx"), required=True)
    ap.add_argument("--streams", type=int, required=True)
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--device", choices=("gpu", "cpu"), default="gpu")
    ap.add_argument("--max-draws", type=int, default=0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.streams <= 0 or args.workers <= 0 or args.chunk <= 0 or args.max_draws < 0:
        ap.error("positive streams, workers and chunk; nonnegative max-draws required")
    schedule = [(d, P) for d, P, _ in sim.reg.load()]
    if args.max_draws:
        schedule = schedule[:args.max_draws]
    start = time.perf_counter()
    if args.backend == "cpu":
        result = sim.cpu_null(args.model, args.streams, schedule, args.seed, workers=args.workers)
    else:
        draws = sim.cp_streams(schedule, args.streams, np.random.default_rng(args.seed))
        result = sim.mlx_log_evidence(args.model, draws, schedule, seed=args.seed, chunk=args.chunk, device=args.device)
    seconds = time.perf_counter() - start
    metadata = sim.metadata(args.seed, schedule, 32, args.chunk, args.device)
    metadata["backend"] = args.backend
    if args.backend == "cpu":
        metadata.update(dtype="float64", execution_device="CPU")
    out = {"_meta": metadata, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "model": args.model, "n_streams": args.streams,
           "workers": args.workers if args.backend == "cpu" else None,
           "wall_s": seconds, "sup": result["sup"].tolist(),
           "log_sr_max": result["log_sr_max"].tolist()}
    if args.backend == "mlx":
        out["summary"] = sim.crossing_summary(result, len(schedule))
    out["implementation"] = "analytic reference (no GPU computation)" if args.model == "uniform" else args.backend
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ("model", "n_streams", "wall_s")} ), flush=True)


if __name__ == "__main__":
    main()
