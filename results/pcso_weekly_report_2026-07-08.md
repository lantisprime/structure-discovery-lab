# PCSO Weekly Update — Report

**Run date:** 2026-07-08 · **Pipeline:** `pcso-weekly-update` · **Dataset:** `datasets/pcso-lotto/`

## Summary

- **28 new draws appended**, spanning **2026-06-25 → 2026-07-07** (previous latest was 2026-06-24). Per game: Lotto 6/42 ×6, Mega 6/45 ×5, Super 6/49 ×6, Grand 6/55 ×5, Ultra 6/58 ×6.
- **Validation: all 28 draws matched on two independent sources (pcsodraw.com + lottopcso.com), zero disagreements**, and in every case the as-drawn order was identical between the two sites. pcsodraw.com draw-number continuity is unbroken for every game.
- **Confirmation tests (pre-registered family m = 9): no flags.** Every computable p-value is above the Bonferroni threshold (lowest = 0.020098 > 0.00556).
- **6/55 number-45:** 1 occurrence in 11 confirmation draws (expected 1.20), two-sided binomial p = 1.000 — consistent with the era-bounded transient having died at the 2026-02-01 boundary.
- **Exploration set (draws ≤ 2026-06-10) remains frozen and byte-identical** to the pre-run backup. All appends are pure additions.
- Workbook recalculated with LibreOffice: **786 formulas, zero errors.**
- **Closeout audit (2026-07-10):** the original untracked result had no generating script. `src/pcso_weekly_update.py` now reproduces the registered null with an explicit RNG-stream contract; two separate runs are byte-identical. Corrected Monte Carlo values change no flag or interpretation.

## 1. New draws appended (as-drawn order)

| Date | Game | Winning combination |
|---|---|---|
| 2026-06-25 | Lotto 6/42 | 26-35-12-08-25-23 |
| 2026-06-25 | Super Lotto 6/49 | 49-19-15-46-25-36 |
| 2026-06-26 | Mega Lotto 6/45 | 09-41-22-45-05-10 |
| 2026-06-26 | Ultra Lotto 6/58 | 53-54-44-57-51-07 |
| 2026-06-27 | Lotto 6/42 | 24-31-03-36-35-23 |
| 2026-06-27 | Grand Lotto 6/55 | 38-27-33-32-49-31 |
| 2026-06-28 | Super Lotto 6/49 | 32-01-35-23-14-29 |
| 2026-06-28 | Ultra Lotto 6/58 | 46-56-08-01-03-05 |
| 2026-06-29 | Mega Lotto 6/45 | 33-13-06-21-18-44 |
| 2026-06-29 | Grand Lotto 6/55 | 01-17-50-25-26-12 |
| 2026-06-30 | Lotto 6/42 | 01-10-24-27-08-26 |
| 2026-06-30 | Super Lotto 6/49 | 26-47-05-44-10-22 |
| 2026-06-30 | Ultra Lotto 6/58 | 14-43-54-52-11-58 |
| 2026-07-01 | Mega Lotto 6/45 | 04-02-36-19-24-17 |
| 2026-07-01 | Grand Lotto 6/55 | 26-42-06-46-44-32 |
| 2026-07-02 | Lotto 6/42 | 29-09-31-33-19-24 |
| 2026-07-02 | Super Lotto 6/49 | 23-22-38-05-48-44 |
| 2026-07-03 | Mega Lotto 6/45 | 43-02-13-05-36-01 |
| 2026-07-03 | Ultra Lotto 6/58 | 15-25-54-27-08-56 |
| 2026-07-04 | Lotto 6/42 | 06-05-25-12-23-08 |
| 2026-07-04 | Grand Lotto 6/55 | 14-15-23-13-45-09 |
| 2026-07-05 | Super Lotto 6/49 | 14-15-33-40-02-34 |
| 2026-07-05 | Ultra Lotto 6/58 | 16-38-47-49-33-46 |
| 2026-07-06 | Mega Lotto 6/45 | 03-36-06-32-16-45 |
| 2026-07-06 | Grand Lotto 6/55 | 49-04-25-55-18-42 |
| 2026-07-07 | Lotto 6/42 | 20-16-12-35-05-06 |
| 2026-07-07 | Super Lotto 6/49 | 26-18-42-19-11-03 |
| 2026-07-07 | Ultra Lotto 6/58 | 50-22-58-57-43-29 |

All rows validated: 6 distinct numbers within pool, no duplicate game+date.

Row counts after update: `data_draws.csv` 224 → **252**; `data_draws_1yr.csv` / `_audited.csv` 806 → **834**; `data_astro_geomagnetic.csv` 224 → **252** draw rows (summary block preserved intact below the new rows). Workbook **Draws** sheet → **252** data rows; **Moon-Sun Test** → **252** ephemeris rows.

## 2. Validation outcome

- The official `pcso.gov.ph/SearchLottoResult.aspx` page is an ASP.NET postback form that returns an empty shell to a plain GET (no POST possible under the web_fetch-only constraint), so it could not serve as a programmatic source this run — same as prior runs.
- **Source 1: lottopcso.com** (per-game history + daily result pages). **Source 2: pcsodraw.com** (per-game "Latest & Archival Results" tables with draw numbers, plus the homepage for the most recent 2026-07-06/07 draws).
- **Every appended number matches across both sources, in identical as-drawn order. No source disagreements; nothing withheld.**
- pcsodraw draw-number continuity (no gaps): 6/42 1795→1801, 6/45 2961→2966, 6/49 1834→1840, 6/55 2452→2457, 6/58 1589→1595.
- Audit file: `Status = two_source_verified`, `Source1 = lottopcso.com`, `Source2 = pcsodraw.com` for all 28 rows.
- Closeout provenance limitation: the July 8 executor did not retain raw HTML or exact per-date URLs. `datasets/pcso-lotto/provenance/pcso_weekly_2026-07-08.json` is a retrospective manifest of the contemporaneous audited CSV, temporary append script, and this report. The source-match claim was not independently re-fetched during closeout.
- 2026-07-08 draws (6/45, 6/55) were not yet published at fetch time (drawn 9 PM PHT tonight); they will be picked up next run.

## 3. Ephemeris

Moon alt/az/illumination/distance, lunar tidal acceleration, and Sun altitude recomputed with PyEphem 4.2.1 at observer 14.5794 N, 121.0359 E, elev 10 m, 13:00 UTC (= 21:00 PHT), pressure 1013 hPa. The setup was validated against stored rows and reproduced them exactly (e.g. 2026-06-24: alt 52.75°, az 212.1°, dist 395,205 km, tidal 4.86e-15, sun −32.18° — exact match; Moon illumination agrees within the documented ≤0.002 3-dp rounding artifact noted in DATASET.md §10 V2).

**Kp (geomagnetic):** left **blank** for the new draws. The GFZ endpoint (`kp.gfz.de`) is not reachable under the web_fetch provenance / no-HTTP-client constraint, and recent values would be GFZ-preliminary regardless. This matches established practice for the 2026-06-11..24 draws. A GFZ definitive backfill for 2026-06-11..07-07 remains an open follow-up.

## 4. Confirmation tests (pre-registered, held-out data only)

Confirmation set = draws after 2026-06-10 → **58 draws** (6/42 ×12, 6/45 ×11, 6/49 ×12, 6/55 ×11, 6/58 ×12), up from 30 last week. Family m = 9. **Flag threshold = 0.05/9 = 0.00556.** (The task text writes "0.05/9 = 0.00625"; 0.05/9 is mathematically 0.00556, the value registered in DATASET.md §6 and used by prior runs, so 0.00556 was applied.) MC/permutation seed = 20260708. Full output: `results/pcso_confirmation_2026-07-08.json`.

Closeout procedure: one `random.Random(20260708)` stream in the published test
order; each null draw is `random.sample(range(1, P+1), 6)`; Monte Carlo and
permutation p-values use the add-one correction. The predictor for covariate
tests is standardized within game before the global permutation, preserving the
registered protection against cross-game pooling confounds.

| Test | Statistic | p-value | Flag |
|---|---|---|---|
| Chi-square uniformity (MC 10k) — Lotto 6/42 (n=12) | χ²=54.00 | 0.020098 | no |
| Chi-square uniformity (MC 10k) — Mega 6/45 (n=11) | χ²=39.00 | 0.504350 | no |
| Chi-square uniformity (MC 10k) — Super 6/49 (n=12) | χ²=31.44 | 0.941506 | no |
| Chi-square uniformity (MC 10k) — Grand 6/55 (n=11) | χ²=37.33 | 0.935006 | no |
| Chi-square uniformity (MC 10k) — Ultra 6/58 (n=12) | χ²=52.06 | 0.505149 | no |
| Pearson perm (20k) — mean-drawn vs Moon altitude (n=58) | r=0.207639 | 0.116194 | no |
| Pearson perm (20k) — mean-drawn vs Moon illumination (n=58) | r=0.058347 | 0.666217 | no |
| Pearson perm — mean-drawn vs Kp | — | n/a | not computable (Kp blank) |
| Binomial — 6/55 number-45 (n_655=11) | k=1, exp=1.20 | 1.000 | no |

**Flagged: none.**

Audit correction: the original hand-authored values were not reproducible because
no script or RNG-stream allocation was retained. Re-running the registered null
changes some Monte Carlo values but leaves all eight computable tests unflagged.
The lowest chi-square p (6/42, 0.020098) is above the family threshold and is
not corrected-significant. The mean-drawn vs Moon-altitude correlation continues
its regression toward zero as n grows (r = 0.63 at n=13 → 0.21 at n=30 →
0.207639 at n=58), consistent with a noise fluctuation rather than a persistent
effect.

## 5. Integrity & scope

- Exploration set (≤ 2026-06-10) is **frozen and byte-identical** to the pre-run backup: verified for all three draw CSVs (777 exploration rows each incl. header) and the 194 astro exploration rows. Appends are pure byte-suffix additions.
- Original **CRLF line endings preserved** in all four CSVs; astro summary/correlation block relocated intact below the new rows.
- Reproducibility closeout: manifest/CSV agreement PASS; frozen-prefix SHA-256 guards PASS; two full runner executions byte-identical at SHA-256 `11c8af729f0353a83f130253100dadb5fb3413d49cceec11fa031d64daf054a4`.
- Workbook: **Draws** and **Moon-Sun Test** extended; **Frequency** SUMPRODUCT ranges extended 225→253 (249 formulas) and Moon-Sun correlation ranges extended to row 253 (moon/sun t-tests n=252; Kp t-tests kept n=194 as Kp columns gain no new values). Recalculated via LibreOffice → **786 formulas, 0 errors**. Protected sheets **Protocol, EV Calculator, Read Me, Hot-Cold, Future Draws** verified **0 formula/text diffs** vs backup; `lotto_picker.html` untouched.
- LibreOffice note: the Basic-macro recalc path (`scripts/recalc.py`) could not complete `store()` within the sandbox's 45-second command limit (soffice cold-start alone exceeds it). Recalculation was instead performed via `soffice --headless --convert-to xlsx`, which recomputed all formulas and cached values in ~1 s; the resulting workbook is structurally identical (same 8 sheets, same 786 formulas, extended ranges) with zero error cells, and was promoted to the canonical file.

**Reminder:** confirmation-set results are G0 exploratory forward monitoring. The
m=9 correction controls one look only; no sequential alpha-spending rule has been
registered across weekly cumulative looks. A flag (none this week) would mean
"requires a separately registered fresh replication," never a betting
recommendation. Exploration-set findings remain frozen and are not re-tested.
