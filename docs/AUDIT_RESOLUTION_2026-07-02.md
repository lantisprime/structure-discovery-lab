# AUDIT RESOLUTION — Strategy, Steps, Evidence

Companion to AUDIT_CORRECTNESS_2026-07-02.md · 2026-07-02
Every fix below was **executed and verified in this repo** unless its status
says otherwise. Adversarial review of these solutions: §5.

---

## 1. Strategy

Four rules governed every fix:

**R-A (frozen-file policy).** Files headed `FROZEN HISTORICAL RECORD` are
never edited — they reproduce hash-ledgered results. Corrected
implementations live in new modules (`corrected_reruns.py`,
`eq_selection_v4.py`, `readmit_r1_r7.py`, `measure_equivalence.py`) that
import the frozen code read-only. Infrastructure that is *supposed* to be
living (verifiers, builders, meta panel, ledgers) is fixed in place.

**R-B (metadata corrections are records, not edits).** Hash-committed result
JSONs and frozen docstrings with wrong metadata are corrected via
`results/metadata_corrections_2026-07-02.json` + ledger-side fixes with
per-row `migration_note` provenance — the artifacts themselves stay
byte-identical to their commitment hashes.

**R-C (verdicts change only by arithmetic or by rerun).** Where a corrected
status follows from stored numbers alone (the never-executed multiplicity
step), it is recomputed by script and published as an addendum
(RESULTS_EQ_READJUDICATION.md). Where it needs recomputation on data, the
corrected instrument was actually rerun (shadow runs, ledgered as
exploratory) — no verdict was changed by prose.

**R-D (every fix leaves a gate behind).** Each class of defect now has a
verifier check, a calibration control, or a registry that would catch its
recurrence mechanically.

Execution order: broken gates first (nothing downstream is trustworthy while
the verifiers crash), then ledger schema, then statistics, then equation
re-adjudication, then registries/harnesses, then docs.

## 2. Per-finding resolution

### C-1 Verifiers crash / publication gate broken — **RESOLVED, gates green**
Steps: (1) `src/migrate_ledger_v2.py` migrated the ledger to schema v2
(`row_type: test | family_charge`; backup kept; idempotent). (2)
`design_verifier.py` rewritten: per-row-type schema validation, charge-row
registration existence, equation claims added to the method map, and a new
check 5 (run-ledger ↔ test-ledger reconciliation, the G-3 gap). (3)
`verify_relational_docs.py` ledger section rewritten for schema v2.
Evidence: `design_verifier.py` exits 0 — `PASS | 0 violations, 111 warnings
(historical floor warnings preserved) | 260 test rows (188 live), 4 charge
rows`; reconciliation 260 declared = 260 ledgered; full
`verify_relational_docs.py` suite exits 0.

### G-1 Truncating ledger builders — **RESOLVED, tested**
Both builders now rebuild to a temp file, preserve every row not derivable
from their backfill, and ABORT if a rebuilt row disagrees with disk
(append-only invariant). Positional matching handles rows sharing a key
(the 6 firstrun knn rows). `build_run_ledger.n_ledger_tests` also fixed
(`.get` — it crashed on charge rows, same C-1 class).
Evidence: both builders rerun against a copy of the live ledgers —
`preserved 9 appended rows; global_m=188` / `8 backfill + 10 preserved runs,
253 real-data tests`; row_type/superseded/m-corrections survive the rebuild.

### G-2 Dead sensitivity check — **RESOLVED, now enforcing**
Prefix match (`hit-count*`), violation-level for non-historical runs. First
activation immediately fired 5 false positives (games with zero suspicious
rows); the check now derives the affected games from the audited CSV itself
and requires regimes only where quarantined rows exist. Evidence: remediation
lambda-max group passes via its real ex_suspicious row; a synthetic
missing-regime row raises a violation (checked during development).

### G-3 "Every test in the ledger" unimplemented — **RESOLVED (v1)**
Check 5 reconciles `sum(run_ledger.real_data_tests)` with ledger test-row
counts per run and total, and flags test rows whose run_id has no run-ledger
entry. The 5 missing equation test rows (v1 A/B, v2 A/B, confirm1) were added
with their binding p's — reconciliation now holds at 260. (Full
results-JSON manifest scanning remains future work; the run-level
reconciliation closes the M6 failure mode that actually occurred.)

### M-1 Add-one rule absent in legacy files — **RESOLVED without touching frozen files**
`corrected_reruns.mc_p_addone` is the only sanctioned MC p-value; the frozen
files' defect is documented there with the monotonicity argument: add-one
strictly increases p, and every legacy minimum (markov 0.053, cross-theorem
0.09, powerlaw 0.017-vs-multiplicity) was already non-significant, so no
published verdict flips. Any future reuse of those instruments must import
the corrected estimator.

### M-2 Presence-MC null broke the row-sum invariant — **RESOLVED, rerun, defect demonstrated**
`run_presence_mc_v2` uses constrained 6-of-P nulls with the frozen mask.
Executed on real data as an UNREGISTERED, UNCITABLE exploratory shadow
(review M-B): joint verdict NULL (min p 0.28 > Šidák 0.0102) — an
*exploratory indication* that the published conclusion is ensemble-robust,
pending the registered rerun (fresh seed, this look disclosed). The calibration
control demonstrates the original defect empirically: on synthetic H0 data
the corrected null gives mean p = 0.488 (calibrated) while the frozen
col-permuted null gives mean p = 0.925 — a real ensemble mismatch, in the
masking direction (it also explains the odd high-p pileup the old
`rem_presence_mc` rows fed into the v1 meta panel).

### M-3 Unstandardized ridge-CCA — **RESOLVED, shadow-rerun stable**
`ridge_cca_heldout_std` z-scores X/Y with train moments before whitening.
Shadow rerun: H_R3 draws-vs-covariates stays NULL (ρ=0.068, p=0.345); H_R4
positive control still detects the mechanism (ρ=0.992, p=0.005). The fix
opens the power channel for small-unit covariates without disturbing either
published verdict. Registered rerun required before the numbers are citable.

### M-4 Biased graphon attribution — **RESOLVED, rerun, conclusion sharpened**
`attribute_v2` removes the lead ball's row/col (no −c stripe) and uses
constrained 6-of-(P−1) nulls at K=999 (floor 0.001 ≤ threshold/2). Executed (exploratory shadow, same caveat as M-2):
6/55 without ball 45 → B1 = 24.50, p = 0.148 — the fire dissolves after
lead-ball removal; consistent with same-driving-rows, though reduced power
at the smaller T is not excluded (the measured ρ=0.988 closes that gap
independently). The
frozen version's anticonservative branch never actually misled (it also
concluded same-rows), but the corrected instrument now demonstrates it
cleanly, and the measured ρ(λ_max, B1) = 0.988 (below) explains why the
graphon flag was never independent evidence.

### M-5 Meta panel composition — **RESOLVED, panel v2 published**
`meta_uniformity.py` v2: ledger-driven (single source of truth), excludes
median-of-repeats rows (Beta-distributed), superseded rows, exploratory
rows, physical/equation rows; dedupes re-run statistics keeping latest;
reference = simulated discrete lattice with the panel's own m composition.
Result (panel v2.1, post-review): 126 tests, discrete meta p = 0.044,
10.3% ≤ 0.05 vs simulated band [2.4%, 8.7%] — **the panel now formally
flags a small-p excess**, replacing v1's falsely-comfortable continuous-KS
0.111. The flag is robust across four registered alternative compositions
(8.9–10.9%; `composition_sensitivity` in the JSON) and *concentrates* in
the traced #45 family: dropping the two 6/55 λ_max rows returns the panel
to the band edge (8.9%) — concentration measured, not asserted (review
M5.3). Rows from the miscalibrated col-permuted presence null are excluded
pending their registered rerun (review M5.1); the exploratory stratum is
reported separately so the honesty meter is not blind to it (review M-C).
Panel carries `panel_sha` (67eaafb4248d72b7).

### M-6 Stale doc numbers — **RESOLVED, synced with sha**
REMEDIATION_LOG.md, CASE_STUDY_1_PCSO.md, RESPONSE_EXTERNAL_REVIEW.md now
quote panel v2 with its sha and an explicit stale-transcription note.
`verify_relational_docs.py` pins panel_version, panel_sha, n, p, frac —
silent drift now fails the build.

### E-1 Double complexity penalty — **RESOLVED for v4; v2 learning downgraded**
`eq_selection_v4.select_family` = pure held-out NLL with train-σ² (optional
pre-registered 1-SE rule). Re-selection from stored v2 family_records:
claim B robust (B1 either way); claim A's A2-vs-A5 margin is 0.17 NLL —
within noise, while A5 had the best test NLL. v2 "capacity refuted" is
downgraded to open question (RESULTS_EQ_READJUDICATION.md §4).

### E-2 Multiplicity charged but never applied — **RESOLVED, executed**
`eq_verdict_correction.py` performs the deferred verdict-time step from the
ledger's cumulative charges (v1 m=5 → v2 m=8 → v3 m=9 → confirm1 m=10).
Corrected statuses: v1-B **AT_FLOOR_RESOLUTION_LIMITED** (p = floor exactly);
v2-B **FAIL_corrected** (0.00995 > 0.00639), and the design itself was
under-resolved at m=8 (B=200 < 313 required). v4 sets B via
`b_required(corrected_alpha(...))` and adjudicates in-run — deferral
language is banned from v4 registrations.

### E-3 Confirmation without baselines — **RESOLVED for future runs; confirm1 downgraded**
`beat_baselines` (registered climatology + textbook a-priori model) and
`confirmation_label` (same-source data caps at MECHANISM_CONSISTENT).
Confirm1's corrected status: **UNCONFIRMED** (pedigree FAIL_corrected + no
baselines + same integrator). Smoke test shows the discrimination working:
a frozen model that loses to the textbook baseline now fails confirmation.

### E-4/E-6 Bootstrap CI under misspecification; Fisher-g misuse — **RESOLVED for v4**
`profile_ci_omega` (profile-RSS, primary CI; smoke test covers the true
period) and `residual_scan_mc` (pre-whiten declared lines → single
AR-surrogate max-ordinate test; smoke test: detects a planted line at
p=0.005, silent at p=0.80 after pre-whitening). The v3 "36.34 d anomaly" is
downgraded to instrument artifact pending this re-test.

### E-5 Post-hoc bands/whitelists — **POLICY SET**
v4 requires a-priori tolerance bands (Rayleigh-overlap identifiability) and
whitelist from standard tables with an amplitude cutoff; the v2 evection
"✓" reads descriptive. No computation needed; encoded in
RESULTS_EQ_READJUDICATION.md §5.7 and the v4 module docstring.

### G-4 R1–R7 admissions below remediation standard — **RESOLVED, FULL RUN EXECUTED: all 7 ADMITTED_V2**
`readmit_r1_r7.py`: n_neg=200, m≥39 (floor 0.025 ≤ α/2), lattice-exact χ²
(expected bin masses from the actual add-one lattice, MC-calibrated p, FPR
band centered at the exact lattice P(p≤α) — the first version used flat
expectations and would have falsely demoted an 87%-calibrated instrument
87% of the time at m=39; caught by adversarial review B2 and fixed before
any full run completed), split rng_data/rng_null (the m6 fix the frozen
file never got),
frozen design hash, both outcome branches declared (FAIL → EXPLORATORY_ONLY,
the GW precedent). Smoke test green; full run executing at time of writing —
results land in `results/readmission_v2.json`; ADMISSION_RELATIONAL v2 doc
to be issued from it. Effect sizes unchanged from the original admissions
(re-run, not re-tune).

### G-5 Family registry fragmentation — **PARTIALLY RESOLVED** (review M-D)
`measure_equivalence.py` → `results/families.json`: canonical registry with
consumption rules, plus the H-protocol measurement ADMISSION_RELATIONAL
left "provisional", now executed on 200 shared synthetic H0 years:
**ρ_Spearman(λ_max, graphon-B1) = 0.988 → same family** (the C9 re-shadow
channel is now measured, not suspected — THEOREM_SYNTHESIS rows 27 and 38
were one instrument in two guises); half-corr and presence-skill are
independent (all |ρ| < 0.5). Ledger migration had already placed
graphon-b1-attribution in `hit-count-cooc`; the measurement retroactively
justifies it. **Honest scope (review M-D):** measured at T=155, P=55 only
(registry carries a scope stanza); the audit's headline unmeasured risk —
R5 cross-game spectra vs the hit-count-cooc class — has no shared scalar on
one game and REMAINS UNMEASURED (needs a dedicated H-protocol run); 4 of 8
families remain declared-only; and verifier consumption of families.json is
designed but not yet wired.

### Minors — status
1/2 (stale m_null, dead rng): `metadata_corrections_2026-07-02.json`;
corrected rng pattern used in all new modules. **Correction-of-correction
(review B1):** the initial 399→999 ledger fix for the ex-suspicious λ_max
row was WRONG — its raw_p 0.0025 = 1/400 lies only on the m=399 lattice, so
the frozen JSON was right and the current source postdates execution. Row
reverted same day with an `at_floor` flag; a p-lattice consistency check
(raw_p·(m+1) ∈ ℤ) is now design-verifier check 6, which would have caught
the error mechanically. The five floors-block rows stay at m=999 (their p's
lie only on the /1000 lattice). 3 (median-of-splits): excluded from panel v2; v4 uses
one registered split. 4 (powerlaw estimator fragility): documented in M1
note; instrument is exploratory-frozen. 5 (markov div-by-zero guard):
noted; frozen file, practically unreachable. 6 (single-trial gates):
superseded by the 200-trial harness standard. 7-12: recorded in the audit;
non-blocking; tracked for the next infrastructure pass.

## 3. New/changed artifacts

| Artifact | Role |
|---|---|
| src/migrate_ledger_v2.py | one-shot schema migration (idempotent, backup) |
| src/design_verifier.py (rewritten) | 5-check design gate, schema v2 |
| src/verify_relational_docs.py (updated) | schema v2 + panel v2 + doc pins |
| src/build_multiplicity_ledger.py / build_run_ledger.py (updated) | non-destructive |
| src/meta_uniformity.py (rewritten) | panel v2, discrete-aware, sha'd |
| src/corrected_reruns.py (+ results/corrected_reruns_2026-07-02.json) | M-1..M-4 corrected instruments, executed |
| src/eq_verdict_correction.py (+ results/eq_readjudication_2026-07-02.json) | E-2 verdict step, executed |
| src/eq_selection_v4.py (+ src/test_v4_smoke.py, results/v4_smoke.json) | E-1/E-3/E-4/E-6 machinery; smoke/validation tests PERSISTED as artifacts (review M4) |
| src/measure_equivalence.py (+ results/families.json) | G-5 registry + measured classes |
| src/readmit_r1_r7.py (+ results/readmission_v2.json, docs/ADMISSION_RELATIONAL_V2.md) | G-4 re-admission: R1–R7 all ADMITTED_V2 (n=200, m≥39, lattice-exact gate) |
| results/metadata_corrections_2026-07-02.json | R-B correction record |
| docs/RESULTS_EQ_READJUDICATION.md | corrected equation statuses + basis grid; RATIFICATION PENDING |
| docs/SUPERSEDED_LABELS.md | sidecar index frozen-label -> current status (review m-3) |
| src/lint_frozen_imports.py | two-truths guard: frozen-import lint (review M-E) |
| src/core/stats.py (rewritten) | canonical p_perm/sidak in core; frozen deps now lazy (audit minor #13) |
| commitment_ledger.txt | new snapshot appended (13 hashes) |
| multiplicity_ledger.jsonl | schema v2; +5 eq rows, +7 exploratory shadow rows |
| run_ledger.jsonl | +audit_shadow_2026-07-02 (G0, 7 tests) |

## 4. What remains open (honest list)

1. **Registered reruns** to make shadow numbers citable: presence-MC v2,
   standardized CCA, graphon attribution v2 (drafted as one registration;
   HUMAN-GATE approval required).
2. **eq v4 execution** (registration draft per §5 of the addendum;
   HUMAN-GATE): corrected selection, B≥399, in-run adjudication, calibrated
   residual scan on the 36.34 d question, baselines for any confirmation.
3. **readmission_v2 full results** → ADMISSION_RELATIONAL_V2.md once the
   background run completes (any FAIL demotes that instrument).
4. Manifest-level ledger completeness (results-JSON scraping) and
   registration-commit-order git check — designed, not yet implemented.
5. **Eval set** (CLAUDE.md trigger) — **EXECUTED 2026-07-02**
   (docs/RESULTS_EVAL_RERUN_2026-07-02.md): registered battery reproduces
   bit-identically on the remediated codebase (235 leaves, 0 diffs; Jun-11
   score carries over: specificity 1.000, sensitivity 0.826); corrected CCA
   variant: 0 verdict flips, true links strengthen. Residual scope: the eval
   set contains no equation units — v4's assembled pipeline still needs a
   sealed eval pack before its first real-data publication.
6. **HUMAN-GATE ratifications** — **DONE 2026-07-02**: Cha ratified all
   four verdict changes and the correction convention (Šidák .05,
   cumulative m — standing convention v1); recorded in
   RESULTS_EQ_READJUDICATION.md and the JSON artifact.
8. **R5-vs-hit-count-cooc H-protocol measurement** (the audit's original
   G-5 target) — still open.
9. **Sealed equation eval pack — BUILT 2026-07-02**: `evals/eq_eval_set_v1`
   (12 units: 5 nulls/traps-for-noise, 4 detect-class, 2 declared-borderline,
   1 era-bounded trap; deterministic seed 20260702; answer key + generator
   sealed via commitment-ledger hashes). Execution requires a FRESH agent
   that has not read the key (SEAL_NOTICE.md role separation) + human-approved
   registration — this pack gates v4's first real-data publication.

## 5. Adversarial review of these solutions — executed, findings remediated

Two independent reviewers attacked the fixes: a code-level reviewer (ran the
new code, constructed exploits in /tmp) and a methodology reviewer (attacked
the decisions and governance). Full reports preserved in the session record;
every finding and its disposition:

### 5.1 Code review — blockers (all fixed same day)

**B1 — My 399→999 ledger "correction" was itself wrong (the reviewer's
lattice proof: raw_p 0.0025 = 1/400 exists only on the m=399 lattice; the
frozen JSON was right; the frozen source was edited after commitment).**
Disposition: row REVERTED with `at_floor: true`; metadata-corrections record
carries a correction-of-correction entry; design-verifier check 6 now
enforces raw_p·(m_perm+1) ∈ ℤ on every test row — the class is closed
mechanically. This is the single most instructive finding of the day: the
audit trusted current source over the artifact's own arithmetic.

**B2 — The re-admission gate's flat-expectation χ² would falsely demote a
perfectly calibrated instrument 87% of the time at m=39.** Disposition: the
compromised background run was killed before any full result was written;
gate rebuilt with lattice-exact expected bin masses, MC-calibrated χ² p, and
the FPR band centered at the exact lattice P(p≤α); validated false-demotion
rate now 0.00–0.03; run relaunched.

**B3 — The "non-destructive" builder still dropped appended rows sharing a
key and stripped annotation fields (demonstrated).** Disposition: rebuilt —
disk fields all carry forward, unconsumed same-key disk rows are preserved,
and a full superset assertion aborts any lossy rebuild; the reviewer's two
exploit scenarios now pass (rerun row and quarantine annotation survive).

### 5.2 Code review — majors (all fixed)

M1 global_m drift on rebuild → shared live definition (excludes exploratory)
+ global_m pinned in verify_relational_docs. M2 gate-dodging (gate_based
abuse, exploratory abuse, total-only reconciliation — all demonstrated) →
gate_based restricted to a method whitelist; exploratory rows must reference
a G0 run-ledger entry; reconciliation now per-run. M3 readmission artifact
overclaim + smoke-overwrite channel → artifact table corrected; smoke
results write to separate keys. M4 uncited smoke evidence →
src/test_v4_smoke.py persisted with results/v4_smoke.json, including the
reviewer's stronger checks (profile-CI coverage 200 reps; residual-scan
calibration under AR(1) H0). During persistence the coverage test EXPOSED a
real defect the original smoke missed: the χ²-form profile CI undercovers
(~90%); fixed with the finite-sample F-form + half-grid-step widening →
coverage 0.94–0.965 across seeds. M5 panel composition → miscalibrated
presence rows excluded, alias-normalized dedup, exploratory stratum
reported, composition-sensitivity appendix published, "entirely
attributable" replaced by the measured concentration statement.

### 5.3 Code review — minors
b_required off-by-one fixed (312/195, brute-force-verified); the two
adjudicators unified (FAIL takes precedence over under-resolution);
'all' filter alias handled in the sensitivity check; direction-of-bias
wording corrected (masking, not false-positive); attribution verdict
carries the power caveat; eq v2-B ledger p re-rounded from source (0.01,
full value alongside); families.json overclaims rescoped.

### 5.4 Methodology review — blockers (dispositions)

**B-1 — Verdict changes without HUMAN-GATE ratification (confirm1 was
owner-ratified; de-adjudication is a verdict act).** Disposition: accepted
in full. The readjudication addendum now opens with a ratification table;
all four status changes read "computed; ratification pending" until Cha
signs. Standing rule adopted into the addendum: changing a verdict label on
a hash-committed claim requires the approval class of the registration that
produced it.

**B-2 — The correction convention was discretionary and chosen
post-outcome; v2-B's FAIL does not survive per-run or playbook-H-4
readings.** Disposition: accepted. Full 6-basis sensitivity grid computed
and published (addendum §2b + JSON); v2-B labeled basis-dependent; the
H-4-vs-cumulative contradiction is surfaced and its resolution assigned to
the ratification decision. Conceded by the reviewer: confirm1's downgrade is
overdetermined regardless of basis; v1-B is at-floor under every basis.

### 5.5 Methodology review — majors (dispositions)

M-A empty §5 stub → this section. M-B unregistered shadow results doing
citational work → conclusions rewritten as exploratory indications
(§M-2/M-4 above); registered rerun must disclose the look and use fresh
seeds. M-C exploratory row class re-opens the free-look hole → bounding
rules adopted (below); exploratory stratum now visible in the meta panel
artifact; verifier requires G0 linkage. M-D families.json scope → registry
carries a scope stanza (measured@T155P55), statuses corrected
(knn-recovery NOT measured; R5 coupling REMAINS UNMEASURED), G-5 restated
as PARTIALLY RESOLVED. M-E two-truths repo → src/lint_frozen_imports.py
(header-comment detection, wrapper allowlist, core-shim debt tracked);
core/stats.py rewritten so core no longer drags frozen modules at import
time. M-F artifact-table overclaim + eval obligation → table corrected;
eval-set run remains a BLOCKING precondition for the next verdict-bearing
publication (§4.5).

**Adopted exploratory-row rules (M-C):** (1) an exploratory row must link to
a G0 run-ledger entry (verifier-enforced) and to a registered follow-up or
abandonment record; (2) a registered test whose hypothesis was touched by an
exploratory row must disclose it and use fresh randomness, or charge the
look; (3) the exploratory stratum is published alongside every panel; (4)
exploratory numbers are never citable in verdict-bearing docs.

### 5.6 What both reviewers could not break (their words, condensed)
Add-one p-values, Šidák/floor arithmetic, the discrete lattice reference,
seed hygiene in all new code, 0/1-indexing at every boundary, the
readjudication input numbers against the frozen JSONs, panel v2
bit-reproducibility, the v4 tools' statistical soundness (profile CI
coverage, scan calibration, b_required by brute force), builder behavior on
reordered disk rows, and the run/test reconciliation. And the methodology
reviewer's central concession: **every verdict change cut against the lab's
own positive results** — the direction of motivated reasoning is absent.

### 5.7 Corrections the review forced on the audit itself
The audit (AUDIT_CORRECTNESS) claimed the ex-suspicious λ_max block ran 999
nulls; that was wrong (B1). The audit's M-2 wrote "false-positive channel";
the measured direction is masking. Both corrections are recorded where the
original claims were made. An audit that cannot be corrected by review is
not an audit.
