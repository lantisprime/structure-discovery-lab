# Architecture — Lab Kernel and Modules

**Status: assessment / proposed doctrine, written 2026-06-13. No files have been moved.**
This document answers one question: *can the founding stochastic work be treated as a "module"
the same way `riemann-zero-lab` is?* Short answer — **yes at the doctrine level (it already
satisfies the contract), and the repo half-implemented this on 2026-06-11; a physical
relocation of the frozen legacy is possible but costly and is not recommended.** Sources:
`docs/SANITIZATION.md`, `docs/THEOREM_GOVERNANCE.md`, `docs/AGENT_WORKFLOW.md`,
`riemann-zero-lab/README.md`.

---

## 1. Current state — a kernel boundary already exists

The 2026-06-11 sanitization (`docs/SANITIZATION.md`) already split the repo into a
domain-neutral core and a domain coupling point:

- `src/core/` — the neutral instrument engine (stats, discrete_draws, recovery, paired,
  geometry, graphs, completion): "the forward-facing API for all new experiments."
- `src/domains/<domain>.py` — "the single coupling point" (currently `pcso_lotto.py`,
  `synthetic_lottery.py`). A new domain = a new file with the same interface; core never changes.
- The constitution (A1–A8, C1–C11), `RUNBOOK`, `EVALUATION_PROTOCOL`, and the agents were
  declared "domain-portable by design," and `lint_domain_neutrality.py` mechanically keeps the
  neutral zone free of domain vocabulary.

So the lab is *already* "kernel + domain coupling." What it does **not** yet have is an explicit,
documented **module contract** and a symmetric vocabulary that treats both the stochastic
application and `riemann-zero-lab` as peers over that kernel. That gap is what this document
closes (in doctrine).

## 2. Two module flavors (the asymmetry is mostly honest)

`riemann-zero-lab` and the stochastic application are **different shapes of module for a real
reason** — measured, not assumed:

| | Engine-sharing module (stochastic domains) | Standalone module (`riemann-zero-lab`) |
|---|---|---|
| Shares the kernel **instruments** (`src/core`)? | **Yes** — rides discrete_draws, recovery, graphs, … | **No** — imports **0** lines from `src/core` (different mathematics) |
| Shares the kernel **discipline** (constitution, cards-first, registration, JSON-from-scripts, role-separated verification, eval slice)? | Yes | Yes |
| Natural physical shape | A config (`src/domains/<x>.py`) + `datasets/<x>/` + registrations/results, over the shared engine | A self-contained folder with its own `src/`, `kb/`, `results/`, `tests/` |
| Example | `pcso_lotto` (Case Study 1), `synthetic_lottery` (Case Study 2) | zeta-zero discovery (Batch 1) |

The lesson: **folder-per-module fits a standalone application; config-over-engine fits a domain
that reuses the shared instruments.** Forcing one shape on both would fight the actual coupling.

## 3. The module contract (what both already satisfy)

A *module* is any application of the lab that supplies all of the following, over the shared
kernel. `riemann-zero-lab` is the clean reference implementation; the stochastic app meets the
same contract in the older in-place layout.

1. **Scope statement** — what the module claims and (critically) what it does not
   (`riemann-zero-lab`: "locate/verify zeros, never prove RH"; PCSO: "detect/exclude structure,
   never beat a fair game").
2. **KB cards** for its own objects, in its own `kb/`, **plus reuse of kernel cards by
   reference** (zeta module links the kernel's Marchenko–Pastur card rather than copying it).
3. **Pre-registration** committed before the first result-producing run.
4. **JSON-from-scripts, results-from-JSON** — numbers only flow scripts → JSON → results doc.
5. **Role-separated independent verification** (verifier ≠ author; `AGENT_WORKFLOW` role-ID rule).
6. **Adversarial-review section** in the results doc.
7. **A run-ledger row** linking registration → scripts → output SHA → verifier identity.
8. **An eval slice** exercising the module's gates against the kernel eval harness
   (`agents/evals/EVAL_SET.md`; the zeta module added §Z).
9. **Governance compliance** — uses the kernel constitution and contributes generalizations back
   (the zeta module added C11/A8).

A module may share the kernel's *instruments* (engine-sharing) or only its *discipline*
(standalone). Both are first-class.

## 4. Kernel vs module inventory (measured)

**Kernel (stays at root; shared by all modules):**

- Governance: `THEOREM_GOVERNANCE.md` (A1–A8, C1–C11, onboarding Parts 3–4), `RUNBOOK.md`,
  `EVALUATION_PROTOCOL.md`, `AGENT_WORKFLOW.md`, `THEOREM_SYNTHESIS.md`.
- Engine: `src/core/` (7 neutral modules).
- Agents + evals: `agents/` (8 roster + `evals/EVAL_SET.md`), `evals/structure_eval_set_v1/`.
- Integrity: `verify_relational_docs.py`, `design_verifier.py`, `lint_domain_neutrality.py`,
  the four-level ledger system, the G0–G6 evidence ladder.
- KB: ~24 of the 26 cards are **generic methodology** (CLT, chi-square, RMT, permutation,
  scan statistics, …) and belong to the kernel. Only `covering-designs-lottery.md` and
  `expected-value-stern-cover.md` are genuinely application-specific.

**Module 0 — the founding stochastic application (currently in place at root):**

- Config: `src/domains/pcso_lotto.py`, `src/domains/synthetic_lottery.py`.
- Data: 5 `datasets/<x>/` (pcso-lotto + 4 covariates).
- Evidentiary record: 24 `docs/RESULTS_*` / `REGISTRATION_*`, 35 `results/*.json`, the
  case studies, `lotto_picker.html`, and the KB "use in this project" fields.
- Code: 38 `src/*.py`, of which **27 are stamped FROZEN HISTORICAL RECORD / DOMAIN ARTIFACT**
  (reproduce ledger rows 1–39).

**Module 1 — `riemann-zero-lab/`:** already a clean self-contained folder-module.

## 5. Target architecture (proposed)

```
structure-discovery-lab/                ← LAB KERNEL
  docs/        constitution, runbook, protocols, ARCHITECTURE.md, MODULES.md (contract+registry)
  docs/kb/     generic methodology cards (the ~24 neutral ones)
  src/core/    neutral instrument engine
  agents/  evals/   shared agents + eval harness
  *verifiers* + lint_domain_neutrality

  ── modules (peers over the kernel) ──
  [Module 0] stochastic-structure   src/domains/* + datasets/* + registrations/results
                                     (the founding application; stays in place — see §6)
  [Module 1] riemann-zero-lab/       standalone folder-module (already here)
  [Module 2] markets-lab/  (future)  born as a folder-module, per the contract
```

Two ways to realize it:

- **Doctrine-level (low-risk, recommended).** Write the module contract (§3) into governance,
  add a root `MODULES.md` registry, and a `stochastic-structure` manifest/README that *indexes*
  the in-place legacy as Module 0. **No files move.** The architecture becomes symmetric in
  doctrine; the kernel boundary that already exists is made explicit and reusable.
- **Physical relocation (higher-cost, optional, scoped).** Give *new, non-frozen* stochastic
  work the folder shape (as `riemann-zero-lab` was born); optionally relocate non-frozen legacy
  later. See the risk ledger.

## 6. Migration risk ledger (why not to move the frozen core)

| Risk | Detail |
|---|---|
| **Reproducibility chain** | 27 frozen/domain-stamped scripts reproduce hash-ledgered rows 1–39. `SANITIZATION` is explicit: "rewriting them would break the reproducibility chain, which would be falsifying history, not sanitizing code." |
| **Root-relative ledger paths** | `results/run_ledger.jsonl` stores `script: src/…` and `output: results/…`. A physical move invalidates every path field unless the ledger is rewritten or a path-map shim is added. |
| **Flat intra-`src` imports** | Frozen scripts use `sys.path.insert(0, HERE)` and flat imports (`from relational_first_run import …`). Moving them under a module folder breaks import resolution without shims. |
| **Cross-references** | 24 result/registration docs, the README, and the case studies cross-link by path; a move is a large, error-prone find-replace. |
| **Verification cost** | Any move must be proven inert by re-running the three verifiers **and** the blind eval to demonstrate byte-identical outputs — the same bar SANITIZATION met for the `core` repoint. |

Net: the **frozen legacy should stay in place**; modularizing it is a *labelling* problem
(Module 0 manifest), not a *moving* problem. New domains get folders for free.

## 7. Recommendation

1. **Adopt the kernel + modules vocabulary in doctrine now** (write §3 contract into governance,
   add `MODULES.md`, label the stochastic app "Module 0" via a manifest over the in-place files).
   Symmetric, near-zero risk, and it tightens governance by making the contract reusable.
2. **Born-modular for new domains.** Markets, sensors, etc. start as folder-modules like
   `riemann-zero-lab` — own `kb/src/results/tests`, reusing kernel cards by reference and the
   kernel engine where applicable.
3. **Do not physically relocate the frozen stochastic legacy.** Treat it as append-only history;
   if a future cleanup wants it under a folder, move only non-frozen artifacts, behind path
   shims, gated by a verifier + blind-eval byte-identity check.
4. **Keep the KB split honest:** generic methodology cards are kernel; only truly
   application-specific cards live with a module (or carry a module tag).

The headline: the stochastic structure *can* get the RH treatment, and largely already has —
the productive move is to **name the contract both modules satisfy**, not to relocate
reproducibility-locked history into a matching folder.

---

*Companion docs: `SANITIZATION.md` (the kernel/domain split), `THEOREM_GOVERNANCE.md` (A8/C11,
the deterministic-math extension that first exercised the standalone-module path),
`riemann-zero-lab/README.md` (the reference module).*
