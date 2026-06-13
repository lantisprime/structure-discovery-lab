# Gaussian Unitary Ensemble (GUE) & Random-Matrix Spacing

**Domain face**: cross-sectional / physical (the random-matrix baseline for zero spacings)

**Statement**:
- GUE(N) is the distribution on N×N Hermitian matrices H with independent zero-mean complex
  Gaussian entries, density ∝ exp(−(1/2) Tr H²) (Dyson index β = 2; GOE is β = 1 real
  symmetric, GSE β = 4). It is the unique Hermitian ensemble both invariant under unitary
  conjugation H → UHU* and having independent entries.
- The joint eigenvalue density carries the Vandermonde factor Π_{i<j} |λ_i − λ_j|^β; its
  vanishing as eigenvalues coincide produces **level repulsion**: the probability of a small
  gap scales like s^β (s² for GUE).
- **Nearest-neighbour spacing (Wigner surmise)**: for GUE (β = 2),
  p(s) ≈ (32/π²) s² exp(−4s²/π); for GOE (β = 1), p(s) ≈ (π/2) s exp(−π s²/4). Both are
  normalized to unit mean spacing. The empirical eigenvalue density follows the Wigner
  semicircle law (radius 2 for the standard scaling).
- **Connection to ζ**: the GUE pair correlation 1 − (sin(πu)/(πu))² coincides with the
  conjectured pair correlation of the unfolded zeta zeros (Montgomery 1973 / Dyson),
  suggesting a spectral (Hilbert–Pólya) reading of the zeros as eigenvalues of some
  self-adjoint operator. See [[zeta-zero-spacing]].

**Assumptions**: the spacing law is the **bulk**, asymptotic (N → ∞) statistic; the Wigner
surmise is itself an excellent approximation (derived exactly for 2×2) to the true GUE gap
distribution (a Fredholm determinant / Painlevé V object), differing by < 1% in shape. For
comparison to a *finite* set of zeta zeros, the surmise is the registered reference form.

**Null value / role in this module**: GUE is **not** the null hypothesis here — it is the
*expected* alternative. The genuine "no structure" null for spacings is the **Poisson**
process (exponential spacings, no repulsion). The spacing analysis pits the empirical zero
spacings against both, so that "looks GUE, not Poisson" is reported as the qualitative
finding, with the asymmetric-verdict caution (A4): at N ≈ 200 a failure to distinguish is a
power statement.

**Detects / blind to**: the GUE/Poisson contrast detects **level repulsion** — the single
most robust, low-N-accessible signature separating spectral (random-matrix-like) from purely
random (Poisson) point processes. Blind at this N to: discriminating GUE from GOE/GSE (all
repel, differ in exponent), the long-range pair-correlation oscillations (need many zeros and
height), and any number-theoretic content beyond the spacing shape.

**Finite-sample / numerical cautions**: (1) the surmise is a 2×2-derived approximation; for a
"truth" comparison one may simulate actual GUE matrices and diagonalize, but for N ≈ 200 the
surmise suffices and is the registered baseline (simulation is a flagged refinement). (2) Mean
normalization: the empirical spacings must be unit-mean before comparison; this is done in
[[zeta-zero-spacing]] by unfolding, not by dividing by the sample mean (which would mask a
density-trend error). (3) GUE/Poisson predictions for P(s<0.5) (≈0.112 vs ≈0.393,
both computed exactly from the surmise/exponential CDFs in `src/spacing_analysis.py`) are
the headline discriminator and are robust; fine distributional features are not, at this N.

**Reference summary** (distilled from fetched sources —
https://en.wikipedia.org/wiki/Gaussian_unitary_ensemble ,
https://en.wikipedia.org/wiki/Random_matrix):
GUE(N) is the distribution on N×N Hermitian matrices with i.i.d. zero-mean Gaussian entries,
density ∝ exp(−½ Tr H²), β = 2; it is the unique unitarily-invariant ensemble with independent
entries. The Vandermonde factor Π|λ_i−λ_j|^β drives level repulsion (small-gap probability
∝ s^β); the eigenvalue density is the Wigner semicircle. Nearest-neighbour spacings follow the
Wigner surmise — GUE: p(s) ≈ (32/π²) s² exp(−4s²/π); GOE: p(s) ≈ (π/2) s exp(−π s²/4).
Originating with Wigner (1951) for nuclear level spacings and systematized by Dyson, the GUE
pair correlation 1 − (sin πu/πu)² matches the conjectured pair correlation of Riemann zeta
zeros (Montgomery–Dyson 1973; Odlyzko numerics), motivating a spectral interpretation.

**Canonical references**:
- https://en.wikipedia.org/wiki/Gaussian_unitary_ensemble
- https://en.wikipedia.org/wiki/Random_matrix
- M. L. Mehta, *Random Matrices*, 3rd ed., Elsevier, 2004.
- F. J. Dyson, "Statistical theory of the energy levels of complex systems I–III," 1962.
- existing project card [[../../../docs/kb/marchenko-pastur-tracy-widom]] (TW edge / MP bulk).

**Use in this project**: supplies the GUE Wigner-surmise reference used by
`src/spacing_analysis.py`. Pairs with [[zeta-zero-spacing]] (unfolding + Poisson baseline) and
echoes the lab's existing RMT card [[../../../docs/kb/marchenko-pastur-tracy-widom]], whose
null λ_max skewness (+0.316 vs TW-GOE +0.293) already demonstrated universality reaching the
lab's own machinery.
