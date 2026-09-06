# RESULTS — PCSO refresh 2026-09-06: official data, monitoring, conscious-selection instrument, strategy backtest

Grade: **G0 exploratory** throughout (no REGISTRATION_*.md was opened; nothing here enters the
confirmation family). Executor: Claude Fable 5.1 session (author of the three scripts); verification:
two-run byte-identical for every output, cross-model execute-only re-run recorded in
`results/verification_pcso_refresh_2026-09-06.md`. Commitment snapshot before execution:
`results/commitment_ledger.txt` digest `83b4bcdc3df1ad58…` (pre-run); a closeout snapshot follows.

## 1. Data refresh (Part 4 D3/D4/D8)

| Item | Value |
|---|---|
| New draws appended | 128 (2026-07-08 … 2026-09-05; 6/42 26 · 6/45 26 · 6/49 25 · 6/55 26 · 6/58 25) |
| Primary source | **pcso.gov.ph** `SearchLottoResult.aspx` date-range search, per game, raw HTML retained (`datasets/pcso-lotto/provenance/raw_2026-09-06/`, 22 gzipped captures) |
| Cross-checks | lottopcso.com 128/128 agree; pcsodraw.com 100/100 agree (its 20-draw window); draw-number continuity consistent for all five games across the 28 draws pcsodraw does not cover |
| Conflicts | 0 |
| Full-year official re-verification | all **834** rows previously on file re-fetched from the official page: **834 exact matches (exit order included), 0 mismatches, 0 missing** — including the three `suspicious_or_needs_review` 6/55 rows (M4) |
| Canonical rows now | `data_draws_1yr.csv` 962 · `data_draws.csv` 380 · audited 962 (`official_verified` for the new rows) · astro 380 dated rows (PyEphem 4.2.1; generator parity 54/58 exact, 4 rows differ by 0.001 in Moon Illum — the §10 rounding artifact) |
| New file | `data_official_draws_jackpots.csv` — 984 official draws (Jun 1 2025 … Sep 5 2026) with jackpot (PHP) and number of winning bets: the payout-layer input |
| Manifest | `datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json` (`expected_new_draws` 128, per-draw sources, jackpot, winners, continuity) |
| Not done | the Excel workbook was not extended (its invariants are verified unchanged); Kp backfill still open, so the registered Kp test stays non-computable |

## 2. Registered m=9 monitoring family on the confirmation set (n=186 draws after 2026-06-10)

Script `src/pcso_monitoring_run.py` (validators and family imported from the July closeout module),
seed 20260906, MC 10,000 / permutations 20,000, Bonferroni threshold 0.05/9 = 0.005556.
Output `results/pcso_confirmation_2026-09-06.json` (two-run SHA-256 `baff97e8ed93d8e7…`).

| Test | n | statistic | p | flag |
|---|---|---|---|---|
| chi-square MC, Lotto 6/42 | 38 | χ²=48.68 | 0.0662 | no |
| chi-square MC, Mega 6/45 | 37 | χ²=38.68 | 0.4981 | no |
| chi-square MC, Super 6/49 | 37 | χ²=58.76 | 0.0457 | no |
| chi-square MC, Grand 6/55 | 37 | χ²=51.51 | 0.3758 | no |
| chi-square MC, Ultra 6/58 | 37 | χ²=64.34 | 0.1069 | no |
| mean-drawn vs moon altitude (perm.) | 186 | r=−0.015 | 0.833 | no |
| mean-drawn vs moon illumination (perm.) | 186 | r=+0.005 | 0.950 | no |
| mean-drawn vs Kp | — | not computable (Kp blank) | — | — |
| 6/55 ball #45 binomial | 37 | 2 hits vs 4.04 expected | 0.427 | no |

**Verdict: 0 flags; minimum p = 0.046 > 0.0056.** The 2025 #45 excess remains dead (2 hits in 37
post-freeze 6/55 draws). Repeated-look caveat unchanged: weekly cumulative looks are G0 monitoring
without a sequential alpha-spending rule.

## 3. Strategy backtest — does any selection rule change P(match)? (family `strategy-backtest`, m=7)

Script `src/pcso_strategy_backtest.py`, 834 draws after a 30-draw warm-up, 2 tickets per play,
300 replicates per draw for the three pickers (100 for the "prediction" rules), seed 20260906.
Unit of independence = the draw (replicate tickets scored on one draw are correlated through it);
statistic = mean per-draw difference in matches per ticket versus the uniform-disjoint baseline on
the **same** draws; p from a sign-flip permutation (m=9,999, floor 1e-4); Šidák α for m=7 = 0.0073.
Output `results/pcso_strategy_backtest_2026-09-06.json` (SHA-256 `b5195e2023828dc4…`).

| Strategy | mean matches/ticket (H₀ 0.7333) | Δ vs uniform, same draws | z | p | P(≥3) obs / H₀ |
|---|---|---|---|---|---|
| uniform disjoint pair (baseline) | 0.7320 | — | — | — | 0.01902 / 0.01925 |
| picker v1 (four pattern filters, the previous web page) | 0.7360 | +0.0040 | +2.71 | **0.0061** | 0.01929 / 0.01925 |
| picker v2 (CSI-filtered, this page) | 0.7401 | +0.0081 | +2.45 | 0.0139 | 0.01961 / 0.01925 |
| hot top-6 (trailing 50 draws) | 0.7440 | +0.0120 | +0.75 | 0.46 | 0.01785 / 0.01925 |
| cold bottom-6 (trailing 50) | 0.6912 | −0.0408 | −2.58 | 0.0101 | 0.01766 / 0.01925 |
| overdue (longest gap) | 0.7310 | −0.0010 | −0.06 | 0.95 | 0.01833 / 0.01925 |
| repeat last draw | 0.7285 | −0.0035 | −0.30 | 0.77 | 0.02029 / 0.01925 |
| Markov order-1 pair proxy | 0.7390 | +0.0070 | +0.42 | 0.67 | 0.02172 / 0.01925 |

Best result in 1.67 million backtested tickets: one 5-match (three strategies), never a jackpot.
Fixed 3-match return ₱0.67–0.92 per ₱25 ticket.

**One flag** (picker v1, p = 0.0061 < 0.0073). A3/A4 trace before reporting: the v1 and v2 filters
push tickets toward numbers above 31, and in this sample the drawn numbers above 31 exceed their
expectation (1,912 vs 1,844.4, z = +2.12, itself not significant); the per-draw v1 and v2 differences
correlate at 0.40 (same driving rows), while cold does not share them (0.07). The registered per-game
chi-square on the same confirmation draws is null (§2), so this is the marginal-frequency
fluctuation of one year seen through a filter that happens to lean on it — **charged once as the
marginal-frequency class, not as evidence of an exploitable edge**; per A4 it stands as an
exploratory flag that only a fresh-draw replication can promote or dissolve. No "prediction" rule
(hot, cold, overdue, repeat, Markov) differs from uniform. Power statement: with 834 paired draws the
test detects a shift of ≈0.004 matches/ticket at z≈2.7, i.e. effects an order of magnitude smaller
than any that would matter for payout.

## 4. Conscious-selection instrument — first run (kb card 28, family `payout-sharing`, m=2)

Script `src/csi_popularity.py`, 984 official draws, 77 draws with ≥1 winning bet (94 bets).
**Stratification is essential**: pool size drives both the CSI level (6/42 tickets are mostly ≤31 by
construction) and the win rate (1/C(42,6) is 27× 1/C(58,6)). The first null trial, run pooled,
returned a null mean of +0.004 for T1 (7 standard errors from 0) — the Step-4 gate did its job and
the statistics were re-specified within game before any real-data claim was written down.

Step 4 null trial (500 simulated datasets of the real shape, uniform draws, Poisson winners
independent of the combination): T1 null mean 0.0010, sd 0.112 (499 distinct values); T2 null mean
0.0002, sd 0.031 — non-degenerate, centred on theory. C3 null correlation with the chi-square
frequency statistic on the same simulated draws: −0.03 / −0.05 (new equivalence class).

Step 6 first run (winners permuted within game, m=19,999, floor 5e-5; Šidák α for m=2 = 0.0253):

| Statistic | observed | null (Step 4) | z | perm. p |
|---|---|---|---|---|
| T1: mean within-game-standardized CSI, winner draws − winner-less draws | **+0.736 sd** | 0.001 ± 0.112 | 6.6 | **5e-05 (floor)** |
| T2: rank correlation (within-game CSI rank, winning bets) | **+0.162** | 0.000 ± 0.031 | 5.2 | **1e-04** |

Descriptive Poisson GLM with game fixed effects: winning bets ∝ exp(0.52 ± 0.075 · z_CSI) (Wald
z 6.9), log-jackpot slope +0.33 ± 0.15 (bigger jackpots, more bets, as expected), dispersion 2.2
(overdispersed, as Baker & McHale predict). Within-game tertiles of CSI: share of draws with a
winner 5.0% / 5.8% / **13.5%** (bottom / middle / top); winning bets per draw 0.050 / 0.089 / 0.162;
top-vs-bottom sharing multiplier ≈ **2.8×**. Power at the observed slope: 1.00.

**Verdict: both tests reject at the floor — the popularity proxy predicts jackpot sharing on PCSO
data.** This is a statement about *players*, not about the draw (A7: decision layer only). It changes
expected payout, never P(win). Caveats (card 28): winners are winning *bets* (one bettor can hold
several), only the jackpot tier is observable, weights are literature proxies that were fixed before
this run and must not be tuned on these draws, one era (Feb-2026 restructure inside the window).
Promotion (Step 8) requires a reset boundary and fresh draws.

## 5. Consequences for the web picker (`lotto_picker.html`)

- Constants now come from these three JSONs (monitoring p-values, CSI thresholds and parity vectors,
  backtest verdicts) and from the official page (jackpots, winners, Feb-2026 prize matrix).
- Ticket generation: CSPRNG uniform, disjoint pair, both tickets required to fall in the bottom 40%
  of the CSI distribution for that pool (q40 thresholds: 6/42 0.0243 · 6/45 0.0091 · 6/49 0.0282 ·
  6/55 0.0172 · 6/58 0.0033); the v1 four-rule filter is a strict subset of this rule.
- EV: hypergeometric tiers with the official Feb-2026 matrix (Category II/III are pools shared per
  winning bet — sales-dependent), 20% tax above ₱10k, Poisson co-winner split with the exploratory
  sharing multiplier exp(0.52·z_CSI) applied to the jackpot tier and shown as G0.
- The page states, above the fold, that nothing on it changes P(win) = 1/C(P,6).

## 6. Reproduction

```
.venv/bin/python src/pcso_monitoring_run.py --manifest datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json --verify
.venv/bin/python src/csi_popularity.py --verify
.venv/bin/python src/pcso_strategy_backtest.py --verify
```
Each prints `PASS sha256=…; wrote=none` when the regenerated bytes equal the committed file.
