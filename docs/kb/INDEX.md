# Knowledge Base Index — Theorem & Methodology Cards

Each instrument family used in this project (776 draws, ~25 instrument families) has a card below following the standard template (statement, assumptions, null value under i.i.d. uniform, detects/blind-to, finite-sample cautions, reference summary, canonical references, use in project).

**Governance**: per THEOREM_GOVERNANCE.md Part 3, a KB card in this folder is REQUIRED before any new theorem/instrument is admitted into the analysis. No card, no test.

## Four-face classification

Instruments are classified by which "face" of the data they interrogate:
- **statistical** — marginal frequencies and calibrated inference machinery
- **dynamical** — time/serial structure (memory, periodicity, long-range dependence)
- **algorithmic** — description-length and combinatorial structure
- **cross-sectional/physical** — joint structure across numbers and physics-style universality
- **relational** — structure shared between two datasets, or between a subset and the
  whole it is drawn from (see `docs/CROSS_DATASET_FRAMEWORK.md`, the fifth face). Cards
  for relational instruments (Gromov–Wasserstein, MMD/energy distance, persistence-diagram
  distances, the CCA family, graph matching/spectra, coresets/landmarks, matrix
  completion/compressed sensing) are admitted here under the same Part-3 gate; a card +
  passed null trial on **independent** data is required before any relational instrument
  touches real data.
- **decision** — converting (non-)findings into betting decisions

## Card table

| # | Card | Face | One-line description |
|---|------|------|----------------------|
| 1 | [law-of-large-numbers-clt.md](law-of-large-numbers-clt.md) | statistical | LLN/CLT underwriting all z-scores; CLT as RG fixed point used in block-mean kurtosis flow. |
| 2 | [chi-square-and-exact-monte-carlo.md](chi-square-and-exact-monte-carlo.md) | statistical | Frequency uniformity; asymptotic chi-square invalid at E=4.0–5.4, replaced by exact MC under 6-without-replacement (p=0.10–0.90). |
| 3 | [permutation-tests.md](permutation-tests.md) | statistical | Assumption-free covariate correlation tests; within-game z-scoring fixed pooling; moon/sun/Kp/tides all null (p>=0.18). |
| 4 | [scan-statistics-look-elsewhere.md](scan-statistics-look-elsewhere.md) | statistical | Kulldorff-style max windowed z over numbers/windows/games; 6/55 #45 anomaly: naive p=0.001 -> global p=0.148. |
| 5 | [multiple-comparisons.md](multiple-comparisons.md) | statistical | Bonferroni/BH, equivalence-class counting of m, forking paths, pre-registration; m=9/15/18 families. |
| 6 | [markov-chains-order-tests.md](markov-chains-order-tests.md) | dynamical | Order-0 vs order-1 tests, overlap/stickiness, tercile G-test; relaxation time 1.05–1.14 draws; Markov vs i.i.d. clarified. |
| 7 | [hurst-rs-analysis.md](hurst-rs-analysis.md) | dynamical | Long-range memory via R/S; estimator biased upward on short series (raw 0.56–0.70 = i.i.d. null) — calibration mandatory. |
| 8 | [doob-optional-stopping.md](doob-optional-stopping.md) | decision | No betting system beats a fair game; the decision-layer gate; why martingale doubling fails. |
| 9 | [kelly-criterion-st-petersburg.md](kelly-criterion-st-petersburg.md) | decision | Log utility resolves St. Petersburg; f* <= 1/C(n,6) => PHP25 stake needs ~PHP1B bankroll; Doob gates, EV measures, Kelly sizes. |
| 10 | [shannon-kolmogorov-compression.md](shannon-kolmogorov-compression.md) | algorithmic | Source-coding bound 22.3–25.3 bits/draw; incompressibility as one-sided Martin-Löf certificate; raw DEFLATE. |
| 11 | [marchenko-pastur-tracy-widom.md](marchenko-pastur-tracy-widom.md) | cross-sectional/physical | RMT eigenvalue bulk: zero escapes in all games; null lambda_max skewness +0.316 vs TW-GOE +0.293. |
| 12 | [wiener-khinchin-fisher-g.md](wiener-khinchin-fisher-g.md) | dynamical | Spectrum<->autocovariance equivalence; Fisher's exact g-test for hidden periodicities; all games p>=0.33. |
| 13 | [per-bak-soc-universality.md](per-bak-soc-universality.md) | cross-sectional/physical | SOC signatures, data collapse, RG flow, Binder cumulant; verdict: trivial fixed point; pseudo-plateau caught by calibration. |
| 14 | [power-laws-csn-zipf-taylor-benford.md](power-laws-csn-zipf-taylor-benford.md) | cross-sectional/physical | CSN MLE+Vuong (gaps geometric, z=-35.3); Zipf=chi-square in disguise; Taylor b~0.9; Benford vs exact uniform digit law. |
| 15 | [covering-designs-lottery.md](covering-designs-lottery.md) | algorithmic | Cushing–Stewart L(59,6,6,2)=27 via Fano planes; PCSO estimates ~13–26 tickets for a worthless 2-match guarantee. |
| 16 | [expected-value-stern-cover.md](expected-value-stern-cover.md) | decision | Hypergeometric tier EV, 20% tax, Poisson co-winner split; break-even jackpots; prize-weighting exposed -71% ROI of the Markov model. |
| 17 | [szemeredi-furstenberg-ap.md](szemeredi-furstenberg-ap.md) | marginal/combinatorial | Density alone forces APs (the Ramsey trap); two-sided MC-calibrated AP counts within draws and hot sets; Furstenberg bridge to recurrence. |
| 18 | [graphons-cut-norm.md](graphons-cut-norm.md) | cross-sectional/combinatorial | Dense graph limits; null co-occurrence graph -> constant graphon W=c; spectral-norm proxy for cut distance; equivalence vs MP measured by H-protocol. |
| 19 | [concentration-sparse-recovery.md](concentration-sparse-recovery.md) | marginal/geometric | Exclusion instrument: simultaneous MC band -> bias bound eps ~ sqrt(log P / n) + EV impact; null-calibrated soft-threshold (lasso) sparse recovery. |
| 20 | [mmd-energy-distance.md](mmd-energy-distance.md) | relational | R1 kernel two-sample tests (MMD/energy); pool-and-relabel null; equality of distribution ≠ relatedness. **Admitted** (see docs/ADMISSION_RELATIONAL.md). |
| 21 | [gromov-wasserstein.md](gromov-wasserstein.md) | relational | R2 alignment of metric-measure spaces without shared coordinates; always returns a coupling → null-critical. **Admitted**. |
| 22 | [cca-family.md](cca-family.md) | relational | R3 paired multi-view correlation (CCA/KCCA/PLS/HSIC); held-out only; shuffled-pairing null; in-sample ρ̂ is never evidence. **Admitted**. |
| 23 | [tda-persistence-distances.md](tda-persistence-distances.md) | relational | R4 persistence diagrams + bottleneck/Wasserstein; matched-density geometric null; witness complexes for subset topology. **Admitted**. |
| 24 | [graph-matching-spectra.md](graph-matching-spectra.md) | relational | R5 graph spectra/matching/community recovery; degree-preserving null mandatory (ER forbidden as sole control). **Admitted**. |
| 25 | [coresets-landmarks.md](coresets-landmarks.md) | relational | R6 coresets/Nyström/leverage landmarks; uniform-random-subset baseline; recovery curve is the deliverable. **Admitted**. |
| 26 | [matrix-completion-compressed-sensing.md](matrix-completion-compressed-sensing.md) | relational | R7 low-rank/sparse reconstruction as assumption-checking; marginal + permuted-entry nulls. **Admitted**. |
| 27 | [lagmax-crosscorrelation.md](lagmax-crosscorrelation.md) | relational | R8 phase-invariant lag-max cross-correlation (scan over lags, circular-shift null). **Admission FAILED at frozen gate** (FPR calibrated; power 0.58 < 0.8 at gating σ=1.0; curve 0.94/0.58/0.22). NOT admitted; redesign (coherence / Fourier-CCA) on roadmap; post-hoc benchmark check confirms declared blind spot (solved-set S1|S2 p=0.69). |
