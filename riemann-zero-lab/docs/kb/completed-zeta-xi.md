# Completed Zeta / Riemann Xi Function ξ(s)

**Domain face**: analytic / number-theoretic (symmetry bookkeeping for the zeros)

**Statement**:
- ξ(s) = (1/2) s(s−1) π^{−s/2} Γ(s/2) ζ(s).
- **Symmetric functional equation**: ξ(s) = ξ(1−s). Equivalently, with s = 1/2 + it, the
  function Ξ(t) = ξ(1/2 + it) is **even and real** for real t.
- ξ is **entire** (the factor s(s−1) cancels ζ's pole at s = 1 and the trivial zero
  contributions; the Γ(s/2) factor absorbs the trivial zeros of ζ at s = −2, −4, …). Hence
  **the zeros of ξ are exactly the non-trivial zeros of ζ**.
- Hadamard product: ξ(s) = ξ(0) Π_ρ (1 − s/ρ), the product over non-trivial zeros ρ taken in
  pairs {ρ, 1−ρ} for convergence. This exhibits the zeros as the complete "spectrum" of ξ.

**Assumptions**: none beyond those for ζ; ξ is entire of order 1. The completed form is the
clean object on which the zero symmetry ρ ↔ 1−ρ ↔ ρ̄ ↔ 1−ρ̄ is manifest (zeros come in
quadruples unless on the critical line or real axis, where they pair).

**Reference / baseline behaviour**: because ξ(s) = ξ(1−s) and ξ(s̄) = ξ(s)‾, a non-trivial
zero at 1/2 + it forces a partner at 1/2 − it; a hypothetical off-line zero at β + iγ
(β ≠ 1/2) would force a full quadruple β±iγ, (1−β)±iγ. The module exploits this only as a
**consistency check** (every located zero's mirror must also be a zero), never as evidence
about whether off-line zeros exist.

**Detects / blind to**: ξ makes the four-fold zero symmetry explicit and removes the trivial
zeros and the pole from view, which is why critical-line searches are framed on Z(t) (≡ ξ up
to a positive real factor, since Ξ(t) = −(1/2)(t²+1/4) π^{−1/4−it/2} Γ(1/4+it/2)/|…| · Z(t)
type relation). Blind to the same things ζ is: a finite computation says nothing about the
infinitude of zeros.

**Finite-sample / numerical cautions**: direct evaluation of ξ on the critical line involves
Γ(1/4 + it/2), which grows/decays rapidly (∼ e^{−πt/4}); for large t this underflows in fixed
precision. This module therefore works with Z(t) (a unit-modulus rotation of ζ that stays
O(poly)) rather than ξ/Ξ directly, and uses ξ only symbolically for the symmetry argument.

**Reference summary** (distilled from fetched source —
https://en.wikipedia.org/wiki/Riemann_Xi_function):
The Riemann xi function is a variant of ζ with a maximally symmetric functional equation,
ξ(s) = (1/2) s(s−1) π^{−s/2} Γ(s/2) ζ(s), satisfying ξ(s) = ξ(1−s); for real t, Ξ(t) is even
and real. It is entire and real on the real axis; the s(s−1) and Γ factors cancel ζ's pole at
s = 1 and absorb the trivial zeros, so the zeros of ξ are exactly the non-trivial zeros of ζ.
RH is therefore equivalent to "all zeros of ξ lie on Re(s) = 1/2" (Ξ has only real zeros). ξ
admits a Hadamard product over its zeros and a power-series expansion underlying Li's
criterion, which states RH holds iff a sequence λ_n satisfies λ_n ≥ 0 for all n.

**Canonical references**:
- https://en.wikipedia.org/wiki/Riemann_Xi_function
- https://en.wikipedia.org/wiki/Riemann_hypothesis (Li's criterion, Hadamard product)
- H. M. Edwards, *Riemann's Zeta Function*, Academic Press, 1974.

**Use in this project**: provides the symmetry rationale for searching only t > 0 on the
critical line (zeros at −t are mirror images) and for the [[riemann-hypothesis]] scope
boundary (the module locates zeros *of ξ on the line*; it does not and cannot show ξ has *no*
zeros off the line). Li-coefficient positivity is a flagged **future batch**, not part of
Batch 1. See [[riemann-zeta]] for the base object and [[hardy-z-function]] for the instrument.
