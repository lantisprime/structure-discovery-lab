# Riemann–Siegel Theta Function θ(t)

**Domain face**: analytic / computational (the phase/rotation factor that converts ζ on the
critical line into the real-valued Hardy Z-function, and the clock that unfolds zero spacings)

**Statement**:
- θ(t) = arg Γ(1/4 + it/2) − (t/2) log π, for real t, with the argument taken so that θ is a
  continuous (in fact real-analytic, odd) function with θ(0) = 0 — i.e. the same branch choice
  as the principal branch of log Γ.
- **Role 1 (rotation)**: it is the phase that makes Z(t) = e^{iθ(t)} ζ(1/2 + it) **real** for
  real t; equivalently ζ(1/2 + it) = e^{−iθ(t)} Z(t). This is what turns critical-line
  zero-finding into real root-bracketing [[hardy-z-function]].
- **Role 2 (Gram points)**: g_n is defined by θ(g_n) = nπ; Gram points interlace the zeros
  "usually" (Gram's law) and feed the running zero count.
- **Role 3 (unfolding / counting)**: the smooth zero-counting function is
  N̄(T) = θ(T)/π + 1, so N(T) = θ(T)/π + 1 + S(T) with S(T) = (1/π) arg ζ(1/2+iT). Dividing
  out θ(t)/π rescales raw zero ordinates to unit mean spacing — the unfolding used by the
  spacing cards [[zeta-zero-spacing]].
- **Asymptotic expansion** (non-convergent, accurate for large t):
  θ(t) ≈ (t/2) log(t/2π) − t/2 − π/8 + 1/(48t) + 7/(5760 t^3) + …
- **Closed form / continuation**: θ(t) = (1/2i)[log Γ(1/4 + it/2) − log Γ(1/4 − it/2)]
  − (t/2) log π extends to a holomorphic function on the strip |Im t| < 1/2, inheriting branch
  cuts along the imaginary axis above i/2 and below −i/2. mpmath exposes it as `siegeltheta(t)`.

**Assumptions**: t real for the rotation/unfolding use (θ is defined on the critical line). The
asymptotic expansion is an *asymptotic* (divergent) series — valid for large t with a bounded
number of terms; near t = 0 it must not be used (θ has roots at 0 and at ±t₀ ≈ ±6.2898…, three
roots total, and oscillates / is not monotone for small |t|). For exact values this module
evaluates θ via `mpmath.siegeltheta` (which uses log Γ, not the asymptotic tail) so the same
number underpins both Z(t) and the N̄(T) unfolding.

**Reference / baseline behaviour**: the *baseline (null) behaviour* of θ is the smooth growth
N̄(T) = θ(T)/π + 1; against this baseline the only structure is the fluctuation term S(T),
whose mean is 0 and which is O(log T) in the worst case but typically O(√(log log T)). At a
Gram point the "expected" picture (Gram's law) is one zero per interval and sign(Z(g_n)) =
(−1)^n; this is a heuristic, **not** a theorem — it fails for about 1/4 of Gram intervals in
the long run (first miss at index 126, before the 127th zero). θ itself is increasing for
t ≳ 6.29 (above its positive root), with the only non-monotone behaviour at small |t|.

**Detects / blind to**: θ supplies the **smooth/secular** part of the zero count and the phase
that exposes critical-line zeros; it is *blind by construction* to the **arithmetic
fluctuation** S(T) = (1/π) arg ζ(1/2+iT) — all the "interesting" irregularity (Gram-law
violations, clustering, repulsion) lives in S(T) and in ζ, not in the deterministic smooth θ.
θ/π cannot by itself locate a single zero or distinguish on-line from off-line zeros; it only
calibrates *where zeros should be on average* and rotates ζ so a real root-search [[hardy-z-function]]
can find the actual ones. Errors in branch choice would silently shift every Gram index.

**Finite-sample / numerical cautions**: (1) **Asymptotics vs. exact**: the divergent expansion
must be truncated near its smallest term; for safety this module uses `mpmath.siegeltheta`
(log-Γ based) rather than the truncated series, especially for t ≲ 240 (the 200-zero range),
where the secular term is comparable to S(T). (2) **Branch / argument continuity**: θ requires
the *continuous* branch of arg Γ(1/4+it/2); naive principal-value `atan2` evaluation introduces
2π jumps that corrupt Gram indexing and the +1 in N̄(T)=θ(T)/π+1 — verify monotone increase of
θ(t)/π between successive Gram points. (3) **Small-t non-monotonicity**: θ is not invertible on
roughly [−24, 24]; Gram indexing is anchored historically (index 0 at the first Gram point above
the first zero at 14.1347…, with the symmetric zero at index −3), so off-by-one Gram-index bugs
are easy and must be cross-checked against N(T). (4) **Unfolding bias**: using the asymptotic
θ instead of exact θ to unfold spacings would inject a smooth bias into the spacing statistics
that mimics a deviation from the GUE/Poisson baselines — unfold with exact θ.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Riemann%E2%80%93Siegel_theta_function):
The Riemann–Siegel theta function is θ(t) = arg Γ(1/4 + it/2) − (t/2) log π for real t, with
the argument chosen for continuity (principal-branch log-Γ convention). It has a non-convergent
asymptotic expansion whose first terms approximate θ well for large t, and a Taylor series at 0
(in terms of polygamma values) converging for |t| < 1/2. Its interest in studying ζ is that it
*rotates* ζ on the critical line into the totally real Z function. θ is an odd real-analytic
function with three real roots (at 0 and ±6.2898…), is increasing for t above its positive root,
has local extrema near ±6.29 and a single inflection point at 0. A closed form via log Γ extends
θ holomorphically to |Im t| < 1/2 (hence Z is holomorphic on the critical strip there), with
branch cuts on the imaginary axis above i/2 and below −i/2. ζ on the critical line is
ζ(1/2+it) = e^{−iθ(t)} Z(t); Gram points g_n solve θ(g_n) = nπ and are approximated via the
Lambert-W function. The smooth zero count is N̄ = θ(T)/π + 1, so the number of zeros up to T is
θ(T)/π + 1 + S(T) with S(T) growing like O(log T); Gram's law (one zero per Gram interval) holds
only heuristically and fails for ~1/4 of intervals in the long run (first miss at index 126).

**Canonical references**:
- https://en.wikipedia.org/wiki/Riemann%E2%80%93Siegel_theta_function
- https://en.wikipedia.org/wiki/Z_function
- https://mathworld.wolfram.com/Riemann-SiegelFunctions.html
- H. M. Edwards, *Riemann's Zeta Function*, Dover, 1974 (Riemann–Siegel chapter).
- W. Gabcke, *Neue Herleitung und explizite Restabschätzung der Riemann–Siegel-Formel*,
  Thesis, Univ. Göttingen, 1979 (rev. 2015).

**Use in this project**: the **phase/clock** behind two instruments. `src/hardy_z.py` calls
`mpmath.siegeltheta(t)` to form Z(t) = e^{iθ(t)} ζ(1/2+it) and to locate Gram points (θ(g_n)=nπ)
for the [[hardy-z-function]] bracketing search and the N(T) reconciliation in
`src/argument_principle_check.py` (N̄(T)=θ(T)/π+1). For the spacing analysis, θ(t)/π is the
unfolding map that rescales raw zero ordinates to unit mean density before comparison to the
Poisson/GUE baselines in [[zeta-zero-spacing]]/[[random-matrix-gue]]. Per the module governance
note, θ is a *deterministic* object: the "reference/baseline behaviour" field replaces the
i.i.d.-uniform null, and the only genuine MC-null comparison happens downstream in the spacing
cards, not here.
