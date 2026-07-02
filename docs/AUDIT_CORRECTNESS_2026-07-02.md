# Correctness Audit — Theorem Operations, Equation Discovery, Governance

Date: 2026-07-02 · Auditor: external pass (3 parallel audit agents + direct verification)
Scope: `src/core/*`, all analysis scripts, `eq_tidal_v1–v3`, all registration/results docs,
governance layer (`design_verifier`, ledgers, admissions R1–R8), agent workflow.

Every CRITICAL/MAJOR finding below was **verified against the actual code or data**
(file:line quoted; verifiers executed on an isolated copy). Nothing here is inferred
from documentation alone.

---

## 0. Verdict in one paragraph

The lab's core discipline is real: add-one Monte Carlo p-values in the modern path,
constraint-preserving nulls, held-out CCA, pre-registration with verified commitment
hashes, published failures, and a null-equation generator that correctly prices search
multiplicity. The defects fall into three clusters: (1) an **older code path** that
predates the modern standards and still feeds verdicts (no add-one rule, wrong null
ensemble in one remediation test); (2) a **governance gate that is currently broken**
(both mandatory verifiers crash on the repo's own ledger; two enforcement checks are
dead code; three published docs carry stale panel numbers); (3) an **equation-selection
criterion that double-penalizes complexity** and changed one scientific conclusion.
All are fixable with localized changes; several trip the CLAUDE.md eval-set trigger.

---

## 1. CRITICAL

### C-1. Both mandatory verifiers crash on the current ledger — publication gate broken
- **Verified:** `python3 src/design_verifier.py` → `KeyError: 'run_id'` at
  `design_verifier.py:44`. `verify_relational_docs.py` fails
  `MISMATCH ledger size 252 != 248` then `KeyError: 'raw_p'`.
- **Cause:** the 4 equation-family charge rows appended to
  `results/multiplicity_ledger.jsonl` (2026-06-11/12,
  `{"family_id": "eq.tidal-manila.harmonic", "m_delta": …}`) lack the
  `run_id`/`method`/`p_floor`/`raw_p` fields both verifiers assume.
- **Consequence:** everything published after the append (eq_tidal_v3,
  eq_moondist_confirm1, synthetic_batch1 expA/expCD, riemann-zero-lab Batch 1) shipped
  while the RELATIONAL_RUNBOOK rule "design_verifier must PASS before publication" was
  unenforceable. `results/design_verifier_report.json` is stale (Jun 11, 248 rows).
- **Fix:** add a `row_type` field (`test` | `family_charge`) to the ledger schema;
  verifiers validate each type separately; replace the hardcoded totals (248, 0.073)
  with recomputation; add a pre-publication hook that runs all three verifiers.

## 2. MAJOR — statistical validity

### M-1. Legacy Monte Carlo p-values lack the add-one rule (p = 0 reachable)
- **Verified:** `src/markov_analysis.py:78-82` (`sum(...)/len(null)`, NSIM=4000,
  feeds a Bonferroni decision at :106); `src/cross_theorem_correlation.py:84`
  (`/NSIM`, NSIM=400, threshold 0.01); `src/powerlaw_sweep.py:51,58` (NSIM=600).
- **Why wrong:** a Monte Carlo p-value of exactly 0 is invalid (Phipson–Smyth); the
  modern path (`relational_batch5.py:32-34`) does it right: `p = (1+#{null≥obs})/(m+1)`.
- **Fix:** one-line change in each; floors (1/4001, 1/401, 1/601) remain below the
  decision thresholds, so verdict feasibility is unaffected. Shadow-rerun to confirm
  no verdict flips.

### M-2. `run_presence_mc` null breaks the 6-balls-per-row invariance
- **Verified:** `src/remediation_r1.py:75` uses `col_permuted(M, rng)` — preserves
  column marginals, destroys the hard row-sum-6 constraint. Observed and null matrices
  come from different ensembles *even under H0*: a false-positive channel in a
  remediation test whose p-values feed `meta_uniformity`.
- **Fix:** generate nulls with the constrained 6-of-P generator already in the repo
  (`relational_first_run.presence_point` pattern / `core.discrete_draws`), same mask;
  add a calibration run where the "observed" matrix is itself a synthetic draw.

### M-3. Ridge-CCA on unstandardized covariates — power silently ≈ 0 for small-unit series
- **Verified:** `relational_first_run.py:185-207` (`whiten` adds fixed `gamma=0.1` to a
  covariance whose diagonal spans ~24 orders of magnitude: Sun km ~10^16 variance vs
  tidal accel ~10^-15). Calibration holds (permutation null), but any coupling carried
  by the tidal-accel column is effectively invisible, and `heldout_rho1` is
  unit-dependent. The recovery path (`load_series`) standardizes for exactly this
  reason; the CCA path skips it. Also used by `remediation_r1.run_cca_splits`.
- **Fix:** z-score X and Y columns with train-set moments before whitening.

### M-4. Graphon attribution re-test biased against the null
- **Verified:** `src/graphon_cooccurrence.py:82-92`: after removing draws containing
  the lead ball, `stats_pair` still centers the (now all-zero) lead column by
  `c = T2·30/(P(P−1))`, injecting a deterministic −c row/col into A that inflates the
  spectral norm; nulls are unconditioned draws where the ball appears normally. The
  "fire persists ⇒ NEW structure" branch is anticonservative by construction. Also the
  floor 1/501 = 0.0020 sits within 25% of the 0.0025 threshold.
- **Fix:** delete the lead ball's row/col before the spectral norm, or use 6-of-(P−1)
  nulls on relabeled balls; raise K so floor ≤ threshold/2.

### M-5. Meta-uniformity panel pools non-p-values and tests the wrong reference
- **Verified:** `src/meta_uniformity.py:29-30` pools `median_p` of 10 repeats (Beta-
  concentrated near 0.5 under H0, not U(0,1)); KS at :57-59 is against continuous
  uniform though many entries live on coarse add-one lattices (m=19 → 20 values) and
  are mutually dependent (same draws).
- **Fix:** pool one designated p per test (never medians of repeats); compare against
  the simulated discrete null CDF of the same panel composition; label KS descriptive.

### M-6. Stale published numbers for the meta panel — three docs disagree with the JSON
- **Verified:** actual `results/meta_uniformity.json` = **136 tests, KS p=0.111,
  8.8% ≤0.05**. `REMEDIATION_LOG.md:28` says 126/0.385/6.3%; `CASE_STUDY_1_PCSO.md:451`
  says 0.385; `RESPONSE_EXTERNAL_REVIEW.md:20` says 173 tests. Drift is material:
  0.385 → 0.111 moves the headline much closer to its own alarm line.
- **Fix:** re-sync the three docs; stamp transcribed values with the source JSON SHA;
  extend `verify_relational_docs.py` to scrape docs, not just the JSON.

## 3. MAJOR — equation-discovery pipeline

### E-1. Selection criterion J double-penalizes complexity; "BIC-rate" label is wrong
- **Verified:** `eq_tidal_v1.py:135` / `eq_tidal_v2.py:159`:
  `J = NLL_validation + (ln n_train / 2) · complexity`. BIC's penalty is derived for a
  *training* likelihood; held-out NLL already prices overfitting — complexity is
  charged twice, on an incoherent scale. Concrete effect in `results/eq_tidal_v2.json`:
  A5 (3 freqs) had the better validation NLL *and* the best test NLL but lost J by
  27.1 points purely on penalty. v2 learning #1 ("capacity refuted as binding
  constraint") is partly criterion-induced. Same hybrid in
  `eval-q3-20260611/eq_fit_eval_q3.py:138`.
- **Fix:** choose one: pure held-out NLL; true BIC on train NLL; or a pre-registered,
  derived λ (nested CV). Re-run as v4 and re-adjudicate the capacity learning.

### E-2. Multiplicity is charged but never applied to equation verdicts
- **Verified:** ledger carries `m_delta` charges for `eq.tidal-manila.harmonic`
  (m=10 total) but every acceptance ran at raw p ≤ 0.01, and all docs defer to "the
  orchestrator applies the correction at verdict time" — no artifact shows it applied.
  Bites concretely: v2 claim B's binding surrogate p = 0.00995 passes 0.01 by half a
  resampling quantum and fails under any m=10 family correction — and that pass is
  cited in `REGISTRATION_EQ_MOONDIST_CONFIRM.md:45` as pedigree for the
  MECHANISM_SUPPORTED promotion. At B=200 surrogates the p-floor (0.00498) cannot even
  resolve 0.01/10; B must scale with m.
- **Fix:** implement the verdict-time correction step (per-family Šidák on declared m,
  B scaled so floor ≤ threshold/2); re-adjudicate v2 claim B and the confirm1 pedigree.

### E-3. confirm1's MECHANISM_SUPPORTED has no skill baseline
- **Verified:** `REGISTRATION_EQ_MOONDIST_CONFIRM.md:146` (`null_baseline: []`);
  criterion C1 = 1.5 × the model's own prior test RMSE, on 86 rows from the same
  DE441 integrator. A textbook a-priori sinusoid (27.555 d, ephemeris amplitude)
  would very likely also pass — the label certifies more than the test discriminates.
- **Fix:** future confirmations register ≥2 baselines (climatology; textbook-constants
  harmonic) and require the frozen equation to beat both.

### E-4. Residual-bootstrap CI invalid under the proven misspecification
- `eq_tidal_v2.py:449-472`: moving-block bootstrap treats residuals as exchangeable
  noise while R1 proves they contain deterministic unmodeled harmonics (p≈10^-21);
  the "inflates, never deflates" conservatism claim is asserted, not demonstrated.
  The headline "CI ∋ 27.555" calibration PASS depends on it.
- **Fix:** profile-likelihood CI on ω, split-half stability, or parametric bootstrap
  injecting the whitelisted lines; or validate the conservatism claim on synthetic
  two-line data.

### E-5. Post-hoc tolerance bands (evection) and data-informed whitelist
- v2's evection band [29.50, 33.40] was drawn after v1 published 30.638 d with a CI
  excluding truth; the §7 whitelist (4 of dozens of lunar lines) was chosen knowing
  v1's residual peaks. Transparent and m-charged, but "evection ✓ attribution-grade"
  should read descriptive, not confirmatory.
- **Fix:** derive bands a priori from a Rayleigh-overlap identifiability model; take
  whitelists from a standard lunar-theory table with an amplitude cutoff.

### E-6. Fisher-g machinery miscalibrated for the "36.34 d anomaly" claim
- `eq_tidal_v2.py:259-283`: iterative max-ordinate deletion invalidates the exact
  Fisher null for subsequent peaks (Siegel's statistic is the correct tool), and
  Fisher's g assumes white iid ordinates — false for residuals of a fitted harmonic
  model. Conservative as a *gate*, anticonservative as *evidence that the lines are
  real*.
- **Fix:** pre-whiten (fit-and-subtract whitelist), then one calibrated
  simulation-based spectral test; complete-linkage cluster collapse.

## 4. MAJOR — governance mechanics

### G-1. "Append-only" ledgers are rebuilt with truncating writes
- **Verified:** `build_multiplicity_ledger.py:117` and `build_run_ledger.py:157` both
  `open(LEDGER, "w")` over backfill sets smaller than the live ledgers — one re-run
  deletes 4 equation charges and 10 post-backfill run rows.
- **Fix:** builders refuse to run if disk rows ∉ backfill; rebuild to temp + diff.

### G-2. design_verifier's sensitivity check is dead code
- **Verified:** `design_verifier.py:34` `SENSITIVITY_REQUIRED = {"hit-count"}` but the
  actual ledger family ids are `hit-count-temporal` (35 rows) and `hit-count-cooc`
  (6 rows) — exact-match never fires; the M4 three-regime rule is enforced by nothing.
- **Fix:** `startswith("hit-count")`; promote missing-regime to violation for new runs.

### G-3. "Every test in the ledger" check is claimed but not implemented
- `design_verifier.py:8` docstring promises it; code only reads the ledger, so an
  unledgered test (the M6 failure mode) is undetectable.
- **Fix:** run scripts emit a test manifest; verifier reconciles manifest ↔ ledger.

### G-4. Standing admissions R1–R7 predate the remediation-era gates
- Negative controls at n=50–100 (vs the adopted ≥200), continuous KS on m=19 lattice
  p-values (only 20 possible values), positive gates with floor = α (no headroom),
  shared rng between data generation and null permutation. `r8_admission.py` (later)
  does all of this right and honestly failed — proving the lab knows the standard.
- **Fix:** re-admit R1–R7 under the r8 harness (n≥200, lattice-aware χ², m ≥ 39,
  split `rng_data`/`rng_null`); re-issue ADMISSION_RELATIONAL v2.

### G-5. Family registry fragmentation
- Ledger family_ids (graph, tda, recovery, cca, two-sample, hit-count-*) don't map
  1:1 to the declared equivalence classes; the promised H-protocol null-correlation
  measurement (R5 vs graphon/MP — the #45-reshadowing risk) is still unmeasured;
  batch-6 originals and batch67_r2 reruns both count toward global m.
- **Fix:** one canonical `families.json` (class membership + measured null
  correlations); `superseded_by` flags; both ledgers reference it. (This is the
  playbook's Algorithm H-2.)

## 5. MINOR (fix opportunistically)

1. `remediation_r1.py` stale metadata: `run_lambda_max` docstring says m=399, code
   runs 999 (verified); ex-suspicious block runs 999 nulls but writes `"m_null": 399`
   (verified :282-287); `run_presence_mc` docstring says m=29, JSON says 199.
   The recorded m is load-bearing for floor audits.
2. `remediation_r1.py:125` — GW pair loop re-seeds `default_rng(SEED+92)` per pair;
   intended outer `rng` is dead code; pair p-values artificially correlated.
3. `run_cca_splits` "median p across nested splits vs Šidák" — median of dependent
   p's is not a p-value (conservative here; rename or use a max-statistic MC).
4. `powerlaw_sweep.py`: P4 pools unstandardized steps across games with different
   pools (mimics heavy tails); `xmin = quantile(0.5)` is not the advertised CSN
   estimator; P2's `log(V+1e-9)` lets a zero-variance ball dominate the slope.
5. `markov_analysis.py:71` — division by zero if a tercile state never occurs (guard).
6. Single-trial "null-trial admission" gates in `graphon_cooccurrence.py:98-105` and
   `szemeredi_ap.py:81-87` have ~no power as calibration checks (pass criterion
   p > 0.0025 fails a *correct* instrument 0.25% of the time). Don't call them
   calibration; use the 200-trial `gate_summary` standard.
7. `core/recovery.py:11` — edge clipping duplicates a 2-NN candidate (symmetric,
   calibration safe, statistic slightly distorted at boundaries).
8. `core/stats.py` imports `remediation_r1` (heavy, wrong dependency direction).
9. Ljung–Box df not reduced by fitted params (`eq_tidal_v1.py:192-200`); nulls built
   from full series vs registration's "train segment" text (`eq_tidal_v1.py:352-356`
   — document or make train-only); `heldout_loglik` is profiled-σ RMSE transform,
   rename. eval-q3: null equations scored on the real test split (:219-233), residual
   gates on full series (:279), hardcoded foreign session path (:65).
10. Tracy–Widom skewness match (+0.316 vs +0.293) presented as universality
    confirmation — indicative only; skewness match ≠ TW shape match (kb caveat exists,
    THEOREM_SYNTHESIS wording is stronger than the kb supports).
11. AGENT_WORKFLOW role-ID fields absent from most run-ledger rows;
    registration-commit-before-run ordering verified by no tool (one-line git check).
12. EVALUATION_PROTOCOL constants (NPERM=20000) never amended for the relational
    program (m=99–1199); version-bump with a relational annex.

## 6. What is correct and must be preserved

1. Add-one Phipson–Smyth p-values throughout the modern path (`relational_batch5.py:32`,
   `core/stats.py`, `core/recovery.py:29`, `graphon_cooccurrence.py:63`).
2. Constraint-preserving nulls: exact 6-of-P generators (argsort trick), degree-
   preserving double-edge swaps, frozen masks/landmarks between obs and null.
3. Held-out CCA discipline: train-only projections, frozen, null permutes only the
   held-out pairing; in-sample ρ₁ logged separately to document inflation.
4. Selection built into the statistic (max|r| recomputed inside the null;
   hot-set selection replayed identically in the null) — no selective-inference leak.
5. The null-equation generator (A1): running the identical grid+refine+selection on
   200 matched nulls internalizes search multiplicity — the correct answer to
   "symbolic regression returns equations on noise." It caught claim A honestly, twice.
6. Pre-registration integrity: all four registration hashes verify against the
   commitment ledger today; both outcome branches declared before execution;
   failures published at full volume (6 of 7 claim-verdicts are FAILs).
7. Walk-forward backtest with correct hypergeometric variance
   (`markov_chain_model.py:91-99`); pseudo-counts centered at 6/P not 0.5.
8. The 200-trial calibration gates + frozen power curves in `remediation_r1.gate_summary`.
9. The PCSO equation-gate refusal (`RESULTS_EQ_pcso-649-marginal.md`): NULL detection
   → no fit, no multiplicity — exactly right.
10. Seed hygiene in modern scripts (single stream, obs before nulls).

## 7. Priority queue

| # | Fix | Files | Effort | Verdict risk if unfixed |
|---|---|---|---|---|
| 1 | C-1 verifier schema + rerun | design_verifier, verify_relational_docs, ledger | small | publication gate stays broken |
| 2 | G-1 non-destructive builders | 2 builders | small | audit trail one re-run from loss |
| 3 | E-1 + E-2 selection criterion + verdict-time correction | eq_tidal v4, ledger consumer | medium | capacity learning + confirm1 pedigree unsound |
| 4 | M-2 constrained presence null; M-4 attribution null | remediation_r1, graphon | small | false-positive channels open |
| 5 | M-1 add-one in legacy path | 3 files | trivial | invalid p=0 possible |
| 6 | M-3 standardize CCA | relational_first_run | small | silent power loss |
| 7 | G-2/G-3 verifier dead code + manifest | design_verifier | small | M4/M6 unenforced |
| 8 | M-6 doc re-sync + doc-scrape checks | 3 docs + verifier | small | stale published claims |
| 9 | G-4 re-admit R1–R7 (r8 harness) | relational_admission v2 | medium | admission evidence below standard |
| 10 | M-5 panel composition | meta_uniformity | small | meta-claim distorted |

**CLAUDE.md trigger:** items 3, 4, 6, 9 materially change agent/methodology behavior —
run `agents/evals` (structure_eval_set_v1) after implementing, before publishing.
