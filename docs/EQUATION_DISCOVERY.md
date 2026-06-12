# EQUATION DISCOVERY — Phase 5 of the lab pipeline

Added: 2026-06-11. Validated and project-grounded from the lab owner's preliminary
research (`equation_discovery_layer.md`). Defines a new phase between CONFIRM
(Phase 4) and DECIDE (now Phase 6): deriving **candidate governing equations** for
structures that have already passed matched-null validation.

> The lab can derive **statistically validated candidate equations or generative
> models** for detected structures. It does not automatically discover true
> governing laws.

---

## 1. Position in the pipeline

```
PHASE 4            PHASE 5              PHASE 6
CONFIRM     ───►   EQUATION      ───►   DECIDE
(held-out          (candidate           (EV/Kelly/Doob —
 data only)         governing            unchanged, renumbered
                    equations)           from 5)
```

- **Input**: confirmed STRUCTURED verdicts only (Phase 4 output, registered family).
- **Output**: candidate equation + parameters + uncertainty + null-adjusted
  validation score + failure cases, under its own verdict labels (§7).
- **Hard gate**: no STRUCTURED verdict → `NO_EQUATION_ATTEMPTED`. The lab never
  searches for equations in unvalidated data. This preserves A7 (each layer answers
  its own question) and keeps the decision layer downstream of, never inside,
  detection.

Distinction from neighboring layers:

| Layer | Question | Output |
|---|---|---|
| Structure detection (Ph 2–4) | Is there non-null structure? | STRUCTURED / NULL |
| Relational detection (R1–R7) | Do datasets share structure beyond chance? | similarity / coupling / shared latent |
| **Equation discovery (Ph 5)** | What compact rule generates the structure? | candidate equation / generative model |
| Mechanism confirmation | Is this the true mechanism? | only with intervention/invariance evidence |
| Decide (Ph 6) | Should anyone act? | Doob gate, EV, Kelly stake |

Many distinct equations can fit the same detected pattern (non-identifiability,
§9.1); detection therefore never implies a unique equation.

---

## 2. Current eligibility (as of 2026-06-11)

Equation discovery is gated on confirmed STRUCTURED claims. Today that means:

| Source claim | Verdict | Eligible equation family | Known ground truth (calibration target) |
|---|---|---|---|
| tidal-manila, TDA H₁ delay-embed loop (p=0.01) | STRUCTURED | latent-phase / harmonic (§4.4, §4.8) | at the dataset's DAILY sampling, M2 (12.42 h) is beyond Nyquist — recoverable targets are the spring-neap cycle ≈ 14.765 d and anomalistic month ≈ 27.555 d; recovery is the pass condition |
| jpl-horizons moon distance, TDA H₁ (p=0.01) | STRUCTURED | latent-phase / harmonic | anomalistic month ≈ 27.55 d |
| openmeteo-pressure-manila: seasonal pairs MMD 6/6 (p=0.0025, batch67_r2) and pressure↔sun-moon CCA (ρ₁=0.403–0.567 across 3 splits, p=0.005) | STRUCTURED (positive controls; single-source caveat — positive pressure claims gated until second source) | harmonic regression (annual + diurnal); latent-variable (§4.3) for the sun-moon coupling | 365.25 d and 24 h (atmospheric tide) components; known ephemeris mechanism |
| All PCSO lotto claims (5 games, all faces) | NULL | — | `NO_EQUATION_ATTEMPTED` |
| 6/55 #45 transient (era-bounded, died Feb 2026) | era-bounded, G2–G4, not confirmed | — | `NO_EQUATION_ATTEMPTED` (fails the gate: no post-freeze confirmation; coefficients would encode a dead era) |

The three physical positive controls are the correct first deployment: each has an
externally known governing rule, so the equation layer can be **calibrated against
ground truth** before it is ever pointed at a dataset where the answer is unknown.
This mirrors how the blind 9-series eval validated the detection layer (9/9).

---

## 3. Theorem-card grounding

Each candidate equation family maps onto instruments the lab has already carded
(docs/kb/INDEX.md). No new mathematics is required to *fit*; what is new is the
selection-and-validation contract (§6).

| Detected structure | Candidate equation family | Existing card(s) |
|---|---|---|
| Marginal bias | probability-weight law (§4.1) | 1, 2 (chi-square+MC), 19 (detectability bound) |
| Memory / temporal dependence | Markov / autoregressive (§4.2) | 6 (Markov), 7 (Hurst) |
| Periodic cycle | harmonic / oscillator (§4.4) | 12 (Wiener–Khinchin, Fisher g) |
| Regime shift | piecewise / changepoint (§4.5) | 4 (scan statistics) |
| Low-rank matrix | factorization (§4.6) | 11 (MP/TW), 26 (matrix completion) |
| Graph community | stochastic block model (§4.7) | 24 (graph matching/spectra), 25 |
| Topological loop | latent-phase parameterization (§4.8) | 23 (TDA persistence) |
| Shared latent relation | latent-variable model (§4.3) | 22 (CCA), 21 (GW) |
| Causal relation | structural causal equation | none carded — requires onboarding + causal evidence; out of scope until then |
| Smooth numeric relation | symbolic regression / SINDy | none carded — must be onboarded with an A1 null generator before first use |

Complexity control (§6) is the operational form of card 10
(Shannon–Kolmogorov / MDL): a governing equation is a *compression* of the data,
and the compression certificate is the natural simplicity metric.

---

## 4. Equation families (corrected forms)

Notation: draws of k numbers from 1..P (PCSO: k=6, P∈{42,45,49,55,58}); D_t is the
draw set at time t. Forms below generalize beyond lotteries; lottery notation is
the worked example, consistent with the RUNBOOK.

### 4.1 Marginal bias

P(i ∈ D_t) = k/P + δ_i, subject to the identifiability constraint **Σᵢ δ_i = 0**
(the k inclusion probabilities must sum to k; unconstrained δ are not estimable).

Era-bounded variant (worked example — the real 6/55 #45 case, NOT a hypothetical):

```
P(45 ∈ D_t) = 6/55 + δ₄₅  for t in the ~three-quarter era ending 2026-02
P(i  ∈ D_t) = 6/55        otherwise       (era boundaries: ERA_REGISTRY,
                                           src/domains/pcso_lotto.py)
```

Estimation duties: which i have δ_i ≠ 0; global vs era-bounded; survival under the
three data regimes (all rows / ex-suspicious / verified-only, per M4 — coefficients
inherit data-quality sensitivity *explicitly*); held-out skill vs uniform null.

**Detectability floor (card 19)**: at the current n (≈776 draws across 5 games,
~155 per game), per-number biases below ε ≈ 0.16–0.20 (RESULTS_BATCH4 exclusion
bounds: 0.161–0.198 across the five games, i.e. 114–182% of 6/P) are below the
power floor. A fitted |δ̂_i| under that floor is noise dressed as a coefficient and
must not be reported as a candidate equation.

### 4.2 Memory (Markov)

Detection form: P(i ∈ D_t | i ∈ D_{t-1}) > P(i ∈ D_t | i ∉ D_{t-1}).

Fitted form: P(i ∈ D_t) = α·1(i ∈ D_{t-1}) + β·1(i ∉ D_{t-1}),
subject to **kα + (P−k)β = k** (expected draw size constraint; α, β are not free).

Generative form: D_t = R_t ∪ M(D_{t-1}), with retention mechanism M and fresh
content R_t, retention probability estimated from data.

Nulls: uniform constrained generator; shuffled-time; block-shuffled if eras exist;
held-out next-step prediction. Note: `src/markov_chain_model.py` already fits this
family walk-forward for backtesting — Phase 5 promotes it to a *claim-bearing*
instrument only under the §6 contract, never via the backtest path (failure mode
#5: proxy-metric backtests).

### 4.3 Shared latent variable

D_t = f_D(z_t) + ε_{D,t}, E_t = f_E(z_t) + ε_{E,t} with hidden driver z_t.
Conservative protocol: estimate ẑ_t = g(S_t) from one view, test D_t ≈ f_D(ẑ_t)
on held-out data. Supports "conditionally predictable from a shared recovered
latent factor" — never causality by itself.
(Currently no eligible claim: all lotto-vs-covariate CCA verdicts are NULL.)

### 4.4 Periodic

Canonical identifiable form (k harmonics):

x_t = a₀ + Σ_{j=1..K} [ a_j sin(jωt) + b_j cos(jωt) ] + ε_t

(Correction to the draft: a₁sin(ωt+φ) + a₂cos(ωt+φ) is over-parameterized — φ is
redundant given free a, b. Use the sin/cos pair per harmonic; amplitude and phase
are derived quantities √(a²+b²), atan2(a,b).)

Phase-shifted pair: x_t = f(θ_t) + ε_t, y_t = g(θ_t + φ) + η_t — handles
nonlinear/phase-lagged periodic coupling that same-time correlation misses.
Instruments: harmonic regression, Fourier features, cross-spectrum/coherence,
lagged cross-correlation, phase reconstruction, delay-embedding alignment, DTW —
all against matched nulls (phase-randomized surrogates preserve the spectrum;
plain permutation does not — use both).

### 4.5 Regime / changepoint

x_t = f₁(t) + ε_t for t < τ; f₂(t) + ε_t for t ≥ τ (or distributional: P₁ → P₂).
Do not force a periodic model onto a segment difference. Validation: held-out
segment prediction; τ stability under resampling; block-permutation null;
bootstrap/posterior uncertainty on τ; within-regime residual checks. (The #45
transient is the house example of why fitted coefficients die with their era.)

### 4.6 Low-rank matrix

M = UVᵀ + ε. Estimate rank k (MP/TW edge, card 11), factors, held-out
reconstruction vs iid and shuffled-entry nulls, bootstrap factor stability.
Cleanest case for equation claims.

### 4.7 Graph community

P(A_ij = 1 | z_i, z_j) = B_{z_i z_j} (SBM). Estimate ẑ, B̂ by block edge densities;
validate that graphs generated from B̂ reproduce degree distribution, modularity,
spectra, motif counts, held-out edge likelihood.

### 4.8 Topological loop → latent phase

A confirmed H₁ loop licenses a phase variable θ_t ∈ [0, 2π):
x_t = A·[cos θ_t, sin θ_t]ᵀ + b + ε_t (embedded circle; the equation may live in
the recovered latent coordinate, not the original ones). Validate: loop persists
under bootstrap; phase predicts held-out points; circle model beats blob null;
same phase explains multiple views. **This is the tidal/lunar deployment path**,
and the recovered angular velocity ω̂ = dθ/dt has a known answer for both (§2).

---

## 5. Three levels of equation claims

1. **Descriptive** — summarizes detected structure (M ≈ UVᵀ; x_t ≈ a sin(ωt)+...).
   Useful; never a governing-law claim.
2. **Predictive** — beats matched nulls on held-out data (x̂_{t+1} = f(x_t, ...)).
3. **Mechanistic / governing law** — explains *why*; requires stable parameters,
   interpretable variables, and confirmation under intervention or new
   environments. The lab can reach levels 1–2 internally; level 3 additionally
   requires external/mechanistic evidence and fresh-data confirmation.

**Doob separation (card 8)**: even a level-2 PREDICTIVE_EQUATION confers no
action license. Phase 6 (Decide) still applies the Doob gate, payout-relevant
EV, and Kelly sizing. An equation that predicts in proxy units can still lose in
the unit that pays (single-hit z=+2.1 → −71% ROI precedent).

---

## 6. Registration contract and selection rule

Every equation-discovery attempt is registered (human-approved, like every
REGISTRATION_*.md), hashed into `results/commitment_ledger.txt` before the run,
recorded in `results/run_ledger.jsonl`, and charged to the global multiplicity
family in `results/multiplicity_ledger.jsonl` (A3: equation searches are a new
equivalence class; they add to m, never bypass it).

```yaml
equation_claim_id: eq.tidal-manila.phase.v1
source_structure_claim: <claim id with STRUCTURED verdict, post-freeze>
structure_verdict: STRUCTURED
equation_type: latent_phase            # one family per claim
candidate_family: [circle_phase, fourier_k3, damped_oscillator]   # declared BEFORE fitting
inputs: [t, lagged_values]
target: [x_t]
fit_split: {train: first_60pct, validation: next_20pct, test: final_20pct}
null_baseline: [permutation, phase_randomized_surrogate, AR_null]
null_equation_generator: >            # A1 requirement, see below
  run the identical discovery procedure on B matched-null synthetic series;
  record the distribution of recovered equations, complexities, and scores
selection_rule: min_description_length_subject_to_heldout_skill
metrics: [RMSE, heldout_loglik, residual_autocorrelation, parameter_stability, null_adjusted_p]
data_regimes: [all_rows, ex_suspicious, verified_only]   # M4: report coefficients per regime
multiplicity_charge: {family_id: <id>, m_delta: <count of families tried>}
public_claim_allowed: false_until_confirmed
```

**Null-equation generator (A1, the key addition over the draft)**: detection
instruments require a computable null generator; so do equation searches. The
procedure that proposes equations must itself be run on matched synthetic nulls.
SINDy/symbolic regression on pure noise *returns equations* — the null
distribution of recovered-equation scores is what converts "we found an equation"
into a calibrated p-value. Without this, the equation layer is failure mode #1
(estimator bias read as signal) in new clothing.

**Selection objective**: J(f) = L_heldout(f) + λ·complexity(f); choose
f* = argmin J. Accept only if L_test(f*) < L_test(f_null) at the
multiplicity-corrected threshold, AND f* is stable under bootstrap, AND residuals
pass §8. (Tuning λ *after* seeing test scores is the M1 tuned-to-pass failure —
λ is declared in the registration.)

---

## 7. Verdict labels (new family, separate from detection labels)

| Verdict | Meaning |
|---|---|
| NO_EQUATION_ATTEMPTED | source claim not STRUCTURED, or family not registered |
| CANDIDATE_EQUATION | descriptive fit exists (level 1) |
| PREDICTIVE_EQUATION | beats matched nulls on held-out data (level 2) |
| MECHANISM_SUPPORTED | stable, interpretable, externally corroborated |
| GOVERNING_LAW_CONFIRMED | fresh-data confirmation + mechanism evidence (level 3) |
| FAILED_EQUATION_SEARCH | structure confirmed but no compact equation passed validation |

FAILED_EQUATION_SEARCH is a publishable, informative outcome (structure without
compressibility — consistent with card 10's distinction between statistical
structure and algorithmic compressibility). Equation verdicts never upgrade a
detection verdict; a NEAR_MISS_REGISTERED_SIGNAL stays a near miss regardless of
how well an equation fits it.

---

## 8. Required residual checks

For r_t = x_t − x̂_t: autocorrelation; periodogram / spectral peaks (Fisher g);
MMD against null residuals (card 20); heteroskedasticity; changepoint tests;
TDA on residual embeddings; compression/entropy. A good equation makes residuals
match the *declared* noise model — structured residuals demote the verdict to
FAILED_EQUATION_SEARCH or force a declared model-class extension (new
registration, new multiplicity charge).

---

## 9. Failure modes (extends the RUNBOOK gallery)

1. **Non-identifiability** — many equations fit one pattern (a sinusoid and a GP
   both fit a periodic series). Report the simplest adequate model; never claim
   uniqueness. Enforce constraint sets (Σδ=0; kα+(P−k)β=k) so reported
   coefficients are at least well-defined.
2. **Wrong attribution** — "this dataset is structured" underdetermines *what* to
   fit. The equation layer consumes the detection layer's attribution output
   (driving rows/variables/segments/communities/loop coordinates); no attribution,
   no fit.
3. **Overfit symbolic equations** — symbolic regression memorizes noise
   impressively. Controls: held-out split, complexity penalty, null-equation
   generator (§6), bootstrap parameter stability, residual tests, fresh-data
   confirmation.
4. **Correlation read as mechanism** — y_t = f(x_t) is predictive, not causal,
   absent intervention / time order / natural experiment / cross-environment
   invariance. Publish at the level the evidence supports.
5. **Era-fitted coefficients** (this project's specific lesson) — coefficients
   estimated inside one regime (ball set, prize structure, season) silently encode
   the regime. Every coefficient is reported with its era bounds and its
   sensitivity across the three data regimes.

---

## 10. Pipeline summary

```
PHASE 5 — EQUATION DISCOVERY
1.  Gate: confirmed STRUCTURED claims only (else NO_EQUATION_ATTEMPTED)
2.  Consume attribution (which rows/variables/segment/loop)
3.  Classify structure type → select candidate families (declared, small)
4.  Register: family, splits, nulls, null-equation generator, λ, m-charge
    → human approval → commitment-ledger hash
5.  Fit on train only; select by held-out skill + MDL
6.  Compare against matched null equations (incl. null-recovered-equation dist.)
7.  Residual checks (§8)
8.  Bootstrap parameter stability; per-regime coefficient report (M4)
9.  Fresh-data confirmation before any label above PREDICTIVE_EQUATION
10. Publish under §7 labels; Phase 6 (Decide) unchanged downstream
```

First deployment (recommended): the three calibration targets in §2, run as
positive controls with known ground-truth equations, before the layer is trusted
on any open question. Agent routing: **equation-analyst** (agents/
equation-analyst.md) designs and fits (Fable), Haiku re-runs (cross-model rule),
independent-verifier checks recovered parameters against the known constituents,
docs-web-editor publishes. Role-ID rule: the equation-analyst instance for a
claim is never the structure-analyst instance that detected it.
