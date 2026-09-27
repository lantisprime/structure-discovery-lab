# REGISTRATION — pcso.signshare.seq1 (hierarchical sign-sharing reset filter: candidate algorithm + simulation study)

**STATUS: APPROVED 2026-09-27 (lab owner, in session: "yes 1 2 3"). Candidate only.** This file is
commitment-hashed into `results/commitment_ledger.txt` before any implementing code, and the implementation and
study runner are hashed before any evaluation stream (IDs 1,000–3,999) is opened. It adds no real-data testing
allocation and is not added to the picker ensemble or to `pcso.picker.prospective1`; promotion requires a new
prospective manifest/allocation (clause 24).

Design: GPT Astra 6 (peer mathematician seat), 2026-09-27 rounds 1–2. Mechanism assumed: a shared physical
influence tilts every game by a similar magnitude along the standardized ball-number feature, with game-specific
direction; its strength occasionally restarts. Unlike CP-NEST's permanently accumulating precision, the filter can
restart its amplitude distribution. Approximate expectation (NEEDS-EVIDENCE): median ≈ 818 pooled draws to reach
E = 100 at a persistent common a = 0.05 (Brownian first-passage approximation), versus measured CP-NEST 918 and
tilt_linear 707; the larger potential gain is under opposing game signs.

Feature (registry `src/pcso_model_registry.py` lines 131–140, first basis feature): φ_g(i) = (i − (P_g+1)/2) / sqrt((P_g²−1)/12).
Conditioning check (Astra, read-only): on the 1,005 rows through 2026-09-25 (input sha256 `5a34f0c1…`), posterior hazard
masses (0.741231, 0.163964, 0.094805), all-positive sign mass 0.712036, total mass 1 + 4.4e-16; closed-form vs iterated
two-step propagation differ by 6.9e-18. This is an implementation check, not evidence.

## Clauses

1. Status: candidate algorithm and simulation study; no additional real-data testing allocation and no automatic addition to the picker ensemble.
2. Pools, feature and normalized CP emission law: f_{g,a,s}(S) = exp[a s_g Σ_{i∈S} φ_g(i)] / e_6(exp[a s_g φ_g]).
3. State z = (h, s, a): s_42 = +1, other four signs arbitrary (16 patterns); a ∈ {0, ±.025, ±.05, ±.10}; h ∈ {0, 1/256, 1/1024}; 3 × 16 × 7 = 336 states.
4. Independent prior: π_s = .8 δ_{+++++} + .2 Uniform(16); π_h = (.8, .1, .1).
5. Amplitude masses: zero .10; each of ±.025 .09; each of ±.05 .27; each of ±.10 .09.
6. Predict q_g(S) = Σ_{h,s,a} w_{hsa} f_{g,a,s}(S) from the current state distribution; update by normalized emission likelihood, then apply (Tw)_{hsa} = (1−h) w_{hsa} + h π_a Σ_{a'} w_{hsa'} once per pooled draw, retaining s, h.
7. Freeze batch-position laws using T^{j−1} w, (T^j w)_{hsa} = (1−h)^j w_{hsa} + [1 − (1−h)^j] π_a Σ_{a'} w_{hsa'}; no conditioning on unavailable outcomes. Record each target's realized law and scheduled ordinal before drawing.
8. At refresh, process observations in event order; missing emissions equal one. Delayed observations require forward replay from an earlier checkpoint, not an update at the wrong time.
9. Initial conditioning uses the 1,005-row snapshot/hash above; all these outcomes are design data. Future qualified conditioning additions must be manifest-recorded; prospective evidence starts at one.
10. Comparators: production CP-NEST (M = 128, τ = .05, ρ = .001) and registered tilt_linear, with the same information, frozen batches and initialization arms.
11. Candidate study cells: all-positive prior coefficient η ∈ {.5, .8} crossed with Pr(h = 0) = r ∈ {.5, .8}; residual hazard mass splits equally. Seq1 remains exactly (η, r) = (.8, .8).
12. DGP cells: stationary strengths .025/.05/.075/.10, each with signs `+++++` and `+-+-+` in ascending pool order.
13. Additional cells, for both sign patterns: onset from zero after draw 1,005; reversal +.05 to −.05 after 1,005; and a .05 episode during draws 1,006–1,261. Include conditional-uniform null streams.
14. Initialization arms: prior start, independently simulated 1,005-draw uniform conditioning, and the fixed real 1,005-row conditioning snapshot; evidence resets after conditioning.
15. Repeat the pinned 1,005-target schedule with translated dates, preserving date groups; horizons are 1,005, 3,015 and 6,030 future draws.
16. Availability/refresh arms: next-day release with daily refresh, and next-day release with refresh every seven calendar days; freeze all intervening target laws.
17. Use 4,000 paired power streams per scenario: IDs 0–999 for selection/development, 1,000–3,999 untouched evaluation; use 20,000 separate null streams per initialization/refresh arm.
18. Seed base 20260927; pin integer namespaces for history, future draws and predictive normals, keyed by scenario, initialization and global stream ID, never shard/chunk size.
19. Reuse the per-stream caching and pairing pattern of `tools/pcso_cpnest_sensitivity.py`; share draws across candidates/comparators, cache comparators once, and keep jobs within its 300-second supervision limit.
20. Selection may motivate a separately registered seq2; it cannot change seq1 or its promotion criteria. Freeze code and manifests before opening evaluation streams.
21. Report crossing fractions, censoring-aware medians and mean capped crossing times at boundaries 200/1,400/1,600; also report cumulative scores and the `pcso.picker.prospective1` confidence bounds. Never compute medians only among crossers.
22. Promotion uses boundary 200 and U = min(τ, 6030)/6030: versus each comparator, require at least 10% smaller mean U over the seven equally weighted .05 opposed-stationary/onset/reversal/episode cells, and at most 10% worse mean U on common-sign stationary .05.
23. Require those gates under real-history conditioning in both refresh arms: eight simultaneous one-sided 95% bounds. For each paired contrast X = .9U_b − U_seq1 (or 1.1U_b − U_seq1), require X̄ − sqrt(2 s_X² log(2/δ)/n) − 7R log(2/δ)/(3(n−1)) > 0, with δ = .05/8 and R = 1.9 or 2.1; average targeted contrasts per stream before computing variance (empirical Bernstein bound, Maurer & Pontil 2009).
24. Promotion also requires normalization/replay checks, CPU–MLX agreement and no significant null overcrossing under a predeclared Bonferroni binomial diagnostic across candidate/comparator × initialization × refresh cells. Passing simulation checks is not proof of predictive advantage; promotion requires a new prospective manifest/allocation.
