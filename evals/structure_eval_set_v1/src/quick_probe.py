#!/usr/bin/env python3
"""
Quick probe for Structure Discovery Evaluation Set v1.

This is not the full lab. It computes lightweight diagnostics to verify that the files
are readable and that some broad signal families are detectable.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

try:
    from scipy import stats
except Exception:
    stats = None

ROOT = Path(__file__).resolve().parents[1]
BLIND = ROOT / "blind" / "datasets"

def chi2_pvalue(chi, df):
    if stats is None:
        return float("nan")
    return float(1 - stats.chi2.cdf(chi, df=df))

def probe_draws():
    path = BLIND / "draws" / "draws_all.csv"
    df = pd.read_csv(path)
    rows = []
    for stream, g in df.groupby("stream_id"):
        P = int(g["pool_size"].iloc[0])
        nums = g[[f"n{i}" for i in range(1,7)]].to_numpy().ravel()
        counts = np.bincount(nums, minlength=P+1)[1:]
        E = len(g) * 6 / P
        chi = float(((counts - E) ** 2 / E).sum())
        draws = g[[f"n{i}" for i in range(1,7)]].to_numpy()
        overlaps = [len(set(draws[i]).intersection(draws[i-1])) for i in range(1, len(draws))]
        rows.append({
            "stream_id": stream,
            "chi2": round(chi, 3),
            "chi2_p_asymptotic_probe": round(chi2_pvalue(chi, P-1), 6),
            "mean_consecutive_overlap": round(float(np.mean(overlaps)), 3),
            "max_count": int(counts.max()),
            "argmax_count_number": int(counts.argmax()+1)
        })
    return pd.DataFrame(rows)

def probe_draw_sensor():
    draws = pd.read_csv(BLIND / "draws" / "draws_all.csv")
    sensors = pd.read_csv(BLIND / "sensors" / "sensor_panel.csv")
    rows = []
    for stream, g in draws.groupby("stream_id"):
        g = g.copy()
        g["draw_sum"] = g[[f"n{i}" for i in range(1,7)]].sum(axis=1)
        m = g.merge(sensors, on="date")
        for sensor in [c for c in sensors.columns if c.startswith("sensor_")]:
            r = float(np.corrcoef(m["draw_sum"], m[sensor])[0,1])
            rows.append({"stream_id":stream, "sensor":sensor, "corr_draw_sum":round(r,3)})
    return pd.DataFrame(rows)

def probe_matrices():
    rows = []
    for name in ["M1","M2"]:
        M = pd.read_csv(BLIND / "matrices" / f"matrix_{name}.csv").drop(columns=["row_id"]).to_numpy()
        s = np.linalg.svd(M, compute_uv=False)
        rows.append({
            "matrix": name,
            "top_singular": round(float(s[0]), 3),
            "s1_over_s4": round(float(s[0]/s[3]), 3),
            "rank3_energy_fraction": round(float((s[:3]**2).sum()/(s**2).sum()), 3)
        })
    return pd.DataFrame(rows)

def main():
    print("\n[draws]")
    print(probe_draws().to_string(index=False))
    print("\n[draws_vs_sensors]")
    print(probe_draw_sensor().pivot(index="stream_id", columns="sensor", values="corr_draw_sum").round(3).to_string())
    print("\n[matrices]")
    print(probe_matrices().to_string(index=False))

if __name__ == "__main__":
    main()
