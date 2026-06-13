# riemann-zero-lab

A disciplined **computational-mathematics** module of the Structure Discovery Laboratory,
extending it from stochastic datasets to **deterministic mathematical structure** — here, the
zeros of the Riemann zeta function ζ(s).

> **Scope boundary (binding).** This module locates, verifies, and analyzes zeros. It **does
> not prove, and presents no evidence for the truth of, the Riemann Hypothesis.** RH concerns
> infinitely many zeros; the module touches finitely many. The legitimate outputs are a
> verified zero list, a finite-range "no zero missed" count check, and a descriptive spacing
> comparison. See `docs/kb/riemann-hypothesis.md`.

## What it does (Batch 1)

1. **Find** the first N non-trivial zeros on the critical line s = ½ + it via Hardy
   Z-function sign-change bracketing (`src/find_zeta_zeros.py`, `src/hardy_z.py`).
2. **Verify** each zero independently — residual |ζ(½+it)| via a different code path, and an
   independent cross-check against `mpmath.zetazero` (`src/verify_zeta_zeros.py`).
3. **Count** — cross-check the number of located zeros against the Riemann–von Mangoldt N(T),
   `mpmath.nzeros`, and a contour argument-principle integral (`src/argument_principle_check.py`).
4. **Analyze spacing** — unfold via θ(t)/π and compare nearest-neighbour spacings to the
   Poisson and GUE baselines (`src/spacing_analysis.py`).

All numbers are written to `results/*.json` by scripts; documents are written from JSON only.
The pipeline is deterministic (mpmath, fixed precision, no RNG): two runs are byte-identical.

## Layout

```
riemann-zero-lab/
  docs/
    REGISTRATION_ZETA_ZERO_BATCH1.md   pre-registration (committed before any result run)
    RESULTS_ZETA_ZERO_BATCH1.md        results: discovery / structure / proof-limits + adversarial review
    kb/                                7 theorem cards + INDEX (no card, no instrument)
  src/                                 hardy_z, find_zeta_zeros, verify_zeta_zeros,
                                       argument_principle_check, spacing_analysis
  results/                             zeta_zeros_batch1.json, *_count, *_spacing, *_verification,
                                       run_ledger.jsonl, agent_runs/ (eval dispatch records)
  tests/                               4 regression tests (trivial/non-trivial zeros, dup guard, precision)
```

## Quickstart

Requires Python 3 with `mpmath` and `numpy` (no scipy needed).

```bash
cd riemann-zero-lab
# 1) locate the first 200 zeros (dps=80) -> results/zeta_zeros_batch1.json
python3 src/find_zeta_zeros.py --n 200 --out results/zeta_zeros_batch1.json
# 2) independent verification (run this as a DIFFERENT executor than step 1)
python3 src/verify_zeta_zeros.py --in results/zeta_zeros_batch1.json
# 3) zero-count cross-check (N(T) + contour argument principle)
python3 src/argument_principle_check.py --in results/zeta_zeros_batch1.json --t0 31.0
# 4) spacing analysis (GUE vs Poisson)
python3 src/spacing_analysis.py --in results/zeta_zeros_batch1.json
# regression tests (run files directly, or via pytest)
python3 tests/test_known_nontrivial_zeros.py
```

## Batch 1 result (verified)

- **200 non-trivial zeros** located at dps = 80; ζ₁ = ½ + 14.1347251417…i, ζ₂₀₀ = ½ +
  396.3818542…i; residuals 2.7e-51 … 3.1e-47; precision-stable to 56–60 digits; two-run
  byte-identical.
- **No zero missed**: located 200 = N(T) = `mpmath.nzeros` = 200, and the contour ∮ζ′/ζ over
  [0,1]×[0.5,31] = 4 = the 4 zeros below height 31 (finite verification, **not** RH).
- **Spacing**: mean 0.999; decisively **not Poisson** (KS D = 0.35, p≈0), **consistent with
  GUE** level repulsion (KS D = 0.07) — labelled descriptive at N = 199.
- Independent verification (verifier ≠ author) caught and fixed a serialization-precision
  defect before sign-off; see `docs/RESULTS_ZETA_ZERO_BATCH1.md` §4–5.

## Governance — how a deterministic module fits the lab

The lab's Article A1 ("every null is Monte-Carlo-derived") has no meaning for the *existence*
of a zeta zero — there is nothing random to resample. This is registered as conflict **C11**
and resolved by article **A8 (deterministic-certificate substitution)** in
`../docs/THEOREM_GOVERNANCE.md`: a deterministic claim is admitted on a three-leg
**certificate** — (i) exact computation to a declared tolerance, (ii) independent recomputation
by a different instance, (iii) an analytic invariant cross-check (count = N(T) = contour
integral) — instead of an MC-null. The MC-null discipline (A1–A7) is retained **unchanged** for
the only genuinely stochastic question here, the **spacing** comparison (Poisson null, GUE
alternative). A7's one-way flow keeps the two layers apart: existence → distribution.

Standard lab protocol is followed: KB cards first (`docs/kb/INDEX.md`), pre-registration
committed before the first result run, JSON-from-scripts / results-from-JSON, role-separated
independent verification, adversarial-review section, and a run-ledger row. A methodology-change
**eval slice** (Z-V1/Z-V2/Z-O1, `../agents/evals/EVAL_SET.md` §Z) confirmed the verification and
onboarding gates transfer to deterministic math — **3/3 PASS**.

## Status & future batches

Batch 1 complete. Flagged next steps (not started): cross-check against a non-mpmath source
(arb/FLINT or Odlyzko tables); larger-N / higher-height spacing for a real Montgomery
pair-correlation test; Li-coefficient positivity; Nyman–Beurling experiments; Lean skeletons for
verified sub-claims. **Each is a separately governed batch; none may claim to prove RH.**
