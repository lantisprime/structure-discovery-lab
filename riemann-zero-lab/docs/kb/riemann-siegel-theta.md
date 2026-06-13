# Riemann–Siegel Theta Function θ(t)

**Domain face**: analytic / computational (the phase that rotates ζ on the critical line into
the real Hardy Z-function, and the clock that unfolds zero spacings)

> Onboarded 2026-06-13 from eval Z-O1. Numeric claims below were re-verified with mpmath at
> dps=30 (`src/hardy_z.py` uses `siegeltheta`); the eval draft's statement that ±6.2898 are
> "roots" was **corrected** — those are extrema; see Statement.

**Statement**:
- θ(t) = arg Γ(1/4 + it/2) − (t/2) log π, for real t, with the argument taken on the
  **continuous** branch (θ real-analytic, odd, θ(0) = 0) — not the principal value. `mpmath`
  exposes this continuous branch as `siegeltheta(t)`.
- **Role 1 (rotation)**: θ is the phase that makes Z(t) = e^{iθ(t)} ζ(1/2 + it) **real** for
  real t; equivalently ζ(1/2 + it) = e^{−iθ(t)} Z(t). This turns critical-line zero-finding
  into real root-bracketing [[hardy-z-function]].
- **Role 2 (Gram points)**: g_n is defined by θ(g_n) = nπ; g_0 ≈ 17.8456 (= the first positive
  root of θ). Gram points interlace the zeros "usually" (Gram's law) and anchor the running
  zero count.
- **Role 3 (unfolding / counting)**: the smooth zero-counting function is N̄(T) = θ(T)/π + 1,
  so N(T) = θ(T)/π + 1 + S(T) with S(T) = (1/π) arg ζ(1/2+iT). Dividing out θ(t)/π rescales
  raw zero ordinates to unit mean spacing — the unfolding used by the spacing cards
  [[zeta-zero-spacing]].
- **Shape (verified, dps=30)**: θ is odd with θ(0) = 0 (an inflection). Its only stationary
  points are **extrema** at t = ±6.289836… where θ = ∓3.53097 (these are **not** roots). θ is
  monotonically **increasing for t > 6.289836**; its first positive **root** is t = 17.845600…
  (= g_0). So on the positive axis: root at 0, minimum at 6.2898, root again at 17.8456.
- **Asymptotic expansion** (non-convergent, accurate for large t; verified to 3.95e-17 at
  t = 396): θ(t) ≈ (t/2) log(t/2π) − t/2 − π/8 + 1/(48t) + 7/(5760 t³) + …
- **Closed form / continuation**: θ(t) = (1/2i)[log Γ(1/4 + it/2) − log Γ(1/4 − it/2)]
  − (t/2) log π extends holomorphically to the strip |Im t| < 1/2 (so Z is holomorphic there),
  with branch cuts on the imaginary axis above i/2 and below −i/2.

**Assumptions**: t real for the rotation/unfolding use (θ lives on the critical line). The
asymptotic series is *asymptotic* (divergent) — valid for large t with a bounded number of
terms; it must not be used near t = 0, where θ is non-monotone. This module evaluates θ via
`mpmath.siegeltheta` (log-Γ based, continuous branch), so the same number underpins both Z(t)
and the N̄(T) unfolding.

**Reference / baseline behaviour** (deterministic-math substitute for the i.i.d.-uniform null,
per [[INDEX]] §Governance): the baseline is the smooth growth N̄(T) = θ(T)/π + 1; against it the
only structure is the fluctuation S(T), with mean 0, typical size O(√(log log T)) and worst case
O(log T). Gram's law — one zero per Gram interval with sign(Z(g_n)) = (−1)^n — is a **heuristic,
not a theorem**: its first failure is at **Gram index n = 126** (g_126 ≈ 282.45, where
(−1)^126 Z(g_126) = −0.0276 < 0; verified here), and it fails infinitely often thereafter.

**Detects / blind to**: θ supplies the **smooth/secular** part of the zero count and the phase
that exposes critical-line zeros. It is *blind by construction* to the **arithmetic
fluctuation** S(T) = (1/π) arg ζ(1/2+iT) — all the interesting irregularity (Gram-law
violations, clustering, repulsion) lives in S(T) and in ζ, not in the deterministic θ. θ/π
cannot locate any single zero or distinguish on-line from off-line zeros; it only calibrates
where zeros sit *on average* and rotates ζ so a real root search [[hardy-z-function]] can find
the actual ones.

**Finite-sample / numerical cautions**: (1) **Asymptotics vs exact**: prefer
`mpmath.siegeltheta` over the truncated divergent series, especially for t ≲ 240 (the 200-zero
range) where the secular term is comparable to S(T). (2) **Branch continuity (load-bearing)**:
θ needs the *continuous* branch of arg Γ(1/4+it/2); a naive principal-value `atan2` differs from
θ by multiples of 2π — e.g. at t = 20 the principal-branch value is off by exactly 4π (verified)
— which corrupts Gram indexing and the "+1" in N̄(T)=θ(T)/π+1. Verify θ(t)/π increases between
successive Gram points. (3) **Small-t non-monotonicity**: θ is not invertible near the origin
(it decreases to its minimum at 6.29 before rising), so Gram indices are anchored at g_0 ≈
17.8456 and off-by-one Gram bugs must be cross-checked against N(T). (4) **Unfolding bias**:
unfolding spacings with the *asymptotic* θ instead of exact θ injects a smooth bias that can
mimic a deviation from the GUE/Poisson baselines — unfold with exact θ.

**Reference summary** (distilled from fetched source —
https://en.wikipedia.org/wiki/Riemann%E2%80%93Siegel_theta_function; numeric specifics
re-verified with mpmath):
The Riemann–Siegel theta function is θ(t) = arg Γ(1/4 + it/2) − (t/2) log π for real t, with the
argument on the continuous (log-Γ) branch. It has a non-convergent asymptotic expansion accurate
for large t and a Taylor series at 0 (in polygamma values) converging for |t| < 1/2. Its role in
studying ζ is to *rotate* ζ on the critical line into the totally real Z function:
ζ(1/2+it) = e^{−iθ(t)} Z(t). θ is odd and real-analytic, with an inflection/root at 0 and local
extrema at ±6.2898… (where θ ≈ ∓3.531 — extrema, not roots); it increases for t above that
extremum, with its first positive root at ≈ 17.8456. A closed form via log Γ continues θ to
|Im t| < 1/2 with branch cuts on the imaginary axis above i/2 and below −i/2. Gram points g_n
solve θ(g_n) = nπ (approximable via the Lambert-W function). The smooth zero count is
N̄ = θ(T)/π + 1, so N(T) = θ(T)/π + 1 + S(T) with S(T) = O(log T); Gram's law holds only
heuristically, first failing at index 126.

**Canonical references**:
- https://en.wikipedia.org/wiki/Riemann%E2%80%93Siegel_theta_function
- https://en.wikipedia.org/wiki/Z_function
- https://mathworld.wolfram.com/Riemann-SiegelFunctions.html
- H. M. Edwards, *Riemann's Zeta Function*, Dover, 1974 (Riemann–Siegel chapter).
- W. Gabcke, *Neue Herleitung und explizite Restabschätzung der Riemann–Siegel-Formel*,
  Diss., Univ. Göttingen, 1979 (rev. 2015).

**Use in this project**: the **phase/clock** behind two instruments. `src/hardy_z.py` calls
`mpmath.siegeltheta(t)` to form Z(t) = e^{iθ(t)} ζ(1/2+it) and to define Gram points (θ(g_n)=nπ)
for the [[hardy-z-function]] bracketing search and the N(T) reconciliation in
`src/argument_principle_check.py` (N̄(T)=θ(T)/π+1). For the spacing analysis, θ(t)/π is the
unfolding map that rescales raw ordinates to unit mean density before comparison with the
Poisson/GUE baselines in [[zeta-zero-spacing]]/[[random-matrix-gue]]. Per the module governance
note, θ is a *deterministic* object: the "reference/baseline behaviour" field replaces the
i.i.d.-uniform null, and the only genuine MC-null comparison happens downstream in the spacing
cards, not here.
