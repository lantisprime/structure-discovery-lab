# Ground Truth — Structure Discovery Evaluation Set v1

Open this only after the lab has completed its blind run.

## Summary

This benchmark contains a mix of nulls and planted structures. It is designed to test
whether the lab can detect real structure without overclaiming.

## Expected detections

| Area | Unit | Ground truth | Expected lab behavior |
|---|---|---|---|
| Draws | A | pure constrained-uniform stream | all tested faces should be null except nominal false positives |
| Draws | B | first-half-only marginal bias | frequency/stationarity positive; trace to numbers 17 and 42; no persistence claim |
| Draws | C | exact-balanced marginals plus order-1 overlap memory | marginal null; memory/overlap/stickiness positive |
| Draws | D/E | date-paired latent relationship | CCA/correlation with `sensor_01` positive; shuffled-pairing null kills signal |
| Sensors | sensor_03 | independent noise | null with draws and series |
| Series | S1/S2 | periodic structured series | subset-to-whole recovery, spectral, and TDA loop positive |
| Series | S3 | iid noise | null |
| Series | S4 | regime/changepoint structure | cross-segment MMD positive; no clean loop expected |
| Clouds | X/Y | same circle geometry in different dimensions, no row anchors | TDA/GW positive; row-wise CCA invalid |
| Clouds | Z | Gaussian blob | topology/geometric null vs X/Y |
| Graphs | A/B | two 4-community SBMs | graph spectra/community similarity positive |
| Graphs | C | density-matched ER control | community-structure null |
| Matrices | M1 | rank-3 plus noise | matrix completion and spectral low-rank tests positive |
| Matrices | M2 | iid Gaussian | completion/reconstruction null |

## Scoring suggestions

Score your lab on:

1. **True positives**: B frequency/era, C memory, D/E sensor relationship, S1/S2 loops,
   S4 regime, X/Y topology, A/B graph structure, M1 low rank.
2. **True negatives**: draw A, sensor_03, series S3, cloud Z, graph C, matrix M2.
3. **False positives**: any claimed relationship not listed above.
4. **Claim hygiene**: correct null model, adjusted p-values, permutation floors, and
   power caveats.
5. **Overclaim control**: no causality claims; no row-wise alignment claim for clouds
   X/Y; no persistence claim for draw stream B beyond its first-half era.
