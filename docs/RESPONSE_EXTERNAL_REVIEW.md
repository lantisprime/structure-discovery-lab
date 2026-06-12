# Response to External Review (lab_system_external_review.md)

**Date**: 2026-06-11 · The external review examined documents predating
`REMEDIATION_LOG.md`; several of its priorities were already executed. This
response maps every finding to its disposition and records the items newly
adopted because of the review.

## Finding-by-finding disposition

| External finding | Disposition |
|---|---|
| C1 pre-registration not verifiable | **Concur; remediated forward** — git baseline `e1bc32b` + append-only hash ledger (`results/commitment_ledger.txt`); all prior registrations explicitly labeled retroactive. The review's fuller registration-manifest schema is **adopted** for future batches. Sandbox blocks further git commits; host-side `git commit` is the owner's standing action |
| C2 role collapse | **Concur; partially remediated** — blind independent verification executed (separate agent, blinded series, own methods): **9/9 concordance** + exact numerical replication (`results/independent_verification.json`). Mechanical role-ID enforcement adopted for future runs |
| C3 wrong subset-to-whole null | **Concur; fixed** — re-specified as matrix completion vs marginal + permuted-within-column nulls (now m=199, floor-compliant): all 5 games null, min p=0.23. Old test relabeled frequency-bias-generalization |
| M1 tuned-to-pass power | **Concur; fixed** — frozen power curves over declared grids published (REMEDIATION_LOG); admission language narrowed exactly as the review words it |
| M2 low-resolution gates | **Concur; fixed and productive** — n=200 gates; the GW gate then **failed** distribution calibration → GW demoted to exploratory. "Provisional admission" framing adopted |
| M3 permutation floors | **Concur; fixed** — floor rule (p_floor ≤ α_corrected/2) in runbook AND enforced mechanically by the new design verifier, which immediately forced λ_max to m=999 and presence-MC to m=199. Outcome: the 6/45 borderline flag (p=0.0100 at m=399) **closed** at m=999 (p=0.0150); 6/55 hardened (p=0.0010) |
| M4 data-quality sensitivity | **Concur; standard output now** — three-regime reporting implemented; #45 verdict updated to "era-bounded and data-quality-sensitive" for the half-corr statistic, while the co-occurrence λ_max shadow is shown NOT data-quality-driven (p=0.0025 ex-suspicious). Row adjudication vs PCSO official records remains the open external action |
| M5 stability vs power | **Concur; fixed** — relabeled throughout; two-column convention adopted |
| M6 global multiplicity | **Concur; implemented** — `results/multiplicity_ledger.jsonl` (173 tests, one row per real-data test, family + global m, data_filter); meta-uniformity panel per batch (fig9: KS p=0.385, 6.3% ≤ 0.05) |
| M7 single-split CCA | **Concur; fixed** — 3 time-ordered splits run (split excursions p=0.04–0.10 appear/vanish, as predicted); rolling-origin variant adopted for future confirmatory use |
| m1 environment capture | **Adopted** — `results/environment.json` (Python/numpy/scipy/POT/ripser/networkx versions, platform) |
| m2 version ambiguity | **Adopted** — supersession header added to `EXTERNAL_REVIEW_BRIEF.md` |
| m3 claim language | **Adopted verbatim** — the review's recommended public wording now heads the picker page footer |
| A evidence-grade ladder | **Adopted** — see below |
| B shape-conditional admission | **Adopted** — `admitted_for_shape` / `real_data_shape` / `shape_match` fields required in future result tables (runbook) |
| C design verifier | **Adopted and implemented** — `src/design_verifier.py` checks claim-type↔method mapping, floor rule per family, sensitivity-regime presence; current verdict **PASS (0 violations; 111 historical warnings)**. It has already earned its keep (caught the remediation batch's own floor violations) |

## Evidence-grade ladder (adopted) and current grades

| Grade | Meaning | Current holders |
|---|---|---|
| G0 | exploratory, no claim | GW real-data pairs (post-demotion); 6/45 watch item |
| G1 | calibrated instrument | R1–R7 (FPR-calibrated at tested shapes; GW G1 with distribution-calibration flag) |
| G2 | internal result, registered-ish | most batch 5–7 results; pressure covariate results |
| G3 | auditable registration | none yet retroactively; future batches via hash ledger + host git |
| G4 | independent reproduction | **series-level structure/null verdicts for all 9 datasets (blind 9/9); 6/55 half-corr sensitivity (replicated to 3 decimals)** |
| G5 | held-out confirmation | none (confirmation family untouched, by design) |
| G6 | decision-grade | the *refusal* decision (no betting edge) — asymmetric: declining to act requires less evidence than acting; rests on Doob + entropy floor + uniformly null G2–G4 evidence |

## Where we differ (mildly)

The review treats "registered expectations" as part of good practice; on the
lab owner's directive we went further — discovery tests now carry **no outcome
expectations at all** (REMEDIATION_LOG, protocol change). The review's
"registration should include expected outputs" field is implemented as
*decision rules and falsification criteria*, not predicted results.

## Open items (external dependencies)

1. Host-side `git commit` to anchor the hash ledger (sandbox cannot).
2. Adjudication of the 3 suspicious 6/55 rows against PCSO official records.
3. Second source for the pressure dataset (PAGASA/NAIA).
4. Cross-model reproduction (different LLM re-running the deterministic
   scripts byte-identically) — the AGENT_WORKFLOW cross-executor step.
