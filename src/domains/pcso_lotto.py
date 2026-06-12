"""Domain config: PCSO lottery application.

THE ONLY place in forward-facing code where this domain's vocabulary may
appear (enforced by src/lint_domain_neutrality.py). A new domain = a new file
in src/domains/ with the same interface; core instruments never change.

Interface every domain module provides:
  DRAW_ENSEMBLES: {name: pool_size}      (for k-of-P draw domains; else {})
  load_draws(name, ...) -> int array     (T x k)
  covariates() -> DataFrame              (date-keyed covariate bundle)
  ANOMALY_REGISTRY: adjudicated anomalies (for C9 row-trace duties)
  ERA_REGISTRY: declared regime boundaries (A5)
"""

import os

import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA = os.path.join(ROOT, "datasets")

DRAW_K = 6
DRAW_ENSEMBLES = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45,
                  "Super Lotto 6/49": 49, "Grand Lotto 6/55": 55,
                  "Ultra Lotto 6/58": 58}

ANOMALY_REGISTRY = [
    {"id": "655-45-2025", "ensemble": "Grand Lotto 6/55", "elements": [45, 42],
     "era": "2025, dead since 2026-02", "status": "adjudicated, era-bounded, "
     "data-quality-sensitive for hit-count statistics (3 suspicious rows)"},
]

ERA_REGISTRY = [
    {"ensemble": "Grand Lotto 6/55", "boundary": "2026-02",
     "kind": "declared era boundary"},
]


def load_draws(name, exclude_suspicious=False, verified_only=False):
    d = pd.read_csv(os.path.join(DATA, "pcso-lotto/data_draws_1yr_audited.csv"))
    rows = d[d["Game"] == name].sort_values("Date")
    if exclude_suspicious:
        rows = rows[rows["Status"] != "suspicious_or_needs_review"]
    if verified_only:
        rows = rows[rows["Status"].isin(["two_source_verified",
                                         "official_verified",
                                         "two_source_verified(spot)"])]
    return rows[[f"N{i}" for i in range(1, 7)]].to_numpy(int), rows


def covariates():
    tid = pd.read_csv(os.path.join(DATA, "tidal-manila/tidal_derived.csv"))[
        ["Date", "Total tidal accel (g)"]]
    sm = pd.read_csv(os.path.join(DATA, "jpl-horizons-sun-moon/sun_moon_daily.csv"))[
        ["Date", "Moon Dist (km)", "Moon Illum (0-1)", "Sun Dist (km)"]]
    kp = pd.read_csv(os.path.join(DATA, "gfz-kp-geomagnetic/kp_daily.csv"))[
        ["Date", "Kp_daily_mean", "Kp_daily_max"]]
    pr = pd.read_csv(os.path.join(DATA, "openmeteo-pressure-manila/pressure_daily.csv"))
    pr["P_range"] = pr["P_msl_max_hPa"] - pr["P_msl_min_hPa"]
    return tid.merge(sm, on="Date").merge(kp, on="Date").merge(pr, on="Date")
