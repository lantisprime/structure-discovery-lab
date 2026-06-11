# Dataset: gfz-kp-geomagnetic

**Source of record**: GFZ Potsdam Kp index web service (kp.gfz.de), CC BY 4.0.
**Fetched**: 2026-06-11, in 3 chunks (2025-06-11→09-30, 2025-10-01→2026-02-28, 2026-03-01→06-10); raw JSON preserved in `_kp_raw_1yr.json` (2,920 three-hourly bins, 365 days, zero gaps; consecutive-bin continuity verified at fetch time).

## Files
- `_kp_raw_1yr.json` — raw 3-hourly Kp + fetch metadata (provenance).
- `make_kp_daily.py` — deterministic → `kp_daily.csv`.
- `kp_daily.csv` — Date, Kp_12-15UTC (the bin containing 13:00 UTC = PCSO draw time 21:00 PHT), Kp_daily_mean, Kp_daily_max, n_bins (8 for every day).

## Validation
- 365/365 days with all 8 bins; Kp range observed 0.000–7.333 (storms up to Kp 7+ in the window); values in [0,9].
- Known revision: the 2026-06-10 12–15 UT bin differs by 0.334 from the legacy pcso-lotto astro file because GFZ finalized a preliminary value after that file was written; daily means agree. The raw file here carries the definitive values as of fetch date.

## Known gaps / notes
- Kp is a global 3-hourly planetary index; for minute-scale or local (Philippines) geomagnetic data, a local observatory (e.g., INTERMAGNET station) would be the next source — not onboarded.
