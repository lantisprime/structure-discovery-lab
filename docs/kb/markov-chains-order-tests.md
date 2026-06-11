# Markov Chains & Order Tests

**Domain face**: dynamical

**Statement**: A sequence {X_t} on finite state space S is a Markov chain of order r if P(X_t | X_{t-1}, ..., X_1) = P(X_t | X_{t-1}, ..., X_{t-r}). Order-0 (i.i.d.) vs order-1 is tested by the likelihood-ratio (G) statistic G = 2 * sum_{i,j} n_ij * ln( n_ij / (n_i. * n_.j / n) ) ~ chi^2 with (|S|-1)^2 df under order-0 (Anderson & Goodman 1957). For an estimated transition matrix P-hat, the second-largest eigenvalue modulus |lambda_2| sets the relaxation/mixing time: correlations decay as |lambda_2|^t, with characteristic time tau = -1/ln|lambda_2|.

**Assumptions**: stationarity over the sample; enough transitions per cell for the chi-square asymptotics (or Monte Carlo calibration); a chosen state coarse-graining (e.g., terciles of a draw statistic) that is fixed before testing.

**Null value under i.i.d. uniform**: transition rows all equal the stationary (uniform-derived) distribution; G ~ chi^2_{(k-1)^2}; estimated |lambda_2| is NOT 0 but positive with magnitude ~ O(1/sqrt(n)) per entry noise — the null |lambda_2| distribution must be simulated.

**Detects / blind to**: detects first-order serial dependence: stickiness/overlap between consecutive draws (the overlap test is a monotone-equivalent of a class of order-1 alternatives), tercile-state persistence, slow mixing. Blind to higher-order or long-range dependence with vanishing one-step signature, and to dependence in statistics outside the chosen coarse-graining.

**Finite-sample cautions**: empirical |lambda_2| of a noisy estimated transition matrix is biased upward — even i.i.d. data yields |lambda_2| well above 0 — so relaxation-time estimates need an i.i.d.-simulated null band. Sparse transition cells break G-test asymptotics. Terminology trap: "memoryless" in the Markov-property sense (future depends only on present) is weaker than i.i.d. (future independent of present too); a fair lottery is i.i.d., which implies but is not implied by the Markov property — failure to reject order-0 vs order-1 does not "prove i.i.d.", it bounds one-step memory.

**Reference summary**:
Markov chains, introduced by A.A. Markov in 1906, model sequences in which the future depends on the past only through the present state. Their statistical theory was systematized by Anderson and Goodman (1957) and Billingsley (1961), who gave maximum-likelihood estimates of transition probabilities (row-normalized transition counts) and chi-square/likelihood-ratio tests of whether a chain has order 0 (independence) against order 1, or order r against r+1. These order tests are the standard instrument for asking "does yesterday's draw inform today's?"

The spectral view complements the testing view: a transition matrix P has eigenvalue 1 with the stationary distribution as eigenvector, and the second-largest eigenvalue modulus |lambda_2| governs the geometric rate at which the chain forgets its initial condition (relaxation time tau = -1/ln|lambda_2|). A relaxation time barely above 1 draw means next-to-no usable memory: even if dependence existed at the point estimate, it would decay essentially within a single draw.

For lottery analysis, draws were coarse-grained into interpretable states (e.g., terciles of sum/spread statistics; overlap counts between consecutive draws). Each test in this family targets a specific one-step alternative; together with calibrated nulls for the eigenvalue statistics they bound the exploitable serial structure.

**Canonical references**:
- https://en.wikipedia.org/wiki/Markov_chain
- Anderson & Goodman, "Statistical inference about Markov chains", Ann. Math. Statist. 28 (1957).
- https://en.wikipedia.org/wiki/G-test
- Levin & Peres, *Markov Chains and Mixing Times*, AMS — https://pages.uoregon.edu/dlevin/MARKOV/

**Use in this project**: Order-0 vs order-1 tests; overlap/stickiness statistic (monotone-equivalent alternative); tercile G-test; |lambda_2| relaxation time estimated at 1.05–1.14 draws (consistent with the simulated i.i.d. null). The memoryless terminology was explicitly clarified (Markov property vs i.i.d.). Scripts: markov_analysis.py, markov_chain_model.py.
