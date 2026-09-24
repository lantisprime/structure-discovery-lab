"""Conformance of the real repository's conditioning rows to the pinned snapshot."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pcso_model_registry as R


def test_load_matches_real_conditioning_pin():
    rows = R.load()
    snapshot = R._parse_rows(R._snapshot_bytes().decode("utf-8-sig"))
    assert all(row[0] <= R.REGISTERED_AFTER for row in snapshot)
    assert [row for row in rows if row[0] <= R.REGISTERED_AFTER] == [
        (date, P, S) for date, _, P, S in sorted(snapshot)
    ]
