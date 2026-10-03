#!/usr/bin/env python3
"""Tests for tools/pcso_official_fetch.py — no network.

Parity gate: for every committed official capture in
datasets/pcso-lotto/provenance/raw_2026-09-21/, parse_results must reproduce
EXACTLY the rows of the canonical data_official_draws_jackpots.csv for that
game within the capture window 2026-09-01..2026-09-20 (numbers in the
official published order, jackpot to 2 decimals, winners).

Run: python3 -m pytest tests/test_pcso_official_fetch.py -q
"""
import csv
import datetime
import gzip
import importlib.util
import os
import shutil
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(REPO, "tools", "pcso_official_fetch.py")
CAPTURES_DIR = os.path.join(
    REPO, "datasets", "pcso-lotto", "provenance", "raw_2026-09-21")
CANONICAL_CSV = os.path.join(
    REPO, "datasets", "pcso-lotto", "data_official_draws_jackpots.csv")

WINDOW_START = datetime.date(2026, 9, 1)
# The captures were fetched 2026-09-21T19:55+08:00, before that evening's
# 21:00 draws, so they cannot contain draws dated 2026-09-21.
WINDOW_END = datetime.date(2026, 9, 20)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F = load("pcso_official_fetch", TOOL)


def read_capture(gid):
    path = os.path.join(
        CAPTURES_DIR, f"official_{gid}_2026-09-01_2026-09-21.html.gz")
    with open(path, "rb") as fh:
        return gzip.decompress(fh.read()).decode("utf-8", "replace")


def canonical_rows():
    with open(CANONICAL_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            yield {
                "game": row["Game"].strip(),
                "date": row["Date"].strip(),
                "numbers": [int(row[f"N{i}"]) for i in range(1, 7)],
                "jackpot": float(row["Jackpot"]),
                "winners": int(row["Winners"]),
            }


# --------------------------------------------------------------------------
# 1. Parity: parse_results on committed captures == canonical CSV rows
# --------------------------------------------------------------------------

@pytest.mark.parametrize("gid", sorted(F.GAME_ID_TO_NAME))
def test_capture_matches_canonical_csv(gid):
    game = F.GAME_ID_TO_NAME[gid]
    html = read_capture(gid)
    parsed = F.parse_results(html)
    assert parsed, f"no rows parsed from committed capture for {game}"

    expected = sorted(
        (r for r in canonical_rows()
         if r["game"] == game
         and WINDOW_START <= datetime.date.fromisoformat(r["date"]) <= WINDOW_END),
        key=lambda r: r["date"])
    actual = sorted(parsed, key=lambda r: r["date"])

    assert len(actual) == len(expected), (
        f"{game}: parsed {len(actual)} rows, canonical has {len(expected)} "
        f"in {WINDOW_START}..{WINDOW_END}")
    for got, want in zip(actual, expected):
        assert got["game"] == want["game"]
        assert got["date"] == want["date"], game
        assert got["numbers"] == want["numbers"], (
            f"{game} {want['date']}: numbers differ (published order)")
        assert got["winners"] == want["winners"], f"{game} {want['date']}"
        assert abs(got["jackpot"] - want["jackpot"]) <= 0.005, (
            f"{game} {want['date']}: jackpot {got['jackpot']} vs "
            f"{want['jackpot']}")


# --------------------------------------------------------------------------
# 2. Game-id mapping covers exactly the five dataset games
# --------------------------------------------------------------------------

def test_game_id_mapping_exactly_five_games():
    assert set(F.GAME_ID_TO_NAME) == {1, 2, 13, 17, 18}
    assert set(F.GAME_ID_TO_NAME.values()) == {
        "Lotto 6/42", "Mega Lotto 6/45", "Super Lotto 6/49",
        "Grand Lotto 6/55", "Ultra Lotto 6/58"}
    # canonical names must match the CSV's exact spelling
    csv_games = {r["game"] for r in canonical_rows()}
    assert set(F.GAME_ID_TO_NAME.values()) == csv_games


def test_game_options_parser_derives_mapping():
    html = read_capture(18)
    options = F.parse_game_options(html)
    for gid, name in F.GAME_ID_TO_NAME.items():
        assert options.get(gid) == name


# --------------------------------------------------------------------------
# 3. Offline re-run of the committed captures yields zero candidate rows
#    (everything in the capture window is already in the canonical CSV) —
#    via the real CLI, which must exit 0 and write nothing.
# --------------------------------------------------------------------------

def test_from_dir_committed_captures_zero_candidates():
    proc = subprocess.run(
        [sys.executable, TOOL, "--from-dir", CAPTURES_DIR],
        cwd=REPO, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "", (
        f"expected zero candidate CSV lines, got:\n{proc.stdout}")


# --------------------------------------------------------------------------
# 4. Client fallback chain (no network): urllib 403 -> curl 403 -> headed
#    browser. The edge rejects non-browser/headless clients by fingerprint
#    (2026-10-03), so a 403 from curl must reach the browser, not abort.
# --------------------------------------------------------------------------

def _raise_403(*_args, **_kwargs):
    raise F.Http403("HTTP 403")


def test_curl_403_falls_back_to_browser(monkeypatch):
    calls = []
    monkeypatch.setattr(F, "_urllib_request", _raise_403)
    monkeypatch.setattr(F, "_curl_fetch", lambda *a: calls.append("curl") or _raise_403())
    monkeypatch.setattr(F, "_browser_fetch", lambda *a: calls.append("browser") or "<html/>")
    html, client = F.fetch_with_client(17, "2026-09-28", "2026-09-28")
    assert (html, client, calls) == ("<html/>", "browser", ["curl", "browser"])


def test_curl_403_status_raises_http403(monkeypatch, tmp_path):
    monkeypatch.setattr(F.shutil, "which", lambda _name: "/usr/bin/curl")
    monkeypatch.setattr(F, "_curl_run", lambda *a: ("403", b"Access Denied"))
    with pytest.raises(F.Http403):
        F._curl_fetch(17, datetime.date(2026, 9, 28), datetime.date(2026, 9, 28))


def test_curl_other_error_does_not_reach_browser(monkeypatch):
    def curl_500(*_a):
        raise F.FetchError("curl GET returned HTTP 500")
    monkeypatch.setattr(F, "_urllib_request", _raise_403)
    monkeypatch.setattr(F, "_curl_fetch", curl_500)
    monkeypatch.setattr(F, "_browser_fetch", lambda *a: pytest.fail("browser must not run"))
    with pytest.raises(F.FetchError, match="HTTP 500"):
        F.fetch_with_client(17, "2026-09-28", "2026-09-28")


def test_validate_rows_enforces_requested_game_range_and_unique_keys():
    rows = F.parse_results(read_capture(18))
    start, end = datetime.date(2026, 9, 1), datetime.date(2026, 9, 21)
    assert F.validate_rows(rows, 18, start, end) is rows

    wrong_game = [dict(rows[0], game="Lotto 6/42")]
    with pytest.raises(F.ParseError, match="does not match requested game"):
        F.validate_rows(wrong_game, 18, start, end)

    out_of_range = [dict(rows[0], date="2026-08-31")]
    with pytest.raises(F.ParseError, match="outside requested range"):
        F.validate_rows(out_of_range, 18, start, end)

    duplicate = [rows[0], dict(rows[0])]
    with pytest.raises(F.ParseError, match="duplicate row"):
        F.validate_rows(duplicate, 18, start, end)


def test_from_dir_rejects_capture_copied_under_wrong_game_id(tmp_path):
    for gid in sorted(F.GAME_ID_TO_NAME):
        source = os.path.join(
            CAPTURES_DIR, f"official_{gid}_2026-09-01_2026-09-21.html.gz")
        target_end = "2026-09-20" if gid == 13 else "2026-09-21"
        target = tmp_path / f"official_{gid}_2026-09-01_{target_end}.html.gz"
        shutil.copyfile(source, target)
    wrong_game_copy = tmp_path / "official_13_2026-09-01_2026-09-21.html.gz"
    shutil.copyfile(
        os.path.join(CAPTURES_DIR,
                     "official_18_2026-09-01_2026-09-21.html.gz"),
        wrong_game_copy)

    proc = subprocess.run(
        [sys.executable, TOOL, "--from-dir", str(tmp_path)],
        cwd=REPO, capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0
    assert "does not match requested game" in proc.stderr


def test_aggregate_clients_summarizes_successful_captures():
    assert F.aggregate_clients([(13, "urllib"), (18, "urllib")]) == "urllib"
    assert F.aggregate_clients([(13, "curl"), (18, "urllib")]) == (
        "mixed: 13=curl, 18=urllib")
    # Failed games are omitted from pairs because they have no capture entry.
    assert F.aggregate_clients([(13, "urllib")]) == "urllib"
