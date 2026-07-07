#!/usr/bin/env python3
"""Fetch Manila daily surface pressure from NASA POWER (MERRA-2) — the
SECOND independent pressure source gating positive pressure claims
(README Limitations: 'Single-source covariate').

Run from the repo root ON A NETWORK-ENABLED MACHINE (the remote lab
sandbox blocks weather hosts):

    python3 datasets/nasa-power-manila/fetch_nasa_power.py

Writes (never edits in place; re-running overwrites the _raw file only):
    datasets/nasa-power-manila/_raw_nasa_power.json      raw provenance
    datasets/nasa-power-manila/pressure_daily_nasa.csv   canonical daily kPa->hPa

Then cross-check against the existing source before any instrument runs:
    python3 datasets/nasa-power-manila/crosscheck_sources.py
"""
import csv
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# Same site as openmeteo-pressure-manila: Manila 14.60 N, 120.98 E.
# Window matches the existing series' coverage; extend END as the lab's
# draw data grows (append, never edit).
START, END = "20260301", "20260630"
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point"
       "?parameters=PS&community=RE&longitude=120.98&latitude=14.60"
       f"&start={START}&end={END}&format=JSON")


def main():
    raw = urllib.request.urlopen(URL, timeout=60).read()
    with open(os.path.join(HERE, "_raw_nasa_power.json"), "wb") as f:
        f.write(raw)
    j = json.loads(raw)
    ps = j["properties"]["parameter"]["PS"]        # kPa (MERRA-2 PS)
    rows = [(f"{d[:4]}-{d[4:6]}-{d[6:]}", round(float(v) * 10.0, 2))
            for d, v in sorted(ps.items()) if float(v) > 0]
    out = os.path.join(HERE, "pressure_daily_nasa.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "pressure_hpa"])
        w.writerows(rows)
    print(f"wrote {len(rows)} daily rows -> {out} "
          f"(source MERRA-2 via NASA POWER, kPa*10 = hPa)")


if __name__ == "__main__":
    main()
