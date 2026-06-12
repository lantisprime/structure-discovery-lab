# Stein–Chen Poisson Approximation

**Domain face**: statistical

**Statement**: For a sum W = sum_{i=1}^{n} X_i of indicator variables (X_i ∈ {0,1}) with weak dependence, the total variation distance between the law of W and a Poisson distribution with mean lambda = E[W] satisfies:

d_TV(L(W), Poisson(lambda)) <= 2 * sum_{i=1}^{n} E[X_i^2 * E[X_i | X_i, (X_j)_{j in N(i)}]] / E[W]^2,

or more practically: d_TV <= 2 * (E[W^2] - E[W]) / E[W]^2 = 2 * (Var(W) + E[W]^2 - E[W]) / E[W]^2.

For the Stein–Chen coupling: d_TV <= 2 * A + B, where A = sum_{i,j adjacent} Cov(X_i, X_j) / E[W], and B = sum_i E[X_i^2 * sum_{j: i-j adjacent} (X_j + E[X_j])^2 / E[W]^2, with "adjacent" defined by the dependence graph. Under independence (A=0, B~0), W is approximately Poisson(E[W]).

**Assumptions**: 
- X_i are indicator (Bernoulli) random variables; W is their sum.
- Dependence structure is sparse and local: each X_i depends on at most O(1) others, not all.
- Mean lambda = E[W] is bounded away from 0 and infinity (practically: lambda > 1 suffices).
- Second-moment bounds are finite: E[W^2] < infinity.
- For the coupling bound, each X_i has a "regeneration" or "local" structure allowing explicit covariance control.

**Null value under i.i.d. uniform**: Under i.i.d. uniform draws from {1, 2, ..., n}, rare events (e.g., how many tickets achieve exactly 2 matches in a 6/55 lottery across N drawings) are governed by a sum of weakly dependent indicators. If matching events are rare (probability p = 1/C(55,2) << 1), the count W of such events converges to Poisson(N*p) as N -> infinity. The Stein–Chen bound guarantees this convergence *at finite N*: d_TV <= O(p), quantifying how close the true distribution (a sum of weakly dependent indicator indicator variables) is to Poisson(N*p).

**Detects / blind to**: 
- **Detects**: rare-event aggregation that violates Poisson scaling, signal overdispersion (variance > mean, suggesting clusters of co-occurring matches) or underdispersion (variance < mean). Applied to lottery co-winner counts, it detects whether human choice patterns (non-uniform number popularity) create clustering that Poisson (assumed independence) would miss.
- **Blind to**: the underlying probability p of a single match; it only constrains the *aggregated* count's law given lambda. Blind to changes in p over time (non-stationarity of draw rules). Blind to long-range dependence in the sequence of draws (assumes local mixing).

**Finite-sample cautions**:
- The Stein–Chen bound d_TV <= 2*(A + B) is *exact* but the constants A, B are difficult to compute without explicit model details. Practical application requires either (i) estimating them from observed data (covariances), or (ii) invoking a general bound like d_TV <= 2*E[W^2]/E[W]^2 which is looser and depends on the second moment.
- At very small lambda (rare events, few observed instances), the approximation's accuracy—even if theoretically valid—is unhelpful: the Poisson law has most mass near 0 with thin tails, and any observed cluster looks "significant" in relative terms. Absolute error is still small (because lambda is small) but relative misspecification matters.
- Sample size n_draws matters: the bound improves as dependence weakens (A,B shrink). With strong local structure (many pairs of indicators tightly coupled), the bound may be loose; MC sampling of the null W distribution is then preferable to asymptotic Poisson.
- The connection between theoretical lambda = E[W] and its empirical estimate (count / total events) depends on stationarity: if the match probability p(t) drifts across the n_draws observations, the effective lambda is misspecified. This is a stationarity gate parallel to THEOREM_GOVERNANCE.md A5.

**Reference summary**:
The Stein–Chen method, introduced by L.H.Y. Chen in *Ann. Probab.* 3 (1975), provides quantitative bounds on the distance between a sum of weakly dependent indicators and the Poisson distribution. Unlike older Poisson-limit results (Barbier, 19th century), which only stated "approximately Poisson," Stein–Chen gives explicit error terms: d_TV bounds in terms of covariances and second moments.

The key insight is a "Stein coupling": given any two probability measures (the true law of W and Poisson(lambda)), one can construct a joint distribution on both such that they differ only when certain dependence conditions are violated. This coupling transforms convergence into a measurable quantity—the total variation distance—that can be controlled via local-dependence parameters. The bound does not require W to be the sum of *independent* indicators, only that dependence is weak and local (e.g., each indicator depends on O(1) neighbors).

Arratia, Goldstein & Gordon's 1989 *Ann. Probab.* article "Two moments suffice" simplified application: the second moment E[W^2] alone (along with the first E[W] = lambda) is often enough to bound the Poisson distance, without needing explicit covariance computation, making the method practical for data-driven analysis.

Barbour, Holst & Janson's 1992 Oxford monograph *Poisson Approximation* systematized Stein–Chen for applied probability and provided the definitive reference for lottery problems: co-winner counts (does the number of all-six-match tickets across a season follow Poisson, indicating independence, or cluster due to human correlation in number choice?), collision counts in hash tables, record counts in random permutations, and rare-event counts in dynamic processes all fall into the regime where Stein–Chen applies.

**Canonical references**:
- Chen, L.H.Y. (1975). "Poisson approximation for dependent trials." *Ann. Probab.* 3(3): 534–545. https://projecteuclid.org/euclid.aop/1176996891
- Arratia, R., Goldstein, L., Gordon, L. (1989). "Two moments suffice for Poisson approximations: the Chen–Stein method." *Ann. Probab.* 17(1): 9–25. https://projecteuclid.org/euclid.aop/1176991496
- Barbour, A.D., Holst, L., Janson, S. (1992). *Poisson Approximation* (Oxford Studies in Probability). Oxford University Press. ISBN 978-0-198-51385-4.
- https://en.wikipedia.org/wiki/Poisson_distribution (see "limiting case" and "rare events")

**Use in this project**: The Stein–Chen bound will constrain rare-event statistics on the PCSO lotto dataset, specifically co-winner counts and repeat-combination counts. If a lottery is fair (tickets independent, draws stationary), these rare-count distributions should be approximately Poisson; deviations quantifiable by Stein–Chen d_TV indicate either systematic non-uniformity in ticket choice (human clustering of "lucky" numbers, e.g., birthdays) or structural nonstationarity (rule changes that alter match probabilities). Applied as a detection gate: does the observed co-winner count distribution have d_TV > threshold from Poisson? The threshold will be set by simulating the null (6-without-replacement, observed draw sequence, i.i.d. ticket generation), measuring its co-winner law, and bounding its distance to Poisson(E[co-winners]); if real data's d_TV lies outside the null band, it signals non-exchangeability in tickets or nonstationarity in rules. The card's role is to formalize this approximation's accuracy, not to assume Poisson counts blindly.
