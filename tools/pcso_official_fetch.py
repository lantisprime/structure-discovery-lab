#!/usr/bin/env python3
"""Repeatable official PCSO draw fetch — candidate preparation for the pcso-lotto refresh.

Data provenance (scientific framing)
------------------------------------
The canonical official per-draw record for the pcso-lotto dataset is
``datasets/pcso-lotto/data_official_draws_jackpots.csv`` (DATASET.md §2/§8).
Its source of record is the PCSO's own date-range search page,
``https://www.pcso.gov.ph/SearchLottoResult.aspx`` — role ``PRIMARY official
draw results (combination, jackpot, winners)`` in every refresh manifest.

This tool automates the fetch-and-candidate-preparation half of the §8 refresh
procedure. By design it NEVER appends to or edits any CSV (human review is a
required pipeline step). For each of the five 6/N games it

  1. GETs the ASP.NET search page and reads the hidden form fields
     (``__VIEWSTATE``, ``__VIEWSTATEGENERATOR``, ``__EVENTVALIDATION``),
  2. POSTs the date-range + game search with browser headers (Safari UA);
     if the site's edge returns HTTP 403 to the urllib client, the identical
     GET/POST sequence is retried through ``curl`` with the same headers and a
     shared cookie jar,
  3. saves the raw response HTML, gzipped, as immutable provenance,
  4. parses the result rows (game, draw date, combination in the official
     published order, jackpot PHP, winners) for the five 6/N games only,
  5. prints CANDIDATE rows — rows strictly newer than the last date recorded
     per game in the canonical CSV — as canonical CSV lines, and
  6. writes a draft manifest ``candidate_manifest.json`` (sources, raw capture
     sha256/byte counts, candidate rows, provenance_status) for review.

Offline re-run: ``--from-dir <dir>`` parses previously saved captures instead
of fetching (no network), for verification and re-analysis.

Run (fetch):
    python3 tools/pcso_official_fetch.py --start YYYY-MM-DD --end YYYY-MM-DD \
        --out-dir <dir>
Run (offline re-parse):
    python3 tools/pcso_official_fetch.py --from-dir <dir> [--out-dir <dir>]

Standard library only. Exit status: 0 success, 1 fetch/parse failure,
2 usage error.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html import unescape as _html_unescape

# --------------------------------------------------------------------------
# Constants — official endpoint and canonical dataset
# --------------------------------------------------------------------------

BASE_URL = "https://www.pcso.gov.ph/SearchLottoResult.aspx"
ORIGIN = "https://www.pcso.gov.ph"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CANONICAL_CSV = os.path.join(
    REPO_ROOT, "datasets", "pcso-lotto", "data_official_draws_jackpots.csv"
)

CANONICAL_HEADER = ["Game", "Date", "N1", "N2", "N3", "N4", "N5", "N6", "Jackpot", "Winners"]

# Game-id -> canonical game name, derived from the ``ddlSelectGame`` options of
# the official page (verified against the committed raw captures in
# datasets/pcso-lotto/provenance/raw_2026-09-21/). Only the five 6/N games of
# the dataset are covered; all other ids on the page belong to other games and
# are ignored.
GAME_ID_TO_NAME = {
    13: "Lotto 6/42",
    2: "Mega Lotto 6/45",
    1: "Super Lotto 6/49",
    17: "Grand Lotto 6/55",
    18: "Ultra Lotto 6/58",
}
GAME_BY_NAME = {name: gid for gid, name in GAME_ID_TO_NAME.items()}

# Canonical presentation order: date ascending, then pool order 42/45/49/55/58.
POOL_ORDER = ["Lotto 6/42", "Mega Lotto 6/45", "Super Lotto 6/49",
              "Grand Lotto 6/55", "Ultra Lotto 6/58"]

# ASP.NET control name prefix on this page (form id "mainform").
F_PREFIX = "ctl00$ctl00$cphContainer$cpContent$"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Browser headers (Safari fingerprint; the site's edge has returned 403 to
# non-browser clients in past refreshes — see provenance manifest
# pcso_refresh_2026-09-21.json, fetch_client note).
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) "
              "Version/17.4.1 Safari/605.1.15")
BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-PH,en;q=0.9",
}
POST_EXTRA_HEADERS = {
    "Referer": BASE_URL,
    "Origin": ORIGIN,
}

TIMEOUT_SECS = 60
CURL_GRACE_SECS = 30  # extra headroom for the curl subprocess itself


class FetchError(RuntimeError):
    """Clear failure while contacting the official source."""


class Http403(FetchError):
    """HTTP 403 from the edge — triggers the curl fallback."""


class ParseError(RuntimeError):
    """Clear failure while parsing an official response."""


# --------------------------------------------------------------------------
# HTML helpers (regex-based; the page is machine-generated ASP.NET markup)
# --------------------------------------------------------------------------

def _clean_cell(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = _html_unescape(text)
    return text.replace("\xa0", " ").strip()


def _hidden_value(html: str, name: str):
    for pattern in (
        r'<input[^>]*\bname="%s"[^>]*\bvalue="([^"]*)"',
        r'<input[^>]*\bvalue="([^"]*)"[^>]*\bname="%s"',
    ):
        m = re.search(pattern % re.escape(name), html)
        if m:
            return _html_unescape(m.group(1))
    return None


def extract_hidden_fields(html: str) -> dict:
    """Read the ASP.NET hidden fields required for a valid POST."""
    fields = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        value = _hidden_value(html, name)
        if value is None:
            raise ParseError(
                f"hidden field {name!r} not found in official page — "
                "page structure may have changed"
            )
        fields[name] = value
    return fields


def parse_game_options(html: str) -> dict:
    """Derive the game-id -> game-name mapping from the ddlSelectGame options."""
    m = re.search(
        r'<select[^>]*\bname="[^"]*ddlSelectGame"[^>]*>(.*?)</select>',
        html, re.S | re.I,
    )
    if not m:
        raise ParseError("ddlSelectGame select not found in official page")
    options = {}
    for om in re.finditer(
        r'<option[^>]*\bvalue="([^"]*)"[^>]*>(.*?)</option>', m.group(1), re.S | re.I
    ):
        try:
            options[int(om.group(1))] = _clean_cell(om.group(2))
        except ValueError:
            continue
    return options


# --------------------------------------------------------------------------
# parse_results
# --------------------------------------------------------------------------

def _results_table(html: str) -> str:
    m = re.search(
        r'<table[^>]*\bid="[^"]*GridView1"[^>]*>(.*?)</table>', html, re.S | re.I
    )
    if not m:
        m = re.search(
            r'<table[^>]*search-lotto-result-table[^>]*>(.*?)</table>',
            html, re.S | re.I,
        )
    if not m:
        raise ParseError(
            "official results table not found "
            "(looked for GridView1 / search-lotto-result-table)"
        )
    return m.group(1)


def parse_results(html: str) -> list:
    """Parse the official results table.

    Returns rows ``{game, date (YYYY-MM-DD), numbers (6 ints, official
    published order), jackpot (float PHP), winners (int)}`` for the five 6/N
    games only, in table (date-ascending) order. Raises ParseError with a
    clear message on any structural surprise.
    """
    table = _results_table(html)
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if not cells:
            continue  # header row (th cells)
        if len(cells) < 5:
            raise ParseError(
                f"results row has {len(cells)} cells, expected 5: {tr[:120]!r}"
            )
        game = _clean_cell(cells[0])
        # The results table spells two games without a space ("Superlotto 6/49",
        # "Megalotto 6/45") while the game dropdown uses the canonical names.
        game = {"Superlotto 6/49": "Super Lotto 6/49", "Megalotto 6/45": "Mega Lotto 6/45"}.get(game, game)
        if game not in GAME_BY_NAME:
            continue  # keep only the five 6/N games of this dataset
        combo = _clean_cell(cells[1])
        date_s = _clean_cell(cells[2])
        jackpot_s = _clean_cell(cells[3])
        winners_s = _clean_cell(cells[4])

        m = re.fullmatch(
            r"(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*"
            r"-\s*(\d{1,2})\s*-\s*(\d{1,2})",
            combo,
        )
        if not m:
            raise ParseError(f"unparsable combination {combo!r} for {game}")
        numbers = [int(x) for x in m.groups()]  # official published (exit) order

        dm = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_s)
        if not dm:
            raise ParseError(f"unparsable draw date {date_s!r} for {game}")
        month, day, year = (int(x) for x in dm.groups())
        try:
            date_iso = datetime.date(year, month, day).isoformat()
        except ValueError as exc:
            raise ParseError(f"invalid draw date {date_s!r} for {game}: {exc}")

        try:
            jackpot = float(jackpot_s.replace(",", ""))
        except ValueError:
            raise ParseError(f"unparsable jackpot {jackpot_s!r} for {game}")
        try:
            winners = int(winners_s)
        except ValueError:
            raise ParseError(f"unparsable winners field {winners_s!r} for {game}")

        rows.append({
            "game": game,
            "date": date_iso,
            "numbers": numbers,
            "jackpot": jackpot,
            "winners": winners,
        })
    return rows


# --------------------------------------------------------------------------
# fetch — GET the page, read hidden fields, POST the search
# --------------------------------------------------------------------------

def _iso_date(text: str, what: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(text)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be YYYY-MM-DD, got {text!r}")


def _build_post_fields(game_id: int, start: datetime.date, end: datetime.date,
                       hidden: dict) -> str:
    fields = [
        ("__EVENTTARGET", ""),
        ("__EVENTARGUMENT", ""),
        ("__VIEWSTATE", hidden["__VIEWSTATE"]),
        ("__VIEWSTATEGENERATOR", hidden["__VIEWSTATEGENERATOR"]),
        ("__EVENTVALIDATION", hidden["__EVENTVALIDATION"]),
        (F_PREFIX + "ddlStartMonth", MONTHS[start.month - 1]),
        (F_PREFIX + "ddlStartDate", str(start.day)),
        (F_PREFIX + "ddlStartYear", str(start.year)),
        (F_PREFIX + "ddlEndMonth", MONTHS[end.month - 1]),
        (F_PREFIX + "ddlEndDay", str(end.day)),
        (F_PREFIX + "ddlEndYear", str(end.year)),
        (F_PREFIX + "ddlSelectGame", str(game_id)),
        (F_PREFIX + "btnSearch", "Search Lotto"),
    ]
    return urllib.parse.urlencode(fields)


def _urllib_request(url: str, data, headers: dict) -> bytes:
    req = urllib.request.Request(
        url, data=data, headers=headers,
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise Http403(f"HTTP 403 (edge blocked urllib client) for {url}")
        raise FetchError(f"HTTP {exc.code} from {url}: {exc.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FetchError(f"network error contacting {url}: {exc}")


def _curl_run(args: list, headers: dict, out_path: str) -> tuple:
    cmd = ["curl", "-sS", "--max-time", str(TIMEOUT_SECS),
           "-o", out_path, "-w", "%{http_code}"]
    for key, value in headers.items():
        cmd += ["-H", f"{key}: {value}"]
    cmd += args
    try:
        proc = subprocess.run(cmd, capture_output=True,
                              timeout=TIMEOUT_SECS + CURL_GRACE_SECS)
    except subprocess.TimeoutExpired:
        raise FetchError(f"curl timed out after {TIMEOUT_SECS + CURL_GRACE_SECS}s")
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", "replace").strip()
        raise FetchError(f"curl failed (rc={proc.returncode}): {stderr}")
    status = proc.stdout.decode("ascii", "replace").strip()
    try:
        with open(out_path, "rb") as fh:
            body = fh.read()
    except OSError as exc:
        raise FetchError(f"could not read curl output file: {exc}")
    return status, body


def _curl_fetch(game_id: int, start: datetime.date, end: datetime.date) -> str:
    if shutil.which("curl") is None:
        raise FetchError("HTTP 403 from official site and no curl on PATH")
    with tempfile.TemporaryDirectory(prefix="pcso_fetch_") as tmpdir:
        jar = os.path.join(tmpdir, "cookies.jar")
        out = os.path.join(tmpdir, "response.html")
        get_headers = dict(BASE_HEADERS)

        status, body = _curl_run(["-b", jar, "-c", jar, "-L", BASE_URL],
                                 get_headers, out)
        if status != "200":
            raise FetchError(f"curl GET returned HTTP {status} for {BASE_URL}")
        page_html = body.decode("utf-8", "replace")
        hidden = extract_hidden_fields(page_html)
        options = parse_game_options(page_html)
        if options and game_id not in options:
            raise ParseError(
                f"game id {game_id} not offered by the live ddlSelectGame "
                f"options {sorted(options)}"
            )

        body_data = _build_post_fields(game_id, start, end, hidden)
        post_file = os.path.join(tmpdir, "post.txt")
        with open(post_file, "w", encoding="ascii") as fh:
            fh.write(body_data)  # no trailing newline: --data @file would strip it anyway

        post_headers = dict(BASE_HEADERS)
        post_headers.update(POST_EXTRA_HEADERS)
        status, body = _curl_run(
            ["-b", jar, "-c", jar, "--data", "@" + post_file, BASE_URL],
            post_headers, out)
        if status != "200":
            raise FetchError(f"curl POST returned HTTP {status} for {BASE_URL}")
        return body.decode("utf-8", "replace")


def fetch_with_client(game_id: int, start, end) -> tuple:
    """Fetch one game's official date-range search; return (html, client)."""
    start = _iso_date(start, "--start")
    end = _iso_date(end, "--end")
    if game_id not in GAME_ID_TO_NAME:
        raise ValueError(f"unknown game id {game_id!r}; expected one of "
                         f"{sorted(GAME_ID_TO_NAME)}")
    if start > end:
        raise ValueError(f"--start {start} is after --end {end}")

    try:
        page = _urllib_request(BASE_URL, None, dict(BASE_HEADERS))
        page_html = page.decode("utf-8", "replace")
        hidden = extract_hidden_fields(page_html)
        options = parse_game_options(page_html)
        if options and game_id not in options:
            raise ParseError(
                f"game id {game_id} not offered by the live ddlSelectGame "
                f"options {sorted(options)}"
            )
        post_data = _build_post_fields(game_id, start, end, hidden)
        post_headers = dict(BASE_HEADERS)
        post_headers.update(POST_EXTRA_HEADERS)
        post_headers["Content-Type"] = "application/x-www-form-urlencoded"
        resp = _urllib_request(BASE_URL, post_data.encode("ascii"), post_headers)
        return resp.decode("utf-8", "replace"), "urllib"
    except Http403:
        print("[fetch] HTTP 403 from official site via urllib; "
              "falling back to curl with the same browser headers",
              file=sys.stderr)
        return _curl_fetch(game_id, start, end), "curl"


def fetch(game_id: int, start, end) -> str:
    """Fetch the official search response HTML for one game and date range."""
    html, _client = fetch_with_client(game_id, start, end)
    return html


# --------------------------------------------------------------------------
# Canonical CSV reading + candidate selection (read-only; NEVER writes CSVs)
# --------------------------------------------------------------------------

def load_canonical_rows(csv_path: str) -> list:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            game = (row.get("Game") or "").strip()
            date = (row.get("Date") or "").strip()
            if game in GAME_BY_NAME and date:
                rows.append({
                    "game": game,
                    "date": date,
                    "numbers": [int(row[f"N{i}"]) for i in range(1, 7)],
                    "jackpot": float(row["Jackpot"]),
                    "winners": int(row["Winners"]),
                })
    return rows


def last_date_per_game(canonical_rows: list) -> dict:
    last = {}
    for row in canonical_rows:
        if row["game"] not in last or row["date"] > last[row["game"]]:
            last[row["game"]] = row["date"]
    return last


def select_candidates(parsed_by_game: dict, last_dates: dict) -> list:
    candidates = []
    for game, rows in parsed_by_game.items():
        cutoff = last_dates.get(game)
        if cutoff is None:
            candidates.extend(rows)  # game absent from canonical file: all rows new
            continue
        candidates.extend(r for r in rows if r["date"] > cutoff)
    pool_index = {name: i for i, name in enumerate(POOL_ORDER)}
    candidates.sort(key=lambda r: (r["date"], pool_index.get(r["game"], 99)))
    return candidates


def candidate_csv_lines(candidates: list) -> list:
    lines = [",".join(CANONICAL_HEADER)]
    for row in candidates:
        numbers = ",".join(str(n) for n in row["numbers"])
        lines.append(
            f"{row['game']},{row['date']},{numbers},{row['jackpot']},{row['winners']}"
        )
    return lines


# --------------------------------------------------------------------------
# Raw capture + manifest
# --------------------------------------------------------------------------

def capture_filename(game_id: int, start: str, end: str) -> str:
    return f"official_{game_id}_{start}_{end}.html.gz"


def save_capture(out_dir: str, game_id: int, start: str, end: str,
                 raw_bytes: bytes) -> str:
    name = capture_filename(game_id, start, end)
    path = os.path.join(out_dir, name)
    with gzip.open(path, "wb", compresslevel=9) as fh:
        fh.write(raw_bytes)
    return name


def file_meta(filename: str, game_id: int, raw_bytes: bytes) -> dict:
    return {
        "file": filename,
        "game_id": game_id,
        "game": GAME_ID_TO_NAME[game_id],
        "sha256_uncompressed": hashlib.sha256(raw_bytes).hexdigest(),
        "bytes": len(raw_bytes),
    }


def build_manifest(mode: str, run_date: str, start: str, end: str,
                   files_meta: list, candidates: list, client: str,
                   last_dates: dict, complete: bool, capture_dir=None) -> dict:
    if mode == "fetch":
        status = ("official_fetched_unreviewed" if complete else
                  "official_fetch_incomplete")
    else:
        status = ("official_reparse_unreviewed" if complete else
                  "official_reparse_incomplete")
    manifest = {
        "schema_version": 1,
        "run_date": run_date,
        "mode": mode,
        "range": {"start": start, "end": end},
        "canonical_csv": os.path.relpath(DEFAULT_CANONICAL_CSV, REPO_ROOT),
        "last_date_per_game_in_canonical": last_dates,
        "sources": [{
            "id": "pcso.gov.ph",
            "base_url": BASE_URL,
            "role": "PRIMARY official draw results (combination, jackpot, winners)",
        }],
        "raw_source_capture": {
            "available": bool(files_meta),
            "fetch_client": client,
            "capture_dir": capture_dir,
            "files": files_meta,
        },
        "candidate_rows": candidates,
        "provenance_status": status,
        "note": ("draft manifest for human review — nothing has been appended "
                 "to any dataset file by this tool"),
    }
    return manifest


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _gather_from_dir(from_dir: str) -> tuple:
    """Pick the latest capture per game from a directory. Returns
    (per-game {gid: (start, end, path)}, union range)."""
    pattern = re.compile(
        r"^official_(\d+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.html\.gz$"
    )
    found = {}
    for filename in sorted(os.listdir(from_dir)):
        m = pattern.match(filename)
        if not m:
            continue
        gid = int(m.group(1))
        if gid not in GAME_ID_TO_NAME:
            continue
        rng = (m.group(2), m.group(3))
        if gid not in found or rng > found[gid][:2]:
            found[gid] = (rng[0], rng[1], os.path.join(from_dir, filename))
    missing = sorted(GAME_ID_TO_NAME[g] for g in GAME_ID_TO_NAME if g not in found)
    if missing:
        raise FetchError(
            f"--from-dir {from_dir} is missing official captures for: "
            f"{', '.join(missing)} (expected official_<gameid>_<start>_<end>.html.gz)"
        )
    starts = [found[g][0] for g in found]
    ends = [found[g][1] for g in found]
    return found, min(starts), max(ends)


def _run(args) -> int:
    csv_path = args.csv or DEFAULT_CANONICAL_CSV
    if not os.path.exists(csv_path):
        print(f"error: canonical CSV not found at {csv_path}", file=sys.stderr)
        return 2

    canonical_rows = load_canonical_rows(csv_path)
    last_dates = last_date_per_game(canonical_rows)
    files_meta = []
    parsed_by_game = {}
    failures = []
    client = "n/a (offline re-parse)" if args.from_dir else "urllib"
    run_date = datetime.date.today().isoformat()

    if args.from_dir:
        start, end = None, None
        try:
            captures, start, end = _gather_from_dir(args.from_dir)
        except (FetchError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        for gid in sorted(captures):
            cstart, cend, path = captures[gid]
            try:
                with open(path, "rb") as fh:
                    raw = gzip.decompress(fh.read())
                html = raw.decode("utf-8", "replace")
                rows = parse_results(html)
                if not rows:
                    raise ParseError(
                        "no result rows parsed from capture — page structure "
                        "may have changed or the range has no draws"
                    )
            except (OSError, ParseError) as exc:
                failures.append((GAME_ID_TO_NAME[gid], str(exc)))
                print(f"[error] {GAME_ID_TO_NAME[gid]}: {exc}", file=sys.stderr)
                continue
            parsed_by_game[GAME_ID_TO_NAME[gid]] = rows
            files_meta.append(file_meta(os.path.basename(path), gid, raw))
    else:
        start, end = args.start, args.end
        os.makedirs(args.out_dir, exist_ok=True)
        for gid in sorted(GAME_ID_TO_NAME):
            game = GAME_ID_TO_NAME[gid]
            try:
                html, client_used = fetch_with_client(gid, start, end)
                client = client_used
                raw = html.encode("utf-8")
                save_capture(args.out_dir, gid, start, end, raw)
                rows = parse_results(html)
                if not rows:
                    raise ParseError(
                        "no result rows parsed from official response — page "
                        "structure may have changed or the range has no draws"
                    )
            except (FetchError, ParseError, ValueError) as exc:
                failures.append((game, str(exc)))
                print(f"[error] {game}: {exc}", file=sys.stderr)
                continue
            parsed_by_game[game] = rows
            files_meta.append(
                file_meta(capture_filename(gid, start, end), gid, raw))

    candidates = select_candidates(parsed_by_game, last_dates)

    # Candidate rows go to stdout as canonical CSV lines (header only if any).
    for line in candidate_csv_lines(candidates) if candidates else []:
        print(line)

    print(f"{len(candidates)} candidate row(s) newer than the canonical "
          f"last date per game {dict(sorted(last_dates.items()))}",
          file=sys.stderr)

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        manifest = build_manifest(
            mode="from_dir" if args.from_dir else "fetch",
            run_date=run_date,
            start=start, end=end,
            files_meta=files_meta,
            candidates=candidates,
            client=client,
            last_dates=last_dates,
            complete=not failures,
            capture_dir=args.from_dir,
        )
        manifest_path = os.path.join(args.out_dir, "candidate_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
            fh.write("\n")
        print(f"draft manifest written: {manifest_path} "
              "(review before appending anything to the canonical file)",
              file=sys.stderr)

    if failures:
        print(f"error: {len(failures)} game(s) failed: "
              + "; ".join(f"{g}: {msg}" for g, msg in failures), file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch official PCSO date-range search results per game, "
                    "save raw captures, and print candidate rows for human "
                    "review (never modifies any CSV).")
    parser.add_argument("--start", help="range start, YYYY-MM-DD (fetch mode)")
    parser.add_argument("--end", help="range end, YYYY-MM-DD (fetch mode)")
    parser.add_argument("--out-dir",
                        help="directory for raw .html.gz captures and "
                             "candidate_manifest.json")
    parser.add_argument("--from-dir",
                        help="parse previously saved official captures from "
                             "this directory instead of fetching (offline)")
    parser.add_argument("--csv", default=None,
                        help="canonical CSV override "
                             f"(default: {DEFAULT_CANONICAL_CSV})")
    args = parser.parse_args(argv)

    if args.from_dir:
        if args.start or args.end:
            parser.error("--from-dir cannot be combined with --start/--end")
    else:
        if not (args.start and args.end):
            parser.error("fetch mode requires --start YYYY-MM-DD and "
                         "--end YYYY-MM-DD (or use --from-dir)")
        if not args.out_dir:
            parser.error("fetch mode requires --out-dir")
        try:
            _iso_date(args.start, "--start")
            _iso_date(args.end, "--end")
        except ValueError as exc:
            parser.error(str(exc))
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
