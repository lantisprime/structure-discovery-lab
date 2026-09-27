#!/usr/bin/env python3
"""Parity gate for the official markdown captures — offline, stdlib+pytest.

The PRIMARY official capture of the 2026-09-23, 2026-09-24, 2026-09-26 and
2026-09-27 refreshes is the searxng-rendered markdown of pcso.gov.ph (raw HTML
unavailable: direct fetch returned HTTP 403), which parse_results cannot
ingest — so tests/test_pcso_official_fetch.py does not cover it.  This test
parses each capture's markdown table directly and asserts exact equality, in
both directions (no missing, no extra), with the canonical
data_official_draws_jackpots.csv rows dated inside that capture's window:
numbers in the official published order, jackpot to 2 decimals, winners.

Run: python -m pytest tests/test_pcso_official_markdown_capture.py -q
"""
import csv
import datetime
import os
from decimal import Decimal

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROVENANCE = os.path.join(REPO, "datasets", "pcso-lotto", "provenance")
CANONICAL_CSV = os.path.join(
    REPO, "datasets", "pcso-lotto", "data_official_draws_jackpots.csv")

# (capture file, first draw date, last draw date, table row count) of each
# official capture.  The 2026-09-26 view returned 6 rows (that day's table had
# no seventh row); the 2026-09-27 view returned 4 rows (two overlap + two new).
CAPTURES = [
    (os.path.join(PROVENANCE, "raw_2026-09-23", "official_searxng_2026-09-23.md"),
     datetime.date(2026, 9, 20), datetime.date(2026, 9, 22), 7),
    (os.path.join(PROVENANCE, "raw_2026-09-24", "official_searxng_2026-09-24.md"),
     datetime.date(2026, 9, 21), datetime.date(2026, 9, 23), 7),
    (os.path.join(PROVENANCE, "raw_2026-09-26", "official_searxng_2026-09-26.md"),
     datetime.date(2026, 9, 23), datetime.date(2026, 9, 25), 6),
    (os.path.join(PROVENANCE, "raw_2026-09-27", "official_searxng_2026-09-27.md"),
     datetime.date(2026, 9, 25), datetime.date(2026, 9, 26), 4),
]

# The capture table uses the PCSO site's compact game names.
GAME_ALIASES = {
    "Superlotto 6/49": "Super Lotto 6/49",
    "Megalotto 6/45": "Mega Lotto 6/45",
}
CENT = Decimal("0.01")


def table_rows(text):
    """Yield the data rows of the markdown table as 5 stripped cells."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        # Header and separator rows contain no digits.
        if len(cells) != 5 or not any(ch.isdigit() for ch in "".join(cells)):
            continue
        yield cells


def capture_rows(capture):
    with open(capture, encoding="utf-8") as fh:
        rows = []
        for game, combos, date, jackpot, winners in table_rows(fh.read()):
            rows.append((
                GAME_ALIASES.get(game, game),
                datetime.datetime.strptime(date, "%m/%d/%Y").date(),
                tuple(int(n) for n in combos.split("-")),
                Decimal(jackpot.replace(",", "")).quantize(CENT),
                int(winners),
            ))
        return rows


def canonical_rows(start, end):
    with open(CANONICAL_CSV, newline="", encoding="utf-8") as fh:
        rows = []
        for row in csv.DictReader(fh):
            date = datetime.date.fromisoformat(row["Date"].strip())
            if not (start <= date <= end):
                continue
            rows.append((
                row["Game"].strip(),
                date,
                tuple(int(row[f"N{i}"]) for i in range(1, 7)),
                Decimal(row["Jackpot"]).quantize(CENT),
                int(row["Winners"]),
            ))
        return rows


@pytest.mark.parametrize("capture,start,end,expected_rows", CAPTURES)
def test_capture_has_expected_rows_in_window(capture, start, end, expected_rows):
    rows = capture_rows(capture)
    assert len(rows) == expected_rows
    assert all(start <= r[1] <= end for r in rows)


@pytest.mark.parametrize("capture,start,end,_", CAPTURES)
def test_capture_matches_canonical_exactly(capture, start, end, _):
    """Bidirectional: no missing and no extra canonical rows in the window."""
    assert sorted(capture_rows(capture)) == sorted(canonical_rows(start, end))
