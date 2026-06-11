# Expected Value Decomposition & Payout-Relevant Backtesting (Stern-Cover Framing)

**Domain face**: decision

**Statement**: The expected value of a lottery ticket decomposes over prize tiers:
EV = sum over tiers t of P(match_t) * E[prize_t] - cost, where
- P(match_t) is hypergeometric: P(exactly m matches) = C(6,m) * C(n-6, 6-m) / C(n,6);
- jackpot prize is shared among co-winners: with K ~ Poisson(lambda) other winners (lambda = ticket sales x 1/C(n,6), adjusted for popularity of number combinations), the expected share multiplier is E[1/(1+K)] = (1 - e^{-lambda})/lambda;
- net prizes carry the 20% Philippine tax on winnings above the threshold.
Break-even jackpot J* solves EV = 0 given fixed lower tiers, tax, and expected co-winners. Backtesting any predictive model must score it by *payout-weighted* returns (ROI under the real prize structure), not proxy metrics (hit-rate, log-loss on numbers), because tier payouts weight errors by orders of magnitude differently.

**Assumptions**: known prize structure and tax; Poisson approximation for independent co-winners (breaks for popular human-chosen combinations — birthdays, sequences — which raise lambda conditional on those combinations winning); stationary ticket sales or modeled sales.

**Null value under i.i.d. uniform**: every ticket has identical EV; EV < 0 for all realistic jackpot levels once takeout, tax, and co-winner splitting are included; break-even jackpots typically exceed observed jackpots except in extreme rollover regimes, and even then co-winner inflation at high-sales rollovers claws the edge back.

**Detects / blind to**: a measurement layer, not a detector: converts any claimed predictive edge into pesos. It exposes models that look good on proxy metrics but lose money. Blind to risk preferences (handled by Kelly) and to whether an edge exists at all (handled by the statistical layer and Doob's gate).

**Finite-sample cautions**: backtested ROI on 776 draws is dominated by whether any near-jackpot hit occurred — variance is enormous, so backtests should compare against the distribution of ROI of random strategies on the same draws (paired null). Proxy metrics are systematically misleading: a model can raise 3-match hit-rate (worth ~PHP20-1000) while doing nothing for the tiers that carry essentially all EV. Poisson co-winner lambda is itself estimated; sensitivity analysis over sales and popularity assumptions is required.

**Reference summary**:
The expected-value analysis of lotteries is standard decision theory: enumerate prize tiers, attach hypergeometric probabilities, net out taxes, and — the step most often omitted — model jackpot sharing. Because all tickets in a pari-mutuel jackpot split the pool, the relevant quantity is E[J/(1+K)] where K is the number of co-winners; for K Poisson(lambda) this is J * (1 - e^{-lambda})/lambda, which decays toward J/lambda at high sales. This is why huge rollovers attract sales that largely neutralize the apparent EV improvement, and why unpopular (less human-typical) combinations have slightly better conditional EV without any change in winning probability — the only legitimate "strategy" content in lottery mathematics (cf. Stern & Cover's analysis of optimal lotto numbers under nonuniform popular play; Ziemba et al. on the same effect).

The framing borrowed from Stern & Cover (1989) — who studied lotto as a game where the *probabilities* are fixed but the *payoffs* depend on others' behavior — supplies the project's measurement discipline: a model's worth equals its payout-weighted expected return under the actual prize structure, not its accuracy on any intermediate statistic. The project verified this the hard way: proxy metrics (match-count based) flattered the Markov model, while prize-weighted backtesting revealed -71% ROI, i.e., decisively worse than useless for wealth.

Combined with the rest of the decision stack (Doob's optional stopping gates whether any strategy can be +EV; Kelly sizes a hypothetical edge), the EV decomposition with sensitivity analysis over jackpot level, sales, tax, and co-winner assumptions establishes break-even jackpot ranges for each PCSO game — none of which made any ticket +EV during the studied period.

**Canonical references**:
- Stern & Cover, "Maximum entropy and the lottery", J. Amer. Statist. Assoc. 84 (1989).
- https://en.wikipedia.org/wiki/Lottery_mathematics
- https://en.wikipedia.org/wiki/Hypergeometric_distribution
- https://en.wikipedia.org/wiki/Expected_value
- Ziemba et al., *Dr. Z's 6/49 Lotto Guidebook* (popularity/EV effects).

**Use in this project**: EV decomposition with hypergeometric prize tiers, 20% tax, and Poisson co-winner split E[J/(1+K)]; break-even jackpot ranges computed per game with sensitivity analysis. Payout-relevant backtesting was decisive: proxy metrics flattered the Markov model until prize-weighting showed -71% ROI.
