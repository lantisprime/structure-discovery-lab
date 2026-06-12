# Blind Evaluation Scoring Report — structure_eval_set_v1

**Scored by**: independent-verifier agent (sonnet tier)  
**Date**: 2026-06-11  
**Verdicts file**: `results/blind_eval_verdicts.json`  
**Ledger entry checked**: `results/commitment_ledger.txt`

---

## 1. Tamper Check

Commitment ledger entry:
```
# blind-eval VERDICTS committed BEFORE unsealing 2026-06-11T08:17:07.649550Z
1d0a4d3ed4d2dd4d  results/blind_eval_verdicts.json
```

Recomputed SHA-256 truncated to 16 hex digits:
```
1d0a4d3ed4d2dd4d
```

**Match: YES.** The verdicts file is unaltered since it was committed to the ledger before the answer key was unsealed.

---

## 2. Ground Truth Summary (from answer key)

The eval set contains 14 named dataset objects. After mapping their expected behaviors onto the 68 registered claim units, the truth distribution is:

| Category | Count |
|---|---|
| True-STRUCTURED claim slots | 23 |
| True-NULL claim slots | 45 |
| **Total registered claims** | **68** |

**True-STRUCTURED slots** (claims where ground truth requires a STRUCTURED verdict):

| Claim | Ground truth basis |
|---|---|
| DRAW-MARGINAL-B | `draws.B`: numbers 17 and 42 upweighted in first half only |
| DRAW-MEMORY-C | `draws.C`: order-1 memory; retains 2 previous numbers with p=0.76 |
| DRAW-SUBSET-C | `draws.C`: same order-1 memory makes subsets recoverable |
| DRAW-STATION-B | `draws.B`: first-half-only bias; half-vs-half deviation should be non-stationary |
| DRAW-CROSS-D\|E | `draws.D` and `draws.E` share `z_common` latent; paired CCA expected positive |
| DRAW-SENSOR-D | `draws.D` linked to `z_common`; `sensor_01` is its noisy proxy |
| DRAW-SENSOR-E | `draws.E` same mechanism |
| SENSOR-STRUCT-sensor_01 | `sensor_01`: noisy proxy for `z_common` |
| SENSOR-STRUCT-sensor_02 | `sensor_02`: periodic proxy related to `z_common` cycle |
| SENSOR-STRUCT-sensor_04 | `sensor_04`: regime step aligned with first/second half |
| SERIES-RECOVERY-S1 | `series.S1`: periodic cycle; subset recovery expected positive |
| SERIES-RECOVERY-S2 | `series.S2`: related periodic cycle; same |
| SERIES-RECOVERY-S4 | `series.S4`: regime/changepoint; "subset recovery moderate" per key |
| SERIES-TDA-S1 | `series.S1`: periodic cycle; delay-embedding H1 loop expected |
| SERIES-TDA-S2 | `series.S2`: related periodic cycle; topological loop expected |
| SERIES-PAIR-S1\|S2 | `series.S1` and `series.S2`: same periodic structure; cross-series relation expected |
| SERIES-SEGMENT-S4 | `series.S4`: regime/changepoint; cross-quarter MMD expected positive |
| CLOUD-TDA-X | `cloud.X`: noisy circle in 2D; H1 loop expected |
| CLOUD-TDA-Y | `cloud.Y`: same circle geometry embedded in 5D, row-shuffled; H1 loop expected |
| GRAPH-COMMUNITY-A | `graph.A`: 4-community SBM; Laplacian spectrum clustered |
| GRAPH-COMMUNITY-B | `graph.B`: 4-community SBM; same |
| GRAPH-PAIR-A\|B | `graph.A` and `graph.B`: both SBMs; spectral similarity expected |
| MATRIX-M1 | `matrix.M1`: rank-3 plus noise; low-rank completion beats null |

---

## 3. Confusion Matrix — Overall

| | Lab: STRUCTURED | Lab: NULL |
|---|---|---|
| **Truth: STRUCTURED** | 19 (TP) | 4 (FN) |
| **Truth: NULL** | 0 (FP) | 45 (TN) |

**Overall: TP=19, TN=45, FP=0, FN=4**  
**Sensitivity**: 19/23 = **0.826**  
**Specificity**: 45/45 = **1.000**  
**PPV (precision)**: 19/19 = **1.000**  
**NPV**: 45/49 = **0.918**  
**Accuracy**: 64/68 = **0.941**

---

## 4. Confusion Counts per Claim Family

| Family | TP | TN | FP | FN | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| DRAW-MARGINAL | 1 | 4 | 0 | 0 | 1.00 | 1.00 |
| DRAW-MEMORY | 1 | 4 | 0 | 0 | 1.00 | 1.00 |
| DRAW-STATION | 0 | 4 | 0 | 1 | 0.00 | 1.00 |
| DRAW-SUBSET | 1 | 4 | 0 | 0 | 1.00 | 1.00 |
| DRAW-CROSS | 0 | 9 | 0 | 1 | 0.00 | 1.00 |
| DRAW-SENSOR | 2 | 3 | 0 | 0 | 1.00 | 1.00 |
| SENSOR-STRUCT | 3 | 1 | 0 | 0 | 1.00 | 1.00 |
| SERIES-RECOVERY | 3 | 1 | 0 | 0 | 1.00 | 1.00 |
| SERIES-TDA | 1 | 2 | 0 | 1 | 0.50 | 1.00 |
| SERIES-PAIR | 0 | 5 | 0 | 1 | 0.00 | 1.00 |
| SERIES-SEGMENT | 1 | 3 | 0 | 0 | 1.00 | 1.00 |
| CLOUD-TDA | 2 | 1 | 0 | 0 | 1.00 | 1.00 |
| GRAPH-COMMUNITY | 2 | 1 | 0 | 0 | 1.00 | 1.00 |
| GRAPH-PAIR | 1 | 2 | 0 | 0 | 1.00 | 1.00 |
| MATRIX | 1 | 1 | 0 | 0 | 1.00 | 1.00 |
| **TOTAL** | **19** | **45** | **0** | **4** | **0.826** | **1.000** |

---

## 5. Every Miss — False Negatives (Truth STRUCTURED, Lab NULL)

### FN-1: DRAW-STATION-B
- **Lab verdict**: NULL (p=0.0575, corrected α=0.0102)
- **Ground truth**: `draws.B` has a transient first-half-only marginal bias on numbers 17 and 42. The DRAW-STATION statistic (half-vs-half per-number deviation correlation) is precisely the instrument designed to detect this era shift.
- **Truth quoted**: *"type: transient_era_bias; biased_numbers: [17, 42]; era: first_half_only; expected: frequency and stationarity/era tests positive; no persistence in second half"*
- **Analysis**: p=0.0575 misses the family-corrected threshold (Sidak 5-unit α'=0.0102) by a factor of ~5.6. The signal is real but weak enough that the correction absorbs it at m=399. Appears in exploratory_flags as a near-miss. This is a genuine sensitivity shortfall — the Sidak penalty for 5 stream units against moderate bias strength puts the signal below detection.

### FN-2: DRAW-CROSS-D|E
- **Lab verdict**: NULL (p=0.0075, corrected α=0.0051)
- **Ground truth**: `draws.D` and `draws.E` both respond to the shared `z_common` latent variable. The DRAW-CROSS statistic (held-out CCA ρ₁, date-paired) is the correct instrument.
- **Truth quoted**: *"type: paired_latent_sum_relation; shared_latent: z_common; expected: date-paired CCA/correlation with sensor_01 and with each other positive; shuffled-pairing null should kill relation"*
- **Analysis**: p=0.0075 misses α'=0.0051 (Sidak 10-unit cross-pair family) by a factor of ~1.5. The 10-unit family size (all stream pairs) is the direct cause. The underlying signal IS detected by DRAW-SENSOR-D and DRAW-SENSOR-E (both STRUCTURED), confirming z_common is recoverable. This miss reflects a registration choice (10-unit cross-pair family) that sets a tighter threshold than the signal supports. Appears in exploratory_flags.

### FN-3: SERIES-TDA-S2
- **Lab verdict**: NULL (p=0.995, max_h1=0.298 vs null_q95=0.572)
- **Ground truth**: `series.S2` is "a different view of related periodic cycle" with expected "topological loop."
- **Truth quoted**: *"truth: different view of related periodic cycle; expected: subset-to-whole positive; cross-series relation with S1; topological loop"*
- **Analysis**: The lab's delay-embedding (τ=3, d=3) finds max_h1=0.298, well below the null 95th percentile (0.572), giving p=0.995 — effectively anti-signal. SERIES-RECOVERY-S2 correctly returns STRUCTURED (p=0.005), confirming the periodic structure is detectable by recovery. The TDA failure implies the chosen delay parameters do not form a persistent H1 loop in S2's particular encoding of the cycle (possibly phase-shifted or nonlinearly transformed relative to S1). No near-miss; this is a clean instrument-specific null despite real underlying structure.

### FN-4: SERIES-PAIR-S1|S2
- **Lab verdict**: NULL (p=0.7462, |Spearman ρ|=0.316)
- **Ground truth**: `series.S2` is a "different view of related periodic cycle"; key expects "cross-series relation with S1."
- **Truth quoted**: *"expected: subset-to-whole positive; cross-series relation with S1; topological loop"*
- **Analysis**: Absolute Spearman ρ=0.316 at p=0.7462 under the circular-shift null (461 exhaustive shifts). The circular-shift null preserves each series' own autocorrelation; if S2 is a phase-shifted or nonlinear view of S1, the time-domain rank correlation is destroyed by the phase offset while the null also shifts — meaning neither the observed statistic nor the null knows where the cycles align. This is an instrument-specific miss: the SERIES-PAIR statistic (time-domain Spearman) cannot detect relations that are periodic but phase-indeterminate.

---

## 6. Coverage Gaps

Planted structures for which the lab has NO registered claim capable of issuing a STRUCTURED verdict in principle. These are **not** scored as FN; they represent scope limitations of the registered claim set.

### Gap-1: Row/number attribution for draws.B (numbers 17 and 42)
The answer key specifies: *"row/number trace to 17 and 42."* No registered claim tests for identity of specific biased numbers. DRAW-MARGINAL-B correctly returns STRUCTURED (frequency test confirms bias), but no claim asks which numbers carry the bias. Sub-inference capability not registered.

### Gap-2: CLOUD-GW cross-geometry verdict
The answer key confirms that `cloud.X` and `cloud.Y` share the same circular latent geometry. CLOUD-GW-X|Y scored p=0.01 — a real signal — but carries a standing G0 exploratory-only flag established pre-run and recorded in the registration. The instrument correctly sensed the signal but cannot issue a verdict without first graduating from G0. CLOUD-TDA-X and CLOUD-TDA-Y (both STRUCTURED) cover the detection; GW remains a blocked secondary instrument.

### Gap-3: sensor_04 x draws.B era-detection link
The key notes sensor_04 is "a regime step aligned with the first/second half" and "may help detect B era split." No registered DRAW-SENSOR-B claim sub-tests sensor_04 specifically against stream B's era. The DRAW-SENSOR family uses a pooled sensor panel CCA; individual sensor x stream links are not separately registered.

### Gap-4: sensor_02 x draws.D/E individual link
The key predicts "weaker positive with D/E" for sensor_02. SENSOR-STRUCT-sensor_02 confirms sensor_02 has periodic structure (STRUCTURED). DRAW-SENSOR-D/E confirm D and E respond to the panel (STRUCTURED). However, no individual sensor_02 x D/E claim is registered; the per-sensor attribution within the panel is not resolvable from the registered claims.

---

## 7. Exploratory Flags vs Ground Truth

| Flag | Raw p | True state | Assessment |
|---|---|---|---|
| DRAW-STATION-B | 0.0575 | STRUCTURED | Near-miss: real signal below corrected threshold (FN-1) |
| DRAW-SUBSET-D | 0.0125 | NULL | Noise excursion on null data |
| DRAW-SUBSET-E | 0.0175 | NULL | Noise excursion on null data |
| DRAW-CROSS-A\|B | 0.0125 | NULL | Noise; A is pure uniform |
| DRAW-CROSS-A\|C | 0.0913 | NULL | Noise excursion |
| DRAW-CROSS-B\|C | 0.0175 | NULL | Noise; no B-C planted dependency |
| DRAW-CROSS-B\|E | 0.025 | NULL | Noise excursion |
| DRAW-CROSS-D\|E | 0.0075 | STRUCTURED | Near-miss: real signal (FN-2); missed α' by factor 1.5 |
| SERIES-PAIR-S3\|S4 | 0.0759 | NULL | Noise; S3 is iid |
| GRAPH-PAIR-A\|C | 0.095 | NULL | Noise; C is ER control |
| MATRIX-M2 | 0.030 | NULL | Noise; M2 is iid Gaussian |
| CLOUD-GW-X\|Y (G0) | 0.010 | STRUCTURED | Real signal; suppressed by standing G0 instrument flag |
| CLOUD-GW-X\|Z (G0) | 0.260 | NULL | Correct null |
| CLOUD-GW-Y\|Z (G0) | 0.180 | NULL | Correct null |

**Summary**: 2 of 14 flags are near-misses on real planted structure (both scored FN above). 1 flag is a suppressed real signal (GW, G0 flag). 11 flags are noise excursions on null data that correctly stayed below verdict threshold — the FP rate on null excursions is zero.

---

## 8. Granularity Mismatch Notes

**DRAW-SUBSET-C** (scored TP): The key primarily designates `draws.C` as "Markov/overlap/stickiness positive" (DRAW-MEMORY family). DRAW-SUBSET uses k-NN recovery of draw-sum values, a structurally different claim. The TP is valid — the order-1 memory mechanism plausibly creates recoverable temporal structure in draw sums — but should be understood as secondary confirmation of memory rather than an independent detection. Both DRAW-MEMORY-C and DRAW-SUBSET-C return STRUCTURED and agree with truth.

**SERIES-TDA-S4** (scored TN): Key says "no clean loop" for S4. Lab returns NULL (p=1.0, max_h1=0.135 vs null_q95=0.85). SERIES-SEGMENT-S4 is separately STRUCTURED. Together these correctly characterize S4: regime shift present (SEGMENT), no topological loop (TDA). No conflict.

**SENSOR-STRUCT-sensor_02** (scored TP): The key's primary expectation for sensor_02 is "weaker positive with D/E" (cross-series link). SENSOR-STRUCT tests within-series recovery, not the cross-series link. Both the within-series structure and the expected cross-link are consistent with sensor_02 being a periodic z_common proxy, so the TP is valid — but the specific cross-draw prediction is confirmed by panel tests, not this claim directly.

---

## 9. One-Paragraph Honest Assessment

The lab's methodology performed strongly on this 68-claim benchmark: zero false positives across 45 null slots, and 19 of 23 planted-structure slots detected, yielding specificity 1.000, sensitivity 0.826, and accuracy 0.941. The perfect specificity is the headline result — the permutation-based nulls, Sidak family corrections, and Phipson-Smyth +1 floors held without exception even when several null excursions reached raw p-values of 0.01–0.03 (DRAW-CROSS-A|B, GRAPH-PAIR-A|C, MATRIX-M2). The four misses divide cleanly into two types: two near-threshold misses (DRAW-STATION-B p=0.0575, DRAW-CROSS-D|E p=0.0075) where the signal is real and visible but the Sidak correction for the family size absorbs it — an expected cost of conservative multiple-comparison control that the methodology explicitly acknowledges in its NULL-verdict caveat ("below detection at these shapes, not proof of absence"); and two instrument-specific misses (SERIES-TDA-S2, SERIES-PAIR-S1|S2) where fixed embedding parameters or time-domain rank correlation fail to represent phase-indeterminate or nonlinearly encoded periodic relationships, even though the same underlying structure is detectable by complementary instruments. No overclaims were made: the lab correctly returned NULL on all ER controls, iid series, Gaussian clouds, and uniform draw streams. The four coverage gaps (number attribution, GW in G0, per-sensor attribution, sensor_04-era link) are design-level scope limitations rather than methodological failures, and the GW suppression — conservative given its calibration state — cost the lab one blocked confirmatory result while TDA covered the gap independently.

---

*Report written by independent-verifier agent. No lab scripts read, modified, or executed. No outcome changed. This file is the sole deliverable of this scoring pass.*
