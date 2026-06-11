# Scan Statistics & the Look-Elsewhere Effect

**Domain face**: statistical

**Statement**: A scan statistic is the maximum of a local test statistic over a family of windows: S = max over windows w of T(w) (e.g., max windowed z-score over all numbers, window lengths, and games). Its null distribution is NOT that of a single T(w); it must be calibrated against the distribution of the maximum, typically by Monte Carlo: p_global = P_H0( max_w T(w) >= S_obs ). The discrepancy between the naive (local) p-value of the best window and the global p-value is the look-elsewhere effect.

**Assumptions**: the null mechanism over the whole search space can be simulated (or bounded analytically, e.g., Naus approximations); the search family (all windows actually examined, including those examined implicitly) is fully enumerated in the null simulation. Kulldorff's spatial scan additionally uses a likelihood-ratio form T(w) for window w vs. outside.

**Null value under i.i.d. uniform**: the global maximum of windowed z-scores is large by chance: with hundreds of (number, window, game) combinations, max z of 3+ is routine. The global p-value of the observed maximum is uniform on (0,1).

**Detects / blind to**: detects localized clusters — a number running hot in a specific era, a temporal burst — at unknown location and scale, with correct multiplicity control. Blind to diffuse, non-localized departures (spread weakly over everything) and to alternatives outside the window family scanned.

**Finite-sample cautions**: windows overlap, so local statistics are strongly correlated; Bonferroni over windows is very conservative while ignoring multiplicity is grossly anti-conservative — Monte Carlo over the exact search procedure is the calibrated middle. Walther & Perry (2022) show asymptotic optimality results are too imprecise to guide practice and that scan statistics need finite-sample calibration, with scale-dependent critical values trading power between short and long signals.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Scan_statistic):
A scan statistic, or window statistic, addresses clustering of randomly positioned points: the canonical problems are the largest cluster of points in a moving window of fixed length, or the longest success run seen by a sliding window. Joseph Naus first published on the problem in the 1960s and is called the "father of the scan statistic"; the results are applied in epidemiology, public health, and astronomy to find unusual clusters of events.

Martin Kulldorff extended the method in 1997 to multidimensional settings and *varying* window sizes — scanning over both location and scale with a likelihood-ratio statistic and Monte Carlo calibration of the maximum — in what became the most cited article in *Communications in Statistics – Theory and Methods*, and the basis of the SaTScan software. The key idea this project borrows is exactly Kulldorff's: report the maximum local statistic, but compute its p-value from the null distribution of the maximum over the entire search.

Recent work (Walther & Perry, JRSS-B 2022) shows that asymptotically optimal calibrations of the scan can lose substantial finite-sample power for short signals, and proposes finite-sample calibration criteria — reinforcing that the null distribution of the scan maximum should be obtained by simulation matched to the actual data size and search family, which is what was done here.

**Canonical references**:
- https://en.wikipedia.org/wiki/Scan_statistic
- Kulldorff, "A spatial scan statistic", Comm. Statist. Theory Methods 26 (1997), http://www.satscan.org/papers/k-cstm1997.pdf
- https://en.wikipedia.org/wiki/Look-elsewhere_effect
- Glaz, Naus & Wallenstein, *Scan Statistics*, Springer (2001).

**Use in this project**: Kulldorff-style maximum windowed z-score scanned over all numbers, all window lengths, and all games, calibrated by Monte Carlo over the full search. This resolved the 6/55 number-45 anomaly: the naive local p = 0.001 became global p = 0.148 once the look-elsewhere effect was accounted for — not significant. Script: explore_batch2.py.
