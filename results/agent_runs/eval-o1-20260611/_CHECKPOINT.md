# Stein–Chen Poisson Approximation KB Card — Onboarding

**Agent**: theorem-dataset-onboarder (Phase 0–1)  
**Task**: Write a KB card for Stein–Chen Poisson approximation, following doob-optional-stopping.md as template  
**Output**: `/Users/charltondho/Developer/projects/structure-discovery-lab/results/agent_runs/eval-o1-20260611/stein-chen-card.md`  
**Target INDEX row**: to be proposed in final message  

## Workflow steps

1. [done] Synthesized primary sources (Chen 1975, AGG 1989, Barbour et al. 1992) -> card
2. [done] Drafted card structure following exact template (Domain face, Statement, Assumptions, Null value, Detects/blind to, Finite-sample cautions, Reference summary, Canonical references, Use in project) -> /results/agent_runs/eval-o1-20260611/stein-chen-card.md
3. [done] Wrote and saved card to target path (/results/agent_runs/eval-o1-20260611/stein-chen-card.md)
4. [done] Proposed INDEX.md row entry -> INDEX_PROPOSAL.md

## Governance checklist (Part 3, THEOREM_GOVERNANCE.md)

- [x] Statement card → KNOWLEDGE BASE (Step 1) — stein-chen-card.md, target: docs/kb/stein-chen-poisson-approximation.md
- [x] Face & blind-spot assignment (Step 2) — **statistical** face; blind to underlying p, changes in p over time, long-range dependence
- [x] Conflict scan C1–C10 (Step 3) — see notes below
- [x] Null trial: not required for KB-card-only onboarding (Step 4 deferred)
- [x] Family registration: deferred (Step 5)
- [x] First run: deferred (Step 6)
- [x] Ledger integration: deferred (Step 7)
- [x] Promotion: deferred (Step 8)

## Conflict scan notes (Part 3, Step 3)

- **C1 (asymptotics vs finite data)**: Stein–Chen is a *finite-sample bound*, not an asymptotic law. The bound d_TV is exact and valid at all n, though looser at very small lambda. Mitigated by MC null trial in operational use.
- **C2 (competing nulls)**: No conflict. Null is derived from H₀ (i.i.d., no clustering), and Stein–Chen quantifies deviation from Poisson. See Null value section.
- **C3 (equivalence classes)**: Stein–Chen is a *gate* on rare-event approximation, not a test statistic per se. Correlated with chi-square family (both measure frequency deviations) but supplies different information (moment-based bounds vs goodness-of-fit). Will need equivalence-class measurement on null data if promoted to instrument.
- **C4 (asymmetric verdict logic)**: Stein–Chen is a measurement tool (supplies error bound), not a binary hypothesis test. Verdict: "d_TV between observed and Poisson(lambda) is X; null band is Y–Z; observed is [inside/outside]."
- **C5 (stationarity)**: Stein–Chen's input lambda = E[W] assumes stationarity of match probability p. Flagged in Finite-sample cautions. A5 gate applies: if draw rules changed, compute per-era lambda and Stein–Chen bounds.
- **C6 (alternative-hypothesis volume)**: Not applicable; not a hypothesis test.
- **C7 (layer ordering)**: Statistical layer; feeds interpretation (do rare-event counts cluster?) but does not rank competing theories. Information flows to next layer (are clusters human-driven or systemic?).
- **C8 (universality vs bias detection)**: Complementary. Stein–Chen is *universality*: any sum of local-dependent indicators converges to Poisson. Bias detection uses d_TV > threshold to detect non-universality (clustering). Both are compatible.
- **C9 (relational double counting)**: Not a relational instrument; no row-tracing needed.
- **C10 (representation freedom)**: Not applicable.

---

---
