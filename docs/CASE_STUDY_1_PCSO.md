# Case Study 1 — PCSO Lottery Draws

**Framework version:** v2.1  
**Dataset:** 776 multi-source-validated observations, 5 games  
**Status:** complete — all planned faces run, anomaly adjudicated, external verifications done  
**Last updated:** Jun 11, 2026

---

## 0. Overview and rationale

The PCSO (Philippine Charity Sweepstakes Office) lottery draw corpus was chosen as the
laboratory's inaugural dataset for a principled reason: its ground truth is engineered.
A system *designed* to be structureless is the ideal instrument calibrator. Every
certificate that stays silent here is demonstrably honest when pointed at data where
structure is expected. Certificates that fired on this dataset were either real
anomalies (adjudicated) or estimator artifacts caught and documented as worked examples
of false-discovery prevention.

The study is negative by design: the framework's value is in its resistance to false
positives, not in finding them.

---

## 1. Dataset

| Property | Value | Source |
|---|---|---|
| Observations | 776 multi-source-validated draws | `datasets/pcso-lotto/DATASET.md` |
| Games | 6/58, 6/55, 6/49, 6/45, 6/42 | DATASET.md schema |
| Validation | multi-source (canonical + audited + provenance CSVs) | `datasets/pcso-lotto/` |
| Suspicious rows | 3 flagged 6/55 rows, pending adjudication against official records | `docs/REMEDIATION_LOG.md M4` |
| Era registry | ERA_REGISTRY in `src/domains/pcso_lotto.py`; era boundaries from known regime events | A5 |
| Holdout structure | confirmation family (m=9, α' = 0.0056) untouched; declared in DATASET.md | G5 reserve |

**Data-quality caveat:** the half-correlation verdict is data-quality-sensitive (drops
from p=0.05 at all rows to p=0.11 excluding 3 suspicious rows). All three-regime
sensitivity results (all / ex-suspicious / verified-only) are reported throughout.
The "ex-suspicious" regime governs published verdicts until adjudication is complete.

**Covariate datasets:**

| Dataset | Source | Caveat |
|---|---|---|
| Tidal (Manila) | `datasets/tidal-manila/` | — |
| Sun/moon ephemerides | `datasets/jpl-horizons-sun-moon/` | — |
| Geomagnetic Kp | `datasets/gfz-kp-geomagnetic/` | — |
| Atmospheric pressure (Manila) | `datasets/openmeteo-pressure-manila/` | single-source (ERA5/Open-Meteo); positive pressure claims gated until second source added |

---

## 2. Statistical face results

**Instrument: Chi-square + exact Monte Carlo** (KB card 2; ledger row 1)

Marginal frequency non-uniformity test (hot/cold balls). Asymptotic chi-square is invalid
at expected counts of 4.0–5.4 in these games (6-without-replacement inflation); replaced
by exact MC under the true mechanism.

Observed p-values: **0.10–0.90 across all games and periods** — no frequency anomaly at
any resolution. At the tested resolution (n = 155–776), any persistent per-ball bias
exceeding ε ≈ 0.15–0.20 is excluded with probability < 5% (exclusion instrument, ledger
row 26; caveat: ε is vacuous as an EV constraint at feasible n).

**Instrument: Scan statistics / look-elsewhere** (KB card 4; ledger row 10)

Kulldorff-style maximum windowed z-score over all numbers, window lengths, and games,
calibrated by MC over the full search space. Applied to the 6/55 #45 anomaly:

- Naive local p = 0.001 (before look-elsewhere correction)
- Global p = **0.148** after look-elsewhere correction — not significant at this resolution

This scan result is complementary to rolling-window persistence (row 13, p = 0.002),
which has a different alternative hypothesis. The two results are not in contradiction.

**Instrument: Multiple comparisons** (KB card 5; ledger rows throughout)

Equivalence-class accounting: the 2025 6/55 number-45 excess was flagged by **nine
correlated statistics** (|r| > 0.90 on simulated data ⇒ same class). It is one anomaly.
Family sizes used: m = 9 (confirmation battery), m = 15 (Markov family), m = 18
(scaling-law family).

---

## 3. Dynamical face results

**Instrument: Markov chains / order tests** (KB card 6; ledger row 4)

Order-0 vs order-1 likelihood-ratio G-test; overlap/stickiness; tercile G-test; |λ₂|
relaxation time. Estimated relaxation times: **1.05–1.14 draws**, consistent with the
simulated i.i.d. null. Minimum p across all 15 tests: **0.053** (the expected minimum
of 15 tests under H₀).

**Instrument: Hurst / R/S analysis** (KB card 7; ledger row 12)

Raw H-hat: **0.56–0.70** on lottery statistics. This matches the simulated i.i.d. null
exactly — the R/S estimator is biased upward on short series (pseudo-critical artifact 1
of 2). After calibration against a same-length i.i.d. null: **no long-range memory found.**

**Instrument: Wiener–Khinchin / Fisher g** (KB card 12; ledger row 8)

Flat periodogram test for hidden periodicities. All games: **p ≥ 0.33** — no periodic
structure. A flat spectrum certifies zero autocorrelation at all lags (second-order only);
the compression certificate covers nonlinear dependence the spectrum misses.

---

## 4. Algorithmic face results

**Instrument: Shannon / Kolmogorov compression** (KB card 10; ledger row 6)

Source-coding entropy floor: **H = log₂ C(P,6) = 22.3–25.3 bits/draw** across PCSO
games — this entropy floor makes prediction impossible in principle. Practical test:
raw DEFLATE compressed sizes matched the simulated null — **no compressible structure
found.**

**Instrument: Covering designs** (KB card 15; ledger row — combinatorial bound)

Partition-based estimates for PCSO pools: **roughly 13–26 tickets** to guarantee a
(worthless) 2-match across game sizes. Disjoint-pair rule: two disjoint tickets give
jackpot probability exactly 2/C(n,6) — coverage cannot create expected value.

---

## 5. Cross-sectional / physical face results

**Instrument: Marchenko–Pastur / Tracy–Widom** (KB card 11; ledger rows 7, 17)

RMT eigenvalue bulk applied to number co-occurrence correlation matrices: **zero
eigenvalues escape above the noise bulk in all games** (ledger row 7).

Meta-check: the simulated null distribution of λ_max had skewness **+0.316** versus the
universal TW-GOE constant **≈+0.293** (ledger row 17) — universality governs the lab's
own noise floor, not the lottery mechanism.

**Instrument: Power laws / CSN / Zipf / Taylor / Benford** (KB card 14; ledger rows 16, 21–25)

- Inter-occurrence gaps favor geometric over power law: **Vuong z = −35.3** on n = 4,407
  gaps (ledger row 16) — decisive against SOC-style and Lévy-flight mechanisms
- Taylor b ≈ **0.9** (without-replacement-consistent, ledger row 22; p ≥ 0.27)
- Naive Benford rejected at χ² = **1312**; exact uniform-derived digit law fits at
  χ² = **9.3** (ledger row 23) — correct null matters
- Lévy-flight step Vuong z = **−9.4** (ledger row 24)

**Instrument: Szemerédi / Furstenberg APs** (KB card 17; ledger row 28)

Two-sided MC-calibrated AP counts within draws and hot sets: **all inside simulated CI
at p ≥ 0.011** (ledger row 28). No additive structure found.

**Instrument: Graphons / cut norm** (KB card 18; ledger row 27)

6/55 spectral norm: **32.74, p = 0.0005** — identified as the #45 pair-affinity shadow
(C9 row-trace: loading **0.439** on #45), one anomaly not a second detection.
Equivalence-class measurement against MP λ_max confirmed ρ = **+0.11**.

**Instrument: Concentration / sparse recovery** (KB card 19; ledger row 26)

Simultaneous Hoeffding/MC band at n = 155–776: any persistent per-ball bias exceeds
**ε ≈ 0.15–0.20** with probability < 5%. Lasso soft-threshold (null-calibrated λ)
recovers **empty support** on ≥ 99% of null replicates. The #45 number was re-detected
in batch 4 via this instrument. Caveat: ε is vacuous at feasible n as an EV constraint.

---

## 6. Per Bak / SOC & universality — full narrative (card 13)

**Sources:** `docs/kb/per-bak-soc-universality.md`, `docs/THEOREM_SYNTHESIS.md §5b`,
ledger rows 12, 15, 16, 17, 18, 19, 20.

### SOC signature suite

SOC (Bak, Tang, Wiesenfeld 1987) asserts that certain driven dissipative systems
self-tune to a critical point, displaying power-law avalanche distributions P(s) ~ s^−τ,
1/f^α power spectra, and long-range correlations H ≠ 0.5.

Observed results on this dataset:

- **1/f spectral slope:** observed α = **0.03–0.16**, against the white-noise null α = 0
  and far from the critical α ≈ 1. All games p ≥ **0.09**.
- **Avalanche size distributions:** geometric, not heavy-tailed. Vuong z = **−3.2**
  favoring geometric (ledger row 16); the largest avalanche was **8**, giving a
  **0.9-decade** scaling range — below the ≥ 2 decades required for any reliable
  exponent estimate.
- **Hurst:** raw H-hat **0.56–0.70** = i.i.d. null after calibration (pseudo-critical
  artifact 1; see card 7). No long-range memory found.

### Two failed preconditions for universality-class identification

1. **Criticality itself:** every tail is exponential-family. Vuong z = **−35.3** on
   n = 4,407 gaps (ledger row 16) decisively favors geometric — a characteristic scale,
   meaning the bulk phase, where universality has no critical fixed point to organize.
2. **Measurability:** 0.9-decade scaling range is below the ≥ 2 decades any exponent
   estimate requires. Universality-class ID is not "not yet done"; it is not
   attemptable on this system by construction.

### The counter-argument: running the full RG toolkit anyway

The owner's counter-argument — that universality machinery does not require criticality,
it identifies whichever fixed point the system occupies — was conceded and executed
(source: `docs/THEOREM_SYNTHESIS.md §5b`). Results (ledger rows 18–20):

- **Data collapse** (ledger row 18): the **five games' avalanche distributions**, treated
  as five system sizes, collapse onto a single universal scaling function — the geometric
  law of the trivial fixed point — with **maximum spread 0.21** across all five ensembles.
- **RG flow** (ledger row 19): block-mean kurtosis tracked at k = 1–16 shows excess
  kurtosis **≈ 0 at all k** — the data is already AT the Gaussian/CLT fixed point; there
  is nothing to renormalize.
- **Binder cumulant** (ledger row 20): apparent pseudo-plateau at large window sizes
  initially mimicked a critical crossing. Null calibration against simulated i.i.d.
  draws of identical length showed the plateau reproduced exactly — **n ≈ 4-window
  estimator bias**, pseudo-critical artifact 2 of 2. Inside null CI at all window sizes.

### The inversion: universality governs the lab's instruments

- **Tracy–Widom:** λ_max null skewness **+0.316** vs TW-GOE universal constant **+0.293**
  (ledger row 17) — microscopic details wash out as TW universality predicts.
- **CLT / Gaussian class:** underwrites every z-score; block-mean kurtosis flows to the
  Gaussian fixed point (ledger row 19).
- **Gumbel extreme-value class:** governs the scan statistic's null.

### Verdict

The verdict upgrades from "no criticality found" to **"fixed point positively identified
as trivial / infinite-temperature"** — the strongest statement the universality framework
permits about any system. The lottery contains no critical system, but its randomness is
itself a universality phenomenon: the same limit laws govern any other well-mixed
selection mechanism, which is why these conclusions transfer beyond PCSO.

---

## 7. Relational face results

**Sources:** `docs/RESULTS_RELATIONAL_FIRSTRUN.md`, `docs/RESULTS_BATCH5.md`,
`docs/RESULTS_BATCH6.md`, `docs/RESULTS_PRESSURE.md`; ledger rows 29–40.

### Recovery curves (card 25 / R6)

Subset-to-whole recovery protocol (k-NN on the time index, within-series permutation
null, 10 seeds × m = 49):

- **Tidal series:** z → **+19.7** at 40% subset
- **Moon series:** z → **+19.3** at 40% subset
- **Kp geomagnetic:** z → **+3.65** at 40% subset
- **All 5 lottery games:** flat — lotto median p **0.34–0.64** at every k

The physical-series rises are the registered positive controls confirming the pipeline
can detect structure that exists. The flat lottery curves are the relational form of the
entropy floor (ledger row 30).

### Cross-game: 10 game pairs null (card 24 / R5)

Pairwise co-occurrence spectra (m = 99) across all 10 PCSO game pairs: min pair
p = **0.05** > Šidák threshold **0.0051**. No two games share co-occurrence community
structure beyond independent constrained-uniform generation. The 6/55 λ_max p = 0.01
traces to the #45 pair-affinity shadow (C9 row-trace: loading 0.439 on #45) — same
equivalence class, one anomaly. Source: `docs/RESULTS_BATCH5.md B5-A`.

### Partition tests: 65 tests null (card 20 / R1)

Batch 6 partition tests (MMD ×30, spectra ×30, half-corr ×5) across quarters and halves
of all games: joint null across all three families (min p **0.040 / 0.070 / 0.025**, all
> respective Šidák thresholds). The 6/55 half-correlation raw flag traces to the same
#45/#42 driving rows as ledger rows 27/32 — one anomaly per C9, no additional evidence.

### Covariate CCA: null (card 22 / R3)

Per-game date-paired CCA of draw features vs atmospheric pressure, vs solar/lunar
ephemerides, vs Kp geomagnetic (multi-split, 3 split points): all games null, joint null
(min CCA p = **0.030** > Šidák **0.0102**). Per-split excursions (p = **0.04–0.10**)
appear and vanish across splits — demonstrating split noise. Source:
`docs/RESULTS_PRESSURE.md`.

**Positive control confirmed — tidal ↔ ephemerides mechanism:** date-paired CCA
(R3 protocol, shuffled-pairing null, m = 199), held-out ρ₁ = **0.9977**, p = **0.005**
(floor). This verifies the pipeline on a known mechanism (tidal columns are derived from
the ephemerides). Source: `docs/RESULTS_RELATIONAL_FIRSTRUN.md §3`.

### TDA / persistence distances (card 23 / R4)

Delay-embedded topology: H₁ loops detected in structured tidal series (max H₁
persistence **1.124** vs null **0.427**; p = **0.01** floor), flat for lotto (max
persistence **0.427**, p = **0.25**). Tidal loop recoverable from 20% landmarks (median
p = **0.02**). All lotto null.

### GW alignment (card 21 / R2) — exploratory only (G0)

First real run (ledger row 37): tidal ↔ moon align (p = **0.05** floor); pressure ↔
lotto null (p = **0.30**). Status exploratory-only pending null redesign: FPR 0.055 at
n=200 gate confirmed but p-distribution was non-uniform (lattice χ² p = **0.002**).

### Matrix completion (card 26 / R7)

Flat recovery curve on lottery draw-history matrices — on i.i.d. data, SoftImpute sits
on the null line. This is the registered expected outcome from the entropy floor. Admitted;
FPR calibrated, power demonstrated on planted low-rank data (ledger row 38).

---

## 8. The #45 anomaly — full adjudication record

The 2025 6/55 number-45 excess is era-bounded, resolution-stable, and partially
data-quality-sensitive. Full disposition (source: `docs/REMEDIATION_LOG.md M3, M4`):

- **λ_max co-occurrence statistic:** p = **0.0010** at m = 999 (the sole corrected
  rejection in the λ_max family). Survives ex-suspicious at p = **0.0025** at m = 399 —
  the #45 shadow is **not** a data artifact.
- **Half-correlation statistic:** drops from **0.251** (all rows) to **0.154**
  (ex-suspicious 3 rows), p changing from **0.05** to **0.11** — **data-quality-sensitive**.
  Source: `docs/REMEDIATION_LOG.md M4`; `results/independent_verification.json`.
- **Scan statistic look-elsewhere:** p = **0.148** (not significant at tested resolution).
- **Rolling-window persistence:** p = **0.002**. Different alternative hypothesis from
  the scan; not a contradiction.
- **Era boundary:** the excess spans three quarters before dying at the Feb 2026 boundary.
- **Graphon / spectral norm shadow:** 6/55 spectral norm p = 0.0005, traced to #45
  pair-affinity (loading 0.439 on #45) — same equivalence class as λ_max row per C9.
- **PENDING:** adjudication of the 3 suspicious rows against PCSO official records
  (needs external source access).
- **Pre-registered confirmation test** (m = 9 family, α' = 0.0056) is the designated
  arbiter for forward-looking persistence; exploration cannot confirm.

**The nine-flags-one-anomaly resolution:** A3 equivalence-class accounting — nine
statistics flagged the #45 excess; |r| > 0.90 on simulated data confirmed they are one
class. One anomaly, not nine.

**The 6/45 λ_max watch item:** the 6/45 λ_max flag opened at m = 399 at p = **0.0100**
(exactly at the Šidák threshold) and was closed at m = 999 at p = **0.0150** — above
the threshold. The two estimates are statistically compatible; the higher-resolution one
governs. Disposition: **exploratory watch only**. This sequence — flag opened by a
borderline estimate, closed by the floor rule it triggered — is documented as the worked
example of why the permutation floor rule exists.

---

## 9. External validations using this dataset

### Blind 9-series verification (G4)

Source: `results/independent_verification.json`, `docs/REMEDIATION_LOG.md C2`.

A separate agent, barred from lab code, documentation, and any prior results, was given
9 standardized series with neutral names and no dates. The agent implemented its own
test suite and applied its own decision rule (Bonferroni 0.05/4 across 4 statistics, or
≥ 2 tests with raw p < 0.05).

Result: **9/9 concordance** — all 4 physical series returned STRUCTURED, all 5 lotto
series returned NO DETECTED STRUCTURE.

Numerical replication: 6/55 half-correlation **0.251** (all rows) / **0.154**
(ex-suspicious) matched the lab's published values to 3 decimal places. Conducted
expectation-free.

### Sensitivity replication

The three-regime sensitivity results (all / ex-suspicious / verified-only) are documented
in `docs/REMEDIATION_LOG.md M4`. The half-correlation movement from 0.251 to 0.154 (and
p from 0.05 to 0.11) on removal of the 3 suspicious rows was independently replicated in
the blind verification above. "At the tested resolution" applies throughout: all
sensitivity conclusions are bounded by n = 155–776.

---

## 10. Decision layer

**Doob gate (card 8):** all detection instruments null ⇒ the supermartingale condition
holds ⇒ no betting layer is reachable. Doob gate: **closed.**

**Expected value (card 16; ledger row 14):**

Hypergeometric tier EV decomposition, 20% Philippine tax on prizes above threshold,
Poisson co-winner split E[J/(1+K)] where K ~ Poisson(λ).

Observed EV: **≈ PHP 0.17–0.31 per PHP 1** at current jackpots — negative. Break-even
jackpots computed per game with sensitivity analysis over sales, tax, and popularity
assumptions.

Payout-relevant backtesting was decisive: the Markov model's proxy metrics (match-count)
appeared favorable until prize-weighting showed **−71% ROI** (ledger row 14).

**Kelly sizing (card 9):**

Win probability p = 1/C(n,6), so f* ≤ 1/C(n,6) ≈ **10⁻⁷–10⁻⁸**.

A mandatory PHP 25 minimum ticket is Kelly-consistent only with a bankroll of order
C(n,6) × 25 ≈ **PHP 1 billion** — anyone with less is structurally overbetting regardless
of edge sign.

Decision ordering: Doob gates → EV measures → Kelly sizes. All detection instruments
null ⇒ f* = 0.

**Decision-grade (G6):** the refusal decision (no betting edge) — asymmetric: declining
to act requires less evidence than acting; rests on Doob + entropy floor + uniformly null
G2–G4 evidence.

---

## 11. Application layer

`lotto_picker.html` — derived-values interface: combinatorial odds, entropy bounds,
EV/Kelly, decision-theory-compliant output.

A scheduled task (`pcso-weekly-update`, Wednesdays) appends validated observations and
runs only the registered confirmation family (m = 9, α' = 0.0056).

`PCSO_Lotto_Analysis_Mar-Jun_2026.xlsx` — interactive workbook.

---

## 12. Ethics note

This case study is a negative-result study by design. It neither predicts nor claims
to predict lottery outcomes (entropy floor above). The application layer prices tickets
honestly (expected cost approximately PHP 17–20 per PHP 25) and links PCSO
responsible-gaming resources. Nothing in this repository is financial advice; the
framework informs decisions, humans make them.

The framework's design choices are explicitly anti-discovery-bias: the four-casualties
record, the GW demotion, the 6/45 flag closure, and the three-regime sensitivity
reporting are all published because the lab's value is in its resistance to false
positives, not in finding them.

---

## 13. Open items specific to this case study

1. **Suspicious-row adjudication:** the 3 flagged 6/55 rows need comparison against PCSO
   official records. Until resolved, the half-corr verdict carries the
   "data-quality-sensitive" caveat.
2. **Pressure second source:** the Manila atmospheric pressure dataset is single-source
   (ERA5/Open-Meteo); a second source (PAGASA/NAIA) would remove the single-source gate
   on any positive pressure claim.
3. **Confirmation family:** held-out (m = 9, α' = 0.0056); current grade G5 = none.
   The `pcso-weekly-update` task appends observations; forward-looking confirmation
   requires no additional intervention.

---

## 14. Links to results documents and ledgers

| Document | Contents |
|---|---|
| `docs/RESEARCH_NOTES.md` | full evidence log: every test, p-value, correction, adversarial-review trail |
| `docs/RESULTS_RELATIONAL_FIRSTRUN.md` | relational batch 1: recovery curves, CCA, positive controls |
| `docs/RESULTS_BATCH4.md` | batch 4: presence-recovery, λ_max reruns |
| `docs/RESULTS_BATCH5.md` | batch 5: cross-game spectra, delay topology |
| `docs/RESULTS_BATCH6.md` | batch 6: partition tests (65 tests) |
| `docs/RESULTS_PRESSURE.md` | pressure covariate CCA and seasonal tests |
| `docs/THEOREM_SYNTHESIS.md §5` | 40-row results ledger: instrument, functional, H₀ value, observed, corrected p |
| `results/commitment_ledger.txt` | append-only hash ledger (3 snapshots + blind-eval chain) |
| `results/run_ledger.jsonl` | 10 run records with executor identities |
| `results/multiplicity_ledger.jsonl` | 173 real-data test rows |
| `results/meta_uniformity.json` | global meta-uniformity panel (KS p = 0.385) |
| `results/independent_verification.json` | blind 9/9 concordance + numerical replication |
| `results/blind_eval_score.md` | 68-unit methodology benchmark (for framework-level validation) |
| `datasets/pcso-lotto/` | DATASET.md card + canonical/audited/provenance CSVs |
| `datasets/tidal-manila/` | covariate dataset |
| `datasets/jpl-horizons-sun-moon/` | covariate dataset |
| `datasets/gfz-kp-geomagnetic/` | covariate dataset |
| `datasets/openmeteo-pressure-manila/` | covariate dataset (single-source caveat) |

---

*Case Study 1 · PCSO lottery draws · 776 observations, 26 instrument families,
40 ledger rows, 173 real-data tests, 0 exploitable patterns, 1 fully adjudicated
anomaly, 4 estimator artifacts caught and documented, 9/9 blind independent
verification.*
