# RESULTS — eq.tidal-manila.phase.moondist.confirm1 (fresh-data confirmation)

Registration: `docs/REGISTRATION_EQ_MOONDIST_CONFIRM.md`, sha256
`9b0626c12f6f273b62c6905a8b93481aa6e690854e1e06d94743189abf05ea06` (verified
against `results/commitment_ledger.txt`; APPROVED 2026-06-12 **pre-fetch**;
amendments honored: fetch-now approved, MECHANISM_SUPPORTED ceiling stands).
Script: `src/eq_moondist_confirm1.py`. Machine output:
`results/eq_moondist_confirm1.json` (sha256 `7c36abea9fae21ec…`). Raw fetch
(orchestrator data path, committed pre-parse):
`results/eq_confirm1_raw_horizons.txt`, sha256
`4724920d212aa85fadb6c391d89d813048616aa379eef07159bab4ad2585dc30` — matches
the commitment-ledger line. Executed 2026-06-12 by equation-analyst
(confirm1 scoring dispatch; ≠ batch5 analyst, ≠ v2 executor). Seed base
20260614 (scoring deterministic; no resampling drawn).

## Headline

# VERDICT: **MECHANISM_SUPPORTED** — the lab's first.

The frozen v2 B1 equation (registered and hashed before the fresh data
existed) forecast 86 strictly-post-freeze JPL Horizons Moon-distance rows
(2026-06-12..2026-09-05, t = 366..451, **no re-anchoring, no refit, zero free
parameters**) inside every registered gate.

## Gate table (§5, thresholds fixed pre-fetch)

| Gate | Threshold | Observed | Margin | Pass |
|---|---|---|---|---|
| **C1** RMSE_fresh ≤ 1.5 × 4119.801539200268 km | ≤ 6179.702309 km | **5243.525413 km** | +936.18 km | **PASS** |
| **C2** max\|r\| ≤ 3 × 4119.801539200268 km | ≤ 12359.404618 km | **9729.031155 km** (at 2026-09-05, the far edge) | +2630.37 km | **PASS** |
| **C3** completeness | 86 residuals, none NaN | 86, none NaN | — | **PASS** |

RMSE ratio vs the v2 test benchmark: **1.273×** — comfortably inside the
declared 1.5× envelope whose rationale (period-error phase drift ≈ 4.1e3 km in
quadrature with ≈ 4.1e3 km unmodeled inequalities) is borne out by the
residual trace: |r| drifts +33.0 km/d and peaks on the last day, exactly the
declared accumulation pattern.

## §3.2 protocol guards (all enforced pre-scoring)

| Guard | Result |
|---|---|
| Raw sha256 = committed pre-parse hash | PASS (`4724920d…dc30`) |
| Exactly 86 rows, every day 2026-06-12..2026-09-05 | PASS |
| Ephemeris DE441 (`Target: Moon (301) {source: DE441}`) | PASS |
| delta in AU; `1 au = 149597870.700 km`; conversion at 0.1 km precision | PASS |
| CENTER `coord@399`, SITE 121.0359,14.5794,0.02, STEP 1 d, Q=20 | PASS (raw header) |
| 13:00 UT stamps | PASS with **declared deviation** (below) |

**Declared deviation (pre-scoring, checkpoint adjudication 3):** fresh stamps
display minute precision ("13:00") vs the original raw's FRACSEC display
("13:00:02.880"); the request convention (13:00 UT daily) is identical, but
the .880 instant is not literally verifiable from the fresh file. Worst-case
sampling-instant offset 2.88 s bounds the value impact at ≈ 1.4 km
(max |deldot| ≈ 0.48 km/s). The declared tripwire — escalate with no verdict
if any gate margin < 2 km — did **not** trip (margins 936 km and 2630 km);
the deviation is outcome-invariant as declared.

## Freeze verification (§2, pre-scoring)

B1 re-derived via the v2 registered fit path: **byte-equal** to
`results/eq_tidal_v2.json` AND to the registration §2 constants
(a0 = 385294.7950098205, a = −19039.87882118035, b = 11488.61399772309,
P = 27.60387627151598, t = days since 2025-06-11). Fresh rows were NOT
appended to any dataset file (§3.2 guard 4); `tidal_derived.csv` untouched.

## Non-gating diagnostics (§5; n = 86, too short to gate — reported for continuity)

- Residual mean −773.3 km; trend +18.28 km/d; |r| drift +33.05 km/d.
- Fisher-g top fresh-residual peaks: **28.67 d** (p = 2.3e-11), **14.33 d**
  (p = 1.9e-9), 43.0 d (p = 1.7e-4), then 86 d (p = 0.14), 21.5 d (p = 0.054).
  The dominant fresh residual lines sit at the synodic/evection and
  variation regions — the SAME known unmodeled inequalities v2's R1
  adjudicated, and consistent with v3's collapsed 30.8 d / 14.7 d complexes.
  Continuity with v2 learning 3 confirmed out-of-sample.

## Verdict reasoning (§6.1, as registered)

C1 ∧ C2 ∧ C3 → **MECHANISM_SUPPORTED** for
`eq.tidal-manila.phase.moondist.confirm1`. The mechanism is externally known
physics (lunar anomalistic cycle, 27.555 d); fresh-data confirmation per the
§7 ladder is satisfied by this test on post-registration data.

**Scope carve-out (approved):** this verdict attaches to frozen B1 **as a
forecast-grade description of the dominant anomalistic line with declared
error envelope ≤ 6.2e3 km RMSE**. It does NOT overturn, soften, or relabel
`eq.tidal-manila.phase.moondist.v2`'s FAILED_EQUATION_SEARCH (residual
completeness, R1/R3 — reaffirmed today by eq_tidal_v3 on the same residuals).
Both verdicts stand simultaneously on their own claim ids.
GOVERNING_LAW_CONFIRMED is out of scope per the approved registration (no
intervention possible; B1 is a one-line truncation; the data are themselves a
DE441 integration). Equivalence-class note honored: no new detection claim,
no new kb claim about sun_moon_daily. Hard rule 1: batch5 verdict untouched.
Doob separation: no action license; Phase 6 decides downstream.

## Reproducibility

Two-run rule: two separate parse+score executions from the SAME committed raw
file (`results/_eq_moondist_confirm1_run{1,2}.json`); `cmp` empty —
**byte-identical**. Final sha256
`7c36abea9fae21ecaa3b42dbd078512abca3905a4078c1e26ac6f5978ddf9c0d`.
Full 86-row residual trace embedded in the JSON.

## Proposed ledger deltas (PROPOSED — not applied; orchestrator to apply)

1. run_ledger `eq_moondist_confirm1`: status → executed; output sha256
   `7c36abea9fae21ec`; fetch by orchestrator data path; raw sha256 as above.
2. multiplicity_ledger: `{family_id: "eq.tidal-manila.harmonic", m_delta: 1,
   reason: "fresh-data confirmation attempt of frozen v2 B1 (verdict-ladder
   promotion test)"}` — cumulative family charge 10 (with v3's +1).
3. kb/verdict ledger: `eq.tidal-manila.phase.moondist.confirm1` →
   MECHANISM_SUPPORTED (scope carve-out text above travels with the claim);
   `public_claim_allowed` flips per orchestrator policy now that
   confirmation exists — human call, not made here.
4. Independent-verifier task: re-score the 86 rows from the committed raw
   file against the §2 constants; verify C1/C2 numbers and the 1.273× ratio.
5. Post-verdict only, per §3.2 guard 4: fresh rows MAY now be appended to
   `sun_moon_daily.csv`/`tidal_derived.csv` under a new dataset version if
   the lab wants them — separate decision, not performed here.
