#!/usr/bin/env python3
"""Reproduce a registered PCSO monitoring run from a dated provenance manifest (generalized).

Same validators and the same m=9 monitoring family as src/pcso_weekly_update.py (July 2026
closeout), which is kept unchanged as the historical record of that run. Differences:
  * the manifest declares its own batch size (`expected_new_draws`) instead of the
    hard-coded 28 of the July run;
  * per-draw audit status may be `official_verified` (pcso.gov.ph primary source) as well
    as `two_source_verified`, and the manifest lists which registered source ids each draw
    carries (>= 2 required).
Everything else — frozen-prefix hashes, CRLF, three-file agreement, astro join, seed stream,
add-one MC p-values, workbook invariants — is imported from the July module.

Usage: python3 src/pcso_monitoring_run.py --manifest datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json
                                          [--out results/pcso_confirmation_2026-09-06.json] [--verify]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pcso_weekly_update as base

ALLOWED_STATUS = {"two_source_verified", "official_verified"}


def validate_manifest(manifest: dict) -> list[dict]:
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")
    sources = {s["id"] for s in manifest["sources"]}
    records = manifest["draws"]
    expected = int(manifest["expected_new_draws"])
    if len(records) != expected:
        raise ValueError(f"manifest: expected {expected} draws, got {len(records)}")
    seen: set[tuple[str, str]] = set()
    for record in records:
        base.validate_draw(record)
        key = base.draw_key(record)
        if key in seen:
            raise ValueError(f"manifest duplicate: {key}")
        seen.add(key)
        ids = set(record["source_ids"])
        if not ids <= sources or len(ids) < 2:
            raise ValueError(f"{key}: needs >=2 registered source ids, got {sorted(ids)}")
        if record["status"] not in ALLOWED_STATUS:
            raise ValueError(f"{key}: unexpected audit status {record['status']}")
    return records


def validate_inputs(manifest, records):
    """July validator, minus its `two_source_verified`-only status check (re-applied here)."""
    cutoff = str(manifest["confirmation_cutoff"])
    previous_latest = str(manifest["previous_latest_draw_date"])
    latest = str(manifest["latest_draw_date"])
    expected_counts = manifest["expected_row_counts"]
    expected_batch = {base.draw_key(r): base.draw_value(r) for r in records}
    confirmation_sets = []
    for filename, date_column in base.DRAW_FILES.items():
        path = base.DATASET_DIR / filename
        base.require_crlf(path)
        rows = base.dated_rows(path, date_column)
        if len(rows) != expected_counts[filename]:
            raise ValueError(f"{filename}: expected {expected_counts[filename]} rows, got {len(rows)}")
        parsed = [base.draw_record(row, date_column) for row in rows]
        for record in parsed:
            base.validate_draw(record)
        keys = [base.draw_key(record) for record in parsed]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{filename}: duplicate game/date key")
        if max(record["date"] for record in parsed) != latest:
            raise ValueError(f"{filename}: unexpected latest draw date")
        batch = {base.draw_key(r): base.draw_value(r) for r in parsed if r["date"] > previous_latest}
        if batch != expected_batch:
            raise ValueError(f"{filename}: batch differs from manifest")
        if base.exploration_prefix_sha256(path, date_column, cutoff) != base.EXPLORATION_PREFIX_SHA256[filename]:
            raise ValueError(f"{filename}: frozen exploration prefix changed")
        confirmation_sets.append({base.draw_key(r): base.draw_value(r) for r in parsed if r["date"] > cutoff})
        if filename.endswith("_audited.csv"):
            by_key = {base.draw_key(base.draw_record(r, date_column)): r for r in rows}
            for record in records:
                row = by_key[base.draw_key(record)]
                if row["Source1"] not in record["source_ids"] or row["Source2"] not in record["source_ids"]:
                    raise ValueError(f"{base.draw_key(record)}: audit sources not among manifest source ids")
                if row["Status"] != record["status"]:
                    raise ValueError(f"{base.draw_key(record)}: audit status differs")
    if not all(item == confirmation_sets[0] for item in confirmation_sets[1:]):
        raise ValueError("draw CSVs disagree on confirmation rows")
    canonical_rows = base.dated_rows(base.DATASET_DIR / "data_draws_1yr.csv", "Date")
    confirmation = [base.draw_record(row, "Date") for row in canonical_rows if row["Date"] > cutoff]
    astro_path = base.DATASET_DIR / base.ASTRO_FILE
    base.require_crlf(astro_path)
    if base.exploration_prefix_sha256(astro_path, base.ASTRO_DATE, cutoff) != base.EXPLORATION_PREFIX_SHA256[base.ASTRO_FILE]:
        raise ValueError(f"{base.ASTRO_FILE}: frozen exploration prefix changed")
    astro_rows = base.dated_rows(astro_path, base.ASTRO_DATE)
    if len(astro_rows) != expected_counts[base.ASTRO_FILE]:
        raise ValueError(f"{base.ASTRO_FILE}: unexpected dated row count")
    astro_by_key = {(row["Game"], row[base.ASTRO_DATE]): row for row in astro_rows}
    if len(astro_by_key) != len(astro_rows):
        raise ValueError(f"{base.ASTRO_FILE}: duplicate game/date key")
    for record in confirmation:
        key = base.draw_key(record)
        if key not in astro_by_key:
            raise ValueError(f"{base.ASTRO_FILE}: missing {key}")
        row = astro_by_key[key]
        expected_mean = sum(base.draw_value(record)) / (6 * base.GAMES[str(record["game"])])
        if f"{expected_mean:.4f}" != row[base.MEAN_DRAWN]:
            raise ValueError(f"{base.ASTRO_FILE}: mean-drawn mismatch for {key}")
        if row[base.KP_DRAW] or row[base.KP_DAILY]:
            raise ValueError(f"{base.ASTRO_FILE}: expected blank Kp for {key}")
    return confirmation, astro_by_key


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out = (args.out or (base.ROOT / "results" / f"pcso_confirmation_{manifest['run_date']}.json")).resolve()
    status_before = base.git_status_bytes() if args.verify else None
    records = validate_manifest(manifest)
    confirmation, astro = validate_inputs(manifest, records)
    result = base.run_monitoring(manifest, confirmation, astro, manifest_path)
    result["_meta"]["script"] = "src/pcso_monitoring_run.py (validators + family imported from src/pcso_weekly_update.py)"
    result["_meta"]["raw_source_capture"] = manifest.get("raw_source_capture", {})
    payload = base.result_bytes(result)
    if args.verify:
        digest = base.verify_existing_result(out, payload)
        status_after = base.git_status_bytes()
        if status_before != status_after:
            raise RuntimeError("repository status changed during verification")
        print(f"PASS sha256={digest}; validated={len(records)}; confirmation_n={len(confirmation)}; flags={len(result['flags'])}; wrote=none")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    base.atomic_write(out, payload)
    print(f"validated {len(records)} new draws; confirmation n={len(confirmation)}; flags={len(result['flags'])}; wrote {out}")
    for k, v in result["tests"].items():
        print(k, json.dumps(v)[:400])


if __name__ == "__main__":
    sys.exit(main())
