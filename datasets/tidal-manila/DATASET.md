# Dataset: tidal-manila

Two layers, honestly separated:

## 1. `tidal_derived.csv` — DERIVED tidal accelerations (complete, 366 days)

Computed (not measured) from **JPL Horizons source-of-record distances**
(../jpl-horizons-sun-moon/sun_moon_daily.csv) by `../jpl-horizons-sun-moon/parse_horizons.py`,
using the lab's established convention:

- value = C / d³ (d = body distance in metres), in g units.
- C_moon = 2.998598×10¹¹ g·m³ — recovered from the legacy file (std < 0.05%); equals
  2·G·M_moon·r/g₀ with reference height r = 0.300 m.
- C_sun = 8.121786×10¹⁸ g·m³ = C_moon × (M_sun/M_moon = 27,090,711) — same r.
- Columns: Date, Moon Dist (km), Lunar tidal accel (g), Sun Dist (km), Solar tidal
  accel (g), Total tidal accel (g, simple sum — ignores the angular factor between
  the two tidal axes; the within-pair angle is not encoded in scalar accelerations).
- Ranges in window: lunar ~4.3–5.4×10⁻¹⁵ g, solar ~2.31–2.55×10⁻¹⁵ g.

## 2. Measured tide gauge (sample only — recorded gap)

- **Source confirmed live**: IOC Sea Level Station Monitoring Facility, station
  `mani` (Manila). 1-minute resolution, sea level in metres, multiple sensors
  ('prs' = pressure sensor is the sea-level channel). Sample + exact request
  recipe: `_ioc_mani_sample_2025-06-11.json`.
- **Gap, recorded honestly**: a full year of 1-minute data ≈ 365 fetches × ~67 KB —
  not retrievable through this session's fetch tool. UHSLC bulk files (station
  registry / h-files) returned empty responses at fetch time (2026-06-11).
- **To complete later**: loop the IOC request per day (or per week) and aggregate the
  'prs' sensor at 13:00 UTC; or retry UHSLC research-quality hourly data. Do NOT
  substitute predictions for measurements without labeling them as such.

## Why both layers exist

Gravitational tidal acceleration (layer 1) is the physically relevant covariate for
the draw machine; ocean tide gauge readings (layer 2) add local ocean dynamics and
serve as an independent physical proxy. Layer 1 is complete and source-derived;
layer 2 is sampled and documented for future completion.
