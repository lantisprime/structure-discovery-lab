# Review brief for Codex — Unified Theorem Engine (UTE) design, consensus round 1

You are a second-opinion reviewer of a DESIGN, not of code. Read-only. Repository:
/Users/charltonho/Developer/projects/structure-discovery-lab (branch master, 9ea5be5).

## The goal (the lab owner's words, 2026-09-08)
"We need a unified theorem engine that unifies the techniques, strengths and even weaknesses
of the theorems — the super mathematician. Part of that engine is deriving novel equations and
testing them against the dataset. The engine needs to discover updates from arXiv related to
the mathematical goal it is trying to solve, which is to create novel equations to document the
patterns of stochastic data." And: "find a way to have a deterministic engine; reduce the
dependency on LLMs."

## The decision already taken (do not relitigate; review its execution)
The lab will use **Euclid-MCP** (arXiv 2607.21412; PyPI `euclid-mcp` 0.4.6, Apache-2.0) as the
deterministic reasoning layer: its pure-Python native backend runs in-process (no SWI-Prolog,
no network), over facts compiled from the theorem cards, with rules that encode the
constitution's articles. Its neuro-symbolic pattern ("the LLM describes, the engine deduces";
translate → check_kb → run → inspect → repair) is adopted deliberately: the LLM keeps
describe-only seats, never planning or verdicts.

## What to read (in this order)
1. The design: /private/tmp/claude-501/-Users-charltonho-Developer-projects-structure-discovery-lab/279a2698-3c4f-4f66-a361-f4b704c95246/scratchpad/UNIFIED_THEOREM_ENGINE_PROPOSAL.md
2. The probes and their evidence (all reproducible with run_poc.sh in the same directory):
   ute_poc.py (Euclid planning over 6 real cards; rules for A2/A3/A4/A5), eq_poc.py (seeded
   symbolic regression + null-equation generator; run sha256 5dce1632d2640d73).
3. The constitution: docs/THEOREM_GOVERNANCE.md Part 2 (A0 prime directive = autonomous RSI;
   A1 one generative null by Monte Carlo; A2 null-trial admission; A3 equivalence-class
   accounting; A4 asymmetric verdicts / passes = coverage; A5 stationarity gate; A6 designated
   arbiter; A7 layered one-way flow; A8 deterministic certificate). Constraint 6: registrations,
   G3+ grade promotion, constitution edits are owner-reserved.
4. The equation contract the engine must honour: docs/EQUATION_DISCOVERY.md §5–§8
   (three claim levels, registration YAML with a declared family and λ, the null-equation
   generator, selection rule, residual checks).
5. The loop the engine plugs into: docs/LAB_IMPROVEMENT_PLAN.md (Milestone R, R0–R5;
   change sets 8+), docs/plans/LAB_RSI_R2_IMPLEMENTATION_PLAN.md (how a stage is delivered:
   plan, evals before dispatch, live proof, gate), agents/evals/EVAL_SET.md.
6. The knowledge base the facts are compiled from: docs/kb/INDEX.md and two cards, e.g.
   docs/kb/hurst-rs-analysis.md and docs/kb/cca-family.md.
7. Prior art in the owner's homelab (same operator, different repo):
   /Users/charltonho/Developer/projects/home-network/docs/euclid-mcp-adoption-audit.md
   (verdict: adopt narrowly, never rewrite shipped deterministic gates).

## Questions for you (answer each; be specific; cite files/lines)
Q1. Is the five-layer split (facts / Euclid rules / seeded numerics / retrieval + one
    describe-only LLM seat / loop) the right place to cut, given Euclid-IR's limits (Horn
    clauses, negation as failure, arithmetic comparisons only; no aggregation, lists, CLP,
    probabilities; native `what_needs` is shallow)? Where would you move a boundary, and why?
Q2. Does anything in the design violate or weaken A1–A8 or constraint 6? In particular: can
    the engine ever adopt an equation without an owner unseal; can a pass ever be read as
    proof; can the LLM seat's output reach the KB without check_kb + lint + onboarder gate?
Q3. The null-equation generator (A1) as designed: the identical discovery procedure on B
    matched-null series with the lab's p_perm convention. Is B ≥ 199 enough; is the skill
    statistic (null-baseline test MSE minus model test MSE) the right one; what failure modes
    (M1 tuned-to-pass, look-elsewhere across families, leakage through the split) remain?
Q4. Fact-base design: card frontmatter with a controlled vocabulary for alternatives, power
    at the lab's n precomputed by Python, run history from the ledgers, A5 gate status per
    dataset. What is missing for the rules to be sound (e.g. version/commit binding, dataset
    identity, per-game structure, time windows)?
Q5. Delivery order 8 → 9 (L0/L1) → 10 (L2) → 11 (L3) → 12 (L4) under A0 (RSI first). Would
    you reorder or split? What is the minimum live proof per set that would convince you?
Q6. Risks you see that the design does not name (security of the paper→facts seat, prompt
    injection via arXiv text into facts, Euclid version drift, native-backend divergence from
    the Prolog backend, cost blow-up in L2).
Q7. Anything you consider over-engineered or unnecessary.

## Output format
Numbered findings, each: severity (BLOCK / SHOULD / NIT), what, why it matters, concrete
change. Then a one-line verdict: APPROVE / APPROVE-WITH-CHANGES / BLOCK, with reason. This is
round 1 of a consensus chain; a second round will answer your findings with evidence.
