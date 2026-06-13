# Zeta Zero Spacing & Unfolding (Montgomery Pair Correlation)

**Domain face**: statistical / cross-sectional (the structure-analysis layer of this module)

**Statement**:
- The non-trivial zeros 1/2 + iγ_n have a mean density that increases with height:
  dN/dt ≈ (1/2π) log(t/2π). To compare spacings across heights they must be **unfolded** —
  rescaled to unit mean spacing — via the smooth counting function
  Ñ(t) = (t/2π) log(t/2π) − t/2π + 7/8. The unfolded ordinates are w_n = Ñ(γ_n); the
  normalized nearest-neighbour spacings are s_n = w_{n+1} − w_n = (γ_{n+1} − γ_n)·(1/2π)
  log(γ_n/2π) to leading order. By construction mean(s_n) ≈ 1.
- **Montgomery's pair correlation conjecture** (1973): the pair correlation of the unfolded
  zeros follows the density 1 − (sin(πu)/(πu))². Montgomery proved (under RH) that the Fourier
  transform F(α) of the pair correlation equals |α| for |α| < 1, and conjectured F(α) = 1 for
  |α| ≥ 1. Dyson observed in 1973 that 1 − (sin πu/πu)² is exactly the GUE eigenvalue pair
  correlation — the founding zeros↔[[random-matrix-gue]] link.
- **Consequence**: the nearest-neighbour spacing distribution of zeros is conjectured to match
  GUE (β = 2), which exhibits **level repulsion** — P(s → 0) → 0 like s² — in sharp contrast
  to a Poisson process, where spacings are exponential, P(s) = e^{−s}, with no repulsion
  (P(0) = 1).

**Assumptions**: unfolding via Ñ(t) assumes the smooth Riemann–von Mangoldt trend captures
the density; the fluctuating S(t) term is what remains and is the object of interest. Pair
correlation statements are asymptotic (height → ∞); at finite, low height (first few hundred
zeros) they hold only approximately.

**Null / baseline distributions (the two competing references, per A1/A6 governance)**:
- **Poisson baseline (H₀ "no repulsion")**: spacings i.i.d. Exponential(1); nearest-neighbour
  pdf p(s) = e^{−s}; CDF 1 − e^{−s}; P(s < 0.5) ≈ 0.393.
- **GUE baseline (the random-matrix alternative)**: Wigner surmise (β = 2)
  p(s) ≈ (32/π²) s² exp(−4s²/π); strong small-s repulsion, P(s < 0.5) ≈ 0.112 (computed
  exactly from the closed-form surmise CDF, verified by quadrature in
  `src/spacing_analysis.py`). This is the distribution the zeros are *expected* to follow.
The spacing analysis reports the empirical spacing distribution against **both**, with a
two-sample / goodness-of-fit statistic (KS) to each, and is explicit that with N ≈ 200 zeros
at low height the comparison is **descriptive**, not a confirmatory test (small-N + low-height
bias toward weaker repulsion).

**Detects / blind to**: detects the qualitative repulsion signature (GUE-like vs
Poisson-like) and gross departures. Blind, at N ≈ 200, to fine discrimination among
random-matrix ensembles (GUE vs GOE vs GSE differ mainly in the small-s exponent) and to the
pair-correlation tail (needs many more zeros and higher height). A KS "fails to reject
Poisson" at small N would be a **power** statement, not evidence of no repulsion.

**Finite-sample / numerical cautions**: (1) **Low-height bias**: the first 200 zeros sit at
t ≲ 240 where log(t/2π) ≈ 3.6 — unfolding is crude and the empirical spacing distribution is a
biased, under-resolved estimate of the asymptotic GUE law; this is the dominant caveat. (2)
**Edge effects**: the first and last spacings of a finite list are truncated; report N−1
spacings and note endpoint sensitivity. (3) **Unfolding choice**: using the smooth Ñ vs a
local linear unfold changes s_n at the few-percent level; the registered choice is the smooth
Riemann–von Mangoldt Ñ. (4) KS p-values assume independent samples; consecutive spacings are
weakly correlated, so reported KS p-values are *indicative*, with the caveat logged.

**Reference summary** (distilled from fetched source —
https://en.wikipedia.org/wiki/Montgomery%27s_pair_correlation_conjecture):
Montgomery's pair correlation conjecture (1973) states that the pair correlation of the
non-trivial zeros of ζ, normalized to unit mean spacing, is governed by 1 − (sin(πu)/πu)².
When Montgomery described this to Dyson in 1973, Dyson recognized it as exactly the pair
correlation of GUE eigenvalues — the founding link between zeta zeros and random matrix
theory. Montgomery proved (under RH) that the Fourier transform F(α) of the pair correlation
equals |α| for |α| < 1 and conjectured F(α) = 1 for |α| ≥ 1. Odlyzko's computations of zeros
(including near height 10^{20}) gave strong numerical support for GUE spacing statistics. The
framework extends to higher correlations and to automorphic L-functions (Rudnick–Sarnak 1996).

**Canonical references**:
- https://en.wikipedia.org/wiki/Montgomery%27s_pair_correlation_conjecture
- H. L. Montgomery, "The pair correlation of zeros of the zeta function," 1973.
- A. M. Odlyzko, "On the distribution of spacings between zeros of the zeta function,"
  *Math. Comp.* 48 (1987).
- existing project card [[../../../docs/kb/marchenko-pastur-tracy-widom]] (RMT in the lottery face).

**Use in this project**: defines the secondary task of Batch 1. `src/spacing_analysis.py`
unfolds the located ordinates (via θ(t)/π, [[riemann-siegel-theta]]), computes nearest-neighbour
spacings, and compares the empirical distribution to the Poisson and GUE baselines (KS statistic
to each), writing
`results/zeta_zero_spacing_batch1.json`. The random-matrix baseline detail lives in
[[random-matrix-gue]]; the zero source is [[riemann-zeta]].
