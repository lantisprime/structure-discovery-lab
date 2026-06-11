# Gromov–Wasserstein Distance — Alignment Without a Shared Space

**Domain face**: relational (cross-dataset alignment, different feature spaces, no anchors)

**Statement**:
- Mémoli (2011): for metric-measure spaces (X, d_X, μ_X), (Y, d_Y, μ_Y), the GW
  distance minimizes Σ_{i,j,k,l} |d_X(i,k) − d_Y(j,l)|² π_ij π_kl over couplings π with
  marginals μ_X, μ_Y. It is a metric on isomorphism classes of mm-spaces: GW = 0 iff
  the spaces are measure-preserving isometric.
- Only *internal* distances enter — no shared coordinate system, embedding, or feature
  correspondence is needed. Fused GW adds a feature-cost term when partial feature
  correspondence exists.
- The optimizer **always returns a coupling**, including between two independent noise
  clouds. The coupling's existence is zero evidence; only its distortion's position in a
  matched-null distribution is evidence (the relational form of A2/A4).

**Assumptions**: internal pairwise distances are meaningful in both datasets; comparable
intrinsic scale (or scale-normalized costs); the entropic solver adds a regularization
parameter ε that is a declared constant or charged as multiplicity (A3). Non-convex:
solver returns a local optimum — seeds fixed, multi-start declared.

**Null value under independence (relational H₀)**: GW distortion between a dataset and
independently regenerated data with matched marginals/spectrum sits in a
simulation-calibrated null band; observed distortion must fall below the null's α
quantile. Null couplings: GW against matched-marginal regenerations of d_Y, never
against arbitrary noise (preserve every nuisance — size, dimension, distance
distribution — destroy only the claimed correspondence, A1).

**Detects / blind to**: detects shared intrinsic geometry (cluster pattern, manifold
shape, relational motifs) between datasets with disjoint feature spaces. Blind to
direction/causality (symmetric by construction); blind to which of many near-optimal
couplings is "the" correspondence (non-identifiability); blind to structure not encoded
in pairwise distances.

**Finite-sample cautions**: O(n²) memory in the cost matrices — subsample/landmark for
n > ~2000. Entropic GW distortion is biased upward relative to exact GW; compare like
with like (same ε for observed and null). Near-symmetric datasets admit many
equally-good couplings: report coupling entropy alongside distortion. Local optima can
inflate null-band width — same solver settings everywhere.

**Reference summary**: GW is the Gromov–Hausdorff idea made statistical: instead of
asking "can X embed in Y?", it asks "how much must pairwise distances distort under the
best soft matching?" — turning shape comparison into optimal transport on relations.
POT implements exact (conditional-gradient) and entropic solvers.

**Canonical references**:
- Mémoli, "Gromov–Wasserstein Distances and the Metric Approach to Object Matching," FoCM 11 (2011).
- Peyré, Cuturi & Solomon, "Gromov-Wasserstein Averaging of Kernel and Distance Matrices," ICML 2016.
- Flamary et al., "POT: Python Optimal Transport," JMLR 22 (2021). https://pythonot.github.io
- https://en.wikipedia.org/wiki/Gromov%E2%80%93Wasserstein_distance

**Use in this project**: relational instrument R2 (`relational_admission.py`): admission
E1 (independent clouds → null distortion, FPR ≈ α) + E2 (two views of one planted latent
→ distortion below null band). Intended real use: cross-game co-occurrence-geometry
alignment; subset-landmark GW for the §5 cross-dataset alignment protocol.
