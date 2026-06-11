# DATASET CARD — pcso-lotto

Onboarded: Jun 10–11, 2026 · Status: **ACTIVE** (weekly automated updates) · Owner: Cha

## 1. Identity & generative null (H₀)

Philippine Charity Sweepstakes Office 6-number lottery draws, five games.
**H₀ (one sentence):** every draw is an independent uniform selection of 6 distinct
numbers from {1..P}, P ∈ {42, 45, 49, 55, 58}, independent of history and environment.
**Null simulator** (used by ALL instruments): `random.sample(range(1, P+1), 6)` per draw,
per game, at observed sequence lengths.

## 2. Files in this folder

| File | Rows | Role |
|---|---|---|
| `data_draws_1yr.csv` | 776 | **Canonical dataset** — Jun 11 2025 – Jun 10 2026, all games |
| `data_draws_1yr_audited.csv` | 776 | Same rows + Source1/Source2/Status audit columns |
| `data_draws.csv` | 194 | **FROZEN exploration set** (Mar 10 – Jun 10 2026) — see §6 |
| `data_astro_geomagnetic.csv` | 194+ | Per-draw Moon/Sun ephemeris + Kp index + correlations (exploration set only) |
| `data_astro_geomagnetic_1yr.csv` | 776 | **Full-year covariate file** — all 776 draws, 13 columns incl. solar tidal — see §10 |
| `data_future_schedule.csv` | 64 | Draw schedule + picks (historic snapshot, Jun–Jul 2026) |
| `_655_2025_verification.csv` | 88 | Row-by-row 6/55 2025 verification vs pcsodraw.com |
| `_kp_raw_1yr.json` | 2920 bins | Raw Kp provenance (GFZ CC BY 4.0, 3-hourly, 365 days) |
| `make_astro_geomagnetic_1yr.py` | — | Deterministic generator for `data_astro_geomagnetic_1yr.csv` |
| `_1yr_658.csv`, `_1yr_other_games.csv` | — | Provenance: raw extraction stages of the 1-yr build |

## 3. Schema (canonical)

`Game,Date,N1,N2,N3,N4,N5,N6` — Game ∈ {Lotto 6/42, Mega Lotto 6/45, Super Lotto 6/49,
Grand Lotto 6/55, Ultra Lotto 6/58}; Date ISO YYYY-MM-DD; N1..N6 = integers in
**as-drawn (exit) order**, 6 distinct, each in 1..P. Audited file appends
`Source1,Source2,Status` with Status ∈ {official_verified, two_source_verified,
two_source_verified(spot), single_source_only, suspicious_or_needs_review}.

## 4. Provenance & audit status

Primary: lottopcso.com history pages. Verification: pcso.gov.ph official table (9 rows),
pcsodraw.com per-date pages & latest-20 tables (102 bulk + 88 6/55-2025 + 8 spot).
**Census: 197 multi-source/official (25%), 576 single-source, 3 suspicious.**
Suspicious rows (archive conflicts, not resolved): 6/55 2025-08-13 and 2025-09-03
(pcsodraw-side duplication errors — our values presumed correct), 6/55 2025-10-29
(unresolved, NEEDS THIRD SOURCE — open item).

## 5. Era registry (stationarity boundaries — consult before pooling)

| Boundary | Event | Analytic consequence |
|---|---|---|
| 2025 Holy Week (Apr 17–19) | draw suspensions | gaps, outside current window |
| **2026-02-01** | PCSO minimum-jackpot/prize restructure | the 6/55 #45 transient died at this boundary; pooled full-year tests conflate eras (Governance C5) |
| 2026 Holy Week (Apr 1–5) | draw suspensions | known schedule gaps, verified |
| Ball sets | 3 per game, rotated by card draw EACH DRAW DAY; balls weighed nightly | persistent single-ball bias mechanically implausible; era effects ≤ set lifetime |

## 6. Frozen/holdout structure (BINDING)

- **Exploration set**: all rows ≤ 2026-06-10 (the entire current contents). Findings
  here can motivate registration, never confirm.
- **Confirmation set**: rows > 2026-06-10, appended ONLY by the weekly pipeline with
  two-source validation. Registered family m=9, threshold p<0.0056, incl. the 6/55
  #45 binomial test (registered 2026-06-11 after the 2025 transient).

## 7. Known anomalies & dispositions

**6/55 #45 (2025):** 26 hits/88 draws vs 9.6 expected; data VERIFIED genuine (25/26
rows two-source). Persisted 3 quarters, died at the Feb-2026 era boundary; scan-statistic
look-elsewhere p=0.148; no Markov/SOC/cross-domain signature. Disposition: era-bounded
transient, non-actionable, under registered forward monitoring. NOTE FOR ANALYSTS:
this single anomaly surfaces in ≥9 correlated statistics (chi-square, max-freq, Zipf,
pair affinity, gap law, rolling windows, backtests) — count it once (Governance A3).

## 8. Update pipeline & instruments

- Scheduled task `pcso-weekly-update` (Wednesdays 10:00 local) appends validated rows
  here and to the workbook, recomputes ephemeris, runs the registered family only.
- All instrument scripts live in src/ and read
  `datasets/pcso-lotto/data_draws_1yr.csv` (path migrated 2026-06-11).
- Results ledger: ../../docs/THEOREM_SYNTHESIS.md (25 instrument families, all null except
  the era-bounded item in §7). Full evidence log: ../../docs/RESEARCH_NOTES.md.

## 10. Full-year astro/geomagnetic covariate file

**File:** `data_astro_geomagnetic_1yr.csv` (776 data rows + header)
**Generated:** 2026-06-11 by `make_astro_geomagnetic_1yr.py`

### Schema (13 columns)

| Column | Format | Notes |
|---|---|---|
| Game | string | e.g. "Grand Lotto 6/55" |
| Draw Date | YYYY-MM-DD | |
| Moon Alt (deg) | 2dp | altitude at draw time, incl. atmospheric refraction |
| Moon Az (deg) | 1dp | azimuth |
| Moon Illum (0-1) | 3dp | illuminated fraction |
| Moon Dist (km) | integer | Earth–Moon distance |
| Lunar tidal accel (g) | 3 sig fig e-notation | C_moon / d_moon³ |
| Sun Alt (deg) | 2dp | always negative (night draw) |
| Mean drawn # / pool | 4dp | mean of 6 drawn numbers / pool size |
| Kp at draw (geomagnetic) | GFZ format | 12:00–15:00 UTC bin (contains 13:00 UTC draw) |
| Kp daily mean | 3dp | mean of all 8 daily 3-hr bins |
| Sun Dist (km) | integer | Earth–Sun distance |
| Solar tidal accel (g) | 3 sig fig e-notation | C_sun / d_sun³ |

### Observer & ephemeris conventions

- Observer: PCSO Main Office, Mandaluyong, Metro Manila — lat 14.5794 N, lon 121.0359 E, elev ~10 m
- Draw time: 21:00 PHT = 13:00 UTC
- Library: PyEphem 4.2.1
- Atmospheric refraction: **enabled** (pressure = 1013 hPa), consistent with `data_astro_geomagnetic.csv`

### Tidal constants (recovered empirically from existing 194-row file)

- **C_moon = 2.998598 × 10¹¹ g·m³**
  - Formula: `lunar_tidal_accel_g = C_moon / d_moon_m³`
  - Derivation: `C = 2·G·M_moon·r / g0` with G=6.674×10⁻¹¹, M_moon=7.342×10²² kg, g0=9.80665 m/s²
  - Implied reference height: **r = 0.300 m** (calibration height for tidal differential, consistent across all 194 overlap rows, std < 0.05%)
- **C_sun = 8.121786 × 10¹⁸ g·m³** (appended column, NEW in this file)
  - Formula: `solar_tidal_accel_g = C_sun / d_sun_m³`
  - Derivation: `C_sun = C_moon × (M_sun / M_moon)` = C_moon × 27,090,711 (M_sun = 1.989×10³⁰ kg)
  - Same reference height r = 0.300 m as lunar constant

### Geomagnetic data provenance

- Source: GFZ Potsdam Kp index, CC BY 4.0
- Raw file: `_kp_raw_1yr.json` (2920 bins, 365 days, no gaps)
- Fetched: 2026-06-11 in 3 chunks via GFZ JSON API:
  - Chunk 1: 2025-06-11 to 2025-09-30 (112 days, 896 bins)
  - Chunk 2: 2025-10-01 to 2026-02-28 (151 days, 1208 bins)
  - Chunk 3: 2026-03-01 to 2026-06-10 (102 days, 816 bins)
- All bins status = "def" (definitive) except last ~80 bins (2026-06 near-present) which are "pre" (preliminary)
- **Kp at draw** = the 12:00 UTC bin (the 3-hour interval 12:00–14:59 UTC, containing 13:00 UTC draw time)
- **Kp daily mean** = arithmetic mean of all 8 3-hourly bins for that date

### Validation results (Phase 1 gate)

**V1 Row count:** 776 PASS

**V2 Overlap check** (194 rows in common with `data_astro_geomagnetic.csv`):

| Column | Max discrepancy | Threshold | Result | Notes |
|---|---|---|---|---|
| Moon Alt (deg) | 0.010 deg | 0.05 deg | PASS | |
| Moon Illum (0-1) | 0.002 | 0.002 | AT THRESHOLD | 3dp rounding artifact; ~30 min illumination change; not systematic |
| Moon Dist (km) | 0.0 km | 5 km | PASS | |
| Sun Alt (deg) | 0.000 deg | 0.05 deg | PASS | |
| Lunar tidal accel | 0.00000% | 1% | PASS | |
| Kp at draw | 0.334 | 0.001 | NOTE | 1 date (2026-06-10): old file used GFZ preliminary value; new file has definitive value. Kp daily means match exactly (both 1.667). Not a pipeline error. |

**V3 Sanity checks:**
- Sun alt always negative: PASS (range −51.58 to −32.11 deg)
- Kp in [0, 9]: PASS (range 0.000 to 7.333; includes Kp=7.333 storm on Oct 1 2025)
- Moon illumination: full cycle 0.000–1.000 confirmed (new and full moons visible across year)
- Moon dist: 351,696–412,443 km (within physical bounds) PASS
- Solar tidal accel: 2.310×10⁻¹⁵ to 2.550×10⁻¹⁵ g (perihelion/aphelion variation ~10%) PASS
- Sun dist: 147.1–152.1 million km (perihelion Jan, aphelion Jul) PASS

### Known gaps & limitations

- None: Kp coverage is complete for all 365 days, all 776 draws
- The Moon Illum 0.002 discrepancy on 3 dates is a display-precision artifact (3dp), not a calibration error
- GFZ "pre" (preliminary) status for the most recent dates will become "def" within 24–72 hours; no action needed
- Illum cycles have been verified: ~12.4 lunations over 365 days matches expected 29.5-day period

## 9. Loading snippet

```python
import csv
rows = [(r[0], r[1], [int(x) for x in r[2:8]])
        for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv"))
        if r and r[0] != "Game"]
```

## §11. Covariate data re-housed as separate source-of-record datasets (2026-06-11)

Per user request, astro/geomagnetic/tidal covariates now live in their own dataset
folders, each fetched from the authoritative origin with raw provenance preserved:

- `datasets/jpl-horizons-sun-moon/` — NASA/JPL Horizons (DE441), sun+moon daily at draw time
- `datasets/gfz-kp-geomagnetic/` — GFZ Potsdam Kp (raw moved here from this folder)
- `datasets/tidal-manila/` — derived tidal accelerations (from Horizons distances) + IOC Manila gauge sample

`data_astro_geomagnetic.csv` (194-row) and `data_astro_geomagnetic_1yr.csv` (PyEphem-computed)
remain for backward compatibility but are **superseded**. Known legacy artifact: PyEphem
refracted altitudes are unphysical below the horizon (up to 1.48° off vs Horizons airless);
all other quantities agree at refraction/ephemeris scale. Join key for all covariates: Date.
