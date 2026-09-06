**1. Likelihood and posterior predictive**

Let \(S_t\subset\{1,\ldots,P\}\), \(|S_t|=6\), \(X_{ti}=1\{i\in S_t\}\), and \(c_i=\sum_tX_{ti}\).

Unequal weights and sampling without replacement do **not** uniquely specify a distribution. Inclusion probabilities alone do not determine six-set probabilities.

The computations below assume the **product-weight model**
\[
e_6(w)=\sum_{|A|=6}\prod_{i\in A}w_i,\qquad
f_w(S)=\frac{\prod_{i\in S}w_i}{e_6(w)}.
\]
This is conditional Poisson/rejective sampling. Sequential weighted drawing gives a different distribution. [Sampling-model distinction](https://www.agner.org/random/theory/nchyp1.pdf).

Its likelihood, inclusion probabilities, posterior, and predictive distribution are
\[
L(w;D)=\frac{\prod_iw_i^{c_i}}{e_6(w)^T},
\qquad
\pi_i(w)=\frac{w_i e_5(w_{-i})}{e_6(w)},
\qquad \sum_i\pi_i=6,
\]
\[
p(w\mid D,a)\propto
e_6(w)^{-T}\prod_iw_i^{c_i+a-1},
\quad w\sim\operatorname{Dirichlet}(a,\ldots,a),
\]
\[
\boxed{\Pr(S_{\rm next}=S\mid D)
=\mathbb E_{w\mid D}\!\left[\frac{\prod_{i\in S}w_i}{e_6(w)}\right]}.
\]

For sequential drawing, with \(W=\sum_iw_i\),
\[
f_w^{\rm seq}(S)=
\sum_{\sigma\in\operatorname{Perm}(S)}
\prod_{j=1}^{6}
\frac{w_{\sigma_j}}{W-\sum_{\ell<j}w_{\sigma_\ell}}.
\]
Its likelihood is \(\prod_t f_w^{\rm seq}(S_t)\); ball counts generally cease to be sufficient.

**`predict.py`: REJECT its likelihood and predictive multiplier as exact without-replacement inference.**

| Step | Error | Correction |
|---|---|---|
| Multinomial likelihood | Omits \(e_6(w)^{-T}\) | \(L(w;D)\) above |
| Dirichlet posterior | Conjugacy does not survive the omitted factor | Non-Dirichlet posterior above |
| Inclusion probability \(6w_i\) | Generally incorrect | \(w_i e_5(w_{-i})/e_6(w)\) |
| Product of posterior means | Omits posterior dependence and normalization | Integrate \(f_w(S)\) |
| Empirical-Bayes “BF” | Alternative concentration selected using the same data | Fix a proper prior or integrate a proper hyperprior |

Writing \(\bar w=\mathbb E[w\mid D]\), the script’s multiplier and even the corrected **plug-in** multiplier differ:
\[
M_{\rm script}=P^6\prod_{i\in S}\bar w_i,\qquad
R_{\rm plug}=\binom P6\frac{\prod_{i\in S}\bar w_i}{e_6(\bar w)},
\]
\[
\frac{M_{\rm script}}{R_{\rm plug}}
=\frac{P^6e_6(\bar w)}{\binom P6}\le1.
\]
The required multiplier is instead
\[
\boxed{R_D(S)=\binom P6\,\mathbb E[f_w(S)\mid D]}.
\]

Even under the script’s multinomial posterior, with \(b_i=a+c_i\), \(B=\sum_i b_i\),
\[
\mathbb E\!\left[\prod_{i\in S}w_i\mid D\right]
=\frac{\prod_{i\in S}b_i}{B(B+1)\cdots(B+5)}
\ne\prod_{i\in S}\mathbb E[w_i\mid D].
\]

**Numerical specification:** product-weight model; \(a=100\), fixed independently of the observations. Sensitivity: \(a=10,1000\). “10%” means relative deviation. Intervals are 95%.

---

**2. Maximum posterior-predictive six-sets**

\[
S^*=\arg\max_{|S|=6}\Pr(S_{\rm next}=S\mid D).
\]
For this symmetric prior, exchange symmetry implies that \(S^*\) contains the six largest counts. Count ties give equally optimal alternatives.

| Game | Draws | \(S^*\) | Predictive probability | Uniform \(p_0=1/\binom P6\) | Ratio; 95% CrI |
|---|---:|---|---:|---:|---:|
| 6/42 | 192 | 3, 6, 12, 36, 39, 41 | \(2.828\times10^{-7}\) | \(1.906292\times10^{-7}\) | 1.483 [0.987, 2.126] |
| 6/45 | 193 | 4, 5, 8, 24, 25, 27 | \(1.845\times10^{-7}\) | \(1.227738\times10^{-7}\) | 1.503 [0.994, 2.168] |
| 6/49 | 192 | 8, 14, 16, 26, 36, 44 | \(1.115\times10^{-7}\) | \(7.151124\times10^{-8}\) | 1.559 [1.028, 2.259] |
| 6/55 | 193 | 5, 42, 44, 45, 48, 50 | \(5.661\times10^{-8}\) | \(3.449504\times10^{-8}\) | 1.641 [1.076, 2.382] |
| 6/58 | 192 | 12, 15, 17, 43, 50, 57 | \(3.716\times10^{-8}\) | \(2.470639\times10^{-8}\) | 1.504 [0.979, 2.200] |

6/42: replacing 6 with 18 or 35 gives another optimum.

The intervals describe the latent multiplier
\[
R_w(S^*)=\binom P6f_w(S^*),
\]
not uncertainty in a numerically integrated posterior mean. Probability intervals equal these endpoints multiplied by \(p_0\). Under the uniform model, \(p_0\) has no parameter uncertainty.

---

**3. Bayes factors and probability of a material inclusion deviation**

Let \(M_0\) be uniform and \(M_1(a)\) the specified unequal-weight model:
\[
BF_{01}(a)=\frac{\binom P6^{-T}}
{\int L(w;D)\operatorname{Dir}(w;a)\,dw}.
\]

For reproducible importance integration, define
\[
z(w)=\frac{e_6(Pw)}{\binom P6},\qquad
A_a=P^{6T}\frac{\Gamma(Pa)}{\Gamma(Pa+6T)}
\prod_i\frac{\Gamma(a+c_i)}{\Gamma(a)}.
\]
Then
\[
BF_{10}(a)=A_a\,
\mathbb E_{\operatorname{Dir}(a+c)}[z(w)^{-T}].
\]

Define
\[
E_{10}=\left\{\max_i
\left|\frac{\pi_i(w)}{6/P}-1\right|>0.10\right\}.
\]

| Game | \(BF_{01}(10)\) | \(BF_{01}(100)\) | \(BF_{01}(1000)\) | \(\Pr(E_{10}\mid D,M_1(100))\) | \(\Pr(E_{10}\mid D)\), equal model odds |
|---|---:|---:|---:|---:|---:|
| 6/42 | 6,995 | 0.945 | 0.947 | 0.999993 | 0.514 |
| 6/45 | 1,237 | 0.591 | 0.898 | 0.999997 | 0.628 |
| 6/49 | 3,521 | 0.691 | 0.914 | \(\approx1\) | 0.591 |
| 6/55 | 46.01 | 0.221 | 0.800 | \(\approx1\) | 0.819 |
| 6/58 | 558.1 | 0.488 | 0.887 | \(\approx1\) | 0.672 |

Here
\[
\Pr(E_{10}\mid D)
=\frac{\Pr(E_{10}\mid D,M_1)}{1+BF_{01}}
\]
assumes \(\Pr(M_0)=\Pr(M_1)=1/2\). Conditional probability near one under \(M_1\) is **not** posterior evidence that \(M_1\) is true.

Prior sensitivity is substantial:
\[
\Pr(E_{10}\mid D,M_1(1000))
=(0.0122,\ 0.0141,\ 0.0176,\ 0.0253,\ 0.0291).
\]

Numerics: 200,000 importance samples/game at \(a=100\); effective sample sizes 195,741–198,276; relative BF Monte Carlo SE \(\le0.00033\). “\(\approx1\)” means no complementary event observed in that run, not mathematical certainty.

---

**4. Serial dependence**

For ball \(i\), let \(n_{i,ab}\) count transitions \(X_{t-1,i}=a\to X_{ti}=b\). The ballwise order-1 statistic is
\[
G_{\rm ball}^2
=2\sum_{i,a,b}n_{i,ab}
\log\frac{n_{i,ab}(T-1)}
{n_{i,a+}n_{i,+b}}.
\]

This is a **composite** likelihood-ratio statistic: the \(P\) indicators are dependent because each draw contains exactly six balls. A naive \(\chi_P^2\) calibration is invalid. The table uses 19,999 permutations of **whole draws within each game**, preserving ball frequencies and within-draw dependence.

A proper joint order-1 model with a common persistence parameter is
\[
\Pr_\beta(S_t\mid S_{t-1})
=\frac{\exp(\beta|S_t\cap S_{t-1}|)}{Z_P(\beta)},
\]
\[
Z_P(\beta)=\sum_{k=0}^{6}
\binom6k\binom{P-6}{6-k}e^{\beta k}.
\]
Its null \(\beta=0\) specifies uniform independent draws. The reported joint p-value is exact, using convolution of the null hypergeometric overlap distribution.

| Game | \(G_{\rm ball}^2\) | Whole-draw permutation p | Joint overlap LR | Exact joint p |
|---|---:|---:|---:|---:|
| 6/42 | 47.821 | 0.37110 | 0.225 | 0.65234 |
| 6/45 | 54.710 | 0.27665 | 2.223 | 0.14058 |
| 6/49 | 60.980 | 0.25700 | 4.105 | 0.04540 |
| 6/55 | 80.340 | 0.05680 | 3.979 | 0.04761 |
| 6/58 | 70.481 | 0.31680 | 1.955 | 0.17084 |

The permutation test isolates departure from exchangeable draws while permitting unequal marginal frequencies. The joint overlap test additionally assumes uniform marginals under its null.

\[
\alpha_{\text{Bonferroni},5}=0.01:
\qquad \text{no rejection in either five-game family}.
\]

These test own-ball persistence and common overlap persistence; they do not exhaust all cross-ball transition alternatives.

---

**5. `csi_popularity.py`**

| Step | Disposition | Mathematical assessment |
|---|---|---|
| Within-game z-scores | **ACCEPT** | Removes game-specific score location and scale; coefficient is per within-game SD |
| Within-game ranks | **ACCEPT-WITH-MOD** | Valid score; ties prevent identical rank distributions across games |
| Stratified permutation | **ACCEPT-WITH-MOD** | Exact under within-game permutation invariance; changing exposure alone is insufficient to invalidate it if CSI remains exchangeable and independent of the entire outcome vector |
| Poisson coefficient estimator | **ACCEPT-WITH-MOD** | Consistent as Poisson pseudo-MLE when the conditional mean is correct; Poisson variance is unnecessary |
| Poisson information-matrix SE | **REJECT** as robust inference | Replace with sandwich covariance |
| Jackpot as sales proxy | **ACCEPT-WITH-MOD** | Permissible count-prediction covariate; does not identify popularity per bet |
| Pooled tied “tertiles” | **ACCEPT-WITH-MOD** | Unequal game composition can confound raw pooled contrasts; standardize game/exposure composition |
| Šidák correction | **REJECT** as generally guaranteed FWER control | Use Holm or Bonferroni |
| Observed-slope power | **DEFER** | Model-conditional post-hoc power, not independent validation |

The fitted count model is
\[
\mu_t=\mathbb E[Y_t\mid X_t]
=\exp(\alpha_{g(t)}+\beta z_{{\rm CSI},t}
+\gamma z_{\log J,t}).
\]
The corrected covariance is
\[
\widehat V_{\rm HC1}
=\frac{n}{n-p}A^{-1}
\left[\sum_t x_tx_t^\top(Y_t-\hat\mu_t)^2\right]A^{-1},
\quad
A=\sum_t\hat\mu_tx_tx_t^\top.
\]

| Quantity | Computed value |
|---|---:|
| Draws / draws with winners / winning bets | 984 / 77 / 94 |
| \(T_1\), standardized CSI mean difference | 0.735656 |
| \(T_1\), stratified permutation p | 0.000050 |
| \(T_2\), rank correlation | 0.162076 |
| \(T_2\), stratified permutation p | 0.000100 |
| \(\hat\beta_{\rm CSI}\) | 0.518506 |
| Poisson SE / HC1 SE / within-game HAC(8) SE | 0.075010 / 0.077124 / 0.077866 |
| Pearson dispersion | 2.226282 |
| CSI count ratio per SD, HC1 95% CI | **1.680 [1.444, 1.954]** |
| \(\hat\gamma_{\log J}\), HC1 SE | 0.327720, 0.192016 |

For popularity **per purchased bet**, the appropriate mean specification requires exposure:
\[
\mathbb E[Y_t\mid S_t,N_t]
=N_tq_t(S_t),\qquad
\log\mu_t=\log N_t+\alpha_g+\beta z_t+\cdots.
\]
The supplied CSV lacks \(N_t\). Jackpot and game effects do not identify \(q_t(S)\).

For standardized high/low comparisons, use common game weights and exposure:
\[
\frac{\sum_g\omega_g\,\mathbb E[\hat\mu(g,z,J_g^*)\mid H,g]}
{\sum_g\omega_g\,\mathbb E[\hat\mu(g,z,J_g^*)\mid L,g]}.
\]
The script’s \(2.844\) multiplier is an exponential contrast between pooled mean z-scores, not generally this standardized count ratio.

---

**6. `pcso_strategy_backtest.py`**

Let \(q_{s,t,i}\) be ball \(i\)’s inclusion fraction across strategy \(s\)’s generated tickets, and
\[
a_{s,t,i}=q_{s,t,i}-q_{0,t,i},\qquad
D_{s,t}=\sum_i a_{s,t,i}X_{ti},\qquad \sum_i a_{s,t,i}=0.
\]

Under uniform independent draws and tickets chosen before the target draw,
\[
\mathbb E[D_{s,t}\mid\mathcal F_{t-1},q]=0,
\]
\[
\boxed{\operatorname{Var}_0(D_{s,t}\mid\mathcal F_{t-1},q)
=\frac{6(P_t-6)}{P_t(P_t-1)}
\sum_i a_{s,t,i}^2}.
\]

**Sign flips: REJECT as an exact null.**
\[
\mathbb E[D_t\mid\mathcal F_{t-1}]=0
\not\Rightarrow
(D_1,\ldots,D_T)\overset d=
(\epsilon_1D_1,\ldots,\epsilon_TD_T).
\]
Neither symmetry nor independent sign invariance follows from equal expected matches. Adaptive histories also couple subsequent differences.

**Replicates: ACCEPT draw-level aggregation.** For independent randomized replicates conditional on a draw,
\[
\operatorname{Var}(\bar K_R)
=\operatorname{Var}_D\{\mathbb E[K\mid D]\}
+\frac1R\mathbb E_D\{\operatorname{Var}(K\mid D)\}.
\]
Increasing \(R\) removes simulation noise, not uncertainty from the finite draw sample. Two tickets within a replicate also share the same draw.

A corrected asymptotic null statistic is
\[
Z_s=\frac{\sum_tD_{s,t}}
{\sqrt{\sum_t\operatorname{Var}_0(D_{s,t}\mid\mathcal F_{t-1},q)}}.
\]
An exact simulation calibration must regenerate uniform draw histories and replay adaptive strategies.

Reconstructed results, \(T=834\):

| Strategy | Historical mean difference; HAC(8) 95% CI | Conditional-null \(Z\) | Approximate p | Holm p |
|---|---:|---:|---:|---:|
| v1 filters | 0.00401 [0.00101, 0.00701] | 2.663 | 0.00774 | 0.05421 |
| v2 CSI | 0.00809 [0.00134, 0.01484] | 2.464 | 0.01374 | 0.06870 |
| Hot | 0.01196 [−0.01907, 0.04299] | 0.743 | 0.45729 | 1 |
| Cold | −0.04079 [−0.07036, −0.01122] | −2.541 | 0.01105 | 0.06630 |
| Overdue | −0.00096 [−0.03278, 0.03086] | −0.057 | 0.95472 | 1 |
| Repeat | −0.00353 [−0.02773, 0.02067] | −0.310 | 0.75690 | 1 |
| Markov proxy | 0.00704 [−0.02788, 0.04197] | 0.435 | 0.66366 | 1 |

**Multiplicity: REJECT unrestricted Šidák justification and post-hoc equivalence merging.**

\[
\alpha_{\rm Bonferroni}=0.05/7=0.007143.
\]
Shared draws and the shared baseline make the seven tests dependent. Holm remains valid for valid constituent p-values.

The stored correlations are
\[
\rho_{\rm v1,v2}=0.402,\quad
\rho_{\rm v1,cold}=0.068,\quad
\rho_{\rm v2,cold}=-0.022.
\]
They do not establish one equivalent hypothesis. A nonsignificant omnibus frequency test does not erase a directional result.

Changing only multiplicity, while retaining the original sign-flip p-values, gives v1 Holm p \(=7(0.0061)=0.0427\). The revised value \(0.0542\) also changes the null calibration.

---

**7. Next-draw edge: quantities, values, uncertainty**

For a randomized single-ticket rule \(Q_s\), define
\[
R_s(w)=\binom P6\sum_SQ_s(S)f_w(S),
\qquad
\Delta_s(w)=\sum_iq_{s,i}\pi_i(w)-\frac{36}{P}.
\]
\(R_s\) measures jackpot-probability ratio; \(\Delta_s\) measures expected additional matches per ticket. Neither is a payout-return ratio.

Under \(M_0\), every valid history-based rule has
\[
\boxed{R_s=1,\quad \Delta_s=0}
\]
exactly. Two distinct tickets have jackpot probability \(2/\binom P6\).

The following posterior summaries condition on the static-weight \(M_1(100)\). Strategy histories use the official data through each game’s latest draw; weight fitting uses the canonical 962 draws. These do not estimate a changing “hotness” or Markov mechanism.

**Single-ticket rules in `predict.py`: \(R_s\), posterior mean [95% CrI].**

| Rule | 6/42 | 6/45 | 6/49 | 6/55 | 6/58 |
|---|---:|---:|---:|---:|---:|
| Top six | 1.483 [.987, 2.126] | 1.503 [.994, 2.168] | 1.559 [1.028, 2.259] | 1.641 [1.076, 2.382] | 1.504 [.979, 2.200] |
| Bottom six | .673 [.432, .990] | .654 [.417, .968] | .694 [.441, 1.032] | .674 [.426, 1.007] | .650 [.408, .976] |
| Hot six, last 50 | 1.300 [.859, 1.874] | 1.077 [.704, 1.570] | 1.363 [.893, 1.981] | 1.217 [.788, 1.786] | 1.168 [.751, 1.716] |
| Last draw’s six | 1.201 [.789, 1.735] | .883 [.571, 1.297] | 1.156 [.753, 1.689] | .992 [.637, 1.465] | 1.092 [.700, 1.609] |

**Two-ticket strategy rules: \(1000\Delta_s\), posterior mean [95% CrI].**

| Rule | 6/42 | 6/45 | 6/49 | 6/55 | 6/58 |
|---|---:|---:|---:|---:|---:|
| Uniform disjoint | 0 [0, 0] | 0 [0, 0] | 0 [0, 0] | 0 [0, 0] | 0 [0, 0] |
| v1 filters | .39 [−1.34, 2.12] | .00 [−1.08, 1.09] | −.13 [−.75, .48] | .15 [−.14, .44] | .05 [−.16, .26] |
| v2 CSI | 1.12 [−5.17, 7.44] | .50 [−4.86, 5.88] | −.55 [−5.35, 4.25] | 1.91 [−2.53, 6.34] | 1.32 [−3.00, 5.62] |
| Hot | 18.98 [−10.51, 48.58] | 11.69 [−15.78, 39.47] | 23.38 [−4.79, 51.89] | 19.74 [−7.52, 47.35] | 13.29 [−10.96, 37.80] |
| Cold | −25.03 [−55.44, 5.51] | −15.18 [−44.50, 14.40] | −19.55 [−45.15, 6.32] | −14.86 [−40.38, 11.01] | −18.15 [−42.72, 6.56] |
| Overdue | −6.71 [−37.44, 24.12] | .51 [−30.29, 31.51] | −4.54 [−33.62, 24.92] | 2.13 [−24.99, 29.55] | −12.97 [−38.92, 13.27] |
| Repeat | 9.85 [−11.10, 30.91] | −5.90 [−25.72, 14.39] | 6.98 [−12.12, 26.61] | −.11 [−17.95, 18.12] | 3.82 [−13.56, 21.50] |
| Markov proxy | 35.74 [3.37, 68.38] | 29.70 [−.18, 59.79] | 24.07 [−4.11, 52.74] | 24.72 [−1.37, 51.00] | 24.98 [−1.30, 51.57] |

Picker-rule integration used one million candidate pairs/game, with randomized ticket splitting. Additional Monte Carlo SE of the estimated mean edge was below \(0.000020\) matches/ticket.

Model averaging changes the means to
\[
R_{s,\rm mix}=1+\frac{R_{s,M_1}-1}{1+BF_{01}},
\qquad
\Delta_{s,\rm mix}=\frac{\Delta_{s,M_1}}{1+BF_{01}},
\]
and adds posterior point mass at \(R=1\) or \(\Delta=0\). Intervals above exclude this model uncertainty.

**CSI: predicted winning-bet count relative to uniform ticket selection**, conditional on the fitted mean model and equal game/exposure:
\[
C_{s,g}=
\frac{\mathbb E_{Q_s}e^{\beta z_{\rm CSI}}}
{\mathbb E_{U}e^{\beta z_{\rm CSI}}}.
\]

| Picker | 6/42 | 6/45 | 6/49 | 6/55 | 6/58 |
|---|---:|---:|---:|---:|---:|
| v1: \(C_{s,g}\), HC1 slope-based 95% CI | .779 [.692, .857] | .831 [.757, .894] | .901 [.854, .939] | .909 [.854, .949] | .933 [.891, .962] |
| v2: \(C_{s,g}\), HC1 slope-based 95% CI | .560 [.438, .689] | .572 [.448, .700] | .655 [.545, .763] | .532 [.389, .676] | .547 [.407, .688] |

These intervals cover slope uncertainty only. They are model-based count contrasts, not calibrated jackpot-return gains. The latter requires
\[
V_s=\mathbb E_{S\sim Q_s}
\left[f_w(S)\,J\,\mathbb E\!\left[\frac1{1+W(S)}\right]\right].
\]
Mean winner counts alone do not determine \(\mathbb E[1/(1+W)]\).

**Monitoring quantities in `pcso_monitoring_run.py` / `pcso_weekly_update.py`:**

| Instrument | Computed quantity and uncertainty | Next-draw edge |
|---|---|---|
| Per-game frequency \(\chi^2\) | MC p: .06619, .49805, .04570, .37576, .10689 | No prediction rule; calibrated static alternative is §2 |
| Moon altitude | \(r=-.01538\), stratified bootstrap CI [−.16172, .13918]; stratified p=.83760 | Not identified by correlation |
| Moon illumination | \(r=.00479\), CI [−.13103, .14791]; stratified p=.95005 | Not identified by correlation |
| Kp | Missing confirmation covariates | Not computable |
| 6/55 ball 45 | Confirmation \(2/37\), binomial p=.42745 | For a ticket containing 45 plus five uniformly selected others: \(R=\pi_{45}/(6/55)=1.121\) [.958, 1.293], under \(M_1(100)\) |

Monitoring assessment: **ACCEPT** uniform six-set Monte Carlo frequency calibration and within-look Bonferroni \(m=9\); **ACCEPT-WITH-MOD** lunar permutations—permute within game instead of globally. Repeated cumulative looks require separate sequential error control, as the scripts acknowledge.

Verification: 962 shared draw records, zero cross-file discrepancies; normalization and marginal identities checked by exhaustive small-pool enumeration; CSI `--verify` passed; reconstructed backtest means matched stored results; **files edited: 0**.