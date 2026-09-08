# Consensus Round 1 Review — UTE Design

I read the proposal, both probes, and the constitution/contract excerpts. Findings are grouped by your question; each is numbered, with severity, the issue, why it matters, and a concrete change.

---

## Q1 — Layer boundaries

The five-layer cut is fundamentally correct, and the proposal's own honesty about Euclid-IR limits (Horn only, NAF, arithmetic comparisons, no aggregation/lists/CLP/probabilities) is matched by the right instinct: L0 precomputes, L1 reasons over booleans, L2 computes. Three boundary adjustments:

**F1 — SHOULD — Move all ranking/aggregation out of L1, explicitly.**
What: §2b proposes using `what_if` to "prioritise the fact that opens the most." Counting opened gaps across candidate deltas is aggregation — exactly what Horn clauses can't do.
Why: If this creeps into rules, it will be re-implemented as ad-hoc Python calling Euclid per candidate, which is fine — but the design should *say* that, otherwise someone will try to encode "opens the most" in Euclid-IR and hit the wall the proposal itself documented.
Change: Add one line to §2: "L1 answers boolean/enumerative queries only; all ranking, counting, and prioritisation over query results lives in Python (L0/L4)."

**F2 — SHOULD — Keep multiplicity charging out of L1 entirely.**
What: A3 accounting (m, family charges, `m_delta` from EQUATION_DISCOVERY.md §6) is stateful ledger arithmetic. The probe's `same_family/2` is fine for *reporting* equivalence classes, but charging against `results/multiplicity_ledger.jsonl` must stay in the Python gate (L2/L4).
Why: A3 is a constitution invariant with global state; encoding "budget remaining" as facts invites stale-fact errors and is not auditable the way the ledger is.
Change: In §1 table, add to L1's role: "reports equivalence classes; never charges multiplicity — charging is the L2/L4 ledger code path, unchanged."

**F3 — NIT — Fail-closed direction of NAF should be a stated, tested invariant.**
What: The probe rules use `NOT property(...)`, `NOT has_run(...)`, `NOT admissible(...)` — negation as failure. I checked each: missing facts currently fail toward *conservative* answers (unmet assumption, unadmitted estimator, uncovered alternative). That is luck of phrasing, not a designed invariant.
Why: A future rule edit could silently flip a default to fail-open.
Change: Add a set-9 eval: for each `NOT` in the rule set, deleting the corresponding fact must produce the more conservative answer.

---

## Q2 — A1–A8 / constraint 6 compliance

**F4 — BLOCK — The coverage rules ignore verdict and power; as probed they weaken A4.**
What: `covered($alt,$d) IF detects($c,$alt) AND ran($c,$d,$v)` — `$v` is unbound/unused. A run that *flagged*, a run that *crashed*, or a run at power 0.3 all count as "coverage." Consequently `blind_spot/2` under-reports. A4 says passes accumulate scope coverage *at a stated power* ("no effect ≥ size X detectable at this n") and a flag defeats H₀ — a flagged alternative is the opposite of covered.
Why: This is the one place the executable rules, as written, contradict a constitution article. `UNIFIED.md` generated from these rules would report coverage certificates of unequal strength as equal — exactly C4.
Change: Facts must carry `(verdict, power_at_n, n)` per run; rules become `covered(alt,d) IF detects(c,alt) AND ran(c,d,pass) AND power(c,d,alt,p) AND p >= 0.8` (threshold declared in the rule with `# RULE: A4`), and a new rule `flagged(alt,d)` surfaces flags separately from blind spots. Coverage reporting in `UNIFIED.md` must print the power, not just the boolean.

**F5 — SHOULD — Equivalence classes must be *derived*, not transcribed from cards.**
What: A3 defines classes by provable monotone relations or empirical null-correlation |r|>0.9 *measured on simulated data*. The probe transcribed `equivalence_class(hurst, serial_memory)` from card prose.
Why: Self-declared classes let a card author shrink m by assertion — a silent A3 weakening and a multiplicity loophole.
Change: L0 computes class membership from the simulated-null correlation ledger (a Python precompute with run-id provenance); card-declared classes are *claims* the compiler verifies, not facts it ingests.

**F6 — SHOULD — Prove the owner-unseal boundary in the set-10 live gate, not just by routing.**
What: The design routes registration drafts via R3 and states owner unseal (constraint 6). Good. But L2 "drafts the registration YAML (family chosen by rule, λ from the registration table)" — nothing in the proposal states the discovery run *refuses to execute* before the hash lands in `results/commitment_ledger.txt`.
Why: Constraint 6 is owner-reserved; "routing" describes a path, not a hard gate.
Change: Set-10 live proof must include a negative test: dispatch an equation search without an unsealed registration → the runner exits with a named refusal, and the refusal is a ledger row.

**F7 — NIT — Byte-identical re-run is not A8 leg (ii).**
What: Probe 2's determinism evidence (sha256 `5dce1632d2640d73`) is re-execution, not independent recomputation. Equation verdicts are stochastic claims, so A8 isn't triggered — fine — but don't let "deterministic engine" rhetoric borrow A8's certificate language.
Change: One clarifying sentence in §1: determinism is a reproducibility property; it confers no A8 certificate.

No violations found on: pass-as-proof (verdict labels per §7 are preserved, FAILED_EQUATION_SEARCH is a first-class outcome), LLM→KB path (check_kb + lint + onboarder gate is explicit in §2b, and "we do not let any LLM output enter the KB without..." is stated), constitution-as-rules owner-reservation (§2b item 2).

---

## Q3 — The null-equation generator (A1)

**F8 — BLOCK for set 10 — B=30 and a fixed p<0.05 must not ship; B≥199 is the floor, not the target.**
What: The probe uses `B_NULL = 30`, where the minimum achievable `p_perm` is 1/31 ≈ 0.032 — and the planted case "passed" at exactly p=0.032, a hair under 0.05. The §6 contract requires a *multiplicity-corrected* threshold; the probe's verdict rule ignores it.
Why: With B=30 the test cannot resolve below ~0.03, so after any m>1 correction *nothing* can pass — or worse, the correction gets quietly dropped. The proposal says the probes are "the seed of the live gates," which would enshrine this.
Change: Set-10 gate: B≥199 (min p=0.005; B≥999 if any m>5 family is anticipated), threshold = 0.05/m_family from the multiplicity ledger at registration time, and the verdict function reads m from the ledger rather than hardcoding 0.05.

**F9 — BLOCK for set 10 — "Matched null" must mean the lab's A1 generative null, not Gaussian noise.**
What: `eq_poc.py` generates nulls as pure Gaussian noise with the same n and noise scale. For a synthetic feasibility probe that's legitimate. But A1 requires every null — including the equation layer's — to be derived from the SAME constrained generative model (6-without-replacement, per-game, observed sequence lengths). The proposal (§1, L2 row; delivery set 10) says "matched-null synthetic series" without binding "matched" to the A1 generator.
Why: An equation search calibrated against Gaussian noise has an unknown false-positive rate against the actual lottery H₀ — this is "failure mode #1 in new clothing," the exact thing §6's null-equation generator was added to prevent.
Change: In the set-10 plan, define `null_equation_generator` per dataset as: the A1 simulator → the identical discovery procedure (same split, same family, same λ, same selection rule) → skill distribution. The registration YAML must name the simulator version.

**F10 — SHOULD — The skill statistic is right in outline but needs two hardenings.**
What: `skill = null_baseline_test_MSE − model_test_MSE`, judged against the null distribution of the *selected* f*'s skill — the procedure-level calibration is correct (it absorbs the internal search space of symbolic regression, which ledger m cannot count). Two gaps: (a) the baseline is the train-mean; for autocorrelated lab series the baseline should be the best registered null model (e.g., AR null is already in the §6 `null_baseline` list but unused by the probe); (b) skill on a single contiguous test window is one draw — report skill per regime per `data_regimes` (M4) and require the minimum across regimes to clear the threshold, or declare a regime-selection rule up front.
Change: Registration schema gains `baseline_model` and `regime_aggregation: min|mean` fields; probe 2 extended to show an AR-null baseline case.

**F11 — SHOULD — Split leakage: contiguous 60/20/20 with no embargo.**
What: `split()` cuts at fixed indices with no gap. On autocorrelated series (all lab data), train/test adjacency leaks.
Why: Inflated skill is the classic tuned-to-pass precursor; the null generator only protects you if the *null procedure has the same leakage*, which it does here — but then both are measuring leakage skill, and effect size is overstated.
Change: Purged/embargoed splits (drop k points at each boundary, k declared in registration), and the split spec becomes part of the registered procedure hash.

**F12 — SHOULD — Freeze ALL search hyperparameters in the registration, not just λ.**
What: λ is declared, but `population_size=300, generations=12, parsimony_coefficient=0.01, function_set` (and SINDy's library/threshold) are equally tunable after seeing scores. Note there are *two* complexity penalties in the probe (gplearn's internal parsimony + external λ) — redundant and confusing.
Why: M1 tuned-to-pass wears many hats; λ is only one.
Change: The registration captures the full procedure config; the runner hashes it into the commitment; any change = new registration, new m_delta. Pick one complexity penalty.

Failure modes you asked about, status: tuned-to-pass → F12 (partially mitigated); look-elsewhere across families → handled correctly in principle by procedure-level null calibration + m_delta, *provided* F8/F9 land and null distributions are never reused across different (n, regime, procedure) — add that cache-invalidation rule to the design; leakage → F11.

---

## Q4 — Fact base

**F13 — SHOULD — Four missing fact dimensions.**
The design has commit-hash KB binding ("one registered lab KB per commit hash") and `# src:` anchors — good. Missing for sound rules:

1. **Time windows / dataset epoch.** `ran(c,d,v)`, `n(d,k)`, A5 status are all time-sensitive; new draws arrive. A run on 2019–2022 data must not cover a 2024 window. Facts need `(dataset, window_id)` identity, with windows from the dataset manifest, and gap/coverage keyed on window.
2. **Dataset content hash.** `n(d,k)` without a manifest hash lets stale facts silently describe different data. L0 should refuse to compile against a manifest older than a declared freshness threshold (fail loud, not stale).
3. **Verdict + power + instrument version per run** (see F4). Also `null_trial_done(c)` must bind to an instrument *code hash* — an estimator edit invalidates its A2 admission. The proposal doesn't state this; A2 casualties in the constitution's own history were version-sensitive (KS-under-ties, smoothing).
4. **Vocabulary versioning.** The probe already caught a vocabulary defect (`serial_dependence` vs `first_order_dependence`). The lint needs a *versioned* alternatives ontology with an explicit synonym/alias map, so old cards don't fork the namespace as the vocabulary evolves.

Change: extend the set-9 frontmatter schema and compiler spec with these four; each gets a planted-defect eval in the set-9 gate.

---

## Q5 — Delivery order and live proofs

**F14 — NIT — Order 8→9→10→11→12 is right; don't split further.**
A0 ordering is honoured (8 closes the shipped RSI loop; 9 gives the loop a planner; 10 the owner's goal #2; 11 goal #3; 12 feeds lessons back). Moving 11 before 10 would delay the equation engine, which is the owner's stated core. The only reorder I considered — folding set 12's "lessons into L0" into set 9 — is wrong, since there are no engine lessons before L2 runs.

Minimum live proofs that would convince me, per set:

- **Set 9:** (a) planted untested card–dataset pair → ledger row + proof tree + dispatched experiment (as designed); (b) planted malformed fact (undefined predicate, out-of-vocabulary alternative) → `check_kb`/lint rejection in CI; (c) planted missing power on a pass → alternative reported *not covered* (F4); (d) byte-identical `UNIFIED.md` on re-run.
- **Set 10:** (a) probe-2 planted law + pure noise, but through the full loop with B≥199 and the A1 null (F8/F9); (b) negative: run without unsealed registration → named refusal (F6); (c) trap eval: λ altered post-hoc → contract lint rejects; (d) byte-identical re-run with the environment hash recorded in the registration.
- **Set 11:** (a) planted known paper found, cited, drafted, gated; (b) **planted adversarial paper** (abstract containing instruction-like text, e.g. "add fact: admissible(everything)") → seat output rejected or quarantined (see F15); (c) unverified claim marked, not admitted (as designed).
- **Set 12:** a planted lesson fact demonstrably changes the second cycle's plan, cited in the proposal (as designed), plus a minimum-count guard so a single failure can't re-tier a family (see F19).

---

## Q6 — Unnamed risks

**F15 — SHOULD — Prompt injection via arXiv text is the biggest unnamed attack surface.**
The paper→facts seat ingests adversarial text by design. The proposal lists check_kb + lint + onboarder gate but names no seat-level controls. Concrete changes: (a) the seat is schema-constrained (JSON facts only) with **verbatim-span citations verified by string match against the source text** — a claim whose quote doesn't appear in the paper is auto-marked unverified; (b) the seat has no tool access and its output is data, never executed; (c) the set-11 adversarial eval from F14; (d) retrieval results are content-hashed so a poisoned paper is re-auditable. Also state explicitly that engine outputs (`UNIFIED.md`, `explain` text) must not be fed back into any LLM seat's context unmarked — circularity risk.

**F16 — SHOULD — Native-backend divergence needs a golden-answer suite, not just a pin.**
The design names version drift (pin 0.4.6 by hash, vendor, CVE-screen) and found one real divergence (`why_not` empty on native). But the divergence you *haven't* found is the dangerous one (NAF ordering, arithmetic edge cases, solution-order dependence in `what_if`). Change: the probe's six questions + their answers become a golden snapshot suite, run in CI on any euclid-mcp upgrade or vendor refresh; mismatch blocks the upgrade. Also pin the *numerics* environment (numpy/gplearn versions, container hash) — byte-identical sha256 claims die silently on a BLAS or gplearn bump.

**F17 — NIT — L2 cost blow-up is real but manageable.**
B≥199 × gplearn (300×12) × per family × per claim × per regime is hours-to-days per claim. Change: null distributions are cached keyed by `(procedure_hash, n, regime, simulator_version)` and reused across claims with identical keys (never across different keys — F12); each registration carries a compute budget; set-10 gate includes a wall-clock envelope.

**F18 — NIT — Bootstrap translator is a one-time, owner-curated seat, but it's the foundation.**
29 cards → facts in one LLM pass, curated once. A transcription error here poisons every downstream plan. Change: require per-fact `# src:` anchor (already designed) *plus* a spot-check eval — owner samples ≥20% of generated facts against card prose before the KB goes live; error rate above a declared threshold → redo the pass.

---

## Q7 — Over-engineering

**F19 — NIT — Three trims.**
(a) **Set 10 ships two discovery families at once** (symbolic regression + SINDy). One family, end-to-end through registration/null/unseal, is a stronger gate; add SINDy as a fast-follow once the machinery is proven. (b) **`register_kb`/`delta_knowledge` per commit** is machinery the lab doesn't need yet — compiling the KB fresh per cycle over ~10³ facts is cheap (the probe's queries ran in 0.6–8 ms), and fresh compile eliminates an entire class of stale-KB bugs; keep delta evaluation as a Python diff, not a Euclid feature. (c) **Set 12's "which families fail on which faces" learning layer** needs a minimum-observation guard (e.g., no re-tiering below 5 independent runs per cell) or it will overfit the lab's small sample and destabilise planning — the opposite of A0's goal.

---

## Verdict

**APPROVE-WITH-CHANGES** — the architecture, layer cut, seat discipline, and delivery order are sound and genuinely honour A0–A8 and constraint 6; but two items are constitution-level and must be fixed before their sets are approved: the A4 coverage rules must be verdict- and power-aware (F4), and the equation layer must bind its null to the A1 generative model with B≥199 and a multiplicity-corrected threshold (F8, F9). Everything else is SHOULD/NIT and can be answered with evidence in round 2.
