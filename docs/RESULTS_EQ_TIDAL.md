# RESULTS — eq.tidal-manila.phase.v1 / eq.tidal-manila.phase.moondist.v1

Phase 5 first equation-discovery run — **calibration target / positive control**.
Registration: `docs/REGISTRATION_EQ_TIDAL.md`, sha256 `9df78eca25e20ab5…`
(verified against `results/commitment_ledger.txt` before execution; approved
pre-fit). Script: `src/eq_tidal_v1.py`. Machine output: `results/eq_tidal_v1.json`
(sha256 `a239f13a2cd1d4db…`). Executed 2026-06-11 by equation-analyst
(execute dispatch); NOT the batch5 detection analyst (independence, rule 2, OK).

All numbers below are traceable to `results/eq_tidal_v1.json`.

## Headline

| Claim | Target | Selected family | Verdict | Calibration (period recovery) |
|---|---|---|---|---|
| A `eq.tidal-manila.phase.v1` | Total tidal accel (g) | A2 (2 freq, K=1) | **FAILED_EQUATION_SEARCH** (+ instrument-miscalibration flag, §11 rule 3 path) | **FAIL** — anomalistic ✓ (27.487 d, 0.25% err), spring–neap ✗ (2nd freq went to 30.64 d) |
| B `eq.tidal-manila.phase.moondist.v1` | Moon Dist (km) | B1 (1 freq, K=1) | **FAILED_EQUATION_SEARCH** (§11 rule 2 path: structured residuals) | **PASS** — anomalistic ✓ (27.604 d, 0.18% err; CI [27.371, 27.846] ∋ 27.555) |

Per hard rule 1 these verdicts do NOT touch the batch5 STRUCTURED detection
verdict. Doob separation: no action license conferred.

## Registered-tolerance check table (§8)

| Claim | Constituent | Ground truth | Tolerance band | Recovered P̂ | Bootstrap 95% CI | In band | CI ∋ truth | Result |
|---|---|---|---|---|---|---|---|---|
| A | anomalistic | 27.555 d | [26.18, 28.93] | 27.487 d | [27.284, 27.728] | YES | YES | PASS |
| A | spring–neap | 14.765 d | [14.03, 15.50] | **not recovered** (2nd freq = 30.638 d, CI [29.932, 31.228]) | — | NO | NO | **FAIL** |
| B | anomalistic | 27.555 d | [26.18, 28.93] | 27.604 d | [27.371, 27.846] | YES | YES | PASS |
| any | P̂ < 4 d (M2 alias guard) | — | auto-FAIL flag | none | — | — | — | clean |

## Fitted equations (train-fitted, original units, coefficients above the floor)

Floors (4·σ̂·√(2/n_train), n_train = 220): A → 6.53e-17 g (σ̂ = 1.71e-16 g);
B → 2.33e+03 km (σ̂ = 6.11e+03 km). All reported amplitudes are above floor.
data_regime: all_rows (single regime per §2.1; era bounds = full file range
2025-06-11..2026-06-11, single era).

**A (Total tidal accel, g):**
ŷ = 7.733e-15 + 8.97e-16·[sin/cos @ P=27.487 d] + 3.69e-16·[sin/cos @ P=30.638 d]
- amp₁ = 8.973e-16 g, boot CI [8.32e-16, 9.77e-16], CV 4.2%
- amp₂ = 3.688e-16 g, boot CI [3.04e-16, 4.45e-16], CV 9.7%
- RMSE_test = 4.35e-16 g. Family scores J_val: A1 29.8, **A2 21.1**, A3 42.1.

**B (Moon Dist, km):**
ŷ = 385295 + 22240·[sin/cos @ P=27.604 d]
- amp = 2.224e+04 km, boot CI [1.94e+04, 2.52e+04], CV 6.4%
- RMSE_test = 4120 km. Family scores J_val: **B1 27.0**, B2 32.7.

(amplitude = √(a²+b²) from the registered sin/cos pairs; full a/b values and
all-coefficient table in the JSON.)

## Null-equation generator + test-vs-null (B = 200 per type per claim)

Null-adjusted p = (1 + #{null test NLL ≤ observed}) / 201; attainable floor 0.00498.

| Claim | Null | p | obs test NLL | null median (min) | beaten at 0.01? |
|---|---|---|---|---|---|
| A | permutation | 0.00498 | 67.1 | 105.1 (91.4) | YES |
| A | AR(1) | 0.00498 | 67.1 | 106.1 (87.2) | YES |
| A | phase-randomized surrogate | **0.209** | 67.1 | 93.2 (−2.0) | **NO** |
| B | permutation | 0.00498 | 0.7 | 106.0 (92.9) | YES |
| B | AR(5) | 0.00498 | 0.7 | 110.2 (5.8) | YES |
| B | phase-randomized surrogate | 0.00498 | 0.7 | 89.9 (0.7) | YES |

Null-equation-generator distributions (full detail in JSON): the identical
grid+refine+J-selection procedure returns an equation on EVERY null series —
on permutation nulls typically a low-amplitude line (recovered-period spread
across the whole 4–120 d window), on A-claim phase surrogates frequently
near-27.5 d lines with competitive test scores (the surrogate preserves the
line spectrum of a quasi-deterministic series). This is exactly the A1
admission requirement working: claim A's fit is NOT distinguishable from its
spectrum-matched surrogate at the registered 0.01 level.

## Residual checks (§7, on train+validation residuals of frozen f*; declared α = 0.05)

| Check | A: stat / p | A pass | B: stat / p | B pass |
|---|---|---|---|---|
| 1 Ljung–Box (40) | p ≈ 0 | FAIL | p ≈ 0 | FAIL |
| 2 Fisher g 4–120 d | peak 14.65 d, p = 8.6e-21 | FAIL | peak 29.30 d, p = 1.9e-11 | FAIL |
| 3 MMD vs Gaussian | p = 0.005 | FAIL | p = 0.005 | FAIL |
| 4 Breusch–Pagan | p = 0.0035 | FAIL | p = 0.0004 | FAIL |
| 5 CUSUM changepoint | p = 0.005 | FAIL | p = 0.294 | PASS |
| 6 TDA H₁ on residual embedding | p = 0.01 | FAIL | p = 0.01 | FAIL |
| 7 Compression (zlib) | p = 0.005 | FAIL | p = 0.005 | FAIL |

Structured residuals on both claims ⇒ demotion per §11 rule 2 / hard rule 6.
Notably the H₁ loop is NOT gone from either residual series — the registered
families do not absorb all of the loop-licensing structure.

## Bootstrap stability (moving-block, block 15 d, B = 500)

| Claim | family re-selected | amp CV | P̂ CIs in band | stable per §9? |
|---|---|---|---|---|
| A | 77.8% (A2) | 4.2% / 9.7% | freq1 yes, freq2 no | **NO** (re-selection < 90%; freq2 CI outside band) |
| B | 99.8% (B1) | 6.4% | yes | YES |

## What was learned (dead-ends logged, per CLAUDE.md — not dismissed)

1. **Period-recovery machinery is well calibrated where identifiable.** Three of
   three recovered base frequencies landed within 0.25% of true lunar
   constituents' family (27.49, 27.60 d vs 27.555 d anomalistic) — far inside
   the ±5% band, beating the Rayleigh limit as predicted in §6 of the
   registration. The grid+NLS+J pipeline finds real periods with tight,
   truthful bootstrap CIs.
2. **Spring–neap miss is a model-capacity finding, not a search bug.** In Total
   tidal accel the second-strongest line is the evection-band inequality
   (true ≈ 31.81 d; recovered 30.64 d, biased low by partial Rayleigh overlap
   with 27.55 d over the 219 d train span), which OUTCOMPETES the 14.77 d
   variation line for the single remaining registered frequency slot. The
   spring–neap energy is demonstrably present — it is the residual Fisher-g
   peak at 14.65 d (p = 8.6e-21). Recovering it would need a 3-frequency
   family, which is NOT in the registered closed list; fitting it now would be
   a quiet extension (forbidden). Correct route: new registration, new m charge.
3. **The declared Gaussian noise model is the wrong null for ephemeris-grade
   deterministic data.** Residual σ is tiny but residuals are themselves
   deterministic harmonics, so every distributional residual check fails by
   construction. For future near-noiseless calibration targets, the
   registration should declare a "remaining-harmonics" residual model or a
   stopping rule on explained variance — to be designed in a NEW registration,
   never patched post hoc.
4. **Phase-randomized surrogates are the binding null for line spectra** (claim
   A p = 0.209). Permutation and AR nulls are easy; surrogates that keep the
   power spectrum keep most of the predictability of a quasi-periodic series.
   Claim B beat even the surrogates (p = 0.005) because a single coherent
   phase-locked line predicts held-out points better than any random-phase
   realization; claim A's two-line model left enough unmodeled spectrum that
   21% of surrogates scored better. This validates the registration's choice
   of the surrogate null as "the stringent null".
5. **Multiplicity**: m_delta = 5 charged as registered (A1, A2, A3, B1, B2);
   orchestrator applies the global ledger correction at verdict time.

### Instrument-miscalibration flag (claim A, §11 rule 3)

A statistically tight fit recovered a wrong/missing constituent under the
registered family cap. The equation layer is NOT to be pointed at open
questions with multi-line spectra until the family-capacity issue (finding 2)
and noise-model issue (finding 3) are addressed in a new registration.
Single-line targets (claim-B-like) calibrated cleanly.

## Reproducibility

- Seed scheme: base 20260611, stage offsets {null_equation_generator 0, fit 1,
  nulls 2, bootstrap 3, residuals 4}, per-replicate SeedSequence spawning
  (claim, null-type, replicate) — in the JSON.
- In-process double run: byte-identical.
- External two-run rule: two full script executions; output files byte-identical
  (`cmp` empty; sha256 `a239f13a2cd1d4dbbc4d08d2d97c15b7f75696990fe38f0d2be1815005a7df69` both runs).

## Declared deviations (all conservative)

1. scipy/ripser not preinstalled at dispatch — installed (same ripser stack as
   batch5); no procedural change.
2. Residual-check α not numerically fixed in the registration → declared 0.05,
   which is STRICTER than the run's 0.01 standard (easier to demote a verdict,
   never easier to pass). Raw p-values reported, so any α can be re-applied;
   at α = 0.01 every FAIL above except claim-A Breusch–Pagan (p = 0.0035…)
   still fails — verdicts unchanged.
3. Series standardized by their own train mean/std inside the discovery
   procedure (identical for real and null series; coefficients reported in
   original units) — numerical-stability measure, affects real and null
   identically.

## Proposed ledger deltas (PROPOSED — not applied; orchestrator to apply)

1. run_ledger `eq_tidal_v1`: status → executed; equation_analyst_id → this
   executor; verifiers → independent-verifier pending; output_sha256
   `a239f13a2cd1d4db`.
2. multiplicity_ledger: `{family_id: "eq.tidal-manila.harmonic", m_delta: 5}`
   (as registered §12).
3. Independent-verifier task: check recovered 27.49/27.60 d against anomalistic
   27.555 d ground truth and re-derive null-adjusted p for claim A surrogates.
