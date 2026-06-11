# Dataset: jpl-horizons-sun-moon

**Source of record**: NASA/JPL Horizons API v1.2 (https://ssd.jpl.nasa.gov/api/horizons.api), ephemeris DE441.
**Fetched**: 2026-06-11 (Horizons run stamps 2026-Jun-10 22:23:40 / 22:23:59 Pasadena), two GET requests (Moon=301, Sun=10), raw responses preserved verbatim in `_raw_horizons_moon.txt` / `_raw_horizons_sun.txt` ($$SOE block + header summary).
**Observer**: topocentric, PCSO Main Office Mandaluyong — GEODETIC 121.0359 E, 14.5794 N, 0.02 km.
**Epochs**: daily at 13:00:02.88 UT (= 21:00 PHT draw time; the 2.88 s offset is Horizons' UT mapping of the requested JD grid), 2025-06-11 → 2026-06-11, 366 rows.
**Convention**: airless apparent az/el (QUANTITIES=4), illuminated fraction (10), observer range (20). **Airless ≠ legacy**: the superseded PyEphem file (pcso-lotto/data_astro_geomagnetic*.csv) used refracted altitudes at 1013 hPa.

## Files
- `_raw_horizons_moon.txt`, `_raw_horizons_sun.txt` — provenance (verbatim data blocks).
- `parse_horizons.py` — deterministic parser → `sun_moon_daily.csv` (+ emits ../tidal-manila/tidal_derived.csv).
- `sun_moon_daily.csv` — Date, Moon Az/Alt (deg), Moon Illum (0–1), Moon Dist (km), Sun Az/Alt (deg), Sun Dist (km).

## Validation (vs the independent PyEphem pipeline, all 776 draw dates)
| Quantity | Max |Horizons − PyEphem| | Verdict |
|---|---|---|
| Moon alt, alt > 5° | 0.167° | refraction + ephemeris scale — PASS |
| Moon alt, −1° < alt ≤ 5° | 0.588° | horizon refraction — expected |
| Moon alt, below horizon | 1.477° | **PyEphem artifact**: refraction formula applied below horizon, where it is unphysical; Horizons airless is correct. Logged as a legacy data-quality note. |
| Moon az | 0.145° (moon near zenith, az ill-conditioned) | PASS |
| Moon illum | 0.0075 | PASS |
| Moon dist | 42.3 km (~1×10⁻⁴ relative) | ephemeris-model scale — PASS |
| Sun alt | 0.017° | PASS |

The full-coverage comparison doubles as a transcription check on the raw blocks: a digit error would appear as an isolated outlier; none found (discrepancies are smooth functions of altitude).

## Known gaps / notes
- Daily sampling at draw time only (the draws are the use case).
- Airless altitudes: add refraction downstream if a use case needs optical visibility.
- 2026-06-11 row is one day past the draw set's last date (harmless surplus from the JD grid).
