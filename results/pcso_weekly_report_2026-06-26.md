# PCSO Weekly Update — Report

**Run date:** 2026-06-26 · **Pipeline:** `pcso-weekly-update` · **Dataset:** `datasets/pcso-lotto/`

## Summary

- **17 new draws appended**, spanning **2026-06-17 → 2026-06-24** (previous latest was 2026-06-16). Per game: Lotto 6/42 ×3, Mega 6/45 ×4, Super 6/49 ×3, Grand 6/55 ×4, Ultra 6/58 ×3.
- **Validation: all 17 draws matched on ≥2 independent sources, zero disagreements.** Draw-number continuity on pcsodraw.com is unbroken for every game.
- **Confirmation tests (pre-registered family m=9): no flags.** Every computable p-value is far above the Bonferroni threshold (0.0556 ≫ 0.00556).
- **6/55 number-45:** 0 occurrences in 6 confirmation draws (expected 0.66), two-sided binomial p = 1.0 — consistent with the era-bounded transient having died at the 2026-02-01 boundary.
- **Exploration set (draws ≤ 2026-06-10) remains frozen and byte-unchanged.** All appends are pure additions.
- Workbook recalculated with LibreOffice: **786 formulas, zero errors.**

## 1. New draws appended (as-drawn order)

| Date | Game | Winning combination |
|---|---|---|
| 2026-06-17 | Mega Lotto 6/45 | 34-35-09-10-19-32 |
| 2026-06-17 | Grand Lotto 6/55 | 55-31-46-37-48-01 |
| 2026-06-18 | Lotto 6/42 | 07-36-31-03-35-42 |
| 2026-06-18 | Super Lotto 6/49 | 27-26-21-06-20-16 |
| 2026-06-19 | Ultra Lotto 6/58 | 43-53-08-45-20-11 |
| 2026-06-19 | Mega Lotto 6/45 | 27-15-09-13-12-08 |
| 2026-06-20 | Lotto 6/42 | 24-39-23-05-38-12 |
| 2026-06-20 | Grand Lotto 6/55 | 24-10-55-36-04-41 |
| 2026-06-21 | Super Lotto 6/49 | 44-13-27-33-24-42 |
| 2026-06-21 | Ultra Lotto 6/58 | 15-05-45-11-17-39 |
| 2026-06-22 | Mega Lotto 6/45 | 28-03-24-31-18-16 |
| 2026-06-22 | Grand Lotto 6/55 | 37-32-23-35-53-18 |
| 2026-06-23 | Lotto 6/42 | 30-20-11-07-36-01 |
| 2026-06-23 | Super Lotto 6/49 | 44-08-32-42-12-27 |
| 2026-06-23 | Ultra Lotto 6/58 | 04-21-41-40-39-52 |
| 2026-06-24 | Mega Lotto 6/45 | 41-29-27-21-33-19 |
| 2026-06-24 | Grand Lotto 6/55 | 22-51-17-23-54-29 |

All rows validated: 6 distinct numbers within pool, no duplicate game+date.

Row counts after update: `data_draws.csv` 207 → **224**; `data_draws_1yr.csv` / `_audited.csv` 789 → **806**; `data_astro_geomagnetic.csv` 207 → **224** draw rows (summary block preserved). Workbook **Draws** sheet → 224 data rows; **Moon-Sun Test** → 224 ephemeris rows.

## 2. Validation outcome

- The official `pcso.gov.ph/SearchLottoResult.aspx` page is an ASP.NET form that returns an empty shell to a plain GET (no POST possible under the web_fetch-only constraint), so it could not serve as a programmatic source this run.
- **Source 1 (primary): lottopcso.com** per-date pages. **Source 2: pcsodraw.com** per-game results + per-date summary pages (draw numbers checked for continuity).
- The June 17 lottopcso per-date page would not render (returned empty on three attempts); that date was instead confirmed by **pcsodraw.com + GMA News + Inquirer.net**, all three matching exactly.
- **Every appended number matches across its two+ sources. No source disagreements; nothing withheld.**
- pcsodraw draw-number continuity (no gaps): 6/42 1792→1795, 6/45 2957→2961, 6/49 1831→1834, 6/55 2448→2452, 6/58 …→1589.
- Audit file: `Status = two_source_verified`, `Source2 = pcsodraw.com` (June 17 rows use `Source1 = gmanetwork.com`; all others `Source1 = lottopcso.com`).

## 3. Ephemeris

Moon alt/az/illumination/distance, lunar tidal acceleration, and Sun altitude recomputed with PyEphem at observer 14.5794 N, 121.0359 E, elev 10 m, 13:00 UTC, pressure 1013 hPa. The setup was validated against three existing stored rows and reproduced them exactly (e.g. Ultra 2026-06-16: alt −14.50°, az 302.1°, illum 0.032, dist 361,115 km, tidal 6.37e-15, sun −32.53° — exact match). Computed values also agree with the future-schedule snapshot.

**Kp (geomagnetic):** left **blank** for the new draws. The GFZ endpoint (`kp.gfz.de`) is not reachable under the web_fetch-only / no-HTTP-client constraint, and recent values would be GFZ-preliminary regardless. This matches the established practice already recorded in the workbook note for the 2026-06-11..16 draws.

## 4. Confirmation tests (pre-registered, held-out data only)

Confirmation set = draws after 2026-06-10 → **30 draws (6 per game)**. Family m = 9. **Flag threshold = 0.05/9 = 0.00556.** (The task text writes "0.05/9 = 0.00625"; 0.05/9 is mathematically 0.00556, which is the value registered in DATASET.md §6 and used by the prior run, so 0.00556 was applied.) Monte-Carlo / permutation seed = 20260626. Full output: `results/pcso_confirmation_2026-06-26.json`.

| Test | Statistic | p-value | Flag |
|---|---|---|---|
| Chi-square uniformity — Lotto 6/42 (n=6) | χ²=45.67 | 0.093 | no |
| Chi-square uniformity — Mega 6/45 (n=6) | χ²=36.50 | 0.674 | no |
| Chi-square uniformity — Super 6/49 (n=6) | χ²=53.83 | 0.118 | no |
| Chi-square uniformity — Grand 6/55 (n=6) | χ²=40.39 | 0.873 | no |
| Chi-square uniformity — Ultra 6/58 (n=6) | χ²=51.00 | 0.584 | no |
| Pearson perm — mean-drawn vs Moon altitude (n=30) | r=0.214 | 0.248 | no |
| Pearson perm — mean-drawn vs Moon illumination (n=30) | r=0.165 | 0.388 | no |
| Pearson perm — mean-drawn vs Kp | — | n/a | not computable (Kp blank) |
| Binomial — 6/55 number-45 (n_655=6) | k=0, exp=0.66 | 1.000 | no |

**Flagged: none.**

Note: last week the Moon-altitude correlation read r=0.63 (p=0.025, n=13) — below the per-test 0.05 line but never below the registered family threshold. With the larger confirmation set (n=30) it regressed to r=0.21 (p=0.25), the expected behaviour of a noise fluctuation rather than a real effect.

## 5. Integrity & scope

- Exploration set (≤ 2026-06-10, 776 rows in the 1-yr file) is **frozen and byte-identical** to the pre-run backup. CSV appends verified as pure byte-prefix matches; the astro summary block was relocated intact below the new rows.
- Original **CRLF line endings preserved** in all four CSVs (a mid-run LF normalization was caught and reverted).
- Untouched as required: Quick Pick, Protocol, EV Calculator sheets, and `lotto_picker.html`. Column formats per DATASET.md §3 retained.
- A new GFZ Kp definitive backfill for 2026-06-11..24 remains an open follow-up for a future run.
- 2026-06-25 draws (6/42, 6/49) were **not yet published** by the sources at fetch time; they will be picked up next run.

**Reminder:** confirmation-set results are exploratory monitoring. A flag (none this week) would mean "requires further replication," never a betting recommendation. Exploration-set findings remain frozen and are not re-tested.
