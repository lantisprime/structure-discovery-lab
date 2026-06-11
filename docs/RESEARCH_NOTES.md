# PCSO Lotto Prediction Project — Research Dossier

Compiled: June 10, 2026 · Analyst: Claude (with Cha)
Scope: 194 verified draws, Mar 10 – Jun 10, 2026, all five PCSO 6-number games.

---

## 1. Files in this folder

| File | Contents |
|---|---|
| `PCSO_Lotto_Analysis_Mar-Jun_2026.xlsx` | Master workbook: Read Me, Draws, Frequency (chi-square), Hot-Cold, Moon-Sun Test (+ geomagnetic), Future Draws, EV Calculator |
| `data_draws.csv` | Raw 194 draws (game, date, 6 numbers) |
| `data_astro_geomagnetic.csv` | Per-draw Moon alt/az/illumination/distance, Sun altitude, Kp geomagnetic index, plus correlation results |
| `data_future_schedule.csv` | Draw schedule Jun 11 – Jul 10, 2026 with quick picks and ephemeris |
| `RESEARCH_NOTES.md` | This document |

## 2. Data sources

- **PCSO official results**: pcso.gov.ph/SearchLottoResult.aspx (primary; used to verify every overlapping draw — all matched)
- **Draw history archive**: lottopcso.com per-game history pages (6/42, 6/45, 6/49, 6/55, 6/58)
- **Known gaps**: 6/58 Apr 3; 6/42 Apr 2 & 4 (no results published)
- **Ephemeris**: PyEphem 4.2.1, observer at PCSO Main Office, Mandaluyong (14.5794°N, 121.0359°E), draw time 21:00 GMT+8
- **Geomagnetic**: GFZ Potsdam Kp index, 3-hourly, CC BY 4.0 (kp.gfz.de)
- **Game rules/odds/prizes**: PCSO game pages; Wikipedia "PCSO Lottery Draw"

## 2b. Data validation (added Jun 11, 2026 after adversarial review)

- **102 draws cross-validated against pcsodraw.com** (independent archive, data back to 2007, sources pcso.gov.ph): the latest 20 per game plus targeted checks — **0 mismatches**. With 0 errors in 102, the archive error rate is below ~3% at 95% confidence.
- **6 draws verified against the official PCSO results table** (Jun 7–10).
- **Anomaly resolution**: an integrity scan flagged two adjacent draw pairs sharing 4 of 6 numbers (6/42 May 21/23; 6/49 Mar 22/24) — a possible transcription-copy signature (~3% probability by chance). Both pairs were verified draw-by-draw against pcsodraw per-date pages (incl. draw numbers #1795/#1796, consecutive): **all genuine; real coincidences**.
- **Internal integrity**: no duplicate game+date rows, no duplicate combinations, all numbers within pool, 6 distinct numbers per draw; pcsodraw draw-numbering continuity consistent with the Holy Week gaps.
- **Validation status: 106/194 (55%) independently multi-source validated; the remaining 88 draws (Mar 10 – Apr 21) rest on lottopcso.com plus the two spot checks above.** Aggregate statistics are robust to this residual risk (a single corrupted row shifts no test conclusion), but per-draw lookups for the older window should be treated as single-source.

## 3. Hypotheses tested and results

All tests on the 194-draw sample. Response variable: mean drawn number normalized by pool (and full frequency distributions for chi-square).

| # | Hypothesis | Test | Result | p-value | Verdict |
|---|---|---|---|---|---|
| 1 | Number frequencies deviate from uniform (6/42) | Chi-square, df=41 | χ²=26.6 | 0.96 | Random |
| 2 | Same, 6/45 | df=44 | χ²=46.0 | 0.39 | Random |
| 3 | Same, 6/49 | df=48 | χ²=35.7 | 0.91 | Random |
| 4 | Same, 6/55 | df=54 | χ²=61.2 | 0.23 | Random |
| 5 | Same, 6/58 | df=57 | χ²=60.5 | 0.35 | Random |
| 6 | Moon altitude affects results | Pearson r, n=194 | r=−0.088 | 0.22 | Null |
| 7 | Moon illumination (phase) | Pearson r | r=−0.061 | 0.40 | Null |
| 8 | Moon distance (tidal strength) | Pearson r | r=+0.002 | 0.98 | Null |
| 9 | Sun altitude | Pearson r | — | >0.05 | Null |
| 10 | Geomagnetic Kp at draw time | Pearson r | r=−0.026 | 0.72 | Null |
| 11 | Geomagnetic Kp daily mean | Pearson r | r=−0.023 | 0.75 | Null |
| 12 | Excess primes drawn | vs hypergeometric mean | 364 obs vs 347.6 exp | n.s. | Noise |
| 13 | Excess consecutive pairs | exact combinatorial | 103 obs vs 95.6 exp | n.s. | Noise |
| 14 | Excess 3-term arithmetic progressions | Monte Carlo (2000 reps/draw) | 136 obs vs 120.7 exp | n.s. | Noise |
| 15 | Sums divisible by 9 | uniform expectation | 17 obs vs 21.6 exp | n.s. | Noise |
| 16 | Tidal Δg level at draw (lunisolar vertical gravity perturbation, computed from ephemeris) | Pearson r, n=194 | r=+0.079 | 0.27 | Null |
| 17 | Tidal trend (rising vs falling at 21:00 PHT) | Pearson r | r=+0.055 | 0.44 | Null |

| 18 | Sequence learnability ("token prediction"): hot/cold exponential tilting model P(i)∝exp(β·z_freq) fit sequentially | MLE + likelihood-ratio CI + held-out log-loss | β̂=+0.015, CI [−0.04, +0.08] contains 0; held-out gap 0.0013 nats/draw (noise) | n.s. | Uniform is the optimal predictor |

**Tide magnitude note**: tidal Δg at the venue ranged −6.6×10⁻⁷ to +1.3×10⁻⁶ m/s² across the sample (spring and neap tides both covered) — at most 1.3×10⁻⁷ of g, acting equally on all balls.

**Sample included genuine extreme conditions**: geomagnetic storms to Kp 7.0 (Apr 21–22), full/new moons, perigee/apogee. No condition shifted the draws.

### Corrected statistics (Jun 11, 2026 — methodology fixes after adversarial review)

The original chi-square tests used the asymptotic approximation below its validity conditions (expected counts 4.0–5.4) and ignored within-draw dependence; correlations pooled five games and used a normal approximation. All recomputed properly:

**Exact Monte Carlo chi-square** (10,000 simulated datasets, sampling 6 numbers without replacement per draw): 6/42 p=0.90, 6/45 p=0.19, 6/49 p=0.80, 6/55 p=0.11, 6/58 p=0.18. All consistent with uniform randomness.

**Permutation correlation tests** (within-game z-scored response, 20,000 permutations, assumption-free; family m=12, Bonferroni threshold p<0.0042):

| Covariate | Pearson r (perm-p) | Spearman ρ (perm-p) |
|---|---|---|
| Moon altitude | −0.085 (0.24) | −0.088 (0.23) |
| Moon illumination | −0.062 (0.39) | −0.062 (0.39) |
| Moon distance | −0.002 (0.98) | −0.018 (0.80) |
| Sun altitude | +0.005 (0.95) | +0.005 (0.95) |
| Geomagnetic Kp | −0.038 (0.61) | −0.026 (0.72) |
| Tidal Δg | +0.091 (0.20) | +0.096 (0.18) |

**Number-theory metrics with proper Monte Carlo nulls** (5,000 full-dataset simulations, two-sided p): primes p=0.27, consecutive-pairs p=0.32, AP3 count p=0.18, sum÷9 p=0.30. The same-direction excesses noted in the adversarial review are jointly unremarkable; the data-corruption explanation was also directly ruled out by validation (§2b).

**Power disclosure**: at n=194, 80% power detects only |r| ≥ 0.20 (α=0.05) or |r| ≥ 0.27 (corrected α). Conclusions are therefore "no moderate-to-large effect", not "no effect". (Note: an effect of even r=0.1 would be useless for prediction anyway — it would explain 1% of variance in a game where you must match all six numbers.)

## 3b. Frozen-dataset protocol (pre-registration, binding from Jun 11, 2026)

The 194 draws of Mar 10 – Jun 10, 2026 are hereby **frozen as the exploration set**. Every result above is exploratory: hypotheses were chosen while looking at this data, so no result from this set can ever count as confirmation, regardless of p-value.

**Confirmation set**: all draws after Jun 10, 2026 (appended by the weekly scheduled task with two-source validation). **Pre-registered test family (fixed, m=8)**: per-game MC chi-square (5 tests) + permutation Pearson of within-game z-scored mean-drawn-number vs moon altitude, moon illumination, Kp (3 tests). **Decision rule**: flag only at p < 0.00625; a flag triggers replication on further fresh data, never a betting decision. No tests may be added to the family without re-registering and resetting the confirmation set. This rule exists because weekly re-testing on accumulating data ("peeking") otherwise guarantees an eventual false positive.

## 4. Physics summary

- **Chaos**: the draw chamber is a mixing dynamical system with positive Lyapunov exponents. Hundreds of ball collisions/second make the prediction horizon milliseconds, even though the system is deterministic. (Contrast: roulette was historically beatable — few interactions, smooth deceleration — Thorp & Shannon 1961.)
- **Lunar/solar gravity**: tidal acceleration across a ball ≈ 10⁻¹³ g vs ~10 g per collision (13 orders of magnitude), and it acts equally on all balls — cannot favor a number.
- **Magnetism**: independent force from gravity; balls are non-magnetic; Kp 7 storm ≈ few hundred nT ≈ 0.5% of the static field. Confirmed null empirically (tests 10–11).
- **Real historical anomalies were fraud, not physics**: 1980 Pennsylvania "Triple Six Fix" (weighted balls). PCSO countermeasures: independent panel, COA oversight, random ball-set selection by card draw (≈3 sets/game), on-camera per-ball weighing. Machine/ball-set IDs are **not published** in results data — and set rotation + weighing breaks the persistent-bias chain that machine-tracking would need.

## 5. Mathematical theorems applied

- **Doob's optional stopping theorem**: no betting system, stake sizing, or stopping rule converts a fair/unfavorable game into a favorable one. Closes the "system" door permanently.
- **Law of large numbers / CLT**: frequencies converge to uniform (observed); small samples show streaks (the hot/cold illusion).
- **Ergodic mixing**: past draws decorrelate completely from future ones.
- **Kolmogorov complexity**: random = incompressible = no exploitable pattern, by definition.
- **Covering/lottery designs (Cushing & Stewart 2023, arXiv 2307.12430; *Constraints* 2024)**: L(59,6,6,2)=27 — minimum tickets to guarantee even a 2-ball match in a 59-ball game, via Fano-plane constructions. Partition-method estimates for PCSO pools (tickets to guarantee a 2-match): 6/42 ≈ 13, 6/45 ≈ 15, 6/49 ≈ 19, 6/55 ≈ 23, 6/58 ≈ 26. **PCSO pays nothing for 2 matches**, so guarantees relevant to prizes need far more tickets. With 1–2 tickets, no guarantee of any kind exists.
- **Stern–Cover expected-value analysis**: EV varies with jackpot size and splits; see EV Calculator sheet. At Jun 10, 2026 jackpots, every game returns ₱0.17–0.31 per peso. **Sensitivity analysis (Jun 11)**: ticket-sales estimates (±2× range) move EV by under 2% at current jackpots; lower-tier prize uncertainty (pari-mutuel values are estimates; a possible 2026 prize restructure could raise them up to ~5×) moves EV to at most ₱12–19 per ₱25 ticket — **still -EV in every scenario at current jackpots**. Break-even jackpots are therefore ranges, not points: 6/42 ₱0.09–0.15B, 6/45 ₱0.14–0.23B, 6/49 ₱0.25–0.39B, 6/55 ₱0.32–0.75B, 6/58 ₱0.38–1.02B (6/58 crossed ₱1B once in history, Oct 2018, split 2 ways). Update the yellow prize cells from official PCSO figures before relying on any specific number.
- **Game theory of splits**: choose unpopular combinations to keep more when winning. Case study: Oct 1, 2022 PCSO 6/55 drew 9-18-27-36-45-54 → 433 winners split the jackpot (~₱545k each instead of ₱236M).

## 6. The 2-ticket protocol (final recommendation)

For a seldom player buying at most 2 combinations:

1. **WHEN**: play only deep rollovers — check the EV Calculator; EV varies ~5× between minimum and record jackpots. This is the largest controllable effect.
2. **DISJOINT**: make the two tickets share no numbers (12 distinct). Jackpot events are mutually exclusive; 2 distinct tickets = exactly 2/C(n,6). The only rigorous odds improvement that exists.
3. **UNPOPULAR**: random picks, rejected if pattern-like (all ≤31, sequences, multiples, famous numbers). Doesn't change win probability; substantially changes expected payout via split avoidance.
4. **LOG**: record every play and outcome; expect the loss; treat the spend as entertainment priced at ~₱17–20 per ₱25 ticket.

## 6b. One-year dataset extension (Jun 11, 2026) — `data_draws_1yr.csv`

776 draws, Jun 11 2025 – Jun 10 2026, all five games. Kept **separate** from the frozen 194-draw exploration set. Sources: lottopcso year-2025 + 2026 history pages; assembled partly by a delegated agent run.

**Validation performed**: 0 integrity errors (6 distinct numbers in pool, no duplicate game+date, no duplicate combinations); every draw date falls on its game's scheduled weekday; the only schedule gaps are Holy Week (Apr 17–19 2025, Apr 1–5 2026 — known PCSO suspensions); 12+ draws cross-checked against jackpot-winners records; 2025 spot checks against pcsodraw.com per-date pages matched exactly (6/55 Jun 16 and Sep 24, 2025 — including drawn-order). 2026 portion inherits the earlier 106-draw multi-source validation. Residual status: most 2025 rows are single-source + structural checks.

**Finding worth recording — 6/55 chi-square, full year: MC p = 0.003.** Decomposition: the deviation is entirely in the 2025 half (n=88, p=0.001), driven by number 45 (26 hits vs 9.6 expected) and number 42 (elevated); the 2026 half is unremarkable (p=0.10), 45 hit 9 times vs 8.3 expected there, and the per-number deviation correlation across halves is r=+0.09 (≈0, no persistence). The hot-45 rows were spot-verified as genuine.

**Interpretation (disciplined)**: (a) this is exploratory — we tested the year because we had it, so the p-value cannot be taken at face value; with the number of looks taken, familywise significance is marginal (~0.01); (b) if it was a real transient bias (one ball set, since rotated/retired — PCSO changed prize structures Feb 2026), it is *already gone*: zero persistence into 2026; (c) either way it has **no betting value today**. This is the project's thesis in miniature: even a "signal" found in lottery history evaporates under non-stationarity before it can be used.

**Re-registration (binding)**: since the confirmation set was still empty, the pre-registered family is re-registered once, now m=9: the original 8 tests + "6/55 number-45 frequency vs Binomial(n_draws, 6/55)" on post-Jun-10-2026 draws only. New threshold p < 0.05/9 = 0.0056. No further additions without resetting the confirmation set.

## 6c. Markov-chain memory analysis (Jun 11, 2026) — `markov_analysis.py`

Independent bias-detection pass on the 776-draw year, testing for *memory* (frequency tests detect favored numbers; Markov tests detect whether draw t influences draw t+1 — the signature of ball wear, poor mixing, or set-rotation artifacts). Four MC-calibrated tests per game (exploratory family m=20, threshold p<0.0025): T1 consecutive-draw overlap vs 36/P; T2 per-number 2-state presence-chain stickiness P(1→1)−P(0→1); T3 order-1 vs order-0 likelihood-ratio G-test on draw-mean terciles; T4 second-eigenvalue modulus of the tercile transition matrix (mixing speed).

**Result: no memory.** Smallest of 20 p-values = 0.053 (6/45 overlap) vs ~0.048 expected minimum under pure randomness — the dataset passes at exactly the theoretical rate. Stickiness signs scatter (+ for 6/42/45/49, − for 6/55/58), G-statistics straddle their null mean, all |λ₂| at or below null levels (fast mixing). Caveats: T1/T2 are near-duplicate statistics (effective family is smaller, which is anti-conservative in our favor only on the threshold side); script seeded and reproducible.

## 6d. Pure Markov model + walk-forward backtest (Jun 11, 2026) — `markov_chain_model.py`

Fitted per-ball 2-state presence chains (Laplace-smoothed) and tercile 3-state chains as a *working model* (no testing), then backtested top-6 predictions walk-forward (fit on draws 1..t-1, predict draw t, 626 predictions). Chain parameters (CORRECTED Jun 11 after code review — original (x+1)/(n+2) Laplace smoothing pulled small-sample estimates toward 0.5, inflating all P(repeat); smoothing now centered at the memoryless rate 6/P): mean P(repeat) scatters around the memoryless value — above it in 6/42/45/49 (e.g. 6/45: 0.150 vs 0.133), below it in 6/55/58 (e.g. 6/58: 0.087 vs 0.103) — consistent with the unsmoothed stickiness signs in §6c, i.e. noise. Relaxation times 1.05–1.14 draws (≈ instant forgetting); strongest "successor links" (e.g. 32→34 at 0.62) are 6–10-observation artifacts.

**Backtest (CORRECTED after smoothing fix): 484 single-number hits vs ~459 expected (aggregate z ≈ +1.3, n.s.; was 500 / z ≈ +2.1 under the biased smoother — the 0.5-centered prior made the model systematically over-prefer last-draw repeats, manufacturing roughly half the apparent edge).** Dissection: (a) the excess concentrates in 6/55 (z=+2.02) — the walk-forward model keeps selecting number 45 through 2025, i.e. it *rediscovers the already-known dead transient*; this is the same single anomaly counted again, not independent evidence; (b) p ≈ 0.03 is exploratory and does not clear any corrected threshold used in this project; (c) the held-out token-prediction test (§ table, #18) found β CI [−0.04, +0.075] — consistent with zero; (d) even taken at face value, +9% single-ball hit rate pays nothing (PCSO prizes start at 3 matches) and evaporates with the transient that causes it. Verdict: the "edge" is the hot-45 ghost in a new costume. The 6/55 #45 confirmation test (registered, §6b) remains the arbiter.

## 6e. Theorem-based structure discovery suite (Jun 11, 2026) — `structure_discovery.py`

Dataset treated as an abstract sequence; three independent mathematical certificates: (I) **Shannon source-coding / Kolmogorov incompressibility** — bit-packed sequence attacked with LZMA/zlib/bz2; best compression stayed 30%+ *above* the entropy bound H = log₂C(P,6) per draw in all games (no computable regularity found); (II) **Marchenko–Pastur (random matrix theory)** — eigenvalue spectra of the T×P presence-correlation matrices show zero eigenvalues escaping the MC-calibrated null band (no collective modes/factors); (III) **Wiener–Khinchin + Fisher's exact g-test** — no significant periodogram peak in any game (no hidden cycles; smallest p = 0.37). All three certificates independent of the earlier statistical (frequency/correlation), dynamical (Markov), and learning-theoretic (token-prediction) instruments; all concur.

## 6f. Cross-theorem correlation detector (Jun 11, 2026) — `cross_theorem_correlation.py`

Joint test for structure invisible to single instruments: per-ball signals from five theorem domains (frequency z, Markov stickiness, spectral peak, RMT leading-eigenvector loading, recurrence-gap variance) correlated pairwise within each game; statistic = max |r| over 10 pairs, MC-calibrated against the constrained null (features share raw data, so null correlations are structurally nonzero — e.g. freq×gap-variance ≈ 0.6 under H₀). Result: all five games null (MC p = 0.09–0.93); observed max-couplings sit at or below null medians. No latent bias couples the domains.

## 6g. Exploration batch 2 (Jun 11, 2026) — `explore_batch2.py`

Five new angles, MC-calibrated: **E1** physical exit-order position effects (first use of the as-drawn order data) — null, p=0.58–0.78, exit position carries no information; **E2** weekday/draw-slot effects — null; **E3** pair affinity (max co-occurrence, look-elsewhere over all pairs) — 6/55 mildest at p=0.043 (the pair involves the 2025 hot numbers; n.s. with 5 games); **E4** cross-game same-night coupling (shared studio/eve) — null, p=0.61; **E5 Kulldorff-style scan statistic** — the decisive one: the hottest 30-draw run of ANY number in ANY window of ANY game is z=5.11 (it is the 6/55 #45 run), but the fully look-elsewhere-corrected global p = **0.148**: about 1 in 7 perfectly random five-game years contains a run at least that hot somewhere. **The hot-45 anomaly is hereby explained**: its naive half-year p=0.001 was an artifact of implicitly searching 55 numbers × many windows × 5 games; corrected for the search space it is unremarkable. The pre-registered #45 confirmation test stays in place as a formality, with expectation of a null.

## 6h. Independent-review response + exploration batch 3 (Jun 11, 2026) — `review_response.py`

An external LLM review proposed 11 steps; 8 were already implemented. The 3 gaps were built: **R1 row-level audit table** (`data_draws_1yr_audited.csv`): 9 rows official-verified, 105 two-source (13.5%), 662 single-source (85%) — the exposure is now quantified per row, not just in aggregate. **R2 payout-relevant backtest** of the walk-forward Markov model: 14 vs 11.4 expected 3+-matches; prize-weighted payout ₱4,480 vs ₱2,360 expected — but vs ₱15,650 ticket cost; the excess is one 4-match in 6/55 (the known cluster); match-count distribution otherwise tracks the hypergeometric baseline. **R3 rolling-window persistence** (4 windows, cross-window correlation of per-number deviations): four games null; **6/55: r=+0.150, MC p=0.002 (familywise ~0.01)** — #45 bias-ratio by window: 3.06, 1.88, 2.35, 0.94. The 2025-era 6/55 deviation persisted across THREE quarters and normalized exactly in the window containing the Feb 2026 prize/era change. This upgrades the interpretation from "single lucky burst" toward "era-specific transient idiosyncrasy (ball set?) that decayed" — though all 6/55 statistics remain correlated views of one number cluster, and 85% of the 2025 rows are single-source (two #45 rows spot-verified exact). Non-actionable either way: window 4 (current era) is normal. **E6′ recurrence-gap law** (binned chi-square vs exact Geometric(6/P), MC): four games null; 6/55 p=0.028 (same cluster; n.s. familywise). Note: the first E6 (KS) was degenerate under ties and replaced — logged as a methods lesson.

**Follow-up COMPLETED (Jun 11)**: all 88 single-source 2025 6/55 rows verified against pcsodraw per-date pages (`_655_2025_verification.csv`): **85/88 exact match, including 25 of the 26 #45 rows**. Three mismatches flagged in the audit table: 2025-08-13 and 2025-09-03 (archive-side errors — pcsodraw's pages repeat their own previous draw's numbers verbatim while showing distinct draw metadata) and 2025-10-29 (unresolved, needs a third source). **The 2025 6/55 era-effect now stands on verified data**: even discarding the one conflicted #45 row, #45 appeared 25× vs ~9.6 expected in the 2025 half. Audit census after update: 197 multi-source/official (25%), 576 single-source, 3 under review.

## 6i. Per Bak / self-organized criticality scan (Jun 11, 2026) — `perbak_soc_analysis.py`

Tested the three SOC signatures (Bak–Tang–Wiesenfeld) on draw-mean series, MC-calibrated, family m=15: **S1 spectral slope** α = 0.03–0.16 vs SOC's α≈1 (white-noise flat; p=0.28–0.91); **S2 avalanche sizes** (above-median runs) consistent with the geometric law, no heavy tail (p≥0.09); **S3 Hurst exponent** raw Ĥ = 0.56–0.70 but the MC null shows identical values — the R/S estimator's known upward bias at short series, fully absorbed by calibration (p=0.12–0.89; an uncalibrated analysis would have "discovered" long-range memory here). Verdict: no criticality reaches the outputs — the chamber is driven granular matter, but the draw *selection* destroys any internal correlation structure, as designed.

**6i-b. Universality & power-law addendum (Jun 11, 2026).** (i) *Universality-class identification was not attempted because it is not attemptable*: class exponents (BTW τ≈1.27, mean-field τ=3/2, directed percolation, etc.) require a power-law scaling regime of ≥2–3 decades; the data's largest avalanche is 8 → scaling range 0.9 decades, below any exponent estimation threshold. Class analysis presupposes criticality; the SOC scan rejected criticality at step one. (ii) *Formal power-law test* (Clauset–Shalizi–Newman MLE + Vuong LR vs geometric): recurrence gaps n=4407, Vuong z=−35.3 → decisively geometric; avalanche sizes n=206, z=−3.2 → geometric; extreme-streak lengths n=70, z=−0.2 → indistinguishable (insufficient n). Exponential-family tails everywhere = characteristic scale = off-critical bulk phase, where universality has nothing to organize. (iii) *Where universality DID govern this project*: the mathematical side — CLT (Gaussian class) under every z-score; extreme-value/Gumbel behavior in the scan statistic; and **Tracy–Widom**: the MC null of λ_max for the 6/55 presence-correlation matrix shows skewness +0.316 vs the universal TW-GOE value ≈+0.293 — our binary, row-constrained matrices land in the same universality class as Gaussian ensembles, exactly as TW universality predicts. The randomness of the lottery is itself a universality phenomenon: its statistics are governed by the same limit laws regardless of microscopic mechanism.

**6i-c. Full universality machinery applied (Jun 11, 2026) — `universality_collapse.py`.** Conceding the methodological point that universality tools do not require criticality (they *identify the fixed point*), three canonical analyses were run. **U1 data collapse**: the five games' avalanche CCDFs, rescaled by mean size, collapse onto one curve (max cross-game spread 0.21 incl. tail noise) — and the universal scaling function they collapse onto is the *geometric* form 2^−(2x−1) of the trivial fixed point, not a power law. **U2 RG flow**: excess kurtosis of block means fluctuates around 0 at all block sizes k=1..16 — the data already sits AT the Gaussian (CLT) fixed point; no flow away. **U3 Binder cumulant**: raw U rises to ≈0.3–0.5 at W=32, superficially resembling a critical plateau — but MC calibration shows the i.i.d. null produces the identical rise (n_windows≈4 estimator bias; observed U inside the null 95% CI at every W: e.g. W=32, U=0.32 vs null mean 0.36, CI [−0.05,+0.60]). *Second instance, after Hurst, of an uncalibrated physics estimator manufacturing a pseudo-critical signature on short series.* Conclusion: universality machinery fully applied; fixed point identified as the trivial/infinite-temperature one; the scaling function and flow direction are exactly those of i.i.d. uniform.

## 6j. Overlooked power-law family sweep (Jun 11, 2026) — `powerlaw_sweep.py`

Five scaling laws not previously tested (family m=18, threshold p<0.003): **P1 Zipf** rank-frequency slopes s=0.21–0.28 vs null ~0.20–0.23 (i.i.d. sampling noise, not Zipf's s≈1); mildest p=0.017 (6/55) and 0.022 (6/45) — n.s. familywise, and the Zipf slope is a monotone transform of frequency dispersion, i.e. the chi-square family in disguise (6/55 = the #45 cluster again). **P2 Taylor's law** fluctuation-scaling exponent b=0.3–1.3 vs binomial null ~0.9, all p≥0.27 (no multiplicative clustering, b≁2). **P3 first-digit laws**: Benford decisively rejected (χ²=1312, df=8) while the *exact* uniform-derived digit law fits (χ²=9.3) — the data follows the correct law, not the famous one; Benford would only be expected on multiplicatively-grown quantities like rollover jackpots, not on uniform draws. **P4 Lévy flights**: step-length tails exponential (Vuong z=−9.4), α̂=2.81 moot. **P5 coupon-collector**: time-to-full-coverage inside the MC 95% CI in all games (e.g. 6/58: 66 vs CI [27,70]). Verdict: no overlooked power law; every scaling relation matches the i.i.d. form.

## 7. Limitations & adversarial review log (Jun 11, 2026)

A full adversarial review was conducted; status of each finding:

| Finding | Severity | Status |
|---|---|---|
| 188/194 draws unverified vs official source | 1 | **Mitigated**: 106 multi-source validated (0 mismatches); residual 88 single-source, see §2b |
| Adjacent-draw similarity anomaly (possible transcription error) | 1 | **Resolved**: both pairs verified genuine |
| Holy Week gaps unconfirmed as suspensions | 2 | Open (consistent with Apr 2–4 holiday; numbering continuity supports it) |
| Chi-square below validity conditions; within-draw dependence | 2 | **Fixed**: exact Monte Carlo (§"Corrected statistics") |
| Pooled-games correlation; normal-approx p-values | 2 | **Fixed**: within-game z-scoring + permutation tests |
| Single response variable (mean/pool) | 2 | **Disclosed**: tests are blind to variance/parity/specific-number effects; confirmation family kept narrow deliberately |
| Retroactive test family ("forking paths") | 2 | **Fixed**: exploration set frozen, pre-registered confirmation protocol (§3b) |
| Sequential weekly testing inflates false positives | 2 | **Fixed**: scheduled task now tests confirmation set only with fixed family m=8 |
| Low power undisclosed | 2 | **Fixed**: power statement added |
| Draw time assumed exactly 21:00 PHT for all games | 3 | Open: games draw sequentially over the broadcast; attenuates covariate correlations slightly |
| Kp is planetary, not local Manila field; some values preliminary | 3 | Disclosed; local magnetometer data not freely available |
| EV inputs guessed (lower-tier prizes, ticket sales) | 3 | **Mitigated**: sensitivity analysis added; conclusion robust |
| Webpage picks seeded by date (implied date relevance) | 3 | **Fixed**: picks now pure random, label updated |

Standing limitations: results apply to Mar–Jun 2026 PCSO machine draws only; "null" means no moderate-to-large effect (see power); the unpopular-numbers heuristic is supported by international studies and the 433-split case but unvalidated against Philippine bet-distribution data (not published by PCSO).

## 8. References

- PCSO Search Lotto Results — https://www.pcso.gov.ph/SearchLottoResult.aspx
- PCSO Responsible Gaming — https://www.pcso.gov.ph/Games/ResponsibleGaming.aspx
- LottoPCSO history pages — https://www.lottopcso.com/ (6/42, 6/45, 6/49, 6/55, 6/58 history-and-summary)
- GFZ Potsdam Kp index — https://kp.gfz.de/ (CC BY 4.0)
- Cushing, D. & Stewart, D.I., "Applying constraint programming to minimal lottery designs" — https://arxiv.org/abs/2307.12430 ; journal version: https://link.springer.com/article/10.1007/s10601-024-09368-5
- U. Manchester press release — https://www.manchester.ac.uk/about/news/how-many-lottery-tickets-do-you-need-to-buy-to-guarantee-a-win-manchesters-mathematicians-find-the-answer/
- The Aperiodical explainer (27 tickets) — https://aperiodical.com/2023/07/27-tickets-that-guarantee-a-win-on-the-uk-national-lottery-but-what-prize/
- Wikipedia, "PCSO Lottery Draw" (procedures, odds, prizes, 433-winner event) — https://en.wikipedia.org/wiki/PCSO_Lottery_Draw
- BBC News, "Philippines lottery: Questions raised as hundreds win jackpot" (Oct 2022) — https://www.bbc.com/news/business-63126558
- Thorp, E. — roulette wearable computer (1961, with Shannon); Diaconis, P. — coin-flip bias; Stern, H. & Cover, T. — "Maximum entropy and the lottery" (split-risk EV analysis)

---
*Methodology note: every hypothesis was tested against real data with stated p-values; every claim above is reproducible from the CSVs in this folder. The project's conclusion is itself the scientific result: PCSO draws are statistically indistinguishable from uniform randomness across physical, astronomical, geomagnetic, and number-theoretic dimensions.*

## 9. Exploration batch 4 — harmonization instruments (Jun 11, 2026)

Registered before running (docs/REGISTRATION_BATCH4.md): three instruments from the
"harmonization bridges" — concentration/compressed-sensing exclusion
(`concentration_exclusion.py`), graphon cut-norm proxy (`graphon_cooccurrence.py`),
Szemerédi AP counts (`szemeredi_ap.py`). Free probability was *not* onboarded
(predicted same class as MP); RG already implemented. Full results:
docs/RESULTS_BATCH4.md. Headline: no new structure; the 6/55 #45 adjudicated anomaly
re-detected by two more correlated statistics (8th/9th flags, still one anomaly);
B1 measured *out* of the MP equivalence class (null-rho=+0.11 vs predicted >=0.90);
exclusion bounds shown vacuous at feasible n (~130-330 yrs for a 10% bound — logged
as a capability boundary); Ramsey-trap baselines (3.2-4.4 forced APs per hot set)
added to the failure-mode gallery. Confirmation arbiter: held-out draws >= 2026-06-12.
