# Registration Template — Synthetic Structure Eval Set

Use this before running the blind benchmark.

## H0

For each dataset unit, state the null that preserves its nuisance properties and destroys
only the relationship being tested.

## Required claim declarations

| claim_id | dataset(s) | representation | statistic | matched null | expected outcome before running |
|---|---|---|---|---|---|
| DRAW-MARGINAL-* | draw streams | per-number counts | MC chi-square / max dev | 6-of-60 constrained generator | TBD by lab |
| DRAW-MEMORY-* | draw streams | consecutive draws | overlap / stickiness / Markov | constrained generator preserving stream length | TBD by lab |
| DRAW-SENSOR-* | draws + sensors | date-paired features | held-out CCA/corr | shuffled date pairing | TBD by lab |
| SERIES-RECOVERY-* | series | time + value | subset-to-whole recovery curve | within-series value permutation/block null | TBD by lab |
| SERIES-TDA-* | series | delay embedding | max H1 persistence | permuted series / matched noise | TBD by lab |
| CLOUD-GW-* | point clouds | pairwise distances | GW distortion / diagram distance | matched-density/matched-cov cloud | TBD by lab |
| GRAPH-* | graphs | graph spectra/community | spectral/community similarity | degree-preserving/null graph | TBD by lab |
| MATRIX-* | matrices | train/test entries | held-out RMSE | shuffled-entry/matched-noise null | TBD by lab |

## Decision rule

Report raw p-values, adjusted thresholds, permutation floors, effect sizes, and null
model validity. Do not claim causality.
