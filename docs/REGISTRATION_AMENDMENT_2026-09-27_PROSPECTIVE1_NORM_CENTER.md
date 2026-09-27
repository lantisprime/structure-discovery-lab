# REGISTRATION AMENDMENT 2 + CLARIFICATIONS — 2026-09-27 — pcso.picker.prospective1

**STATUS: APPROVED 2026-09-27 (lab owner, in session: exact q=r/M; D-hat = 0; embedded children; first batch slips until ready).** Ruling drafted by GPT Astra 6 (peer mathematician seat) from its round-2 review of the frozen-law implementation (finding N3) and its normalization/center ruling (Q1–Q3). This file is commitment-hashed into `results/commitment_ledger.txt` before any code that implements it and before any forecast is anchored. No prospective batch has been anchored; nothing below reinterprets a locked artifact.

Everything not stated here is unchanged: clause 19 (ensemble uniform-null, boundary 200, allocation 0.005), the seven-model advantage family, allocation 0.005, boundary 1,400, the fixed 13-point empirical-Bernstein grid with permanent killing (`docs/REGISTRATION_AMENDMENT_2026-09-27_PROSPECTIVE1_EB.md`), certified enclosures (its clause 22), and the conditional-mean estimand.

## C1 — Normalized-law semantics (clarification of clause 6)

For a frozen law graph g with stored raw formula r_g(S) (its reference-evaluator value computed from the stored binary64 parameters), the committed predictive law is defined **exactly** as

  q_g(S) = r_g(S) / M_g,  M_g = Σ_{|S|=6} r_g(S),

where M_g is the mathematical total mass determined by the frozen graph. M_g is enclosed and refined by a certified evaluation (`certified_mass`); neither an interval endpoint nor a rounded value defines it. Eligibility requires a certified positive finite mass, a nonnegative raw formula and finite all-subset certified score bounds. A construction-quality gate additionally rejects any law whose certified mass interval is not contained in [1 − 10⁻¹², 1 + 10⁻¹²]; this gate is a quality check, not the validity argument.

Reason: a positive normalization tolerance alone cannot establish validity. Scoring an unnormalized r with M_t ≤ 1 + ε inflates the null evidence by at most (1 + ε)^n (for ε = 10⁻¹², n ≤ 10⁵: factor 1.0000001, crossing probability ≤ 0.0050000005 instead of 0.005), and r = (1 + ε)p₀ eventually crosses any boundary deterministically. With q = r/M every locked law is exactly normalized, so the registered validity paragraph holds as written. Native and reference evaluators use these same semantics.

## C2 — Mixture children (clarification of the Canonical law format)

"Mixture nodes store child references and weights" is pinned as: **mixture nodes contain ordered, recursively embedded frozen child laws with corresponding weights; every child is contained in the hashed artifact. The ensemble embeds its own realized sampled children. External references are prohibited.** This is a self-contained serialization choice; no law or inferential rule changes. The schema, reference evaluator and dependency versions are versioned and committed before the first artifact is hashed.

## A2 — Center of the empirical-Bernstein residual (amends the EB amendment's Replacement Definitions)

Replace the own-law center definition

  D̂_t^m = Σ_{|S|=6} q_t^m(S) log[q_t^m(S)/p_{0,t}(S)]

by

  **D̂_t^m = 0 for every model m and every scored target t.**

All other definitions are unchanged: H_{j,n}^m = Σ_{t≤n} ψ(λ_j c_t^m) (D_t^m)² / (c_t^m)² for c_t^m > 0 (zero for c_t^m = 0), G_EB, permanent killing, inversion at 1,400, L_n^m, uniform fallbacks (D = c = 0, factor one, counted in n), and the estimand (mean conditional expected log-score improvement over all scored targets).

Validity. For a normalized law q against the uniform law p₀ on the same finite outcome set, q/p₀ cannot exceed one everywhere or fall below one everywhere, so min_S D(S) ≤ 0 ≤ max_S D(S); hence 0 lies in every valid score enclosure [ℓ_t, h_t] and R_t = D_t / c_t ∈ [−1, 1]. The residual inequality of Howard, Ramdas, McAuliffe and Sekhon (2021, Appendix A.8) then applies with the predictable center 0 exactly as in the EB amendment's proof sketch; each λ_j is constant in time, so inversion still targets the unweighted conditional-mean average, and the combined false-claim probability remains at most 0.01.

Reason. The own-law center requires a certified evaluation of each committed law's entropy; for CP mixtures, the ensemble and the sparse mixture no practical tight certified evaluation is available, and a loose center enclosure would cost power. Planning comparison (disclosed, not a claim): in the EB amendment's oracle scenario (θ = 0.05), the residual second moment with center 0 is σ² + μ², and with the disclosed ranges μ = 0.006581–0.006837, σ² = 0.013153–0.013665 the ratio μ²/σ² is about 0.33–0.34%, i.e. center 0 raises the residual second moment by about a third of one percent over the own-law center's σ²; the fixed-grid planning crossings change correspondingly little.

## Operational note (owner decision 2026-09-27)

The first prospective batch is not targeted for 2026-09-28. It is anchored only after the frozen-law gates, the certified EB accumulation, eligibility/locking/scoring, an end-to-end rehearsal and independent review pass. Under clauses 1, 11 and 17 a later start only delays the beginning of prospective evidence; earlier draws are never backfilled.
