# Pre-Registration — Zeta Zero Batch 1 (riemann-zero-lab)

Registered: 2026-06-13, **before any result-producing run** (lab rule: registration
committed first; the first run references this file's git commit). Module:
`riemann-zero-lab` (extends the structure-discovery lab from stochastic datasets to
deterministic mathematical structure). Analyst: Claude (with Cha).
Status: **NUMERICAL DISCOVERY + STRUCTURE ANALYSIS — NOT A PROOF.**

## Scope boundary (binding, read first)

This batch locates and verifies non-trivial zeros of ζ on the critical line and analyzes
their spacing. It makes **no claim to prove, or to provide evidence "for the truth of", the
Riemann Hypothesis.** RH concerns infinitely many zeros; this batch touches finitely many.
The legitimate output is (a) a verified list of located zeros, (b) a finite-range
verification that the located count matches N(T), and (c) a descriptive spacing comparison.
The hard boundary is stated in the scope card [[kb/riemann-hypothesis]] and is repeated in
the results document. Any proof-adjacent work (Li coefficients, Nyman–Beurling, Lean
skeletons) is a separate, governance-routed future batch.

## Question

Can the lab reproducibly **locate and verify the first N = 200 non-trivial zeros** of ζ on
the critical line s = ½ + it, to declared high precision, with an independent cross-check that
no zero in the searched range is missed; and does the **unfolded nearest-neighbour spacing**
distribution qualitatively match the GUE random-matrix law rather than a Poisson process?

- Target equation: ζ(s) = 0.
- Critical-line form: s = ½ + it, t > 0.
- Primary task: first **N = 200** non-trivial zero ordinates t_n.
- Secondary task: spacing analysis of the t_n after unfolding, vs Poisson and GUE
  ([[kb/zeta-zero-spacing]], [[kb/random-matrix-gue]]).

## Precision settings (declared before running)

- Working precision: **mpmath dps = 80** (decimal places) for discovery and the primary
  verification. Reported ordinates are emitted at 30 significant decimals (more than any
  standard reference table) with the full-precision value retained internally.
- **Precision-stability protocol**: every zero is recomputed at dps = 50 and dps = 80; a zero
  is "precision-stable" iff the two agree to ≥ 40 decimal places. The agreement digit count is
  recorded per zero. (This is the operational form of validation requirement #4.)
- Residual acceptance: a located t̂ is accepted iff |ζ(½ + i t̂)| < 10^{−30} at dps = 80
  (far below the ~10^{−48}-scale the example record anticipates; the threshold is the
  conservative gate, the achieved residual is reported).

## Methods (the registered pipeline — all 10 required elements mapped)

1. **High-precision arithmetic** — mpmath, dps = 80 (`src/*` all set `mp.dps` explicitly).
2. **Search over t > 0** — scan the Hardy Z-function on an increasing t-grid from t = 0.
3. **Bracketing via sign changes of Hardy Z(t)** — Z(t) = e^{iθ(t)}ζ(½+it) is real for real
   t and |Z| = |ζ(½+it)|; a sign change brackets an odd number of critical-line zeros
   ([[kb/hardy-z-function]]). Base scan step Δt = 0.1, refined adaptively where Gram's law is
   violated or where the running count lags N(t).
4. **Root refinement** — each bracket is refined by bisection on Z to a tight interval, then
   polished by `mpmath.findroot` (secant/Newton) on Z to full dps. Root accepted only inside
   the original bracket (no jumping).
5. **Independent verification of |ζ(½+it)|** — `src/verify_zeta_zeros.py` recomputes the
   residual via `mpmath.zeta` directly (a *different code path* than `siegelz`), and
   independently cross-checks each ordinate against `mpmath.zetazero(n)` (mpmath's own
   zero-finder, an independent algorithm) requiring agreement to ≥ 40 decimals.
6. **Duplicate-root prevention** — roots are collected in increasing t with a minimum
   separation guard (no two accepted roots within 10^{−6}); the index n is assigned by sorted
   order; the per-zero Gram/sign-change provenance is stored. A duplicate or out-of-order root
   is a hard failure (`tests/test_duplicate_root_handling.py`).
7. **Known-zero regression tests** — `tests/` checks trivial zeros at s = −2,−4,−6,… and the
   first several non-trivial ordinates against published reference values to ≥ 25 decimals.
8. **JSON output** — `results/zeta_zeros_batch1.json` (one record per zero, schema below) and
   `results/zeta_zero_spacing_batch1.json`. All numbers written from scripts only.
9. **Result verification script** — `src/verify_zeta_zeros.py` re-derives residuals, the
   zetazero cross-check, precision stability, monotonicity, and the N(T) count, emitting a
   PASS/FAIL table; `src/argument_principle_check.py` independently counts zeros in the range.
10. **Documentation of numerical precision** — this §Precision section + per-record
    `precision_dps` and `stable_decimals` fields.

### Zero-count cross-check (validation requirement #6)

`src/argument_principle_check.py` computes the expected count via the Riemann–von Mangoldt
formula N(T) = θ(T)/π + 1 + S(T), with S(T) = (1/π) arg ζ(½+iT) evaluated directly, at the
height T = t_200 + ε just above the last located zero. The number of located zeros must equal
round(N(T)) exactly (allowing the documented ±1 only if T lands within 10^{−3} of a zero, in
which case T is nudged). As a second, contour-based check on a sub-range, the argument
principle (1/2πi)∮ ζ′/ζ ds is evaluated numerically around a rectangle enclosing the strip
0 < Re < 1, 0 < Im < T₀ for a modest T₀ (≈ first 10 zeros) and compared to the same N(T₀).
Agreement of the line-search count, N(T), and the contour integral is the "no zero missed"
certificate **on the line and in the strip up to T₀**; it is explicitly *not* an RH statement.

## Expected output schema (per zero record)

```json
{
  "zero_index": 1,
  "s_real": "0.5",
  "t_imag": "14.134725141734693790457251983562",
  "s": "0.5 + 14.134725141734693790457251983562i",
  "zeta_abs": "1.2e-48",
  "precision_dps": 80,
  "stable_decimals": 47,
  "zetazero_match_decimals": 50,
  "verified": true,
  "method": "Hardy-Z bracketing + high-precision refinement"
}
```

## Validation requirements (all must pass before the results doc is written)

1. Trivial zeros detected/confirmed at s = −2, −4, −6, … (|ζ| = 0 to precision).
2. First non-trivial zero recovered near ½ + 14.134725 i.
3. First several ordinates match known reference values within declared precision (≥ 25 dp).
4. Increasing precision (50 → 80 dps) does not materially move the roots (≥ 40 dp stable).
5. No duplicate roots; strictly increasing ordinates.
6. Zero count in range cross-checked by N(T) (and contour argument principle on a sub-range).

## Determinism & reproducibility (lab two-run rule, adapted)

The pipeline is **deterministic** (no RNG; mpmath at fixed dps). The two-run rule is met by
running the full pipeline **twice** and requiring **byte-identical** JSON (sha256 match). The
cross-executor rule is met by the independent-verification dispatch (a separate agent
instance re-runs `verify_zeta_zeros.py` and recomputes against `mpmath.zetazero` — verifier ≠
author, per `docs/AGENT_WORKFLOW.md` role-ID separation). Seeds: none required; the seed-field
in the run ledger row records "deterministic / mpmath dps=80".

## Multiplicity / confirmatory vs descriptive (A4 discipline)

- The zero **locations and verifications** are deterministic computations, not hypothesis
  tests — no p-values, no multiplicity budget. "Verified" means the residual + cross-check +
  stability gates passed.
- The **spacing comparison** is the only statistical element. It is registered as
  **descriptive / exploratory**, not confirmatory: at N = 200 zeros and low height (t ≲ 240)
  the asymptotic GUE law holds only approximately. The KS statistic to GUE and to Poisson is
  reported with the explicit caveat that "fails to reject" is a power statement (A4). The
  headline discriminator is P(s < 0.5): Poisson ≈ 0.393 vs GUE ≈ 0.04 vs empirical. No claim
  of "confirms Montgomery/GUE" is permitted from this N; only "consistent with GUE-like
  repulsion, inconsistent with Poisson, at this resolution."

## Governance checklist

1. This document is the one-page pre-registration, committed before any result run.
2. KB cards admitted first (6 cards + INDEX, [[kb/INDEX]]); no instrument runs uncarded.
3. Deterministic-math adaptation of Article A1 documented ([[kb/INDEX]] §Governance): MC-null
   machinery applies only to the spacing analysis (Poisson null), not to zero existence.
4. Scope boundary ([[kb/riemann-hypothesis]]) binds the results document: discovery /
   structure / proof-limitations kept in separate sections; no RH-proof claim.
5. JSON written from scripts only; results doc written from JSON only.
6. Independent verification by a different agent instance (role-ID separation).
7. Adversarial review section required in the results document.

## Success criteria (Batch 1)

1. First 200 non-trivial zeros located. 2. Each independently verified (residual + zetazero
cross-check + stability). 3. Precision stability demonstrated (≥ 40 dp). 4. Results
reproducible from script output (byte-identical two-run). 5. Spacing-analysis JSON produced
with GUE + Poisson comparison. 6. Results doc separates numerical discovery, structure
analysis, and proof-related limitations.

## Methodology-change notice (lab rule)

Adding a deterministic-mathematics module materially extends the lab's methodology (the
A1 MC-null premise does not apply to zero existence). Per CLAUDE.md, an **eval-set run is
offered** to the lab owner to confirm the existing agents/governance behave correctly under
this extension before the module is treated as standing infrastructure.

**Human approval required before any run.** Approved by: Cha ("follow the lab's workflow",
2026-06-13) — recorded as approval-to-proceed under the lab workflow. Date: 2026-06-13.
