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
5. **Expected outcome** — written down in advance (the first run's H-R1…H-R4 are the
   template). A predicted *negative* is a registrable expectation.
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
