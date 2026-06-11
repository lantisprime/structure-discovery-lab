# DATASET — openmeteo-pressure-manila

**Status**: ACTIVE (covariate) · onboarded 2026-06-11 per THEOREM_GOVERNANCE Part 4.

## 1. H₀ and executable null simulator (A1)

This is a **covariate** dataset: no randomness claim is made about it. The null it
serves is on the *pairing*: "atmospheric pressure at the draw site has no
relationship with draw outcomes." Because the series is strongly autocorrelated
(lag-1 r = 0.854), the admissible nulls are **shuffled draw–pressure pairing** (for
paired tests) and **block shuffle / circular shift** of the pressure series (for
temporal tests) — never plain value permutation as sole control (A5).
Executable: `numpy roll by random offset ≥ 30 days` or block-permute with 14-day
blocks; pairing null: permute the Date join.

## 2. Schema (frozen)

`pressure_daily.csv`: `Date` (YYYY-MM-DD, Asia/Manila civil day),
`P_msl_mean_hPa`, `P_msl_min_hPa`, `P_msl_max_hPa` (mean-sea-level pressure,
hPa, daily aggregates of ERA5 hourly). Append-only.

## 3. Provenance

- **Source**: Open-Meteo Historical Weather API (ERA5 reanalysis), grid cell
  14.586995 N, 121.002785 E, elevation 15 m — the cell containing the PCSO draw
  studio (Sun Plaza, Shaw Blvd, Mandaluyong; site coords 14.5794 N, 121.0359 E,
  ~3.7 km from cell center; MSL pressure is smooth at this scale).
- **Raw file**: `_raw_openmeteo_pressure.csv` (as exported, with API metadata
  header), user-downloaded 2026-06-11; derived by `parse_pressure.py`.
- **Window**: 2025-06-11 .. 2026-06-11 (matches all covariate datasets).
- **Verification**: single-source (ERA5) at onboarding. ⚠️ Second-source
  spot-check (PAGASA Port Area / NAIA synoptic station) PENDING — until then the
  dataset is admitted for *null-expected covariate tests only*, and any positive
  finding against draws would require the second source before being reportable
  (mirror of the lotto two-source rule, applied with proportionate force).

## 4. Row-level audit (census 2026-06-11)

366/366 days present, 0 missing, 0 duplicates, 0 NaNs, 0 min≤mean≤max
violations. Range 996.2–1016.4 hPa (mean 1010.0) — physically plausible for
Manila MSL. Lowest values 2025-11-09/10 (996.2/998.6) and 2025-07-19 (999.7),
consistent with wet-season/typhoon passages; retained (real weather, not errors).

## 5. Era registry (declared before testing, A5)

NW-monsoon dry season (≈Nov–Apr, higher mean, low variance) vs SW-monsoon wet
season (≈May–Oct, lower mean, typhoon lows): a known **annual cycle + synoptic
autocorrelation** structure. Any within-dataset structure finding must beat a
null preserving this (block/seasonal null), and any draws-coupling claim is
era-gated by it.

## 6. Freeze declaration

Full window is **exploration** for within-dataset structure; for draws-coupling
tests the standing relational confirmation discipline applies (A6): registered
expectation filed in `docs/RESULTS_PRESSURE.md` before the run. Appends follow
the weekly pipeline with ERA5's ~5-day lag.

## 7. Use in project

Joins the covariate bundle (tidal, sun/moon, Kp). First registered run:
recovery curve (expect structure — autocorrelated weather) + per-game date-paired
CCA/permutation vs draw features (expect null), `src/relational_pressure.py`.
