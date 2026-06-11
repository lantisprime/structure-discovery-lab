# Hurst Exponent & Rescaled Range (R/S) Analysis

**Domain face**: dynamical

**Statement**: For a time series, the rescaled range over span n is R(n)/S(n), where R(n) is the range of the cumulative mean-adjusted deviations and S(n) their standard deviation. The Hurst exponent H is defined by the asymptotic scaling E[R(n)/S(n)] = C * n^H as n -> infinity. H = 0.5: short memory (autocorrelations decay at least exponentially); 0.5 < H < 1: persistent long-range positive autocorrelation (power-law decay); 0 < H < 0.5: anti-persistent switching. For self-similar series, fractal dimension D = 2 - H.

**Assumptions**: stationary increments; the scaling regime must actually be reached within the available spans; estimation by fitting log(R/S) vs log(n) assumes the power law holds across the fitted span range.

**Null value under i.i.d. uniform**: asymptotically H = 0.5. But the finite-n expectation E[R(n)/S(n)] for white noise deviates substantially from C*n^0.5 at small n (Anis–Lloyd exact formula involving the gamma function), so the raw log-log slope on a short series sits well above 0.5 under pure i.i.d. noise.

**Detects / blind to**: detects long-range dependence — slowly (power-law) decaying autocorrelations, fractional-Brownian-motion-like persistence, the "Joseph effect." Blind to short-memory structure (an order-1 Markov chain with fast mixing still gives H = 0.5 asymptotically) and to dependence that leaves second moments untouched.

**Finite-sample cautions**: THE key caution: the R/S estimator is biased upward on short series — raw H-hat values of 0.56–0.70 are entirely consistent with i.i.d. data at the series lengths in this project, exactly matching the simulated i.i.d. null. The Anis–Lloyd correction (regressing log[R/S - E_white-noise(R/S)] style adjustments, slope added to 0.5) and Weron's bootstrap confidence intervals exist precisely because of this; subseries shorter than ~50 points should be excluded as they inflate variance. Calibration against a simulated i.i.d. null of the same length and span grid is mandatory before interpreting any H-hat > 0.5.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Hurst_exponent):
The Hurst exponent measures the long-term memory of a time series via the rate at which autocorrelations decay with lag. It originated in hydrology: Harold Edwin Hurst studied Nile river levels to size reservoirs against long droughts and floods, and Mandelbrot later connected the exponent to fractal geometry and self-similar processes (fBm). H in (0.5, 1) means persistence — high values tend to follow high values, with autocorrelation decaying as a power law slower than exponential; H in (0, 0.5) means anti-persistent switching; H = 0.5 means short memory with quickly decaying autocorrelations.

The classical estimator is rescaled-range (R/S) analysis: divide the series into non-overlapping blocks of length n, compute for each block the range of cumulative mean-adjusted deviations divided by the block standard deviation, average, and fit the power law E[R(n)/S(n)] = C n^H by the slope of log(R/S) against log(n). Alternatives include detrended fluctuation analysis (DFA), periodogram regression, aggregated variances, local Whittle, and wavelet estimators.

Critically, the Wikipedia treatment itself flags that this slope-fitting approach "is known to produce biased estimates," with significant deviation from the 0.5 slope at small n. Anis and Lloyd (1976) derived the exact expected white-noise values of the R/S statistic (a gamma-function expression), giving the Anis–Lloyd corrected estimator (0.5 plus the slope of the deviation from the white-noise expectation), and Weron (2002) provided bootstrap-based finite-sample confidence intervals for both corrected R/S and DFA. No asymptotic distribution theory exists for most Hurst estimators, so simulation-based calibration is the standard of practice.

**Canonical references**:
- https://en.wikipedia.org/wiki/Hurst_exponent
- https://en.wikipedia.org/wiki/Rescaled_range
- Anis & Lloyd, "The expected value of the adjusted rescaled Hurst range of independent normal summands", Biometrika 63 (1976).
- Weron, "Estimating long-range dependence: finite sample properties and confidence intervals", Physica A 312 (2002), https://arxiv.org/abs/cond-mat/0103510

**Use in this project**: Long-range memory instrument within the SOC battery. CAUTION confirmed empirically: the R/S estimator is biased upward on short series — raw H-hat of 0.56–0.70 on the lottery statistics matched the simulated i.i.d. null exactly, so no long-range memory was found. Calibration against a same-length i.i.d. null is mandatory for any future use. Script: perbak_soc_analysis.py.
