# Lab Reliability and Accuracy Improvement Plan

**Plan ID:** `LAB-RELIABILITY-2026Q3`
**Version:** 1.3
**Created:** 2026-07-10
**Updated:** 2026-09-06 -- re-ordered under constitution article A0
**Status:** IN PROGRESS -- Milestone 0 merged; Milestone R (closed-loop
self-improvement) is the organizing milestone; Milestone 1 active as its first
substrate
**Governing article:** `docs/THEOREM_GOVERNANCE.md` Part 2, **A0** (prime
directive -- autonomous recursive self-improvement; ratified by the lab owner
2026-09-06; immutable). Every milestone below is ordered by its contribution to
A0. This plan may not weaken, deprioritize, or reinterpret A0.
**Scope:** the closed self-improvement loop, and the lab infrastructure,
statistical controls, provenance, and verification that loop needs as substrate
**Implementation plan:** `docs/plans/LAB_RELIABILITY_M0_IMPLEMENTATION_PLAN.md`
(Milestone 0)
**Planning checkpoint:** PR #18, merge commit
`a0d334b5f8e3c1cd6fabf3ea771c59f9ab2d28d6`

## 1. Objective

**Primary (A0).** Make the repository an autonomous, self-learning,
self-correcting, self-healing system: it observes its own outcomes, attributes
each defect to the agent definition, instrument, theorem card, adapter, or
method responsible, applies the correction, and re-evaluates, without waiting
for a human to notice the defect.

**Supporting.** Increase confidence that every new lab result is statistically
valid, reproducible from a clean environment, traceable to immutable inputs, and
independently verifiable. A self-improving system that cannot measure itself
reliably improves toward noise, so these controls are the loop's substrate,
not a separate program.

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
6. **Autonomy is the default; owner-reserved decisions are enumerated.** Under
   A0 the loop acts without a human unless the decision is on the reserved list:
   amending A0 itself; ratifying a constitution article or conflict-registry
   entry (`THEOREM_GOVERNANCE.md` precedent, C12); unsealing holdout data for
   a confirmation run (M4); and promoting an evidence grade to `G3+`. Anything
   not on this list that still waits for a human is a defect the loop must
   report against itself.
7. **Self-modification preserves A1--A8.** A proposed change that breaks a
   constitutional invariant (calibrated null, null-trial admission, class
   accounting, asymmetric verdicts, stationarity gate, designated arbiter,
   one-way flow, deterministic certificate) is rejected by the gate, never
   negotiated.

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
| B9 | The loop is closed by humans. Eval grades (`src/grade_agent_eval.py`), calibration results, monitoring flags, CI and `--verify` failures are observed and acted on by the lab owner; no artifact in the repository consumes those signals to change an agent definition, instrument, theorem card, adapter, or model tier. The 2026-06-11 agent evals have never been re-run automatically after an agent-definition change. | The repository cannot learn, correct, or heal on its own; A0 is unmet. | P0 (top) |

Baseline evidence is visible in `docs/AGENT_WORKFLOW.md`, `requirements.txt`,
`webapp/server.py`, `src/verify_relational_docs.py`, and
`src/pcso_weekly_update.py`.

### 3.1 Progress since baseline

| Finding | Current disposition | Evidence |
|---|---|---|
| B2 | PARTIALLY RESOLVED | The guided installer, complete runtime `requirements.txt`, recorded constraints, runtime dependency guard, and cross-platform CI are merged. A `pyproject.toml`, hash-pinned lock, manifest-aware import check, and clean-install equivalence proof remain M1 work. |
| B7 | RESOLVED | PR #17 added the canonical PCSO webapp verifier and token-bound reviewed-path closeout workflow. |
| B8 | PARTIALLY RESOLVED | Run-ledger verification is append-safe and checks required IDs plus uniqueness. Broader schema/invariant migration remains in M2 and M5. |

The remaining baseline findings are open unless a later milestone explicitly
closes them.

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
- `C10` -- one command reproduces and verifies the run from a clean environment;
- `C11` -- every defect signal (eval regression, calibration failure, monitoring
  flag, CI or `--verify` failure, source drift) is written to the outcome ledger,
  attributed to a responsible artifact, and either closed by a loop-authored
  merged change or ledgered as an owner-reserved decision; no signal is closed
  by silence.

## 5. Work plan

### Milestone 0 -- Close operational holes

**Priority:** P0
**Status:** COMPLETE AND MERGED (2026-07-10)
**Depends on:** none

Delivered by PR #17, merge commit `0265ed33b74ac5bc9d692c82d464c3c877e1d170`.
The merged `lab-ci` run passed, and conflict reconciliation preserved both
append-only ledger rows and all upstream integrity controls.

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

### Milestone R -- Closed-loop self-improvement (the A0 milestone)

**Priority:** P0 (top; organizes every other milestone)
**Status:** PLANNED (2026-09-06); R0 is startable immediately on the existing
eval set, `./tools/check.sh`, and CI
**Depends on:** nothing for R0; later stages consume M1--M5 as substrate (see
each stage)

The loop has five stages. Each is a shippable change set with its own gate, and
each stage runs on whatever substrate exists when it lands rather than waiting
for M1--M5 to complete. Existing material the loop builds on: the agent eval set
(`agents/evals/EVAL_SET.md`, grader `src/grade_agent_eval.py`, dispatch records
under `results/agent_runs/`), the two sealed eval sets under `evals/`, the
verifiers in `./tools/check.sh` and `.github/workflows/ci.yml`, the run and
multiplicity ledgers, and the `--verify` contract on every results script.

**R0 -- Observe.** One append-only outcome ledger (`results/outcome_ledger.jsonl`,
schema-versioned) that every signal source writes to: eval grades, null-trial
and calibration results, monitoring flags, CI job conclusions, `--verify`
verdicts, source-drift detections. Re-grade the agent eval set automatically
whenever a file under `agents/` changes.
- [x] Define the outcome-ledger row schema (source, artifact under test, signal,
  severity, evidence path, commit, executor identity). -- `src/outcome_ledger.py`
  schema v1, PR #24.
- [x] Emit rows from `grade_agent_eval.py`, `design_verifier.py`,
  `verify_ledger_integrity.py`, every `--verify` entry point, and the CI
  workflow. -- done by wrapping, not editing: `src/outcome_collect.py` runs each
  source and parses its verdict; the instruments keep their no-write contract.
- [x] CI job: any change under `agents/` re-runs the machine-graded evals and
  fails on a new FAIL. -- implemented as: CI re-grades every recorded eval and
  compares each definition's hash with its hash at the eval record's commit;
  a changed definition without a fresh record is a `STALE_EVAL` defect and the
  gate goes red. Re-dispatching evals (an LLM run) is R2 work.
- Gate R0: every signal source listed above produces a ledger row in a clean
  CI run; a deliberately broken agent definition turns CI red without human
  action. -- First observation (2026-09-06) surfaced a real open defect:
  `src/pcso_weekly_update.py --verify` fails since PR #20 grew its input
  (see `docs/plans/LAB_RSI_R0_IMPLEMENTATION_PLAN.md` §15); it is the first
  target for R1/R2.

**R1 -- Attribute.** Map each ledger row to the artifact responsible and the
change that introduced it.
- [x] Artifact registry: agent definitions, instruments (`src/*.py` with
  `--verify`), theorem cards (`docs/kb/*.md`), dataset adapters, model tiers.
  -- `src/artifact_registry.py`, derived from the repo (2026-09-07).
- [x] Bisection over the commit range between last-good and first-bad for every
  new FAIL, recorded on the ledger row. -- `src/outcome_attribute.py`: bisect in
  a temporary worktree (merge commits refined into the merged branch), path
  history for stale evals, `not_reproducible_here` for other-platform defects;
  appended as `attribution` rows. Ground truth: the July-runner defect
  bisects to `9488a9a` via merge `1aff3dc`.
- Gate R1: a planted regression in an instrument and one in an agent prompt are
  each attributed to the correct artifact and introducing commit with no human
  input.

**R2 -- Propose.** A proposal agent drafts the correction as a branch and PR:
diff, ledger rows it addresses, and the checks it expects to flip.
- [ ] `lab-proposer` agent definition (cheapest tier that passes its own eval),
  restricted to the artifact class named in the attribution.
- [ ] Proposal record saved before dispatch, PR body generated from it.
- [ ] Proposal agent has its own rows in `EVAL_SET.md`; no eval pass, no
  dispatch (existing rule, applied to the loop itself).
- Substrate: M2 machine-readable contracts, so a proposal can be validated
  before it runs.

**R3 -- Gate and merge.** Mechanical acceptance replaces human review for
non-reserved changes.
- [x] *Minimal (2026-09-07, `docs/plans/LAB_RSI_R3_IMPLEMENTATION_PLAN.md`):*
  `src/lab_gate.py` decides every heal PR: merge iff the required CI checks
  (the full `check.sh` battery on two platforms) are green, the defect's own
  check passes at the PR head in a fresh worktree, the scope is clean (ledger
  files append-only, no test deletions, constitution byte-identical) and a
  read-only verifier of a **different model family** (pi/LiteLLM open-weights
  or codex; the family inequality is enforced in code, `C7`) answers AGREE.
  Still open: re-graded eval set and calibration fixtures (M3) and a semantic
  A1--A8 checker (M5) as gate inputs.
- [x] Auto-merge on green (`Merge PR #N: …`, branch deleted); auto-close with
  the reasons and a `gate` ledger row on red; owner-reserved decisions
  (constraint 6: constitution, registrations, G3+ grades, the gate's own
  machinery, an agent's `OWNER-RESERVED` flag, or an exhausted heal attempt
  cap) are routed as one labelled GitHub issue per occurrence with the
  evidence attached. `tools/lab_loop.sh` runs observe → attribute → heal →
  gate → learn on a schedule (launchd / cron) and commits the appended rows.
- Gate R3: a loop-authored PR that breaks a calibration fixture is rejected
  with no human action; one that fixes an attributed FAIL merges with no human
  action.

**R4 -- Heal.** Detect and repair breakage that no eval covers.
- [x] *Minimal closed loop (2026-09-07, lab owner directive "RSI first"):*
  `src/lab_heal.py` takes each open ledger defect, dispatches a repair agent
  (headless `claude -p`) in a git worktree with a brief carrying the defect,
  its attribution, the relevant lessons and the A0/A1--A8 guardrails, gates the
  result with `./tools/check.sh` plus the defect's own check, commits on a
  `heal/…` branch and opens the PR (`--push`). Every attempt is a `heal` row
  (`PROPOSED` / `REJECTED`). Merging remains R3.
- [ ] Source-drift fixtures (M4) and stale-hash detection open ledger rows and
  trigger R2 automatically.
- [ ] Scheduled clean-checkout replay (M1) opens a row on any non-deterministic
  fixture hash.
- Gate R4: a simulated upstream HTML change and a simulated lockfile drift
  each end in a merged repair or an owner-routed decision.

**R5 -- Learn.** Feed outcomes back into how the loop itself works.
- [x] *Minimal (2026-09-07):* `results/lessons.jsonl` written by
  `src/lab_learn.py --derive` for every defect that closed (evidence,
  introducing commit from R1, fixing commit, platform) and read by the healer
  into every repair brief. Three lessons recorded from the two R0 defects.
- [ ] Lessons ledger consumed by agent definitions at dispatch (recorded
  lesson → prompt section, hash-linked).
- [ ] Model re-tiering from eval outcomes: a seat that passes at a cheaper tier
  is moved down; a seat that fails is moved up. Recorded as proposals through
  R2/R3.
- [ ] Hypothesis proposals from monitoring flags and exploratory rows become
  draft registrations (expectation-free, per the registration protocol) that
  wait only for owner-reserved unseal.
- Gate R5: two consecutive loop cycles show the second cycle's proposals
  citing lessons from the first; no regression in any eval.

**Acceptance gate R (whole milestone)**

1. From a clean checkout, a planted defect of each class (agent prompt,
   instrument, theorem card, adapter, environment) is observed, attributed,
   fixed, gated, and merged with zero human actions, and the fix is recorded
   in the outcome ledger with the introducing and fixing commits.
2. Zero merged changes violate A1--A8 (invariant check history in CI).
3. Every owner-reserved decision in the period is on the reserved list;
   anything else that waited for a human is ledgered as a loop defect.

---

### Milestone 1 -- Reproducible environment and continuous integration

**Priority:** P0
**Status:** IN PROGRESS (2026-07-10)
**Depends on:** M0 only for preferred execution order
**Serves A0 as:** the measurement substrate. A loop that cannot tell an
environment change from a real regression attributes wrongly (R1) and heals
against noise (R4).

- [ ] Declare the supported Python version and complete direct dependencies in
  `pyproject.toml`.
- [ ] Produce a fully pinned, hashable lockfile. Separate core, webapp, PCSO, and
  Riemann extras where their dependency sets differ.
- [ ] Complete the clean-environment CI workflow with schema checks, unit tests,
  verifiers, and deterministic artifact replay. The merged workflow covers clean
  installation, tests, and verifiers; scientific artifact regeneration remains.
- [ ] Record Python, OS, architecture, dependency-lock hash, and relevant numerical
  library versions in every new run bundle.
- [ ] Add a dependency-manifest test so an undeclared scientific dependency fails
  CI. The merged runtime guard checks a manually maintained import list but does
  not discover new undeclared imports automatically.

Merged foundation from PRs #11-#16: guided clean installation, complete runtime
dependency declarations, recorded constraints, a runtime import guard, and
Ubuntu/macOS CI. M1 remains open because `pyproject.toml`, a hash-pinned lock,
CI artifact replay, per-run environment binding, manifest-aware import drift
detection, and two-install deterministic equivalence are not yet complete.

**Next action:** create the template-grade M1 implementation plan for the
remaining gaps. Do not start M2 schema migration until the M1 acceptance gate is
fully satisfied.

**Acceptance gate M1**

1. A clean checkout installs without manual package discovery.
2. The supported environment runs the full fast verification suite successfully.
3. Two clean installs produce the same deterministic fixture hashes.

### Milestone 2 -- Machine-readable experiment contracts

**Priority:** P0
**Status:** PLANNED
**Depends on:** M1
**Serves A0 as:** the contract the proposer (R2) writes against and the gate
(R3) validates before anything runs; without machine-readable registrations a
proposal can only be reviewed by a human.

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
**Serves A0 as:** the outcome signal. Calibration fixtures (type-I bound, power
curve) are what R0 observes for every instrument and what R3 re-runs before
merging a loop-authored change to one.

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
**Serves A0 as:** the honesty guard on a self-modifying system. Role-ID
inequalities and the different-model-family verifier are what stop the loop
from approving its own work (R3); source-drift fixtures are R4's trigger.
Delivered ahead of sequence by PR #20 (2026-09-06): official pcso.gov.ph as
primary source with archives recorded as separate corroboration, retained raw
HTML with hashes and a per-draw manifest, and a second-implementation review by
a different model family (Codex gpt-6-astra). Recorded here as evidence of
feasibility; the checklist items stay open until the mechanisms are general
rather than one refresh's practice.

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
**Serves A0 as:** the acceptance gate's teeth. The method-change gate, semantic
invariants, and generated views are what let R3 merge without a human: a change
is safe to auto-merge exactly when these checks can say so mechanically. Under
constraint 6 the method-change gate's "renewed calibration" is required; its
human approval is not, unless the change is on the owner-reserved list.

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

| Change set | Contents | Required gate | Delivery status |
|---|---|---|---|
| 1 | Webapp verifier job and safe closeout staging | M0 | COMPLETE -- PR #17 |
| 2 | **R0** outcome ledger, signal emitters, eval re-grade on `agents/` change | R0 | NEXT -- implementation plan next; no substrate dependency |
| 3 | Complete dependency declaration, lockfile, clean CI | M1 | ACTIVE -- may run in parallel with change set 2 |
| 4 | **R1** artifact registry and attribution bisection | R1 | IN PROGRESS (2026-09-07) |
| 5 | **R4 + R5, minimal closed loop**: healer that takes an open ledger defect, dispatches a repair agent in a worktree, gates it with the full check battery and opens the PR; lessons ledger written on every closed defect and read by the healer | R4, R5 | NEXT -- lab owner directive 2026-09-07: RSI stages first |
| 6 | **R2** proposer generalized (artifact-class-restricted proposer with its own evals; the healer's dispatch becomes the proposer) | R2 | after 5 |
| 7 | **R3** mechanical gate and auto-merge, owner-reserved routing, loop scheduler | R3 | COMPLETE (minimal) -- 2026-09-07, pulled ahead of 6 because heal PRs were waiting for a human |
| 8 | **R4 + R5, full**: source-drift and replay triggers; model re-tiering; hypothesis-to-registration | R4, R5 | after 7 |
| 9 | Complete dependency declaration, lockfile, clean CI | M1 | LAST TIER -- only when an R stage needs deterministic replay |
| 10 | Schemas, registration source of truth, atomic artifact writes | M2 | LAST TIER -- only when the proposer needs machine-readable contracts |
| 11 | Null contracts, RNG streams, MC uncertainty, calibration suite; sequential controller | M3 | LAST TIER -- only when the gate needs calibration fixtures |
| 12 | Raw-source adapters, run bundles, holdout seal, role enforcement | M4 | LAST TIER -- parts already delivered by PR #20, #24 |
| 13 | Independent recomputation, generated workbook, semantic verifiers | M5 | LAST TIER |

Ordering rule under A0 (restated by the lab owner 2026-09-07): **the goal is
RSI; anything that does not contribute to it, or contributes little, is last.**
R stages run first and back to back. An M-stage is pulled forward only when an
R stage cannot proceed without it, and then only the part the R stage needs.

Do not combine a statistical-method change with a historical artifact migration in
the same change set. Reviewers, human or loop, must be able to distinguish
evidence changes from infrastructure changes.

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
| Defect signals with no outcome-ledger row (`C11`) | 0 |
| Ledgered defects closed by a loop-authored merged change, without human action | rising each cycle; 100% for non-reserved classes at R3 |
| Median time from ledger row to merged fix, non-reserved classes | falling each cycle |
| Loop-authored PRs rejected by the gate that were nonetheless merged | 0 |
| Merged changes violating an A1--A8 invariant check | 0 |
| Decisions that waited for a human and were not on the reserved list | 0 (each one is a ledgered loop defect) |

Test coverage percentage is supporting information, not the primary target. The
required target is behavioral coverage of scientific invariants and failure modes,
and, under A0, the fraction of that behavior the loop maintains on its own.

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
8. emits a release manifest that verifies the complete evidence chain;

and, under A0, when a planted defect in any artifact class is observed,
attributed, corrected, gated, and merged by the repository itself with zero
human actions, with the whole cycle recorded in the outcome ledger and no
A1--A8 invariant violated along the way (acceptance gate R).

## 10. Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-10 | Established the seven-milestone reliability and accuracy program. |
| 1.1 | 2026-07-10 | Recorded M0 delivery through PR #17 and activated M1 without overstating partial CI/dependency controls. |
| 1.2 | 2026-07-10 | Recorded the merged PR #18 planning checkpoint and added explicit delivery status to every change set. |
| 1.3 | 2026-09-06 | Re-ordered the program under constitution article A0 (PR #21): A0 becomes the primary objective; added baseline finding B9, control C11, constraints 6-7 (owner-reserved decisions, A1-A8 preserved), Milestone R (closed-loop self-improvement, stages R0-R5) as the organizing milestone, a "serves A0 as" note on M1-M5, the interleaved 13-step delivery sequence, loop metrics, and the A0 completion condition. Recorded PR #20's ahead-of-sequence M4 evidence. M0-M5 checklists unchanged. |
| 1.4 | 2026-09-07 | Lab owner directive: the goal is RSI and anything with little impact on it is last. Delivery sequence re-ordered: R1, then a minimal R4+R5 closed loop (healer + lessons ledger), then R2, R3, full R4+R5; M1-M5 moved to the last tier, pulled forward only when an R stage needs them. R0 recorded COMPLETE (PR #24, defects closed by PR #25, #27). |
| 1.5 | 2026-09-07 | R3 delivered ahead of R2 (change set 7 before 6): heal PRs were waiting for a human, which constraint 6 counts as a loop defect. Recorded the minimal R3 gate (mechanical checks + different-family verifier + owner routing + scheduler) and what stays open in it (M3 fixtures, M5 semantic invariants). |

## 11. Method references

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
