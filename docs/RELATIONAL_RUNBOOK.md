# Relational Runbook — Hypothesis → Experiment, Every Claim Earns Its Evidence

**Scope**: operating procedure for every cross-dataset / subset-to-whole claim in this
lab. Companion to `CROSS_DATASET_FRAMEWORK.md` (theory), `THEOREM_GOVERNANCE.md`
(constitution), `RUNBOOK.md` (the within-dataset six-phase cycle), and
`AGENT_WORKFLOW.md` (who executes what). **The rule this document exists to enforce:
no claim without a registered experiment; no experiment without a matched null; no
instrument without admission.**

---

## Phase 0 — Eligibility gates (before any hypothesis is written)

| Gate | Requirement | Where |
|---|---|---|
| Dataset gate | both datasets onboarded with completed `DATASET.md` cards | Governance Part 4, D1–D6 |
| Instrument gate | instrument has a KB card AND passed admission | KB cards 20–26; `docs/ADMISSION_RELATIONAL.md` |
| Shape gate | admission shape ≈ real-data shape, else re-run the negative control at matched shape | Part 4 D7 |
| Era gate | era registries of both datasets consulted; claims never span undeclared era boundaries | A5 |

Currently admitted relational instruments: R1–R7 (all, 2026-06-11 — see the
admission report for shapes and power statements).

## Phase 1 — Hypothesis registration (one page, written BEFORE running anything)

Every relational hypothesis is registered with exactly these fields:

1. **Claim type** — one of the eight in framework §1.2 (similarity / scalar distance /
   alignment map / subset-to-whole / predictive generalization / latent sharing /
   topological correspondence / causal). Causal claims stop here unless an
   intervention or environment-heterogeneity design exists.
2. **Representation bundle** — the ONE declared representation per dataset
   (embedding/distance/graph/diagram). Extra representations are charged (C10).
3. **Instrument + statistic** — from the admitted list; sidedness declared.
4. **Matched null** — from the null table (framework §6.2); state what it preserves
   and the one thing it destroys.
5. **Decision rule & falsification criteria** — what statistic, what threshold,
   what would count against the null AND against the alternative.
   **(Amended 2026-06-11, lab-owner directive + ADVERSARIAL_REVIEW bias
   finding): discovery tests carry NO outcome expectations.** Predicted results
   are forbidden in registrations; they bias design and reading. Mechanism
   predictions are permitted only as *instrument-validity controls* ("the
   pipeline must detect X or the pipeline is broken"), clearly labeled as
   calibration, never as discovery. Registrations are **git-committed before
   the run script produces results** (C1 remediation); results commits
   reference the registration SHA.
6. **Multiplicity charge** — which equivalence class this run joins; new m if a new
   class is created (A3).
7. **Era/freeze declaration** — which rows are exploration, which are confirmation
   (A6); held-out data named before it is touched.

Registration lives in `docs/REGISTRATION_<batch>.md` (same convention as batch 4).

## Phase 2 — Experiment execution (the only admissible designs)

Every claim type maps to one experiment skeleton. No other path to a claim exists.

| Claim | Skeleton | Null | Decision rule |
|---|---|---|---|
| Distributional similarity/difference | two-sample statistic on the declared shared space | pool-and-relabel (block variant if temporal) | p ≤ α/m, +1-corrected |
| Scalar structural similarity | T(D_A, D_B) | matched-marginal regeneration | observed below null α-quantile |
| Alignment map | fit coupling/matching on S_A,S_B only; freeze; score once on H_A,H_B | random/shuffled couplings; degree-preserving rewiring for graphs | held-out distortion/retrieval beats null |
| Subset-to-whole | recovery curve over k ∈ {1,2,5,10,20,40}%, ≥10 seeds, m ≥ 49 | marginal baseline + permuted-target + (for draws) the A1 constrained generator | curve rises above null band; flat = honest negative |
| Predictive generalization | train on A (or S), freeze, score once on held-out B (or H) | shuffled A–B pairing | held-out skill beats null |
| Latent sharing | CCA-family held-out protocol | shuffled held-out pairing | held-out ρ beats null; in-sample ρ is never cited |
| Topological correspondence | diagram distance | matched-density geometric null | distance below null α-quantile |

Execution requirements (all from the constitution, all non-negotiable):
seeded and deterministic; the +1 permutation correction; results written to
`results/*.json` *by the script* — every number in any document must be recomputable
from a JSON the script wrote (no hand-transcribed values; each results doc carries
its recompute snippet, as `ADMISSION_RELATIONAL.md` does).

Added by REMEDIATION_LOG (2026-06-11):
- **Floor rule (M3)**: the permutation count m must satisfy
  1/(m+1) ≤ corrected-threshold/2, or the run is inadmissible.
- **Gate rule (M2)**: negative-control gates use ≥200 trials; calibration is
  checked with the lattice-aware χ² (KS against continuous uniform is invalid
  for discrete permutation p-values).
- **Meta panel (M6)**: every batch appends its real-data p-values to the
  global meta-uniformity panel (`src/meta_uniformity.py`).
- **Data-regime sensitivity (M4)**: every hit-count statistic reports
  {all / ex-suspicious / verified-only} variants.
- **Stability vs power (M5)**: per-seed rates on one dataset are reported as
  seed-stability, never as power.
- **Instrument status (M2/A4)**: GW is exploratory-only — its
  moment-matched-regeneration null is FPR-correct at α=0.05 but fails
  full-distribution calibration at n=200; redesign pending.

Added from the external review (RESPONSE_EXTERNAL_REVIEW.md, 2026-06-11):
- **Design verifier**: `src/design_verifier.py` must PASS before any results
  doc is published (claim↔method map, floor rule per family, sensitivity
  presence). Complements the numeric verifier.
- **Global ledgers** (three levels, cross-checked):
  *run-level* — `results/run_ledger.jsonl` (one row per experiment execution:
  script, stages, seeds, registration artifact, output SHA, verifiers, grade;
  append-only via `build_run_ledger.append_run`, duplicate run_ids refused);
  *test-level* — `results/multiplicity_ledger.jsonl` (one row per real-data
  p-value; totals must reconcile with the run ledger);
  *file-level* — `results/commitment_ledger.txt` (SHA-256 hashes).
- **Evidence grades**: every claim carries a G0–G6 grade (ladder in
  RESPONSE_EXTERNAL_REVIEW.md).
- **Shape fields**: result tables carry `admitted_for_shape` /
  `real_data_shape` / `shape_match`.
- **Environment capture**: `results/environment.json` regenerated with each
  ledger rebuild.
- **Domain neutrality (SANITIZATION.md, 2026-06-11)**: new scripts import only
  `src/core` + one `src/domains/<domain>.py`; `src/lint_domain_neutrality.py`
  must PASS before publication. Historical scripts are FROZEN records.

## Phase 3 — Mandatory checks before any verdict (the §6.3 checklist, ordered)

1. Permutation/randomization p, +1-corrected, at the A3-corrected threshold.
2. Bootstrap + subsample stability (A4) — a flag that vanishes under resampling is
   not a flag; a single admissible flag against a claim defeats it (passes never
   outvote a flag).
3. Metric/kernel sensitivity (C8): survives ≥2 reasonable choices or is reported as
   single-metric-dependent (and the sweep is charged).
4. **C9 row trace**: trace any positive to driving rows; if the rows underlie a known
   anomaly (the #45 set is the standing example), the flag joins that anomaly's
   equivalence class and is reported as a shadow, not a discovery.
5. Era attribution (A5): does the relation survive within each declared era?
6. Held-out confirmation (A6): exploration motivates, only the registered frozen
   test confirms; scoring H more than once voids the result (A7).

## Phase 4 — Reporting (dual report, asymmetric verdicts)

Every run reports: observed value · position in the null distribution · corrected p ·
power statement (what effect size the instrument could have seen — the admission
power curve is the reference) · curve shape classification for recovery claims
(§4.5 taxonomy) · explicit claim-strength tier (framework §9: weak / moderate /
strong / strongest-practical). Negative results are first-class deliverables and use
the same template (see `RESULTS_RELATIONAL_FIRSTRUN.md` — three positives, three
predicted-and-confirmed nulls).

### Five-tier verdict taxonomy (adopted 2026-06-11, admin recommendation)

Every reported verdict is assigned exactly one of the following tiers. Tier
annotations for the blind-eval baseline live in
`results/blind_eval_verdict_tiers.json`.

| Tier | Definition | Counts in accuracy? |
|---|---|---|
| **STRUCTURED** | Instrument returned p ≤ corrected α; verdict stands. | Yes (TP) |
| **NULL** | Instrument returned p > corrected α at tested resolution. Does not prove absence — bounded by admission power curves. Qualifier: "below detection at these shapes, not proof of absence." | Yes (TN or FN) |
| **NEAR_MISS_REGISTERED_SIGNAL** | Raw p below 0.10 but above corrected α. Signal may be real (near-threshold FN) or a noise excursion on null data (correctly held below verdict). Triggers pre-registered replication or follow-up; never used in public claims. | No — reported separately |
| **EXPLORATORY_ONLY** | GW (G0) or any instrument not yet admitted. Real signal may be present but the instrument cannot issue a verdict pending calibration completion. | No — reported separately |
| **OUT_OF_SCOPE** | Structure type is real but no registered claim covers it (coverage gap, instrument-gap, or registration-scope limitation). Not scored as FN. | No — reported as scope gap |

**Rules (non-negotiable):**

1. **NEAR_MISS never STRUCTURED.** A NEAR_MISS_REGISTERED_SIGNAL result never counts
   as STRUCTURED in any accuracy table, public report, web deliverable, or
   decision-layer document. It triggers a pre-registered replication experiment only.

2. **NEAR_MISS triggers replication.** When a NEAR_MISS involves a real signal
   (ground truth STRUCTURED and raw p below 0.10), it triggers a pre-registered
   follow-up experiment charged to the multiplicity ledger. The follow-up is registered
   before it runs (C1 rule); its design cannot be adjusted after the near-miss is seen.

3. **NEAR_MISS never public.** Near-miss results are never cited in public claims,
   press releases, web deliverables, or decision-layer documents. They appear only in
   internal runbook records and the tier annotation file.

4. **Latent-triangulation sub-tag (LATENT-SUPPORTED/NEEDS-CONFIRMATION).** When
   instrument pairs confirm: (A-Z STRUCTURED) AND (B-Z STRUCTURED) AND (A-B is
   NEAR_MISS_REGISTERED_SIGNAL), the tag LATENT-SUPPORTED/NEEDS-CONFIRMATION may be
   applied to the A-B claim. This sub-tag signals that a shared latent mechanism is
   plausible and warrants a direct A-B test at higher power. It is never
   auto-upgraded to STRUCTURED; it is never used in public claims; it registers a
   pre-registration target only.

5. **Coverage reporting separation.** Registered-claim accuracy (TP/TN/FP/FN) is
   reported separately from each of: coverage gaps (OUT_OF_SCOPE), instrument-blocked
   detections (EXPLORATORY_ONLY), near-threshold detections
   (NEAR_MISS_REGISTERED_SIGNAL), and out-of-scope structures. These four categories
   are never pooled with the accuracy tally. Every eval report must include a
   "Coverage and gaps" section alongside the confusion matrix.

## Phase 5 — Ledger and synthesis integration

Add a row to THEOREM_SYNTHESIS §5; update the C9 standing-shadow list if a new
anomaly's rows are identified; update the KB card's "use in this project" field; log
in RESEARCH_NOTES with a section number. Promotion of an exploratory relational
finding into the confirmation family happens only at a confirmation-set reset
boundary (Part 3 Step 8).

## Phase 6 — Decision layer (unchanged, one-way)

Relational verdicts flow forward to the decision theorems exactly like within-dataset
ones: Doob gates (is there an edge?), EV measures, Kelly sizes. A relational
"similarity" or "alignment" with no held-out predictive skill **never** reaches the
decision layer — it is structure, not edge. Nothing in the relational face changes
the standing decision verdict for the lottery datasets: no strategy, no stake.

---

## Worked instantiations (current registry)

| Run | Status | Where |
|---|---|---|
| Admission suite E1–E8 synthetic controls (R1–R7) | **complete, all admitted** | `src/relational_admission.py` → `results/relational_admission.json` |
| First registered run: tidal / sun-moon / Kp / lotto recovery curves + paired CCA (H-R1…H-R4) | **complete, all four expectations confirmed** | `src/relational_first_run.py` → `results/relational_first_run.json` |
| Cross-game co-occurrence graph comparison (R5) | candidate next batch — requires registration page + matched-shape negative control + C9 row trace | — |
| Witness-complex topology recovery on delay-embedded tidal vs draws (R4) | candidate next batch | — |

## Agent routing (per AGENT_WORKFLOW)

The **onboarder** writes/updates KB and dataset cards and runs admission; the
**analyst** writes the registration page, designs nulls, runs Phase 2–3, and
interprets; the **editor** copies results into web/docs surfaces, copy-only.
Checkpoint rule applies: each phase ends with results written to disk before the
next begins (a dropped run resumes from the last JSON, as the chunked admission
suite does).
