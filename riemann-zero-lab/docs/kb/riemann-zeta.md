# Riemann Zeta Function ζ(s)

**Domain face**: analytic / number-theoretic (this module's primary object)

**Statement**:
- For Re(s) > 1, ζ(s) = Σ_{n=1}^∞ n^{-s} (absolutely convergent Dirichlet series), and
  equivalently the Euler product ζ(s) = Π_p (1 − p^{-s})^{-1} over all primes p.
- ζ continues analytically to a meromorphic function on all of ℂ, holomorphic except for
  a simple pole at s = 1 with residue 1.
- Functional equation: ζ(s) = 2^s π^{s−1} sin(πs/2) Γ(1−s) ζ(1−s).
- **Trivial zeros**: the sin(πs/2) factor forces ζ(s) = 0 at s = −2, −4, −6, … (negative
  even integers). These are simple zeros.
- **Non-trivial zeros**: lie in the critical strip 0 < Re(s) < 1, symmetric about the
  critical line Re(s) = 1/2 (functional equation) and about the real axis (Schwarz
  reflection, ζ(s̄) = ζ(s)‾). The first few ordinates t_n of zeros 1/2 + i t_n are
  14.134725…, 21.022040…, 25.010858…, 30.424876…, 32.935062…, 37.586178…, 40.918719….
- **Zero-counting function** (Riemann–von Mangoldt): the number of non-trivial zeros with
  0 < Im(s) < T is N(T) = (T/2π) log(T/2π) − T/2π + 7/8 + S(T) + O(1/T), where
  S(T) = (1/π) arg ζ(1/2 + iT) is small on average (mean 0, typical size O(log log T)).

**Assumptions / domain of validity**: the Dirichlet-series and Euler-product forms require
Re(s) > 1; everywhere else ζ is accessed by analytic continuation (functional equation,
Riemann–Siegel/Euler–Maclaurin, or the alternating eta series η(s) = (1−2^{1−s})ζ(s) valid
for Re(s) > 0). High-precision evaluation in this module uses mpmath's `zeta`, which
implements continuation internally.

**Reference / baseline behaviour**: special values ζ(2) = π²/6 (Basel), ζ(0) = −1/2,
ζ(−1) = −1/12. ζ has **no zeros on Re(s) = 1** (equivalent to the prime number theorem).
The expected zero count up to height T is N(T) above — this is the deterministic baseline
against which the argument-principle zero count is cross-checked (Step "validation").

**Detects / blind to (as a module object)**: the zeros of ζ encode the distribution of
primes through the explicit formula (ψ(x) = x − Σ_ρ x^ρ/ρ − …). Numerically locating zeros
says nothing, on its own, about zeros not yet computed: the object is infinite and zero
lists are finite evidence only.

**Finite-sample / numerical cautions**: (1) the series converges only for Re(s) > 1, so
naive truncation is invalid on the critical line — use the library's continued evaluation.
(2) Near a zero, |ζ| is tiny; a reported residual |ζ(1/2 + i t̂)| is meaningful only
relative to the working precision (dps): a residual ≈ 10^{−dps·k} for some k < 1 is the
expected size, not exact zero. (3) Cancellation: on the critical line ζ is computed as a
near-cancellation of oscillatory terms; declared precision must exceed the magnitude of the
partial sums. (4) The S(T) term means N(T) jumps by ±1 around its smooth trend; zero-count
cross-checks must round and allow ±1 near Gram-point irregularities.

**Reference summary** (distilled from fetched source —
https://en.wikipedia.org/wiki/Riemann_zeta_function):
ζ(s) is defined for Re(s) > 1 by the absolutely convergent series Σ 1/n^s and by the Euler
product over primes, linking it to prime distribution. It is meromorphic on the whole plane,
holomorphic except for a simple pole at s = 1 (residue 1). The functional equation
ζ(s) = 2^s π^{s−1} sin(πs/2) Γ(1−s) ζ(1−s) relates s and 1−s; the sine factor produces the
trivial zeros at the negative even integers. All non-trivial zeros lie in the critical strip
0 < Re(s) < 1, symmetric about Re(s) = 1/2 and the real axis; the smallest-ordinate zero is
1/2 + 14.13472514… i. Special values include ζ(2) = π²/6, ζ(−1) = −1/12, ζ(0) = −1/2, and
ζ has no zeros on Re(s) = 1 (equivalent to the prime number theorem).

**Canonical references**:
- https://en.wikipedia.org/wiki/Riemann_zeta_function
- E. C. Titchmarsh (rev. Heath-Brown), *The Theory of the Riemann Zeta-Function*, OUP, 1986.
- H. M. Edwards, *Riemann's Zeta Function*, Academic Press, 1974.
- A. M. Odlyzko, tables and computations of zeros (AT&T), 1980s–2000s.

**Use in this project**: the central object of `riemann-zero-lab`. Trivial zeros are checked
directly (`tests/test_known_trivial_zeros.py`); non-trivial zeros are bracketed via the Hardy
Z-function [[hardy-z-function]] and refined to high precision (`src/find_zeta_zeros.py`),
independently verified via |ζ(1/2 + it)| (`src/verify_zeta_zeros.py`), and counted against
N(T) (`src/argument_principle_check.py`). Spacings feed [[zeta-zero-spacing]] and the
[[random-matrix-gue]] comparison. The completed form ξ(s) [[completed-zeta-xi]] makes the
zero symmetry explicit; the open conjecture about zero location is [[riemann-hypothesis]].
