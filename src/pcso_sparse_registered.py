#!/usr/bin/env python3
"""Score cp_sparse_switch under registration pcso.sparse.seq1.

Condition on draws through 2026-09-23, retain the learned weights, and restart
the switching clock and registered evidence accounting for subsequent draws.
Outputs a deterministic evidence-process and hypothesis-test record. --verify
recomputes the record from current code and input and compares bytes without writing.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy

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
            "first_registered_date": min((d for d, _, _ in registered_rows), default=None),
            "last_registered_date": max((d for d, _, _ in registered_rows), default=None),
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


def _qualify_registered(csv_bytes: bytes) -> list[dict]:
    """Qualify every registered CSV row before the frozen loader can filter it."""
    try:
        registered = {}
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")), strict=True)
        required = {"Date", "Game", *(f"N{i}" for i in range(1, 7))}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV must contain Date, Game and N1..N6")
        for row in reader:
            draw_date, game = row["Date"], row["Game"]
            if date.fromisoformat(draw_date).isoformat() != draw_date:
                raise ValueError(f"invalid ISO draw date: {draw_date!r}")
            if draw_date <= REGISTRATION_DATE:
                continue
            key = draw_date, game
            if game not in R.POOL:
                raise ValueError(f"unknown game or pool {key}; a new registration is required")
            if key in registered:
                raise ValueError(f"duplicate registered (date, game): {key}")
            P = R.POOL[game]
            number_error = f"{key} must contain 6 distinct integers in 1..{P}"
            try:
                numbers = tuple(sorted(int(row[f"N{i}"]) for i in range(1, 7)))
            except (TypeError, ValueError) as exc:
                raise ValueError(number_error) from exc
            if len(set(numbers)) != 6 or not all(1 <= n <= P for n in numbers):
                raise ValueError(number_error)
            registered[key] = numbers

        qualified = {}
        if registered:
            for path in sorted((ROOT / "datasets/pcso-lotto/provenance").glob("pcso_refresh_*.json")):
                manifest = json.loads(path.read_bytes())
                for draw in manifest["draws"]:
                    key = draw["date"], draw["game"]
                    if key not in registered or key in qualified:
                        continue
                    numbers = draw.get("numbers")
                    sources = draw.get("source_ids")
                    if (draw.get("status") in ("official_verified", "two_source_verified")
                            and isinstance(numbers, list) and len(numbers) == 6
                            and all(type(n) is int for n in numbers)
                            and tuple(sorted(numbers)) == registered[key]
                            and isinstance(sources, list)
                            and all(isinstance(s, str) and s.strip() for s in sources)
                            and len(set(sources)) >= 2):
                        qualified[key] = path.relative_to(ROOT).as_posix()
        missing = registered.keys() - qualified.keys()
        if missing:
            raise ValueError(f"no qualifying manifest for registered draw {min(missing)}")
        return [{"date": d, "game": game, "manifest": qualified[d, game]}
                for d, game in sorted(registered)]
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
        raise ValueError(f"{REGISTRATION} §3: {exc}") from exc


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
        input_path = R.DRAWS.relative_to(ROOT).as_posix()
        snapshot = {path: (ROOT / path).read_bytes() for path in (
            input_path, "src/pcso_sparse_switch.py", "src/pcso_model_registry.py", SCRIPT)}
        hashes = {path: hashlib.sha256(data).hexdigest() for path, data in snapshot.items()}
        input_hashes = {input_path: hashes[input_path]}
        code_hashes = {path: digest for path, digest in hashes.items() if path != input_path}
        if args.verify:
            expected = dst.read_bytes()
            recorded = json.loads(expected)["_meta"]
            if recorded.get("input_sha256") != input_hashes:
                recorded_sha = recorded.get("input_sha256", {}).get(input_path)
                raise ValueError("input has advanced since this record "
                                 f"(recorded {recorded_sha} vs live {hashes[input_path]}); "
                                 "byte verification needs the recorded input")
            if recorded.get("code_sha256") != code_hashes:
                raise ValueError("code drift since this record "
                                 f"(recorded {recorded.get('code_sha256')} vs live {code_hashes}); "
                                 "byte verification needs the recorded code")
        provenance = _qualify_registered(snapshot[input_path])
        rows = R.load()
        result = score(rows)
        try:
            after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in snapshot}
        except OSError as exc:
            raise ValueError("input or code changed during scoring") from exc
        if after != hashes:
            raise ValueError("input or code changed during scoring")
        result["_meta"].update({
            "run_date": args.run_date,
            "input_snapshot_commit": R.INPUT_SNAPSHOT_COMMIT,
            "input_sha256": input_hashes,
            "code_sha256": code_hashes,
            "registered_provenance": provenance,
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "machine": platform.machine(),
                "platform": platform.platform(),
            },
            "verify_scope": "byte verification is defined within the recorded environment",
        })
        # score() has already computed decisions from the unmodified statistics.
        result["registered"] = {
            key: "overflow" if key in ("E_final", "E_max", "M_max") and not math.isfinite(value)
            else value for key, value in result["registered"].items()
        }
        payload = (json.dumps(result, sort_keys=True, indent=1, allow_nan=False) + "\n").encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        if args.verify:
            if expected != payload:
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
