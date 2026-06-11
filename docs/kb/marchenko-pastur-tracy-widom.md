# Marchenko–Pastur Law & Tracy–Widom Distribution

**Domain face**: cross-sectional/physical

**Statement**:
- Marchenko–Pastur (1967): let X be an m x n random matrix with i.i.d. entries of mean 0 and variance sigma^2, and Y = (1/n) X X^T. As m, n -> infinity with aspect ratio lambda = m/n in (0, infinity), the empirical eigenvalue distribution of Y converges weakly to the MP law with density f(x) = sqrt((lambda_+ - x)(x - lambda_-)) / (2 pi sigma^2 lambda x) on [lambda_-, lambda_+], where lambda_± = sigma^2 (1 ± sqrt(lambda))^2 (plus an atom at 0 of mass 1 - 1/lambda when lambda > 1).
- Tracy–Widom (1994/96): the largest eigenvalue fluctuates around the bulk edge lambda_+ on scale n^{-2/3}, with limiting law TW_beta (beta = 1 for real symmetric/GOE-class). TW-GOE has mean ~ -1.2065, skewness ~ +0.293.
- For correlation matrices of n observations of m variables: eigenvalues inside [lambda_-, lambda_+] with sigma^2 = 1 are indistinguishable from noise; only escapes above lambda_+ (calibrated by TW) indicate genuine common factors.

**Assumptions**: independent entries (or rows) with finite fourth moment; large dimensions; for correlation matrices, standardized columns. Universality theorems make the limit insensitive to the entry distribution.

**Null value under i.i.d. uniform**: all eigenvalues of the number-indicator correlation matrix fall within the (finite-size, simulation-calibrated) MP-type bulk; the largest eigenvalue's fluctuations follow the TW-GOE shape (positive skew ~ 0.29) around the edge.

**Detects / blind to**: detects linear cross-sectional structure — clusters of numbers that co-occur or avoid each other, common "factors" across the pool, machine-induced correlated ball behavior — as eigenvalues escaping the noise bulk. Blind to nonlinear or higher-order dependence with zero pair correlation, and to time-structure (it pools over draws).

**Finite-sample cautions**: MP and TW are asymptotic; with m ~ 42-58 numbers and n = a few hundred draws, the bulk edges are blurred and the indicator variables are Bernoulli with within-draw negative dependence (exactly-6-per-draw constraint), shifting the null spectrum — so the null bulk and the lambda_max distribution must be simulated from real 6-without-replacement draws rather than read off the formulas. Eigenvalue estimates near the edge are biased outward; a single modest escape needs TW-calibrated, simulation-checked p-values.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Marchenko%E2%80%93Pastur_distribution):
The Marchenko–Pastur law, proved by Volodymyr Marchenko and Leonid Pastur in 1967, describes the asymptotic eigenvalue (singular-value) distribution of large rectangular random matrices: for Y_n = (1/n) X X^T with i.i.d. zero-mean variance-sigma^2 entries and aspect ratio m/n -> lambda, the empirical spectral measure converges to a deterministic law supported on [sigma^2(1-sqrt(lambda))^2, sigma^2(1+sqrt(lambda))^2], with explicit density and moments (mean sigma^2, variance sigma^4 lambda, skewness sqrt(lambda)). The same law arises as the free Poisson law in free probability.

The practical use highlighted in the source is exactly the one in this project: for sample *correlation* matrices, sigma^2 = 1 and the eigenvalues falling inside [(1-sqrt(lambda))^2, (1+sqrt(lambda))^2] "could be considered spurious or noise" — e.g., for 10 stocks over 252 days only eigenvalues above (1+sqrt(10/252))^2 ~ 1.43 are significantly different from random. Escapes above the bulk edge are the signature of genuine common structure; this is the standard RMT denoising recipe in econophysics.

The source also notes the max/min singular values converge to the bulk edges but that for finite matrices these are "more what you'd call guidelines than actual rules" — the fluctuation theory at the edge is governed by the Tracy–Widom distribution at scale n^{-2/3}, which supplies the proper test for whether the largest observed eigenvalue is an escape or just an edge fluctuation. Hence the pairing: MP gives the bulk, TW gives the edge test.

**Canonical references**:
- https://en.wikipedia.org/wiki/Marchenko%E2%80%93Pastur_distribution
- https://en.wikipedia.org/wiki/Tracy%E2%80%93Widom_distribution
- Marchenko & Pastur, Mat. Sb. 72 (1967).
- Bai & Silverstein, *Spectral Analysis of Large Dimensional Random Matrices*, Springer (2010).

**Use in this project**: RMT eigenvalue bulk applied to number co-occurrence correlation matrices: zero escapes above the noise bulk in all games. As a meta-check, the simulated null distribution of lambda_max had skewness +0.316 versus the universal TW-GOE +0.293 — universality reaching the analysis itself (the null machinery reproduced the predicted universal edge law). Script: structure_discovery.py.
