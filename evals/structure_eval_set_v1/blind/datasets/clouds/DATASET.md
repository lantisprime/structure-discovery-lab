# DATASET.md — Synthetic Point Clouds

## Purpose

Three unlabeled point clouds for intrinsic geometry and topology tests.

## Files

- `cloud_X.csv`: 2D point cloud.
- `cloud_Y.csv`: 5D point cloud.
- `cloud_Z.csv`: 5D point cloud.

## Blind-use rules

Do not assume row alignment between clouds. Use intrinsic-distance methods, persistence
diagrams, and Gromov-Wasserstein style comparisons. CCA on row order is intentionally
invalid here.
