#!/usr/bin/env python3
"""R4 source-drift check (R4 remaining slice — source-drift fixtures).

Adapter-level detector for upstream pcso.gov.ph HTML and GFZ Kp JSON
structure changes. When pcso.gov.ph renames a table column or GFZ renames
a JSON key, downstream instruments would silently parse shifted data and
emit wrong results. This module fails closed at the adapter layer and
emits a typed error naming itself so the loop attributes the FAIL row to
the parser/adapter (`src/source_drift_check.py`), not to a downstream
instrument like `src/meta_uniformity.py`.

    python3 src/source_drift_check.py --verify

Exits 0 on PASS (no drift detected against the committed captures).
Exits 1 with a typed error message on FAIL (drift detected), so the
outcome collector (`src/outcome_collect.py`) opens a `verify_entrypoint`
FAIL row attributed to this file.

Builds on the M4 substrate already shipped in PR #20/#24
(`datasets/pcso-lotto/provenance/raw_2026-09-06/*.html.gz` with
`sha256_uncompressed` per file, `datasets/gfz-kp-geomagnetic/_kp_raw_1yr.json`
with `{datetime, Kp, meta}` shape). Does not modify the live captures.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))


class SourceDriftDetected(Exception):
    """Raised when an upstream capture no longer matches the declared
    contract. The message names `src/source_drift_check.py` and the
    offending artefact so the outcome ledger FAIL row attributes to the
    adapter, not a downstream instrument."""


REQUIRED_GFZ_KEYS = ("datetime", "Kp")


def check_gfz_kp_shape(raw_path):
    """Assert a GFZ Kp raw JSON has the keys `make_kp_daily.py` depends on.

    `datasets/gfz-kp-geomagnetic/make_kp_daily.py` iterates `raw["datetime"]`
    and `raw["Kp"]` (line 9, `for ts, kp in zip(raw["datetime"], raw["Kp"])`).
    If GFZ renames either key, the parser currently raises `KeyError` with
    no adapter attribution. This check catches the rename at the adapter
    layer with a typed, attributable error.
    """
    try:
        data = json.load(open(raw_path))
    except Exception as e:
        raise SourceDriftDetected(
            f"src/source_drift_check.py: GFZ Kp raw JSON unreadable at {raw_path}: {type(e).__name__}: {e}"
        ) from e
    actual = list(data.keys())
    missing = [k for k in REQUIRED_GFZ_KEYS if k not in data]
    if missing:
        raise SourceDriftDetected(
            f"src/source_drift_check.py: GFZ Kp shape drifted — required keys "
            f"{list(REQUIRED_GFZ_KEYS)} missing {missing}; actual keys {actual[:8]} "
            f"in {raw_path}; downstream make_kp_daily.py would raise KeyError. "
            f"Update REQUIRED_GFZ_KEYS in src/source_drift_check.py if the upstream "
            f"rename is intentional."
        )


def check_pcso_manifest_sha256(manifest_path, capture_dir):
    """For every file entry in a PCSO manifest, assert the live capture's
    sha256 matches the declared `sha256_uncompressed`.

    `datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json` declares a
    `sha256_uncompressed` per capture so a re-run can prove the bytes are
    the ones originally parsed. If the live bytes drift (an upstream page
    was edited, a re-fetch served different content, a capture was
    corrupted), this check fails closed at the manifest layer.
    """
    try:
        m = json.load(open(manifest_path))
    except Exception as e:
        raise SourceDriftDetected(
            f"src/source_drift_check.py: PCSO manifest unreadable at {manifest_path}: {type(e).__name__}: {e}"
        ) from e
    cap = m.get("raw_source_capture") or {}
    files = cap.get("files") or []
    if not files:
        raise SourceDriftDetected(
            f"src/source_drift_check.py: PCSO manifest has no raw_source_capture.files in {manifest_path}"
        )
    for entry in files:
        rel = entry.get("file")
        declared = entry.get("sha256_uncompressed")
        if not rel or not declared:
            raise SourceDriftDetected(
                f"src/source_drift_check.py: PCSO manifest entry missing file/sha256 in {manifest_path}: {entry}"
            )
        path = os.path.join(capture_dir, rel)
        if not os.path.exists(path):
            raise SourceDriftDetected(
                f"src/source_drift_check.py: PCSO capture missing on disk: {path} "
                f"(declared in {manifest_path})"
            )
        actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if actual != declared:
            raise SourceDriftDetected(
                f"src/source_drift_check.py: PCSO capture sha256 drifted — "
                f"{rel} declared {declared[:12]}..., actual {actual[:12]}...; "
                f"capture_dir={capture_dir}, manifest={manifest_path}. "
                f"Re-fetch upstream and update the manifest, or restore the original bytes."
            )


def main_verify():
    """CI entry point: check the committed provenance captures against
    their declared contracts. Exits 0 on PASS.

    Emits the conventional `PASS sha256=<hex>; ...` line so
    `outcome_collect.parse_verify_output` classifies the run as PASS.
    The sha256 is a deterministic hash of (a) the GFZ raw sha256 and
    (b) the concatenation of every PCSO capture's `sha256_uncompressed`,
    so the PASS line itself is stable across runs against unchanged
    captures and changes iff any capture's bytes change.
    """
    gfz_raw = os.path.join(REPO, "datasets/gfz-kp-geomagnetic/_kp_raw_1yr.json")
    pcso_manifest = os.path.join(
        REPO, "datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json"
    )
    pcso_capture_dir = os.path.join(REPO, "datasets/pcso-lotto")
    check_gfz_kp_shape(gfz_raw)
    check_pcso_manifest_sha256(pcso_manifest, pcso_capture_dir)
    # PASS-line sha256: a real 64-char hex digest of (gfz_raw_bytes,
    # pcso_manifest_capture_shas) so the lab's PASS-line convention is met.
    gfz_sha = hashlib.sha256(open(gfz_raw, "rb").read()).hexdigest()
    m = json.load(open(pcso_manifest))
    capture_shas = sorted(e["sha256_uncompressed"] for e in m["raw_source_capture"]["files"])
    pcso_combined = hashlib.sha256("".join(capture_shas).encode("utf-8")).hexdigest()
    composite = hashlib.sha256(
        (gfz_sha + "|" + pcso_combined).encode("utf-8")
    ).hexdigest()
    print(
        f"PASS sha256={composite}; gfz_raw_sha={gfz_sha}; "
        f"pcso_manifest_sha={pcso_combined}; n_captures={len(capture_shas)}; "
        f"wrote=none"
    )


if __name__ == "__main__":
    if "--verify" in sys.argv:
        try:
            main_verify()
        except SourceDriftDetected as e:
            print(f"FAIL: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:                # noqa: BLE001
            print(f"ERROR: src/source_drift_check.py: {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    print("usage: src/source_drift_check.py --verify", file=sys.stderr)
    sys.exit(2)
