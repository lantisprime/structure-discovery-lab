# Structure Discovery Laboratory

**A governed, reproducible research framework for detecting — or rigorously excluding —
structure in stochastic data.** The laboratory combines instruments from five
mathematical traditions under a single calibration discipline, with formal protocols for
onboarding theorems and datasets, harmonizing their conflicts, and confirming findings on
held-out data.

![The Structure Lab console — the Overview landing page](docs/images/console-overview.png)

*The lab drives from a local web console (`python3 webapp/server.py` → http://localhost:8787).
The **Overview** landing page always surfaces the single next action, alongside live counts
from the run ledger, the multiplicity ledger, and the honesty meter. Nine views plus a
guided wizard cover the whole pipeline — pre-registration, human-gated approvals, execution,
and results.*

The five faces of structure interrogated are **statistical** (uniform marginals),
**dynamical** (future ⊥ past), **algorithmic** (incompressible), **cross-sectional /
physical** (no collective modes), and — added with the relational extension —
**relational** (two datasets share more structure than independent generation predicts;
or a subset determines the whole). Source: `docs/CROSS_DATASET_FRAMEWORK.md §0`.

---

## Table of contents

- [Why this lab exists](#why-this-lab-exists)
- [Research questions the framework answers](#research-questions-the-framework-answers)
- [The constitution: articles A1–A8 and conflict registry C1–C11](#the-constitution-articles-a1a8-and-conflict-registry-c1c11)
- [Instrument inventory](#instrument-inventory)
- [The theorem arsenal — how each instrument is used](#the-theorem-arsenal--how-each-instrument-is-used)
- [Equation discovery — Phase 5](#equation-discovery--phase-5)
- [Verification and integrity stack](#verification-and-integrity-stack)
- [Four-level ledger system](#four-level-ledger-system)
- [Agent system](#agent-system)
- [Independently verified performance](#independently-verified-performance)
- [Evidence-grade ladder G0–G6](#evidence-grade-ladder-g0g6)
- [Domain architecture](#domain-architecture)
- [Module: riemann-zero-lab (deterministic mathematics)](#module-riemann-zero-lab-deterministic-mathematics)
- [Repository guide](#repository-guide)
- [Limitations](#limitations)
- [Reviews and audits trail](#reviews-and-audits-trail)

---

## Why this lab exists

The lab began with a deceptively simple question — do public lottery draws contain
any structure an analyst could detect, or better, exploit? — and discovered that the
honest pursuit of that question requires machinery far larger than the question
itself. Most apparent "structure" in stochastic data is self-deception in one of a
few recurring costumes: estimator bias read as signal, textbook asymptotics
misapplied to finite samples, look-elsewhere effects, era-bounded transients
mistaken for persistent mechanisms, and analyses quietly tuned until they pass.
Case Study 1 produced four such false signals (Hurst bias, Binder pseudo-plateau,
degenerate KS, smoothing-bias backtest edge) — every one dissolved by the same
discipline, simulating the null from the actual generative mechanism (A1).

The lab therefore exists to do three things that ad-hoc analysis cannot:

1. **Make negative results as rigorous as positive ones.** "No structure found" is
   reported with its power ("no effect ≥ size ε at this n"), backed by exclusion
   certificates, and dead-end hypotheses are logged as results, never discarded.
2. **Make positive results survivable.** Every claim must pass calibrated nulls,
   multiplicity accounting, era gates, independent re-execution by a different
   agent identity, and — before any label above exploratory — held-out or
   fresh-data confirmation, with commitments hashed before outcomes are known.
3. **Generalize the discipline.** The instruments live in a domain-neutral core
   (`src/core/`); the lottery is Case Study 1, not the mission. Any stochastic
   dataset — financial series, physical measurements, synthetic benchmarks — can
   be onboarded against the same constitution, and the framework's verdict is
   equally valuable in both directions: structure detected, or structure rigorously
   excluded at a stated resolution.

The result is less a collection of analyses than a governed laboratory: theorems
are onboarded like instruments, conflicts between them are adjudicated by written
articles, and the lab's own tools are required to fail loudly on synthetic nulls
before they are ever trusted on real data.

---

## Research questions the framework answers

1. **Detection** — does this sequence deviate from its declared null model, on any of
   the five faces of structure?
2. **Attribution** — is a detected deviation data corruption, estimator bias,
   look-elsewhere illusion, era-bounded transient, or persistent mechanism?
3. **Decision** — if structure exists, what is it worth under explicit decision theory
   (Doob gate → expected value → Kelly sizing), net of costs?

---

## The constitution: articles A1–A8 and conflict registry C1–C11

Source: `docs/THEOREM_GOVERNANCE.md`.

### Harmonization articles (A1–A7, plus deterministic-math extension A8)

**A1. One generative null, many lenses.** Every instrument's null distribution is
derived by Monte Carlo from the same constrained generative model — never from textbook
asymptotics. This discipline dissolved four false signals in Case Study 1 (Hurst bias,
Binder pseudo-plateau, degenerate KS, smoothing-bias backtest edge) and is documented
as the primary source of methods casualties.

**A2. Null-trial admission.** No estimator touches real data before demonstrating
silence on simulated H₀ data of identical shape.

**A3. Equivalence-class accounting.** Multiplicity budget m counts statistics grouped
into classes (null-correlation |r| > 0.90 on simulated data). Anomalies are identified
by their driving rows, not by which statistics noticed them.

**A4. Asymmetric verdict logic.** A flag from any admissible instrument defeats H₀
pending replication; passes accumulate scope coverage, not proof. Every "pass" is
reported with its power: "no effect" always means "no effect ≥ size X at this n."

**A5. Stationarity gate.** Before any pooled statistic is interpreted, run the
windowed-homogeneity check. If eras differ, pooled p-values are quarantined and the
analysis proceeds per era.

**A6. Designated arbiter.** Conflicting exploratory verdicts define what gets
pre-registered; the held-out confirmation test is the only arbiter, never argument.

**A7. Layered one-way flow.** Detection → interpretation → decision. Information flows
forward only; each theorem is asked only the question of its own layer.

**A8. Deterministic-certificate substitution** *(deterministic-math extension, 2026-06-13).*
When a claim is a deterministic mathematical fact with no sampling model, the MC-null (A1/A2)
is replaced by a three-leg **certificate**: exact computation to a declared tolerance,
independent recomputation by a different instance, and an analytic invariant cross-check (e.g.
located zero count = N(T) = argument-principle contour integral). A8 leaves A1–A7 intact for
every stochastic question; it only supplies an admission path for claims that cannot be
resampled. First applied in `riemann-zero-lab`.

### Conflict registry: C1–C11

The ten recorded collisions between theorem families (source: `docs/THEOREM_GOVERNANCE.md`):

| # | Collision | Resolution |
|---|---|---|
| C1 | Asymptotic theorems vs finite data (produced 3 false signals: Hurst, Binder, KS) | A1: simulate the null from H₀ |
| C2 | Competing nulls — two "laws" predicting different baselines | A1: each theorem's null derived from H₀, not imported |
| C3 | Statistic equivalence — theorems wearing each other's clothes | A3: equivalence-class counting; flags within a class count once |
| C4 | One-sided certificates vs two-sided tests | A4: asymmetric verdicts; passes accumulate scope, not proof |
| C5 | Pooled stationarity vs era structure | A5: stationarity gate; era boundaries from known regime events first |
| C6 | Same anomaly, opposite verdicts under different alternatives | A6: designated arbiter; held-out confirmation decides |
| C7 | EV vs Kelly vs Doob — superficially inconsistent prescriptions | A7: layered ordering; each theorem answers its own layer's question |
| C8 | Universality vs bias-hunting | A7: universality fixes null fluctuation laws; bias detection hunts deviations from those laws |
| C9 | Relational double counting — one anomaly, many faces | Mandatory row-trace before any relational flag is reported; if driving rows underlie a known anomaly the flag joins that equivalence class |
| C10 | Representation freedom as uncharged multiplicity | Representation bundle declared per dataset before the run; A3 budget counts representation × method × metric classes |
| C11 | Deterministic mathematics vs the MC-null premise (no sampling model exists for "is t_n a zero of ζ?") | A8: admit deterministic claims on a verification certificate (exact computation + independent recomputation + analytic invariant count), MC-null retained for stochastic sub-questions (spacing vs Poisson) |

### Expectation-free registration protocol

**Discovery tests carry no outcome expectations.** Source: `docs/REMEDIATION_LOG.md`
"Protocol change first" section. A registration contains: claim type, representation,
instrument, null, decision rule, and falsification criteria — never a predicted result.
Mechanism-based predictions survive only as *instrument-validity controls* (e.g. "if
the pipeline cannot detect the tidal loop, the pipeline is broken"), which calibrate
tools, not outcomes. Codified in `docs/RELATIONAL_RUNBOOK.md` Phase 1 (amended). Prior
registrations written with outcome expectations are explicitly labeled retroactive in
the run ledger and in `results/commitment_ledger.txt`.

---

## Instrument inventory

### Knowledge base: 26 cards in 6 faces

Source: `docs/kb/INDEX.md`. Every instrument requires a KB card before touching real
data (Part 3 of the governance protocol).

| Face | Cards | Instruments |
|---|---|---|
| Statistical | 5 (cards 1–5) | LLN/CLT, chi-square+exact MC, permutation tests, scan statistics, multiple comparisons |
| Dynamical | 4 (cards 6–8, 12) | Markov chains, Hurst/R-S, Doob optional stopping, Wiener–Khinchin/Fisher g |
| Decision | 3 (cards 8–9, 16) | Doob, Kelly criterion, expected-value/Stern-Cover |
| Algorithmic | 2 (cards 10, 15) | Shannon–Kolmogorov compression, covering designs |
| Cross-sectional / physical | 7 (cards 11, 13–14, 17–19, 26) | Marchenko–Pastur/Tracy–Widom, SOC/universality, power laws/Zipf/Taylor/Benford, Szemerédi APs, graphons, concentration/exclusion |
| Relational (R1–R7) | 7 (cards 20–26) | MMD/energy distance (R1), Gromov–Wasserstein (R2), CCA family (R3), TDA persistence distances (R4), graph matching/spectra (R5), coresets/landmarks (R6), matrix completion/compressed sensing (R7) |

**Admission status.** All 7 relational families (R1–R7) are admitted: FPR calibrated
at tested shapes; power curves frozen over declared effect grids (source:
`docs/REMEDIATION_LOG.md M1`). **GW (R2) is demoted to exploratory-only (G0):** the
n=200 gate confirmed FPR (0.055) but the p-distribution was non-uniform (lattice χ²
p=0.002); a symmetric-null variant also fails (p=0.005). The miscalibration is
inherent to moment-matched regeneration nulls for GW at these shapes. GW is flagged G0
pending null redesign; A4 holds: the flag stands and no published verdict relied on GW
alone (source: `docs/REMEDIATION_LOG.md M2`).

**Results ledger: 40 rows.** Source: `docs/THEOREM_SYNTHESIS.md §5`. Each row records
instrument, functional, H₀ value, observed value, and corrected p-value basis.

---

## The theorem arsenal — how each instrument is used

### Preamble: the implication lattice

The 26 instruments are not independent claims. They form a one-way lattice
(source: `docs/THEOREM_SYNTHESIS.md §2`): H₀ implies uniform marginals, order-0 serial
structure, flat spectrum, MP eigenvalue bulk, and maximal entropy — but none of those
properties individually implies H₀. The master equivalence is algorithmic:
incompressibility (Shannon/Kolmogorov/Martin-Löf) is the only single property
*equivalent* to H₀, because any computable structure — frequency bias, memory, cycle,
or factor — reduces entropy rate and admits compression. Consequently:

- uniform marginals ⇏ randomness (a deterministic rotation gives perfect chi-square forever)
- order-0 lag-1 ⇏ no memory (pairwise independence at lag 1 does not exclude lag-7 dependence)
- flat spectrum ⇏ independence (spectra capture second moments only; nonlinear dependence is spectrally invisible)
- incompressibility ≈ H₀ (the conjunction of all other properties)

The suite covers each other's blind spots in a closed loop; the joint verdict is
stronger than the sum of individual passes.

**Two pseudo-critical artifacts** illustrate the methods-casualty discipline required to
maintain this loop: (1) raw Hurst H-hat on a short i.i.d. series is biased upward —
calibration against a same-length null is mandatory before any memory claim; (2) the
Binder cumulant can show a pseudo-plateau mimicking a critical fixed point, which
n≈4-window estimator bias reproduces exactly on simulated i.i.d. data. Both are
documented as worked examples of how false discoveries are produced; both were caught
before any real-data claim was made.

Applied results: `docs/CASE_STUDY_1_PCSO.md §3` (dynamical), `§6` (Per Bak).

---

### Statistical face (cards 1–5)

**Card 1 — LLN / CLT** (ledger rows 1, 19): every z-score in the project rests on the
CLT; under H₀ sample frequencies converge to 6/P and standardized counts are
asymptotically N(0,1). Null functional: excess kurtosis of block means → 0. The
CLT-as-RG-fixed-point view connects this card to the universality analysis: block-mean
kurtosis flow at k=1–16 is the empirical test. *Role: calibration baseline. Blind to
dependence structures that preserve marginals.*

**Card 2 — Chi-square + exact Monte Carlo** (ledger row 1): detects marginal frequency
non-uniformity (hot/cold balls). Asymptotic chi-square is invalid at low expected counts
under 6-without-replacement sampling; replaced by exact MC under the true mechanism.
*Role: marginal-uniformity instrument. Blind to all structure that preserves uniform
marginals — the reason the other four faces exist.*

**Card 3 — Permutation tests** (ledger row 2): assumption-free covariate correlation
tests; null is exchangeability of the draw–covariate pairing. Within-game z-scoring is
required to fix a pooling problem (Simpson-type confound across games with different
number ranges). *Role: covariate association instrument. Blind to associations orthogonal
to the chosen statistic and to autocorrelation within a single series.*

**Card 4 — Scan statistics / look-elsewhere** (ledger row 10): Kulldorff-style maximum
windowed z-score over all numbers, window lengths, and games, calibrated by MC over the
full search. Distinguishes a locally extreme observation (global null) from a persistent
anomaly (rolling-window alternative). *Role: look-elsewhere correction. Blind to diffuse,
non-localized departures.*

**Card 5 — Multiple comparisons** (ledger rows throughout): Bonferroni/BH applied with
equivalence-class accounting — m counts hypothesis classes (|r| > 0.90 on simulated data
⇒ same class), not raw statistics. Family sizes: m = 9 (confirmation battery), m = 15
(Markov family), m = 18 (scaling-law family). *Role: multiplicity control. Blind when m
undercounts paths actually explored.*

Applied results: `docs/CASE_STUDY_1_PCSO.md §2`.

---

### Dynamical face (cards 6–8, 12)

**Card 6 — Markov chains / order tests** (ledger row 4): order-0 vs order-1 likelihood-
ratio G-test; overlap/stickiness; tercile G-test; |λ₂| relaxation time. Under H₀ the
transition rows all equal the stationary distribution. Distinguishes the Markov property
from i.i.d.: failure to reject order-0 vs order-1 bounds one-step memory, not all memory.
*Role: short-memory instrument. Blind to higher-order or long-range dependence.*

**Card 7 — Hurst / R/S analysis** (ledger row 12): long-range memory instrument. Null
H = 0.5 asymptotically, but the R/S estimator is biased upward on short series —
calibration against a same-length i.i.d. null is therefore mandatory (pseudo-critical
artifact 1 of 2). *Role: long-memory instrument. Blind to short-memory structure with
fast mixing and to dependence that leaves second moments untouched.*

**Card 8 — Doob optional stopping** (ledger row — decision gate): if the game is fair,
E[wealth at any stopping time] ≤ initial wealth for any betting strategy. No betting
schedule, stake sizing, or stopping rule has positive expected profit under a
supermartingale. *Role: detection-to-action gate. Not a detector; blind to strategies
that genuinely flip the sign of per-bet EV.*

**Card 12 — Wiener–Khinchin / Fisher g** (ledger row 8): spectrum and autocovariance
are a Fourier-transform pair (one equivalence class, not two tests); Fisher's exact
g-test gives a look-elsewhere-correct test for hidden periodicities. Null: flat
periodogram, g follows the exact alternating-binomial distribution. A flat spectrum
certifies zero autocorrelation at all lags (second-order only); compression covers
nonlinear dependence the spectrum misses. *Role: spectral / periodic-structure instrument.*

Applied results: `docs/CASE_STUDY_1_PCSO.md §3`.

---

### Algorithmic face (cards 10, 15)

**Card 10 — Shannon / Kolmogorov compression** (ledger row 6): the master instrument.
Incompressibility via Martin-Löf randomness is the one property equivalent to H₀: any
computable structure reduces entropy rate and admits compression. The entropy floor
(H = log₂ C(P,6) per draw) makes prediction impossible in principle. Practical test uses
raw DEFLATE versus identically processed simulated nulls. *Role: master certificate.
One-sided only: failure to compress proves nothing absolute for structure outside the
compressor's model class.*

**Card 15 — Covering designs** (ledger row — combinatorial bound): pure combinatorics,
no probabilistic assumptions. Cushing–Stewart (arXiv 2307.12430) proved L(59,6,6,2) = 27
via Fano planes. Disjoint-pair rule: two disjoint tickets give jackpot probability exactly
2/C(n,6) — coverage cannot create expected value. *Role: combinatorial bound instrument.
Not a detector; answers "cheapest guarantee of a t-match."*

Applied results: `docs/CASE_STUDY_1_PCSO.md §4`.

---

### Cross-sectional / physical face (cards 11, 13–14, 17–19, 26)

**Card 11 — Marchenko–Pastur / Tracy–Widom** (ledger rows 7, 17): RMT eigenvalue bulk
applied to co-occurrence correlation matrices. Meta-check: the simulated null distribution
of λ_max tracks TW-GOE universality — universality governs the lab's own noise floor,
not the mechanism under study. *Role: linear cross-sectional structure detector. Blind
to nonlinear or higher-order dependence and to time structure.*

**Card 13 — Per Bak SOC & universality** (ledger rows 12, 15–20): the full
methodological treatment is in the dedicated subsection below.

**Card 14 — Power laws / CSN / Zipf / Taylor / Benford** (ledger rows 16, 21–25): CSN
MLE + Vuong test on gap and avalanche distributions. Zipf slope is chi-square in disguise
(one equivalence class, not a separate test). The exact uniform-derived digit law differs
from naive Benford — correct null matters. *Role: tail-structure instrument. Blind to
light-tailed structure and to dependence that leaves marginal tails geometric.*

**Card 17 — Szemerédi / Furstenberg APs** (ledger row 28): density alone forces
arithmetic progressions (the Ramsey trap) — any top-k hot-number set must contain APs
at a theorem-forced baseline rate, independent of any bias mechanism. Two-sided MC-
calibrated AP counts within draws and hot sets. *Role: blind-spot coverage for additive
structure. Blind to non-AP structure.*

**Card 18 — Graphons / cut norm** (ledger row 27): spectral norm of centered
co-occurrence matrix as a proxy for the graphon cut distance; null graphon is constant
W ≡ c under i.i.d. uniform. C9 row-trace duty: any flag must be checked for overlap with
known anomaly driving rows before a new detection is declared. *Role: community-structure
instrument.*

**Card 19 — Concentration / sparse recovery** (ledger row 26): the lab's only exclusion
instrument. Simultaneous Hoeffding/MC band converts non-detection into the strongest
honest statement: any persistent per-ball bias exceeds ε with probability < 5%, at
ε ≈ 0.15–0.20 for n = 155–776. Caveat: ε is vacuous at feasible n as an EV constraint.
*Role: exclusion certificate. Blind to temporal and combinatorial structure with exact
uniform marginals.*

**Card 26 — Matrix completion / compressed sensing** (ledger row 38, relational face):
low-rank / sparse reconstruction as assumption-checking; held-out RMSE versus marginal-
baseline and permuted-entry nulls. On full-rank / i.i.d. data the solver sits on the
null line — the registered expected outcome from the entropy floor. *Role: relational
null-check instrument.*

Applied results: `docs/CASE_STUDY_1_PCSO.md §5`.

---

### Per Bak / SOC & universality — methodological treatment (card 13)

**Sources**: `docs/kb/per-bak-soc-universality.md`, `docs/THEOREM_SYNTHESIS.md §5b`,
ledger rows 12, 15, 16, 17, 18, 19, 20.

SOC (Bak, Tang, Wiesenfeld 1987) asserts that certain driven dissipative systems
self-tune to a critical point, displaying power-law avalanche distributions P(s) ~ s^−τ,
1/f^α power spectra, and long-range correlations H ≠ 0.5. The universality / RG
framework predicts that near a critical fixed point observables collapse onto universal
scaling functions, block statistics flow under the RG map, and the Binder cumulant
U = 1 − ⟨m⁴⟩/(3⟨m²⟩²) is scale-invariant (curves for different system sizes cross);
off-critical systems flow to trivial fixed points.

**SOC signature suite design:** the suite tests all three classical SOC signatures —
spectral slope (1/f^α), avalanche size distributions (power-law vs geometric Vuong test),
and long-range memory (Hurst R/S). Each is calibrated against the same-shape H₀ null
before any real-data interpretation. This calibration step is mandatory because all three
estimators exhibit finite-sample bias under i.i.d. data.

**The two preconditions test logic:** universality-class identification requires (1)
evidence of criticality (exponential tails refute it; Vuong test against geometric is
the discriminating instrument) and (2) a measurable scaling range (≥ 2 decades of
power-law behavior; anything less makes exponent estimation unreliable by construction).
Both are pre-checked before any universality-class claim is made.

**The fixed-point-identification upgrade:** when both preconditions fail, the analysis
does not stop at "no criticality found." The RG toolkit (data collapse across system
sizes, RG flow via block-mean kurtosis at k = 1–16, Binder cumulant scale invariance)
is run on all ensembles to identify which fixed point the system actually occupies. This
upgrades the verdict from an absence claim to a positive identification. The trivial /
Gaussian fixed point and the critical / power-law fixed point are the two possible
outcomes; both are detectable by the suite.

**The universality inversion as a principle:** even when the dataset is not critical,
universality governs the lab's own instruments. The RMT eigenvalue bulk follows
Tracy–Widom universality; every z-score rests on CLT / Gaussian-class universality;
the scan statistic's null follows Gumbel extreme-value universality. This is not a
result of the case study — it is a structural property of the framework.

Applied results (empirical numbers for the PCSO dataset): `docs/CASE_STUDY_1_PCSO.md §6`.

---

### Relational face (cards 20–26 / R1–R7)

**Card 20 — MMD / energy distance (R1)** (ledger row 29): kernel two-sample test
(pool-and-relabel null) detecting distributional differences across datasets sharing a
feature space. Admitted: FPR calibrated at tested shapes; power 1.00. *Role: distributional
difference detector. Equality of distribution ≠ relatedness — a critical asymmetry noted
in the card. Blind to structure not expressed in the chosen kernel.*

**Card 21 — Gromov–Wasserstein (R2)** (ledger row 37): alignment of metric-measure
spaces without shared coordinates. Always returns a coupling; only its position in a
matched-null distribution is evidence. Admitted at n=200 gate (FPR 0.055); demoted to
exploratory-only G0 because p-distribution was non-uniform (lattice χ² p = 0.002) —
the instrument the lab built failed its own calibration check and was immediately
demoted. *Role: cross-space alignment instrument. Status: G0, exploratory-only pending
null redesign.*

**Card 22 — CCA family (R3)** (ledger rows 31, 36): held-out canonical correlation of
draw features vs date-paired covariates. In-sample ρ̂ is never evidence (RMT inflation;
held-out only). Positive control confirmed: known physical mechanism returned held-out
ρ₁ = 0.9977, p = 0.005 (floor), verifying the pipeline. *Role: cross-dataset
correlation instrument. Blind to nonlinear associations.*

**Card 23 — TDA / persistence distances (R4)** (ledger rows 33–34): delay-embedded
topology — H₁ loops in structured series, flat for unstructured. Tidal loop recoverable
from 20% landmarks. The FN-3 miss in the blind methodology eval (a cycle under different
delay parameters) is documented as an instrument-representation limit, not a false null.
*Role: topological structure instrument.*

**Card 24 — Graph matching / spectra (R5)** (ledger row 32): pairwise co-occurrence
spectra across all game pairs (m = 99); degree-preserving rewiring null (Erdős–Rényi
forbidden as sole control). C9 row-trace duty applies. *Role: graph spectral alignment
instrument.*

**Card 25 — Coresets / landmarks (R6)** (ledger row 30): subset-to-whole recovery
curves (k-NN on time index; within-series permutation null; 10 seeds × m = 49). The
relational form of the entropy floor: structured series rise strongly (registered
positive controls); i.i.d. series are flat. *Role: subset-recovery instrument.*

**Card 26 — Matrix completion / compressed sensing (R7)** (ledger row 38 admission):
SoftImpute nuclear-norm minimization. Prediction from the entropy floor: completion sits
on the null line; flat recovery curve is the registered expected outcome. Admitted (FPR
calibrated, power demonstrated on planted low-rank data). *Role: low-rank structure
instrument.*

Applied results: `docs/CASE_STUDY_1_PCSO.md §7`.

---

### Decision face (cards 8–9, 16)

**Card 8 — Doob optional stopping** (see dynamical face): the detection-to-action gate.

**Card 9 — Kelly criterion / St. Petersburg** (ledger row — decision sizing): log
utility resolves the St. Petersburg paradox (Bernoulli 1738); Kelly (1956) gives the
growth-optimal stake f* = p − q/b. Decision ordering: Doob gates → EV measures → Kelly
sizes. All detection instruments null ⇒ f* = 0. *Role: stake-sizing instrument. Blind to
whether an edge exists at all — that is the statistical layer's and Doob's job.*

**Card 16 — Expected value / Stern–Cover** (ledger row 14): hypergeometric tier EV
decomposition with Poisson co-winner correction E[J/(1+K)] where K ~ Poisson(λ).
Payout-relevant backtesting (not proxy metrics) was decisive for evaluating generative
models. *Role: EV measurement instrument. Blind to risk preferences (Kelly's job) and to
whether an edge exists (statistical layer + Doob).*

Applied results: `docs/CASE_STUDY_1_PCSO.md §10`.

---

## Equation discovery — Phase 5

Source: `docs/EQUATION_DISCOVERY.md`, `docs/RUNBOOK.md` Phase 5. Added 2026-06-11
as a new pipeline phase between CONFIRM (Phase 4) and DECIDE (renumbered to
Phase 6). The lab can derive **statistically validated candidate equations or
generative models** for detected structures. It does not automatically discover
true governing laws.

### Hard gate: STRUCTURED claims only

Equation discovery consumes only confirmed STRUCTURED verdicts, post-freeze, with
driving-row/variable attribution on file. Anything else returns
`NO_EQUATION_ATTEMPTED` — the lab never searches for equations in unvalidated
data. This preserves A7 (each layer answers its own question). The gate is
demonstrated in practice: a request to fit marginal-bias coefficients to PCSO
6/49 (a NULL-verdict series) was refused without loading the dataset
(`docs/RESULTS_EQ_pcso-649-marginal.md`), because every fitted |δ̂ᵢ| would sit
below the card-19 detectability floor — noise dressed as a coefficient.

### Equation families

Eight candidate families, each grounded in instruments the lab has already carded
(no new mathematics to fit; what is new is the selection-and-validation contract):

| Detected structure | Candidate equation family | Card(s) |
|---|---|---|
| Marginal bias | probability-weight law, Σδᵢ = 0 constrained | 1, 2, 19 |
| Memory / temporal dependence | Markov / autoregressive, kα+(P−k)β = k constrained | 6, 7 |
| Periodic cycle | harmonic regression (sin/cos pairs per harmonic) | 12 |
| Regime shift | piecewise / changepoint | 4 |
| Low-rank matrix | factorization M = UVᵀ | 11, 26 |
| Graph community | stochastic block model | 24, 25 |
| Topological loop | latent-phase parameterization θ_t ∈ [0, 2π) | 23 |
| Shared latent relation | latent-variable model | 22, 21 |

Symbolic regression / SINDy and structural causal equations are explicitly out of
scope until onboarded with their own A1 null generators.

### Selection-and-validation contract

Every equation search is registered before fitting (candidate families, splits,
nulls, complexity penalty λ, multiplicity charge — human-approved and hashed into
the commitment ledger), then selected by MDL subject to held-out skill:
J(f) = L_heldout(f) + λ·complexity(f). The key A1 addition is the
**null-equation generator**: the identical discovery procedure is run on matched
synthetic nulls, because equation searches on pure noise *return equations* —
only the null distribution of recovered-equation scores converts "we found an
equation" into a calibrated p-value. Acceptance additionally requires bootstrap
parameter stability, residual checks (§8: autocorrelation, Fisher g, MMD,
changepoints, TDA, compression), coefficients above the card-19 floor, and
per-regime / per-era coefficient reports (M4).

### Verdict ladder

| Verdict | Meaning |
|---|---|
| NO_EQUATION_ATTEMPTED | source claim not STRUCTURED, or family not registered |
| CANDIDATE_EQUATION | descriptive fit exists (level 1) |
| PREDICTIVE_EQUATION | beats matched nulls on held-out data (level 2) |
| MECHANISM_SUPPORTED | stable, interpretable, externally corroborated |
| GOVERNING_LAW_CONFIRMED | fresh-data confirmation + mechanism evidence (level 3) |
| FAILED_EQUATION_SEARCH | structure confirmed but no compact equation passed validation — a publishable result |

Doob separation holds: even a PREDICTIVE_EQUATION confers no action license;
Phase 6 still gates. Equation verdicts never upgrade a detection verdict.

### Calibration record (runs to date)

The layer was first deployed on physical positive controls with externally known
governing rules — mirroring how the blind 9-series eval validated the detection
layer before it was trusted:

| Run | Target | Verdict | Calibration outcome |
|---|---|---|---|
| eq.tidal v1–v2 (`RESULTS_EQ_TIDAL.md`, `_V2.md`) | total tidal acceleration | FAILED_EQUATION_SEARCH | anomalistic month recovered (27.487 d, 0.25% err); spring–neap missed; surrogate null not beaten (p = 0.194) |
| eq.tidal v3 fine-grid (`RESULTS_EQ_TIDAL_V3.md`) | residual-line adjudication | FAILED_EQUATION_SEARCH | leakage hypothesis registered, tested, and **logged dead**; 5 unattributed refined lines published as a discovery-grade anomaly in ephemeris-derived data; any v4 gated on human review |
| eq.moondist v1–v2 | Moon distance | FAILED_EQUATION_SEARCH | period recovery PASS (27.604 d, CI ∋ 27.555 d anomalistic month); structured residuals blocked the verdict |
| eq.moondist confirm1 (`RESULTS_EQ_MOONDIST_CONFIRM1.md`) | Moon distance, fresh data | **MECHANISM_SUPPORTED — the lab's first** | the frozen v2 equation (hashed before the data existed, zero free parameters, no refit) forecast 86 strictly post-freeze JPL Horizons rows inside every registered gate (RMSE ratio 1.273× vs the declared 1.5× envelope) |
| eq.pcso-649 marginal (`RESULTS_EQ_pcso-649-marginal.md`) | PCSO 6/49 δ coefficients | NO_EQUATION_ATTEMPTED | hard gate held: NULL source claim, no registration, no attribution — no fit performed |

Agent routing: **equation-analyst** (`agents/equation-analyst.md`) designs and
fits; the independent-verifier checks recovered parameters against known ground
truth; the equation-analyst instance for a claim is never the structure-analyst
instance that detected it.

---

## Verification and integrity stack

### Numeric verifier: `src/verify_relational_docs.py`

Mechanically re-derives every documented number from its source JSON and checks all six
sections of the relational results. Current verdict: all 6 sections green. The script
is run as part of every dispatch and its output is the first item in the verifier's
report.

### Design verifier: `src/design_verifier.py`

Enforces structural properties of the claim-instrument mapping before any result is
published:
- **Claim-type ↔ method mapping**: each registered claim is of a declared type
  (subset-to-whole, cross-dataset similarity, latent-sharing, topological,
  distributional, marginal, memory, stationarity); the method must match.
- **Permutation floor rule**: p_floor ≤ α_corrected / 2 for every registered family.
  This rule caught a borderline λ_max case and forced a rerun at higher resolution —
  where the flag closed.
- **Sensitivity-regime presence**: three-regime reporting (all / ex-suspicious /
  verified-only) required for any claim touching data with flagged rows.

Current verdict: **PASS, 0 violations** (111 historical warnings resolved).

### Domain-neutrality lint: `src/lint_domain_neutrality.py`

Ensures domain vocabulary is confined to `src/domains/<domain>.py`, frozen historical
records, domain datasets/results, and domain deliverables. Current verdict: **PASS,
16 files clean** (source: `docs/SANITIZATION.md`).

### n=200 calibration gates

All instrument families are re-gated at n=200 before any real-data run that will
produce a publishable verdict. Gate mechanics: 500 simulated H₀ datasets of the real
data's exact shape; FPR must sit within 3-SE of α; p-distribution must be uniform
(KS test). The quarter-shape gate passes (FPR 0.035, KS p=0.20); the GW gate fails
(source: `docs/REMEDIATION_LOG.md M2`).

### Commitment devices

- **git baseline commit `e1bc32b`**: the first anchored state; all prior
  "registrations" are explicitly labeled retroactive in the run ledger (source:
  `docs/REMEDIATION_LOG.md C1` and `results/run_ledger.jsonl`).
- **Append-only hash ledger** (`results/commitment_ledger.txt`): SHA-256 of every
  doc, script, and result file, snapshotted after each batch. Registrations are
  committed to the ledger before their run scripts execute. The blind-eval verdict hash
  `1d0a4d3ed4d2dd4d` was committed before the answer key was unsealed (verified by
  recompute in `results/blind_eval_score.md`).
- **Owner action pending**: host-side `git commit` to anchor the ledger to version
  control (the sandbox cannot issue git commits).

---

## Four-level ledger system

| Ledger | Location | Content |
|---|---|---|
| Results ledger | `docs/THEOREM_SYNTHESIS.md §5` | 40 rows: every instrument, functional, H₀ value, observed value, corrected p |
| Run ledger | `results/run_ledger.jsonl` | 10 runs: script, seed scheme, executor identities, grade, output SHA-256 |
| Multiplicity ledger | `results/multiplicity_ledger.jsonl` | 173 real-data tests, one row per test: claim type, method, raw p, m_perm, p_floor, family ID, data filter |
| Commitment hash ledger | `results/commitment_ledger.txt` | SHA-256 of every doc/script/result at each batch snapshot; blind-eval commitment chain |

**Meta-uniformity panel** (source: `results/meta_uniformity.json`): across the 126
lotto-side real-data p-values from the relational batches, KS vs uniform p = 0.385,
6.3% ≤ 0.05, 0.8% ≤ 0.01 — globally consistent with honest null testing. Physical-
series positives excluded by design (they are positive controls, not null tests).

**Note on the 173 vs 126 figures**: the multiplicity ledger contains 173 real-data
tests total; the meta-uniformity panel covers the 126 lotto-side tests (the 47 excluded
are physical-series confirmatory positives and cross-executor verification runs with no
null hypothesis).

---

## Agent system

Source: `docs/AGENT_WORKFLOW.md`, `agents/evals/EVAL_SET.md`.

### Agent roster

| Agent | Role | Phases | Primary model | Escalation |
|---|---|---|---|---|
| `lab-orchestrator` | routes phases, enforces gates + role-ID separation, maintains run ledger; produces nothing itself | all (coordination only) | **Fable** | fable → opus; never below |
| `research-scout` | literature, canonical references, dataset sources, prior art | 0 (sourcing) | **Sonnet** | sonnet → opus (contested literature) |
| `data-reader` | file extraction, row audits, schema checks, result-JSON lookups; read-only, no interpretation | 0–5 (support) | **Haiku** | haiku → sonnet (ambiguous formats) |
| `theorem-dataset-onboarder` | cards theorems, onboards datasets (gate-checked, clerical) | 0–1 | **Haiku** | haiku → sonnet → opus → any LLM + human diff |
| `structure-analyst` | null design, instrument implementation, real-data runs, attribution, multiplicity | 2–4 | **Fable** (design); **Haiku** (execute-only re-runs) | design: fable → opus → sonnet; execution: haiku → any LLM execute-only |
| `equation-analyst` | derives candidate equations for confirmed STRUCTURED claims: family registration, null-equation generator, constrained fits, MDL selection, residual checks, equation verdicts; never detects, never decides | 5 | **Fable** (design/interpretation); **Haiku** (execute-only fits) | design: fable → opus → sonnet; execution: haiku → any LLM execute-only |
| `docs-web-editor` | generates RESULTS docs, figures-from-JSON, ledger sync, web pages; numbers copy-only | 5 | **Sonnet** | sonnet → opus (narrative restructuring) → human diff review |
| `independent-verifier` | numeric + design verification, reproduction diffs, blind replication, ledger reconciliation; never verifies own authorship | all (after each) | **Haiku** (numeric) / **Sonnet** (design) | identity rule has no fallback: a different instance than the author, always |

**Role-ID separation** is mechanical and recorded per run in `results/run_ledger.jsonl`:
`onboarder_id != analyst_id`, `analyst_id != verifier_id`, `editor_id != analyst_id`,
`verification_executor != script_author`, `equation_analyst_id != detection_analyst_id`
(per claim: the detector never fits its own equations). A run missing these fields, or violating them,
is unpublishable.

**Replay and audit**: every dispatch produces a `results/agent_runs/<run_id>/` directory
containing `prompt.md` (saved before dispatch), `agent.txt` (identity), `report.md`
(verbatim return), `files.txt` (diff), and `grade.json` when the dispatch is an eval.
All analysis scripts are deterministic with fixed seeds; replaying a run = re-executing
the named script; byte-identical output is the pass condition.

**Eval suite**: 12/12 PASS (source: `agents/evals/EVAL_SET.md`). One real pipeline bug
found by eval A-2: a stale meta-uniformity panel (inputs changed post-build); the panel
was refreshed and the correct KS p = 0.385 was published. Evals V-1, V-2, V-3, D-1,
D-2, A-1, A-2, O-1, R-1, E-1, X-1, X-2. Two evals (X-1, X-2) carry a human-review
grading caveat (graded by orchestrator-builder, not an independent agent).

---

## Independently verified performance

### Blind 9-series verification (source: `results/independent_verification.json`, `docs/REMEDIATION_LOG.md C2`)

A separate agent, barred from lab code, documentation, and any prior results, was given
9 standardized series with neutral names and no dates. The agent implemented its own
test suite and applied its own decision rule (Bonferroni 0.05/4 across 4 statistics, or
≥ 2 tests with raw p < 0.05). Result: **9/9 concordance** — all 4 physical series
returned STRUCTURED, all 5 lotto series returned NO DETECTED STRUCTURE. Conducted
expectation-free. Details and replication numbers: `docs/CASE_STUDY_1_PCSO.md §9`.

### External blind methodology benchmark: structure_eval_set_v1

Source: `results/blind_eval_score.md`. 68 registered claim units across 16 claim
families, drawn from 14 synthetic dataset objects. The answer key was sealed in the
commitment ledger (hash `979b75a420b01952`) before analysis began; lab verdicts were
committed (hash `1d0a4d3ed4d2dd4d`) before the key was unsealed; scoring was conducted
by an independent-verifier agent that did not run the analysis. Role separation
recorded in `results/run_ledger.jsonl` run `blind_methodology_eval_v1`.

**Results:**

| Metric | Value |
|---|---|
| True Positives | 19 |
| True Negatives | 45 |
| False Positives | 0 |
| False Negatives | 4 |
| Sensitivity | 0.826 |
| Specificity | 1.000 |
| Accuracy | 0.941 |

Zero false positives: the permutation-based nulls, Šidák family corrections, and
Phipson–Smyth +1 floors held without exception even when several null excursions reached
raw p = 0.01–0.03. The 4 misses are documented with honest descriptions in
`results/blind_eval_score.md §5`; all four are instrument-representation or
family-size-threshold limits, not false nulls on genuinely structured data.

---

## Evidence-grade ladder G0–G6

Source: `docs/RESPONSE_EXTERNAL_REVIEW.md`.

| Grade | Meaning | Current holders |
|---|---|---|
| G0 | exploratory, no claim | GW real-data pairs (post-demotion); 6/45 watch item |
| G1 | calibrated instrument | R1–R7 (FPR-calibrated at tested shapes; GW G1 with standing distribution-calibration flag) |
| G2 | internal result, registered-ish | most batch 5–7 results; pressure covariate results |
| G3 | auditable registration | none retroactively; future batches via hash ledger + host git |
| G4 | independent reproduction | series-level structure/null verdicts for all 9 blinded datasets (blind 9/9); 6/55 half-corr sensitivity (replicated to 3 decimals); blind methodology eval (68-unit benchmark, role-separated) |
| G5 | held-out confirmation | none (confirmation family untouched, by design) |
| G6 | decision-grade | the *refusal* decision (no betting edge) — asymmetric: declining to act requires less evidence than acting; rests on Doob + entropy floor + uniformly null G2–G4 evidence |

---

## Domain architecture

Source: `docs/SANITIZATION.md`.

```
src/core/          # domain-neutral instrument library (stats, discrete_draws,
                   # recovery, paired, geometry, graphs, completion)
src/domains/       # one file per domain (currently: pcso_lotto.py)
src/               # 21 frozen historical scripts — reproduce ledger rows 1–39;
                   # stamped FROZEN HISTORICAL RECORD; do not rewrite
datasets/          # per-domain datasets with DATASET.md cards
results/           # ledgers, JSONs, figures
agents/            # agent definitions + eval set
evals/             # eval suites (structure_eval_set_v1)
docs/              # governance, runbook, KB, results docs
```

`src/core/` provides the forward-facing API for all new experiments. Domain vocabulary
(`src/domains/pcso_lotto.py`) contains: draw-ensemble registry, loaders with data-quality
regimes, covariate bundle, ANOMALY_REGISTRY (C9 row-trace duties), ERA_REGISTRY (A5).
`src/lint_domain_neutrality.py` must PASS before any results doc is published.

**Adding a new domain**: create `src/domains/<domain>.py` with the same interface
(ensemble registry, loader, covariate bundle, ANOMALY_REGISTRY, ERA_REGISTRY), onboard
the dataset per `THEOREM_GOVERNANCE.md Part 4`, and run the three verifiers
(numeric + design + lint). All instruments, nulls, gates, ledgers, and agents work
unchanged. For financial data the mission inverts: H₀ rejections are expected (heavy
tails, volatility clustering, factor structure); the framework's anti-self-deception
machinery matters most in attribution and net-of-costs survival testing.

---

## Module: riemann-zero-lab (deterministic mathematics)

Source: `riemann-zero-lab/README.md`. Added 2026-06-13 — the lab's first **deterministic-
mathematics** module. Instead of testing stochastic data for structure, it locates and verifies
zeros of the Riemann zeta function ζ(s). It is **numerical discovery, never an RH proof**: RH is
an infinite statement; the module touches finitely many zeros (`riemann-zero-lab/docs/kb/riemann-hypothesis.md`).

**Batch 1** located and verified the first **200 non-trivial zeros** on the critical line
(Hardy Z-function sign-change bracketing, mpmath dps=80): residuals ≤ 3.1e-47, precision-stable
to 56–60 digits, two-run byte-identical. The located count equals N(T), `mpmath.nzeros`, and a
contour argument-principle integral (no zero missed up to height ≈ 397 — a *finite* check, not
RH). Unfolded nearest-neighbour spacings are decisively **non-Poisson** and **GUE-like**
(KS D_GUE = 0.07 vs D_Poisson = 0.35), reported as descriptive at N = 199.

**Why it fits the constitution (C11 / A8).** A1's "every null is Monte-Carlo-derived" is
undefined for the *existence* of a zero — nothing random to resample. Conflict **C11** records
this; article **A8 (deterministic-certificate substitution)** resolves it: deterministic claims
are admitted on a three-leg certificate (exact computation to a declared tolerance, independent
recomputation by a different instance, analytic invariant cross-check count = N(T) = contour
integral), while the MC-null discipline (A1–A7) governs the one genuinely stochastic layer — the
spacing-vs-Poisson comparison — unchanged. A methodology-change eval slice
(`agents/evals/EVAL_SET.md` §Z: Z-V1/Z-V2/Z-O1) confirmed the verification and onboarding gates
transfer: **3/3 PASS**.

Same discipline as the rest of the lab — cards-first (`riemann-zero-lab/docs/kb/INDEX.md`, 7
cards), registration committed before the first result run, JSON-from-scripts /
results-from-JSON, role-separated independent verification, adversarial-review section, and a
run-ledger row. Start at `riemann-zero-lab/README.md`.

---

## Repository guide

### Framework documents (domain-agnostic, reading order)

1. **docs/RUNBOOK.md** — the 7-phase workflow (Phases 0–6, including Phase 5
   equation discovery) + failure-mode gallery + domain-porting guide
2. **docs/EVALUATION_PROTOCOL.md** — formula-level spec (E0–E9 evaluation, H1–H7
   harmonization); the deterministic guide for human or LLM executors
3. **docs/THEOREM_GOVERNANCE.md** — conflict registry C1–C11, harmonization constitution
   A1–A8 (A8 = deterministic-certificate substitution), theorem onboarding (Part 3),
   dataset onboarding (Part 4)
4. **docs/THEOREM_SYNTHESIS.md** — the theory map: five faces of structure, the
   implication lattice, instrument correlation, the 40-row results ledger
5. **docs/CROSS_DATASET_FRAMEWORK.md** — the relational extension (fifth face):
   cross-dataset similarity/alignment and subset-to-whole recovery (D = S ∪ H), folded
   onto the same constitution (A1–A7). Method-by-case taxonomy, matched relational
   nulls, 9-experiment benchmark suite, decision tree, recovery curve.
6. **docs/RELATIONAL_RUNBOOK.md** — the relational experiment protocol: Phase 0
   (registration, expectation-free), Phase 1 (admission), Phase 2 (run), Phase 3
   (verification)
7. **docs/REMEDIATION_LOG.md** — all adversarial-review findings and their dispositions;
   the protocol change history
8. **docs/RESPONSE_EXTERNAL_REVIEW.md** — external review findings, G0–G6 ladder
9. **docs/SANITIZATION.md** — domain-neutral refactor record
10. **docs/AGENT_WORKFLOW.md** — model-routed agent execution: 8-agent roster, role-ID
    separation, replay mechanics, eval gate
11. **docs/EQUATION_DISCOVERY.md** — Phase 5 specification: STRUCTURED-only gate,
    equation families, registration contract, null-equation generator, verdict ladder
12. **docs/LAB_IMPROVEMENT_PLAN.md** — prospective reliability and accuracy program:
    executable registrations, calibrated nulls, sequential error control, provenance,
    independent verification, and measurable delivery gates
13. **docs/kb/** — 26 theorem/methodology cards + INDEX
14. **admin_onboarding.html** — gate-checked wizard for new theorems and datasets

### Case study

- **docs/CASE_STUDY_1_PCSO.md** — Case Study 1 (PCSO lottery draws): full per-face
  results, anomaly adjudication, external validations, decision layer, ethics note,
  links to all results documents and ledgers

### Case Study 1 artifacts (PCSO lottery)

- **docs/RESEARCH_NOTES.md** — full evidence log: every test, p-value, correction,
  and the adversarial-review trail
- **docs/RESULTS_RELATIONAL_FIRSTRUN.md**, **RESULTS_BATCH4.md**, **RESULTS_BATCH5.md**,
  **RESULTS_BATCH6.md**, **RESULTS_PRESSURE.md** — batch-by-batch relational results
- **docs/RESULTS_EQ_TIDAL.md**, **RESULTS_EQ_TIDAL_V2.md**, **RESULTS_EQ_TIDAL_V3.md**,
  **RESULTS_EQ_MOONDIST_CONFIRM1.md**, **RESULTS_EQ_pcso-649-marginal.md** — Phase 5
  equation-discovery runs (registrations in **docs/REGISTRATION_EQ_*.md**)
- **datasets/pcso-lotto/** — DATASET.md card + canonical/audited/provenance CSVs
- **datasets/tidal-manila/**, **datasets/jpl-horizons-sun-moon/**,
  **datasets/gfz-kp-geomagnetic/**, **datasets/openmeteo-pressure-manila/** — covariate
  datasets (DATASET.md cards with single-source caveats where applicable)
- **results/commitment_ledger.txt** — append-only hash ledger (3 snapshots + blind-eval chain)
- **results/run_ledger.jsonl** — 10 run records with executor identities
- **results/multiplicity_ledger.jsonl** — 173 real-data test rows
- **results/meta_uniformity.json** — global meta-uniformity panel (KS p=0.385)
- **results/independent_verification.json** — blind 9/9 concordance + numerical replication
- **results/blind_eval_score.md** — 68-unit methodology benchmark (answer key sealed until
  verdict hash committed)
- **results/agent_runs/** — dispatch records for every agent eval and verification run

### Instrument scripts (domain-specific; frozen historical records; run from project root)

```bash
# Declared core deps, plus the instrument-script deps requirements.txt does not
# yet pin. The Run centre jobs (meta_panel/families/R5/TDA) import these, so a
# fresh setup needs them too. On an externally-managed interpreter (e.g. Homebrew
# Python — PEP 668) either work inside a venv, or append --break-system-packages.
pip install -r requirements.txt                # ephem, numpy, openpyxl
pip install scipy matplotlib pandas ripser     # scipy: R5/families · matplotlib: honesty-meter figure · pandas · ripser: persistent-homology (TDA)
# Verify the runtime deps are all importable before running jobs:
python3 webapp/test_lab_deps.py
python3 src/montecarlo_certification.py   # marginal uniformity + ensemble certification
python3 src/markov_analysis.py            # dynamical face: order-0 vs order-1
python3 src/structure_discovery.py        # algorithmic + cross-sectional: compression/RMT/spectra
python3 src/powerlaw_sweep.py             # scaling laws: Zipf, Taylor, first-digit, Levy, coverage
python3 src/perbak_soc_analysis.py        # statistical physics: SOC signatures
python3 src/universality_collapse.py      # data collapse, RG flow, Binder cumulant
python3 src/explore_batch2.py             # positional/calendar/pair/scan statistics
python3 src/cross_theorem_correlation.py  # cross-domain coupling detector
python3 src/review_response.py            # audit table, payout-relevant backtest, persistence
python3 src/markov_chain_model.py         # generative model + walk-forward evaluation
python3 src/relational_first_run.py       # relational: recovery curves + CCA
python3 src/relational_batch5.py          # cross-game spectra, delay topology
python3 src/relational_allgames.py        # all-games symmetry
python3 src/relational_subsets.py         # partition: quarters, halves
python3 src/relational_pressure.py        # pressure covariate baseline
python3 src/relational_batch7.py          # pressure seasons, GW first run
python3 src/remediation_r1.py             # full remediation batch (expectation-free)
python3 src/eq_tidal_v1.py                # Phase 5: tidal/moondist equation calibration v1
python3 src/eq_tidal_v2.py                # Phase 5: v2 (3-line family, surrogate nulls)
python3 src/eq_tidal_v3.py                # Phase 5: v3 fine-grid residual adjudication
python3 src/eq_moondist_confirm1.py       # Phase 5: fresh-data confirmation (MECHANISM_SUPPORTED)
python3 src/verify_relational_docs.py     # numeric verifier (all 6 sections)
python3 src/design_verifier.py            # design verifier (claim↔method, floor rule)
python3 src/lint_domain_neutrality.py     # domain-neutrality lint
python3 src/meta_uniformity.py            # global meta-uniformity panel
```

The scripts in `src/core/` (stats, discrete_draws, recovery, paired, geometry, graphs,
completion) are the forward-facing instrument API for new domains; they are not run
directly.

### Verifiers and evals

```bash
python3 src/verify_relational_docs.py     # PASS — all 6 sections green
python3 src/design_verifier.py            # PASS — 0 violations
python3 src/lint_domain_neutrality.py     # PASS — 16 files clean
python3 src/grade_agent_eval.py           # grades agent dispatch records
```

---

## Limitations

- **Retroactive registrations:** git baseline commit `e1bc32b` is the first genuine
  commitment device. All registrations prior to that commit are explicitly labeled
  retroactive in the run ledger and commitment ledger; they do not carry G3 grade.
- **Single primary case study:** the framework has been exercised on one dataset
  (PCSO lottery draws, Case Study 1). Transferability to other domains is supported by
  architecture (domain-neutral `src/core/`) but not yet empirically demonstrated.
- **G5 empty:** the confirmation family (m = 9, α' = 0.0056) has not been touched;
  no result currently holds G5 grade. This is by design, not an omission.
- **GW miscalibration:** GW (R2) is demoted to G0. Any analysis relying on GW alone
  is unpublishable until null redesign is complete.
- **Resolution bounds:** all "no structure found" verdicts are bounded by ε at tested n.
  ε ≈ 0.15–0.20 is vacuous as an EV constraint at feasible ticket counts. "At the tested
  resolution" qualifies every null result.
- **Single-source covariate:** Manila atmospheric pressure is ERA5/Open-Meteo only;
  positive pressure claims are gated until a second source is added.
- **Operating point — high specificity by design:** the lab is a conservative detector,
  not a maximum-sensitivity one. The blind methodology benchmark (source:
  `results/blind_eval_score.md`) confirms this empirically: 0 false positives across
  45 null slots with sensitivity 0.826 at the tested instrument set. The cost of the
  conservative operating point is deliberate — Šidák corrections and Phipson–Smyth +1
  floors absorb near-threshold signals rather than emit marginal claims. Near-misses and
  instrument-gap detections are tracked via the five-tier verdict taxonomy and the
  instrument roadmap; they do not count as STRUCTURED verdicts and are never cited in
  public claims. See `docs/RESPONSE_BLIND_EVAL_ADMIN.md` for the full admin review
  disposition and roadmap.

---

## Reviews and audits trail

`docs/ADVERSARIAL_REVIEW.md` is a self-adversarial review conducted before any external
examination; it identified the seven major findings (M1–M7) that drove the remediation
program. An external LLM review (`docs/EXTERNAL_REVIEW_BRIEF.md`) independently raised
overlapping concerns and introduced new items (evidence-grade ladder, design verifier,
multiplicity ledger, environment capture); the response (`docs/RESPONSE_EXTERNAL_REVIEW.md`)
adopts all of them with notes on any divergence. The remediation log
(`docs/REMEDIATION_LOG.md`) records what was done for each finding and its outcome —
including the GW gate failure (M2: the instrument the lab built itself failed its own
calibration check and was immediately demoted), the 6/45 flag opening and closing (M3:
a borderline estimate at insufficient resolution, closed when forced to higher resolution),
and the stale meta-uniformity panel caught live by eval A-2 (the A-2 eval re-ran a
script and found byte-level discrepancy; the panel was refreshed to KS p = 0.385).

---

*Protocol v2.1 · Jun 11, 2026*

## Web console (`webapp/`)

Local, zero-dependency console for the lab (Python stdlib only):

```
python3 webapp/server.py          # http://localhost:8787   (redesigned console)
python3 webapp/server.py --lan    # + phone access on the same Wi-Fi
```

Or just double-click **Start Lab Console.command** (macOS) — it starts the
server and opens the browser; close the Terminal window to stop.

The redesigned, Apple-style, mobile-friendly console is served at **`/`**; the
original console remains available at **`/classic`**. Nine views plus a pipeline
wizard: **Overview** with the lab's single next step, **Experiments** with PDF
export, **Equations** with a try-it sandbox (descriptive fits only — 0
multiplicity, never citable), a searchable **Theorems** arsenal (docs/kb), the
multiplicity **Ledger** + honesty meter, the **Run centre** for live agent/script
status, HUMAN-GATE **Approvals** (append-only audit log at
`results/webapp_approvals.jsonl`; fills blank `approved_by_human` lines), an
**Admin** page whose API keys live in `webapp/config.local.json` (gitignored,
masked when served), and a dynamic **Help** page with a live "lab at a glance"
and the protocol docs. Binds 127.0.0.1 only.
