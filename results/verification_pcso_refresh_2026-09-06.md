# Verification — PCSO refresh 2026-09-06

Closeout date: 2026-09-06

## Scope and identity

Executor: Claude Fable 5.1 session (`claude-fable-5-1`) that also authored `src/pcso_monitoring_run.py`,
`src/csi_popularity.py`, `src/pcso_strategy_backtest.py`, the dataset append, kb card 28, and this note.
The checks below are mechanical same-session verification, **not** the independent executor the
cross-model rule requires. All three runs remain **G0 exploratory**.

Cross-model execute-only re-run: a Claude Haiku 4.5 dispatch (`claude-haiku-4-5-20251001`) with the
three `--verify` commands **terminated before running** (API rate limit, HTTP 429, request id
`req_011CemHsFk6JmH4VNXnDQaHW`, 2026-09-06 ~09:50 Asia/Manila).

Cross-model mathematical review (r2, ~11:55–12:30 Asia/Manila): **Codex gpt-6-astra** (OpenAI Codex
CLI, `--sandbox read-only`, files edited: 0) reviewed the four scripts and the draft predictor,
reconstructed the CSI first-run values and the backtest means from the data (its report states
"CSI `--verify` passed; reconstructed backtest means matched stored results"), and computed the
product-weight posterior, Bayes factors and order-1 tests independently; after the review was applied,
`src/pcso_next_draw_posterior.py` reaches the same conclusions with third-decimal differences in the
point estimates and a different overlap-test ordering (RESULTS §8). Report:
`results/codex_review_2026-09-06.md`. A second read-only Codex review of `lotto_picker.html`
(`results/codex_review_page_2026-09-06.md`) listed 12 required edits, all applied in r3. This satisfies the different-model-family requirement for the
CSI instrument and the posterior predictor; a separate-instance byte re-run of the monitoring and
backtest `--verify` commands remains the open item.

r2 two-run SHA-256 (after applying the review): `csi_popularity` `a1af7008d0d5c980…`,
`pcso_strategy_backtest` `67ddd1d039711995…`, `pcso_confirmation` `a2a4309bc58b97d6…` (within-game
lunar variant added), `pcso_next_draw_posterior` `e9308ba0252709f3…`.

## Checks (same session)

- PASS — official source: 984 rows fetched from pcso.gov.ph date-range search (per game, two ranges),
  raw HTML retained (22 gzipped captures, sha256 of the uncompressed bytes in the manifest).
- PASS — full-year re-verification: 834/834 rows on file match the official page exactly (exit order
  included); 0 mismatches; 0 rows absent from the official page.
- PASS — 128 new draws: official + lottopcso.com 128/128; official + pcsodraw.com 100/100 (its window);
  0 conflicts; pcsodraw draw-number continuity consistent for all five games across the uncovered gap.
- PASS — manifest validation: 128 unique, in-pool draws, ≥2 registered source ids each, status
  `official_verified`; batch equals the rows > 2026-07-07 in all three draw CSVs; latest date 2026-09-05.
- PASS — frozen exploration prefixes through 2026-06-10 unchanged (registered SHA-256) for all four CSVs.
- PASS — CRLF preserved on every line of the four append-only CSVs.
- PASS — astro join: all 186 confirmation draws join one-to-one; stored normalized means match; Kp blank.
  Generator parity on the pre-existing 58 confirmation rows: 54 byte-identical, 4 differ by 0.001 in
  Moon Illum only (documented rounding artifact).
- PASS — workbook invariants unchanged (8 sheets, 786 formulas, 252 draw rows, no cached errors).
- PASS — two-run byte identity: `pcso_confirmation_2026-09-06.json` sha256 `baff97e8ed93d8e79a3877bd0b6c7b3695371187fa7f29924e9854eb1409997c`;
  `csi_popularity_2026-09-06.json` `26c104c223759d3fadc8747e3fe0561102cc4d60ff76d88e38ed8e1c98f81a40`;
  `pcso_strategy_backtest_2026-09-06.json` `b5195e2023828dc4ca64dd37af9a04b1e4d2ff7e807976387ff711aefadeabde`.
- PASS — Step-4 null trial for kb card 28: 500 trials, non-degenerate, centred on theory after within-game
  stratification (the pooled version failed this gate and was replaced before any real-data claim).
- PASS — design verifier: 0 violations (276 test rows, 195 live; 9 new rows exploratory with a G0 run-ledger
  entry; new claim types `payout-sharing`, `strategy-edge` declared in the design map and families.json).
- PASS — ledger integrity verifier: 10 pass, 0 fail.
- PASS — web page CSI parity self-test against the 8 committed vectors (browser console badge).
- NOTE — commitment snapshot digest before execution: `83b4bcdc3df1ad58a4ae30c4ccc31afc133926c45bfb5623e110cda756cc604a`.
