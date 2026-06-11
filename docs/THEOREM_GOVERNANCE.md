# THEOREM GOVERNANCE — Conflicts, Harmonization, Onboarding

Companion to THEOREM_SYNTHESIS.md (what the theorems say) and RUNBOOK.md (the workflow).
This document covers what neither does: **how theorems collide, the constitution that
harmonizes them, and the protocol for admitting a new one.** Every conflict listed was
actually encountered in this project; none is hypothetical.

---

## Part 1 — Conflict registry (observed collisions between theorem families)

### C1. Asymptotic theorems vs finite data  *(severity: produced 3 false signals)*
Many theorems hold in limits the data never reaches: chi-square asymptotics need
expected counts ≥5 (ours: 4.0–5.4); Marchenko–Pastur edges assume T,P→∞ (literal edge
2.32–2.60 vs the correct finite-constrained null 2.27–2.47); R/S Hurst and Binder
cumulant estimators are biased at short series. **Collisions observed**: uncalibrated
Hurst read Ĥ=0.70 as long memory; Binder read U=0.5 as a critical plateau; both were
the estimator's finite-sample bias. The theorem was true; its asymptotic regime wasn't ours.

### C2. Competing nulls — two "laws" predicting different baselines
Benford's law and the uniform-derived digit law both claim to be "the" first-digit
expectation; they disagree (χ²=1312 apart on our data). KS theory assumes continuous
distributions; our discrete tied gaps made the KS statistic degenerate (p≡1.0
identically). **The conflict is not between theorem and data but between theorem and
the generative model**: each theorem's null must be *derived* from H₀, not imported
from the theorem's home domain.

### C3. Statistic equivalence — theorems wearing each other's clothes
Provably or near-provably equivalent statistics entered under different names:
T1 overlap ≡ T2 stickiness (monotone transform — identical p-values); Zipf slope ≡
chi-square dispersion; max-frequency ≡ a chi-square component; the Markov backtest's
6/55 edge ≡ the chi-square #45 excess. **Collision**: double-counting corrupts the
multiplicity budget both ways — inflating m makes thresholds unfairly strict, while
counting correlated flags as independent confirmations falsely "replicates" findings
(the #45 anomaly was flagged by NINE correlated statistics; it is one anomaly).

### C4. One-sided certificates vs two-sided tests
Compression (Kolmogorov) can only *detect* structure, never certify randomness (real
compressors are weak); chi-square is two-sided and powered. Treating "compression
passed" as equal evidence to "chi-square passed" overstates the former. Conversely:
if chi-square flags and compression doesn't, that is NOT a contradiction — it's a
power difference. **Collision type: verdicts of unequal logical strength read as votes.**

### C5. Pooled stationarity vs era structure
The full-year 6/55 chi-square (p=0.003) and the windowed persistence test (p=0.002)
vs the within-era tests (2026 half: p=0.10) appear to contradict. They don't: pooled
tests assume stationarity that the data violated (the Feb-2026 era boundary). A pooled
theorem applied across a regime change conflates eras — it can both *manufacture*
significance from a dead transient and *dilute* a live one. **Ergodic theorems and
era-bounded reality collide whenever ball sets, prize rules, or equipment change.**

### C6. Same anomaly, opposite verdicts under different alternatives
Scan statistic: hot-45 p=0.148 (alternative: a 30-draw burst). Rolling-window
persistence: p=0.002 (alternative: multi-quarter elevation). Same rows, defensible
methods, opposite-feeling conclusions. **Not a contradiction — different alternative
hypotheses have different look-elsewhere volumes** — but without governance it reads
as "the math disagrees with itself."

### C7. Decision-layer collisions: EV vs Kelly vs Doob
EV>0 says "the ticket is worth more than it costs"; Kelly says "stake ≈ 0 anyway"
(f* ≤ 1/C(n,6)); Doob says "no strategy exists at all." Superficially inconsistent
prescriptions. **Resolution is ordering, not adjudication**: Doob gates (is there an
edge to size?), EV measures (how big?), Kelly sizes (how much to commit?). Each theorem
answers a different question; conflict only appears when one is asked another's question.

### C8. Universality vs bias-hunting — the philosophical collision
Universality (CLT, Tracy–Widom, Gumbel) says microscopic details wash out of the
statistics; bias detection exists to find microscopic details. If detail washes out,
what are we hunting? **Resolution**: they govern different layers — universality fixes
the *null fluctuation laws* (what noise must look like); bias detection hunts
*deviations from those universal laws*. Universality is the courtroom, not the defendant.

### C9. Relational double counting — one anomaly, many faces *(added with the relational face)*
The 2025 6/55 #45 excess is a function of 26 draw rows. It has already been flagged by
six hit-count statistics (C3's worked example) and shadows into the graphon instrument
(ledger row 27, p=0.0005). Every relational instrument that consumes those rows —
cross-game graph comparison, draw-feature MMD, paired-covariate CCA — will re-detect it
and present it as a *new cross-dataset relationship*. **Resolution**: before any
relational flag is reported, trace it to driving rows (Part 3 Step 6); if the rows
underlie a known anomaly, the flag joins that anomaly's equivalence class and adds no
multiplicity-adjusted evidence. A relationship "between" datasets that disappears when
the known-anomaly rows are removed is a shadow, not a discovery. The #45 row-set is the
registered standing example; the trace-to-rows check is mandatory in the relational
checklist (CROSS_DATASET_FRAMEWORK §11).

### C10. Representation freedom as uncharged multiplicity *(relational form of C6)*
A dataset can be embedded, kernelized, graph-ified, delay-embedded, or filtered many
ways before any relational instrument touches it. Searching representations until a
relationship appears is the relational forking-paths error. **Resolution**: the
representation bundle R_i is declared per dataset *before* the run (registration), and
the A3 budget counts **representation × method × metric** classes, not raw tests. One
declared representation per claim; extras are charged.

---

## Part 2 — Harmonization constitution (seven articles)

**A1. One generative null, many lenses.** Every instrument's null distribution is
derived from the SAME constrained generative model (here: 6-without-replacement,
per-game, observed sequence lengths) by Monte Carlo — never from the theorem's textbook
asymptotics. *Dissolves C1, C2: asymptotic mismatch and imported baselines cannot
occur when the null is simulated, not assumed.*

**A2. Null-trial admission.** No estimator is admissible until it has been run on pure
simulated H₀ data and returned null. *Would have pre-empted every C1 casualty (Hurst,
Binder, KS-under-ties, 0.5-centered smoothing) before they touched real data.*

**A3. Equivalence-class accounting.** Statistics are grouped into equivalence classes:
provable monotone relations, or empirical null-correlation |r| > 0.9 (measured on
simulated data). The multiplicity budget m counts classes; flags within a class count
once; anomalies are identified by their DRIVING ROWS, not by which statistics noticed
them. *Dissolves C3 and the nine-flags-one-anomaly problem.*

**A4. Asymmetric verdict logic.** A flag from any admissible instrument defeats H₀
(pending replication); passes never outvote a flag; passes accumulate *scope coverage*
(which alternatives are excluded at what power), not proof. Every "pass" is reported
with its power: "no effect" is always "no effect ≥ size X detectable at this n."
*Dissolves C4: certificates of unequal strength stop being votes.*

**A5. Stationarity gate.** Before any pooled statistic is interpreted, run the
windowed-homogeneity check. If eras differ, pooled p-values are quarantined and the
analysis proceeds per-era, with era boundaries taken from known regime events first
(rule changes, equipment cycles), data second. *Dissolves C5.*

**A6. Designated arbiter.** Conflicting exploratory verdicts (C6) are never argued to
a winner. The disagreement defines what gets pre-registered; the held-out confirmation
test is the only arbiter. (Hot-45: scan said luck, persistence said era-effect; the
registered binomial test on post-freeze draws settles it, not us.)

**A7. Layered one-way flow.** Detection (p-values) → interpretation (row tracing,
era attribution) → decision (Doob gate → EV measure → Kelly size). Information flows
forward only; decisions never feed back into detection choices; each theorem is asked
only the question of its own layer. *Dissolves C7, C8.*

---

## Part 3 — Theorem onboarding protocol (8 steps, run for every new theorem)

**Step 1 — Statement card → KNOWLEDGE BASE.** One page in `docs/kb/<theorem-id>.md`
(template = any existing card; index = `docs/kb/INDEX.md`): theorem, exact assumptions, the
functional it constrains, its value under the project H₀, the alternatives it can
detect, finite-sample cautions, AND a reference summary distilled from a fetched
authoritative source (Wikipedia/arXiv/textbook) with links — the methodology's
documentation is downloaded into the KB at onboarding, not left as external links only.
A theorem without a KB card is inadmissible (mirror of the dataset-card rule, Part 4).
*(Template: "Wiener–Khinchin: autocovariance ↔ spectrum; assumes 2nd moments,
stationarity; H₀ value: flat spectrum; detects: periodicity, linear memory.")*

**Step 2 — Face & blind-spot assignment.** Place it on the four-face map
(statistical / dynamical / algorithmic / cross-sectional). State explicitly what it
CANNOT see. If its scope is fully contained in an existing instrument's, onboarding
stops — it's redundant, not wrong.

**Step 3 — Conflict scan against the registry.** Check C1–C10 one by one
(C9 row-trace and C10 representation charge are mandatory for relational instruments):
- Asymptotics: at what n do its limit results bite? (C1)
- Null import: does its textbook baseline match our generative H₀? (C2)
- Equivalence: derive relations to existing statistics, then MEASURE null correlation
  against every ledger member on simulated data. (C3)
- Certificate type: one-sided or two-sided? (C4)
- Stationarity assumptions? (C5)  Alternative-hypothesis volume / look-elsewhere? (C6)
- Which layer does it live in — detection, interpretation, or decision? (C7/C8)

**Step 4 — Null trial (the gate that catches everything).** Implement the statistic;
run it on ≥500 pure simulated H₀ datasets of the real data's exact shape. Required:
(a) its null distribution is non-degenerate (kills KS-under-ties),
(b) its location matches theory or the discrepancy is documented as estimator bias
(kills Hurst/Binder misreads), (c) seeds fixed, script standalone.

**Step 5 — Family registration.** Assign equivalence class (new or existing); recompute
m as the number of classes; publish the new Bonferroni/BH threshold; mark the
instrument EXPLORATORY. It cannot touch the confirmation family yet.

**Step 6 — First run, dual report.** Observed value + position in MC null + p-value of
correct sidedness + power statement. Any flag: trace to driving rows before reporting;
check whether those rows already underlie a known anomaly (A3).

**Step 7 — Ledger integration.** Add a row to THEOREM_SYNTHESIS results ledger; update
the implication lattice (what it implies, what implies it, whose blind spot it covers);
update the webpage constants block with its derived values; log in RESEARCH_NOTES with
a section number.

**Step 8 — Promotion (optional, gated).** The instrument may enter the pre-registered
confirmation family ONLY at a confirmation-set reset boundary, with threshold
recomputed, per A6/RUNBOOK Phase 3. Exploratory findings never self-promote.

### Onboarding worked example (retrospective): Per Bak / SOC
S1: BTW criticality; assumes slow drive + threshold dynamics; H₀ value: no 1/f, geometric
avalanches, H=½. S2: physical face; blind to marginal bias. S3: C1 hit (Hurst bias) —
flagged; C3: avalanche stats near-independent of chi-square family — new class. S4: null
trial would have shown Ĥ_null=0.6–0.7 immediately (in practice we found it on the real
run and recovered via calibration — the protocol exists so it never reaches that point
again). S5: m 15→18. S6: all null with power statement. S7: §6i, ledger rows 12/15–20,
webpage updated. S8: not promoted — nothing to confirm.

---

## Part 4 — Dataset onboarding protocol (the data-side mirror of Part 3)

Theorems and datasets are the project's two first-class citizens; both are gated.
**Structure: every dataset lives in `datasets/<dataset-id>/` containing its canonical
files, provenance stages, audit table, and a completed `DATASET.md` card (template:
`datasets/_TEMPLATE/DATASET.md`). A dataset without a completed card is inadmissible —
no instrument may read it.**

**Step D1 — Folder & card.** Copy `datasets/_TEMPLATE/` to `datasets/<id>/`. Fill the
card's §1 first: the one-sentence H₀ **and the executable null simulator**. If the
constrained generative model cannot be written down, onboarding stops — every
instrument's calibration depends on it (Article A1).

**Step D2 — Schema freeze.** Declare columns, types, units, and ordering semantics
(does field order carry physics, like PCSO's exit order?). Canonical file is
append-only; schema changes force re-onboarding.

**Step D3 — Acquisition with provenance.** Pull from the primary source; keep raw
extraction stages in the folder as provenance files; identify ≥2 independent
verification sources before analysis begins.

**Step D4 — Row-level audit.** Produce the `_audited` variant (Source1/Source2/Status
per row); run structural integrity (ranges, duplicates, near-duplicate signatures,
calendar/schedule consistency, sequence continuity); adjudicate every flag against
independent sources; record the census in card §4.

**Step D5 — Era registry.** Enumerate known regime events (rules, equipment, market
structure) in card §5 BEFORE testing — era boundaries discovered later are findings;
era boundaries known in advance are constraints (A5).

**Step D6 — Freeze declaration.** Set the exploration/confirmation boundary and the
append rules in card §6. The boundary is binding from the first instrument run.

**Step D7 — Instrument admission.** Only now may instruments run — each one passing
its own Part 3 onboarding against THIS dataset's null simulator (a theorem admitted
for one dataset is not automatically admitted for another: the null trial, equivalence
classes, and family size m are dataset-specific).

**Step D8 — Living card.** Anomalies, dispositions, audit-census changes, and pipeline
details are maintained in the card (§7–8) as the analysis proceeds; the card is the
single page a new analyst (or model) reads first.

**Registered datasets:** `pcso-lotto` (ACTIVE, card complete, weekly pipeline);
`tidal-manila`, `jpl-horizons-sun-moon`, `gfz-kp-geomagnetic` (covariates);
`openmeteo-pressure-manila` (covariate, onboarded 2026-06-11, single-source
caveat in card §3 — second source PENDING).
Next intended: a market-returns dataset per RUNBOOK "porting" notes — its card will
differ at §1 (block-bootstrap null), §5 (era registry becomes central), and §10 (costs).

---

*Adopted Jun 11, 2026 (Parts 1–3); Part 4 added same day. Applies to this project and
to any RUNBOOK-based successor (including the markets application, where C5 —
stationarity — is expected to be the dominant conflict rather than an edge case).*
