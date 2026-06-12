# Lag-Max Cross-Correlation — Phase-Invariant Pairwise Dependence (R8)

**Domain face**: relational (temporal pairs)

**Statement**:
- Define the lag-shifted cross-correlation: ρ(d) = corr(x_t, y_{t+d}) over lags d in a
  declared window D = [−d_max, d_max]. The lag-max cross-correlation statistic is
  T = max over d ∈ D of |ρ(d)|, typically computed using circular (wrap-around) indexing
  to preserve the full autocorrelation structure of each series.
- This statistic detects monotone association between x and y at ANY phase offset d.
  Unlike Pearson correlation at lag 0 alone (which requires x and y to move in sync),
  lag-max scans over a window of lags to find the phase shift that maximizes alignment.
- The max-over-lags is a scan statistic (see kb/scan-statistics-look-elsewhere.md):
  the null distribution is NOT that of a single ρ(d), but rather the distribution of
  the maximum over all d ∈ D. This look-elsewhere effect is priced directly into the
  null model (see Null value section), so the same global-p calibration applies to
  every null sample.

**Assumptions**:
- Stationarity-ish within the lag window D (mean and autocorrelation structure stable
  over the window length). Violations lead to inflated false positives.
- The lag window D is declared a priori as part of the instrument registration
  (C10: representation charge applies if D is widened post-hoc). Once D is registered,
  the scan over D ∈ [−d_max, d_max] is the contracted test, and the null is calibrated
  for that fixed D.
- Both series are standardized (mean 0, SD 1) before cross-correlation is computed.
  Scaling does not affect correlation, but standardization aids numerical stability
  and interpretation.

**Null value under i.i.d. uniform** (circular-shift null):
- Under H₀ (no phase-shifted dependence), y is rolled by a uniform random offset δ
  drawn from [−∞, ∞] such that δ mod N is uniform on {0, 1, …, N−1} and |δ| > d_max
  (ensuring the offset is large enough to destroy cross-alignment without wrapping back
  into the original phase). The rolled y' = y_{t+δ} is then cross-correlated with the
  original x over the lag window D.
- This circular-shift null preserves the autocorrelation structure (serial dependence)
  within each series, destroying only the cross-temporal alignment. This is the
  correct null for phase-shifted monotone association: it allows x to have memory and
  y to have memory, but forces y to be uncorrelated with x at all lags d ∈ D.
- The p-value is computed as P_H₀(max_d |ρ'(d)| >= T_obs), where ρ' is the
  cross-correlation of x with the null-shifted y'. Monte Carlo sampling of the null:
  repeat the shift-and-correlate operation many times, collect the maximum |ρ'(d)|
  across all d ∈ D for each sample, and compute p = (# samples with max >= T_obs) / N_MC.
- Phipson–Smyth +1 floor: p_final = (# successes + 1) / (N_MC + 1), ensuring p > 0
  even if T_obs is extreme. This guards against zero p-values in finite samples and
  matches the lab's standard floor rule (docs/RELATIONAL_RUNBOOK.md M3).

**Detects / blind to**:
- **Detects**: lagged and phase-shifted monotone (Pearson-correlatable) relationships
  between x and y. Examples: y lags x by d* time steps with unknown d*, or y is a
  delayed version of x, or x and a phase-shifted copy of y co-vary. The monotone
  scope is precisely that of Pearson correlation (linear association).
- **Blind to**: nonlinear amplitude encodings that do not project onto a monotone
  direction without additional transformation (e.g., amplitude modulation, frequency
  modulation where the instantaneous frequency is the signal of interest, or DTW-style
  elastic warping). Also blind to directional causality (the test is symmetric: it
  cannot distinguish x causes y from y causes x).
- **Scope boundary**: the test is a relational (pair) test, not a marginal one. It
  reports on the association structure between two series, not on the marginal
  properties of either series alone. It requires two distinct series to run.

**Finite-sample cautions**:
- **Lag-window inflation**: the lag window |D| inflates the statistic's null mean.
  The max-over-lags is larger than any single lag's correlation. The null distribution
  prices this: as |D| grows, the expected maximum correlation under the null increases,
  but so does the critical value. However, power *falls* as |D| grows (more lags to
  search means more noise in the search space). Declare the smallest *physically
  motivated* lag window: if you expect the association to occur within d_max = 10 time
  steps, do not scan d_max = 1000 on the hope of finding something. Multiplicity cost
  is automatic in the null, but efficiency is not.
- **Edge effects**: under non-circular variants (linear shift with zero-padding or
  reflection), the boundaries introduce artifacts. Circular (wrap-around) indexing is
  strongly preferred and is the default here; if any code path uses linear shifting,
  this assumption is violated.
- **Series must be standardized**: unstandardized correlations depend on the scale of x
  and y, which can mislead. Always center and scale to SD=1 before computing lags.
- **Autocorrelation and stationarity**: if x or y has strong autocorrelation, the
  circular-shift null is still valid (shift preserves the autocorrelation of y),
  but the cross-correlation at individual lags will show spurious structure due to
  the memory. A strong autocorrelation in both series can inflate the max correlation
  at lag 0 or nearby. If such structure is present, report it but be cautious about
  interpretation: the signal may be driven by high autocorrelation rather than
  true phase-shifted dependence.

**Reference summary**:
Cross-correlation is a classical tool in signal processing and time-series analysis
for detecting lagged relationships. The cross-correlation function (CCF) ρ_xy(d) is
the correlation between x_t and y_{t+d}; plotting ρ_xy(d) over a range of lags reveals
the phase and strength of association.

The lag-max statistic T = max_d |ρ_xy(d)| is a *scan statistic* over lags (see the
lab's internal card kb/scan-statistics-look-elsewhere.md for the general framework).
The null distribution of the maximum is calibrated by Monte Carlo, not by asymptotic
theory, because the distribution of the max is non-standard and depends on the lag
window's size and the series' autocorrelation.

The circular-shift null is a standard resampling technique in time-series testing
(Politis & Romano 1994 on the stationary bootstrap; Lahiri 1999 on block bootstrap
variants; Shao 2011 on the fixed-b asymptotic theory of studentized U-statistics under
dependent data). The idea is to break the cross-alignment while preserving the
marginal time-series structure — achieved by rolling one series by a large uniform
random offset.

**Canonical references**:
- Box & Jenkins, *Time Series Analysis: Forecasting and Control*, 3rd ed., Wiley (2008).
  Classic reference for CCF and lagged relationships in ARIMA modeling. Chapters 7–8 cover
  intervention analysis and transfer functions (lagged input-output relationships).
- Politis & Romano, "The stationary bootstrap," Journal of the American Statistical
  Association 89, no. 428 (1994): 1303–1313. Foundational resampling method for
  dependent data; circular shift is a special case of the stationary bootstrap with a
  fixed shift location chosen to be far outside the lag window.
- Lahiri, S.N., *Resampling Methods for Dependent Data*, Springer (2003). Comprehensive
  treatment of block bootstrap, stationary bootstrap, and sub-sampling for time series.
  Chapter 3 covers methods for establishing validity of resampling under weak dependence.
- Shao & Tu, *The Jackknife and Bootstrap*, Springer (1995). General theory of
  resampling; Chapter 5 covers weakly dependent data.
- Internal cross-reference: kb/scan-statistics-look-elsewhere.md for the generic
  max-over-windows framework and look-elsewhere effect.

**Use in this project**: Relational instrument R8 (`relational_admission.py`). Intended
use: admission suite E1 (FPR on independent AR(1) pairs generated independently, no
cross-coupling — all shifts are nulls) + positive control (common periodic cycle with
random phase offset applied to one series; a phase-shifted relationship that Spearman
at lag 0 would miss). Status: **admission pending** — the analyst will run the E1 and
E4 suite and report results in ADMISSION_RELATIONAL.md. Addresses the blind-eval miss
FN-4 (SERIES-PAIR-S1|S2: p=0.7462 under Spearman circular-shift null, missing a
phase-indeterminate periodic relationship that lag-max cross-correlation is designed to
detect).
