# CCA Family — Paired Multi-View Correlation (CCA / KCCA / Deep CCA / PLS / HSIC)

**Domain face**: relational (paired rows, latent-factor sharing)

**Statement**:
- Hotelling (1936): CCA finds projections a, b maximizing corr(Xa, Yb); successive
  pairs are orthogonal. Solved by SVD of the whitened cross-covariance
  Σ_X^{-1/2} Σ_XY Σ_Y^{-1/2}; canonical correlations are its singular values.
- KCCA/Deep CCA replace linear maps with kernel/neural maps (more reach, more
  capacity, more overfitting). PLS maximizes covariance instead of correlation
  (no whitening — stabler at small n).
- HSIC (Gretton et al. 2005): ‖cross-covariance operator‖²_HS; with characteristic
  kernels HSIC = 0 ⇔ independence of the paired variables.

**Assumptions**: **correctly paired rows** — the single load-bearing assumption. The
family is undefined for unpaired datasets; misapplying it there is the most common
error in this space (CROSS_DATASET_FRAMEWORK §2, constitutional note). Linear CCA
additionally assumes linear shared structure and well-conditioned covariances
(regularize when p ≈ n).

**Null value under independence (relational H₀)**: with shuffled pairing, *held-out*
canonical correlation collapses to a null distribution centered near 0 (width set by
n, p, q — calibrated by simulation, not formula). **In-sample canonical correlations
are not evidence at any value**: for p + q ≳ n they approach 1 between independent
datasets (the relational face of the Marchenko–Pastur phenomenon — the largest sample
canonical correlations of independent Gaussians follow RMT laws; see
`marchenko-pastur-tracy-widom.md`).

**Detects / blind to**: detects shared latent factors across two views of the same
entities, with held-out predictive confirmation. Blind to direction (correlation is
symmetric); blind to everything when pairing is wrong or absent; linear CCA blind to
nonlinear sharing (KCCA's job, at multiplicity cost, A3).

**Finite-sample cautions**: the high-dimensional spurious-correlation regime starts
early (in-sample ρ̂₁ between *independent* 50-dim Gaussians at n = 100 is ≈ 0.9);
ridge-regularize and report held-out only. Number of components retained is a
multiplicity dimension. HSIC permutation null: permute one view's row order, m ≥ 199,
+1 correction.

**Reference summary**: CCA is the two-view diagonalization of shared variance; its
modern reading is that X and Y are conditionally independent given a shared latent z,
and the canonical directions estimate z's loadings. The lab's rule reduces the whole
family to one sentence: *fit on train pairs, freeze, report held-out correlation
against the shuffled-pairing null* — everything in-sample is geometry, not evidence.

**Canonical references**:
- Hotelling, "Relations Between Two Sets of Variates," Biometrika 28 (1936).
- Andrew, Arora, Bilmes & Livescu, "Deep Canonical Correlation Analysis," ICML 2013.
- Gretton, Bousquet, Smola & Schölkopf, "Measuring Statistical Dependence with
  Hilbert-Schmidt Norms," ALT 2005.
- https://en.wikipedia.org/wiki/Canonical_correlation

**Use in this project**: relational instrument R3 (`relational_admission.py`):
admission E1 (independent views, shuffled-pairing FPR ≈ α; in-sample inflation
demonstrated and logged as the negative control's teaching output) + E6 (planted linear
latent: held-out canonical correlation beats shuffled null, dies under shuffling).
Real use requires genuinely paired rows — e.g. draw-date-paired (draw features, tidal/
geomagnetic features); note covariate permutation tests (ledger row 2) already cover
the scalar version and are all null.
