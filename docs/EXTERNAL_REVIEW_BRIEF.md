# External Review Brief — Structure Discovery Laboratory

**Document**: EXTERNAL_REVIEW_BRIEF · **Version**: 1.1 · **Status**: active ·
**Supersedes**: 1.0 (any earlier copy without this header) ·
**SHA-256**: recorded in `results/commitment_ledger.txt`

**Purpose**: hand this document (plus repository access) to an independent
system or reviewer to audit the lab's processes, methodologies, and approaches.
**Prepared**: 2026-06-11. **v1.1 note**: one external review has been received
and answered (`docs/RESPONSE_EXTERNAL_REVIEW.md`); a remediation batch
(`docs/REMEDIATION_LOG.md`) post-dates the materials that review saw. New
reviewers should still review independently before reading either.

> **Anchoring control — read this first.** A self-review exists at
> `docs/ADVERSARIAL_REVIEW.md`. Do **NOT** read it until you have completed and
> written your own findings. Independent discovery of its issues (or of issues
> it missed) is the point of this exercise. Compare afterwards.

---

## 1. What this lab is

A statistical laboratory testing one hypothesis class: *do PCSO lottery draws
(5 games, 776 validated draws, Jun 2025–Jun 2026) deviate from i.i.d. uniform
on any of five "faces" of randomness* — statistical, dynamical, algorithmic,
cross-sectional/physical, and relational (cross-dataset / subset-to-whole)?
Physical covariate datasets (tides, sun/moon ephemerides, geomagnetics,
atmospheric pressure) serve as paired controls. The lab's published verdict:
everything null except one era-bounded 2025 anomaly (6/55 number 45), with the
decision layer concluding no playable edge.

## 2. Repository map (review in this order)

| Layer | Files |
|---|---|
| Constitution & governance | `docs/THEOREM_GOVERNANCE.md` (conflicts C1–C10, articles A1–A7, onboarding Parts 3–4) |
| Theory | `docs/THEOREM_SYNTHESIS.md` (implication lattice + results ledger rows 1–37), `docs/CROSS_DATASET_FRAMEWORK.md` (relational face) |
| Method cards | `docs/kb/INDEX.md` → 26 cards (esp. rows 20–26, the relational instruments) |
| Protocols | `docs/RUNBOOK.md`, `docs/RELATIONAL_RUNBOOK.md`, `docs/AGENT_WORKFLOW.md`, `docs/EVALUATION_PROTOCOL.md` |
| Registrations (written before runs, allegedly) | `docs/REGISTRATION_BATCH4.md`, `_BATCH5.md`, `_BATCH6.md`, `_BATCH7.md` |
| Results | `docs/RESULTS_BATCH4.md`, `docs/ADMISSION_RELATIONAL.md`, `docs/RESULTS_RELATIONAL_FIRSTRUN.md`, `docs/RESULTS_BATCH5.md`, `_BATCH6.md`, `docs/RESULTS_PRESSURE.md` |
| Code | `src/*.py` — esp. `relational_admission.py`, `relational_first_run.py`, `relational_batch5.py`, `relational_allgames.py`, `relational_subsets.py`, `relational_batch7.py`, `relational_pressure.py`, `make_relational_figures.py`, `verify_relational_docs.py` |
| Raw outputs (ground truth for every published number) | `results/*.json`, figures in `results/figures/` |
| Data + provenance cards | `datasets/<id>/DATASET.md` + raw/derived files (5 datasets) |
| Public surface | `lotto_picker.html` (claims shown to end users) |

## 3. The claims register (what you are auditing)

1. **Admission**: 7 relational instrument families are calibrated (FPR ≈ α on
   independence) and powered (detect planted structure) — `ADMISSION_RELATIONAL.md`.
2. **Structure where physics is**: tidal/lunar/seasonal/pressure series show
   subset-to-whole recovery, persistent H₁ loops, seasonal regime shifts, and
   cross-dataset couplings with known mechanisms (ledger rows 30–33, 36–37).
3. **Null where the machine is**: five lotto games show no temporal,
   frequency, topological, cross-game, cross-segment, or covariate-coupled
   structure at any tested resolution (rows 30–36), beyond one already-known
   era-bounded anomaly (#45) that re-appears as a traced "shadow" in every
   hit-count statistic (conflict C9).
4. **Decision layer**: no betting edge exists; uniform random picks with
   split-risk filters are optimal (`lotto_picker.html` footer).

## 4. Review mandates (attack these specifically)

**A. Pre-registration integrity.** Registrations and runs were authored by the
same agent in the same session. Assess what the "registered before execution"
labels are actually worth, and what minimal commitment infrastructure would
make them verifiable.

**B. Null-model correctness.** For each experiment, check the null against the
framework's own rule ("preserve every nuisance, destroy only the claimed
relationship", CROSS_DATASET_FRAMEWORK §6.2). Look for claim-type/null
mismatches (§1.2 taxonomy), autocorrelation leaks, and floors: compare each
permutation count m against the multiplicity-corrected threshold the verdict
cites.

**C. Admission hygiene.** The suite (`relational_admission.py`) was tuned
during development (statistics and planted effect sizes changed after observed
failures — changes are documented in `ADMISSION_RELATIONAL.md`). Decide
whether the "power 1.00" claims carry evidential weight, and what a clean
admission protocol would look like.

**D. Data quality propagation.** `datasets/pcso-lotto/DATASET.md` §4 reports
576/776 rows single-source and 3 suspicious rows. Trace whether downstream
experiments handled row status, and what sensitivity analysis is required
before any hit-count statistic is trusted. (A sensitivity artifact exists at
`results/sensitivity_655_suspicious.json` — check it *after* forming your own
view of what should have been done.)

**E. Power honesty.** For every published null, determine the smallest effect
the test could plausibly have detected (admission effects, n≈155 draws/game,
m values), and judge whether published language ("no structure") matches
demonstrated resolution.

**F. Multiplicity accounting.** Count every real-data test across the
relational program; check within-run corrections against the lab's own A3
standard (class-level global m, equivalence classes for correlated statistics);
verify the C9 "one anomaly, many shadows" accounting for #45 (rows 27, 32, 35).

**G. Independence and stability.** Identify where correlated repeats,
shared rng streams, single train/test splits, or same-dataset reuse (positive
controls doubling as covariates) weaken the stated confidence.

**H. Verification depth.** `verify_relational_docs.py` re-derives published
numbers from JSONs. Determine what classes of error it can and cannot catch,
and whether any published claim depends on logic the verifier never touches.

**I. Communication integrity.** Compare `lotto_picker.html` claims against the
underlying results: any overstatement, understatement, or precision theater?

**J. Reproduction.** Pick at minimum: one admission family, one positive
control (e.g. tidal H₁ or B7-1 seasons), and one null (e.g. 6/55 presence
recovery). Re-run from the seeds in the scripts; confirm the JSONs regenerate.
All scripts are standalone Python (numpy/scipy/pandas/POT/ripser/networkx/persim).

## 5. Known constraints (context, not excuses)

Compute ran in a sandbox with ~45-second execution windows, which influenced
permutation counts, trial counts, and subsample sizes. The pressure dataset is
single-source (ERA5 via user-downloaded export; card §3 caveat). The lab's
prior within-dataset program (ledger rows 1–28) predates this review scope but
shares the constitution.

## 6. Deliverable format

Findings classified Critical / Major / Minor, each with: the artifact and line
it concerns, the failure mode, whether any published verdict changes, and a
concrete remediation. Conclude with: (a) which of the four claim groups in §3
survive your review, (b) a list of issues you found that the lab's own
adversarial review missed (read `docs/ADVERSARIAL_REVIEW.md` only at this
final step), and (c) the three highest-value process changes.
