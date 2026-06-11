# Coresets, Landmarks & Nyström — Subset-Preserved Structure

**Domain face**: relational (subset-to-whole recovery; geometry/objective preservation)

**Statement**:
- Coresets (Feldman & Langberg 2011): a weighted subset S with the *sensitivity*
  guarantee L(M_S, D) ≤ (1+ε) L(M_D, D) for a **specific objective** L (k-means,
  regression, …). The guarantee is objective-bound: a k-means coreset proves nothing
  about regression.
- Nyström (Williams & Seeger 2000): for kernel matrix K, landmarks give
  K ≈ C W† Cᵀ; approximation error is controlled by the spectral decay of K — fast
  decay (low effective rank) ⇔ few landmarks suffice.
- Leverage scores (Drineas et al. 2012): row/column influence in the low-rank
  structure; CUR decompositions select influential rows/cols with provable
  reconstruction bounds.
- Farthest-first traversal gives 2-approximate geometric coverage (k-center) —
  the standard landmark selector for manifold/topology preservation.

**Assumptions**: each guarantee names its own structure — sensitivity bound
(coresets), kernel spectral decay (Nyström), low-rank linear structure (leverage/CUR),
manifold/metric coverage (farthest-first). **No structure assumption, no guarantee**:
for i.i.d. unstructured data every informed selector performs like uniform random
(this is a *prediction* of the theory, used as the negative control).

**Null value under independence (relational H₀)**: the baseline is always the
**uniform-random subset at the same k** — every selector is measured as improvement
over it, with permutation/seed-resampled bands. On structureless data, informed
selectors sit inside the uniform-random band at every subset fraction (the flat
recovery curve, CROSS_DATASET_FRAMEWORK §4.5); on low-effective-rank data they beat it.

**Detects / blind to**: detects redundancy/compressibility — that a small subset
carries the dataset's geometry, spectrum, or objective. Blind to structure outside the
declared objective/kernel; blind to *why* the structure exists; landmark methods blind
to features thinner than the landmark spacing.

**Finite-sample cautions**: W near-singular at small landmark counts — regularize W +
γI and report γ. Adaptive/active selection optimistically biases later choices —
strict held-out discipline (A6). Selector choice is multiplicity (uniform, stratified,
farthest-first, leverage = 4 classes in the admission suite, charged per A3).

**Reference summary**: the entire family operationalizes one sentence — *structure is
whatever lets a part stand for the whole* — which is the lab's compression definition
of structure (`shannon-kolmogorov-compression.md`) made geometric. The recovery curve
(quality vs subset fraction, null-adjusted) is the family's single honest deliverable.

**Canonical references**:
- Feldman & Langberg, "A Unified Framework for Approximating and Clustering Data," STOC 2011.
- Feldman, "Introduction to Core-sets: An Updated Survey," arXiv:2011.09384.
- Williams & Seeger, "Using the Nyström Method to Speed Up Kernel Machines," NIPS 2000.
- Drineas, Magdon-Ismail, Mahoney & Woodruff, "Fast Approximation of Matrix Coherence
  and Statistical Leverage," JMLR 13 (2012).

**Use in this project**: relational instrument R6 (`relational_admission.py`):
admission E8 (Nyström spectral reconstruction on a low-rank+manifold dataset beats the
uniform-random-landmark null; on i.i.d. noise it does not). Real use: the registered
first run — tidal series (structured, curve should rise) vs lotto draws (i.i.d.
control, curve should sit on the null line), `relational_first_run.py`.
