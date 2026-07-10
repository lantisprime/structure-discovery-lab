# Lab Reliability and Accuracy Improvement Plan

**Plan ID:** `LAB-RELIABILITY-2026Q3`
**Version:** 1.0
**Created:** 2026-07-10
**Status:** IN PROGRESS -- Milestone 0 complete; Milestones 1-6 planned
**Scope:** prospective lab infrastructure, statistical controls, provenance, and
verification
**Implementation plan:** `docs/plans/LAB_RELIABILITY_M0_IMPLEMENTATION_PLAN.md`
(Milestone 0)

## 1. Objective

Increase confidence that every new lab result is statistically valid,
reproducible from a clean environment, traceable to immutable inputs, and
independently verifiable.

This program improves the reliability of conclusions. It does not make a truly
random process predictable, and completing infrastructure work does not upgrade
an experiment's evidence grade. In particular, the 2026-07-08 PCSO batch remains
`G0` unless a future, prospectively registered experiment satisfies the evidence
ladder independently.

## 2. Operating constraints

1. **Prospective changes only.** Frozen historical registrations, results, and
   hash-committed artifacts remain byte-identical. Corrections are additive
   records or new versioned runs.
2. **No evidence upgrade by tooling.** Better software can make a result easier
   to trust, but cannot repair prior peeking, retrospective registration, missing
   raw inputs, or insufficiently independent verification.
3. **One source of truth.** Machine-readable records own parameters and numbers;
   Markdown reports and workbooks are generated views.
4. **Gates before convenience.** The webapp and CLI must call the same validation
   and execution code. A UI action cannot bypass a scientific gate.
5. **Acceptance is mechanical.** A work package is complete only when its listed
   checks run automatically and pass from a clean checkout.

## 3. Current baseline

| ID | Finding | Consequence | Priority |
|---|---|---|---|
| B1 | Registrations and role-separation rules are primarily Markdown contracts. | Parameter drift, missing approvals, or self-verification can escape mechanical rejection. | P0 |
| B2 | `requirements.txt` lists three broad lower bounds while the code imports additional scientific packages. | A rerun can silently use materially different numerical libraries or fail on a clean machine. | P0 |
| B3 | The main scientific code has sparse unit and property coverage relative to its surface area. | Statistical and artifact-contract regressions rely too heavily on end-to-end snapshot checks. | P0 |
| B4 | Registrations, results, provenance, and JSONL ledgers do not share versioned schemas. | Malformed or incomplete records can become de facto interfaces. | P0 |
| B5 | Repeated looks, representation choices, null validity, and Monte Carlo resolution are not governed by one executable experiment contract. | The reported family-wise error rate can differ from the advertised rate. | P0 |
| B6 | Raw primary-source captures and complete space-weather covariates are not consistently available. | Input lineage cannot always be reconstructed; some covariate tests are non-computable. | P1 |
| B7 | The webapp lacks a PCSO weekly verifier job, and its commit action omits dataset, workbook, and repository-policy artifacts. | A webapp-only closeout can be unverifiable or committed incompletely. | P0 |
| B8 | Some verifiers pin global counts or exact snapshots instead of validating schemas and semantic invariants. | Valid additions require verifier edits and may encourage weakening a gate to accommodate growth. | P1 |

Baseline evidence is visible in `docs/AGENT_WORKFLOW.md`, `requirements.txt`,
`webapp/server.py`, `src/verify_relational_docs.py`, and
`src/pcso_weekly_update.py`.

## 4. Target controls

All prospective registered runs must eventually satisfy these controls:

- `C1` -- schema-valid registration approved before holdout access;
- `C2` -- immutable hashes for registration, code, environment, and every input;
- `C3` -- calibrated null with synthetic type-I error and power evidence;
- `C4` -- experiment-wide multiplicity and sequential-look allocation;
- `C5` -- deterministic, order-independent random streams and declared MC resolution;
- `C6` -- atomic, schema-valid result and ledger writes;
- `C7` -- mechanically distinct author, executor, and verifier identities where required;
- `C8` -- independent recomputation for headline statistics, not only same-code replay;
- `C9` -- report and workbook values generated from committed machine-readable results;
- `C10` -- one command reproduces and verifies the run from a clean environment.

## 5. Work plan

### Milestone 0 -- Close operational holes

**Priority:** P0
**Status:** COMPLETE (2026-07-10)
**Depends on:** none

- [x] Add a `pcso_weekly_verify` webapp job that invokes the canonical runner in
  verification mode.
- [x] Replace the hard-coded webapp commit path list with an explicit closeout
  manifest or repository-wide staged-path preview requiring human confirmation.
- [x] Include `datasets/`, the PCSO workbook, `.gitattributes`, and provenance
  artifacts when they belong to the approved closeout.
- [x] Show the exact command, input hashes, output hash, exit status, and dirty-tree
  comparison in the webapp verification result.
- [x] Add routing and job-definition tests for the new workflow.

**Acceptance gate M0**

1. A webapp-only dry run reproduces the canonical PCSO result hash.
2. The staged-path preview contains every intended July closeout artifact and no
   unrelated file.
3. Existing webapp tests and the new closeout tests pass.

### Milestone 1 -- Reproducible environment and continuous integration

**Priority:** P0
**Status:** PLANNED
**Depends on:** M0 only for preferred execution order

- [ ] Declare the supported Python version and complete direct dependencies in
  `pyproject.toml`.
- [ ] Produce a fully pinned, hashable lockfile. Separate core, webapp, PCSO, and
  Riemann extras where their dependency sets differ.
- [ ] Add a clean-environment CI workflow for schema checks, unit tests, verifiers,
  and deterministic artifact replay.
- [ ] Record Python, OS, architecture, dependency-lock hash, and relevant numerical
  library versions in every new run bundle.
- [ ] Add a dependency-import test so an undeclared scientific dependency fails CI.

**Acceptance gate M1**

1. A clean checkout installs without manual package discovery.
2. The supported environment runs the full fast verification suite successfully.
3. Two clean installs produce the same deterministic fixture hashes.

### Milestone 2 -- Machine-readable experiment contracts

**Priority:** P0
**Status:** PLANNED
**Depends on:** M1

- [ ] Add versioned schemas for registrations, results, provenance, run-ledger
  rows, and multiplicity-ledger rows.
- [ ] Define required registration fields: frozen inputs, hypotheses, statistics,
  null generator, exclusions, representation family, alpha allocation, sequential
  plan, MC budget rule, seed derivation, code entry point, and approval identity.
- [ ] Make runners consume registration JSON directly. Generate registration
  Markdown from the validated record.
- [ ] Introduce `lab validate`, `lab run`, and `lab verify` entry points, or
  equivalent commands, shared by the CLI and webapp.
- [ ] Write results and ledgers through temporary files plus atomic replacement;
  reject partial or schema-invalid transactions.
- [ ] Migrate living records with explicit schema versions. Do not rewrite frozen
  historical records solely to normalize their format.

**Acceptance gate M2**

1. Mutation tests show that changing a registered threshold, input, seed scheme,
   or statistic causes execution to fail before data analysis.
2. Truncated and malformed result or ledger writes leave the prior valid state intact.
3. Markdown registrations reproduce from their JSON source without numeric drift.

### Milestone 3 -- Statistical accuracy gates

**Priority:** P0
**Status:** PLANNED
**Depends on:** M2

- [ ] Require each test to declare why observations are exchangeable under its
  null. Use restricted permutations for blocks or an exact generative simulator
  when global row permutation is not justified.
- [ ] For lottery confirmations, simulate the registered game, draw schedule, and
  fixed covariate layout under `H0`; preserve duplicate-date and game structure.
- [ ] Add a prospective sequential policy covering every planned weekly look.
  Prefer a simulated maximum statistic over all registered metrics and looks;
  use an always-valid or alpha-spending design when the stopping rule requires it.
- [ ] Charge representations, transformations, exclusions, and method variants to
  the central multiplicity ledger before execution.
- [ ] Report MC exceedances `b`, simulations `B`, `(b+1)/(B+1)`, the attainable
  p-value floor, and a binomial uncertainty interval.
- [ ] Register an adaptive simulation rule that increases `B` when Monte Carlo
  uncertainty overlaps the decision boundary.
- [ ] Derive independent random streams from a stable hash of registration ID,
  test ID, and replicate ID. Record the RNG algorithm and version.
- [ ] Build synthetic calibration fixtures for every admitted instrument: matched
  nulls for false-positive control and planted alternatives for power.

**Acceptance gate M3**

1. Each admitted instrument passes its preregistered empirical type-I error bound.
2. Each instrument has a documented power curve or remains explicitly exploratory.
3. Reordering or adding unrelated tests does not change an existing test's output.
4. A repeated-look fixture demonstrates experiment-wide error control at the
   registered level.

### Milestone 4 -- Provenance, holdout, and independent verification

**Priority:** P1
**Status:** PLANNED
**Depends on:** M2 and M3

- [ ] Build primary-source adapters that retain immutable raw responses, retrieval
  timestamps, source URLs, parser versions, normalized rows, and hashes.
- [ ] Use official PCSO results as the primary lottery source and record independent
  corroboration separately. Retrieve definitive GFZ Kp observations when available.
- [ ] Emit one immutable run bundle linking entities, activities, and agents:
  registration, raw inputs, normalized inputs, code, environment, command, outputs,
  author, executor, verifier, and approvals.
- [ ] Mechanically seal confirmation data until the registration hash and human
  approval are recorded. Log the unseal event.
- [ ] Enforce role-ID inequalities from `AGENT_WORKFLOW.md`; represent unavailable
  provider session IDs explicitly rather than inventing them.
- [ ] Require a second implementation or independently derived calculation for
  statistics supporting `G3+` claims. Same-code byte replay remains a separate
  reproducibility check.
- [ ] Add source-drift fixtures so upstream HTML or API changes fail closed rather
  than silently changing parsed data.

**Acceptance gate M4**

1. A result can be traced from report number to output field, execution activity,
   exact code/environment, normalized input, and raw source capture.
2. Attempted holdout access before approval fails and is audited.
3. Self-verification or a missing required identity makes a run unpublishable.
4. The independent implementation agrees within its registered tolerance.

### Milestone 5 -- Maintainability and publication integrity

**Priority:** P1
**Status:** PLANNED
**Depends on:** M1-M4

- [ ] Add focused unit and property tests for core statistics, parsers, ledger
  reconciliation, p-value lattices, formula generation, and report rendering.
- [ ] Replace global-count snapshot assertions with schema checks and semantic
  invariants such as uniqueness, referential integrity, monotonic append history,
  and declared family accounting.
- [ ] Make the PCSO workbook a generated view. Validate formulas by sheet and cell
  identity, not only aggregate formula count.
- [ ] Add a method-change gate: changes to a null, statistic, representation,
  exclusion, threshold, or stopping rule require a new registration version and
  renewed calibration.
- [ ] Generate reports only from validated results; fail publication when a number
  cannot be traced to a machine-readable field.
- [ ] Produce a release manifest with artifact hashes and verification status.

**Acceptance gate M5**

1. Adding a legitimate ledger row does not require editing an expected global count.
2. A changed workbook formula or untraceable report number fails verification.
3. A registered-method change is detected before it can overwrite prior evidence.
4. The release manifest verifies every distributed artifact.

## 6. Delivery sequence

Use small, reviewable changes in this order:

| Change set | Contents | Required gate |
|---|---|---|
| 1 | Webapp verifier job and safe closeout staging | M0 |
| 2 | Complete dependency declaration, lockfile, clean CI | M1 |
| 3 | Schemas, registration source of truth, atomic artifact writes | M2 |
| 4 | Null contracts, RNG streams, MC uncertainty, calibration suite | M3 |
| 5 | Sequential multiplicity controller and prospective PCSO registration | M3 |
| 6 | Raw-source adapters, run bundles, holdout seal, role enforcement | M4 |
| 7 | Independent recomputation, generated workbook, semantic verifiers | M5 |

Do not combine a statistical-method change with a historical artifact migration in
the same change set. Reviewers must be able to distinguish evidence changes from
infrastructure changes.

## 7. Program metrics

Track these values in CI or the lab console:

| Metric | Target |
|---|---|
| New registered runs passing schema validation | 100% |
| New real-data runs with prior synthetic calibration | 100% |
| New published values traceable to result fields | 100% |
| New confirmation runs with declared sequential allocation | 100% |
| New run bundles with input, code, environment, and output hashes | 100% |
| Required role-separation violations admitted to publication | 0 |
| Undeclared runtime dependencies in clean CI | 0 |
| Scientific gate failures bypassable through the webapp | 0 |

Test coverage percentage is supporting information, not the primary target. The
required target is behavioral coverage of scientific invariants and failure modes.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Schema migration rewrites historical evidence. | Version living records; wrap or index frozen records without changing their bytes. |
| A new sequential design is tuned using already observed weekly outcomes. | Design and calibrate it on synthetic data; begin it only with a newly frozen prospective series. |
| Independent verification repeats the same conceptual bug. | Require a separately written derivation or algorithm, not only a different executor. |
| Source adapters break when upstream pages change. | Retain raw captures, test parser fixtures, and fail closed on unrecognized structure. |
| More gates make routine work unusable. | Expose one shared `validate -> run -> verify -> stage` workflow through both CLI and webapp. |
| Dependency pinning makes security updates difficult. | Use reviewed lockfile updates with full calibration and deterministic replay gates. |

## 9. Definition of program completion

The program is complete when a new confirmation experiment can be performed from a
clean checkout using one documented workflow that:

1. validates a human-approved machine-readable registration;
2. proves calibration and sequential error control before exposing holdout data;
3. captures and hashes raw primary-source inputs;
4. executes with a locked environment and order-independent random streams;
5. atomically writes schema-valid results and ledger records;
6. generates reports and workbook views from those results;
7. passes role-separated replay and independent recomputation; and
8. emits a release manifest that verifies the complete evidence chain.

## 10. Method references

- Johari, Pekelis, and Walsh, *Always Valid Inference: Bringing Sequential
  Analysis to A/B Testing*, https://arxiv.org/abs/1512.04922
- Phipson and Smyth, *Permutation P-values Should Never Be Zero*,
  https://arxiv.org/abs/1603.05766
- Winkler et al., *Multi-level block permutation*,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4644991/
- W3C, *PROV-O: The PROV Ontology*, https://www.w3.org/TR/prov-o/
- Python documentation, *Notes on Reproducibility*,
  https://docs.python.org/3/library/random.html#notes-on-reproducibility
- PCSO, *Search Draw Results*, https://www.pcso.gov.ph/SearchLottoResult.aspx
- GFZ German Research Centre for Geosciences, *Kp data and API*,
  https://kp.gfz.de/en/data
