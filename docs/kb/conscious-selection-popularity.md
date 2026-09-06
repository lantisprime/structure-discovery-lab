# Conscious Selection & Jackpot Sharing (popularity of combinations)

**Domain face**: decision (payout layer; sits beside card 16, below Doob/Kelly)

**Statement**: In a pari-mutuel lotto the win probability of a ticket is fixed, 1/C(P,6), but its
payout is not: if q(c) is the fraction of all N bets placed on combination c, the number of other
winning bets when c is drawn is K ~ Poisson(N·q(c)) (Stern & Cover 1989), and the expected jackpot
share is J·E[1/(1+K)] = J·(1−e^{−λ})/λ with λ = N·q(c). Players do not choose uniformly ("conscious
selection", Cook & Clotfelter 1993): q(c) is far from 1/C(P,6) for combinations built from birthday
numbers (≤31), small/"lucky" digits, and visual or arithmetic patterns, so the expected payout of a
ticket is a decreasing function of its popularity while P(win) is untouched. The **conscious-selection
index (CSI)** implemented in `src/csi_popularity.py` is a declared (not fitted) proxy for the rank of
q(c): a weighted sum of the ticket's excess share of numbers ≤31, ≤12, and in {1,3,5,7,9,11,12,13},
plus pattern flags (6-term and 5-term arithmetic progressions, runs of ≥3/≥4 consecutive numbers,
a common divisor ≥2, a single last digit, single parity), clipped to [0,1]. The functional it
constrains is E[winning bets | drawn combination] as a function of CSI.

**Assumptions**: the draw itself is i.i.d. uniform (the lab's standing verdict — this card asks a
question about *players*, not the machine); bets on distinct combinations are independent so that
co-winner counts are Poisson given q(c); the published "winners" count is the number of winning
standard bets (a bettor holding k identical bets counts k times, a System play counts its shares);
the proxy's components transfer from the UK/French/Israeli/Greek/Canadian markets where they were
measured to Philippine bettors (unverified locally — see cautions).

**Null value under i.i.d. uniform**: if draws are uniform AND selection is uniform (or simply
independent of the drawn combination), the winner count of a draw is independent of every function
of the drawn combination, so T1 = mean CSI of winner draws − mean CSI of winner-less draws = 0 and
T2 = rank correlation(CSI, winners) = 0. **Executable null (A1)**: draws by `random.sample(range(1,P+1),6)`
at the observed per-game lengths; winners by Poisson with the observed per-game mean, independent of
the combination. Null trial (Step 4, 500 datasets of the real shape): both statistics non-degenerate,
centred on 0 — recorded in `results/csi_popularity_2026-09-06.json` `step4_null_trial`, together with
their null correlation against the chi-square frequency statistic of the same simulated draws (C3
measurement: the sharing statistics are not functions of hit counts).

**Detects / blind to**: detects dependence of jackpot sharing on the popularity proxy — i.e. whether
the proxy captures anything about how Filipinos fill play-slips. Blind to: any property of the draw
process (by construction it conditions on the draw); the per-combination level of q(c) (only its
rank is proxied); sharing at Category II/III (5- and 4-match pools are shared per PCSO's Feb-2026
matrix but per-draw tier winner counts are not published); syndicates and repeated identical bets;
play-slip position effects (Polin et al. 2021 found first-row numbers most popular in Israel — the
PCSO slip layout has not been measured).

**Finite-sample cautions**: one year of official data (984 draws, 77 draws with ≥1 winning bet,
94 winning bets) — the observable effect is a contrast between the top CSI tertile and the rest,
not a calibrated q(c). Winner counts are overdispersed relative to Poisson (Baker & McHale 2009
predict exactly this under conscious selection), so Wald z from the Poisson GLM is descriptive; the
permutation p-values are the inferential statement. Multiple-bet inflation (e.g. 10 winning bets on
6/58 2026-05-05 for a low-CSI combination, CSI 0.09) adds noise that cannot be separated from
popularity. Weights were fixed from the literature before the first run; they must not be tuned on
these 984 draws — any refit is a new instrument requiring a fresh card and a held-out set.

**Reference summary** (distilled from fetched sources, 2026-09-06 research brief):
- Stern & Cover, *Maximum entropy and the lottery* (JASA 1989): estimated the joint distribution
  of number selection in Canadian 6/49 from marginal popularity data via constrained maximum entropy
  and showed by Monte Carlo that tickets made of unpopular numbers can have expected return above
  cost when sales or carry-overs are large — payoffs depend on other players, probabilities do not.
- Cook & Clotfelter, *The peculiar scale economies of lotto* (AER 1993, NBER w3766): coined the
  conscious-selection framing; sales respond to the visibility of winners, not to the odds.
- Farrell, Hartley, Lanot & Walker (JBES 2000): UK rollovers occur far more often than uniform choice
  predicts — direct evidence that q(c) is non-uniform.
- Baker & McHale (JRSS-A 2009): conscious selection makes winner counts overdispersed and correlated
  across prize tiers relative to the Poisson/uniform-choice model.
- Roger & Broihanne (J. Applied Statistics 2007), French 6/49 over 25 years: most popular numbers
  7, 12, 9, 13, 11, 5; least popular 32, 41, 39, 40, 38, 43; the top 1% of combinations held ~10% of
  all tickets in a 70-million-ticket draw.
- Polin, Ben-Isaac & Aharon (Judgment and Decision Making 2021), >800 million Israeli selections:
  small numbers over-selected (1 and 9 most), repeated digits preferred, multiples of 7 avoided,
  strong play-slip-position effects.
- Halpern & Devereaux (1989), Pennsylvania Daily Number: strongly non-uniform, pattern-seeking bets.
- PCSO, 2022-10-01 Grand Lotto 6/55: 9-18-27-36-45-54 (multiples of 9) drawn; ₱236,091,188.40
  shared by 433 winning bets (~₱545k each) — the local existence proof.

**Canonical references**:
- https://www.tandfonline.com/doi/abs/10.1080/01621459.1989.10478862 (Stern & Cover 1989)
- https://www.nber.org/papers/w3766 (Cook & Clotfelter 1993)
- https://www.tandfonline.com/doi/abs/10.1080/07350015.2000.10524865 (Farrell et al. 2000)
- https://academic.oup.com/jrsssa/article-abstract/172/4/813/7084574 (Baker & McHale 2009)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1959809 (Roger & Broihanne 2007)
- https://www.cambridge.org/core/journals/judgment-and-decision-making/article/patterns-in-manually-selected-numbers-in-the-israeli-lottery/F7167C1DD46E4876DAFCDDD6CE8F238C (Polin et al. 2021)
- https://link.springer.com/article/10.3758/BF03329930 (Halpern & Devereaux 1989)
- https://www.lottopcso.com/october-1-2022-6-55-pcso-lotto-jackpot-winner/ (PCSO 433-winner draw)

**Conflict scan (Step 3)**: C1 none (permutation inference, no asymptotics). C2 the executable null
is simulated, not imported. C3 measured in the null trial: T1/T2 vs chi-square null correlation
reported in the results JSON; new equivalence class `payout-sharing` (decision layer, not a hit-count
statistic). C4 two-sided. C5 the Feb-2026 price/jackpot restructure changed sales — one era in this
sample, flagged for the next reset. C6 two statistics, m=2 within the family. C7/C8 decision layer
only: its output never feeds detection. C9/C10 not relational.

**Use in this project**: EXPLORATORY (G0) decision-layer instrument, first run 2026-09-06 on 984
official draws (`results/csi_popularity_2026-09-06.json`, `docs/RESULTS_PCSO_REFRESH_2026-09-06.md`).
The web picker uses the same CSI (parity vectors in the results JSON) to reject the top 60% most
popular candidate tickets; this changes expected payout only, never P(win), and the picker says so.
Promotion to a confirmation family requires a reset boundary and fresh draws (Step 8).
