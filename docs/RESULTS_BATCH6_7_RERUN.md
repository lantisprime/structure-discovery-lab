# Results — Batch 6 & 7 Rerun (run id: batch67_r2)

**Registration hash**: 2709deedb274f0f6 — committed pre-run, first G3-grade batch  
**Architecture**: first full batch on `src/core` + `src/domains` (sanitized)  
**Executor**: haiku execute-only agent, orchestrated by the remediated-methodology runner  
**Seed**: 20260611 · **Date**: 2026-06-11  

Sources: `results/rerun_batch67.json` (new), `results/relational_subsets.json` (original
batch 6), `results/relational_batch7.json` (original batch 7),
`docs/REGISTRATION_BATCH6_7_RERUN.md`.

---

## Why a rerun

The original batch 6 and batch 7 runs predate four standing rules that are now mandatory
per the design verifier:

1. **Floor rule** — m_perm must satisfy p_floor ≤ α′/2 per family; originals fell short
   on several families (e.g. b6_mmd at m=99 gives p_floor=0.01 >> Šidák α′/2=0.000854).
2. **M4 three-regime sensitivity** — half-corr statistics must be reported for all-draws,
   ex-suspicious, and verified-only subsets; original batch 6 halves reported a single
   regime.
3. **M7 multi-split CCA** — CCA p-values must be confirmed across three train/test splits
   (50/60/70%); original batch 7 CCA used a single 60/40 split.
4. **GW demotion** — the GW instrument was demoted to G0 exploratory (REMEDIATION_LOG M2)
   after distribution calibration failed; any GW output carries no corrected claims.

Originals remain on record in the JSON files listed above. This rerun supersedes them for
the meta-uniformity panel.

---

## Stage-by-stage comparison

### b6_mmd — Cross-quarter MMD (5 games × 6 pairs = 30 tests)

| | m_perm | min p | lone excursion | Šidák α′ | Joint verdict |
|---|---|---|---|---|---|
| Original | 99 | 0.040 (6/58 Q2\|Q4) | 1 of 30 | 0.001709 | NULL |
| **Rerun** | **1199** | **0.049 (6/58 Q2\|Q4)** | **1 of 30** | 0.001709 | **NULL** |

The lone excursion is the same pair in the same game (Ultra Lotto 6/58, Q2|Q4). At m=1199
the resolved value is p=0.049166... vs 0.040 at m=99 — a floor artifact in the original
that moves toward the bulk at higher resolution. The joint null holds in both runs.

### b6_spectra — Cross-quarter co-occurrence spectra (30 tests)

| | m_perm | min p | Joint verdict |
|---|---|---|---|
| Original | 99 | 0.070 (6/49 Q1\|Q2 and Q2\|Q3) | NULL |
| **Rerun** | **1199** | **0.036 (6/49 Q2\|Q3)** | **NULL** |

At m=1199 the minimum is 0.035833..., lower than the original's 0.070 — finer resolution
reveals more of the tail, but the value remains well above Šidák α′=0.001709. Joint null
confirmed; no family-level rejection.

### b6_halves — Half-vs-half hot-number correlation (5 games, 3 regimes)

Rerun adds two sensitivity regimes that were absent from the original. Original reported
one value per game (all-draws); rerun reports three: all, ex-suspicious, verified-only.

| Game | Regime | n | corr | p |
|---|---|---|---|---|
| Grand Lotto 6/55 | all | 156 | 0.251 | 0.050 |
| Grand Lotto 6/55 | ex-suspicious | 153 | 0.154 | 0.195 |
| Grand Lotto 6/55 | verified-only | 108 | 0.177 | 0.070 |

The 6/55 raw flag (corr=0.251, p=0.050) replicates to three decimal places the value
observed in the blind independent verification (row 39 of the ledger: 0.251/0.154).
Removing suspicious-sourced rows halves the correlation and pushes p to 0.195; the
verified-only subset (n=108) sits at p=0.070. Caveat travels: this flag is a data-quality
sensitivity result, not a structure detection. Šidák threshold is 0.010206; the raw
minimum p=0.050 does not survive correction; joint verdict NULL. m_perm=199.

### b7_seasons — Pressure quarter-pair MMD (6 pairs)

| | m_perm | All 6 pairs p | n corrected rejections | Šidák α′ | Verdict |
|---|---|---|---|---|---|
| Original | 199 | all 0.005 | 6 | 0.008512 | 6/6 REJECT |
| **Rerun** | **399** | **all 0.0025** | **6** | 0.008512 | **6/6 REJECT** |

With m=399 the floor halves to 0.0025 and all six pairs hit it, deepening each rejection.
The 6/6 corrected-rejection verdict is stable and strengthened. Note: these are results on
the atmospheric pressure series — this is a positive-control result confirming seasonal
structure in the physical covariate, not in the lottery draws.

### b7_cca — Date-paired CCA (pressure vs sun-moon; pressure vs Kp)

Original used a single 60/40 split. Rerun applies M7 three-split protocol.

**pressure vs sun-moon** (all three splits reject at Šidák α′=0.025321):

| Split | ρ₁ | p |
|---|---|---|
| 0.5 | 0.403 | 0.005 |
| 0.6 | 0.567 | 0.005 |
| 0.7 | 0.529 | 0.005 |

Median p = 0.005; all three at the permutation floor. The original single-split value
(ρ₁=0.567, p=0.005) is now confirmed as the 60% split result. Verdict REJECT, strengthened
by cross-split stability. This confirms the pressure↔sun-moon coupling (mechanism known —
tidal loading); it is a positive-control result on the physical series.

**pressure vs Kp** (geomagnetic index):

| Split | ρ₁ | p |
|---|---|---|
| 0.5 | 0.009 | 0.430 |
| 0.6 | −0.012 | 0.590 |
| 0.7 | 0.058 | 0.260 |

Median p = 0.430. All three splits null; Kp null replicates and is robust across splits.

### b7_gw — Gromov–Wasserstein (G0 exploratory only)

The GW instrument is demoted (REMEDIATION_LOG M2); outputs are reported for continuity
but carry **no corrected claims**. The pattern at m=99 is unchanged from the original:
tidal|moon score=−0.023 p=0.01, pressure|lotto655 score=−0.097 p=0.27, pressure|tidal
p=1.0. Status string from JSON: "G0 EXPLORATORY ONLY — instrument demoted (REMEDIATION_LOG
M2); no corrected claims attach to these numbers."

---

## Panel correction — a worked example of panel-design honesty

The meta-uniformity panel (`results/meta_uniformity.json`) was refreshed after this rerun.
Before the refresh, the panel pooled both the original batch 6/7 results and the rerun
results. This double-counted correlated tests — the same 30 MMD comparisons and 5 halves
tests appeared twice, with small differences driven purely by m_perm resolution. The
artifact was a KS p=0.027 suggesting mild non-uniformity in the p-value distribution,
which disappeared once duplicates were replaced by the current-best version.

The refreshed panel uses one version per test: the rerun values for b6_mmd (30 tests),
b6_spectra (30 tests), and b6_halves (15 tests across three regimes). Panel as of
2026-06-11:

- n = 136 tests (lotto-side real-data only; physical-series positives excluded by design)
- KS p = 0.111 (KS stat = 0.102)
- 8.8% ≤ 0.05 (12/136); 0.7% ≤ 0.01 (1/136)

The panel is consistent with a uniform null distribution. The pre-refresh KS p=0.027 was
not a discovery; it was a panel-design error. This is the correct resolution: document the
artifact and its cause, replace it with the de-duplicated panel, and carry the explanation
forward rather than silently updating the number.

---

## Verdict impact

All original verdicts are resolution-stable:

- **b6_mmd**: NULL confirmed; lone 6/58 Q2|Q4 excursion unchanged in identity, sharpened
  in p-value (0.040 → 0.049).
- **b6_spectra**: NULL confirmed; minimum moves to 0.036 at higher resolution.
- **b6_halves**: NULL confirmed; 6/55 raw flag replicates including three-decimal agreement
  with the blind verification. Data-quality sensitivity caveat travels: the 6/55 signal is
  dominated by suspicious-sourced rows; ex-suspicious and verified-only subsets are null.
- **b7_seasons**: REJECT ×6 confirmed and strengthened (all p now at finer floor 0.0025).
- **b7_cca pressure↔sun-moon**: REJECT confirmed and strengthened across all three splits
  (ρ₁ range 0.403–0.567, all p=0.005).
- **b7_cca pressure↔Kp**: NULL confirmed and robust across splits.
- **b7_gw**: G0 exploratory, no verdict change, pattern unchanged.

No new flags. No new structure detected in lottery draws.
