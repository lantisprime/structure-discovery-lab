# PLAYBOOK — Harmonizing Mathematical Theorems for LLM-Free Structure Discovery

Version 1.0 · 2026-07-02 · Companion to THEOREM_SYNTHESIS.md, RELATIONAL_RUNBOOK.md,
AUDIT_CORRECTNESS_2026-07-02.md

**Audience:** any executor — another LLM, a human analyst, or (the design goal) a
plain scheduler running scripts with no language model in the loop.

**Contract of this document:** every step is either (a) an algorithm precise enough to
implement from this text alone, (b) a schema whose instances are validatable by
machine, or (c) explicitly marked `HUMAN-GATE` (the short list of steps that stay
human). If a step is none of these, it is a bug in the playbook.

---

## Part 0 — Definitions and the one governing principle

- **Dataset** `D`: a finite matrix of observations with a declared sampling frame.
- **H0 (the null object)**: a fully specified stochastic process claimed to generate
  `D` (e.g., i.i.d. uniform on C(P,6) combinations). H0 must come with a **sampler**.
- **Instrument**: (statistic `T`, null generator `G`, sidedness, claim type). An
  instrument is *admitted* only after passing Algorithm H-1.
- **Theorem card**: machine-readable record of the theorem an instrument instantiates
  (Part I).
- **Family**: a set of instruments whose statistics are correlated under H0 above a
  threshold (Algorithm H-2). Multiplicity is charged per family, not per instrument.
- **Flag ≠ anomaly ≠ discovery.** A flag is a corrected rejection by one family; an
  anomaly is a flag surviving row-trace deduplication (Algorithm S-6); a discovery is
  an anomaly surviving a pre-registered confirmation on new data.

**The governing principle (from THEOREM_SYNTHESIS §1–2):** i.i.d.-type nulls are
simultaneously extremal on several mathematically distinct *faces* — statistical
(marginals), dynamical (memory), algorithmic (compressibility), spectral/cross-
sectional (collective modes). No single face implies the others (each implication is
one-way, with known counterexamples). Therefore harmonization means: **cover every
face with at least one admitted instrument, measure the instruments' correlations
under H0, charge multiplicity by correlation class, and let a decision table — not
judgment — turn p-values into verdicts.**

---

## Part I — The theorem card: machine-readable theorem representation

Prose knowledge-base cards (docs/kb/) stay as documentation. The *executable* card is
a YAML/JSON record. Every admitted instrument references exactly one card.

```yaml
# schema: theorem_card.v1
id: marchenko-pastur.lambda-max          # unique slug
theorem: "Marchenko–Pastur / Tracy–Widom edge"
face: cross-sectional                    # one of: statistical | dynamical |
                                         #   algorithmic | spectral | cross-sectional
h0_functional: "largest eigenvalue of standardized co-occurrence matrix"
extremal_at_h0: "inside MC-simulated bulk"   # what value H0 forces
sidedness: upper                         # upper | lower | two-sided
asymptotic_assumptions:                  # each entry is machine-checkable
  - {name: iid_entries, holds_for_data: false,
     mitigation: "null MUST be simulated from the constrained ensemble, never analytic"}
  - {name: n_min, value: 500, data_n: 776, holds_for_data: true}
blind_spots:                             # faces/structures this test cannot see
  - temporal-order        # invariant to row permutation
  - nonlinearity-beyond-second-moment
detects:                                 # structures it is powered for
  - collective-modes
  - pair-affinity
null_generator: constrained-6ofP         # id into the generator registry (Part III S-1)
claim_types: [within-game-cooccurrence]  # what claims it may support (verifier whitelist)
power_curve: results/power/lambda_max.json   # frozen, from admission
admission: results/admission/lambda_max.json # Algorithm H-1 output
equivalence_class: spectral-cooc         # from families.json (Algorithm H-2)
```

**Validation rules (mechanical):**
1. `asymptotic_assumptions[*].holds_for_data == false` ⇒ a `mitigation` must exist and
   the null generator must be simulation-based (never a closed-form reference).
2. `claim_types` must be a subset of the design-verifier whitelist.
3. `power_curve` and `admission` files must exist and be newer than the card.
4. Union of `detects` across all admitted cards must cover all five faces
   (Algorithm H-3 checks this).

This card is what makes the conflict scan (old C1–C11) mostly mechanical: C1 is
`n_min vs data_n`, C4 is the `sidedness` field, C5 is a stationarity flag, C3 is the
measured `equivalence_class`.

---

## Part II — Harmonization algorithms

### Algorithm H-1 — Instrument admission (calibration + power gate)

Never trust a new instrument on real data. Admit it on synthetic data first.
(The lab's r8_admission.py is the reference implementation; the single-trial gates in
older files are NOT — they have ~no power as calibration checks.)

```
ADMIT(instrument I = (T, G, sidedness), alpha, n_trials=200, m_null>=39):
  # -- freeze the design BEFORE running --
  design_hash = sha256(serialize(I, alpha, n_trials, m_null, seeds))
  require m_null >= ceil(2/alpha) - 1          # floor rule: 1/(m+1) <= alpha/2

  # -- negative control: FPR calibration --
  rng_data, rng_null = split_streams(master_seed)   # NEVER share one stream
  P = []
  for t in 1..n_trials:
      D_null = G.sample(rng_data)               # synthetic H0 data
      p = MC_P(T, D_null, G, m_null, rng_null)  # Algorithm S-3
      P.append(p)
  fpr = mean(P <= alpha)
  # lattice-aware uniformity: p-values live on {1/(m+1), ..., 1}; use chi-square
  # on >=20 equiprobable lattice bins, NOT continuous KS
  unif_p = lattice_chi2(P, m_null, bins=20)
  pass_negative = |fpr - alpha| <= 3*sqrt(alpha*(1-alpha)/n_trials)  and unif_p > 0.01

  # -- positive control: power curve --
  for effect in declared_grid:                  # e.g., bias eps in {.01,.02,.05,.1}
      power[effect] = mean( MC_P(T, G.sample_with(effect), G, m_null) <= alpha
                            for n_trials trials )
  pass_positive = power[declared_target_effect] >= 0.8

  # -- verdict: mechanical --
  status = ADMITTED if (pass_negative and pass_positive) else
           EXPLORATORY_ONLY                     # never silently discard; GW precedent
  emit admission record {design_hash, fpr, unif_p, power_curve, status}
  freeze power_curve                            # power statements later cite this file
```

Re-admission trigger (mechanical): any change to `T`, `G`, standardization, or the
data schema invalidates `design_hash` ⇒ status reverts to PENDING.

### Algorithm H-2 — Equivalence classes: measure, don't assume

Two instruments that are deterministic functions of the same data slice will co-fire
on one anomaly (the six-flags-one-anomaly trap, THEOREM_SYNTHESIS §4b). The fix is to
*measure* correlation under H0 and merge correlated instruments into one family for
multiplicity purposes.

```
BUILD_FAMILIES(admitted_instruments, G_h0, n_sims=500, rho_merge=0.90, rho_report=0.5):
  # simulate the whole battery on shared null datasets
  for s in 1..n_sims:
      D_s = G_h0.sample(rng)
      for I in admitted_instruments:
          S[I][s] = I.T(D_s)                    # raw statistic, standardized later
  # correlation matrix of statistics under H0
  R[i][j] = spearman(S[i], S[j])                # rank corr: robust to monotone maps
  # single-linkage merge at rho_merge; REPORT (not merge) couplings in
  # [rho_report, rho_merge) — these are the "structural correlations under H0"
  families = connected_components( graph(|R| >= rho_merge) )
  emit families.json:
      { family_id, members[], measured_R_submatrix,
        provenance: {n_sims, seed, G_h0 id, date} }
```

**Consumption rules (this is what the current repo lacks — a single registry):**
1. The multiplicity ledger's `family_id` MUST come from `families.json`. One registry;
   ledgers reference it; no free-text families.
2. Šidák/Bonferroni is applied with m = number of *families* engaged in a run.
3. If two instruments in one family both reject, that is ONE flag (they are the same
   evidence), and the row-trace (S-6) must confirm they load on the same rows.
4. Monotone-equivalent statistics (|rho| ≈ 1, e.g., T2 affine in T1) are detected here
   automatically and collapse to one ledger row.
5. Rerun BUILD_FAMILIES whenever an instrument is added or its statistic changes;
   `families.json` carries provenance so staleness is detectable by timestamp/hash.

### Algorithm H-3 — Coverage audit: the blind-spot matrix

Harmonization is not just de-duplication (H-2); it is also completeness. Each theorem
card declares `detects` and `blind_spots`. The battery is complete for a face when
some admitted instrument detects it and its blind spots are covered by another.

```
COVERAGE(cards):
  faces = {statistical, dynamical, algorithmic, spectral, cross-sectional}
  for f in faces:
      detectors[f] = {c : f in c.detects and c.admission.status == ADMITTED}
      require detectors[f] != {} else emit GAP(f)
  # pairwise blind-spot closure: for every card c and every b in c.blind_spots,
  # some other admitted card must list b in detects
  for c, b: require exists c' != c with b in c'.detects else emit GAP(c, b)
  # circularity check: the closure graph must not have a face covered ONLY by
  # instruments in a single equivalence class (one family = one view)
  for f: require |{class(c) : c in detectors[f]}| >= 1 and
         (|detectors[f]| == 1 or classes differ) else emit WEAK(f)
```

Output is a matrix (faces × families) published with every batch. A structure claim
of "no structure anywhere" is only as strong as this matrix is complete — publish the
GAP list alongside null verdicts.

### Algorithm H-4 — Alpha allocation and the multiplicity ledger

```
LEDGER RULES (schema multiplicity_ledger.v2):
  row_type: test | family_charge            # fixes the verifier crash class
  test rows:   {run_id, family_id, method, raw_p, m_null, p_floor, data_filter,
                dataset, date, superseded_by?}
  charge rows: {family_id, m_delta, reason, registration_sha, date}
  invariants (verifier-enforced, Part V):
    - append-only: builders may only add; a rebuild must reproduce existing rows
      byte-identically or abort
    - every test row's p_floor = 1/(m_null+1) <= corrected_alpha/2   (floor rule)
    - superseded rows excluded from global m
    - every results-JSON p-value has a ledger row (manifest reconciliation)

ALPHA(run):
  m_fam  = #{families engaged in this registered run}
  alpha_fam = 1 - (1-0.05)^(1/m_fam)          # Šidák
  require every instrument's m_null >= ceil(2/alpha_fam) - 1
  # verdict-time consumption — the step the equation pipeline skipped:
  for each claim: corrected_pass = (raw_p <= alpha_fam)   # applied, not deferred

CONVENTION v1 (ratified by the lab owner 2026-07-02, reconciling this
section with RESULTS_EQ_READJUDICATION.md §2b):
  - DETECTION runs (independent batteries): m = families engaged in the
    registered run, as above.
  - ACCUMULATING claim families (repeated attacks on the same target across
    registrations, e.g. an equation program's v1/v2/v3 chain): m = the
    family's CUMULATIVE charged m at verdict time, from the multiplicity
    ledger's family_charge rows. The stricter reading governs because each
    re-registration is another look at the same claim, not a new family.
```

### Algorithm H-5 — Mechanical conflict scan (pre-run linter)

Run before any battery; each check is a pure function of theorem cards + dataset
metadata. (These were LLM judgment calls C1–C11; the starred ones are now mechanical.)

```
CONFLICT_SCAN(cards, dataset_meta):
  for c in cards:
    *C1  n-threshold:      any assumption with data_n < n_min and no mitigation -> BLOCK
    *C3  equivalence:      c.equivalence_class missing from families.json      -> BLOCK
    *C4  sidedness:        registration sidedness != card sidedness            -> BLOCK
    *C5  stationarity:     dataset_meta.era_boundaries intersect sample and
                           card lacks era-stratified mode                      -> QUARANTINE (S-7)
    *C9  re-shadowing:     claim's family shares class with a family already
                           charged for a known anomaly (ANOMALY_REGISTRY)      -> require S-6 trace
     C2,C6-C8 (novel-domain semantic fit)                                      -> HUMAN-GATE
```

---

## Part III — The structure-detection loop (repeatable, LLM-free)

The loop is a fixed DAG: `REGISTER → GENERATE NULLS → EXECUTE BATTERY → CORRECT →
TIER → TRACE → QUARANTINE/PUBLISH → META-PANEL`. Every node below is an algorithm.

### S-1 — Null generator contract

A generator `G` is a seeded program, registered by id, that samples datasets from H0
**preserving every hard constraint of the real data**. This is the single most common
source of false positives (see AUDIT M-2: column permutation destroyed the
6-per-row constraint).

```
GENERATOR REGISTRY (each entry admitted once, reused forever):
  constrained-6ofP:   rows = rng.random((T,P)).argsort(axis=1)[:, :6]   # exact uniform
  degree-preserving:  double-edge swaps on graphs (fixed degree sequence)
  phase-surrogate:    |FFT| preserved, phases randomized (2nd-order structure kept)
  block-permutation:  within-block row shuffles (era structure kept)
  paired-shuffle:     permute the PAIRING between X and Y, never the rows themselves
CONTRACT (checkable):
  1. G.sample must satisfy every declared invariant of D (row sums, marginals,
     pairing, mask). Test: assert_invariants(G.sample(rng), D.invariants) x 100.
  2. Everything frozen in the observed computation (masks, landmarks, train/test
     boundaries, standardization moments) is IDENTICAL in null computations.
  3. rng streams: rng_data (synthetic data), rng_null (permutations) — never shared.
  4. Standardize columns (train moments) BEFORE any scale-sensitive statistic
     (ridge/whitening/distance) — units must never carry information (AUDIT M-3).
```

### S-2 — Registration record (no prose required)

```yaml
# schema: registration.v2 — a form, not an essay
run_id: b8_example
dataset: {id: pcso-lotto, filter: "2025-07-01..2026-06-30", n: 366,
          era_boundaries: ["2026-02-01"]}
h0: {generator: constrained-6ofP, params: {P: 55, k: 6}}
instruments: [lambda-max, mmd-quarters, cca-pressure]   # ids -> cards -> families
families_engaged: 3                                     # from families.json — derived
alpha: 0.05
alpha_corrected: 0.0170                                 # Šidák, derived
m_null: {lambda-max: 999, mmd-quarters: 1199, cca-pressure: 399}  # floor-checked
outcome_branches:                                       # BOTH declared
  reject: "flag -> S-6 trace -> anomaly registry"
  null:   "publish as null; update coverage matrix"
seeds: {master: 20260702}
registration_sha: <sha256 of this file, committed BEFORE execution>
approved_by_human: true                                 # HUMAN-GATE (intentional)
```

Mechanical checks at submit time: families derived not asserted; floor rule per
instrument; era intersection triggers stratified mode; commit timestamp < first
results timestamp (one-line git check — currently enforced by no tool).

### S-3 — The Monte Carlo p-value (the only p-value allowed)

```
MC_P(T, D, G, m, rng, sidedness):
  t_obs = T(D)
  null = [ T(G.sample_null(rng)) for 1..m ]
  if sidedness == upper:     c = #{ null >= t_obs }
  if sidedness == lower:     c = #{ null <= t_obs }
  if sidedness == two-sided: # add-one on EACH tail, ties in both (szemeredi_ap style)
      lo = (1 + #{null <= t_obs}) / (m+1); hi = (1 + #{null >= t_obs}) / (m+1)
      return min(1, 2*min(lo, hi))
  return (1 + c) / (m + 1)                  # Phipson–Smyth add-one; p=0 impossible
INVARIANTS:
  - p ∈ {1/(m+1), ..., 1}; report m alongside p ALWAYS
  - floor rule: 1/(m+1) <= alpha_corrected/2, else the run is unregistrable
  - never compare a lattice of these to continuous uniform (use lattice_chi2)
```

### S-4 — Battery execution

```
EXECUTE(reg):
  rng = default_rng(reg.seeds.master); consume observed stats FIRST, nulls after
  results = {}
  for I in reg.instruments:
      results[I] = MC_P(I.T, D, I.G, reg.m_null[I], rng, I.card.sidedness)
  run twice (separate processes), require byte-identical JSON   # two-run rule
  emit results.json + manifest {every p-value emitted}          # ledger reconciliation
  append test rows to multiplicity ledger (schema v2)
```

### S-5 — Verdict tiers: a decision table, not judgment

```
TIER(claim):                                  # deterministic; inputs all machine-held
  given: p (raw), alpha_corrected, floor = 1/(m_null+1),
         admission_status, registered (bool), era_clean (bool from S-7)
  if admission_status != ADMITTED:                       return EXPLORATORY_ONLY
  if not registered:                                     return EXPLORATORY_ONLY
  if p >  alpha_corrected and p <= 2*alpha_corrected:    return NEAR_MISS   # queue for rerun at higher m
  if p >  alpha_corrected:                               return NULL_CONFIRMED
  # p <= alpha_corrected from here on
  if p == floor and floor > alpha_corrected/4:           return FLAG_AT_FLOOR  # rerun at m'>=4/alpha-1
  if not era_clean:                                      return ERA_BOUNDED_FLAG
  else:                                                  return FLAG -> run S-6
Escalation of FLAG to ANOMALY and ANOMALY to DISCOVERY happens only via S-6 and a
new registered confirmation run respectively — never inside the same run.
```

### S-6 — Row-trace attribution (the de-duplicator)

Purpose: convert k co-firing flags into the number of *distinct* anomalies (the
six-flags-one-anomaly lesson). Fully mechanical greedy leverage:

```
TRACE(flag, D, registry=ANOMALY_REGISTRY):
  base = flag.statistic(D)
  contrib = {}
  for unit u in D.rows (or balls, per flag's granularity):
      contrib[u] = base - flag.statistic(D minus u)      # leave-one-out leverage
  driving_set = smallest S by |contrib| descending such that
                statistic(D minus S) falls below the null median
  for known in registry:
      if jaccard(driving_set, known.driving_set) > 0.5:
          return SAME_ANOMALY(known.id)                  # charge nothing new
  registry.append({id, driving_set, flags: [flag.id], date})
  return NEW_ANOMALY
```

Two flags mapping to the same driving set are ONE anomaly with two views; the ledger
marks the second `attributed_to: <anomaly_id>` and it adds no multiplicity weight to
"number of discoveries." (This is the #45 story, mechanized.)

### S-7 — Era quarantine (automatic, pre-verdict)

```
ERA_GATE(reg, D):
  for boundary in dataset.era_boundaries:
      if boundary inside reg.dataset.filter:
          split D at boundary; rerun each engaged instrument per segment
          era_clean(claim) = (verdict identical in all segments)
          pooled p-values with era_clean == false are QUARANTINED:
          reported, never promoted past ERA_BOUNDED_FLAG
```

### S-8 — Meta-uniformity panel (honesty meter, discrete-aware)

```
META_PANEL(ledger):
  panel = one designated raw_p per test row, excluding:
      superseded rows, family_charge rows, medians-of-repeats (Beta-distributed!),
      positive controls (physical series)
  # null reference: simulate the SAME panel composition (same m lattice per row)
  ref = [ [ (1+rng.integers(0, m_i+1)) / (m_i+1) for i in rows ] for 1..1000 ]
  ks_obs = ks_stat(panel);  p_meta = (1 + #{ks(ref_j) >= ks_obs}) / 1001
  alarms: frac(p<=.05) outside simulated band; p_meta < .05
  publish {n, frac_le_05, frac_le_01, p_meta, panel_sha}
  RULE: any doc citing panel numbers embeds panel_sha; a doc-scrape verifier
  compares docs against the JSON (prevents the 0.385-vs-0.111 drift class).
```

---

## Part IV — Candidate-equation discovery (repeatable, LLM-free)

Equation discovery is *gated* by detection: fit nothing until the detection loop has
rejected H0 with a corrected p (the PCSO refusal precedent — NULL detection ⇒ no fit,
zero multiplicity). Then:

### Q-1 — Gate

```
EQ_GATE(dataset):
  require exists claim with TIER in {FLAG, ANOMALY} on this dataset,   # from Part III
      OR dataset declared non-stochastic (physical series) at onboarding
  else: emit REFUSAL record (0 multiplicity charged) and STOP
```

### Q-2 — Split, grid, fit

```
EQ_FIT(series y(t), contract):
  split chronologically 60/20/20 (train/val/test); test is touched ONCE, at the end
  standardize with TRAIN moments only
  candidate families F (declared in contract): e.g. harmonic sums
      f(t) = Σ_j [a_j cos(2π ω_j t) + b_j sin(2π ω_j t)] + trend terms
  frequency search: coarse grid (Rayleigh-spaced, declared bounds) then local
      refinement per frequency; JOINT 2-D refinement for any pair closer than
      2 Rayleigh (near-degenerate pairs merge basins otherwise — v1's 30.64 d bias);
      log per-sweep objective decrease; multi-start if non-convex
  linear coefficients by least squares given frequencies
```

### Q-3 — Selection criterion (fixed — do not reintroduce AUDIT E-1)

```
SELECT(family_records):
  criterion J = held-out NLL on validation, computed with TRAIN-estimated sigma^2.
  NO additional complexity penalty on top of held-out loss.        # not "BIC-rate"
  (If parsimony tie-breaking is wanted: among models within one SE of min-J,
   choose the smallest complexity — the 1-SE rule, declared in the contract.)
  winner is refit on train+val with frozen structure; evaluated ONCE on test.
```

### Q-4 — The null-equation generator (the multiplicity killer — preserve)

The search itself finds equations in noise. Price the whole search, not the winner:

```
EQ_NULL(y, B=null_count, generators={permutation, phase-surrogate, AR(1)-matched}):
  require B >= ceil(2*m_family/alpha) - 1     # B scales with charged multiplicity!
  for g in generators, b in 1..B:
      y_b = g(y_train_stats)                  # built from TRAIN-only statistics,
                                              # extended to full length (doc the choice)
      J_b = run the ENTIRE EQ_FIT + SELECT pipeline on y_b   # identical grid/menu
  p_g = (1 + #{ J_b <= J_obs }) / (B + 1)
  binding_p = max over generators             # the hardest null must be beaten
  APPLY the family correction NOW: pass iff binding_p <= sidak(alpha, m_family)
      # never defer "to the orchestrator" — that step was never executed (AUDIT E-2)
  score null equations on their OWN test splits, never on the real test split
```

### Q-5 — Residual spectral scan (calibrated)

```
RESIDUAL_SCAN(residuals r, whitelist W of a-priori lines):
  # W comes from a standard table (e.g., lunar inequalities above an amplitude
  # cutoff), declared BEFORE seeing any residual spectrum — never curated post hoc
  1. pre-whiten: iteratively fit-and-subtract every W line (NLS)
  2. ONE spectral test on the pre-whitened residuals with a SIMULATION null:
     null spectra from AR-matched surrogates of the residuals; statistic = max
     ordinate; p by MC_P                       # not iterative Fisher-g deletion
  3. cluster surviving lines by complete linkage within 1 Rayleigh
  4. attribution tolerance bands derived a priori from Rayleigh-overlap
     identifiability (band = ±1 Rayleigh resolution at series length), never drawn
     around an already-published estimate
```

### Q-6 — Uncertainty on recovered constants

```
EQ_CI(model, y):
  primary: profile-likelihood CI on each frequency (grid the frequency, refit rest)
  secondary: split-half stability (fit halves independently; report both estimates)
  bootstrap ONLY if residuals pass a whiteness gate after Q-5; otherwise a residual
  bootstrap treats unmodeled coherent lines as noise and the CI is untrustworthy
  a recovered constant "matches" a physical constant iff the physical value lies
  inside the profile CI AND the CI half-width < the spacing to the nearest
  competing constant (identifiability, not proximity)
```

### Q-7 — Confirmation protocol (promotion to MECHANISM_SUPPORTED)

```
CONFIRM(frozen_equation, new_data):
  register BEFORE seeing new_data; freeze equation bytes (hash)
  baselines (>=2, registered):  B0 climatology (mean), B1 textbook a-priori model
      (known constants, no fitting)                     # AUDIT E-3
  criteria: RMSE(frozen) < RMSE(B0) and RMSE(frozen) <= RMSE(B1) * (1+delta_declared)
  data-independence statement: if new_data shares a generator/integrator with
      training data, the maximum attainable label is MECHANISM_CONSISTENT,
      not MECHANISM_SUPPORTED (independent-source requirement)
```

### Q-8 — Verdict labels (decision table)

```
if EQ_GATE refused:                                REFUSED_NULL_DETECTION
if binding_p > sidak(alpha, m):                    FAILED_EQUATION_SEARCH   # publish loudly
if pass Q-4 but Q-5 finds unattributed lines:      PARTIAL_MODEL (list lines; no anomaly
                                                   language until a calibrated Q-5 pass)
if pass Q-4 + Q-5 clean + Q-6 identifiable:        CANDIDATE_EQUATION
if CANDIDATE + Q-7 passed on independent source:   MECHANISM_SUPPORTED
if CANDIDATE + Q-7 passed on same-source data:     MECHANISM_CONSISTENT
```

---

## Part V — Running the lab LLM-free

### V-1 The orchestrator is a DAG runner, not a mind

```
PIPELINE (config-driven; any scheduler — make, cron, or a 50-line Python driver):
  onboard:   fetch data (per-source scripts + checksums) -> E0 integrity gate
             -> invariant extraction (row sums, eras, pairing) -> dataset_meta.json
  harmonize: H-1 admissions -> H-2 families.json -> H-3 coverage matrix -> H-5 lint
  register:  fill registration.v2 form -> mechanical checks -> HUMAN-GATE approve
             -> git commit (hash into commitment ledger)
  execute:   S-4 battery (two-run byte-identical) -> ledger append
  adjudicate: H-4 correction -> S-5 tiers -> S-6 trace -> S-7 era gate
  publish:   template-render results doc FROM the JSON (numbers never hand-typed)
             -> verifiers (V-2) must PASS -> commit
  monitor:   S-8 meta panel -> alarm rules
  equations: Q-1..Q-8 when gated in
  release:   end-to-end negative control — a full synthetic-null dataset through the
             ENTIRE pipeline each release; required output: zero tiers above
             NEAR_MISS and a uniform meta panel (this is the pipeline-level negative
             control the lab currently lacks)
```

### V-2 The verifier suite (the LLM-free reviewer)

The design verifier grows from a floor-rule linter into the full gate:

1. schema validation (ledger v2, registration v2, theorem cards)
2. floor rule per family; correction applied (not just charged) at verdict time
3. manifest ↔ ledger reconciliation (every emitted p has a row)
4. claim-type ↔ method whitelist (from theorem cards, incl. equation claims)
5. sensitivity-regime presence for hit-count families (prefix match, violation-level)
6. era-boundary intersection ⇒ stratified rows present
7. registration-commit precedes results-commit (git timestamps)
8. doc-scrape: every number in a results doc matches the source JSON (+sha)
9. append-only ledger invariant (rebuild = byte-identical or abort)
10. two-run byte-identity of results JSONs
11. release gate: end-to-end negative control passed; coverage matrix has no GAP

### V-3 What must stay human (the honest residue)

| Step | Why irreducible |
|---|---|
| H0 authorship for a genuinely new domain | choosing the null object is a modeling act |
| Registration approval | accountability, not capability |
| C2/C6–C8 semantic fit of a theorem to a new data type | meaning, not mechanics |
| Candidate-family menus for equations (physics priors) | hypothesis generation |
| Deciding what to investigate next | taste; though a NEAR_MISS + coverage-GAP priority queue mechanizes ~80% |

Everything else in this playbook — admission, families, correction, tiers, tracing,
era gating, equation search, confirmation, verification, publication — is a seeded
program. An LLM may still *write* the prose narration of a results doc, but no verdict
anywhere depends on it: delete the narrator and the verdicts do not change. That is
the definition of LLM-free this playbook targets.

### V-4 Migration checklist from the current repo (ordered)

1. Fix the broken gates first (AUDIT C-1, G-1, G-2, G-3) — nothing downstream is
   trustworthy while the verifiers crash and ledgers are truncatable.
2. `families.json` + ledger schema v2 (H-2, H-4) — unifies the fragmented registries.
3. Legacy p-value add-one fixes and null-ensemble fixes (AUDIT M-1, M-2, M-4);
   standardization in CCA (M-3).
4. Mechanize S-6 (trace_rows.py), S-7 (era gate in the runner), S-5 (tier table) —
   the three highest-value moves from LLM judgment to script.
5. Theorem-card YAML for the ~30 existing instruments (mostly transcription from kb/).
6. Equation pipeline v4: Q-3 criterion, Q-4 verdict-time correction, Q-5 calibrated
   scan, Q-7 baselines; re-adjudicate v2 claim B and confirm1.
7. Re-admit R1–R7 under the r8 harness (AUDIT G-4).
8. Template-render results docs; doc-scrape verifier; retire hand-typed numbers.
9. Stand up the release-gate negative control (V-1 `release`).
10. Run agents/evals/structure_eval_set_v1 after steps 3, 6, 7 — the CLAUDE.md
    trigger applies to each.

---

## Appendix — Quick-reference invariant card (print this)

- p = (1 + #{null beats obs}) / (m + 1). Always. Report m with every p.
- Floor 1/(m+1) ≤ corrected α / 2, or the test cannot run.
- Null preserves every hard constraint of the data. Column shuffles that break row
  sums are not nulls.
- Standardize (train moments) before anything scale-sensitive.
- Selection multiplicity lives inside the statistic (replay selection in the null)
  or inside the family charge — never nowhere.
- Held-out loss OR information criterion — never both.
- Corrections are applied at verdict time, in code, in the same run.
- k co-firing instruments on the same rows = 1 anomaly (trace it).
- Median of repeated p-values is not a p-value.
- Continuous-uniform tests do not apply to lattice p-values.
- Two runs, separate processes, byte-identical output, or it didn't happen.
- Failures are published at the same volume as successes.

