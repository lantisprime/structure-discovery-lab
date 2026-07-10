# Verification — PCSO weekly monitoring 2026-07-08

Closeout date: 2026-07-10

## Scope and identity

Executor: Codex closeout session that also authored
`src/pcso_weekly_update.py`. These checks are mechanical same-session
verification, **not** the independent executor required for an evidence-grade
upgrade. The run remains G0 exploratory forward monitoring.

Independent re-execution supplied by the lab owner:

- Executor/provider: OpenAI Codex
- Model: GPT-5-based Codex
- Session or run ID: not exposed to the executor
- Verification date: 2026-07-10 (Asia/Manila, UTC+08:00)
- Reported result: PASS; exit 0, expected SHA-256 matched, byte comparison
  identical, initial/final repository status identical, flags = 0

This establishes a separate-executor numeric reproduction on the supplied
identity attestation. It does not satisfy the stronger cross-model rule because
the authoring and verification executors are both GPT-5-based Codex. The run
therefore remains G0 and the cross-model check remains pending.

## Checks

- PASS — provenance manifest contains 28 unique, in-pool, two-source-marked
  draw records spanning 2026-06-25 through 2026-07-07.
- PASS — manifest values match `data_draws.csv`, `data_draws_1yr.csv`, and
  `data_draws_1yr_audited.csv`; all three contain the same 58 confirmation rows.
- PASS — audited source/status fields match the manifest for all 28 new rows.
- PASS — frozen prefixes through 2026-06-10 match the registered SHA-256
  values for all four CSVs.
- PASS — every line in all four append-only CSVs retains CRLF endings.
- PASS — all 58 confirmation draws join one-to-one to the astro file and the
  stored normalized means match the drawn numbers.
- PASS — Kp fields are blank for all confirmation rows; the Kp test is
  correctly reported as non-computable.
- PASS — workbook has the expected 8 sheets, 786 formulas, 252 draw rows,
  and zero cached-value error cells.
- PASS — two separate runner processes produced byte-identical JSON at
  SHA-256 `11c8af729f0353a83f130253100dadb5fb3413d49cceec11fa031d64daf054a4`.
- PASS — eight computable tests are unflagged at the within-look threshold
  `0.05/9 = 0.005555...`; the minimum p-value is `0.020098`.

## Limitations

- Raw source HTML and exact per-date URLs were not retained by the original
  July 8 execution. The retrospective manifest preserves the contemporaneous
  audit claim but does not independently re-establish it.
- No sequential alpha-spending rule is registered across cumulative weekly
  looks. This artifact cannot be used as confirmatory evidence by itself.
- Separate-executor reproduction passed, but the executor did not expose a run
  ID and used the same model family as the authoring session. A different-model
  executor is still required before any grade above G0 is considered.
