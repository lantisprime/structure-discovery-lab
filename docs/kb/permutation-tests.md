# Permutation Tests

**Domain face**: statistical

**Statement**: Under H0 of exchangeability (the joint distribution of the data is invariant under permutations of the labels/pairing), any test statistic T has an exact null distribution obtained by recomputing T over the group of permutations. The Monte Carlo version with M random permutations gives p = (1 + #{T_pi >= T_obs}) / (M + 1), which is exactly valid for any M.

**Assumptions**: exchangeability under the null — for a correlation test between an outcome series and a covariate series, the null is that the pairing is arbitrary, i.e. shuffling one series against the other does not change the joint law. No distributional assumptions on either variable. Heterogeneity across strata (e.g., different games with different number ranges) must be removed first, otherwise pooling violates exchangeability.

**Null value under i.i.d. uniform**: permutation p-value is (sub-)uniform on (0,1); any correlation statistic centers at its permutation-null mean.

**Detects / blind to**: detects any association between the outcome statistic and the covariate that survives the chosen statistic (linear correlation detects monotone-linear links; rank or binned statistics widen this). Blind to associations orthogonal to the statistic, and cannot detect autocorrelation within a single series unless the permutation scheme is designed for it (e.g., block or cyclic-shift permutations).

**Finite-sample cautions**: p-value granularity is 1/(M+1) — 20,000 permutations gives ~7e-5 resolution and Monte Carlo s.e. sqrt(p(1-p)/20000). Pooling non-exchangeable strata creates spurious "associations" via Simpson-type confounding; the fix is within-stratum standardization (z-scoring within each game) or stratified permutations. Covariates with strong autocorrelation (lunar phase, solar indices) make naive permutations slightly liberal for time-trend-like alternatives; this biases toward false positives, so null results are conservative-safe.

**Reference summary**:
The permutation test, originated by R.A. Fisher (1935) and formalized by Pitman, replaces distributional assumptions with a symmetry assumption: if the null hypothesis is true, relabeling or re-pairing the observations should not matter, so the observed statistic can be referred to the empirical distribution of the statistic over all (or many random) relabelings. The result is an exact, assumption-free test whose only requirement is exchangeability under the null.

Permutation tests are the method of choice when the null mechanism cannot be simulated parametrically but a symmetry of it can be exploited. For correlation questions ("do lottery outcomes covary with moon phase / solar activity / geomagnetic Kp / tides?") the natural null symmetry is that the date-to-draw pairing is arbitrary, so shuffling the covariate series against the outcome series generates the null.

The main practical pitfall is hidden stratification: if several games with different ranges and draw schedules are pooled, raw outcome statistics are not exchangeable across games, and a permutation test on the pooled data tests the wrong null. Standardizing the outcome within each game (within-game z-scoring) before pooling restores exchangeability and removes the confound.

**Canonical references**:
- https://en.wikipedia.org/wiki/Permutation_test
- https://en.wikipedia.org/wiki/Exchangeable_random_variables
- Good, *Permutation, Parametric and Bootstrap Tests of Hypotheses*, Springer.
- Ernst, "Permutation Methods: A Basis for Exact Inference", Statistical Science 19 (2004).

**Use in this project**: Assumption-free correlation testing of draw statistics against external covariates. Within-game z-scoring was introduced to fix a pooling/exchangeability problem; 20,000 permutations per test. All covariates tested (moon phase, sun, geomagnetic Kp index, tides) were null with p >= 0.18.
