# Registration — Blind Methodology Eval (structure_eval_set_v1)

**Date**: 2026-06-11 · **Protocol**: RELATIONAL_RUNBOOK Phase 1, expectation-free
(no outcome expectations for any discovery test; the template's "expected outcome"
column is intentionally left out per the lab's 2026-06-11 amendment) ·
**Sealed**: answer_key/, src/GENERATION_NOTES.md, src/quick_probe.py, manifest.json —
not read; unsealing only after `results/blind_eval_verdicts.json` is hash-committed.
**Script**: `src/run_blind_eval.py` (this folder) · seed 20260611 · All instruments
used are admitted (R1/R3/R4/R5/R7 + lab marginal/memory MC instruments); GW is
**exploratory-only** per its standing calibration flag and is reported as G0.

## Claim table (statistic · matched null · m · family · corrected α · floor check)

| claim | units | statistic | null (preserves / destroys) | m | family → Šidák α' | floor ≤ α'/2 |
|---|---|---|---|---|---|---|
| DRAW-MARGINAL | streams A–E | χ² of per-number counts | 6-of-60 constrained generator (pool, T, w/o-replacement / marginal bias) | 399 | 5 → .0102 | .0025 ≤ .0051 ✓ |
| DRAW-MEMORY | A–E | mean consecutive-draw overlap | same generator (destroys serial dependence) | 399 | 5 → .0102 | ✓ |
| DRAW-STATION | A–E | half-vs-half per-number deviation corr | generator per half (destroys persistent bias) | 399 | 5 → .0102 | ✓ |
| DRAW-SUBSET | A–E | draw-sum k-NN recovery, k∈{5,10,20,40}%, 10 seeds | within-stream value permutation | 199 | 5 → .0102 | .005 ≤ .0051 ✓ |
| DRAW-CROSS | 10 stream pairs | held-out CCA ρ₁ on 6 draw features, date-paired | shuffled held-out pairing | 799 | 10 → .0051 | .00125 ≤ .00256 ✓ |
| DRAW-SENSOR | A–E × sensor panel | held-out CCA ρ₁ | shuffled held-out pairing | 399 | 5 → .0102 | ✓ |
| SENSOR-STRUCT | sensor_01–04 | recovery z at k=20% (10 seeds) | within-series permutation | 199 | 4 → .0127 | ✓ |
| SERIES-RECOVERY | S1–S4 | recovery curve k∈{5,10,20,40}% | within-series permutation | 199 | 4 → .0127 | ✓ |
| SERIES-TDA | S1–S4 | max H₁ persistence, delay embed τ=3 d=3 | within-series permutation → same embedding | 399 | 4 → .0127 | ✓ |
| SERIES-PAIR | 6 pairs | \|Spearman ρ(Si,Sj)\| | circular shift δ∈[26,486] (preserves each series' autocorrelation; destroys alignment) | 461 (exhaustive) | 6 → .0085 | .0022 ≤ .0043 ✓ |
| SERIES-SEGMENT | S1–S4 | quarter-pair MMD ([value,\|Δ\|] features), min-p of 6 pairs | pool-and-relabel | 399 | per-series Šidák m=6 (.0085); outer 4 | ✓ |
| CLOUD-TDA | X,Y,Z | max H₁ persistence | matched mean/cov Gaussian | 399 | 3 → .0170 | ✓ |
| CLOUD-GW | 3 pairs | −GW distortion (scale-normalized) | matched-Gaussian regeneration of 2nd cloud | 99 | exploratory-only (instrument flag) — no corrected claim | n/a |
| GRAPH-COMMUNITY | A,B,C | mean bottom-12 normalized-Laplacian eigenvalues (one-sided small) | degree-preserving double-edge swaps | 199 | 3 → .0170 | ✓ |
| GRAPH-PAIR | 3 pairs | −L2 between bottom-12 spectra | rewired second graph | 199 | 3 → .0170 | ✓ |
| MATRIX | M1,M2 | held-out-entry skill: RMSE(col-mean baseline) − RMSE(SoftImpute fit on train entries only) | within-column value permutation of train entries, same split | 199 | 2 → .0253 | ✓ |

Decision rule: Phipson–Smyth +1 everywhere; verdict per unit = STRUCTURED if
p ≤ family-corrected α', else NULL; raw 0.0X excursions above α' reported as
exploratory. Falsification: a STRUCTURED verdict is defeated by instability under
seeds or single-metric dependence; a NULL verdict is bounded by the admission
power curves (REMEDIATION_LOG) — it means "below detection at these shapes."
GW outputs are never verdicts (G0).

No outcome expectations are declared for any unit.
