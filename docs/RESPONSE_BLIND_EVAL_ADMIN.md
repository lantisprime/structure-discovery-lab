# Response to Admin Review — Blind Methodology Evaluation (structure_eval_set_v1)

**Date**: 2026-06-11  
**Context**: Admin reviewed `results/blind_eval_score.md` (68-unit blind benchmark:
19 TP / 45 TN / 0 FP / 4 FN; sensitivity 0.826, specificity 1.000) and issued
recommendations. This document records the lab's disposition for every recommendation.

---

## Admin bottom-line verdict (quoted verbatim)

> "The methodology is trustworthy but incomplete: zero false positives across 45 null
> slots confirms the conservative operating point is real and the null-control machinery
> works; the four misses and the coverage gaps tell us where the instrument set needs to
> grow. Keep the lab conservative — precision matters more than recall here."

This directive is adopted as a standing operating principle. See README.md Limitations.

---

## Part A — Immediate items (all actioned today, 2026-06-11)

| # | Recommendation | Action | Status | Evidence |
|---|---|---|---|---|
| A1 | Preserve blind-eval baseline as a permanent reference point | Baseline is intact: eval set at `evals/structure_eval_set_v1/`; run-ledger row `blind_methodology_eval_v1` in `results/run_ledger.jsonl`; scoring report at `results/blind_eval_score.md`. Committed verdict file hash `1d0a4d3ed4d2dd4d` is untouched. | **DONE** | `evals/structure_eval_set_v1/` · `results/run_ledger.jsonl` run `blind_methodology_eval_v1` · `results/blind_eval_score.md` |
| A2 | Add a NEAR_MISS_REGISTERED_SIGNAL tier to the verdict taxonomy | Tier added to the Phase 4 taxonomy in `docs/RELATIONAL_RUNBOOK.md` (five-tier table with rules). Annotation layer `results/blind_eval_verdict_tiers.json` carries per-claim tier assignments. The committed verdicts file `1d0a4d3ed4d2dd4d` is untouched — tiers live in the separate annotation file only. | **DONE** | `docs/RELATIONAL_RUNBOOK.md` Phase 4 · `results/blind_eval_verdict_tiers.json` |
| A3 | Record admin note: lab is a high-specificity conservative detector, not maximum-sensitivity | Note recorded here (§ "Operating point") and added to README.md Limitations as a new paragraph. | **DONE** | `README.md` Limitations · this document |
| A4 | Leave detection thresholds unchanged | Thresholds unchanged. The Šidák family corrections, Phipson–Smyth +1 floors, and permutation counts stand as registered. No post-hoc tuning. | **DONE** | `docs/RELATIONAL_RUNBOOK.md` Phase 2 (floor rule M3, gate rule M2) |

---

## Part B — Next-iteration items

| # | Recommendation | Action | Status | Notes |
|---|---|---|---|---|
| B1 | Phase-invariant series-pair instrument — R8 lag-max cross-correlation (addresses FN-4: SERIES-PAIR circular-shift null fails phase-indeterminate cycles) | KB card R8 onboarding begun as Part 3 of this run. Instrument to be added as an admitted relational method for series-pair claims where the circular-shift null is inappropriate. | **IN PROGRESS** (today, Part 3 onboarding) | Source: `results/blind_eval_score.md` §5 FN-4. SERIES-PAIR-S1\|S2: p=0.7462 under circular-shift null is an instrument-representation miss, not a threshold miss. Lag-max cross-correlation with appropriate phase-shift null is the targeted replacement. |
| B2 | Attribution modules: ATTRIBUTION-MARGINAL, ATTRIBUTION-SENSOR, ATTRIBUTION-TIMESEGMENT, ATTRIBUTION-LATENT-DIRECTION | Registered on the ROADMAP. Each module requires: KB card, admission at matched shape, pre-registered claim before any real-data run. Multiplicity-charged per A3. Never auto-discoveries — each produces a registered finding, not an exploratory claim. | **ROADMAP** | Addresses coverage gaps GAP-1 (number attribution), GAP-3 (sensor_04 x era), GAP-4 (per-sensor attribution). Source: `results/blind_eval_score.md` §6. |
| B3 | Targeted era-shift / changepoint detector: per-coordinate scan, CUSUM, or changepoint model | Registered on the ROADMAP. Addresses FN-1 (DRAW-STATION-B: p=0.0575 with Šidák m=5; a dedicated era-shift instrument at higher power could resolve this near-miss). | **ROADMAP** | Source: `results/blind_eval_score.md` §5 FN-1. NEAR_MISS tier annotation for DRAW-STATION-B in `results/blind_eval_verdict_tiers.json`. |
| B4 | GW confirmatory admission suite: same-shape nulls, different-density nulls, topology positive/negative controls, partial-overlap, subsample stability, floor rule | Registered on the ROADMAP. GW stays at G0 until the full suite passes. The current demotion stands: FPR 0.055 at n=200 gate (moment-matched null), p-distribution non-uniform (lattice χ² p=0.002); symmetric-null variant also fails (p=0.005). The exploratory-only GW signal on CLOUD-GW-X\|Y (p=0.010, ground truth STRUCTURED) is documented in the tier annotation as EXPLORATORY_ONLY, not counted in accuracy tallies, and covered by CLOUD-TDA-X/Y (both STRUCTURED). | **ROADMAP** | Source: `docs/REMEDIATION_LOG.md` M2 · `results/blind_eval_score.md` §6 Gap-2 · `results/blind_eval_verdict_tiers.json`. |
| B5 | Latent-triangulation tier: (A-Z STRUCTURED) + (B-Z STRUCTURED) + (A-B near-threshold) => LATENT-SUPPORTED/NEEDS-CONFIRMATION; never auto-STRUCTURED | Adopted into the runbook taxonomy (Phase 4, `docs/RELATIONAL_RUNBOOK.md`) and into the tier annotation rules (`results/blind_eval_verdict_tiers.json`). Applied immediately to DRAW-CROSS-D\|E (FN-2): DRAW-SENSOR-D and DRAW-SENSOR-E are both STRUCTURED; DRAW-CROSS-D\|E is NEAR_MISS at p=0.0075 (α'=0.0051); tag = LATENT-SUPPORTED/NEEDS-CONFIRMATION. Direct A-B test at higher power is the pre-registration target. | **DONE** (taxonomy adopted) | Source: `results/blind_eval_score.md` §5 FN-2 · `results/blind_eval_verdict_tiers.json` DRAW-CROSS-D\|E entry. |
| B6 | Coverage-separate-from-accuracy benchmark reporting convention | Adopted as eval-report convention. Accuracy (TP/TN/FP/FN) is reported separately from: coverage gaps (OUT_OF_SCOPE), instrument-blocked detections (EXPLORATORY_ONLY), near-threshold detections (NEAR_MISS_REGISTERED_SIGNAL), and out-of-scope structures. These four categories are never pooled with the accuracy tally. Applied retroactively to `results/blind_eval_score.md` (§6 coverage gaps already separate; §7 exploratory flags already separate; §3 confusion matrix covers only verdict-eligible units). | **DONE** (convention adopted) | Source: `results/blind_eval_score.md` §3, §6, §7. Codified in `docs/RELATIONAL_RUNBOOK.md` Phase 4. |

---

## Operating point note (A3)

The lab operates at a **high-specificity, conservative** point by design. The blind
benchmark confirms this empirically: 0 false positives across 45 null slots at
sensitivity 0.826 (source: `results/blind_eval_score.md` §3). The cost is deliberate:
conservative multiple-comparison control (Šidák corrections, Phipson–Smyth +1 floors)
absorbs near-threshold signals. Two of the four misses (DRAW-STATION-B, DRAW-CROSS-D\|E)
are real signals below the corrected threshold — an expected cost of the conservative
operating point that the NULL-verdict caveat explicitly acknowledges
("below detection at these shapes, not proof of absence").

This operating point is **not a bug to be corrected by loosening thresholds**. It is
the correct choice for a domain where false positives have asymmetric costs. Precision
is preserved; recall gaps are addressed by instrument expansion (B1–B4), not by tuning
existing thresholds (A4: thresholds unchanged).

---

## Baseline preservation summary (A1)

The three artefacts that constitute the permanent blind-eval baseline:

| Artefact | Path | Role |
|---|---|---|
| Eval set | `evals/structure_eval_set_v1/` | 14 dataset objects, 68 registered claim units, sealed answer key |
| Run-ledger row | `results/run_ledger.jsonl` run `blind_methodology_eval_v1` | Role-separated execution record; verdict hash committed pre-unseal |
| Scoring report | `results/blind_eval_score.md` | Independent-verifier score (sonnet, barred from analysis); hash `1d0a4d3ed4d2dd4d` verified |

The committed verdicts file `results/blind_eval_verdicts.json` (hash `1d0a4d3ed4d2dd4d`)
is untouched. The tier annotations live exclusively in the separate file
`results/blind_eval_verdict_tiers.json`.

---

*Produced by docs-web-editor agent. Numbers copied from `results/blind_eval_score.md`.
Caveats travel: all FN descriptions carry their instrument-limitation qualifiers as
stated in `results/blind_eval_score.md` §5.*
