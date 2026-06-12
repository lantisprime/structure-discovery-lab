# RESULTS — eq.tidal-manila.phase.v2 / eq.tidal-manila.phase.moondist.v2

Phase 5 follow-up calibration run (v2). Registration:
`docs/REGISTRATION_EQ_TIDAL_V2.md`, sha256 `4761403580ba138b…` (verified
against `results/commitment_ledger.txt` before execution; approved pre-fit,
2026-06-11). Script: `src/eq_tidal_v2.py`. Machine output:
`results/eq_tidal_v2.json` (sha256 `fdc12e7251b59fec…`). Executed 2026-06-11
by equation-analyst (v2 execute dispatch); NOT the batch5 detection analyst
and NOT the v1 same-claim verifier (independence, rule 2, OK — orchestrator
to record in run_ledger row `eq_tidal_v2`). Seed base 20260612.

All numbers below are traceable to `results/eq_tidal_v2.json`.

## Headline

| Claim | Target | Selected family | Verdict | Calibration (§8) |
|---|---|---|---|---|
| A `eq.tidal-manila.phase.v2` | Total tidal accel (g) | **A2** (2 freq, K=1 — the v1-identical comparator; min-J rejected A4/A5) | **FAILED_EQUATION_SEARCH** (§11.2: surrogate null not beaten + gating residuals fail) | **FAIL** — anomalistic ✓ (27.487 d, 0.25% err), spring–neap ✗ (not in selected model); evection band ✓ attribution-grade (30.638 d ∈ [29.50, 33.40]) |
| B `eq.tidal-manila.phase.moondist.v2` | Moon Dist (km) | B1 (1 freq, K=1) | **FAILED_EQUATION_SEARCH** (§11.2: R1 whitelist + R3 TDA absorption fail) | **PASS** — anomalistic ✓ (27.604 d, 0.18% err; CI [27.360, 27.832] ∋ 27.555) |

**v1 benchmark: NOT beaten.** Claim A phase-randomized-surrogate
null-adjusted p = **0.194** (v1: 0.209). The registered PREDICTIVE gate is
p ≤ 0.01 against each null type; 0.194 fails it. The v2 design hypothesis —
that a 3-line family would separate the fit from its spectrum-matched
surrogates — is **refuted**, and in an unexpected way: the registered min-J
rule never selected the 3-line family at all (see learnings).

Per hard rule 1 these verdicts do NOT touch the batch5 STRUCTURED detection
verdict. Doob separation: no action license conferred. The v1
instrument-miscalibration flag on the equation layer for multi-line targets
**remains in force** (not cleared by this run).

## Registered-tolerance check table (§8)

| Claim | Constituent | Ground truth | Band | Recovered P̂ | Bootstrap 95% CI | In band | CI ∋ truth | CI required | Result |
|---|---|---|---|---|---|---|---|---|---|
| A | anomalistic | 27.555 d | [26.18, 28.93] | 27.487 d | [27.303, 27.685] | YES | YES | YES | PASS |
| A | spring–neap | 14.765 d | [14.03, 15.50] | **not in selected model** (A4 had recovered 14.649 d but lost on J) | — | NO | NO | YES | **FAIL** |
| A | evection (attribution-grade) | 31.812 d | [29.50, 33.40] | 30.638 d (3.69% err) | [30.037, 31.296] | YES | (exempt) | NO | PASS (attribution-grade) |
| B | anomalistic | 27.555 d | [26.18, 28.93] | 27.604 d | [27.360, 27.832] | YES | YES | YES | PASS |
| any | P̂ < 4 d (M2 guard) | — | auto-FAIL | none | — | — | — | — | clean |

Calibration claim A = spring–neap AND anomalistic ⇒ **FAIL**. Claim B ⇒ **PASS**.

## Family scores (J = NLL_val + 2.697·complexity; min-J selection)

| Claim | Family | Complexity | NLL_val | J_val | Test NLL | Recovered periods (d) |
|---|---|---|---|---|---|---|
| A | **A2** (2f, K=1) | 9 | −3.148 | **21.124** | 67.101 | 27.487, 30.638 |
| A | A4 (3f, K=1) | 13 | +5.192 | 40.251 | 65.286 | 27.511, 30.738, **14.649** |
| A | A5 (3f, K=2) | 19 | −2.979 | 48.260 | 61.256 | 27.524, 30.673, 14.579 |
| B | **B1** (1f, K=1) | 5 | 13.535 | **27.019** | 0.665 | 27.604 |
| B | B2 (1f, K=2) | 7 | 13.858 | 32.735 | −1.412 | 27.606 |

A2's fit is byte-equivalent to v1's A2 (same periods/coefficients to machine
precision), as the registration required of the comparator.

## Fitted equations (train-fitted, original units, all coefficients above floor)

Floors (4·σ̂·√(2/n_train), n_train = 220): A → 6.53e-17 g; B → 2.33e+03 km.
data_regime: all_rows (single era, 2025-06-11..2026-06-11).

**A:** ŷ = 7.733e-15 + 8.97e-16·[sin/cos @ 27.487 d] + 3.69e-16·[sin/cos @ 30.638 d]
(amp CIs [8.25e-16, 9.71e-16] CV 4.4%; [3.03e-16, 4.47e-16] CV 10.1%; RMSE_test 4.35e-16 g)

**B:** ŷ = 385295 + 22237·[sin/cos @ 27.604 d]
(amp CI [1.93e+04, 2.51e+04] km, CV 6.6%; RMSE_test 4120 km)

## Null comparisons (B = 200 per type per claim; gate p ≤ 0.01 each; floor 0.00498)

| Claim | Null | null_adjusted_p | obs test NLL | null median (min) | beaten? |
|---|---|---|---|---|---|
| A | permutation | 0.00498 | 67.10 | 106.47 (91.82) | YES |
| A | AR(1) | 0.00498 | 67.10 | 106.48 (85.15) | YES |
| A | phase-randomized surrogate | **0.19403** | 67.10 | 98.80 (12.14) | **NO** |
| B | permutation | 0.00498 | 0.665 | 105.23 (92.11) | YES |
| B | AR(5) | 0.00498 | 0.665 | 115.32 (25.63) | YES |
| B | phase-randomized surrogate | 0.00995 | 0.665 | 85.30 (−3.26) | YES |

Null-equation-generator summary: the identical grid+deflation+refine+J
procedure returns an equation on every null series. On claim-A surrogates the
expanded menu is exercised: A2 selected 165/200, A4 32/200, A5 3/200 — i.e.
spectrum-matched surrogates also occasionally license 3-frequency fits,
confirming the surrogate as the binding null. Permutation/AR nulls: A2 (or
B1) selected 200/200 with period spread across the whole 4–120 d window.
Full distributions in the JSON.

## §7 residual checks (train+validation residuals of frozen f*; gating α = 0.01)

| Check | A | A pass | B | B pass |
|---|---|---|---|---|
| R1 whitelist attribution (gating) | 7 significant peaks; 6 attributed (14.65 variation, 13.95+13.32-type anomalistic-2nd, 15.42 variation, 29.30+32.56 evection/synodic side, 26.64 synodic); **36.625 d unattributed** (p = 3.8e-3) | **FAIL** | 20 significant peaks (iteration cap); 7 attributed; **unattributed: 24.42, 36.63, 41.86, 22.54, 48.83, 58.6, 73.25, 20.93, 97.67, 19.53, 18.31, 16.28, 17.24 d** | **FAIL** |
| R2 CUSUM changepoint (gating) | stat 4.785, p = 0.00498 | **FAIL** | stat 0.930, p = 0.378 | PASS |
| R3 TDA H₁ absorption < 0.562 (gating) | residual persistence 0.628 (absorption 44.1%) | **FAIL** | residual persistence 0.886 (absorption 21.2%) | **FAIL** |
| R4 compression (gating A only) | p = 0.00995 | **FAIL** | p = 0.00498 (diagnostic) | (n/a) |
| Ljung–Box (non-gating diag) | p ≈ 0 | — | p ≈ 0 | — |
| MMD vs Gaussian (non-gating diag) | p = 0.0746 | — | p = 0.0199 | — |
| Breusch–Pagan (non-gating diag) | p = 0.0035 | — | p = 0.0004 | — |

The §7 redesign worked as designed in one direction: the *dominant* residual
peaks ARE the pre-declared whitelist lines (claim A top peak 14.65 d,
p = 8.6e-21 = variation; then anomalistic 2nd harmonic). It failed in the
other: both claims carry significant lines OUTSIDE the declared whitelist —
exactly the unexplained structure R1 exists to catch ⇒ FAILED_EQUATION_SEARCH,
not a quiet extension.

## Bootstrap stability (moving-block, block 15 d, B = 500)

| Claim | family re-selected | amp CV | PASS-defining P̂ CIs in band | stable per §9? |
|---|---|---|---|---|
| A | 95.4% (A2) | 4.4% / 10.1% | yes (anomalistic; evection CI-exempt) | YES (v1: NO at 77.8%) |
| B | 99.0% (B1) | 6.6% | yes | YES |

## v1 vs v2 comparison

| Metric | v1 | v2 | Better? |
|---|---|---|---|
| A selected family | A2 of {A1,A2,A3} | A2 of {A2,A4,A5} | same model |
| A surrogate null p | 0.209 | 0.194 | marginal, NOT ≤ 0.01 — benchmark not beaten |
| A spring–neap recovery | absent (capacity) | present in A4 (14.649 d) but J-rejected | diagnosis sharpened |
| A bootstrap re-selection | 77.8% (unstable) | 95.4% (stable) | yes |
| B anomalistic | 27.604 d, 0.18%, calib PASS | 27.604 d, 0.18%, calib PASS | reproduced |
| B surrogate p | 0.00498 | 0.00995 | still ≤ 0.01 (new seeds) |
| B residual adjudication | Gaussian gates (category error) | whitelist R1: FAIL on un-whitelisted lines | honest fail replaces vacuous fail |

## What was learned (dead-ends logged, per CLAUDE.md — not dismissed)

1. **v1 finding 2 ("model capacity") is refuted as the binding constraint.**
   Given the capacity, A4 DID find spring–neap on train (14.649 d, 0.79% from
   truth, inside the band) — but its *validation* NLL (+5.19) is WORSE than
   A2's (−3.15), so J rejects it by 19.1 points and the test set was never
   consulted. The 14.77 d line is real but its train-estimated
   amplitude/phase does not generalize across the chronological split under
   a pure 3-sinusoid form. The binding constraint is the *form* (missing
   synodic/2nd-harmonic structure distorting the small line), not the
   frequency count. A5's overtones did not fix it either (J = 48.26).
2. **The surrogate-null failure of claim A is robust, not a capacity
   artifact** (p = 0.194 vs 0.209 across independent seed bases and a
   different family menu). A two-line model of a multi-line deterministic
   spectrum is simply not distinguishable from its own spectrum-matched
   surrogates at held-out phase coherence — 19% of surrogates score better.
3. **The whitelist residual model is the right instrument and it returned a
   real discovery-grade signal:** both targets contain significant residual
   lines outside {evection, variation, anomalistic-2nd, synodic} — shared
   unattributed peak near 36.6 d and, in Moon Dist, a ladder (24.4, 41.9,
   48.8, 58.6, 73.3, 97.7 d…). Caveat declared: T_trainval = 292 d puts the
   Fourier grid (293/k d) very coarse in the 30–100 d range, so some of these
   ordinates are plausibly leakage/merge artifacts of imperfectly removed
   known lines rather than new constituents; the registered single-ordinate
   deletion cannot distinguish these at this n. A v3 wanting claim B to pass
   must either model more known inequalities explicitly or declare a
   leakage-aware attribution rule — registered in advance, with new m charge.
4. **TDA absorption gate calibrates the "loop absorbed?" question:** A2
   absorbs 44.1% of the batch5 loop persistence (0.628/1.124, just under the
   declared 50% gate); B1 absorbs only 21.2% (0.886). The H₁ loop in the
   delay embedding is licensed mostly by the *multi-line* structure, not by
   the single dominant line — consistent with learning 3.
5. **v1's claim-A bootstrap instability was menu composition, not data:**
   with {A2,A4,A5} the re-selection fraction jumps 77.8% → 95.4% on the same
   data. Family-stability numbers are only interpretable relative to the
   registered menu.
6. **Multiplicity:** m_delta = 3 charged as registered (A4, A5, claim-B
   re-adjudication); A2 re-fit uncharged (deterministic repeat). Cumulative
   family charge eq.tidal-manila.harmonic: 5 + 3 = 8 — orchestrator applies
   at verdict time.

## Reproducibility

- Seed scheme: base 20260612, stage offsets {null_equation_generator 0,
  fit 1, nulls 2, bootstrap 3, residuals 4}, per-replicate SeedSequence
  spawning (claim, null-type, replicate) — in the JSON.
- Two-run rule: TWO SEPARATE full process executions
  (`results/_eq_tidal_v2_run1.json`, `results/_eq_tidal_v2_run2.json`);
  `cmp` empty — byte-identical. `two_run_diff` field records this. Final
  sha256 `fdc12e7251b59fecf33a9301879cb8e5b735673074f79468e1ecb7596bb1a625`.

## Declared deviations (all conservative)

1. **Staged execution:** sandbox enforces 45 s/call and reaps background
   processes, so the script gained `--single`/`--finalize` CLI modes; the
   pipeline itself is unchanged and each run is one process start-to-finish.
   Two-run comparison across separate processes is stronger isolation than
   v1's in-process double run (which remains the script's default mode).
2. **R1 merge attribution applied to claim A only** — the stricter of the two
   registration readings (§7.2 whitelist parenthetical vs attribution-rule
   example); declared pre-execution in `results/eq_tidal_v2_CHECKPOINT.md`.
   Outcome-invariant: every unattributed peak lies outside any merge zone in
   both claims.
3. Merge-zone width implemented as ΔP₁+ΔP₂ (ΔPᵢ = Pᵢ²/T); the two relevant
   whitelist pairs merge under either reading — outcome-invariant.
4. Iterative Fisher-g: max-ordinate deletion per detected peak, stop at
   p ≥ 0.01, cap 20 iterations (declared pre-execution). Claim B hit the cap
   with peaks still significant — can only ADD unattributed peaks, never
   remove them (conservative); R1 had already failed.

## Proposed ledger deltas (PROPOSED — not applied; orchestrator to apply)

1. run_ledger `eq_tidal_v2`: status → executed; equation_analyst_id → v2
   execute dispatch (≠ batch5 analyst, ≠ v1 verifier); output_sha256
   `fdc12e7251b59fec`; verifiers → independent-verifier pending.
2. multiplicity_ledger: `{family_id: "eq.tidal-manila.harmonic", m_delta: 3}`
   (as registered §10/§12).
3. Independent-verifier task: re-derive claim A surrogate p (0.194) and the
   claim-B R1 unattributed-peak list; check 27.487/27.604 d vs anomalistic
   27.555 d; check A2 byte-equivalence to v1.
