# Kelly Criterion & the St. Petersburg Paradox

**Domain face**: decision

**Statement**:
- Kelly (1956): to maximize the long-run exponential growth rate of wealth G = E[ln(1 + f*X)], bet the fraction f* of bankroll that maximizes expected log wealth. For a simple bet winning b-to-1 with probability p: f* = (bp - q)/b = p - q/b. For a long-shot with win probability p and net odds b, f* ~ p when b*p barely exceeds 1; never bet if edge <= 0.
- St. Petersburg (Bernoulli 1738): a game with infinite expected payoff (2^k with prob 2^-k) has finite worth under log utility: the certainty equivalent E[ln payoff] is finite, resolving the paradox; equivalently, finite bankrolls and finite casino capital truncate the tail.

**Assumptions**: known true probabilities and payoffs; repeated independent opportunities; divisible stakes; log utility (or the goal of maximal asymptotic growth / minimal time to reach a wealth target). Overestimating the edge makes Kelly overbet, which is worse than underbetting (growth is concave in f, negative beyond 2f*).

**Null value under i.i.d. uniform**: for a fair-or-worse lottery, edge <= 0 and f* = 0 — the Kelly-optimal stake is zero. Any positive stake has negative expected log growth.

**Detects / blind to**: not a detector; a sizing rule. It translates a measured edge into a stake and a required bankroll. Blind to model error in the edge estimate (garbage in, ruin out) and to utility functions other than log (fractional Kelly is the standard hedge).

**Finite-sample cautions**: Kelly's optimality is asymptotic; over finite horizons full Kelly has brutal variance (median outcomes fine, large drawdown probability), motivating half-Kelly. For a lottery, the win probability of the jackpot is p = 1/C(n,6), so even at a hypothetically positive edge, f* <= 1/C(n,6) ~ 1e-7 to 1e-8: the stake must be a vanishing fraction of bankroll, i.e., a fixed minimum ticket price implies an enormous required bankroll rather than a small bet.

**Reference summary**:
Daniel Bernoulli's 1738 resolution of the St. Petersburg paradox introduced logarithmic utility: a gamble's worth to a person is the expected log of resulting wealth, not the expected payoff, so a game with infinite mean but exploding-only-in-the-tail payoffs has modest log-value. Two centuries later, J.L. Kelly Jr. (Bell Labs, 1956) rediscovered log utility from an information-theoretic direction: a gambler with private information maximizing the exponential growth rate of capital should maximize expected log wealth, and the optimal fraction equals the information rate of the side channel. Breiman (1961) proved the strong optimality properties: Kelly betting asymptotically dominates any essentially different strategy and minimizes expected time to reach distant wealth targets.

The criterion's discipline is its real value here. It forces three numbers into one frame: edge, odds, and bankroll. For combinatorial-jackpot bets the win probability per ticket is 1/C(n,6); even granting a positive edge, the Kelly fraction cannot exceed the win probability, so a mandatory PHP25 minimum ticket is Kelly-consistent only with a bankroll on the order of C(n,6) x 25 ~ PHP 1 billion. Anyone with less is structurally overbetting — guaranteed negative log growth regardless of edge sign.

The project's decision stack is therefore ordered: Doob's optional stopping gates whether any strategy can have positive expectation; the EV decomposition (expected-value card) measures the per-ticket edge including taxes and co-winner splitting; Kelly then sizes the stake — and at every measured edge the answer is f* = 0.

**Canonical references**:
- https://en.wikipedia.org/wiki/Kelly_criterion
- https://en.wikipedia.org/wiki/St._Petersburg_paradox
- Kelly, "A New Interpretation of Information Rate", Bell System Tech. J. 35 (1956).
- Breiman, "Optimal gambling systems for favorable games", Proc. 4th Berkeley Symp. (1961).

**Use in this project**: Bernoulli log utility resolves St. Petersburg and motivates Kelly. Kelly f* <= 1/C(n,6) implies a PHP25 minimum stake needs roughly a PHP1B bankroll to be growth-optimal even under a favorable edge. Ordering of the decision layer: Doob gates, EV measures, Kelly sizes.
