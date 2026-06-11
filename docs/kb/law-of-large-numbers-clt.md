# Law of Large Numbers & Central Limit Theorem

**Domain face**: statistical

**Statement**:
- LLN (strong form): if X_1, X_2, ... are i.i.d. with E|X_1| < infinity, then (1/n) * sum_{i=1}^{n} X_i -> E[X_1] almost surely as n -> infinity.
- CLT (Lindeberg–Lévy): if additionally Var(X_1) = sigma^2 < infinity, then sqrt(n) * (X-bar_n - mu) / sigma -> N(0,1) in distribution.
- RG view: N(0,1) is the unique stable fixed point of the block-averaging (renormalization) map T applied to distributions with finite variance; excess kurtosis of block means of size b decays as kappa_4(b) = kappa_4(1)/b, flowing to the Gaussian fixed point.

**Assumptions**: independence (or weak dependence with summable correlations), identical distribution (or Lindeberg/Lyapunov conditions for non-identical), finite mean (LLN) and finite variance (CLT). Heavy tails with infinite variance flow instead to Lévy alpha-stable fixed points.

**Null value under i.i.d. uniform**: sample frequencies converge to 1/C per number; standardized counts z = (O - E)/sqrt(E(1-p)) are asymptotically N(0,1); block-mean excess kurtosis flows toward 0 as 1/b.

**Detects / blind to**: detects mean shifts and frequency bias via z-scores; the kurtosis-flow diagnostic detects heavy-tailed (Lévy) alternatives that violate finite variance. Blind to dependence structures that preserve marginals (e.g., a stationary Markov chain with uniform stationary distribution gives identical long-run frequencies).

**Finite-sample cautions**: CLT approximation quality is governed by Berry–Esseen (error <= 0.4748 * rho/(sigma^3 sqrt(n))); poor for small expected counts or highly skewed summands. z-scores on counts need continuity correction or exact tests when E < ~5. Block-kurtosis estimates are noisy at large block sizes (few blocks), so the RG flow must be compared against a simulated i.i.d. null, not asymptotics.

**Reference summary**:
The law of large numbers, first proved in Bernoulli's *Ars Conjectandi* (1713) and given its modern almost-sure form by Kolmogorov, states that empirical averages of i.i.d. random variables converge to the population mean. It is the bedrock guarantee that long-run lottery frequencies stabilize, and it underwrites every estimator used in this project.

The central limit theorem sharpens this: fluctuations of the average around the mean, scaled by sqrt(n), are universally Gaussian whatever the parent distribution, provided variance is finite. This universality is why z-scores and chi-square statistics have distribution-free null calibrations at large n.

A deeper reading, due to Jona-Lasinio and others, recasts the CLT as a renormalization-group statement: repeated block averaging is a map on the space of probability distributions, and the Gaussian is its attracting fixed point in the finite-variance basin, while Lévy stable laws attract the infinite-variance basins. Tracking how the excess kurtosis of block means decays with block size therefore tests *which* basin the data lives in — a direct probe for heavy-tailed mechanisms.

**Canonical references**:
- https://en.wikipedia.org/wiki/Law_of_large_numbers
- https://en.wikipedia.org/wiki/Central_limit_theorem
- https://en.wikipedia.org/wiki/Berry%E2%80%93Esseen_theorem
- G. Jona-Lasinio, "Renormalization group and probability theory", Phys. Rep. 352 (2001), https://arxiv.org/abs/cond-mat/0009219
- Billingsley, *Probability and Measure*, 3rd ed., Ch. 5-6.

**Use in this project**: Underwrites all z-scores used across the analysis. The CLT-as-RG-fixed-point view was used directly in the universality analysis: the block-mean kurtosis flow of draw statistics was checked for convergence to the Gaussian fixed point (it converged, consistent with finite-variance i.i.d. behavior). Scripts: all.
