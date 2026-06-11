# Doob's Optional Stopping Theorem

**Domain face**: decision

**Statement**: Let (M_t) be a martingale with respect to filtration (F_t) (E[M_{t+1} | F_t] = M_t), and let T be a stopping time. If any of: (a) T is bounded; (b) T has finite expectation and increments are bounded (|M_{t+1}-M_t| <= c); or (c) the stopped process is uniformly integrable — then E[M_T] = E[M_0]. For a supermartingale (E[M_{t+1}|F_t] <= M_t, the gambler's case with house edge), E[M_T] <= E[M_0].

**Assumptions**: the stopping rule T uses only information available so far (no foresight); one of the integrability conditions holds — in practice guaranteed by any finite bankroll, finite credit, table limits, or bounded playing horizon.

**Null value under i.i.d. uniform**: a fair lottery makes the bettor's cumulative net winnings a martingale (or strict supermartingale after takeout); hence E[wealth at any stopping time] = (or <=) initial wealth. No betting schedule, stake-sizing scheme, or stopping rule has positive expected profit.

**Detects / blind to**: not a detector but a gate: it converts "no predictive edge found" into "no betting strategy can profit," closing the gap between statistical nulls and decision-making. It is blind to (i.e., does not rule out) strategies that change the per-bet expectation itself — a genuinely biased wheel, mispriced prize structure, or +EV jackpot — which is why EV analysis (see expected-value card) sits behind this gate.

**Finite-sample cautions**: the theorem's conditions are not technicalities — the classic "martingale" doubling system *appears* to beat a fair game precisely because unbounded T with unbounded stakes violates conditions (a)-(c); with any finite bankroll B, the small probability of ruin times the catastrophic loss exactly cancels the high probability of small wins, restoring E = 0 (and E < 0 with house edge). Simulations of stopping strategies on finite samples routinely show lucky positive paths; the theorem says the expectation over paths is pinned.

**Reference summary**:
Doob's optional stopping (optional sampling) theorem, a cornerstone of martingale theory developed by J.L. Doob in the 1940s-50s, formalizes the folk truth that you cannot beat a fair game by cleverly choosing when to bet, how much to bet, or when to walk away. If the game is fair, cumulative wealth is a martingale, and under mild integrability conditions its expectation at any stopping time equals the starting wealth; if the game is unfavorable (every real lottery, after takeout and taxes), wealth is a supermartingale and expected wealth can only decrease.

The theorem's power for this project is architectural: it decouples the statistical question from the decision question. Even a project that found weak statistical anomalies would still face Doob — only an anomaly large enough to flip the *sign of per-bet expectation* matters for betting, because stake-sizing and stopping manipulations are provably expectation-neutral. The martingale doubling system is the canonical cautionary example: it converts a fair game into "win 1 unit with probability close to 1, lose everything with small probability," leaving the expectation unchanged at zero and negative once any edge or bet/bankroll limit exists.

Hence the project's decision layer is ordered: Doob gates (is there a sign-flipping edge at all?), EV measures it (expected-value card), and Kelly sizes it (kelly-criterion card). With all statistical instruments null, the Doob gate stays closed and no betting layer is reachable.

**Canonical references**:
- https://en.wikipedia.org/wiki/Optional_stopping_theorem
- https://en.wikipedia.org/wiki/Martingale_(probability_theory)
- https://en.wikipedia.org/wiki/Martingale_(betting_system)
- Williams, *Probability with Martingales*, Cambridge, Ch. 10.

**Use in this project**: The theorem that no betting system beats a fair (or unfavorable) game is the project's decision-layer gate: statistical nulls plus Doob imply no stake-sizing or stopping strategy can profit. Also invoked to explain precisely why martingale doubling fails (violated integrability conditions, finite-bankroll ruin term).
