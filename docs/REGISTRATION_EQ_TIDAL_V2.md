# REGISTRATION — eq.tidal-manila.phase.v2

**STATUS: APPROVED 2026-06-11 (Cha, lab owner — §13). Committed pre-fit; the
commitment-ledger line is the binding hash.**

No fit has been run. No data values have been inspected in this dispatch
beyond what `docs/RESULTS_EQ_TIDAL.md` already publishes. This registration
must be human-approved and commitment-hashed into
`results/commitment_ledger.txt` BEFORE any fitting (EQUATION_DISCOVERY.md §6;
equation-analyst hard rule 3).

Drafted: 2026-06-11 by equation-analyst (Fable, design-only dispatch).
Pipeline position: Phase 5 follow-up calibration run. This is a **NEW
registration with a fresh multiplicity charge** (§10) — explicitly NOT a
quiet extension of `eq.tidal-manila.phase.v1` (hard rule 6 / v1 §11 rule 2:
structured residuals demand a new registration, never a patched model).

## 0. Relationship to v1 (what this registration fixes)

v1 (`docs/REGISTRATION_EQ_TIDAL.md`, executed; results in
`docs/RESULTS_EQ_TIDAL.md`) returned FAILED_EQUATION_SEARCH on both claims
and logged two pre-registered learnings. v2 fixes exactly those two, and
nothing else:

1. **v1 finding 2 (claim A, model capacity):** the registered 2-frequency cap
   forced the evection-band line (recovered 30.64 d) and the spring–neap /
   variation line (residual Fisher-g peak 14.65 d, p = 8.6e-21) to compete
   for one slot. → v2 expands claim A's family to **3 free frequencies**
   (§3, justified in §2.3).
2. **v1 finding 3 (claim B, noise model):** the declared Gaussian residual
   model is the wrong null for deterministic ephemeris-derived data; every
   distributional residual check failed by construction even though period
   recovery PASSED (27.604 d, 0.18% error, CI ∋ truth). → v2 declares a
   **deterministic-remainder residual model** with a known-inequality
   whitelist acceptance criterion (§7), replacing the category-error Gaussian
   gates. Held-out and null criteria are NOT loosened (§5 unchanged from v1).

Everything not listed in §0 is carried over from v1 unchanged: source-claim
gate, data file and regimes, splits, B values, λ rule, detectability floor,
bootstrap scheme, M2 guard, verdict rules including the §11.3
miscalibration clause, Doob separation, two-run reproducibility.

**Benchmark carried forward:** v1 claim A failed the phase-randomized
surrogate null at p = 0.209. That number stands as the benchmark; v2 claim A
must beat the surrogate null at the registered p ≤ 0.01 to reach
PREDICTIVE_EQUATION — there is no fallback gate.

---

## 1. Source claim and gate check (§2 eligibility — unchanged from v1)

| Field | Value |
|---|---|
| source_structure_claim | tidal-manila, TDA H₁ delay-embedding loop (`tidal-manila.tda-h1-delay-embed.batch5`) |
| structure_verdict | STRUCTURED (persistence 1.124 vs matched-null 0.427, p = 0.01) |
| Attribution on file | yes — H₁ loop in the delay-embedded derived tidal series |
| Eligibility | EQUATION_DISCOVERY.md §2 row 1 (calibration target) |
| Independence (rule 2) | executing analyst must NOT be the batch5 detection analyst AND must not be the v1 execution analyst's same-claim verifier conflict; `equation_analyst_id != detection_analyst_id` recorded in run_ledger before execution |

Gate verdict if any of the above fails at execution time: `NO_EQUATION_ATTEMPTED`.

### Calibration framing (positive control, updated)

Data are ephemeris-derived; the governing rule is externally known. At daily
sampling, M2 (12.42 h) is beyond Nyquist and not recoverable. Declared
recoverable constituents for this run:

- **spring–neap / variation ≈ 14.765 d** — now expected to be CAPTURABLE
  (v1 published residual evidence: Fisher-g peak at 14.65 d, p = 8.6e-21,
  inside the ±5% band [14.03, 15.50]); v1's miss is attributed to family
  capacity, not absence of the line.
- **anomalistic month ≈ 27.555 d** — recovered in v1 at 0.18–0.25% error.
- **evection band ≈ 31.812 d** — newly declared (v1's second line, 30.64 d,
  biased low by partial Rayleigh overlap with 27.555 d over the ~219 d train
  span). Attribution-grade target only; see §8 for its weaker tolerance and
  the justification.

The v1 interpretation caveat stands: `Total tidal accel (g)` is a scalar sum
ignoring the sun–moon angle; any 14.77 d line is attributed to the lunar
distance "variation" inequality propagated through C/d³, not to axis
alignment.

---

## 2. Data (unchanged from v1)

| Field | Value |
|---|---|
| File | `datasets/tidal-manila/tidal_derived.csv` |
| Sampling / rows | daily; n = 366, 2025-06-11 .. 2026-06-11 (verified in v1) |
| Provenance | DERIVED from JPL Horizons distances via C/d³ (DATASET.md) |

### 2.1 data_regimes

`data_regimes: [all_rows]` — same justification as v1 §2.1 (deterministically
computed series; no suspicious rows; collapse is a declared, human-approvable
choice). Era bounds = full file range, single era.

### 2.2 Target columns (two claims, same targets as v1)

| Claim | id | Target |
|---|---|---|
| A | `eq.tidal-manila.phase.v2` | `Total tidal accel (g)` |
| B | `eq.tidal-manila.phase.moondist.v2` | `Moon Dist (km)` |

### 2.3 Justification of the 3-frequency cap (claim A) — and why not 4

The cap is set by v1's published residual evidence, line by line:

| # | Line | Evidence from v1 (published) |
|---|---|---|
| 1 | anomalistic ≈ 27.555 d | recovered 27.487 d, 0.25% err, CI ∋ truth |
| 2 | evection band ≈ 31.81 d | recovered 30.638 d as v1's second line (CI [29.93, 31.23]) |
| 3 | spring–neap/variation ≈ 14.765 d | residual Fisher-g peak 14.65 d, p = 8.6e-21 |

Exactly three lines have direct evidence. No fourth line has published
evidence at this n (v1's residual scan reports no further peak claim); adding
a fourth free frequency would be capacity not licensed by evidence — the M1
overfitting direction. HARD CAP: 3 free base frequencies. If v2 residuals
again show a strong unmodeled line, the correct route is a v3 registration
with a new m charge, never a quiet extension.

---

## 3. Registration contract (EQUATION_DISCOVERY.md §6 YAML)

```yaml
equation_claim_id: eq.tidal-manila.phase.v2        # claim A; claim B suffix .moondist.v2
source_structure_claim: tidal-manila.tda-h1-delay-embed.batch5
structure_verdict: STRUCTURED
equation_type: latent_phase_harmonic               # §4.4 canonical form via §4.8 loop license
candidate_family:                                  # declared BEFORE fitting; closed list
  # --- claim A: Total tidal accel (g) ---
  - A2_harmonic_2freq_k1   # IDENTICAL to v1's A2 (baseline comparator; already
                           # charged in v1; deterministic re-fit — see §10)
  - A4_harmonic_3freq_k1   # a0 + Σ_{i=1..3} [aᵢsin(ωᵢt)+bᵢcos(ωᵢt)]; three free ω  (NEW)
  - A5_harmonic_3freq_k2   # as A4 plus first overtone (2ωᵢ) sin/cos pair per base
                           # frequency; K=2 per base, HARD CAP. Rationale: the
                           # anomalistic 2nd harmonic (≈13.78 d) is exactly 2ω₁;
                           # K=2 lets the data express it without a 4th free ω  (NEW)
  # --- claim B: Moon Dist (km) ---
  - B1_harmonic_1freq_k1   # IDENTICAL to v1 (re-adjudicated under §7 residual model)
  - B2_harmonic_1freq_k2   # IDENTICAL to v1
  # NO free phase parameters anywhere: per-harmonic sin/cos pairs only
inputs: [t]                                        # days since first row; no lagged values
target: ["Total tidal accel (g)", "Moon Dist (km)"]
fit_split:                                         # chronological, unchanged from v1
  train: first_60pct
  validation: next_20pct
  test: final_20pct
null_baseline: [permutation, phase_randomized_surrogate, AR_null]
B_nulls: 200                                       # per type per claim; seeded (unchanged)
null_equation_generator: >
  IDENTICAL discovery procedure (grid + refine, all v2 declared families,
  J-minimization, identical splits) on B=200 matched synthetic nulls per type
  per claim; full distribution of recovered frequencies, complexities, J/test
  scores recorded. Null-adjusted p = (1 + #{null <= observed}) / (B + 1).
selection_rule: min_J_subject_to_heldout_skill
metrics: [RMSE, heldout_loglik, residual_line_attribution, parameter_stability,
          null_adjusted_p, period_recovery_error]
data_regimes: [all_rows]
multiplicity_charge: {family_id: eq.tidal-manila.harmonic, m_delta: 3}   # §10
public_claim_allowed: false_until_confirmed
```

---

## 4. Fitting procedure (registered; execute-only at Haiku tier)

Identical to v1 §4 except family complexities, which follow from the same
declared complexity measure:

- ω estimation on train ONLY: coarse periodogram grid over 4–120 d
  (Rayleigh/4 step), then NLS refinement with linear coefficients profiled
  out. For 3-frequency families, frequencies are initialized from the top-3
  non-adjacent grid peaks (deflation order declared: fit, subtract, rescan —
  on train only) before joint NLS refinement. No spectral statistic touches
  validation or test before selection freeze.
- complexity(f) = (# free linear coefficients) + 2 × (# free frequencies):
  **A2 = 9, A4 = 13, A5 = 19, B1 = 5, B2 = 7.**
- λ = ln(n_train)/2 ≈ 2.7 (BIC-rate), fixed NOW (M1 guard, unchanged).
- J(f) = NLL_validation(f) + λ·complexity(f); select f* = argmin J per claim.
- Freeze f*; single test evaluation; nulls (§5); residual checks (§7);
  bootstrap (§9) on train+validation.
- Two-run reproducibility: seeded re-run by a second execute-only instance;
  diff empty to machine precision. **New seed base for v2: 20260612** (stage
  offsets as in v1's scheme; distinct from v1's 20260611 so no stream reuse).

Note on the NLL scale: NLL is computed under a working Gaussian likelihood
for FITTING and null comparison only (a standard quasi-likelihood device,
identical for real and null series). The Gaussian model is explicitly NOT
the declared residual model for acceptance — that is §7.

---

## 5. Null baselines and null-equation generator (UNCHANGED — not loosened)

Identical to v1 §5: permutation, phase-randomized surrogate, AR(p≤5 by AIC)
nulls; B = 200 per type per claim, matched to train marginal mean/variance
and length; full null-equation-generator distributions recorded.

**Acceptance threshold (unchanged):** null-adjusted p ≤ 0.01 against EACH of
the three null types (floor 1/201 ≈ 0.005). v1 established the surrogate as
the binding null (claim A p = 0.209; claim B p = 0.005). The design
hypothesis under test in v2: a 3-line model leaves little unmodeled spectrum,
so phase coherence on held-out rows should now separate the fit from its
spectrum-matched surrogates. If it does not, claim A FAILS again — that is
the experiment.

## 6. Detectability floor (unchanged rule)

Amplitude floor 4·σ̂·√(2/n_train); no harmonic reported below floor
regardless of J (hard rule 5). Rayleigh-limit context per v1 §6; note the
declared caveat that the 27.555/31.812 d pair sits ~1.6 Rayleigh widths
apart over the train span — partial overlap is expected and handled by the
§8 tolerance design, not by post-hoc tuning.

---

## 7. Residual model and checks (REDESIGNED — the v1 finding-3 fix)

### 7.1 Declared residual model

**Deterministic-remainder model:** the data are noiseless ephemeris-derived
values; after removing the registered harmonics, residuals are expected to
be *the remaining known lunar/solar inequality lines*, not stochastic noise.
v1 proved that Gaussian distributional gates (Ljung–Box, MMD-vs-Gaussian,
Breusch–Pagan) fail by construction on such data — they test a null nobody
holds. They are demoted to reported diagnostics (computed, published,
non-gating).

Why not an AR(p) residual process (the considered alternative): a noiseless
sinusoid satisfies an EXACT AR(2) recurrence, so AR-whitening absorbs any
residual line and the downstream checks pass vacuously — it would loosen the
test while appearing to fix it. The whitelist criterion below is strictly
more falsifiable: it names in advance which residual structure is acceptable
and rejects everything else.

### 7.2 Gating residual checks (declared α = 0.01, matching the run standard)

On r_t = x_t − x̂_t over train+validation (test residuals reported, not used
for selection):

1. **R1 — Known-inequality whitelist attribution.** Fisher-g scan of the
   residual periodogram over the declared 4–120 d window. EVERY peak
   significant at p < 0.01 must be attributable to the pre-declared
   whitelist of known unmodeled lunar inequalities:
   - evection 31.812 d, variation 14.765 d, anomalistic 2nd harmonic
     13.777 d, synodic month 29.531 d (and, for claim A only, their
     pairwise Rayleigh merges).
   - Attribution rule (declared): a peak is attributed if it lies within
     one Rayleigh bandwidth (ΔP = P²/T_trainval) of a whitelist period, OR
     between two whitelist periods separated by < 2 Rayleigh bandwidths
     (the merge case — e.g., v1's 29.30 d claim-B peak between 27.555-line
     harmonic content and 31.812 d).
   - ANY significant peak NOT attributable → R1 FAIL (unexplained structure;
     the residual null this check exists to catch).
2. **R2 — Changepoint scan** (card 4): deterministic remainder has no
   changepoints; gate retained unchanged from v1 (claim B passed it in v1).
3. **R3 — Structure-absorption check (TDA H₁, redesigned target).** H₁ on
   the residual delay-embedding. Gate: residual H₁ persistence < 0.562
   (= 50% of the batch5 detected-loop persistence 1.124, threshold declared
   now). Rationale: the equation must absorb the DOMINANT loop-licensing
   structure; demanding the loop be utterly gone is unattainable while
   declared-acceptable whitelist lines remain (they are themselves
   periodic), but a residual loop as strong as the original means the
   equation absorbed nothing.
4. **R4 — Compression/entropy check (card 10): reported, gating only for
   claim A** (whose verdict goal is PREDICTIVE_EQUATION on a multi-line
   target); diagnostic-only for claim B, same rationale as R3 — declared
   deterministic remainder is compressible by construction.

Reported, non-gating diagnostics: Ljung–Box (1–40), MMD vs Gaussian,
Breusch–Pagan — published with raw p-values so any reviewer can re-gate.

Structured residuals outside this declared acceptance ⇒ FAILED_EQUATION_SEARCH
or a NEW (v3) registration with a new m charge — never a quiet extension.

## 8. Pre-declared period-recovery tolerances (calibration PASS condition)

| Claim | Constituent | Ground truth | Declared tolerance | CI ∋ truth required? |
|---|---|---|---|---|
| A | spring–neap / variation | 14.765 d | P̂ ∈ [14.03, 15.50] (±5%, as v1) | YES |
| A | anomalistic month | 27.555 d | P̂ ∈ [26.18, 28.93] (±5%, as v1) | YES |
| A | evection band | 31.812 d | P̂ ∈ [29.50, 33.40] (≈ −7.3%/+5%) | NO (attribution-grade) |
| B | anomalistic month | 27.555 d | P̂ ∈ [26.18, 28.93] (±5%, as v1) | YES |

±5% retained from v1 for the two PASS-defining constituents (v1 demonstrated
0.18–0.25% recovery where identifiable — the band is generous but unchanged;
tightening post-hoc to flatter v1 performance would be tuning). The evection
tolerance is asymmetric and CI-exempt by design: v1 published a low-biased
recovery (30.638 d, CI [29.93, 31.23] excluding truth) with the bias
mechanism identified (partial Rayleigh overlap with 27.555 d over ~219 d
train). At this n the evection frequency is not fully identifiable; gating
calibration PASS on it would make the verdict hinge on a parameter the data
cannot resolve. It is therefore required only to land in the declared band.
Calibration PASS for claim A = spring–neap AND anomalistic both within
tolerance with CI ∋ truth.

**M2 guard (unchanged):** any reported constituent with P̂ < 4 d is an
automatic calibration FAIL flag.

## 9. Bootstrap scheme (unchanged from v1)

Moving-block bootstrap on train+validation residuals added back to the
fitted curve; block length 15 d, B_boot = 500, seeded. Stability: 95% CI of
each gated P̂ within its §8 band; amplitude CV < 20%; identical family
re-selected in ≥ 90% of replicates (v1 claim A failed this at 77.8% — the
criterion is NOT loosened). Declared caveat (carried, not changed): block
resampling of deterministic residuals scrambles whitelist-line phase across
blocks; this inflates, never deflates, parameter spread — conservative.

## 10. Multiplicity charge (declared honestly vs v1's m_delta = 5)

`{family_id: eq.tidal-manila.harmonic, m_delta: 3}`

Equivalence-class reasoning, item by item:

| Item | Charge | Reasoning |
|---|---|---|
| A4 (3 freq, K=1) | 1 | new family, new fit flexibility — new equivalence class |
| A5 (3 freq, K=2) | 1 | new family — new equivalence class |
| B re-adjudication (B1/B2 under §7 residual model) | 1 | the FIT is byte-equivalent to v1 (same families, data, splits, procedure) and is NOT recharged; but the verdict gets a fresh chance under a redesigned acceptance rule — a new test in verdict space. Charged once, honestly. |
| A2 baseline comparator | 0 | identical family, data, splits, procedure as v1's A2 — a deterministic re-fit of an already-charged test adds zero new search flexibility; it is in the list only so A4/A5 must beat it under J |

Total m_delta = 3, appended to the same global family
`eq.tidal-manila.harmonic` (cumulative 5 + 3 = 8). If the human reviewer
strikes A5, m_delta drops to 2; if claim B's re-adjudication is judged free
(pure rule redesign, no new look at data), m_delta drops to 2 — reviewer's
call, noted here before hashing. The orchestrator applies the global ledger
correction at verdict time per the standing A3 rule.

## 11. Verdict rules (declared before any fit — unchanged structure from v1)

Per claim, evaluated in order:

1. Gate fails at execution → **NO_EQUATION_ATTEMPTED**.
2. No family beats all three null types at p ≤ 0.01 on test, OR §7 gating
   residual checks fail, OR bootstrap unstable → **FAILED_EQUATION_SEARCH**
   (publishable; log learnings).
3. Nulls beaten + residuals pass + bootstrap stable, but PASS-defining
   periods outside §8 tolerances → **CALIBRATION FAIL**: recorded as
   FAILED_EQUATION_SEARCH with the explicit instrument-miscalibration flag;
   the equation layer is NOT trusted on open questions until diagnosed
   (v1 §11 rule 3, carried verbatim — a beautiful fit at the wrong period is
   the worst outcome and is never dressed up as success).
4. Statistical criteria pass AND PASS-defining periods within tolerance →
   **PREDICTIVE_EQUATION** + calibration PASS for that claim.
5. Partial pass (descriptive fit, periods in tolerance, held-out/null missed)
   → **CANDIDATE_EQUATION**.
6. MECHANISM_SUPPORTED / GOVERNING_LAW_CONFIRMED out of scope (no fresh
   data, no intervention evidence).
7. Equation verdicts never modify the batch5 detection verdict (hard rule 1).

Doob separation: no verdict here confers action license; Phase 6 (Decide)
applies the Doob gate, EV, and sizing downstream. This analyst computes
neither.

## 12. Proposed ledger deltas (PROPOSED — NOT APPLIED)

To be applied only AFTER human approval, in this order:

1. `results/commitment_ledger.txt`: append SHA-256 of this file
   (post-approval, pre-fit) with timestamp and claim ids
   `eq.tidal-manila.phase.v2`, `eq.tidal-manila.phase.moondist.v2`.
2. `results/run_ledger.jsonl`: new entry — run_id `eq_tidal_v2`, phase 5,
   source run `batch5`, predecessor run `eq_tidal_v1`,
   equation_analyst_id (executor ≠ batch5 detection analyst), registration
   hash, seed base 20260612.
3. `results/multiplicity_ledger.jsonl`: append
   `{family_id: "eq.tidal-manila.harmonic", m_delta: 3, reason: "Phase 5 v2: +A4,+A5 new families; +1 claim-B re-adjudication under redesigned residual model (v1 learnings 2 and 3)"}`.

None of these have been written. This document is the only artifact of this
dispatch.

## 13. Human approval

```
APPROVED BY: Cha (lab owner) — in-session approval
DATE:        2026-06-11
AMENDMENTS:  none — approved as drafted (A5 included; claim-B +1 m-charge;
             evection band CI-exempt, attribution-grade only)
COMMITMENT HASH (post-approval): <appended to results/commitment_ledger.txt
             immediately after this edit; the ledger line is authoritative>
```
