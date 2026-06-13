# Riemann Hypothesis (RH) — Scope Boundary Card

**Domain face**: number theory (the conjecture this module is disciplined *not* to claim)

**Statement**: Every non-trivial zero of ζ(s) has real part exactly 1/2 — all non-trivial
zeros lie on the critical line {1/2 + it}. (Trivial zeros at the negative even integers are
excluded.) The functional equation already confines non-trivial zeros to the strip
0 < Re(s) < 1, symmetric about Re(s) = 1/2; RH asserts they all sit on the centre line.
Proposed by Riemann (1859); part of Hilbert's eighth problem; a Clay Millennium Prize Problem
(US$1,000,000). **Status: OPEN.**

**Why this card exists (governance)**: this is the module's **scope-boundary card**, the
analogue of a "null import" warning in [[../../../docs/THEOREM_GOVERNANCE.md]] (C2/A4). It is
admitted not as an instrument but as a standing reminder of what the numerical pipeline may
and may not assert.

**Assumptions / equivalents**: RH is equivalent to a host of statements — the best-possible
prime-number-theorem error bound (Schoenfeld 1976: under RH, |π(x) − li(x)| < (1/8π) √x log x
for x ≥ 2657), the Mertens-function bound M(x) = O(x^{1/2+ε}), Robin's inequality for
n > 5040, and Li's criterion (λ_n > 0 for all n ≥ 1). None of these is settled.

**What numerical zero-finding CAN establish** (this module's legitimate output):
- That specific located ordinates t_n are zeros of ζ on the line, to a declared precision.
- A *verified lower bound*: at least k critical-line zeros exist below height T (sign changes
  of Z(t)).
- That the count of located zeros **matches** N(T) on the searched interval (no zero missed
  *on the line* within that interval, to the resolution of the scan + argument-principle
  check), i.e. **RH verified up to height T** in the same operational sense as Odlyzko/
  van de Lune et al. — a *finite verification*, not a proof.

**What it CANNOT establish (the hard boundary, A4 asymmetric-verdict logic)**:
- RH itself. RH is a statement about **infinitely many** zeros; any computation touches
  finitely many. "All computed zeros are on the line" is consistent with RH but is **not**
  evidence that uncomputed zeros are, and is **not** a proof. A single off-line zero at any
  unexamined height would refute RH; absence in a finite window says nothing about its
  presence elsewhere.
- That a located zero is *exactly* on Re(s) = 1/2. The search is *restricted to* the line
  (via Z(t)); finding a zero there does not test whether Re = 1/2 versus Re = 1/2 ± 10^{−40}.
  Off-line exclusion in a strip requires an argument-principle contour integral, which this
  module performs only as a **zero-count** (N(T)) check, not as a high-precision real-part
  determination.

**Reference / numerical-evidence status**: RH has been verified for the first ~10^{13} zeros
(van de Lune, te Riele, Wedeniwski, Gourdon) and checked statistically near height 10^{20}+
(Odlyzko); all checked zeros lie on the line. This is strong *evidence*, universally
understood by mathematicians as **not constituting proof**.

**Reference summary** (distilled from fetched source —
https://en.wikipedia.org/wiki/Riemann_hypothesis):
The Riemann hypothesis (Riemann, 1859) conjectures that every non-trivial zero of ζ has real
part 1/2. It is regarded as the most important open problem in pure mathematics, part of
Hilbert's eighth problem, and a Clay Millennium Prize Problem; it remains open. The functional
equation confines non-trivial zeros to the critical strip, symmetric about Re(s)=1/2; RH says
they lie exactly on the centre line. RH is equivalent to the best-possible error term in the
prime number theorem (Schoenfeld's explicit bound), to M(x)=O(x^{1/2+ε}) for the Mertens
function, to Robin's inequality for n>5040, and to Li's criterion. Extensive computation
(Odlyzko's millions of zeros near 10^{20}) supports RH, but numerical verification does NOT
constitute a proof, since infinitely many zeros remain unchecked.

**Canonical references**:
- https://en.wikipedia.org/wiki/Riemann_hypothesis
- Clay Mathematics Institute, Millennium Problems — Riemann Hypothesis.
- B. Riemann, "Ueber die Anzahl der Primzahlen unter einer gegebenen Größe," 1859.
- van de Lune, te Riele, Winter (1986); Odlyzko (1987, 2001) — numerical verifications.

**Use in this project**: cited by `REGISTRATION_ZETA_ZERO_BATCH1.md` and
`RESULTS_ZETA_ZERO_BATCH1.md` as the binding scope boundary. Every results document MUST
separate (a) numerical zero discovery, (b) structure analysis, from (c) proof-related
limitations, and MUST NOT claim RH is proven or "supported as true." Proof-adjacent work
(Li coefficients, Nyman–Beurling, Lean skeletons) is routed through theorem governance as
separate, future batches. See [[completed-zeta-xi]] for why off-line exclusion needs more than
a line search, and [[riemann-zeta]] for N(T).
