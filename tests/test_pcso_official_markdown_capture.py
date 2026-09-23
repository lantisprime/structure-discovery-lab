#!/usr/bin/env python3
"""Parity gate for the 2026-09-23 official markdown capture — offline, stdlib+pytest.

The PRIMARY official capture of the 2026-09-23 refresh is the searxng-rendered
markdown of pcso.gov.ph (raw HTML unavailable: direct fetch returned HTTP 403),
which parse_results cannot ingest — so tests/test_pcso_official_fetch.py does
not cover it.  This test parses the 7-row markdown table directly and asserts
exact equality, in both directions (no missing, no extra), with the canonical
data_official_draws_jackpots.csv rows dated 2026-09-20..2026-09-22: numbers in
the official published order, jackpot to 2 decimals, winners.

Run: python -m pytest tests/test_pcso_official_markdown_capture.py -q
"""
import csv
import datetime
import os
from decimal import Decimal

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAPTURE = os.path.join(
    REPO, "datasets", "pcso-lotto", "provenance", "raw_2026-09-23",
    "official_searxng_2026-09-23.md")
CANONICAL_CSV = os.path.join(
    REPO, "datasets", "pcso-lotto", "data_official_draws_jackpots.csv")

# The capture table uses the PCSO site's compact game names.
GAME_ALIASES = {
    "Superlotto 6/49": "Super Lotto 6/49",
    "Megalotto 6/45": "Mega Lotto 6/45",
}
WINDOW_START = datetime.date(2026, 9, 20)
WINDOW_END = datetime.date(2026, 9, 22)
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


def capture_rows():
    with open(CAPTURE, encoding="utf-8") as fh:
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


def canonical_rows():
    with open(CANONICAL_CSV, newline="", encoding="utf-8") as fh:
        rows = []
        for row in csv.DictReader(fh):
            date = datetime.date.fromisoformat(row["Date"].strip())
            if not (WINDOW_START <= date <= WINDOW_END):
                continue
            rows.append((
                row["Game"].strip(),
                date,
                tuple(int(row[f"N{i}"]) for i in range(1, 7)),
                Decimal(row["Jackpot"]).quantize(CENT),
                int(row["Winners"]),
            ))
        return rows


def test_capture_has_seven_rows_in_window():
    rows = capture_rows()
    assert len(rows) == 7
    assert all(WINDOW_START <= r[1] <= WINDOW_END for r in rows)


def test_capture_matches_canonical_exactly():
    """Bidirectional: no missing and no extra canonical rows in the window."""
    assert sorted(capture_rows()) == sorted(canonical_rows())
