#!/usr/bin/env python3
"""Sharded exploratory pcso.cpnest.sensitivity1 runner; never launches a grid.

Each data/cell/check64 invocation handles an explicit [lo, hi) range and is supervised
for 295 seconds. Use data once per arm/range, cell for each declared cell, and check64
for each check/range. Aggregate requires complete, nonoverlapping coverage. For example:
  python tools/pcso_cpnest_sensitivity.py data --arm null --lo 0 --hi 50
  python tools/pcso_cpnest_sensitivity.py cell --arm null --lo 0 --hi 50 --backend mlx
  python tools/pcso_cpnest_sensitivity.py check64 --check registered_null --lo 0 --hi 1
  python tools/pcso_cpnest_sensitivity.py aggregate --run-date 2026-09-25
`plan` prints every shard command of the full study without executing anything:
  python tools/pcso_cpnest_sensitivity.py plan --null-shard 50 --power-shard 20 --check-shard 10
Small smoke prefixes use --max-draws and cannot be accepted by aggregate.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pcso_mlx_sim as sim

reg = sim.reg
SEED = 20260923
THETAS = (0.025, 0.05, 0.10)
NULL_N, POWER_N = 20000, 2000
NULL_T, POWER_T = 1001, 3003
N1_ALPHA = 0.05 / 18
TOLERANCE = 1e-3
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20260923
PIN = "1ce8541"
# Derived from sorted registry rows at PIN; verification works on the git-free M5 copy.
SCHEDULE_SHA256 = "7ebcf8f0a8ec8ccf51a7f6210de665c9c2999ce65e3303d341f57c9ebe5210e5"
PIN_INPUT_SHA256 = "54d5e85b6e07c918213fdf39852cea5cfafc42d66365ccc8ede78315a441e0f5"
SOURCES = ("tools/pcso_cpnest_sensitivity.py", "src/pcso_mlx_sim.py", "src/pcso_model_registry.py",
           "tools/pcso_mlx_remote.py")
SPEC = "docs/STUDY_PCSO_CPNEST_SENSITIVITY.md"
SUMMARY_KEYS = ("sup", "final_log_e", "crossing", "log_sr_max", "v0_final", "n2_excess")
NOT_REACHED = "not_reached_by_horizon"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def code_hashes():
    return {p: digest((ROOT / p).read_bytes()) for p in SOURCES}


@dataclass(frozen=True)
class Cell:
    tau: float = reg.CPNest.TAU
    rho: float = reg.CPNest.RHO
    v0: str = "geom"
    M: int = 128

    def __post_init__(self):
        if self.v0 not in ("geom", "uniform") or self.M < 2 or self.M % 2:
            raise ValueError("v0 must be geom/uniform and M must be positive and even")
        sim.cp_prior(self.tau, self.rho)

    @property
    def prior(self):
        return sim.cp_prior(self.tau, self.rho, np.ones(7) if self.v0 == "uniform" else None)

    @property
    def key(self):
        return f"tau{self.tau:g}_rho{self.rho:g}_{self.v0}_m{self.M}"


REGISTERED = Cell()
GRID = tuple(Cell(tau, rho) for tau in (0.01, 0.025, 0.05, 0.10, 0.20)
             for rho in (0.0, 0.001, 0.01)) + (Cell(M=32), Cell(M=512), Cell(v0="uniform"))
CHECKS = {
    "registered_null": (REGISTERED, "null", 0.0, 200),
    "small_tau_null": (Cell(0.01, 0.0), "null", 0.0, 200),
    "large_tau_null": (Cell(0.20, 0.01), "null", 0.0, 200),
    "uniform_null": (Cell(v0="uniform"), "null", 0.0, 200),
    "m512_null": (Cell(M=512), "null", 0.0, 100),
    "registered_power": (REGISTERED, "power", 0.05, 200),
}


def pinned_schedule():
    raw = reg.DRAWS.read_bytes()
    # Only (date, pool) is used. Real outcomes never enter a simulation.
    rows = sorted(reg._parse_rows(raw.decode("utf-8-sig")))
    schedule = [(d, P) for d, _, P, _ in rows if d <= "2026-09-23"]
    sha = digest(json.dumps(schedule, separators=(",", ":")).encode())
    if len(schedule) != NULL_T or sha != SCHEDULE_SHA256:
        raise ValueError("schedule differs from conditioning pin 1ce8541")
    return schedule, {"schedule_pin": PIN, "schedule_sha256": sha,
                      "pinned_input_sha256": PIN_INPUT_SHA256,
                      "input_sha256": {str(reg.DRAWS.relative_to(ROOT)): digest(raw),
                                       SPEC: digest((ROOT / SPEC).read_bytes())}}


def arm_index(arm, theta1):
    if arm == "null" and theta1 == 0:
        return 0, 0
    if arm == "power" and theta1 in THETAS:
        return 1, THETAS.index(theta1)
    raise ValueError("null requires theta1=0; power requires theta1 in 0.025, 0.05, 0.10")


def stream_range(lo, hi, limit):
    if not 0 <= lo < hi <= limit:
        raise ValueError(f"require 0 <= lo < hi <= {limit}")


def generate_draws(schedule, arm, theta1, lo, hi):
    a, index = arm_index(arm, theta1)
    stream_range(lo, hi, NULL_N if a == 0 else POWER_N)
    return np.array([[S for _, _, S in reg.synthetic(
        np.random.default_rng(np.random.SeedSequence([SEED, a, index, s])), schedule, theta1)]
        for s in range(lo, hi)], dtype=np.int32)


def generate_normals(T, M, lo, hi):
    """Round once to float32; the float64 reference replays these exact same values."""
    return np.array([np.random.default_rng(np.random.SeedSequence([SEED, 1, M, s]))
                     .standard_normal((T, M // 2, 6)).astype(np.float32)
                     for s in range(lo, hi)])


def save_npz(path, values, meta):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as f:
        np.savez_compressed(f, **values, metadata=np.array(json_bytes(meta).decode()))
    temporary.replace(path)


def read_npz(path):
    with np.load(path, allow_pickle=False) as data:
        return ({k: data[k] for k in data.files if k != "metadata"},
                json.loads(str(data["metadata"])))


def arm_key(arm, theta1):
    a, index = arm_index(arm, theta1)
    return "null" if a == 0 else f"power_theta{index}"


def cache_draws(cache, schedule, arm, theta1, lo, hi, schedule_meta):
    """A file per global stream lets every shard and every cell share the same draws."""
    folder = cache / "data" / arm_key(arm, theta1) / f"t{len(schedule)}"
    arrays, hashes = [], {}
    for s in range(lo, hi):
        path = folder / f"s{s:05d}.npz"
        expected = {**schedule_meta, "arm": arm, "theta1": theta1, "s": s,
                    "T": len(schedule), "data_seed": [SEED, *arm_index(arm, theta1), s]}
        if path.exists():
            values, meta = read_npz(path)
            if any(meta.get(k) != v for k, v in expected.items()):
                raise ValueError(f"stale data cache: {path}")
            draws = values["draws"]
            if draws.shape != (len(schedule), 6) or digest(draws.tobytes()) != meta["draws_sha256"]:
                raise ValueError(f"corrupt data cache: {path}")
        else:
            draws = generate_draws(schedule, arm, theta1, s, s + 1)[0]
            save_npz(path, {"draws": draws}, {**expected, "draws_sha256": digest(draws.tobytes())})
        arrays.append(draws)
        hashes[str(s)] = digest(draws.tobytes())
    return np.array(arrays), hashes


class ReferenceCPNest(reg.CPNest):
    """Float64 reference: only class constants and the initial level prior change."""
    TAU, RHO = reg.CPNest.TAU, reg.CPNest.RHO

    def __init__(self, *, M, v0):
        super().__init__(M=M)
        self.v = sim.cp_prior(self.TAU, self.RHO, v0)


def cpu_evidence(cell, draws, schedule, normals):
    class CellCPNest(ReferenceCPNest):
        TAU, RHO = cell.tau, cell.rho

    le, final_v0 = np.empty(draws.shape[:2]), np.empty(len(draws))
    for s in range(len(draws)):
        model = CellCPNest(M=cell.M, v0=cell.prior)
        model.rng = sim._ZFQueue(normals[s])
        for t, (_, P) in enumerate(schedule):
            S = draws[s, t]
            le[s, t] = model.predict(P).logq(S) + math.log(math.comb(P, 6))
            model.update(P, S)
        final_v0[s] = model.v[0]
    return {**sim.evidence_summary(le), "v0_final": final_v0}


def n2_excess(cumulative, rho, v00):
    cumulative = np.asarray(cumulative, dtype=np.float64)
    bound = -math.log(v00) - np.arange(cumulative.shape[-1]) * math.log1p(-6 * rho / 7)
    return np.max(-cumulative - bound, axis=-1)


def evaluate(cell, draws, schedule, normals, backend="cpu", chunk=50):
    if chunk <= 0 or backend not in ("cpu", "mlx"):
        raise ValueError("positive chunk and cpu/mlx backend required")
    if backend == "cpu":
        # Exercise the same chunk boundary on the CPU reference without altering stream state.
        parts = [cpu_evidence(cell, draws[i:i + chunk], schedule, normals[i:i + chunk])
                 for i in range(0, len(draws), chunk)]
        result = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    else:
        result = sim.mlx_log_evidence("cp_nest", draws, schedule, M=cell.M, chunk=chunk,
                                      zf_seq=normals, device="gpu", tau=cell.tau,
                                      rho=cell.rho, v0=cell.prior)
    result["n2_excess"] = n2_excess(np.cumsum(result["le"], axis=1, dtype=np.float64),
                                    cell.rho, cell.prior[0])
    if any(not np.isfinite(v).all() for v in result.values()):
        raise ValueError("nonfinite evidence or model state")
    return result


def environment(backend):
    if backend == "mlx" and sim.mx is None:
        raise RuntimeError("mlx is not installed; run on the M5")
    return {"backend": backend, "dtype": "float64" if backend == "cpu" else "float32",
            "mlx_version": version("mlx") if sim.mx is not None else None,
            "device": "cpu" if backend == "cpu" else str(sim.mx.gpu),
            "device_info": sim.mx.device_info() if sim.mx is not None else None}


def provenance(schedule_meta):
    return {**schedule_meta, "code_sha256": code_hashes(), "seed": SEED,
            "draw_seed": "SeedSequence([20260923, arm, theta_index, s])",
            "normal_seed": "SeedSequence([20260923, 1, M, s])",
            "normal_dtype": "float64 standard_normal rounded once to float32; CPU replays as float64",
            "sup_units": "log evidence (including E_0=1)", "status": "G0 exploratory"}


def comparator(cache, draws, schedule, theta1, lo, backend, common):
    """Compute tilt_linear once per theta/stream, independent of the grid cell and M."""
    folder = cache / "comparators" / arm_key("power", theta1) / f"t{len(schedule)}"
    expected = {**common, "kind": "comparator", "theta1": theta1, "T": len(schedule)}
    missing = []
    for i, row in enumerate(draws):
        path = folder / f"s{lo + i:05d}.npz"
        if path.exists():
            _, meta = read_npz(path)
            # A hit must match the writing backend and environment exactly: an MLX-computed
            # tilt_linear stream never serves a CPU run.
            want = {**expected, **environment(backend), "s": lo + i, "draws_sha256": digest(row.tobytes())}
            if any(meta.get(k) != v for k, v in want.items()):
                raise ValueError(f"stale comparator: {path}")
        else:
            missing.append(i)
    if missing:
        if backend == "mlx":
            result = sim.mlx_log_evidence("tilt_linear", draws[missing], schedule,
                                          chunk=len(missing), device="gpu")
        else:
            result = sim.cpu_log_evidence("tilt_linear", draws[missing], schedule, summary=True)
        for j, i in enumerate(missing):
            save_npz(folder / f"s{lo + i:05d}.npz",
                     {k: np.asarray(v[j:j + 1]) for k, v in result.items() if k != "le"},
                     {**expected, **environment(backend), "s": lo + i,
                      "draws_sha256": digest(draws[i].tobytes())})


def p_measures(crossing, horizon=POWER_T):
    crossing = np.asarray(crossing)
    validate_crossing(crossing, horizon)
    k, n = int((crossing >= 1).sum()), len(crossing)
    return {"n": n, "P1": k / n, "P1_lower": reg.clopper_pearson_lower(k, n, alpha=0.05),
            "P2": reg.censored_median(crossing, horizon)}


def p2_number(value):
    return math.inf if value == NOT_REACHED else float(value)


def ratio(a, b):
    """An infinity/infinity ratio is undefined, not evidence for a finite ratio."""
    if math.isinf(a) and math.isinf(b):
        return None
    return a / b


def finite_json(value):
    if value is None:
        return "undefined"
    return "infinity" if math.isinf(value) else float(value)


def paired_ratio(a, b, horizon=POWER_T):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.ndim != 1 or not len(a):
        raise ValueError("paired crossing arrays must have identical nonempty shapes")
    n = len(a)
    aa, bb = np.where(a < 0, np.inf, a), np.where(b < 0, np.inf, b)
    point = ratio(p2_number(reg.censored_median(a, horizon)), p2_number(reg.censored_median(b, horizon)))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values, undefined = [], 0
    for _ in range(BOOTSTRAP_N):
        ids = rng.integers(0, n, n)
        mid = (n - 1) // 2
        value = ratio(np.partition(aa[ids], mid)[mid], np.partition(bb[ids], mid)[mid])
        if value is None:
            undefined += 1
        else:
            values.append(value)
    # Order-statistic endpoints avoid interpolation involving infinity. Do not silently
    # drop undefined resamples and present a conditional interval as an unconditional CI.
    interval = None if undefined else [finite_json(v) for v in
                                       np.quantile(values, [0.025, 0.975], method="inverted_cdf")]
    return {"ratio": finite_json(point), "ci_95": interval, "undefined_resamples": undefined,
            "resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED,
            "interval_method": "paired percentile, inverse empirical CDF",
            "undefined_reason": "infinity/infinity" if undefined or point is None else None}


def null_measures(result):
    n = len(result["sup"])
    k = int((result["sup"] >= math.log(100)).sum())
    excess = np.asarray(result["n2_excess"])
    lower = reg.clopper_pearson_lower(k, n, alpha=N1_ALPHA)
    n2 = float(np.mean(excess <= TOLERANCE))
    cost = -np.asarray(result["final_log_e"])
    return {"n": n, "N1": k / n, "N1_lower": lower, "N1_alpha": N1_ALPHA,
            "N2": n2, "n2_max_excess": float(excess.max()),
            "gate": lower <= 0.01 and n2 == 1.0,
            "null_cost_median": float(np.median(cost)), "null_cost_p90": float(np.quantile(cost, .9)),
            "v0_final_median": float(np.median(result["v0_final"])),
            "sup_E_median": float(np.median(np.exp(result["sup"]))),
            "sr_fraction_ge_100": float(np.mean(result["log_sr_max"] >= math.log(100)))}


def selection_key(row):
    c, p = Cell(**row["cell"]), row["selection"]
    return (p2_number(p["P2"]), -p["P1"], c != REGISTERED, c.tau, c.rho,
            c.M != 128, c.v0 != "geom")


def verdict(rows):
    """Rows hold disjoint selection/evaluation summaries at primary theta1=0.05."""
    if any(not row["gate"] for row in rows):
        return {"verdict": "DEFECT", "B": None}
    # GRID order breaks the spec's residual M=32 vs M=512 tie deterministically.
    candidates = sorted(rows, key=lambda r: GRID.index(Cell(**r["cell"])))
    best = min(candidates, key=selection_key)
    registered = next(r for r in rows if Cell(**r["cell"]) == REGISTERED)
    b, r = best["evaluation"], registered["evaluation"]
    if math.isinf(p2_number(b["P2"])):
        label = "UNINFORMATIVE"
    elif p2_number(r["P2"]) <= 1.25 * p2_number(b["P2"]) and r["P1"] >= b["P1"] - .05:
        label = "ROBUST"
    else:
        label = "SENSITIVE"
    return {"verdict": label, "B": best["cell"], "selection_B": best["selection"],
            "evaluation_registered": r, "evaluation_B": b}


def validate_meta(meta, expected):
    if any(meta.get(k) != v for k, v in expected.items()):
        raise ValueError("artifact provenance or dimensions differ from this study/code")


def validate_crossing(crossing, horizon):
    if (crossing.ndim != 1 or not len(crossing) or not np.isfinite(crossing).all()
            or np.any((crossing != -1) & ((crossing < 1) | (crossing > horizon)))
            or np.any(crossing != np.floor(crossing))):
        raise ValueError("crossing must contain draw indices 1..T or -1")


def validate_pairing(meta, paired):
    """Match stream hashes across cells and float64 checks regardless of shard layout."""
    hashes = meta["draws_sha256"]
    if set(hashes) != {str(s) for s in range(meta["lo"], meta["hi"])}:
        raise ValueError("incomplete per-stream input hashes")
    for s, sha in hashes.items():
        key = (meta["arm"], meta["theta1"], int(s))
        if paired.setdefault(key, sha) != sha:
            raise ValueError(f"draw pairing mismatch for {key}")


def coverage(pieces, n, keys):
    """Reject gaps, overlaps, wrong shapes, and nonfinite numerical summaries."""
    seen = np.zeros(n, dtype=bool)
    out = {k: np.empty(n, dtype=np.float64) for k in keys}
    for values, meta in pieces:
        lo, hi = meta["lo"], meta["hi"]
        stream_range(lo, hi, n)
        if seen[lo:hi].any():
            raise ValueError("overlapping shards")
        for k in keys:
            value = values[k]
            if value.shape != (hi - lo,) or not np.isfinite(value).all():
                raise ValueError(f"invalid shard array: {k}")
            out[k][lo:hi] = value
        seen[lo:hi] = True
    if not seen.all():
        raise ValueError(f"incomplete coverage: {seen.sum()}/{n} streams")
    return out


def validated_checks(cache, common, paired=None):
    report, failed = {}, []
    for name, (cell, arm, theta, n) in CHECKS.items():
        pieces, artifacts = [], {}
        for path in sorted((cache / "checks" / name).glob("*.npz")):
            values, meta = read_npz(path)
            validate_meta(meta, {**common, "kind": "check64", "check": name, "cell": asdict(cell),
                                 "arm": arm, "theta1": theta, "T": NULL_T if arm == "null" else POWER_T})
            pieces.append((values, meta))
            if paired is not None:
                validate_pairing(meta, paired)
            artifacts[str(path.relative_to(cache))] = {"sha256": digest(path.read_bytes()), "metadata": meta}
        values = coverage(pieces, n, ("max_abs_delta_log_e",))
        maximum = float(values["max_abs_delta_log_e"].max())
        if np.any(values["max_abs_delta_log_e"] < 0):
            raise ValueError("absolute residuals cannot be negative")
        report[name] = {"n": n, "max_abs_delta_log_e": maximum, "pass": maximum <= TOLERANCE,
                        "artifacts": artifacts}
        if maximum > TOLERANCE:
            failed.append(name)
    return report, failed


def needs_cpu(cell, arm, failed):
    # §7: sharing any failing horizon, M, or v0 requires a complete CPU rerun.
    return any(arm == CHECKS[name][1] or cell.M == CHECKS[name][0].M
               or cell.v0 == CHECKS[name][0].v0 for name in failed)


def collect_cell(cache, cell, arm, theta, backend, common, paired=None):
    pieces, artifacts = [], {}
    folder = cache / "cells" / cell.key / arm_key(arm, theta)
    for path in sorted(folder.glob(f"*-{backend}.npz")):
        values, meta = read_npz(path)
        validate_meta(meta, {**common, "kind": "cell", "cell": asdict(cell), "arm": arm,
                             "theta1": theta, "backend": backend,
                             "T": NULL_T if arm == "null" else POWER_T})
        pieces.append((values, meta))
        if paired is not None:
            validate_pairing(meta, paired)
        artifacts[str(path.relative_to(cache))] = {"sha256": digest(path.read_bytes()), "metadata": meta}
    n = NULL_N if arm == "null" else POWER_N
    result = coverage(pieces, n, SUMMARY_KEYS)
    validate_crossing(result["crossing"], NULL_T if arm == "null" else POWER_T)
    if (np.any((result["crossing"] != -1) != (result["sup"] >= math.log(100)))
            or np.any(result["sup"] < 0) or np.any(result["final_log_e"] > result["sup"])
            or np.any((result["v0_final"] < 0) | (result["v0_final"] > 1))):
        raise ValueError("inconsistent cell summaries")
    return result, artifacts


def collect_comparator(cache, theta, common, paired=None):
    pieces, artifacts = [], {}
    folder = cache / "comparators" / arm_key("power", theta) / f"t{POWER_T}"
    for s in range(POWER_N):
        path = folder / f"s{s:05d}.npz"
        values, meta = read_npz(path)
        validate_meta(meta, {**common, "kind": "comparator", "theta1": theta, "T": POWER_T, "s": s})
        # Verify pairing against the shared data cache, not just a same-sized array.
        _, data_meta = read_npz(cache / "data" / arm_key("power", theta) / f"t{POWER_T}" / f"s{s:05d}.npz")
        if meta["draws_sha256"] != data_meta["draws_sha256"]:
            raise ValueError("comparator draw pairing mismatch")
        if paired is not None and paired[("power", theta, s)] != meta["draws_sha256"]:
            raise ValueError("comparator/cell draw pairing mismatch")
        pieces.append((values, {"lo": s, "hi": s + 1}))
        artifacts[str(path.relative_to(cache))] = digest(path.read_bytes())
    return coverage(pieces, POWER_N, ("crossing",))["crossing"], artifacts


def aggregate(cache, common):
    paired = {}
    checks, failed = validated_checks(cache, common, paired)
    out = {"_meta": {**common, "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_resamples": BOOTSTRAP_N,
                      "grid": [asdict(c) for c in GRID], "M": [32, 128, 512],
                      "conventions": {"residual_M_tie": "declared grid order (32 before 512)",
                                      "infinity_over_infinity": "undefined; no CI if any resample is undefined",
                                      "uninformative": "B evaluation-half P2 not reached, per section 6 step 2"}},
           "checks64": checks, "failed_checks": failed, "cells": [], "artifacts": {}}
    # Stop at the theorem gate, before computing any power conclusions.
    for cell in GRID:
        backend = "cpu" if needs_cpu(cell, "null", failed) else "mlx"
        null, artifacts = collect_cell(cache, cell, "null", 0.0, backend, common, paired)
        out["artifacts"].update(artifacts)
        out["cells"].append({"cell": asdict(cell), "null_backend": backend, "null": null_measures(null)})
    if any(not row["null"]["gate"] for row in out["cells"]):
        out.update(verdict="DEFECT", accepted=False,
                   defect_cells=[r["cell"] for r in out["cells"] if not r["null"]["gate"]])
        return out
    comparators = {}
    primary, rows = {}, []
    for row, cell in zip(out["cells"], GRID):
        backend = "cpu" if needs_cpu(cell, "power", failed) else "mlx"
        row["power"], row["power_backend"] = {}, backend
        for theta in THETAS:
            result, artifacts = collect_cell(cache, cell, "power", theta, backend, common, paired)
            out["artifacts"].update(artifacts)
            if theta not in comparators:
                comparators[theta], artifacts = collect_comparator(cache, theta, common, paired)
                out["artifacts"].update(artifacts)
            crossing = result["crossing"]
            measures = {"full": p_measures(crossing), "selection": p_measures(crossing[:1000]),
                        "evaluation": p_measures(crossing[1000:]),
                        "P3": paired_ratio(crossing, comparators[theta])}
            row["power"][str(theta)] = measures
            if theta == 0.05:
                primary[cell] = crossing
                rows.append({"cell": asdict(cell), "gate": True,
                             "selection": measures["selection"], "evaluation": measures["evaluation"]})
    decision = verdict(rows)
    best = Cell(**decision["B"])
    decision["evaluation_P2_reg_over_B"] = paired_ratio(primary[REGISTERED][1000:], primary[best][1000:])
    decision["full_registered"] = p_measures(primary[REGISTERED])
    decision["full_B"] = p_measures(primary[best])
    out.update(decision=decision, verdict=decision["verdict"], accepted=True,
               comparator={str(theta): p_measures(values) for theta, values in comparators.items()})
    return out


def plan_lines(null_shard, power_shard, check_shard, backend):
    """Every shard command of the full study in dependency order; plan never executes."""
    if min(null_shard, power_shard, check_shard) < 1:
        raise ValueError("shard sizes must be positive stream counts")

    def tile(limit, shard):
        return [(lo, min(lo + shard, limit)) for lo in range(0, limit, shard)]

    arms = (("null", None, NULL_N, null_shard), *(("power", t, POWER_N, power_shard) for t in THETAS))

    def stream_command(kind, arm, theta, middle, lo, hi):
        theta_opt = "" if theta is None else f" --theta1 {theta:g}"
        return (f"python tools/pcso_cpnest_sensitivity.py {kind} --arm {arm}{theta_opt}{middle}"
                f" --lo {lo} --hi {hi}")

    lines = [stream_command("data", arm, theta, "", lo, hi)
             for arm, theta, limit, shard in arms for lo, hi in tile(limit, shard)]
    lines += [f"python tools/pcso_cpnest_sensitivity.py check64 --check {name} --lo {lo} --hi {hi}"
              for name, (_, _, _, n) in CHECKS.items() for lo, hi in tile(n, check_shard)]
    lines += [stream_command("cell", arm, theta,
                             f" --tau {cell.tau:g} --rho {cell.rho:g} --v0 {cell.v0} --m {cell.M}",
                             lo, hi) + f" --backend {backend}"
              for cell in GRID for arm, theta, limit, shard in arms for lo, hi in tile(limit, shard)]
    return lines


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    for command in ("data", "cell", "check64", "aggregate"):
        p = sub.add_parser(command)
        p.add_argument("--cache", type=Path, default=Path("results/exploratory/pcso_cpnest_sensitivity_cache"))
        if command == "aggregate":
            p.add_argument("--run-date", default=date.today().isoformat())
            continue
        p.add_argument("--lo", type=int, required=True)
        p.add_argument("--hi", type=int, required=True)
        if command == "check64":
            p.add_argument("--check", choices=CHECKS, required=True)
        else:
            p.add_argument("--arm", choices=("null", "power"), required=True)
            p.add_argument("--theta1", type=float, default=0.0)
            p.add_argument("--max-draws", type=int, default=0, help="smoke only; aggregate rejects a truncated horizon")
        if command == "cell":
            p.add_argument("--tau", type=float, default=reg.CPNest.TAU)
            p.add_argument("--rho", type=float, default=reg.CPNest.RHO)
            p.add_argument("--v0", choices=("geom", "uniform"), default="geom")
            p.add_argument("--m", type=int, choices=(32, 128, 512), default=128)
            p.add_argument("--backend", choices=("mlx", "cpu"), default="mlx")
            p.add_argument("--chunk", type=int, default=50)
    p = sub.add_parser("plan")
    p.add_argument("--null-shard", type=int, required=True, help="streams per call, null arm")
    p.add_argument("--power-shard", type=int, required=True, help="streams per call, each power theta1")
    p.add_argument("--check-shard", type=int, required=True, help="streams per call, each check64")
    p.add_argument("--backend", choices=("mlx", "cpu"), default="mlx")
    return ap


def main(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    start = time.perf_counter()
    try:
        if args.command == "plan":
            for line in plan_lines(args.null_shard, args.power_shard, args.check_shard, args.backend):
                print(line, flush=True)
            return 0
        base, schedule_meta = pinned_schedule()
        common = provenance(schedule_meta)
        if args.command == "aggregate":
            run_date = date.fromisoformat(args.run_date).isoformat()
            out = aggregate(args.cache, common)
            path = ROOT / "results" / "exploratory" / f"pcso_cpnest_sensitivity_{run_date}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
            print(json.dumps({"output": str(path.relative_to(ROOT)), "verdict": out["verdict"]}), flush=True)
            return 0 if out["accepted"] else 2
        if args.command == "check64":
            cell, arm, theta, limit = CHECKS[args.check]
            backend, max_draws = "mlx", 0
        else:
            arm, theta = args.arm, args.theta1
            arm_index(arm, theta)
            limit, max_draws = (NULL_N if arm == "null" else POWER_N), args.max_draws
            backend = args.backend if args.command == "cell" else "cpu"
            cell = Cell(args.tau, args.rho, args.v0, args.m) if args.command == "cell" else None
            if cell is not None and cell not in GRID:
                raise ValueError("CLI cells must belong to the declared 18-cell grid")
        # No fixed shard cap: the 295 s process-group supervisor bounds every call and
        # partial jobs never save. stream_range still rejects out-of-bounds ranges.
        stream_range(args.lo, args.hi, limit)
        if args.command != "data":
            environment(backend)
        if args.command == "cell" and args.chunk <= 0:
            raise ValueError("chunk must be positive")
        schedule = base * (3 if arm == "power" else 1)
        if max_draws < 0 or max_draws > len(schedule):
            raise ValueError("invalid smoke horizon")
        if max_draws:
            schedule = schedule[:max_draws]
        draws, hashes = cache_draws(args.cache, schedule, arm, theta, args.lo, args.hi, schedule_meta)
        if args.command == "data":
            print(json.dumps({"command": "data", "lo": args.lo, "hi": args.hi, "T": len(schedule),
                              "seconds": time.perf_counter() - start}), flush=True)
            return 0
        sim.validate_power_m(cell.M, theta, sensitivity=True)
        normals = generate_normals(len(schedule), cell.M, args.lo, args.hi)
        meta = {**common, **environment(backend), "kind": args.command, "cell": asdict(cell),
                "arm": arm, "theta1": theta, "lo": args.lo, "hi": args.hi, "T": len(schedule),
                "draws_sha256": hashes, "normals_sha256": digest(normals.tobytes())}
        if args.command == "check64":
            cpu = evaluate(cell, draws, schedule, normals, "cpu", args.hi - args.lo)
            gpu = evaluate(cell, draws, schedule, normals, "mlx", args.hi - args.lo)
            delta = np.max(np.abs(np.cumsum(cpu["le"], axis=1, dtype=np.float64)
                                  - np.cumsum(gpu["le"], axis=1, dtype=np.float64)), axis=1)
            values = {"max_abs_delta_log_e": delta}
            meta.update(check=args.check, tolerance=TOLERANCE, passed=bool(np.all(delta <= TOLERANCE)))
            path = args.cache / "checks" / args.check / f"{args.lo:05d}-{args.hi:05d}.npz"
        else:
            result = evaluate(cell, draws, schedule, normals, backend, args.chunk)
            values = {k: result[k] for k in SUMMARY_KEYS}
            meta["chunk"] = args.chunk
            if arm == "power":
                comparator(args.cache, draws, schedule, theta, args.lo, backend, common)
            path = args.cache / "cells" / cell.key / arm_key(arm, theta) / f"{args.lo:05d}-{args.hi:05d}-{backend}.npz"
        elapsed = time.perf_counter() - start
        meta["seconds"] = elapsed
        save_npz(path, values, meta)
        report = {"command": args.command, "output": str(path), "streams": args.hi - args.lo,
                  "T": len(schedule), "seconds": elapsed,
                  "seconds_per_50_streams": elapsed * 50 / (args.hi - args.lo)}
        if args.command == "check64":
            report.update(passed=meta["passed"], max_abs_delta_log_e=float(delta.max()))
        print(json.dumps(report), flush=True)
        return 2 if args.command == "check64" and not meta["passed"] else 0
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        ap.error(str(exc))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        sys.exit(main(sys.argv[2:]))
    # Same process-group supervisor as every remote command: partial jobs never become
    # accepted artifacts, and descendants cannot outlive the shard deadline.
    from pcso_mlx_remote import SUPERVISOR
    sys.exit(subprocess.run([sys.executable, "-c", SUPERVISOR, "295", sys.executable,
                             str(Path(__file__).resolve()), "--worker", *sys.argv[1:]],
                            timeout=300).returncode)
