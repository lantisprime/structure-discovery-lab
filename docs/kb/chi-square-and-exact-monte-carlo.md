# Chi-Square Goodness-of-Fit & Exact Monte Carlo Tests

**Domain face**: statistical

**Statement**: For observed counts O_i in k categories with expected counts E_i under H0, Pearson's statistic X^2 = sum_i (O_i - E_i)^2 / E_i converges in distribution to chi^2_{k-1} (minus additional df per estimated parameter) as min E_i -> infinity. When the asymptotic is invalid, the exact null distribution of X^2 (or any statistic) can be obtained by Monte Carlo: simulate M datasets from the exact null mechanism, and report p = (1 + #{X^2_sim >= X^2_obs}) / (M + 1).

**Assumptions**: asymptotic version requires independent observations, fixed categories, and all E_i large enough (rule of thumb E_i >= 5, none below 1). Monte Carlo version requires only that the null mechanism can be simulated exactly — here, drawing 6 numbers without replacement from {1..C}, which also handles the negative dependence among the 6 counts within a draw that the asymptotic chi-square ignores.

**Null value under i.i.d. uniform**: E_i = 6N/C per number over N draws; X^2 ~ chi^2_{C-1} approximately; Monte Carlo p uniform on (0,1).

**Detects / blind to**: detects any marginal frequency non-uniformity (hot/cold numbers, mechanical bias of specific balls). Blind to serial dependence, pair correlations, positional effects, and any structure preserving uniform marginals.

**Finite-sample cautions**: with expected counts in the 4.0–5.4 range (as in this project: 776 draws spread over multiple games and periods), the chi^2_{k-1} reference distribution is anti-conservative/distorted; moreover the within-draw sampling is without replacement (multivariate hypergeometric, not multinomial), inflating the naive variance model. Both problems are eliminated by exact Monte Carlo under the true 6-without-replacement mechanism. Monte Carlo p-values have resolution 1/(M+1) and binomial standard error sqrt(p(1-p)/M).

**Reference summary**:
Pearson's 1900 chi-square test compares observed category counts to expectations and is the canonical test of frequency uniformity. Its null distribution is only asymptotic: the multivariate CLT must hold cell-wise, which fails when expected counts are small, when cells are dependent, or both.

The modern remedy, going back to Barnard (1963) and Dwass (1957), is the Monte Carlo exact test: rather than trusting the chi-square approximation, generate the null distribution of the statistic by simulating the data-generating mechanism itself. The estimator p = (1+b)/(M+1), where b counts simulated statistics at least as extreme, is exactly valid (its rejection rate is at most alpha for any M), making it the safe default whenever the null mechanism is fully specified — as it is for a lottery, where the null is literally "6 numbers drawn uniformly without replacement."

For lottery data the mechanism matters twice: small expected counts break the asymptotics, and the without-replacement draw induces negative correlation between the six counts of a single draw. Simulating real draws (not Poisson or multinomial surrogates) bakes both into the null automatically.

**Canonical references**:
- https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test
- https://en.wikipedia.org/wiki/Monte_Carlo_method#Monte_Carlo_testing (Dwass 1957; Barnard 1963)
- https://en.wikipedia.org/wiki/Exact_test
- Agresti, *Categorical Data Analysis*, 3rd ed., Ch. 1, 3.

**Use in this project**: Frequency uniformity testing. The asymptotic chi-square version was found invalid at expected counts of 4.0–5.4 and was replaced by exact Monte Carlo sampling of 6-without-replacement draws; resulting p-values were 0.10–0.90 across all games and periods (no frequency anomaly). Scripts: montecarlo_certification.py.
