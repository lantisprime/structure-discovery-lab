# Unified Theorem Engine (UTE) — deterministic design, for lab-owner approval

Status: DRAFT v2, 2026-09-08 (supersedes v1 of the same day). Not in the repo until approved.
Owner asks: (1) a unified theorem engine that unifies the techniques, strengths and weaknesses
of the theorems; (2) derives novel equations and tests them against the datasets; (3) discovers
arXiv updates related to the goal; (4) **deterministic, with the LLM dependency reduced**, and
check whether Euclid-MCP helps.

## 0. Evidence gathered before writing this (all reproducible, scratchpad `run_poc.sh`)

**Euclid-MCP** (arXiv 2607.21412; github Euclid-BG/Euclid-MCP; PyPI `euclid-mcp` 0.4.6, Apache-2.0)
is a Horn-clause reasoner with proof trees. It has a **pure-Python native backend**, so it runs
in-process in the lab with no SWI-Prolog and no network. Facts + rules + `NOT` + arithmetic
comparisons; no disjunction, lists, aggregation, CLP or probabilities. The homelab already
audited it (home-network `docs/euclid-mcp-adoption-audit.md`): adopt narrowly, never rewrite
shipped deterministic gates, use it for reasoning with proof trees over fact bases.

Probe 1 — planning over real theorem cards. Six cards from `docs/kb` (permutation tests,
exact-MC chi-square, Markov order tests, Hurst R/S, Fisher g periodogram, CCA family) were
transcribed into facts (face, assumptions, detects, blind-to, equivalence class, null
generator, finite-sample floor) with three datasets and the run history; rules encoded A2,
A3, A4, A5 and "no card, no test". Results (native backend, 0.6–8 ms per query, identical
content hash and solution order on re-run):

| question (query) | deterministic answer | proof tree says |
|---|---|---|
| `gap(card, dataset)` | permutation tests never run on `jackpot_winners`, `kp_index` | applicable ∧ admissible ∧ ¬run |
| `blocked_by_a2` | CCA family on `jackpot_winners`: applicable but **no null trial yet** | A2 |
| `blocked_by_assumption` | 15 rows, e.g. Fisher g on `kp_index` missing `stationarity` (A5 gate not run), CCA on unpaired data missing `paired_rows` | the named missing gate |
| `too_small` | Hurst R/S on all three (n=984 < 2000 floor from the card's caution) | finite-sample floor |
| `blind_spot(alt, pcso_draws)` | `broadband_dependence`, `shared_latent_factor` uncovered; also surfaced a vocabulary defect (`serial_dependence` vs `first_order_dependence`) | A4 coverage |
| `same_family` | Hurst ↔ Markov (serial_memory) | A3 |

Probe 2 — equation layer, no LLM. Symbolic regression (gplearn, declared function set, seeded)
under the §6 contract: λ declared before fitting, train/val/test split, null-equation generator
(the identical procedure on 30 matched-noise series), skill judged with the lab's `p_perm`.
Planted `y = 2x − 0.5x² + noise` → recovered `2x − 0.504x²`, skill 5.25 vs null max 0.004,
p = 0.032, **PREDICTIVE_EQUATION**. Pure noise → constant `0.002`, p = 0.42,
**FAILED_EQUATION_SEARCH**. Two runs: identical sha256 `5dce1632d2640d73`. (`pysindy` 2.1.0
installs alongside for the sparse-regression family.)

## 1. Architecture: five layers, LLM at one describe-only seat

| Layer | Engine | Deterministic? | Role |
|---|---|---|---|
| L0 facts | Python compiler over card frontmatter + ledgers + dataset manifests → Euclid-IR | yes (hashed) | the theorem graph: assumptions, nulls, detects/blind, power at n, equivalence classes, cautions as thresholds, run history, A5 gate status |
| L1 reasoning | Euclid-MCP native engine, in-process | yes (content hash, proof trees) | applicability, admissibility (A2), coverage and blind spots (A4), family accounting (A3), gap → experiment proposals, why/why-not/what-if; the generated `UNIFIED.md` is a rendering of L1 answers |
| L2 numerics | the lab's Python: MC nulls (A1), instruments, symbolic regression + SINDy with the null-equation generator, MDL selection, bootstrap stability, residual checks | yes (seeded) | runs the experiments L1 selected; drafts the registration YAML from the L1 proof (family chosen by rule from face + card, λ from the registration table) |
| L3 literature | arXiv API (Atom) + searxng, queries generated from L1 blind spots and failed searches; dedupe by arXiv id; **one LLM seat**: paper → candidate facts with citations (describe, not reason) | retrieval yes; extraction is the LLM seat, evaluated | candidate cards enter through the onboarder gate; `check_kb` validates the fact base; novelty = L1 query "no card detects this alternative" |
| L4 loop | R0–R3 as shipped | yes | every engine output is a proposal through the proposer and the gate; owner unseals registrations and grades |

LLM dependency before/after: today the structure analyst designs tests, the equation analyst
picks families and judges fits, the scout reads papers, the orchestrator plans. After UTE:
planning, applicability, coverage, family choice, λ, null calibration, fitting, selection and
verdicts are code and rules with proof trees; the LLM remains only for (a) paper → facts
(evaluated by R-2/R-3, every claim cited or marked unverified) and (b) optionally proposing a
candidate family *outside* the registered library, which then waits for unseal like any other.
The repair proposer (R2) is unchanged.

## 2. What Euclid does and does not buy (honest limits)

- **Buys**: exact, auditable planning over ~10³ facts with a proof for every "test this next"
  and every "not admissible because"; what-if ("if the A5 gate passes on kp_index, what opens?");
  a single source of truth for methodology rules that today live in prose across RUNBOOK,
  EQUATION_DISCOVERY and the cards.
- **Does not buy**: numerics. Counts, power, p-values, fits are Python; L0 precomputes them into
  facts (no aggregation in Horn clauses). Nothing in the gate machinery is rewritten (homelab
  audit §3.1 applies here too).
- **Caveats found in the probe**: the native backend's `why_not` returned no findings (the
  Prolog backend is richer; acceptable, `blocked_by_*` rules give the reasons directly);
  alternatives need a **controlled vocabulary** (a lint in L0); solution order was stable but
  L0 will sort anyway; single-author project → pin 0.4.6 by hash, vendor the native engine if
  it drifts, CVE-screen like any new component.

## 2b. Using Euclid's neuro-symbolic pattern deliberately (probe 3, 2026-09-08)

Euclid's own pattern is "the LLM describes, the engine deduces", packaged as a
translate → `check_kb` → run → inspect → repair loop, with the *Policy Compiler* recipe
(deterministic parse → optional LLM formalization → `check_kb` → human curation, every rule
carrying `# RULE: <id>` and `# src: <section>` anchors). Probe 3 exercised the tools on the
card KB (native backend):

| tool | result | how the lab uses it |
|---|---|---|
| `explain` | proof tree → 15 ordered English steps, rule and fact citations, **no LLM** | the experiment brief and the registration draft carry the engine's own justification; the PR body for a proposal quotes it; the owner-decision issue quotes it |
| `what_if` (`+`/`-` lines) | "A5 gate passes on kp_index, CCA null trial done" → gaps 2 → 4, naming the two experiments that open | counterfactual planning for the owner ("what does unsealing X open?") and for the loop (prioritise the fact that opens the most) |
| `check_kb` | 69 facts, 15 rules, 27 predicates, valid; catches undefined predicates, cycles, duplicates | CI lint of the compiled fact base; the repair target of the translate loop |
| `diagnose why` | holds, 1 solution | evidence line in ledger rows |
| `diagnose what_needs` | **shallow**: only reports whether each body predicate has any facts; no abduction through nested rules or arithmetic | abduction stays in our rules (`blocked_by_assumption`, `blocked_by_a2`, `too_small` name the missing fact directly), which the probe showed working |
| `register_kb` / `delta_knowledge` | named KB + per-query deltas | one registered lab KB per commit hash; a proposal is evaluated as a delta, never by mutating the base |

Where the LLM sits, and only there (open-weights via pi/LiteLLM per the lab's seat policy;
no premium model needed for describing):
1. **Bootstrap translator** — one pass over the 29 cards: prose → frontmatter facts with
   `# src:` anchors to the card section; `check_kb` + vocabulary lint as the repair loop;
   owner curates once; afterwards facts are edited only through PRs and the gate.
2. **Methodology compiler** — RUNBOOK, EQUATION_DISCOVERY §6 and the constitution articles →
   rules with `# RULE: A2`, `# RULE: A5`, `# src: RUNBOOK §2` anchors; owner-reserved once
   written (they *are* the constitution in executable form).
3. **Paper → facts seat** (L3) — a new paper becomes candidate `detects/requires/blind`
   facts with citations; `check_kb` rejects malformed output; novelty is an L1 query; the
   onboarder eval judges the seat, not the facts' truth (that is the card's job).
4. **Design inside the proof** — when a gap is dispatched, the structure analyst receives the
   `explain` steps as constraints (which null, which family, which floor) and designs the
   test within them; it no longer chooses *whether* or *which*.

What we do not do with it: rewrite the R3 gate, the collector or the healer's scope checks
as Prolog (they are already deterministic and test-pinned; homelab audit §3.1), and we do not
let any LLM output enter the KB without `check_kb`, the vocabulary lint and the onboarder gate.

## 3. Delivery (A0 ordering; each set has its own plan, evals, live proof)

| Set | Contents | Live gate |
|---|---|---|
| 8 (next, already queued) | full R4/R5: source-drift + replay triggers, lessons into prompts, re-tiering from repeated eval rolls | the stale `results/meta_uniformity.json` becomes a ledger defect the loop heals |
| 9 = UTE-L0/L1 | card frontmatter schema + vocabulary lint; fact compiler; rule set (A2–A5, no-card-no-test); `UNIFIED.md` generator; coverage gaps and blocked reasons as ledger rows; `check_kb` in CI | on the real 29 cards: every gap/blocked row carries a proof tree; a planted untested card–dataset pair becomes a row and a dispatched experiment |
| 10 = UTE-L2 | registration drafter from L1 proofs; symbolic-regression + SINDy engine with the null-equation generator, MDL selection, bootstrap, residual checks; verdict labels per §7; owner unseal routing via R3 | planted synthetic law recovered (PREDICTIVE_EQUATION), pure noise FAILED, byte-identical re-run — as in probe 2 but through the loop and the registration ledger |
| 11 = UTE-L3 | arXiv/searxng retrieval from L1 queries; paper→facts seat with evals R-2/R-3; novelty via L1; onboarding gate | a planted known paper is found, cited, drafted as a card, routed to onboarding; an unverified claim is marked, not admitted |
| 12 = UTE-L4 | engine lessons into L0 (which families fail on which faces), re-tiering, synthesis regenerated each cycle | second cycle's proposals cite the first cycle's lessons (R5 gate) |

## 3b. Consensus round 1 (2026-09-08, reviewer kimi-k3 via pi/LiteLLM; Codex channel gated, owner chose to proceed) — disposition

Verdict received: APPROVE-WITH-CHANGES; two constitution-level items (F4, F8+F9) must land before
their sets are approved. Full text: scratchpad `review_round1_kimi.md`.

| # | Finding | Sev | Disposition | Where it lands |
|---|---|---|---|---|
| F1 | ranking/aggregation must not live in L1 (Horn cannot count) | SHOULD | ACCEPT | §1: L1 answers boolean/enumerative queries only; prioritisation is Python (L0/L4) |
| F2 | multiplicity charging stays in the ledger code path | SHOULD | ACCEPT | §1: L1 reports classes, never charges m |
| F3 | negation-as-failure must fail closed by design, tested | NIT | ACCEPT | set-9 eval: delete each negated fact → more conservative answer |
| F4 | `covered/2` ignores verdict and power; weakens A4 | **BLOCK** | **ACCEPT** (my probe rule bound `$v` and never used it) | facts carry `(verdict, power_at_n, n, instrument_hash)` per run; `covered` needs `pass` and power ≥ a `# RULE: A4` threshold; `flagged/2` separate from `blind_spot/2`; UNIFIED.md prints power |
| F5 | equivalence classes must be derived from simulated-null correlations, not transcribed | SHOULD | ACCEPT-WITH-MOD | L0 computes membership from the null-correlation precompute; card-declared classes are claims the compiler verifies; a mismatch is a ledger row, not a silent override |
| F6 | prove the unseal boundary with a refusal, not routing prose | SHOULD | ACCEPT | set-10 negative gate: search without a committed registration hash → named refusal + ledger row |
| F7 | byte-identical re-run is reproducibility, not an A8 certificate | NIT | ACCEPT | one sentence in §1 |
| F8 | B=30 and a fixed 0.05 must not ship | **BLOCK (set 10)** | **ACCEPT** | B ≥ 199 (999 if m>5 anticipated); threshold = 0.05 / m_family read from the multiplicity ledger at registration |
| F9 | "matched null" must be the A1 generator, not Gaussian noise | **BLOCK (set 10)** | **ACCEPT** (probe 2 used noise as a feasibility stand-in) | `null_equation_generator` = A1 simulator (version named in the registration) → identical procedure → skill distribution |
| F10 | baseline should be the best registered null model; skill per regime, min across regimes | SHOULD | ACCEPT | registration gains `baseline_model`, `regime_aggregation` |
| F11 | contiguous split leaks on autocorrelated series | SHOULD | ACCEPT | purged/embargoed split, k declared and hashed into the procedure |
| F12 | freeze the whole search config, not just λ; one complexity penalty | SHOULD | ACCEPT | procedure config hashed into the commitment; single penalty |
| F13 | facts need window identity, dataset content hash, instrument hash on A2 admission, versioned vocabulary | SHOULD | ACCEPT | set-9 schema + a planted-defect eval per item |
| F14 | order stands; minimum live proofs per set as listed | NIT | ACCEPT | §3 gates replaced by the reviewer's list |
| F15 | prompt injection via arXiv text is the main unnamed surface | SHOULD | ACCEPT | seat is schema-constrained JSON, verbatim-span citations string-matched against the source, no tools, output never executed; adversarial-paper eval; engine outputs never re-enter an LLM context unmarked |
| F16 | golden-answer suite against backend divergence; pin numerics | SHOULD | ACCEPT | probe questions become a CI snapshot suite; numpy/gplearn/container hashes pinned |
| F17 | L2 cost | NIT | ACCEPT | null distributions cached by `(procedure_hash, n, regime, simulator_version)`; compute budget per registration |
| F18 | bootstrap translation errors poison everything | NIT | ACCEPT | owner spot-checks ≥ 20 % of generated facts; error-rate threshold → redo |
| F19 | trims: one discovery family first; fresh compile instead of `register_kb`; min-observation guard before re-tiering | NIT | ACCEPT | set 10 ships symbolic regression only, SINDy follows; KB compiled per cycle; ≥ 5 independent runs per cell |

Nothing rejected. Round 2 (Codex, when the bundle is restored; else the same route) receives this
table with the evidence for each landed change.

## 4. Decision requested

Approve the deterministic architecture and the order 8 → 9 → 10 → 11 → 12. On approval I write
the change-set-9 implementation plan (L0/L1) as soon as change set 8 closes, run the eval set at
every agent-definition change, and keep the probe scripts as the seed of the live gates.
