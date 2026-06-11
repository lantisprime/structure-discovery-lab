# Power Laws: Clauset–Shalizi–Newman, Zipf, Taylor, Benford

**Domain face**: cross-sectional/physical

**Statement**:
- Power law: P(x) ~ x^{-alpha} for x >= x_min. CSN procedure: estimate alpha by MLE (continuous: alpha-hat = 1 + n [sum ln(x_i/x_min)]^{-1}); choose x_min minimizing the Kolmogorov–Smirnov distance; assess goodness-of-fit by KS bootstrap p; compare against alternatives (exponential, lognormal, geometric, stretched exponential) via the Vuong likelihood-ratio test with normalized statistic z.
- Zipf's law: rank-frequency f(r) ~ r^{-s}; for near-uniform count data the fitted Zipf slope is a deterministic transform of frequency dispersion — algebraically the same information as the chi-square uniformity statistic.
- Taylor's law: variance of counts scales with mean as Var = a * Mean^b; b = 1 for Poisson-like systems, b -> 2 for strongly clustered ones.
- Benford's law: leading digit d occurs with probability log10(1 + 1/d) — valid only for data spanning several orders of magnitude with scale-invariant generation; bounded uniform integers instead follow an exactly computable digit law derived from the uniform distribution on {1..C}.
- Coupon collector: expected draws to see all C numbers = (C/6) * H_C-ish generalization for 6-per-draw sampling; with known mean and variance for the waiting time.

**Assumptions**: CSN — i.i.d. tail samples, enough tail data (n_tail >~ 50); Vuong — non-nested model pair, finite variance of log-likelihood ratio. Benford — multiplicative/scale-spanning data (explicitly violated by lottery numbers). Taylor — meaningful mean-variance ensemble across units/windows.

**Null value under i.i.d. uniform**: gap/waiting-time distributions are geometric (discrete exponential), NOT power-law — Vuong should decisively favor geometric; Zipf slope ~ 0 (near-uniform frequencies); Taylor b ~ 1 modified by the without-replacement constraint (project measured b ~ 0.9); Benford strongly violated, while the exact uniform-derived first-digit law (P(d) = #{n in 1..C: leading digit d}/C) fits; Lévy-flight tails (alpha < 2 stable) excluded; coupon-collector waiting times within their analytic CI.

**Detects / blind to**: detects heavy-tailed mechanisms (SOC avalanches, Lévy flights, preferential attachment) in gaps, streaks, and count dispersion; detects digit anomalies symptomatic of fabricated or post-processed data. Blind to light-tailed structure and to dependence that leaves marginal tails geometric.

**Finite-sample cautions**: log-log least-squares slopes are biased and overstate power-law evidence — MLE plus Vuong is mandatory (the core CSN message); small tails make lognormal and power law nearly indistinguishable; naive Benford application to bounded support produces spectacular but meaningless rejections (the rejection is of Benford's applicability, not of fairness) — the correct null is the digit law induced by uniform-on-{1..C}; Zipf slope must not be counted as a test separate from chi-square (equivalence-class accounting, see multiple-comparisons card).

**Reference summary** (distilled from fetched source — https://arxiv.org/abs/0706.1062, Clauset, Shalizi & Newman, SIAM Review 51:661-703, 2009):
Power-law distributions occur widely, but their detection is complicated by large fluctuations in the distribution tail — precisely the region of interest — and by the difficulty of identifying the range over which power-law behavior holds. Commonly used methods, notably least-squares fitting of log-log histograms, "can produce substantially inaccurate estimates of parameters," and even when they return accurate answers they give no indication of whether the data obey a power law at all.

CSN's principled framework combines three components: maximum-likelihood estimation of the exponent, goodness-of-fit tests based on the Kolmogorov–Smirnov statistic (also used to select x_min), and likelihood-ratio comparisons (Vuong's test) against competing heavy- and light-tailed alternatives. Applied to twenty-four real-world datasets conjectured to be power laws, they found some conjectures consistent with the data while in others the power law is firmly ruled out — establishing the now-standard discipline that a power-law claim requires surviving both an absolute fit test and relative comparisons.

This project applied the full CSN pipeline to lottery gap/streak/count statistics. The decisive result: inter-occurrence gaps favored the geometric distribution over a power law at Vuong z = -35.3 — about as conclusive as model comparison gets — excluding SOC-style and Lévy-flight mechanisms at the level of tails.

**Canonical references**:
- Clauset, Shalizi & Newman, "Power-law distributions in empirical data", https://arxiv.org/abs/0706.1062 (SIAM Review 2009; code at https://aaronclauset.github.io/powerlaws/)
- https://en.wikipedia.org/wiki/Zipf%27s_law
- https://en.wikipedia.org/wiki/Taylor%27s_law
- https://en.wikipedia.org/wiki/Benford%27s_law
- https://en.wikipedia.org/wiki/Coupon_collector%27s_problem

**Use in this project**: CSN MLE + Vuong test: gaps are decisively geometric (z = -35.3), not power-law. Zipf slope shown to be chi-square in disguise (one equivalence class). Taylor's law b ~ 0.9 (without-replacement-consistent). Naive Benford rejected at chi2 = 1312 while the exact uniform-derived digit law fits at chi2 = 9.3 — a worked example of testing the right null. Lévy flights excluded; coupon-collector waiting times within CI. Script: powerlaw_sweep.py.
