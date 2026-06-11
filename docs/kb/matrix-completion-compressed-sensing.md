# Matrix Completion & Compressed Sensing — Recovery Under Structural Assumptions

**Domain face**: relational (subset-to-whole recovery; reconstruction claims)

**Statement**:
- Candès & Recht (2009): an n×n rank-r matrix with incoherent singular vectors is
  exactly recoverable from O(n^1.2 r log n) uniformly sampled entries by nuclear-norm
  minimization. Practical solver here: iterative soft-thresholded SVD (SoftImpute,
  Mazumder et al. 2010).
- Donoho (2006) / Candès–Romberg–Tao: a signal s-sparse in a known basis is exactly
  recoverable from O(s log(n/s)) *structured random* measurements satisfying RIP, by
  ℓ₁ minimization.
- Both are **conditional impossibility-reversals**: recovery of the unobserved part is
  information-theoretically impossible in general (infinitely many completions exist);
  low rank / sparsity is what collapses the solution set. This is the formal content of
  CROSS_DATASET_FRAMEWORK §4.1.

**Assumptions**: matrix completion — low rank, incoherence (mass not concentrated in
few entries), sampling pattern independent of values; compressed sensing — sparsity in
a *declared* basis and RIP-style measurements (arbitrary row-subsampling does NOT
satisfy RIP; claiming CS guarantees for plain subsets is the classic misuse, forbidden
here). Noise versions degrade gracefully (stable recovery bounds).

**Null value under independence (relational H₀)**: held-out-entry RMSE of the
completion, compared against (a) the marginal baseline (column means) and (b) the same
solver run on a *permuted-entries* null matrix with identical margins and observed
fraction. On full-rank/i.i.d. data, the solver's held-out RMSE sits at the
marginal-baseline band — the honest "no recoverable structure" verdict. The recovery
phase transition (success probability vs sampling fraction) is sharp; admission
verifies the solver sits on the correct side for planted low rank and the null side for
noise.

**Detects / blind to**: detects low-rank (completion) or sparse (CS) structure with a
quantified reconstruction certificate — the strongest subset-to-whole claim available.
Blind to high-rank structure, to structure in an undeclared basis, and to coherent
low-rank structure (spiky singular vectors violate incoherence); blind to causality of
the structure.

**Finite-sample cautions**: rank/sparsity level and regularization λ are multiplicity
dimensions (declare a rule: λ from a *training* split only). Leakage between observed
and held-out entries (duplicated rows, derived columns) fakes recovery — the E8 failure
mode; run the duplicate audit first (dataset card Part 4 discipline). Small matrices:
the log-factor in sample bounds bites; rely on the empirical null, not the asymptotic
threshold (C1).

**Reference summary**: both theorems trade an untestable universal claim ("recover
anything") for a testable conditional one ("if low-rank/sparse, then recoverable, and
here is the certificate"). The lab inverts them: run the solver, and *whether recovery
beats the matched null* becomes the test of whether the structural assumption holds at
all — assumption-checking by attempted reconstruction.

**Canonical references**:
- Candès & Recht, "Exact Matrix Completion via Convex Optimization," FoCM 9 (2009).
- Donoho, "Compressed Sensing," IEEE Trans. Inf. Theory 52 (2006).
- Mazumder, Hastie & Tibshirani, "Spectral Regularization Algorithms for Learning
  Large Incomplete Matrices," JMLR 11 (2010).
- https://en.wikipedia.org/wiki/Matrix_completion

**Use in this project**: relational instrument R7 (`relational_admission.py`):
admission E8 (planted rank-2 matrix: held-out RMSE far below marginal & permuted nulls;
i.i.d. noise matrix: RMSE inside null band). Real use: draw-history matrices
(number × draw presence) — prediction from the entropy floor: completion will sit on
the null line; that flat curve is the registered expected outcome, not a failure.
