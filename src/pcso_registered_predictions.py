#!/usr/bin/env python3
"""Novel-model next-draw tickets and walk-forward backtest (the picker's prediction source).

Models: the pcso.registry.seq1 roster (seed 20260923: six models and the ensemble) and the
pcso.sparse.seq1 model cp_sparse_switch. Every model runs through all rows in (date, game) order
the way the registered harness does: predict, then update (CP-NEST's predict draws its predictive
samples and sets the law its update uses, so it is called exactly once per row), and
cp_sparse_switch restarts its switching clock at the first draw dated after the registration date.
Each ticket is therefore made only from earlier draws. The backtest ticket is law.top6() (what the
registered overlap test scores); the next-draw ticket applies the C3 tie rule
(pcso_frozen_law.ticket_from_inclusion) to the native inclusion probabilities. The uniform model
is the baseline.

Writes results/pcso_registered_predictions_<run_date>.json (byte-deterministic):
  next_draw  per game and model: the ticket for that game's next draw after the last data row, its
             six predictive inclusion probabilities, and R = C(P,6) q(ticket), the ticket's
             predictive probability over the uniform-draw probability (a model statement, not a
             realized evidence increment). Each game is predicted from an independent copy of the
             post-history state (including RNG), as if that game's draw were the next row.
  backtest   per model and draw in the window (default: the 30 days ending at the last data row):
             ticket, actual draw, matches, log-evidence increment log q(S)/p0(S), and summaries.
             DESCRIPTIVE ONLY: eight models over a chosen window are not a registered test and
             carry no multiplicity control. Draws dated <= the registration date are exploratory
             (the models were designed with them). Registered decisions remain the registry's E/M
             processes and the C4 terminal analysis.
Prospective commitment and scoring are not part of this tool yet (pending registration
pcso.picker.prospective1). --verify recomputes the artifact and compares bytes without writing.

Usage: python3 src/pcso_registered_predictions.py --run-date YYYY-MM-DD [--backtest-days 30] [--verify]
"""
from __future__ import annotations

import argparse
import copy
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy

import pcso_model_registry as R
import pcso_sparse_registered as SR
import pcso_frozen_law as FL
from pcso_sparse_switch import CPSparseSwitch

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260923
SPARSE_REGISTRATION_DATE = SR.REGISTRATION_DATE
SCRIPT = "src/pcso_registered_predictions.py"
CODE = ("src/pcso_model_registry.py", "src/pcso_sparse_switch.py", "src/pcso_sparse_registered.py",
        "src/pcso_frozen_law.py", SCRIPT)
GAME = {P: g for g, P in R.POOL.items()}


def roster():
    base, ens = R.roster(SEED)
    return [*base, ens, CPSparseSwitch()]


def _log_e(law, P, S):
    return law.logq(tuple(S)) + math.log(math.comb(P, R.K))


def walk(models, rows, backtest_from, restart_sparse_after=SPARSE_REGISTRATION_DATE):
    """Predict-then-update over rows [(date, P, S)]; record tickets for draws dated >= backtest_from.

    log_e is kept at full precision here; it is rounded only when serialized."""
    per = {m.name: [] for m in models}
    restarted = False
    for d, P, S in rows:
        if not restarted and d > restart_sparse_after:
            for m in models:
                if isinstance(m, CPSparseSwitch):
                    m.t = 0            # pcso_sparse_registered.score: restart only the switching clock
            restarted = True
        for m in models:
            law = m.predict(P)
            if d >= backtest_from:
                ticket = sorted(int(b) for b in law.top6())
                per[m.name].append({"date": d, "game": GAME.get(P, str(P)), "P": P, "ticket": ticket,
                                    "actual": sorted(int(b) for b in S),
                                    "matches": len(set(ticket) & set(S)),
                                    "log_e": _log_e(law, P, S),
                                    "window": "registered" if d > R.REGISTERED_AFTER else "exploratory"})
            m.update(P, S)
    return per


def next_tickets(models, pools):
    """Each game's ticket from an independent deep copy of each model (state and RNG untouched)."""
    out = {}
    for P in pools:
        g = GAME.get(P, str(P))
        out[g] = {}
        for m in models:
            law = copy.deepcopy(m).predict(P)
            pi = law.inclusion()
            ticket = FL.ticket_from_inclusion(pi)
            out[g][m.name] = {"ticket": ticket,
                              "inclusion": [round(float(pi[b - 1]), 6) for b in ticket],
                              "uniform_inclusion": round(R.K / P, 6),
                              "R": round(math.exp(_log_e(law, P, ticket)), 6)}
    return out


def summarize(recs):
    def block(rs):
        if not rs:
            return {"draws": 0}
        o, e, p = R.exact_p([(r["P"], r["matches"]) for r in rs])
        return {"draws": len(rs), "matches": o, "expected_under_uniform": round(e, 3),
                "p_two_sided_exact_descriptive": round(p, 6),
                "draws_with_3plus": sum(r["matches"] >= 3 for r in rs),
                "expected_draws_with_3plus": round(sum(float(R.hyp(r["P"])[3:].sum()) for r in rs), 3),
                "log_evidence": round(math.fsum(r["log_e"] for r in rs), 6)}
    return {"all": block(recs),
            "exploratory": block([r for r in recs if r["window"] == "exploratory"]),
            "registered_in_window": block([r for r in recs if r["window"] == "registered"])}


def build(rows, run_date, backtest_days, input_sha, code_sha, provenance):
    last = max(d for d, _, _ in rows)
    lo = (date.fromisoformat(last) - timedelta(days=backtest_days)).isoformat()
    models = roster()
    per = walk(models, rows, lo)
    summary = {name: summarize(recs) for name, recs in per.items()}
    for recs in per.values():
        for r in recs:
            r["log_e"] = round(r["log_e"], 6)
    return {
        "_meta": {
            "schema_version": 1, "script": SCRIPT, "run_date": run_date, "seed": SEED,
            "last_data_date": last, "backtest_window": [lo, last], "n_rows": len(rows),
            "registered_after": R.REGISTERED_AFTER, "sparse_registration_date": SPARSE_REGISTRATION_DATE,
            "input_snapshot_commit": R.INPUT_SNAPSHOT_COMMIT,
            "input_sha256": input_sha, "code_sha256": code_sha, "registered_provenance": provenance,
            "environment": {"python": platform.python_version(), "numpy": np.__version__,
                            "scipy": scipy.__version__, "machine": platform.machine()},
            "ticket": "next_draw ticket: the C3 tie rule ticket_from_inclusion in src/pcso_frozen_law.py (six sequential picks, each the lowest-numbered remaining ball whose inclusion is within relative 1e-12 of the remaining maximum) applied to the NATIVE inclusion probabilities law.inclusion(), not to the reference evaluator of a frozen committed law (C3 step 1), so exact mathematical ties that the native evaluator separates by more than 1e-12 (pair_parity on pools with equal odd/even counts) are not resolved to lower numbers; descriptive only; backtest ticket: law.top6() (six largest inclusions, ties to the lower ball), identical to the registered harness overlap scoring",
            "R": "C(P,6) * q(ticket): the model's predictive probability of the exact ticket over the uniform-draw probability; a model statement, not a realized evidence increment",
            "baseline": "uniform model (every 6-set has probability 1/C(P,6))",
            "inference": "backtest summaries are DESCRIPTIVE: eight models over a chosen window, no multiplicity control, not a registered test; registered decisions are the registry E/M processes and the C4 terminal analysis",
            "windows": {"exploratory": "draws dated <= the registration date; the models were designed with them",
                        "registered": "draws dated after the registration date"},
            "next_draw_note": "each game is predicted from an independent copy of the post-history state, as if its draw were the next row; a draw of another game in between would update the models first"},
        "next_draw": next_tickets(models, sorted({P for _, P, _ in rows})),
        "backtest": {"summary": summary, "per_draw": per},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-date", required=True, type=lambda s: date.fromisoformat(s).isoformat())
    ap.add_argument("--backtest-days", type=int, default=30)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--tag", default="", type=lambda s: s if all(c.isalnum() for c in s) else ap.error("--tag must be alphanumeric"),
                    help="optional suffix for a second run on the same date (e.g. d0926 = data through 2026-09-26)")
    args = ap.parse_args(argv)
    dst = ROOT / "results" / f"pcso_registered_predictions_{args.run_date}{'_' + args.tag if args.tag else ''}.json"
    rel = dst.relative_to(ROOT).as_posix()
    try:
        if not args.verify and dst.exists():
            raise ValueError(f"refusing to overwrite existing output: {rel}")
        draws_rel = R.DRAWS.relative_to(ROOT).as_posix()
        snapshot = {p: (ROOT / p).read_bytes() for p in (draws_rel, *CODE)}
        hashes = {p: hashlib.sha256(b).hexdigest() for p, b in snapshot.items()}
        input_sha = {draws_rel: hashes[draws_rel]}
        code_sha = {p: hashes[p] for p in CODE}
        if args.verify:
            expected = dst.read_bytes()
            meta = json.loads(expected)["_meta"]
            if meta["input_sha256"] != input_sha or meta["code_sha256"] != code_sha:
                raise ValueError("input or code differs from the record; byte verification needs the recorded state")
        provenance = SR._qualify_registered(snapshot[draws_rel])
        rows = R.load()
        payload = (json.dumps(build(rows, args.run_date, args.backtest_days, input_sha, code_sha, provenance),
                              indent=1, sort_keys=True, allow_nan=False) + "\n").encode()
        if {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in snapshot} != hashes:
            raise ValueError("input or code changed during the run")
        digest = hashlib.sha256(payload).hexdigest()
        if args.verify:
            if payload != expected:
                raise ValueError(f"VERIFY FAIL: byte mismatch: {rel}")
            print(f"PASS sha256={digest}")
            return
        with dst.open("xb") as f:
            f.write(payload)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(f"wrote {rel} sha256={digest}")


if __name__ == "__main__":
    main()
