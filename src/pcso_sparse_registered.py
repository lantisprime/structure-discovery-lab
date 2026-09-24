#!/usr/bin/env python3
"""Score cp_sparse_switch under registration pcso.sparse.seq1.

Condition on draws through 2026-09-23, retain the learned weights, and restart
the switching clock and registered evidence accounting for subsequent draws.
Outputs a deterministic evidence-process and hypothesis-test record. --verify
recomputes the record from current code and input and compares bytes without writing.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

import pcso_model_registry as R
from pcso_sparse_switch import CPSparseSwitch

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "results"
REGISTRATION_DATE = "2026-09-23"
REGISTRATION = "docs/REGISTRATION_PCSO_SPARSE_SWITCH.md"
SCRIPT = "src/pcso_sparse_registered.py"


def _check_registration_date() -> None:
    if REGISTRATION_DATE != R.REGISTERED_AFTER:
        raise ValueError(f"REGISTRATION_DATE={REGISTRATION_DATE} differs from "
                         f"pcso_model_registry.REGISTERED_AFTER={R.REGISTERED_AFTER}")


def score(rows) -> dict:
    """Pure scoring of (date, P, S) rows in load()'s (date, game) order.

    Preserve that order: load() removes game names after sorting, and sorting
    the returned tuples by pool size would change the pooled filtration.
    """
    _check_registration_date()
    model = CPSparseSwitch()
    n_conditioning, last_conditioning_date = 0, None
    registered_rows = []
    for draw_date, P, S in rows:
        if draw_date <= REGISTRATION_DATE:
            model.update(P, S)
            n_conditioning += 1
            last_conditioning_date = draw_date
        else:
            registered_rows.append((draw_date, P, S))

    # Registration §3: the first registered update uses t = 1. reset() would
    # discard the learned weights, so restart only the switching clock.
    model.t = 0
    registered = R.run_registered([model], registered_rows)[model.name]
    return {
        "_meta": {
            "schema_version": 1,
            "script": SCRIPT,
            "registration": REGISTRATION,
            "registration_date": REGISTRATION_DATE,
            "n_conditioning": n_conditioning,
            "last_conditioning_date": last_conditioning_date,
            "alpha": 0.01,
            "thresholds": {"E": 100, "M": 100},
            "combined_alpha": {"E": 0.005, "M": 0.005},
            "combined_thresholds": {"E": 200, "M": 200},
            "note": "Separate hypothesis-test decisions use E_max >= 100 and M_max >= 100. "
                    "A combined decision splits alpha 0.005/0.005 (threshold 200 each) "
                    "for overall error control at 0.01.",
        },
        "registered": registered,
        "decision": {
            "evidence_rejection": registered["E_max"] >= 100,
            "change_alarm": registered["M_max"] >= 100,
            "combined": registered["E_max"] >= 200 or registered["M_max"] >= 200,
        },
    }


def _run_date(value: str) -> str:
    try:
        if date.fromisoformat(value).isoformat() == value:
            return value
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("expected a valid date in YYYY-MM-DD format")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", required=True, type=_run_date, metavar="YYYY-MM-DD",
                        help="output label; all available registered draws are scored")
    parser.add_argument("--verify", action="store_true",
                        help="recompute and compare an existing record without writing")
    args = parser.parse_args(argv)
    dst = OUTPUT_DIR / f"pcso_sparse_registered_{args.run_date}.json"
    try:
        _check_registration_date()
        if not args.verify and dst.exists():
            raise ValueError(f"refusing to overwrite existing output: {dst}")
        rows = R.load()
        result = score(rows)
        result["_meta"].update({
            "run_date": args.run_date,
            "input_snapshot_commit": R.INPUT_SNAPSHOT_COMMIT,
            "input_sha256": {
                R.DRAWS.relative_to(ROOT).as_posix(): hashlib.sha256(R.DRAWS.read_bytes()).hexdigest(),
            },
            "code_sha256": {
                path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                for path in ("src/pcso_sparse_switch.py", "src/pcso_model_registry.py", SCRIPT)
            },
        })
        payload = (json.dumps(result, sort_keys=True, indent=1) + "\n").encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        if args.verify:
            if dst.read_bytes() != payload:
                raise ValueError(f"VERIFY FAIL: byte mismatch: {dst}")
            print(f"PASS sha256={digest}")
            return
        # Exclusive creation also prevents overwriting a file created during scoring.
        with dst.open("xb") as output:
            output.write(payload)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(f"wrote {dst} sha256={digest}")


if __name__ == "__main__":
    main()
