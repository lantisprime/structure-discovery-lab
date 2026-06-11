# Atmospheric Pressure (PCSO Draw Site) — Onboarding & Relational Results

**Date**: 2026-06-11 · **Dataset**: `datasets/openmeteo-pressure-manila/`
(card complete; ERA5 via Open-Meteo, grid cell 14.587 N 121.003 E; 366 days,
audit clean: 0 missing/dupes/NaNs, range 996.2–1016.4 hPa; **single-source
caveat in force** — see card §3) · **Scripts**: `src/relational_pressure.py`,
`src/relational_batch7.py` · **Registration**: card §6 + `REGISTRATION_BATCH7.md`
· **Raw outputs**: `results/relational_pressure.json`, `results/relational_batch7.json`
· **Figure**: `fig8_pressure_experiments.png`.

## Baseline run (registered H-P1, H-P2)

**H-P1 — pressure is structured: CONFIRMED.** Subset-to-whole recovery rises
from the null band at k=5% to z = +4.5 / +7.4 / **+10.5** at k = 10/20/40%
(within-series permutation null, 10 seeds × m=49).

**H-P2 — draws do not couple to pressure: CONFIRMED (joint null).** Per-game
date-paired held-out CCA (draw features vs [P_mean, P_min, P_max, P_range]):

| Game | n paired | held-out ρ₁ | CCA p | corr(sum, P_mean) | scalar p |
|---|---|---|---|---|---|
| 6/42 | 154 | 0.132 | 0.180 | +0.044 | 0.555 |
| 6/45 | 156 | 0.261 | 0.030 | −0.180 | 0.025 |
| 6/49 | 155 | 0.107 | 0.220 | +0.009 | 0.920 |
| 6/55 | 156 | −0.072 | 0.715 | −0.063 | 0.475 |
| 6/58 | 155 | −0.208 | 0.940 | +0.139 | 0.075 |

min CCA p = 0.030 > Šidák threshold 0.0102 (m=5) → **joint null**. The 6/45 raw
pair (CCA 0.030 / scalar 0.025) is two correlated statistics of the same rows
(the scalar is a sub-statistic of the CCA — one flag, not two, C3); a minimum
this small among 5 tests occurs ~12% of the time under H₀, and the dataset's
single-source rule (card §3) would gate any positive claim regardless. Logged
for passive monitoring in the weekly pipeline.

## Batch 7 (registered; all four expectations confirmed)

**B7-1 — Seasonal partition (positive control for the batch-6 pipeline):**
the identical cross-quarter MMD that returned **30 nulls on lotto quarters**
rejects on pressure quarters at the permutation floor for **all 6 pairs**
(p = 0.005 each at m=199, Šidák 0.0085, **6/6 corrected rejections**; quarters
start 2025-06-11/09-10/12-11/2026-03-12). The instrument demonstrably detects
real regime structure — the lotto partition nulls are nulls of the data, not of
the method. (Registered: cross-regime rejection; observed: every pair, i.e. the
monsoon cycle separates even adjacent quarters.)
*Method note, caught by verification*: the first run used m=99, whose
permutation floor (0.01) sits **above** the corrected threshold — a corrected
rejection was unreachable at that resolution. Rerun at m=199 (floor 0.005)
before any verdict was published; logged here as a worked example of
permutation-resolution vs multiplicity-threshold interaction.

**B7-2 — Pressure vs other covariates (CCA, shuffled-pairing null):**

| Pairing | held-out ρ₁ | null q95 | p | registered |
|---|---|---|---|---|
| pressure vs sun/moon ephemerides | **0.567** | 0.148 | **0.005** (floor) | POSITIVE (annual cycle) — confirmed |
| pressure vs Kp geomagnetic | −0.012 | 0.135 | 0.605 | NULL — confirmed |

**B7-3 — First real-data Gromov–Wasserstein run** (shape gate at (120,3):
FPR 0.05, KS p 0.976 — passed):

| Pair (delay embeddings) | GW distortion | null mean | p | verdict |
|---|---|---|---|---|
| tidal vs moon | **0.023** | 0.103 | **0.05** (floor, m=19) | geometries align — lunar mechanism, registered positive confirmed |
| pressure vs lotto 6/55 sum | 0.097 | 0.113 | 0.30 | null, as registered |
| pressure vs tidal | 0.173 | 0.062 | 1.00 | exploratory: *anti*-similar — two structured but different shapes (monsoon drift vs clean loop) align worse than a matched Gaussian does |

The pressure↔tidal result is the honest face of GW: structure ≠ shared
structure. Both series are deeply non-random, and their intrinsic geometries
are *measurably different* — exactly what a distortion above the Gaussian null
band means. No claim of relationship is made or supported.

## Verdict

Pressure at the draw site behaves like every other physical covariate: rich
internal structure (recovery z +10.5, all quarters seasonally distinct),
coupled to the celestial cycle that drives it (ρ₁ = 0.567 with sun/moon), and
**unrelated to the draws by every admitted instrument** (CCA, scalar
correlation, GW geometry — all null). The covariate bundle now spans tides,
ephemerides, geomagnetics, and weather; the draws couple to none of them.
Decision layer unchanged.
