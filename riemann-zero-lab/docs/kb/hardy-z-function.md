# Hardy Z-Function Z(t) (Riemann–Siegel Z)

**Domain face**: analytic / computational (the instrument used to locate critical-line zeros)

**Statement**:
- Z(t) = e^{iθ(t)} ζ(1/2 + it), where θ(t) is the Riemann–Siegel theta function
  θ(t) = arg Γ(1/4 + it/2) − (t/2) log π.
- **Key property**: Z(t) is **real** for real t (consequence of the functional equation),
  is an even, real-analytic function, and |Z(t)| = |ζ(1/2 + it)|.
- Therefore the **real zeros of Z(t) are exactly the zeros of ζ on the critical line**.
  A sign change of Z between t = a and t = b guarantees an odd number of critical-line
  zeros in (a, b); this turns zero-finding into a one-dimensional real root-bracketing
  problem, avoiding complex-plane contour work.
- Computed efficiently by the Riemann–Siegel formula
  Z(t) ≈ 2 Σ_{n=1}^{N} n^{−1/2} cos(θ(t) − t log n) + R(t), N = ⌊√(t/2π)⌋, with an
  asymptotic remainder R(t) = O(t^{−1/4}). mpmath provides Z(t) as `siegelz(t)` and
  θ(t) as `siegeltheta(t)`.

**Assumptions**: t real (the instrument is defined on the critical line). The
Riemann–Siegel asymptotic remainder degrades for small t; library implementations switch to
direct ζ evaluation when needed, so this module evaluates Z via `mpmath.siegelz` (asymptotic)
and independently re-derives |Z| = |ζ(1/2+it)| via `mpmath.zeta` for verification — two code
paths, one number.

**Reference / baseline behaviour**: between consecutive **Gram points** g_n (defined by
θ(g_n) = nπ), Z(t) "usually" has exactly one zero and the sign of Z(g_n) "usually" equals
(−1)^n (Gram's law) — a heuristic, not a theorem; it fails infinitely often (Gram blocks /
violations), which is exactly why a sign-change bracketing search with a fine enough step is
required rather than assuming one zero per Gram interval. The density of real zeros of Z is
~ (1/2π) log(t/2π), matching N′(T).

**Detects / blind to**: detects critical-line zeros (sign changes). Blind, by construction,
to any hypothetical zero **off** the critical line — Z(t) real-zero counting can confirm a
lower bound on critical-line zeros but cannot by itself exclude off-line zeros; that requires
the argument principle / N(T) count [[riemann-zeta]]. A pair of zeros that touch without
crossing (a double zero, or two very close simple zeros not separated by the step) can be
missed by a pure sign-change scan — mitigated by step refinement and by the N(T) count.

**Finite-sample / numerical cautions**: (1) **Step size**: zeros get denser as t grows
(spacing ~ 2π / log(t/2π)); a fixed scan step that is too coarse can skip a close pair —
the search must shrink the step where Gram's law is violated and reconcile the running count
with N(T). (2) **Near-tangent zeros**: |Z| can dip near zero without a sign change; this
module cross-checks every claimed root index against the expected N(T) count to detect a
missed pair. (3) The Riemann–Siegel remainder is asymptotic — for the t-range here (t ≲ 240,
covering 200 zeros) it is accurate, but residual checks use full-precision ζ, not the
asymptotic Z, as the arbiter.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Z_function):
The Z function (Riemann–Siegel Z, Hardy function) studies ζ along the critical line. Defined
via the Riemann–Siegel theta function and ζ, it is real for real t (from ζ's functional
equation), even, and real-analytic; its real zeros are precisely the critical-line zeros of
ζ, while complex zeros of Z in its strip correspond to off-line zeros of ζ. Evaluation is
expedited by the Riemann–Siegel formula with an asymptotic remainder R(t). By the critical
line theorem the density of real zeros is positive (more than five-twelfths of all zeros are
on the line; Pratt–Robles–Zaharescu–Zeindler 2018); under RH all critical-strip zeros are
real zeros of Z and all are conjectured simple. Z(t) oscillates and grows slowly; its RMS
size grows like √(log t), with peak-value growth bounded by the Lindelöf hypothesis.

**Canonical references**:
- https://en.wikipedia.org/wiki/Z_function
- https://en.wikipedia.org/wiki/Riemann–Siegel_formula
- A. Ivić, *The Theory of Hardy's Z-Function*, Cambridge Tracts in Math. 196, CUP, 2013.
- H. M. Edwards, *Riemann's Zeta Function*, Academic Press, 1974 (Riemann–Siegel chapter).

**Use in this project**: the bracketing instrument. `src/hardy_z.py` wraps `siegelz`/
`siegeltheta` and Gram points; `src/find_zeta_zeros.py` scans Z(t) for sign changes over
t > 0, refines each bracket by bisection/Brent to high precision, and hands roots to
[[riemann-zeta]]-based verification. Gram-point bookkeeping feeds the N(T) reconciliation in
`src/argument_principle_check.py`.
