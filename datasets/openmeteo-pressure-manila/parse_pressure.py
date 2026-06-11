#!/usr/bin/env python3
"""
Builds pressure_daily.csv from the raw Open-Meteo ERA5 archive response
(_raw_openmeteo_pressure.json or .csv) for the PCSO draw site.

Site: PCSO main office / draw studio, Sun Plaza, Shaw Blvd, Mandaluyong City,
Metro Manila — 14.5794 N, 121.0359 E.
Window: 2025-06-11 .. 2026-06-11 (matches all other covariate datasets).
Columns out: Date, P_msl_mean_hPa, P_msl_min_hPa, P_msl_max_hPa
(MSL pressure; Manila is near sea level so MSL ~ surface pressure + ~1 hPa.)
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def from_json(path):
    d = json.load(open(path))
    t = d["daily"]["time"]
    rows = zip(t, d["daily"]["pressure_msl_mean"],
               d["daily"]["pressure_msl_min"], d["daily"]["pressure_msl_max"])
    return list(rows)


def from_csv(path):
    rows = []
    with open(path) as f:
        for row in csv.reader(f):
            if row and row[0][:2] == "20" and len(row) >= 4:
                rows.append((row[0], row[1], row[2], row[3]))
    return rows


def main():
    raw_json = os.path.join(HERE, "_raw_openmeteo_pressure.json")
    raw_csv = os.path.join(HERE, "_raw_openmeteo_pressure.csv")
    if os.path.exists(raw_json):
        rows = from_json(raw_json)
    elif os.path.exists(raw_csv):
        rows = from_csv(raw_csv)
    else:
        sys.exit("no raw file found (_raw_openmeteo_pressure.json/.csv)")
    rows = [r for r in rows if r[1] not in ("", None)]
    out = os.path.join(HERE, "pressure_daily.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "P_msl_mean_hPa", "P_msl_min_hPa", "P_msl_max_hPa"])
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows, {rows[0][0]} .. {rows[-1][0]}")


if __name__ == "__main__":
    main()
