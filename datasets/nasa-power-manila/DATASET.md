# DATASET — nasa-power-manila

**Status**: ONBOARDING (awaiting fetch + cross-check on a network-enabled
machine) · card drafted 2026-07-07 per THEOREM_GOVERNANCE Part 4 · Owner: lab owner

Purpose: the **second independent source** for the Manila atmospheric-pressure
covariate. README Limitations gates every positive pressure claim on a second
source; this dataset closes that gate once cross-checked. NOT admissible for
instruments until this card is completed and Status flips to ACTIVE.

## 1. H₀ and executable null simulator (A1)
Covariate dataset — identical framing to `openmeteo-pressure-manila`: the null
lives on the *pairing* ("pressure has no relationship with draw outcomes");
admissible nulls are shuffled pairing and block-shuffle/circular shift of the
series (never plain value permutation as sole control, A5).

## 2. Files
| file | role |
|---|---|
| `fetch_nasa_power.py` | fetch script (NASA POWER MERRA-2, daily PS, 14.60N 120.98E) |
| `_raw_nasa_power.json` | raw provenance (written by fetch; `_`-prefix convention) |
| `pressure_daily_nasa.csv` | canonical daily series, `date,pressure_hpa` |
| `crosscheck_sources.py` | agreement audit vs `openmeteo-pressure-manila` |

## 3. Canonical schema (frozen once ACTIVE)
`date` (YYYY-MM-DD, Asia/Manila calendar dates), `pressure_hpa` (float,
MERRA-2 surface pressure PS, kPa × 10). Schema changes force re-onboarding.

## 4. Provenance / audit census — TO COMPLETE AT FETCH TIME
Run `crosscheck_sources.py` and record: overlap days, Pearson r, mean Δ,
max |Δ| vs the Open-Meteo/ERA5 series. Acceptance guidance (reanalysis vs
reanalysis, same gridpoint scale): r > 0.95 and stable mean offset. Any
disagreement beyond that blocks ACTIVE status and is logged here.

## 5. Era registry
Single era (MERRA-2 reanalysis, constant methodology over the window).

## 6. Frozen / holdout structure (BINDING)
Mirrors the draw data's frozen/holdout split: rows on dates inside the
lab's frozen draw window follow the same freeze; later dates are holdout.

## 7. Anomalies
None known at draft time; fetch-time gaps (missing days, fill values ≤ 0)
are dropped by the fetch script and MUST be counted here.

## 8. Update pipeline & instruments
Re-run `fetch_nasa_power.py` with an extended END (append-style overwrite of
the canonical CSV from raw; never hand-edit). Serves the same instruments as
the first pressure source (paired CCA, seasonal batteries) — a positive
pressure claim requires agreement across BOTH sources.

## 9. Loading snippet
```python
import csv
rows = list(csv.DictReader(open("datasets/nasa-power-manila/pressure_daily_nasa.csv")))
```

## 10. Domain cautions
MERRA-2 gridpoint ≠ station barometer: constant offsets vs sea-level or
station pressure are expected and harmless for the covariate use (temporal
structure is what instruments consume); never mix the two sources in one
series — they enter instruments as separate, cross-validating covariates.
