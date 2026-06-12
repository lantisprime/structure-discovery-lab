# REGISTRATION — eq.tidal-manila.phase.v1

**STATUS: APPROVED 2026-06-11 (Cha, lab owner — §13). Committed pre-fit; the
commitment-ledger line is the binding hash.**

No fit has been run. No data values have been inspected beyond row count /
date range / column names. This registration must be human-approved and
commitment-hashed into `results/commitment_ledger.txt` BEFORE any fitting
(EQUATION_DISCOVERY.md §6; equation-analyst hard rule 3).

Drafted: 2026-06-11 by equation-analyst (Fable, design-only dispatch).
Pipeline position: Phase 5, first real equation-discovery run — **calibration
target / positive control** (EQUATION_DISCOVERY.md §2, §10).

---

## 1. Source claim and gate check (§2 eligibility)

| Field | Value |
|---|---|
| source_structure_claim | tidal-manila, TDA H₁ delay-embedding loop |
| structure_verdict | STRUCTURED |
| Evidence | persistence 1.124 vs matched-null 0.427, p = 0.01 (permutation floor); loop recoverable from 20% landmarks |
| Citation | THEOREM_SYNTHESIS.md §5 row 33; script `src/relational_batch5.py`; `results/run_ledger.jsonl` run_id `batch5` |
| Attribution on file | yes — H₁ loop in the delay-embedded derived tidal series (loop coordinates = delay-embedding of the daily tidal series) |
| Eligibility row | EQUATION_DISCOVERY.md §2, row 1 (tidal-manila calibration target) |
| Independence (rule 2) | the analyst executing the registered fit must NOT be the batch5 detection analyst; `equation_analyst_id != detection_analyst_id` to be recorded in run_ledger before execution |

Gate verdict if any of the above fails at execution time: `NO_EQUATION_ATTEMPTED`.

### Calibration framing (why this is a positive control)

The data are ephemeris-derived; the governing rule is externally known. At
DAILY sampling, M2 (12.42 h) is beyond Nyquist (Nyquist period = 2 d) and is
**not recoverable**; declared recoverable constituents are:

- **spring–neap cycle ≈ 14.765 d** (synodic fortnightly beat; note this is also
  where sub-Nyquist semidiurnal energy aliases at daily sampling — expected and
  acceptable for a positive control)
- **anomalistic month ≈ 27.555 d** (perigee–apogee distance cycle)

The PASS condition is recovery of these periods within the pre-declared
tolerances of §8 — not merely a good fit. The run calibrates the equation
layer before it is pointed at any open question.

---

## 2. Data

| Field | Value |
|---|---|
| File | `datasets/tidal-manila/tidal_derived.csv` |
| Sampling | daily |
| Columns | Date, Moon Dist (km), Lunar tidal accel (g), Sun Dist (km), Solar tidal accel (g), Total tidal accel (g) |
| Rows / date range | **verified 2026-06-11**: n = 366 data rows, 2025-06-11 .. 2026-06-11 (wc/head/tail only; no value statistics computed) |
| Provenance caveats | per `datasets/tidal-manila/DATASET.md`: DERIVED (computed, not measured) from JPL Horizons source-of-record distances via value = C/d³; `Total tidal accel (g)` is a **simple scalar sum** of lunar + solar terms that **ignores the angular factor** between the two tidal axes (see §2.1 and the calibration caveat below) |

**Interpretation caveat (declared now, before fitting):** because Total is a
scalar sum without the sun–moon angle, the classical spring–neap alignment
beat is not encoded directly. A ≈14.77 d component is nonetheless expected in
this series via the lunar orbital "variation" inequality in Moon Dist (period
= half synodic month ≈ 14.765 d), which propagates through C/d³. The PASS
target period is unchanged; the RESULTS doc must attribute any recovered
14.77 d line to the distance-variation term, not to axis alignment.

### 2.1 data_regimes declaration (M4)

`data_regimes: [all_rows]` — with justification: DATASET.md confirms the
series is deterministically computed from JPL Horizons source-of-record
distances (`parse_horizons.py`, C_moon recovered with std < 0.05%), not
scraped/measured records, so the lab's `ex_suspicious` / `verified_only`
regimes (built for provenance-suspect rows) collapse to `all_rows`. There
are no suspicious rows to exclude. (The measured IOC tide-gauge layer in
DATASET.md is a sample with a recorded gap and is NOT used here.) This collapse is itself a declared, human-approvable choice; if the
human reviewer prefers, the three regimes can be run identically and reported
as triplicate (cost only). Either way the coefficient report states the
regime explicitly (failure mode #5, era-fitted coefficients: era bounds =
full file range, single era, no known regime boundary).

### 2.2 Target columns and justification (two claims)

| Claim | Target | Justification |
|---|---|---|
| A (primary) | `Total tidal accel (g)` | the quantity in which the H₁ loop structure was detected (derived tidal series); contains BOTH known constituents (spring–neap beat + anomalistic modulation) — the full two-frequency calibration test |
| B (secondary) | `Moon Dist (km)` | clean single-constituent control (anomalistic month only, ≈ sinusoidal in time); calibrates the single-frequency recovery path with an unambiguous ground truth |

Two targets = two equation claims = both charged to multiplicity (§9).
The lunar/solar component columns are NOT targets (they are intermediate
derivations of the two targets' drivers; fitting them adds m without adding
calibration information).

---

## 3. Registration contract (EQUATION_DISCOVERY.md §6 YAML)

```yaml
equation_claim_id: eq.tidal-manila.phase.v1        # claim A; claim B suffix .moondist.v1
source_structure_claim: tidal-manila.tda-h1-delay-embed.batch5
structure_verdict: STRUCTURED
equation_type: latent_phase_harmonic               # §4.4 canonical form via §4.8 loop license
candidate_family:                                   # declared BEFORE fitting; closed list
  # --- claim A: Total tidal accel (g) ---
  - A1_harmonic_1freq_k1     # a0 + a·sin(ω₁t) + b·cos(ω₁t); one free ω
  - A2_harmonic_2freq_k1     # a0 + Σ_{i=1,2} [aᵢsin(ωᵢt) + bᵢcos(ωᵢt)]; two free ω
  - A3_harmonic_2freq_k2     # as A2 plus first overtone (2ωᵢ) sin/cos pair per base
                             # frequency; fourier cap K=2 per base frequency, HARD CAP
  # --- claim B: Moon Dist (km) ---
  - B1_harmonic_1freq_k1
  - B2_harmonic_1freq_k2     # base + first overtone (eccentricity harmonic)
  # NO free phase parameters anywhere: per-harmonic sin/cos pairs only
  # (amplitude/phase are derived: sqrt(a²+b²), atan2(a,b)) — §4.4 correction
inputs: [t]                                         # t = days since first row; no lagged values
target: ["Total tidal accel (g)", "Moon Dist (km)"] # two claims, charged separately
fit_split:                                          # chronological, no shuffling
  train: first_60pct          # ≈ rows 1–220, ~2025-06-11 .. ~2026-01-16
  validation: next_20pct      # ≈ rows 221–293 (~73 d ≈ 4.9 spring–neap, 2.6 anomalistic cycles)
  test: final_20pct           # ≈ rows 294–366 (untouched until selection is frozen)
null_baseline: [permutation, phase_randomized_surrogate, AR_null]
B_nulls: 200                  # per null type, per claim; seeded
null_equation_generator: >
  Run the IDENTICAL discovery procedure (frequency grid + refine, all declared
  families, J-minimization, identical splits) on B=200 matched synthetic null
  series per null type per claim; record the full distribution of recovered
  frequencies, complexities, and J/test scores. Null-adjusted
  p = (1 + #{null test-score <= observed}) / (B + 1). See §5.
selection_rule: min_J_subject_to_heldout_skill      # §6 objective, λ fixed in §6 below
metrics: [RMSE, heldout_loglik, residual_autocorrelation, parameter_stability,
          null_adjusted_p, period_recovery_error]
data_regimes: [all_rows]                            # justified in §2.1
multiplicity_charge: {family_id: eq.tidal-manila.harmonic, m_delta: 5}
public_claim_allowed: false_until_confirmed
```

---

## 4. Fitting procedure (registered; execute-only at Haiku tier)

1. **ω estimation on train ONLY.** Coarse periodogram grid over declared
   period window **4 d – 120 d** (sub-Nyquist with margin at the short end;
   < half the train span at the long end), grid step = Rayleigh/4 of the
   train span; then nonlinear least-squares refinement of ω with sin/cos
   coefficients profiled out (linear given ω). No spectral statistic is
   computed on validation or test rows before selection freeze.
2. Per family: fit coefficients by least squares on train (Gaussian noise
   model, declared).
3. Evaluate J on validation; select f* = argmin J across the family list for
   that claim.
4. Freeze f*; evaluate once on test; compare against the null-equation score
   distribution (§5); run residual checks (§7) and bootstrap (§8) on
   train+validation.
5. Two-run reproducibility: identical seeded re-run by a second execute-only
   instance; diff must be empty to machine precision.

**Complexity measure (declared):** complexity(f) = (# free linear
coefficients) + 2 × (# free frequencies) (a nonlinear frequency parameter is
charged double — it buys far more fit flexibility than a linear coefficient).
So A1 = 5, A2 = 9, A3 = 13, B1 = 5, B2 = 7.

**Penalty (declared, fixed — M1 guard):** λ = ln(n_train)/2 ≈ 2.7 per
complexity unit on the negative-log-likelihood scale (BIC-rate). λ is fixed
NOW, before any fit; changing it after seeing validation or test scores
voids the run.

**Selection objective:** J(f) = NLL_validation(f) + λ·complexity(f).

---

## 5. Null baselines and null-equation generator (A1)

All nulls are matched to the train segment's marginal mean/variance and
length, generated with declared seeds, B = 200 per type per claim:

| Null | Construction | What beating it shows |
|---|---|---|
| permutation | iid shuffle of the target series | any temporal structure |
| phase_randomized_surrogate | FFT phase randomization preserving the full power spectrum | **the stringent null**: a stochastic process with the identical spectrum has no out-of-sample phase coherence; only a genuinely phase-locked deterministic harmonic predicts held-out points |
| AR_null | AR(p) fitted on train, p ≤ 5 chosen by AIC on the null fit (declared cap) | autocorrelated-but-aperiodic noise does not explain the fit |

**Null-equation generator:** the complete §4 procedure (grid + refine +
family selection by J) is run unchanged on every null series. Recorded per
null: selected family, recovered frequencies, complexity, validation J, test
score. This converts "we found an equation" into a calibrated null-adjusted
p (EQUATION_DISCOVERY.md §6: discovery procedures return equations on pure
noise; the null score distribution is the admission requirement).

**Acceptance threshold (multiplicity-corrected, declared):** with m_delta = 5
charged to the global family, the per-claim acceptance requires
null-adjusted p ≤ 0.01 against EACH of the three null types (with B = 200,
attainable floor is 1/201 ≈ 0.005, so 0.01 is resolvable). The global
multiplicity ledger correction is applied on top by the orchestrator at
verdict time per the lab's standing A3 rule.

---

## 6. Detectability floor (card 19 analogue for this n)

With n_train ≈ 220 daily points and Gaussian residual σ̂:

- **Amplitude floor:** SE(amplitude) ≈ σ̂·√(2/n_train). Declared floor: no
  harmonic is reported as a recovered constituent unless its fitted amplitude
  ≥ 4·σ̂·√(2/n_train) (≈ 0.38·σ̂). Coefficients below this floor are noise
  dressed as coefficients (hard rule 5) and are dropped from the reported
  equation regardless of J.
- **Frequency resolution:** Rayleigh limit of train span (~220 d) gives
  period uncertainty ΔP ≈ P²/T_train: ≈ 1.0 d at P = 14.765 d, ≈ 3.5 d at
  P = 27.555 d. NLS refinement on a high-SNR deterministic series should beat
  Rayleigh substantially; the §8 tolerances are set at ±5% (tighter than
  Rayleigh at the anomalistic period, looser at spring–neap), which is the
  honest compromise for a first calibration at this n.
- Both targets' constituents are expected far above these floors (ephemeris
  data, tiny residual σ); if they are NOT, that is itself a calibration
  finding to log, never to quietly tune away.

---

## 7. Residual checks (EQUATION_DISCOVERY.md §8 — all required)

On r_t = x_t − x̂_t over train+validation (test residuals reported but not
used for selection):

1. Ljung–Box autocorrelation (lags 1–40).
2. Periodogram of residuals + Fisher g (card 12) — no remaining significant
   peak in the declared 4–120 d window.
3. MMD of residuals vs the declared Gaussian noise model draws (card 20).
4. Heteroskedasticity (Breusch–Pagan vs t).
5. Changepoint scan on residuals (card 4 instrument).
6. TDA H₁ on residual delay-embedding — the detected loop must be GONE from
   residuals (the equation should absorb the structure that licensed it).
7. Compression/entropy check (card 10).

Structured residuals ⇒ verdict demotion to FAILED_EQUATION_SEARCH or a NEW
registration with a new m charge — never a quiet model extension.

## 8. Pre-declared period-recovery tolerances (calibration PASS condition)

| Claim | Constituent | Ground truth | Declared tolerance |
|---|---|---|---|
| A (Total tidal accel) | spring–neap | 14.765 d | recovered P̂ ∈ [14.03, 15.50] d (±5%) |
| A (Total tidal accel) | anomalistic month | 27.555 d | recovered P̂ ∈ [26.18, 28.93] d (±5%) |
| B (Moon Dist) | anomalistic month | 27.555 d | recovered P̂ ∈ [26.18, 28.93] d (±5%) |

Additionally the 95% bootstrap CI of each P̂ must contain the ground-truth
value. M2 (12.42 h) must NOT be claimed at this sampling; any reported
constituent with P̂ < 4 d is an automatic calibration FAIL flag.

## 9. Bootstrap scheme (parameter stability)

Moving-block bootstrap on train+validation residuals added back to the
fitted curve (declared block length 15 d ≈ one spring–neap cycle),
B_boot = 500, seeded. Refit f* per replicate. Stability requirements:
95% CI on each P̂ within the §8 tolerance band; amplitude coefficient of
variation < 20%; selected family identical in ≥ 90% of replicates.

## 10. Multiplicity charge

`{family_id: eq.tidal-manila.harmonic, m_delta: 5}` — five family×target
combinations tried (A1, A2, A3, B1, B2) across two claims. Both claims are
charged even though they share a dataset (A3: equation searches are a new
equivalence class; they add to m, never bypass it). If the human reviewer
strikes claim B, m_delta drops to 3 (note here, update before hashing).

## 11. Verdict rules (declared before any fit)

Per claim, evaluated in order:

1. Gate fails at execution (verdict not STRUCTURED post-freeze, attribution
   missing, analyst-independence violated) → **NO_EQUATION_ATTEMPTED**.
2. No family beats all three null types at p ≤ 0.01 on test, OR residual
   checks fail, OR bootstrap unstable → **FAILED_EQUATION_SEARCH**
   (publishable, informative; log what was learned).
3. Nulls beaten + residuals pass + bootstrap stable, but recovered periods
   OUTSIDE §8 tolerances → **CALIBRATION FAIL**: record as
   FAILED_EQUATION_SEARCH with an explicit instrument-miscalibration flag;
   the equation layer is NOT trusted on open questions until diagnosed. A
   statistically beautiful fit at the wrong period is the worst outcome here
   and must not be dressed up as success.
4. Statistical criteria pass AND periods within tolerance →
   **PREDICTIVE_EQUATION** + calibration PASS for that claim.
5. Statistical criteria partially pass (descriptive fit, periods in
   tolerance, but held-out/null criterion missed) → **CANDIDATE_EQUATION**.
6. Nothing above PREDICTIVE_EQUATION is reachable in this run (no fresh
   data, no intervention evidence). MECHANISM_SUPPORTED /
   GOVERNING_LAW_CONFIRMED are explicitly out of scope.
7. Equation verdicts never modify the batch5 detection verdict (hard rule 1).

Doob separation: no verdict here confers action license; Phase 6 unchanged.

## 12. Proposed ledger deltas (PROPOSED — NOT APPLIED)

To be applied only AFTER human approval, in this order:

1. `results/commitment_ledger.txt`: append SHA-256 of this file
   (post-approval, pre-fit) with timestamp and claim ids
   `eq.tidal-manila.phase.v1`, `eq.tidal-manila.phase.moondist.v1`.
2. `results/run_ledger.jsonl`: new entry — run_id `eq_tidal_v1`,
   phase 5, source run `batch5`, equation_analyst_id (executor, ≠ batch5
   detection analyst id), registration hash, seeds.
3. `results/multiplicity_ledger.jsonl`: append
   `{family_id: "eq.tidal-manila.harmonic", m_delta: 5, reason: "Phase 5 first calibration run, 2 claims x declared families"}`.

None of these have been written. This document is the only artifact of this
dispatch.

## 13. Human approval

```
APPROVED BY: Cha (lab owner) — via review comment on this document
DATE:        2026-06-11
AMENDMENTS:  none — approved as drafted (two-claim scope m_delta=5; ±5%
             tolerances; λ=BIC-rate, K=2 cap; data_regimes=all_rows)
COMMITMENT HASH (post-approval): <appended to results/commitment_ledger.txt
             immediately after this edit; the ledger line is authoritative>
```
