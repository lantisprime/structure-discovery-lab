# Wiener–Khinchin Theorem & Fisher's g-Test for Periodicity

**Domain face**: dynamical

**Statement**:
- Wiener–Khinchin: for a wide-sense stationary process, the power spectral density S(f) is the Fourier transform of the autocovariance function: S(f) = sum_tau gamma(tau) e^{-2 pi i f tau}; spectrum and autocovariance carry identical second-order information.
- Fisher's g-test (1929): for a length-N Gaussian white-noise series with periodogram ordinates I(f_1), ..., I(f_m) at the m = floor((N-1)/2) Fourier frequencies, the statistic g = max_k I(f_k) / sum_k I(f_k) has exact null distribution P(g > x) = sum_{j=1}^{floor(1/x)} (-1)^{j-1} * C(m, j) * (1 - j x)^{m-1} (an exact alternating sum), giving an exact test for a hidden sinusoid at unknown frequency.

**Assumptions**: Wiener–Khinchin requires wide-sense stationarity. Fisher's g assumes Gaussian white noise under H0 (i.i.d. lottery statistics are white; mild non-Gaussianity is handled by the periodogram's asymptotic exponentiality, or by Monte Carlo calibration), a single sinusoid alternative, and frequencies restricted to the Fourier grid.

**Null value under i.i.d. uniform**: flat spectrum S(f) = const (white noise); periodogram ordinates approximately i.i.d. exponential; g follows the exact Fisher distribution; p uniform on (0,1).

**Detects / blind to**: detects a strong concentration of variance at one frequency — weekly/monthly/seasonal cycles, machine-rotation periodicities, draw-schedule artifacts. Built-in look-elsewhere control over all Fourier frequencies. Blind to broadband or multi-line spectra splitting power across frequencies (extensions: Siegel's test), frequencies off the Fourier grid (leakage dilutes the peak), and nonstationary/transient oscillations.

**Finite-sample cautions**: the exact null is for Gaussian white noise; for bounded discrete lottery statistics at N ~ a few hundred, the exponential approximation to periodogram ordinates is good but was cross-checked against simulated draws. Unequal spacing or missing draws breaks the Fourier-grid exactness (use Lomb–Scargle then). The test targets the single largest peak — report the whole periodogram alongside g.

**Reference summary**:
The Wiener–Khinchin theorem (Wiener 1930, Khinchin 1934) establishes that for stationary processes the power spectrum and the autocovariance function are a Fourier-transform pair. Its role here is conceptual bookkeeping for the multiple-comparisons ledger: spectral tests and autocorrelation tests are not independent instruments but two coordinates of the same second-order object, so they count as one equivalence class of hypotheses, and a clean spectrum implies clean autocovariances (and vice versa) at second order.

Fisher's g-test (1929) is the classical exact test for a hidden periodicity at unknown frequency. The periodogram of white noise has approximately i.i.d. exponential ordinates, so the largest ordinate's share of total spectral mass, g, has a closed-form null distribution given by an exact alternating binomial sum. This builds the search over all Fourier frequencies directly into the null — an early, exact instance of look-elsewhere correction — and rejects only when one frequency carries implausibly much of the variance.

Applied to lottery draw statistics (sums, means, per-number indicators aggregated per draw), the pair of tools asks whether any clock — calendar, mechanical, or operational — leaves a rhythmic fingerprint. A flat periodogram with non-significant g across games certifies the absence of any single dominant cycle at second order.

**Canonical references**:
- https://en.wikipedia.org/wiki/Wiener%E2%80%93Khinchin_theorem
- Fisher, "Tests of significance in harmonic analysis", Proc. R. Soc. Lond. A 125 (1929).
- https://en.wikipedia.org/wiki/Periodogram
- Brockwell & Davis, *Time Series: Theory and Methods*, Ch. 10.

**Use in this project**: Wiener–Khinchin links spectrum and autocovariance (one hypothesis class, not two); Fisher's exact g-test (exact alternating-sum p-value) used to hunt hidden periodicities in draw statistics. All games null with p >= 0.33 — no periodic structure.
