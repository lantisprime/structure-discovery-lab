The core data constants match the supplied files, but **v2.1 does not fully implement the corrected interpretation**. The main problems are the reversed Bayes-factor claim, an uncalibrated EV calculation, rounded thresholds that change the Python selection rule, and incorrect backtest totals.

Reviewed branch `feature/pcso-refresh-2026-09`, HEAD `d81e1663e31fcf190994d4158647db4070a24f49`. No files changed. Below, **L** refers to lines in [lotto_picker.html](/Users/charltonho/Developer/projects/structure-discovery-lab/lotto_picker.html).

**1. Completeness against the prior review, §1–§7**

“Missing” below distinguishes omitted review material from an incorrect calculation; not every omitted derivation needs to appear in the main picker interface.

**1.1. Prior §1 — likelihood and posterior predictive**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| Specify product-weight sampling instead of assuming that “without replacement” uniquely defines a model | **correct** | L48 explicitly defines \(f_w(S)=\prod_{i\in S}w_i/e_6(w)\). |
| Correct likelihood, including \(e_6(w)^{-T}\) | **correct** | L66. |
| Remove Dirichlet conjugacy and product-of-posterior-means prediction | **correct** | L49 defines the integrated predictive multiplier; L66 describes weighted importance sampling. `Dirichlet(a+c)` is correctly identified as the proposal, not the posterior. |
| Fix the prior independently of the data | **correct** | L48: \(a=100\), fixed a priori; sensitivity \(a=10,1000\) at L66. |
| Correct inclusion probability \(\pi_i=w_i e_5(w_{-i})/e_6(w)\), and \(\sum_i\pi_i=6\) | **missing** | L66/L187 discuss inclusion deviations without defining inclusion probability. Add this formula to the methodological explanation. |
| Full non-Dirichlet posterior, sequential-drawing alternative, and distinctions among script, plug-in, and integrated multipliers | **missing** | Only the selected model and integrated multiplier appear at L48–49/L66. Add a technical appendix if full §1 coverage is intended. |
| Relative “10%” deviation and 95% intervals | **correct** | L53/L66/L187 use deviation from \(6/P\), with 95% intervals identified at L53. |

**1.2. Prior §2 — maximum-predictive sets**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| All five maximum-predictive sets | **correct** | L97–101; generated from counts at L142–144 and displayed at L185. |
| Six largest counts; equal-count alternatives | **correct** | L143 uses descending count, ascending number. L66/L98/L185 correctly identify the 6/42 alternatives 18 and 35. |
| Per-game fitting sample sizes: 192, 193, 192, 193, 192 | **missing** | L87 gives only the aggregate 962. Add per-game fitting \(T\); `GAMES.n` is the confirmation sample size, not fitting \(T\). |
| Uniform probabilities | **correct** | Computed as \(1/\binom P6\), L182. |
| Conditional predictive probabilities in the review’s table | **missing** | L185 shows \(R\), not \(R/\binom P6\). The EV’s probability is model averaged and cannot substitute for these table entries. |
| Predictive multipliers and latent-multiplier intervals | **correct against JSON; mismatch with literal review numbers** | L97–101 copy the JSON correctly. See the numerical comparison below. |
| Intervals concern \(R_w(S^*)\), not numerical uncertainty in its posterior mean | **correct** | Explicit at L66. |
| Probability intervals are \(p_0\) times the multiplier intervals; uniform \(p_0\) has no parameter uncertainty | **missing** | Add this distinction beside the interval explanation. |

The page’s **rendered** values differ from the prior review:

| Game | Page \(R\) [CrI], L185 | Prior §2 \(R\) [CrI] |
|---|---|---|
| 6/42 | 1.482 [0.985, 2.128] | 1.483 [0.987, 2.126] |
| 6/45 | 1.502 [0.994, 2.165] | 1.503 [0.994, 2.168] |
| 6/49 | 1.560 [1.028, 2.262] | 1.559 [1.028, 2.259] |
| 6/55 | 1.640 [1.074, 2.383] | 1.641 [1.076, 2.382] |
| 6/58 | 1.505 [0.978, 2.200] | 1.504 [0.979, 2.200] |

These are differences between the stored integration and independent reconstruction, **not erroneous JSON transcription**. Fix L66’s “agrees to three decimals”; retain the JSON values with their provenance.

**1.3. Prior §3 — Bayes factors and material inclusion deviations**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| \(BF_{01}\) direction and equal prior model odds | **correct in definition** | L50 defines evidence for uniform over unequal weights. |
| Interpretation of the actual \(BF_{01}<1\) values | **mismatch** | L53 says they favour uniform in every game except 6/55. All five favour \(M_1\) over \(M_0\), with varying, prior-sensitive strength. Replace with: “At \(a=100\), all \(BF_{01}\) values are below one; support for unequal weights is strongest in 6/55 and highly prior-sensitive.” |
| Five \(BF_{01}(100)\) values and equal-odds \(P(E_{10}\mid D)\) | **correct** | L97–101/L187 match JSON. |
| Prior sensitivity at \(a=10,1000\) | **correct as ranges; missing as full table** | L66 shows the JSON ranges. The individual five-game sensitivity values from prior §3 are not displayed. |
| Conditional \(P(E_{10}\mid D,M_1(100))\approx1\), and warning that this is not evidence that \(M_1\) is true | **missing** | Add the conditional-versus-model-averaged distinction at L66. |
| \(P(E_{10}\mid D,M_1(1000))=(.0122,.0141,.0176,.0253,.0291)\) | **missing** | Add the sensitivity row if incorporating all corrected quantities. |
| 200,000 samples/game; high effective sample size | **correct as summary** | L66; JSON ESS is 195,744.9–198,276.8. |
| Prior review’s precise ESS range, relative BF MC SE \(\le .00033\), and meaning of “approximately one” | **missing** | Add with explicit attribution to the independent reconstruction; do not imply those diagnostics were regenerated for the stored JSON. |
| Bayes-factor integral/importance identity and event-probability mixing formula | **missing** | Add to the technical appendix for full coverage. |

**1.4. Prior §4 — serial dependence**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| No rejection at five-game Bonferroni threshold .01 | **correct** | L53. Both reviewed test families have this outcome. |
| Composite ballwise \(G^2\), invalid naïve \(\chi^2_P\) calibration, whole-draw permutation method | **missing** | L53/L187 discuss only an aggregate conclusion and overlap p-values. Add the distinction. |
| Five composite statistics and five whole-draw permutation p-values | **missing** | No corresponding table. |
| Joint overlap model and five LR statistics | **missing** | No model equation or LR-statistic table. |
| Exact joint p-values | **mismatch with the review for two games; correct against JSON** | Page L97/L100 uses .0529 for 6/55 and .0407 for 6/49; prior §4 gives .04761 and .04540. |
| Different null assumptions and limited scope of these tests | **missing** | Replace broad “Order-1 dependence … none” with “Neither tested persistence statistic rejects after Bonferroni; other cross-ball transition alternatives were not exhausted.” |

The p-value difference is substantive provenance, not MC noise: [the Python implementation](/Users/charltonho/Developer/projects/structure-discovery-lab/src/pcso_next_draw_posterior.py:69) orders outcomes by **absolute distance from expected total overlap**, whereas the review reports the joint LR test. Either implement the review’s LR ordering or label the page’s test “exact absolute-deviation overlap test.”

**1.5. Prior §5 — CSI inference**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| Within-game standardization for fitted coefficient | **correct in text; mismatch in runtime use** | L68/L108 say within-game SD; L136–141 instead standardize against simulated uniform tickets. See §3.5 below. |
| Within-game ranks, including tied-rank caveat | **missing** | L68 prints T2 without defining it as rank correlation or explaining ties. |
| Within-game permutation | **correct** | L68. Its exchangeability condition is omitted; add if explaining inferential validity. |
| Poisson pseudo-MLE and HC1 sandwich inference | **correct** | L68/L108. The information-matrix SE is not presented as robust inference. |
| Jackpot as a count-prediction covariate; no identified popularity per purchased bet | **correct in text; violated by EV** | Caveat at L68; EV converts the coefficient into per-bet sharing probabilities at L157–158. |
| Reject pooled tertile multiplier as a standardized popularity ratio | **correct by removal** | No 2.8/2.84 multiplier or tertile claim remains. The replacement normalized strategy contrast is missing. |
| Holm instead of Šidák | **correct** | L68. |
| Observed-slope power is not independent validation | **correct by omission** | No power-based validation claim remains. |
| 984 draws, 77 winner draws, 94 winning bets | **correct** | L65/L68/L201. |
| T1=.735656; T2=.162076; adjusted p=.0001 each | **correct, rounded** | L68: .74, .16 and .0001. Individual raw p-values .00005/.0001 are missing. |
| \(\beta=.518506\); count ratio 1.680 [1.444,1.954] | **correct, rounded** | L53/L68/L108/L201. |
| SEs .075010/.077124/.077866, dispersion 2.226282, jackpot coefficient .327720 with HC1 SE .192016 | **missing** | Add diagnostics if the page is intended to carry every corrected quantity. |
| HC1 covariance formula and standardized high/low comparison formula | **missing** | Add to methodological appendix; use the normalized comparison in the implementation where applicable. |

**1.6. Prior §6 — backtest**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| Remove sign-flip calibration | **correct** | L69 describes regenerated uniform draws with generated tickets held fixed. |
| Draw-level aggregation and shared baseline | **correct as summary** | L69 says draw-paired. Replicate counts and the dependence between tickets/replicates sharing a draw are missing. |
| Seven mean differences | **correct, rounded** | L69 matches the current JSON. |
| Seven historical HAC(8) intervals and seven conditional-null Z values | **missing** | No corresponding table. |
| Reviewed asymptotic p-values versus new MC p-values | **mismatch with literal review; correct against JSON** | The page now reports the MC values, detailed below. Label these as a different calibration rather than exact reproduction of the review. |
| Holm over seven; no post-hoc equivalence-class merger | **correct** | L69. “Charged once” is gone. |
| Conditional variance formula, asymptotic Z formula and Bonferroni .007143 alternative | **missing** | Add to technical appendix if full coverage is intended. |
| Correlations .402/.068/−.022 do not establish equivalent hypotheses | **missing, with the misuse removed** | Neither the correlations nor an equivalence-merger claim appear. |
| Exact simulation of adaptive strategies must regenerate histories and replay strategies | **missing** | L69’s fixed-ticket simulation does not do this for hot/cold/overdue/repeat/Markov rules. Add the limitation or use the replay calibration required by the review. |
| Multiplicity-only old result .0427 differs from corrected-null .0542 | **missing, appropriately historical** | No need to restore this abandoned-result comparison in the picker. |

**1.7. Prior §7 — next-draw quantities and monitoring**

| Item | Verdict | Page evidence and exact fix |
|---|---|---|
| \(R\) is a jackpot-probability ratio, not payout-return ratio | **correct in banner; misused in EV** | L49 is correct; L208 applies A’s ratio to A/B. |
| \(R=1\) under uniform draws | **correct** | L49. |
| \(\Delta=0\) under uniform draws; two distinct tickets have jackpot probability \(2/\binom P6\) | **missing explicitly** | L191 gives uniform expected matches per ticket. Add the pair probability and \(\Delta\) distinction. |
| Top-six \(R\) summaries | **correct against JSON** | L185, with reconstruction differences above. |
| Bottom-six, hot-six and last-draw-six \(R\) means and intervals — all 15 game/rule entries | **missing** | Displaying last-draw balls at L183 does not display their posterior summaries. |
| All 40 \(1000\Delta_s\) means and intervals: uniform, v1, v2, hot, cold, overdue, repeat, Markov across five games | **missing** | No next-draw expected-match-edge table. |
| One million candidate pairs/game and MC SE below .000020 matches/ticket | **missing** | Do not substitute L136’s unrelated 20,000-ticket reference simulation. |
| \(R_{\rm mix}\) formula | **correct** | L50. |
| \(\Delta_{\rm mix}\), model-averaged point masses at \(R=1,\Delta=0\), and conditional intervals excluding model uncertainty | **missing** | Add alongside the model-average explanation. |
| Ten normalized CSI strategy contrasts and their HC1 slope-based intervals | **missing** | No \(C_{s,g}\) table. L157 computes a different quantity. |
| Count contrasts are not calibrated jackpot-return gains; payout requires expectation over tickets and co-winner distribution | **mismatch** | L68 acknowledges missing exposure, but L157–160/L208 still present a calibrated-looking EV. See §3.4. |
| Monitoring frequency p-values, lunar correlations, ball-45 test, Kp unavailable | **correct, rounded** | L67/L77–85. |
| Within-game lunar p-values | **correct against JSON; not literal review values** | JSON .835708/.952002 versus review .83760/.95005; page rounds to .84/.95. |
| Lunar bootstrap intervals and ball-45 rule \(R=1.121[.958,1.293]\) | **missing** | No corresponding quantities at L67. |
| Bonferroni applies within one look; repeated cumulative looks need separate control | **missing** | Add the explicit limitation from the confirmation JSON’s final `note`. |
| Static-weight inference is not evidence of changing hotness/Markov mechanisms | **missing explicitly** | Add this scope statement to L66. |

**First-pass residue:** none of the seven named items survives literally as an endorsed page method: sign flips, Šidák, “charged once,” tertile 2.8, empirical-Bayes concentration, Dirichlet-multinomial multiplier, or information-matrix SE. Their replacements appear at L48–50/L66/L68–69. However, **the old conceptual misuse of a CSI count contrast as calibrated sharing risk survives in L157–160**, despite the corrected caveat at L68.

**2. Numeric constants against JSON and CSV sources**

I compared all **249 ball-count entries**, all `POST` fields, all ten `HITS` records, and each last-draw field. The CSV hashes match the hashes recorded in the supplied JSONs; the 962 canonical records match their official CSV records, including number order.

**2.1. `GAMES`, `COUNTS`, monitoring and thresholds — correct as copied**

| Game; page lines | Canonical draws / count entries checked | Confirmation n | Page chi p → JSON p | Page q40 = JSON q40 |
|---|---:|---:|---|---:|
| 6/42; L76–77/L89 | 192 / 42 | 38 | .066 → .066193 | .0243 |
| 6/45; L78–79/L90 | 193 / 45 | 37 | .498 → .498050 | .0091 |
| 6/49; L80–81/L91 | 192 / 49 | 37 | .046 → .045695 | .0282 |
| 6/55; L82–83/L92 | 193 / 55 | 37 | .376 → .375762 | .0172 |
| 6/58; L84–85/L93 | 192 / 58 | 37 | .107 → .106889 | .0033 |

All pools and weekday arrays agree with the official CSV’s game schedules. **No count or monitoring transcription mismatch.** The q40 values have a runtime precision problem, addressed in §3.3.

**2.2. Last draws and jackpot defaults — correct**

| Game | Date | Numbers, as drawn | Jackpot; winning bets |
|---|---|---|---|
| 6/42 | 2026-09-05 | 29,35,37,24,3,36 | ₱28,197,852.66; 0 |
| 6/45 | 2026-09-04 | 26,38,17,35,11,16 | ₱41,598,513.75; 0 |
| 6/49 | 2026-09-03 | 15,45,13,18,8,2 | ₱25,239,749.17; 0 |
| 6/55 | 2026-09-05 | 22,44,4,54,47,1 | ₱177,438,115.66; 0 |
| 6/58 | 2026-09-04 | 53,34,12,9,5,47 | ₱265,466,683.02; 0 |

These equal L77/L79/L81/L83/L85 exactly. L179 therefore initializes every game with its last official jackpot.

**2.3. `POST` — correct against posterior JSON**

| Game; line | R | CrI | Rmix | BF01 | Equal-odds \(P(E_{10})\) | Stored overlap p |
|---|---:|---|---:|---:|---:|---:|
| 6/42; L98 | 1.4825 | [.9851,2.1277] | 1.2480 | .9452 | .5141 | .6523 |
| 6/45; L99 | 1.5024 | [.9935,2.1649] | 1.3158 | .5910 | .6285 | .1406 |
| 6/49; L100 | 1.5603 | [1.0277,2.2622] | 1.3314 | .6906 | .5915 | .0407 |
| 6/55; L97 | 1.6400 | [1.0741,2.3831] | 1.5242 | .2210 | .8190 | .0529 |
| 6/58; L101 | 1.5049 | [.9782,2.2000] | 1.3393 | .4879 | .6721 | .1708 |

Sets and tie arrays also match. The overlap fields are correctly rounded from JSON.

**2.4. `HITS`, CSI constants and prize matrix**

- **correct:** all ten `HITS` records at L103–107 match every official jackpot-winning draw since July 1: game, date, drawn order, jackpot and winner count. No missing or extra hit row.
- **correct:** `BETA_CSI=.5185`, L108, equals the CSI JSON; the coefficient CI comment [.367,.670] agrees with the HC1 calculation.
- **correct:** all ten CSI weights and eight lucky numbers, L111–112, equal Python and JSON.
- **correct against repository documentation; missing from the specified JSON/CSV evidence:** ticket cost, minimum jackpots, and Category II/III matrix. The four JSONs and two CSVs are not a prize-rule registry. These values agree with [DATASET.md:66](/Users/charltonho/Developer/projects/structure-discovery-lab/datasets/pcso-lotto/DATASET.md:66):

| Game | Minimum jackpot | Category II pool | Category III pool | Category IV |
|---|---:|---:|---:|---:|
| 6/42 | ₱10M | ₱1.1M | ₱1.0M | ₱20 |
| 6/45 | ₱15M | ₱1.2M | ₱1.1M | ₱30 |
| 6/49 | ₱25M | ₱1.3M | ₱1.2M | ₱50 |
| 6/55 | ₱45M | ₱1.4M | ₱1.3M | ₱60 |
| 6/58 | ₱75M | ₱1.5M | ₱1.4M | ₱100 |

Exact fix: cite a dated, retained official prize-rule source. The CSV minima corroborate the minimum-jackpot values but cannot establish the complete payout rules.

**2.5. `growth` — missing definition/provenance**

L77–85 provide unexplained constants; L191 calls them “official jackpot growth per rollover draw.” No supplied result defines that estimator.

| Game | Page growth | Latest observed jackpot increment |
|---|---:|---:|
| 6/42 | ₱2,883,029 | ₱3,184,110.07 |
| 6/45 | ₱3,098,930 | ₱3,342,344.51 |
| 6/49 | ₱61,838 | ₱61,365.30 |
| 6/55 | ₱4,928,699 | ₱5,154,358.49 |
| 6/58 | ₱6,667,770 | ₱6,992,139.40 |

These are **not necessarily numerical errors in an unspecified historical estimator**, but they are not the latest increments and cannot be verified as labelled. Remove the line, or specify the estimator/window and reproduce it from the CSV.

**3. JavaScript algorithm review**

**3.1. `csi()` — correct**

L114–127 agrees with [Python `csi()`](/Users/charltonho/Developer/projects/structure-discovery-lab/src/csi_popularity.py:45) for valid six-number integer tickets. This includes all excess-share normalizations, AP6/AP5 precedence, run4/run3 precedence, GCD, last digit, parity and clipping.

Executed results:

| Ticket; pool | JavaScript = Python |
|---|---:|
| 9,18,27,36,45,54; 55 | .8524822695035461 |
| 1,2,3,4,5,6; 42 | 1 |
| 3,7,11,13,21,27; 45 | .44127764127764124 |
| 32,38,39,40,41,43; 49 | .3 |
| 2,12,22,32,42,52; 58 | 1 |
| 5,14,23,33,44,57; 58 | .0033333333333333327 |
| 1,16,25,26,43,58; 58 | .08851851851851851 |
| 10,20,30,40,50,55; 55 | .55 |

All eight rounded expected values satisfy the page’s \(10^{-5}\) tolerance. **Another 1,000 valid tickets agreed exactly.** No fix required to `csi()`.

**3.2. `posteriorTickets()` — correct selection; EV attribution is incorrect**

L142–144 implements the same ordering as [Python:143](/Users/charltonho/Developer/projects/structure-discovery-lab/src/pcso_next_draw_posterior.py:143). Exchange symmetry under the specified prior makes ticket A a maximum-predictive set.

Ticket B is:

| Game | Ticket B |
|---|---|
| 6/42 | 1,18,20,23,24,35 |
| 6/45 | 3,10,17,41,42,43 |
| 6/49 | 6,10,13,15,23,25 |
| 6/55 | 2,9,13,20,24,41 |
| 6/58 | 19,20,23,28,30,34 |

- **correct:** L186 describes B as ranks 7–12, disjoint from A, with its multiplier uncomputed and at most A’s.
- **correct:** this is also the maximum-predictive set restricted to numbers outside A.
- **mismatch:** it is not generally the globally second-best ticket, nor an established optimal pair. L186 avoids claiming that, but L208 nevertheless assigns A’s `Rmix` to B.
- **Exact fix:** integrate \(R_D(B)\) separately; use ticket-specific probabilities and average the two ticket EVs.

**3.3. `sampleUnif()` and `randomPair()`**

**Fisher–Yates structure — correct; exact uniformity — mismatch.**

L133–134 correctly shuffles then slices. However, reducing a uniform uint32 modulo \(m=i+1\) is biased unless \(m\mid2^{32}\).

Writing \(2^{32}=qm+r\), \(r\) residues have probability \((q+1)/2^{32}\); the others have \(q/2^{32}\). The per-step total-variation distance is

\[
\frac{r(m-r)}{m\,2^{32}}.
\]

For these pools:

| Pool | Upper bound on full-shuffle total variation |
|---|---:|
| 42 | \(3.32\times10^{-8}\) |
| 45 | \(3.86\times10^{-8}\) |
| 49 | \(4.60\times10^{-8}\) |
| 55 | \(5.62\times10^{-8}\) |
| 58 | \(6.54\times10^{-8}\) |

The practical effect is tiny, but “uniform” is not mathematically exact. **Fix:** reject uint32 values at or above \(2^{32}-(2^{32}\bmod m)\) before taking `% m`.

**q40 acceptance — mismatch with the Python backtest.**

Python computes and compares against an **unrounded** quantile at [backtest:57](/Users/charltonho/Developer/projects/structure-discovery-lab/src/pcso_strategy_backtest.py:57). The page compares against the rounded exported values:

| Pool | Page threshold | Python threshold | Consequence |
|---|---:|---:|---|
| 42 | .0243 | .02431372549019608 | Excludes the quantile boundary |
| 45 | .0091 | .009090909090909089 | Slightly higher threshold |
| 49 | .0282 | .028184281842818373 | Slightly higher threshold |
| 55 | .0172 | .017210951674088735 | Excludes the quantile boundary |
| 58 | .0033 | .0033333333333333327 | Excludes a large tied boundary |

On the exact seeded 20,000-ticket reference samples, page versus Python accepted fractions were:

- 6/42: **36.320% versus 41.585%**
- 6/45: 43.585% versus 43.585%
- 6/49: 45.910% versus 45.910%
- 6/55: **38.160% versus 44.065%**
- 6/58: **25.290% versus 42.240%**

These are reference-sample fractions, not exact population probabilities. They demonstrate a material rule change caused by rounding.

**Exact fix:** store full-precision thresholds, round only for display, and say “CSI at or below the estimated 40th-percentile cutoff.” Because CSI is discrete, that cutoff does not imply exactly 40% acceptance.

**Disjoint-pair rejection — correct structure, with two qualifications.**

- Before filtering, the shuffled 12-number sample gives a uniform ordered disjoint pair, apart from the tiny modulo bias.
- Rejection conditions on both scores passing. The resulting pair is not uniform over all pairs; a ticket’s marginal distribution also depends on how many acceptable disjoint partners it has.

**400-attempt fallback — mismatch.** L153 returns the best rejected pair, so L68’s “both tickets must” and L188’s “CSI ≤ q40” are not guaranteed. I forced 400 rejected proposals and the function returned `[1,2,3,4,5,6]` and `[7,8,9,10,11,12]`.

Python’s fallback returns the **last** rejected pair, whereas the page returns the **best**. Thus even the failure behavior differs.

**Exact fix:** continue sampling asynchronously until acceptance, or explicitly report failure without presenting rejected tickets as qualifying picks.

**3.4. `ev()` — exact implemented formula and mismatches**

Let

\[
C=\binom P6,\qquad
h_k=\frac{\binom6k\binom{P-6}{6-k}}C,\qquad
s(\lambda)=\frac{1-e^{-\lambda}}{\lambda},
\]

and, for the supplied tickets,

\[
\bar z=\frac1m\sum_{j=1}^m
\frac{\operatorname{CSI}(S_j)-\widehat\mu_{U,P}}
{\widehat\sigma_{U,P}},
\qquad M=e^{0.5185\bar z}.
\]

Except for the `share()` small-\(\lambda\) shortcut, L155–160 computes

\[
\boxed{
EV_{\rm page}
=.8J\frac{R_p}{C}s(NM/C)
+.8A_2h_5s(Nh_5)
+.8A_3h_4s(Nh_4)
+A_4h_3
}
\]

and L209 displays net \(EV_{\rm page}-25\).

L208 supplies \(R_p=R_{\rm mix}(A)\) for A/B and \(R_p=1\) for C/D.

**Hypergeometric tiers — correct under uniform draws.** L138–139 gives the exact probabilities for all seven match counts; executed comparisons matched Python exactly and summed to one.

**Poisson pool-sharing identity — correct under its assumptions.** L140 correctly computes \(E[1/(1+K)]\) for Poisson \(K\). Category II/III pool amounts are multiplied by this expected share, rather than treated as fixed per-winner awards.

However, \(K\sim\operatorname{Poisson}(Nh_k)\) assumes a particular uniform, independent competitor-bet model. The results do not estimate lower-tier co-winner distributions. If \(N\) means total tickets sold, it should also be distinguished from the number of other tickets; Poisson itself approximates the finite-count binomial model.

**Tax — mismatch.** L158–159 always applies 20% tax to Categories I–III. It never checks whether the realized **individual share** exceeds ₱10,000. The threshold rule exempts winnings of ₱10,000 or less. [BIR explanation](https://www.foi.gov.ph/requests/taxation-bir-072588744352/)

Under the stated rule, replace each taxable-pool contribution with

\[
p_k\,E\!\left[
T\!\left(\frac{A_k}{1+K_k}\right)
\right],
\quad
T(x)=
\begin{cases}
x,&x\le10{,}000,\\
.8x,&x>10{,}000.
\end{cases}
\]

Tax must be applied inside the expectation. This matters particularly for Category III at the default sales assumption.

**A’s `Rmix` applied to B — mismatch.** The result defines \(R_D(S)\) for a particular six-set. `Rmix(A)` is not the probability multiplier of every “predicted ticket.”

For a pair, the per-ticket jackpot contribution should average ticket-specific terms:

\[
\frac12\sum_{S\in\{A,B\}}
\frac{R_{\rm mix}(S)}C
E[T(J/(1+K_S))].
\]

The probability that either distinct ticket wins is \([R_{\rm mix}(A)+R_{\rm mix}(B)]/C\), not \(2R_{\rm mix}(A)/C\).

**Model consistency — mismatch.** Multiplying only jackpot probability by `Rmix` while retaining uniform lower-tier probabilities is a hybrid approximation, not the complete posterior-predictive EV. Nor is the CSI-filtered C/D rule guaranteed to have \(R=1\) under the unequal-weight model.

**Exact fix:** either calculate every ticket/tier under the same posterior mixture or explicitly present a uniform-draw scenario with separate posterior jackpot-probability information.

**CSI sharing multiplier — mismatch with the defined result.**

The CSI result defines a **count ratio per fitted within-game SD**, \(e^\beta=1.68\). It does not identify

\[
q(S)=\frac1C e^{\beta z(S)}.
\]

Three separate errors occur:

1. **Missing exposure/calibration:** game/jackpot-adjusted winning-bet counts do not identify purchased-ticket probability \(q(S)\).
2. **Missing normalization:** even under an added exponential ticket-choice model, probabilities would require normalization by \(E_U[e^{\beta z}]\).
3. **Wrong averaging:** \(e^{\beta\bar z}\) is a geometric mean of multipliers. It is neither the mean count multiplier nor the average of nonlinear sharing factors.

The prior review’s defined strategy contrast is

\[
C_{s,g}
=\frac{E_{Q_s}[e^{\beta z}]}{E_U[e^{\beta z}]},
\]

not the page’s \(e^{\beta\bar z}\). Even that corrected count contrast is **not a calibrated payout multiplier**. The fitted dispersion of 2.226 also makes clear that pseudo-MLE/HC1 inference does not establish a Poisson co-winner distribution.

**Exact fix:** report CSI count contrasts separately. Any EV model using them must be explicitly identified as an additional, unvalidated ticket-choice/co-winner scenario and evaluated per ticket.

**3.5. `zcsi()` — mismatch**

L136–141 uses 20,000 newly simulated uniform tickets per pool on every page load. Python [within-game standardization](/Users/charltonho/Developer/projects/structure-discovery-lab/src/csi_popularity.py:129) uses the **observed official draws** used to fit the coefficient.

The fitted reference statistics, recomputed from the CSV, are:

| Pool | Observed-draw mean | Observed-draw sample SD |
|---|---:|---:|
| 42 | .109025883081 | .129033598370 |
| 45 | .099543610457 | .121632734284 |
| 49 | .103452031331 | .129107545078 |
| 55 | .074822679337 | .093637899891 |
| 58 | .070902572402 | .094544668148 |

Both methods standardize within a game, but **they are not the same covariate**. The discrepancy persists even with infinitely many uniform-reference samples. Runtime sampling adds further unnecessary variability to displayed z-scores and EV.

**Exact fix:** export and use the fitted observed-game means/SDs with the coefficient. A uniform-reference z-score may remain as a separately labelled descriptive statistic.

**4. Fact box and footer claims**

**4.1. Fact box, L53**

| Claim | Verdict | Exact fix |
|---|---|---|
| 962 official-verified draws | **correct** | No change. |
| Maximum-set R range 1.48–1.64 | **correct** | Specify conditional on \(M_1(100)\). |
| CrI lower endpoints .98–1.08 | **mismatch against JSON** | JSON endpoints span .9782–1.0741, which round to **.98–1.07**. The 1.08 follows the independent review’s 1.076, not the page’s stored interval. |
| Bayes factors favour uniform except 6/55 | **mismatch** | Reverse the interpretation as described in §1.3. |
| BF ranges .22–.95 at a=100 and 46–6,976 at a=10 | **correct against JSON** | Retain with corrected interpretation. |
| Model-averaged range 1.25–1.52 | **correct** | No numerical change. |
| Order-1 dependence “none” | **mismatch in scope** | Say no rejection by the specified tests, not absence of all serial dependence. |
| Backtest minimum Holm p=.055 | **correct, rounded** | JSON minimum is .0546. Qualify the adaptive-rule calibration. |
| CSI 1.68 [1.44,1.95] per within-game SD, HC1 | **correct** | State that it is an adjusted winning-bet-count association. |
| “Payout only, never P(win)” | **missing qualification** | Replace with “CSI models winning-bet counts; it does not establish a draw-probability effect or calibrated payout gain.” |

**4.2. Data footer, L65**

- **correct:** 984 official records, June 1, 2025–September 5, 2026; 962 canonical records, June 11, 2025–September 5, 2026; 834 existing records verified and 128 additions.
- **mismatch/overstatement:** the wording can imply that all 128 additions were checked against both archives. The [manifest](/Users/charltonho/Developer/projects/structure-discovery-lab/datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json:149) records **128/128 at lottopcso.com, 100/100 at pcsodraw.com**, with continuity checks covering its 28-row coverage gap.
- **Exact fix:** state those coverage counts explicitly.

**4.3. Posterior footer, L66**

- **correct:** likelihood, importance proposal/weights, 200,000 samples, ESS≥195,000, latent-multiplier intervals, BF sensitivity ranges, equal-odds event-probability range .51–.82, and the 6/42 tie.
- **mismatch:** “agrees to three decimals” is disproved by the comparison in §1.2 and the different overlap tests.
- **Exact fix:** “Independent reconstruction uses the same product-weight model and reaches similar conclusions; numerical estimates and overlap-test ordering differ.”
- **missing:** define \(z(w)=e_6(Pw)/\binom P6\), and state that displayed CrIs condition on \(M_1(100)\).

**4.4. Monitoring footer, L67**

All displayed numerical values correctly round the confirmation JSON:

- Five chi-square p-values: .066/.498/.046/.376/.107.
- Altitude \(r=-.015379\), global p=.832608, within-game p=.835708.
- Illumination \(r=.004786\), global p=.950452, within-game p=.952002.
- Ball 45: 2/37, expected 4.036364, p=.427453.
- Registered m=9; eight computable tests; zero flags; threshold .005556; Kp unavailable.

**missing:** the result’s explicit within-look-only error-control caveat. Add it; present .0056 as a rounded display of \(0.05/9\), not a replacement decision threshold.

**4.5. CSI footer, L68**

- **correct:** score ingredients, declared heuristic weights, Python functional parity, 984-draw validation, within-game permutation, T1/T2, Holm p-values, pseudo-MLE/HC1, count ratio/CI, exposure caveat and G0 status.
- **mismatch:** exact-uniform wording, guaranteed q40 acceptance, and “bottom 40%” interpretation; see §3.3.
- **missing source precision:** the result supports **literature-motivated declared weights**, not that the particular decimal weights were estimated or prescribed by those papers. Use that wording.
- **missing model detail:** the proportionality \(e^{.52z}\) is conditional on game and jackpot; the later sentence supplies that condition, but it should accompany the formula.

**4.6. Backtest footer, L69**

All seven displayed means and p-values correctly round the current JSON:

| Rule | JSON mean difference | JSON raw p / Holm p | Prior review raw p / Holm p |
|---|---:|---|---|
| v1 | .004007 | .0078 / .0546 | .00774 / .05421 |
| v2 | .008092 | .0134 / .0670 | .01374 / .06870 |
| Hot | .011958 | .4621 / 1 | .45729 / 1 |
| Cold | −.040787 | .0106 / .0636 | .01105 / .06630 |
| Overdue | −.000961 | .9561 / 1 | .95472 / 1 |
| Repeat | −.003527 | .7561 / 1 | .75690 / 1 |
| Markov | .007042 | .6625 / 1 | .66366 / 1 |

**mismatch:** “Best of 1.67M tickets: one 5-match.”

The JSON totals are:

- **2,335,200 ticket evaluations** across all eight strategies.
- **42 five-match outcomes:** uniform 7, v1 17, v2 7, repeat 4, Markov 7.
- **Zero six-match outcomes.**

Excluding uniform gives 1,834,800 evaluations and 35 five-match outcomes—still not the page’s claim.

**Exact fix:** “Across 2,335,200 simulated ticket evaluations, 42 had five matches and none had six. Evaluations include repeated tickets and share 834 historical draws.”

The 834-draw count and two tickets per replicate are correct, but the footer omits **300 replicates/draw for uniform/v1/v2 and 100 for each other rule**.

**4.7. EV footer, L70, and related rendered claims**

- **correct as stated model ingredients:** hypergeometric tiers, pooled Categories II/III, fixed Category IV, last-official jackpot defaults, and weekday schedules.
- **mismatch:** the tax implementation does not implement the described threshold.
- **mismatch:** the claimed application of `Rmix` to “predicted tickets” assigns A’s value to B.
- **mismatch:** the sharing multiplier is not the count contrast defined by the results.
- **missing:** clear identification of EV as an additional, uncalibrated scenario.
- **missing source in the result files:** prize-rule effective date, ticket price and 9 PM draw time require separate operational-source provenance.
- **mismatch at L191:** “Kelly bankroll ≈25C” is not a calculated Kelly bankroll for this multi-tier, shared-payout model. Remove it or compute Kelly from the complete payoff distribution; the expression is at most a special jackpot-only benchmark.
- **mismatch at L201:** “Full year” labels a roughly 15-month dataset. Replace with “Official sample, June 1, 2025–September 5, 2026.”

**5. Required edits**

1. **Correct L53’s Bayes-factor direction**, change the lower-endpoint range to .98–1.07, and narrow serial-dependence wording to the tests performed.
2. **Remove “agrees to three decimals” at L66** and distinguish the page’s absolute-deviation overlap test from the review’s LR test.
3. **Store full-precision q40 thresholds**, round only for display, and explain discrete cutoff ties.
4. **Use rejection sampling for bounded RNG integers** and prevent the 400-attempt fallback from returning tickets labelled as passing.
5. **Use the fitted observed-game CSI means/SDs** with `BETA_CSI`; remove runtime randomness from fitted z-scores.
6. **Compute B’s posterior multiplier separately** and average ticket-specific EVs. Use a consistent draw model across tickets and prize tiers.
7. **Stop treating `exp(beta * mean(z))` as calibrated sharing risk.** Separate the supported count contrast from any explicitly assumed ticket-choice/co-winner scenario.
8. **Apply the tax threshold to realized individual shares inside the expectation.**
9. **Correct the backtest total to 2,335,200 evaluations, 42 five-match outcomes and zero jackpots**, and include replicate counts.
10. **Add the adaptive-history calibration limitation and within-look monitoring caveat.**
11. **Correct archive coverage, remove or document `growth`, remove the unsupported Kelly-bankroll output, and replace “Full year.”**
12. **For full §1–§7 completeness**, add a technical appendix containing the omitted inclusion/BF formulas, conditional-model caveats, serial-test table, backtest uncertainty/Z table, strategy \(R/\Delta\) summaries, normalized CSI contrasts and monitoring intervals. Keep reconstruction values distinct from current JSON values.

Verification was read-only: extracted JavaScript executed in Node; 8 supplied plus 1,000 additional CSI comparisons passed; all hypergeometric probabilities matched; constant/CSV/hash checks passed; the fallback failure was reproduced. The tracked diff remains empty; the pre-existing untracked `bundles/` directory remains unchanged.