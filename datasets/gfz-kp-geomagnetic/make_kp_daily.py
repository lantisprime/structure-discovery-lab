#!/usr/bin/env python3
"""Deterministic: _kp_raw_1yr.json (GFZ Potsdam Kp, 3-hourly, CC BY 4.0) -> kp_daily.csv.
Kp_12-15UTC = the 3-hourly bin containing 13:00 UTC (= PCSO draw time 21:00 PHT).
"""
import json, csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(HERE, "_kp_raw_1yr.json")))
days = defaultdict(dict)
for ts, kp in zip(raw["datetime"], raw["Kp"]):
    d, t = ts.split("T")
    days[d][t[:2]] = kp
with open(os.path.join(HERE, "kp_daily.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Date", "Kp_12-15UTC", "Kp_daily_mean", "Kp_daily_max", "n_bins"])
    for d in sorted(days):
        bins = days[d]
        vals = list(bins.values())
        w.writerow([d, bins.get("12", ""), f"{sum(vals)/len(vals):.3f}",
                    f"{max(vals):.3f}", len(vals)])
print(f"kp_daily.csv: {len(days)} days, "
      f"complete={all(len(v)==8 for v in days.values())}")
