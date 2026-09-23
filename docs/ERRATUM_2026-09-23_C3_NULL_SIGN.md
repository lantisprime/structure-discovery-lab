# Erratum 2026-09-23: sign error in the C3 null-stream loss-bound check

**Affects:** `results/pcso_model_leaderboard_2026-09-23.json` (v2 registered run, sha256 `d2657118aec3bfa4ccbc94d1ee7a4fe1ed35439eeaacdb7dd4957171926a1e1c`), field `c3_loss_bound_check.null_streams.fraction_satisfied`.
**Registered criterion (amendment v2, A4):** −log E_T ≤ −log v₀(0) + (T−1)·log(1/(1−6ρ/7)), registered conservative form 0.685304 + 0.0010005·T, which must hold on every null stream.

## What was wrong
- `src/pcso_model_registry.py:574`: `_null_rep` returns `r0["log_e_full"]`, which is **+log E_T**.
- Line 668: that value is appended to a list named `neg_loge_null`.
- Line 711: the list is compared against the bound for **−log E_T**.

The real-draws line (709) negates correctly. So the null-stream check tested log E_T ≤ bound instead of −log E_T ≤ bound. It flagged the null stream whose evidence *grew* most, not a stream that broke the bound. The flawed comparison also could not detect a genuine breach: a stream with a large −log E_T but a small +log E_T would have passed.

## Evidence
`results/exploratory/pcso_c3_null_diagnostic_2026-09-23.json` (sha256 `1efc321d…`): an exploratory rerun on the M5 Max at `77660f0` with the same seeds, keeping every stream's value.

| | registered (flawed comparison) | stated criterion |
|---|---|---|
| streams satisfying the bound | 399/400 = 0.9975 | **400/400 = 1.0** |
| flagged stream | s=169: log E_T = +2.4607 > 1.6798 | s=169: −log E_T = −2.4607, margin +4.14 nats |
| tightest margin over all streams and all t | — | 0.434 nats (s=139, t=256) |

- The diagnostic reproduces the registered 0.9975 bit-exactly using the harness's own `_null_rep`.
- `--verify` of the registered run passes (sha `d2657118…`), and the corrected replay (sha `cb8bdc93…`) passes likewise — both only with the pinned 994-draw inputs (conditioning snapshot `bcf39ca` / CSV at `77660f0`). A `--verify` inside a refreshed checkout currently mismatches for a separate reason (live-CSV input handling; tracked separately).
- Harness revisions: the as-produced record (`d2657118…`) was produced by the harness at `77660f0`; the corrected leaderboard (`cb8bdc93…`) was produced by `77660f0` plus this fix — both on the pinned 994-draw inputs.
- The real-draws check (−log E_T = 0.663963 ≤ 1.679801) is unaffected.

## Disposition
- **Record kept:** the leaderboard above is preserved byte-for-byte as produced, as the record, in commit `4c68593`.
- **Fix:** the harness is corrected in commit `322c889`, with a regression test. The leaderboard is regenerated under the same seed and run date. Only `c3_loss_bound_check.null_streams.fraction_satisfied` may change (0.9975 → 1.0); every other field must be byte-identical.
- **Corrected outcome:** C3 loss bound satisfied on the real draws and on 400/400 null streams. C1, C2 and C4 are unaffected.
- **Not an error:** the slope constant 0.0010005 ≈ −log(1−ρ) is the conservative form that A4 registers. It is not a mismatch with 6ρ/7.
