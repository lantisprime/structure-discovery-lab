# MMD & Energy Distance — Kernel Two-Sample Tests

**Domain face**: relational (distributional similarity, same feature space)

**Statement**:
- Gretton et al. (2012): MMD²(P,Q) = E[k(X,X′)] + E[k(Y,Y′)] − 2E[k(X,Y)] for a kernel k.
  If k is *characteristic* (e.g. Gaussian RBF), population MMD = 0 ⇔ P = Q.
- Székely–Rizzo energy distance: E(P,Q) = 2E‖X−Y‖ − E‖X−X′‖ − E‖Y−Y′‖ ≥ 0, with
  equality iff P = Q. Energy distance is MMD with the (conditionally negative-definite)
  distance-induced kernel — the two are one family, not two classes.
- Both admit exact permutation tests by pooling the samples and relabeling
  (exchangeability under H₀: P = Q).

**Assumptions**: both samples live in one shared feature space with a meaningful
metric/kernel; i.i.d. sampling within each dataset (serial dependence breaks the
pooled-permutation null — block variants required, A5); kernel bandwidth chosen by a
pre-declared rule (median heuristic) or charged as multiplicity (A3).

**Null value under independence (relational H₀)**: for two independently generated
samples from the *same* distribution, MMD̂² concentrates at O(1/n) above 0 and the
permutation p-value is U(0,1). The relational claim "A and B differ" requires rejection;
the claim "A and B are alike" is only a *failure to reject* and carries a mandatory
power statement (A4 — absence of evidence is quantified, never asserted).

**Detects / blind to**: detects any distributional difference in the kernel's reach
(location, scale, shape, multimodality). Blind to *relatedness of meaning* — two
identical distributions need not be causally or semantically connected (equality ≠
relationship); blind to row-level correspondence (it never produces a map).

**Finite-sample cautions**: bandwidth selection is a hidden multiplicity dimension —
sweeping bandwidths until rejection is the relational form of the forking-paths error
(charge per A3). Low power in high dimension at small n; the honest report includes the
power curve from the planted-shift positive control (E4). For time-indexed data, pooled
relabeling is forbidden as sole null; use block permutation.

**Reference summary**: the kernel mean embedding maps P to μ_P in an RKHS; for
characteristic kernels the map is injective, so ‖μ_P − μ_Q‖ is a metric on
distributions. The U-statistic estimator is unbiased, degenerate under H₀, with a
non-Gaussian limit — which is why the permutation null, not the asymptotic one, is used
here (mirrors the lab's exact-MC replacement of asymptotic chi-square, C1).

**Canonical references**:
- Gretton, Borgwardt, Rasch, Schölkopf & Smola, "A Kernel Two-Sample Test," JMLR 13 (2012).
- Székely & Rizzo, "Energy statistics: A class of statistics based on distances," JSPI 143 (2013).
- Lopez-Paz & Oquab, "Revisiting Classifier Two-Sample Tests," arXiv:1610.06545.
- https://en.wikipedia.org/wiki/Kernel_embedding_of_distributions

**Use in this project**: relational instrument R1 (`relational_admission.py`): admission
suite E1 (FPR on independent same-distribution samples) + E4 (power on planted mean
shift). Intended first real use: cross-game draw-feature comparison (6/42 vs 6/55 sum,
gap, parity profiles) under pool-and-relabel; any draws-vs-covariate use routes through
the temporal nulls instead (CROSS_DATASET_FRAMEWORK §6.2).
