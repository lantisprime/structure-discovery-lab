# Stochastic-prediction and lottery-prediction literature survey (arXiv + classics)

**Domain face**: statistical (sequential/anytime-valid inference; source of the adopted e-process monitor)

**Compiled:** 2026-09-06 · **Scope:** arXiv survey for the PCSO picker accuracy question ("can any
prediction theorem increase P(picking the winning 6-set)?"), redirected per operator to
*stochastic prediction* theory rather than "lottery" keyword search. Search provider: SearXNG
(`site:arxiv.org` queries); abstracts fetched and read for papers marked **[read]**; the SAVI
survey was read **in full** (992 lines of the arXiv HTML render).

**Verdict (jev-1.13.0, 2026-09-06):** no surveyed theorem provides an honest mechanism to raise
P(pick 6/6) above the picker's model-averaged R_mix (1.25–1.52) given the lab's backtest (no rule
beats uniform after Holm, min p = 0.055) and prior-sensitive Bayes factors (BF₀₁ 0.22–0.95 at
a=100, reversing at a=10). Best defensible improvement (probability 0.99): anytime-valid
e-process monitoring. Full judgment recorded in the PICKER task set, session 2026-09-06.

---

## A. Stochastic prediction theory (operator-directed search)

### A1. [read] Frey, Manton, Zhu — *Online Prediction of Stochastic Sequences with High Probability Regret Bounds*
- **URL:** https://arxiv.org/abs/2602.16236 (ICLR 2026)
- **Claim:** universal prediction of stochastic sequences over a countable alphabet achieves
  regret O(T⁻¹/²δ⁻¹/²) with probability ≥ 1−δ vs the best predictor in the class, plus an
  impossibility result: the δ exponent cannot be improved without extra assumptions.
- **Relevance to PCSO:** a *ceiling* theorem. With T ≈ 192 fitting draws per game and outcome
  space C(58,6) ≈ 4×10⁷, no online learner beats the class-best by more than O(T⁻¹/²); regret is
  measured against the best in-class predictor, not against uniform. Cannot raise pick accuracy.

### A2. [read] O'Neill — *Binomial Prediction Using the Frequent Outcome Approach*
- **URL:** https://arxiv.org/abs/2209.13950 (The Mathematical Scientist 37(2), 2012)
- **Claim:** "predict the most frequent outcome" converges to the accuracy of ideal
  parameter-aware prediction **iff a fixed unknown bias θ exists** (iid non-uniform). Under a
  known-uniform θ it converges to nothing better than uniform.
- **Relevance:** this is the theorem that *would* justify hot-number tickets — but only under a
  fixed bias, which the lab's BF₀₁ evidence supports only weakly and prior-sensitively. Jev:
  boosting hot numbers harder = prior-fishing (0.91). The picker's maximum-predictive ticket A is
  already the Bayesian-optimal version of this theorem under the declared prior.

### A3. [read] Polson, Zantedeschi — *De Finetti + Sanov = Bayes: Exchangeable Prediction under Moment Constraints*
- **URL:** https://arxiv.org/abs/2509.13283 (v3 2026-07-28)
- **Claim:** exchangeable prediction under empirical-moment constraints = Bayesian mixture of
  I-projections of the directing measure; sequential prediction under the limiting law is
  Bayesian prediction from a mixture.
- **Relevance:** confirms the de Finetti representation — under exchangeability the optimal
  predictive law is a mixture over iid product laws. The lab's Dirichlet-mixture M₁ is a
  principled restricted member of this class (Jev: do NOT claim provable optimality, 0.51). Adds
  no new predictive power for this problem.

### A4. [read, FULL] Ramdas, Grünwald, Vovk, Shafer — *Game-Theoretic Statistics and Safe Anytime-Valid Inference*
- **URL:** https://arxiv.org/abs/2210.01948 (v2, survey + monograph)
- **Core prediction/inference algorithm** (§1.2, §2.2 eq. 3–5, §3.2), stated in statistical terms:
  test a null hypothesis by a prequential evidence process. For each outcome, form the
  one-step-ahead (past-only) predictive density; the predictive likelihood ratio Λ_t = q_t/p₀,
  accumulated multiplicatively, is a nonnegative martingale with unit expectation under the null
  (an "e-process"). For a **simple null** (our M₀ uniform draws) the log-optimal ratio is the
  likelihood ratio; for a composite alternative use the **mixture method** — the prequential
  posterior-predictive density ratio, which equals a Bayes-factor process (§3.2.3). Ville's
  inequality: P(sup_t M_t ≥ 1/α) ≤ α — a sequential test whose type-I error control holds at every
  monitoring instant (continuous monitoring, optional stopping). Plug-in method (§3.2.1) must be
  smoothed to avoid assigning zero predictive probability. §5.5: testing *full exchangeability*
  admits no nontrivial evidence martingale in the data filtration (our null is simple uniformity,
  so predictive-likelihood e-processes are admissible). §6.4: the analysis plan (predictive prior)
  must be fixed a priori, never selected after seeing outcomes. §2.9–2.10: e-values combine by
  averaging (any dependence) or multiplication (independent/conditionally valid rounds).
- **Relevance:** **adopted, two layers.** v1 (`src/pcso_eprocess_monitor.py`): prequential
  predictive-likelihood evidence process with the single Dirichlet(100) prior. v2
  (`src/pcso_eprocess_monitor_v2.py`): (i) mixture-prior evidence process over the concentration
  grid {10,30,100,300,1000} (§3.2.2–3.2.4 REGROW robustness — removes the lab's documented
  single-concentration prior-sensitivity; strictly more informative: 6/55 full-history e 11.56 vs
  4.61, and 6/42 now leans uniform at e=0.50); (ii) Shin–Ramdas–Rinaldo e-detector (§5.7) for
  draw-mechanism drift (confirmation-set maxima 2.4–6.8 vs threshold 178.6 — no changepoint).
  No rejection of the uniform null at any monitoring instant in either layer; anytime-valid
  type-I control at α = 0.05/9 throughout. Jev: fits the gap (0.76), best improvement (0.99).
- **Key companion papers cited therein:** Wasserman/Ramdas/Balakrishnan universal inference
  (arXiv:1901.05710); Grünwald/De Heide/Koolen safe testing (RIPr); Waudby-Smith/Ramdas betting
  CS for bounded means; Vovk conformal test martingales; Ramdas et al. testing exchangeability
  (arXiv:2009.03167 e-process admissibility).

### A5. Testing-by-betting / e-process cluster (abstracts from search)
- Shekhar, Ramdas — *Nonparametric Two-Sample Testing by Betting* — https://arxiv.org/abs/2112.09162
- Vovk — *From supermartingales to randomness tests* — https://arxiv.org/abs/2308.13462
- Shafer, Vovk — *Test Martingales, Bayes Factors and p-Values* — https://arxiv.org/abs/0912.4269
- Vovk et al. — *Conformal e-testing* (testing exchangeability) — https://arxiv.org/abs/2006.02329
- **Relevance:** same family as A4; monitoring machinery, no draw-probability lift.

### A6. Exchangeability representation cluster (titles from search, not adopted)
- *Finite and infinite weighted exchangeable sequences* — https://arxiv.org/abs/2306.11584
- *Exchangeable Testing Against an Unknown Benchmark* — https://arxiv.org/abs/2608.04838
- *Exchangeability and randomness for infinite and finite sequences* — https://arxiv.org/abs/2512.22162
- *Bounded Difference Concentration for Infinitely Exchangeable …* — https://arxiv.org/abs/2606.17426

### A7. Online-learning prediction (rejected by jev, F_ml = 0.000)
- *On Finding Predictors for Arbitrary Families of Processes* — https://arxiv.org/abs/0912.4883
- *Sequential Neural Processes* — https://arxiv.org/abs/1906.10264 (and trajectory/attention ML
  variants surfaced by search). With T ≈ 192 per game and 4×10⁷ outcomes, regret theory (A1)
  and the lab backtest both put expected gain ≈ 0; already falsified in spirit by the backtest.

## B. Lottery-specific and popularity/EV classics (first-pass search)

### B1. [read] *Predicting Winning Lottery Numbers* (Compound-Dirichlet-Multinomial)
- **URL:** https://arxiv.org/pdf/2403.12836
- **Claim:** CDM statistical model to "predict" 6/5/pick-4/pick-3 numbers; a "3-strategy" claimed
  profitable for pick-3.
- **Assessment:** the CDM model is a smoothed frequency model of the same family as the lab's
  withdrawn first-pass predictor (Dirichlet-multinomial on counts omits the e₆ normalizer); no
  out-of-sample above-uniform validation is established; the lab's own backtest (hot/cold/
  overdue/Markov/filters, Holm min p 0.055) covers this class. Not adopted. The "profitable
  strategy" claim concerns payout sharing, which the lab handles via CSI (C), not draw prediction.

### B2. Stern, Cover — *Maximum Entropy and the Lottery* (pre-arXiv classic)
- **URL:** https://www.jstor.org/stable/2290073 · PDF: https://isl.stanford.edu/~cover/papers/paper91.pdf
- **Claim:** unpopular-number tickets can have expected return above cost when sales/carryovers
  are large; max-entropy approximates the purchased-ticket distribution from marginals.
- **Relevance:** payout-sharing optimization — **already implemented** in the picker (CSI q40
  cutoff, tickets C/D).

### B3. Cook, Clotfelter — *The Demand for Lotto: The Role of Conscious Selection*
- **URL:** https://www.jstor.org/stable/1392560 (see also lab kb card
  `docs/kb/conscious-selection-popularity.md`)
- **Relevance:** basis of the lab's CSI instrument (β = 0.5185, count ratio 1.68 [1.44,1.95]/SD).

### B4. *Distribution-dependent number preferences* (Cambridge, judgment & decision making)
- **URL:** https://www.cambridge.org/core/services/aop-cambridge-core/content/view/E2D78B93A9846A3783DD75B9952356C6
- **Relevance:** conscious-selection share varies by game/mechanism; supports within-game CSI
  standardization already used by the picker.

---

## Honest summary for the picker

1. **Draw-probability accuracy:** capped. A1 caps online gains at O(T⁻¹/²) regret vs class-best;
   A3 says the optimal exchangeable predictor is the Bayesian mixture the picker already runs;
   A2's frequent-outcome lift requires a fixed bias the BF evidence supports only weakly and
   prior-sensitively; the lab backtest falsifies the whole rule family after Holm. **No change to
   tickets A/B is justified.**
2. **Payout-sharing EV:** already handled (B2/B3, CSI).
3. **Adopted:** A4 — anytime-valid sequential monitor (`src/pcso_eprocess_monitor.py`): a
   prequential predictive-likelihood evidence process that closes the weekly-looks gap with
   Ville-valid type-I error control at α = 0.05/9. In the prediction pipeline this is the
   inference/self-correction layer: the earliest statistically valid detection of a departure from
   uniformity is exactly when the model-averaged predictor is justified in shifting weight toward
   M₁ — i.e., the improvement to the prediction system is a rigorous sequential detection layer,
   not a change to the ticket generator.
