# Blind Benchmark Folder

You are seeing only the blind side of the evaluation set.

## Candidate experiment families

Run your normal structure-discovery pipeline across these datasets:

| dataset area | candidate claims |
|---|---|
| `datasets/draws/` | marginal uniformity, memory, stationarity, subset-to-whole, cross-stream CCA |
| `datasets/sensors/` | paired sensor relationships with draw streams |
| `datasets/series/` | subset-to-whole recovery, topology, spectral structure, regime partitions |
| `datasets/clouds/` | intrinsic topology and geometry, no row anchors |
| `datasets/graphs/` | community/spectral similarity, graph matching under degree-preserving nulls |
| `datasets/matrices/` | low-rank structure and matrix-completion generalization |

## Important blind rules

- Do not assume file names reveal truth.
- Do not assume row order alignment for point clouds or graphs.
- Use shuffled-pairing nulls for paired claims.
- Use matched-marginal or degree-preserving nulls for structural claims.
- For matrices, fit only on train entries and score once on test entries.
