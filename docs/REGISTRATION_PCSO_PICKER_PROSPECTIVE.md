# REGISTRATION — pcso.picker.prospective1 (prospective validation of the picker's novel-model forecasts)

**STATUS: APPROVED 2026-09-27 (lab owner, in session: "yes 1 2 3").** This file is commitment-hashed into
`results/commitment_ledger.txt` before any code that implements it and before any forecast is anchored.
Prospective evidence begins at the first eligible anchored batch (clause 1); nothing before it counts.
**AMENDED 2026-09-27** (before any prospective scoring): clauses 20–22 and the advantage-bound Definitions are replaced by
`docs/REGISTRATION_AMENDMENT_2026-09-27_PROSPECTIVE1_EB.md` (empirical-Bernstein mixture; tighter registered score-bound defaults).
**AMENDED 2026-09-27 (2)** (before any prospective scoring): `docs/REGISTRATION_AMENDMENT_2026-09-27_PROSPECTIVE1_NORM_CENTER.md`
clarifies clause 6 (exact normalization q = r/M) and the Canonical law format (embedded children), and sets the EB center D̂ = 0.
**CLARIFIED 2026-09-28** (C3, `docs/REGISTRATION_CLARIFICATION_2026-09-28_PROSPECTIVE1_TICKET.md`): the headline ticket is the output
of the registered floating-point algorithm `ticket_from_inclusion` (tie tolerance 10⁻¹², ties to lower numbers); tickets stay descriptive.

Purpose: the picker's headline tickets are the novel registered models' predictions (picker r10, PR #60,
`src/pcso_registered_predictions.py`). This registration makes their validation prospective: full predictive
laws are committed and externally timestamped before each draw, locked at a deadline, and scored after the
official result. Design: joint work with GPT Astra 6 (peer mathematician seat), rounds 1–2, 2026-09-27
(frozen-batch validity proof; strategy-commitment analysis; decision rules; law representation; anchor and
lock rules; skipped-refresh validity). Relation to other registrations: `pcso.registry.seq1`,
`pcso.sparse.seq1` and the m = 9 monitoring family are unchanged and keep their own accounting.

**Validity.** Under H0 (clause 2) every locked law q_t is normalized and fixed before draw t, so
E_0[q_t(S_t)/p0_t(S_t) | F_{t-1}] = Σ_S q_t(S) = 1 and E_t = Π_{s≤t} q_s(S_s)/p0_s(S_s) is a nonnegative
martingale; predictable refresh decisions and skipped refreshes preserve this. Retrospectively added targets do not,
hence clause 11.

## Clauses

1. Scope: prospective forecasts for all official six-subset draws in pools 42, 45, 49, 55 and 58, beginning at a publicly anchored start time; no retrospective evidence.
2. Null: conditional uniformity of each draw given all preceding draw outcomes and information used by the forecasts, including across games.
3. Each target records official game, stable draw identity, pool, original scheduled datetime and timezone. Its deadline is the earlier of 20:30 PHT on its original date and its earliest announced start; commitment must also precede actual drawing. Postponement never extends the deadline.
4. Freeze the seven non-uniform algorithms (dirichlet_cp_a100, tilt_high31, tilt_linear, pair_parity, cp_nest, ensemble — the `pcso.registry.seq1` roster, seed 20260923 — and cp_sparse_switch of `pcso.sparse.seq1`), their initialization/update rules, seeds and dependencies in the registration manifest. Uniform is the eighth displayed model and the baseline.
5. Every artifact records input bytes/hashes, availability cutoff, qualification manifest, code/environment hashes, state/RNG provenance, and deterministic historical processing order.
6. Store complete realized normalized laws in the canonical format (below), with tickets, tie rules, scoring parameters and predictable score-range bounds. Reject malformed laws before eligibility.
7. Artifacts specify standing coverage for the five games until superseded, plus target-specific overrides where present. List all currently known upcoming targets; standing coverage governs later occurrences without retrospective amendments.
8. Anchor the full artifact SHA-256, retrieval location, registration/batch IDs, coverage rule and target list in a GitHub issue comment on the lab repository.
9. A submission is eligible only when a pre-deadline independently timestamped archive captures its artifact and the comment's API response with `created_at < deadline`, `updated_at == created_at`, and matching validated bytes (archive: clause A below).
10. At each target deadline, lock the latest eligible covering submission by `(created_at, comment_id)`. An explicit target override takes precedence over its standing game law.
11. With no eligible covering submission, lock the uniform law and lexicographic ticket `[1,2,3,4,5,6]`; its score increment and evidence factor are zero and one.
12. Locked forecasts cannot be replaced or dropped. Subsequent comment edits/deletions do not change archived eligibility. Missing locked artifacts cause a certification hold, never retrospective fallback.
13. A batch comprises targets assigned to one artifact. Skipped refreshes extend use of its standing laws; no outcome-conditioned changes occur within a locked forecast.
14. A rescheduled target retains its identity and any existing lock. Earlier scheduling advances the deadline; later scheduling cannot reopen it.
15. Official cancellation without drawing contributes no observation or factor. Unresolved results remain pending; official corrections require a versioned audit and full score replay.
16. Score in actual draw order, with official order or game-ID order for simultaneous draws. Publish only complete certified prefixes; later resolved targets cannot bypass earlier pending ones.
17. Initialize every prospective evidence process at one. Historical conditioning and the descriptive 30-day backtest contribute no prospective evidence.
18. The ensemble's committed full law is the primary predictor; its headline ticket maximizes expected overlap (maximum-inclusion set), with ties favoring lower ball numbers.
19. Allocate 0.005 solely to the ensemble uniform-null test: reject when its cumulative committed-law evidence reaches 200 at a certified prefix. Other evidence curves and adaptive joint-batch scores are descriptive.
20. Allocate 0.005 equally to the seven non-uniform model-versus-uniform comparisons. Use exactly G, u, L defined below, with boundary 1,400 and no data-selected grid.
21. The confidence-sequence estimand is mean conditional expected log-score improvement over all scored targets, including uniform fallbacks; positive validated advantage requires L_n^m > 0. Uniform's improvement is identically zero.
22. Bounds must cover every possible six-subset. Numerical decisions use conservative certified score/bound evaluations; a threshold-straddling numerical interval cannot trigger a claim.
23. Display commitment link, target/status, law version, ticket objective, scored/pending/fallback counts, cumulative log evidence and the simultaneous lower bound in nats/draw. Model-implied ticket probabilities and overlap outcomes remain descriptive.
24. This registration controls its own combined false-claim probability at 0.01. New algorithms, inferential rules or allocations require a prospectively anchored amendment; existing registrations retain their separate accounting.

**A. Archive and independent timestamp (owner decision 2026-09-27).** Each batch artifact is uploaded as an
asset of a GitHub release on the lab repository (tag `prospective1-<batch_id>`), and an OpenTimestamps proof
(`ots stamp`) of the artifact SHA-256 is created before the deadline and attached to the same release; the anchor
comment (clause 8) links both. Eligibility (clause 9) requires the release asset bytes to hash to the anchored
SHA-256 and the OpenTimestamps attestation (once upgraded) to precede the deadline; until upgraded, the GitHub
server timestamps of the release and comment are recorded and the attestation is completed before certification.

## Definitions (clauses 19–21)

D_t^m = log[q_t^m(S_t)/p0_t(S_t)], A_n^m = Σ_{t≤n} D_t^m, μ_t^m = E[D_t^m | F_{t-1}],
V_n^m = Σ_{t≤n} (c_t^m)^2 with c_t^m a committed valid range width of D_t^m (clause 22), and

G(x, V) = (1/13) Σ_{j=0}^{12} exp{2^{-j} x − 2^{-2j} V/8},  G(u(V,B), V) = B,  L_n^m = (A_n^m − u(V_n^m, 1400)) / n.

Uniform-null rule: reject when E_n^ensemble = exp A_n^ensemble ≥ 200 at a certified prefix. Advantage rule: report
positive validated improvement for model m only when L_n^m > 0 (equivalently G(A_n^m, V_n^m) > 1400). By Hoeffding's
lemma G(A_n^m − Σ μ_t^m, V_n^m) is a nonnegative supermartingale; Ville's inequality with a seven-way union bound
gives simultaneous coverage over models and time ≥ 0.995; with the uniform-null allocation the registered false-claim
probability is ≤ 0.01.

**Expected operating characteristics (disclosed, not claims).** Oracle forecaster at a planted tilt θ = 0.05:
mean crossing of boundary 200 ≈ 799 draws (20,000 streams, seed 2026092702). The advantage bound is conservative:
for the same oracle, mean-trajectory crossings of the Hoeffding mixture lie near 71,000–90,000 draws, so a fast
uniform-null rejection must not be presented as a fast advantage certificate. A variance-adaptive bound would need an
amendment (clause 24).

## Canonical law format (clause 6)

One typed law graph per target: dense conditional-Poisson nodes store realized `logw`, mixture coefficients and
cached normalizers; mixture nodes store child references and weights (the ensemble stores its own sampled children);
parity nodes store their seven-count law parameters; sparse nodes store supports, tilt dictionaries, realized expert
log-weights, normalizers and the outside-uniform mass. Serialization: UTF-8 JSON, sorted ASCII keys, compact
separators, final newline; arrays as base64 of C-order little-endian IEEE-754 binary64 (or unsigned-16 support
indices) with explicit shapes and dtypes. The artifact SHA-256 is taken over these exact bytes. A reference evaluator
with fixed arithmetic order scores the committed law without model state or history; native and replayed log q must
agree within 1e-12 on fixed draws and on all subsets of small test pools.
