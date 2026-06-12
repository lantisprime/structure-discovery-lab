# Theorem Synthesis — How the Instruments Interlock

Companion to RESEARCH_NOTES.md · Jun 11, 2026 · dataset: 776 validated draws, 5 games

This document does what no single test report can: it maps the **logical relationships
between the theorems** used in this project — which properties imply which, where each
instrument is blind, which instruments are secretly correlated, and why the joint verdict
is stronger than the sum of the individual ones.

---

## 1. One object, four faces of randomness

The hypothesis under test is a single mathematical object: the i.i.d. uniform process on
the C(P,6) combinations. But "random" decomposes into four mathematically distinct faces,
and each family of theorems interrogates one face:

| Face | Defining property | Theorem family | Instruments used |
|---|---|---|---|
| **Statistical** | marginal distribution is uniform | LLN, CLT, chi-square | frequency tests, bias ratios, scan statistic, rolling windows |
| **Dynamical** | future ⊥ past (order-0) | Markov theory, ergodic theory, Doob | overlap/stickiness, G-test, λ₂, Hurst, walk-forward models |
| **Algorithmic** | incompressible | Shannon source coding, Kolmogorov/Martin-Löf | LZMA/DEFLATE certificate, token-prediction β |
| **Cross-sectional / physical** | no collective modes, no spectra | Marchenko–Pastur, Wiener–Khinchin, Bak SOC | RMT eigenvalues, Fisher g, 1/f slope, avalanches |

The central fact organizing everything: **i.i.d. uniform is the unique process that is
simultaneously extremal on all four faces.** Each instrument measures a functional whose
extreme value is attained exactly at i.i.d. uniform:

- Entropy rate h = log₂C(P,6) bits/draw (maximum possible) — algorithmic face
- Every transition-matrix row identical, λ₂ = 0, relaxation = 1 draw — dynamical face
- Flat periodogram (α = 0), Hurst H = ½ — spectral face
- All eigenvalues inside the Marchenko–Pastur bulk — cross-sectional face
- All marginals at 6/P — statistical face

## 2. The implication lattice (what proves what)

The theorems are not independent claims; they form a one-way lattice:

```
                    i.i.d. uniform  (H0)
                          │ implies ALL of:
   ┌───────────┬──────────┼───────────┬─────────────┐
 uniform     order-0    flat        MP bulk      h = log2 C(P,6)
 marginals   (no memory) spectrum,  spectrum     (incompressible)
 (LLN)       (Markov)    H=1/2      (RMT)        (Shannon/Kolmogorov)
   │            │           │           │             ▲
   └────────────┴───────────┴───────────┴─────────────┘
        each individual property is implied by H0, but NONE
        of them individually implies H0 — EXCEPT the last:
        maximal entropy rate ⇔ i.i.d. uniform (the master property)
```

Key one-way implications, with the counterexamples that make them one-way:

1. **Uniform marginals ⇏ randomness.** A deterministic rotation through a fixed list of
   combinations has *perfect* chi-square forever yet is fully predictable. This is the
   blind spot of every frequency test — and the reason the Markov suite exists.
2. **Order-0 in one projection ⇏ order-0.** The tercile G-test sees only the draw-mean
   projection; a process could be memoryless in means yet dependent in parity. This is
   why multiple projections (stickiness per ball, overlap, λ₂) were run.
3. **No one-step memory ⇏ no memory.** A process can be pairwise independent at lag 1
   but dependent at lag 7. Hurst/R-S analysis and the spectral slope integrate over ALL
   lags (via Wiener–Khinchin: flat spectrum ⇔ δ-autocovariance ⇔ no correlation at any
   lag) — they generalize the Markov tests from lag 1 to lag ∞.
4. **Flat spectrum ⇏ independence.** Spectra capture only second moments; nonlinear
   dependence (e.g., variance clustering) is spectrally invisible. The compression
   certificate covers this: ANY computable dependence, linear or not, reduces entropy
   rate and admits compression (Shannon–McMillan–Breiman).
5. **The master implication (Martin-Löf / Kolmogorov).** "Random = passes every
   effective test" is not a metaphor; it is the definition. Incompressibility is the
   *conjunction* of all other properties: a frequency bias, a memory, a cycle, or a
   factor structure each constitute a description shorter than the data, i.e.
   compressibility. So the compression certificate is the weakest instrument in power
   (real compressors are crude) but the strongest in scope — it is the only single test
   whose null, if it could be evaluated exactly, would be *equivalent* to H0.

The practical consequence: **the instrument suite covers each other's blind spots in a
closed loop.** Frequency tests ⊥ permutation structure; Markov tests ⊥ marginals; spectra
⊥ nonlinearity; compression ⊥ nothing in principle, everything in practice (power);
RMT ⊥ time (it sees cross-sectional structure that all time-series tests marginalize away).

## 3. The decision-theory layer (theorems about what to DO)

Two theorems sit above the detection lattice and convert any verdict into action:

- **Doob's optional stopping theorem**: if the detection layer's verdict is "fair game,"
  then no betting/stopping strategy has positive expectation. It consumes the output of
  the lattice; it adds no detection power of its own.
- **Bernoulli/Kelly (St. Petersburg resolution)**: even when EV > 0, the growth-optimal
  stake is f* ≤ 1/C(P,6) of bankroll. Detection says *whether* an edge exists; Kelly says
  *how much* it would be worth. For this dataset: nothing, and ≤₱25 per ₱1B respectively.

Combinatorics (Cushing–Stewart covering designs) is the third action-layer result: it
bounds what *guarantees* are purchasable (≥13–26 tickets for a worthless 2-match) —
independent of whether the machine is biased at all.

## 4. Instrument correlation — the empirical map

Section 6f's cross-theorem detector measured the correlations between the per-ball
signals of five domains *within this dataset*. Two distinct kinds of correlation matter:

**(a) Structural correlation under H0** (instruments sharing raw data): frequency and
gap-variance signals correlate at r ≈ 0.6 under pure randomness, because a ball's hit
count mechanically determines how many gaps it contributes. Naively reading such
correlations as "joint signal" is a trap; the MC-calibrated detector absorbs them.
Observed max cross-domain couplings sat at or below their null medians (p = 0.09–0.93):
**no latent factor couples the domains beyond what arithmetic forces.**

**(b) Correlation of verdicts on an anomaly** — the project's best case study. The
2025 6/55 number-45 excess was flagged, in sequence, by: chi-square (p=0.003), max
frequency (rank 0.999), the walk-forward backtest (+2σ), pair affinity (p=0.043),
rolling-window persistence (p=0.002), and the recurrence-gap law (p=0.028). Six flags —
but **one anomaly**: every one of those statistics is a deterministic function of the
same 26 draw rows. Counting them as six discoveries would be the multiplicity error in
its most seductive form. The instruments that are *not* functions of hit counts told the
complementary story: stickiness saw nothing (the excess wasn't draw-to-draw clustered),
SOC saw nothing (no spectral or avalanche trace), the scan statistic priced the burst at
p=0.148 after look-elsewhere, and persistence analysis showed it spanning three quarters
before dying at the Feb 2026 era boundary. Synthesis: a real, verified, era-bounded
excess in the data; an unresolvable split between "1-in-7-years fluctuation" and
"transient equipment idiosyncrasy"; zero forward value either way. The pre-registered
confirmation test (m=9 family, p<0.0056) is the designated arbiter.

## 5. Results ledger (all instruments, final corrected values)

| # | Instrument (theorem) | Functional | H0 value | Observed | p (corrected basis) |
|---|---|---|---|---|---|
| 1 | Chi-square MC (LLN) | freq deviation | 0 | per game | 0.11–0.90 (3-mo), 0.10–0.61 (1-yr ex-6/55) |
| 2 | Covariate permutation (12 tests) | r | 0 | \|r\|≤0.10 | ≥0.18 |
| 3 | Number-theory metrics ×4 | counts | MC null | within noise | ≥0.18 |
| 4 | Markov T1–T4 (order-0 vs 1) | δ, G, λ₂ | 0 | δ∈[−.013,+.024], λ₂≤.12 | min 0.053 (≈expected min of 15) |
| 5 | Token prediction (cross-entropy) | β | 0 | +0.015 | CI ∋ 0 |
| 6 | Compression (Shannon) | bits vs H | ≥H | ≥H all games | one-sided pass |
| 7 | RMT (Marchenko–Pastur) | λ_max escape | 0 escapes | 0 escapes | — |
| 8 | Fisher g (Wiener–Khinchin) | max peak | flat | g≤0.068 | ≥0.33 |
| 9 | MC ensemble (50 statistics) | percentile ranks | U(0,1) | 4 extremes (2=#45) | KS≈0.05 indic. |
| 10 | Exit order / weekday / pairs / cross-game / scan | various | null | null | ≥0.043; scan 0.148 |
| 11 | Cross-theorem coupling | max \|r\| excess | null band | ≤ null median | 0.09–0.93 |
| 12 | SOC (Bak): α, avalanches, Hurst | 0, geom, ½ | white | α≤0.16, geom, Ĥ=null-typical | ≥0.09 |
| 13 | Rolling-window persistence | cross-window r | 0 | 6/55: +0.15 | **0.002** (the #45 cluster) |
| 14 | Payout backtest (hypergeometric) | 3+ matches | 11.4 | 14 | n.s.; −71% ROI |
| 15 | SOC scan (Bak): 1/f slope, avalanches, Hurst | α, tail, H | 0, geom, ½ | α=0.03–0.16, geom, Ĥ=null-typical | ≥0.09 |
| 16 | Power-law vs geometric (CSN MLE + Vuong) | Vuong z | <0 (geom) | gaps z=−35.3; avalanches z=−3.2 | decisive for geometric |
| 17 | Tracy–Widom universality check | skew(λ_max null) | +0.293 (TW-GOE) | +0.316 | consistent — universality governs the noise |
| 18 | Data collapse (5 games as system sizes) | scaling function F(s/⟨s⟩) | geometric 2^−(2x−1) | collapses, spread 0.21 | trivial fixed point identified |
| 19 | RG flow (block-mean kurtosis, k=1–16) | excess kurtosis flow | →0 (CLT fixed pt) | ≈0 at all k | already AT the fixed point |
| 20 | Binder cumulant (MC-calibrated) | U(W) | i.i.d. null curve | inside null CI at all W | pseudo-plateau = n≈4 estimator bias |
| 21 | Zipf rank-frequency | slope s | ~0.2 (sampling) | 0.21–0.28 | min p=0.017 n.s.; = chi-square in disguise |
| 22 | Taylor's law | exponent b | ~0.9 (binomial) | 0.3–1.3 | p≥0.27; no multiplicative clustering |
| 23 | First-digit laws | χ² to Benford / exact law | reject / fit | 1312 / 9.3 | follows the correct law, not the famous one |
| 24 | Lévy flights (CSN+Vuong on steps) | Vuong z | <0 (exp) | −9.4 | no anomalous diffusion |
| 25 | Coupon collector | cover time | MC CI | inside CI all games | i.i.d. coverage rate |
| 26 | Concentration exclusion (Hoeffding/MC band) | eps bound on \|p_i-6/P\| | ~0.15 (n=155) | 0.16-0.20 | bound vacuous at feasible n; #45 re-detected (batch 4) |
| 27 | Graphon cut-norm proxy (Lovász–Szegedy) | spectral norm, centered co-occ | MC null | 6/55: 32.74 | **0.0005** = #45 pair-affinity shadow; distinct class from MP (rho=+0.11) |
| 28 | Szemerédi AP3 (within-draw + hot-set) | AP counts | theorem-forced rate | all inside | >=0.011; Ramsey-trap baselines logged |
| 29 | Relational admission R1–R7 (E1–E8 controls) | FPR / power per family | FPR=α, power≥0.8 | FPR 0.010–0.083, power 1.00 ×7 | all calibrated; all ADMITTED (ADMISSION_RELATIONAL.md) |
| 30 | Subset-to-whole recovery curves (R6 protocol) | null-adjusted z vs k | physical series rise; lotto flat | tidal/moon z→+19.7/+19.3, Kp z→+3.65; lotto z∈[−0.40,+0.56] | lotto median p 0.34–0.64 at all k — entropy floor, relational form |
| 31 | Date-paired CCA, held-out ρ₁ (R3 protocol) | held-out ρ₁ vs shuffled pairing | draws-vs-physics null; tidal-vs-ephemerides positive | ρ₁=0.110 vs ρ₁=0.9977 | p=0.17 (null, replicates row 2) vs p=0.005 (mechanism known, positive control) |
| 32 | Cross-game co-occurrence spectra (R5, batch 5) | −spectral distance, std. top-10 eigs | independence across 10 pairs | all pairs in band | min p=0.05 > Šidák 0.0051 — NULL; 6/55 λ_max p=0.01 = #45 shadow (C9 traced: loading 0.439 on #45) |
| 33 | Delay-embedding H₁ topology (R4, batch 5) | max H₁ persistence vs perm. null | tidal/moon loop; lotto null | 1.124/1.201 vs 0.427 | p=0.01 floor ×2 vs p=0.25; tidal loop recoverable from 20% landmarks (median p=0.02); lotto flat |
| 34 | All-games symmetry (5 games × 4 relational tests) | recovery z, H₁ p, CCA p | all null, all games | all inside ±2z / p>0.05 | registered-and-confirmed; 6/45+6/55 presence z mildly + = traced λ_max shadows, charged per C9 |
| 35 | Sub-dataset partitions (batch 6: quarters + halves) | MMD p ×30, spectra p ×30, hot-corr ×5 | all null vs Šidák | min p .040/.070/.025 | joint NULL ×3; 6/55 half-corr raw flag traces to #45+#42 — same rows as rows 27/32, one anomaly |
| 36 | Pressure covariate (baseline + B7-1/2): recovery, seasons, CCA | z(k), MMD ×6, ρ₁ ×7 | pressure structured & seasonal; draws null | z→+10.5; 6/6 season pairs p=.005 (corrected); draws ρ₁≤0.26 | draws joint NULL (min p .03 > Šidák .0102); pressure↔sun/moon ρ₁=.567 p=.005 (mechanism) — pipeline positive controls on real data |
| 37 | Gromov–Wasserstein first real run (B7-3, gate passed) | GW distortion vs matched-Gaussian null | tidal↔moon align; lotto null | .023 vs null .103 | p=.05 floor (lunar mechanism); pressure↔lotto p=.30; pressure↔tidal anti-similar p=1.0 (structure ≠ shared structure). **Status: exploratory-only — n=200 gate later failed distribution calibration (row 38)** |
| 38 | Remediation R1 (expectation-free; ADVERSARIAL_REVIEW C1–C3, M1–M7) | presence-MC m=199, λ_max m=999, gates n=200, frozen power curves, 3-regime sensitivity, 3-split CCA, meta + design verifier + global ledger | claim-typed nulls, floor-compliant | see REMEDIATION_LOG.md | presence-MC null ×5 (min p=.23); λ_max: 6/55 **p=.0010** (survives ex-suspicious .0025) = sole corrected rejection; 6/45 flag opened at m=399 (.0100) closed at m=999 (.0150); GW null miscalibration → demoted; ledger: 173 tests, 6.9% ≤.05; design verifier PASS |
| 39 | Blind independent verification (separate agent, no expectations, no labels) | own tests, m=999 perms, 9 blinded series | exchangeable null | **9/9 concordance** | 4 physical series STRUCTURED, 5 lotto series NO STRUCTURE; half-corr replication 0.251/0.154 to 3 decimals — verdicts survive removal of experimenter and expectations |
| 40 | External blind methodology eval (structure_eval_set_v1, 68 units, key sealed, role-separated agents) | full registered battery, expectation-free | per-family Šidák + floor rule | **0 FP / 45 TN, 19/23 TP** | specificity 1.000, sensitivity .826, accuracy .941; 2 misses = family-correction absorption (visible as exploratory flags), 2 = instrument representation limits; GW G0 suppression covered by TDA |
| 41 | Registered rerun batch67_r2 (hash 2709deedb274f0f6, first G3 batch; haiku execute-only; src/core+src/domains) | b6_mmd m=1199 min_p=0.049; b6_spectra m=1199 min_p=0.036; b6_halves m=199 3 regimes (6/55 all 0.251/ex-susp 0.154/ver-only 0.177); b7_seasons m=399 6/6 p=0.0025; b7_cca 3-split sun-moon ρ₁ 0.403–0.567 all p=0.005; Kp all null; b7_gw G0 only | floor-compliant m, Šidák per family | all original verdicts resolution-stable | b6 joint NULL ×3; b7 seasons REJECT ×6 strengthened; pressure↔sun-moon REJECT ×3 splits strengthened; Kp NULL; GW G0 no claims; panel corrected to n=136 KS p=0.111, 8.8% ≤0.05 (double-count artifact KS p=0.027 resolved) — RESULTS_BATCH6_7_RERUN.md |

### 5b. Universality: the inversion that closes the physics face

Universality classes (the deep content of Per Bak's program) organize behavior **at**
critical points: there, exponents (τ, α, H) become independent of microscopic detail.
Two preconditions failed here, in order: (1) *criticality itself* — every tail is
exponential-family (Vuong z = −35.3 on n=4407 gaps), meaning a characteristic scale,
meaning the bulk phase, where universality has nothing to organize; (2) *measurability* —
the largest avalanche is 8, a 0.9-decade scaling range, below the ≥2 decades any exponent
estimate requires. So universality-class identification is not "not yet done"; it is
not attemptable on this system, by construction of the machine.

The inversion: universality governs this project from the *mathematical* side. The CLT
(Gaussian class) underwrites every z-score; the scan statistic's null lives in the
Gumbel extreme-value class; and the λ_max null of our binary row-constrained presence
matrices shows skewness +0.316 against the Tracy–Widom GOE universal constant ≈+0.293 —
microscopic details (discreteness, the 6-ones constraint) wash out exactly as TW
universality predicts. The lottery contains no critical system, but its randomness is
itself a universality phenomenon: the same limit laws would govern any other well-mixed
selection mechanism, which is precisely why these conclusions transfer beyond PCSO.

**Addendum (the user's counter-argument, conceded and executed):** universality
machinery does not require criticality — it identifies whichever fixed point the system
occupies. Running the full toolkit (rows 18–20): the five games' avalanche distributions
*do* collapse onto a single universal scaling function when rescaled — and that function
is the geometric law of the trivial fixed point; the RG flow of block statistics shows
the data already sitting at the Gaussian/CLT fixed point with nothing to renormalize;
and the Binder cumulant's apparent critical plateau at large windows reproduces exactly
in the i.i.d. null (small-sample bias — the second pseudo-critical artifact caught by
calibration, after Hurst). This upgrades the physics conclusion from "no criticality
found" to "fixed point positively identified as trivial/infinite-temperature" — the
strongest statement the universality framework permits about any system.

**Joint verdict**: one era-bounded, verified, non-recurring excess (6/55 #45, 2025);
everything else extremal exactly as i.i.d. uniform requires, with p-values *distributed*
as the null predicts (the meta-signature of true randomness). Methods casualties along
the way, all caught by calibration or review: 0.5-centered smoothing (manufactured a
backtest edge), degenerate KS under ties, uncalibrated Hurst bias, look-elsewhere on the
scan — each now documented as a worked example of how false discoveries are produced.

## 6. The one-sentence synthesis

Every theorem family measures a different functional that is extremal exactly at i.i.d.
uniform; this dataset sits at the extremum of all of them simultaneously, the anomalies
that appeared were correlated views of a single verified-but-expired excess, and the only
theorems with anything actionable to say are the decision-layer ones — Doob (no strategy),
Kelly (no stake), covering designs (no guarantee under 13 tickets).
