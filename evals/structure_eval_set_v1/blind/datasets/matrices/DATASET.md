# DATASET.md — Synthetic Matrices

## Purpose

Two random-looking matrices for matrix completion, low-rank detection, and
subset-to-whole recovery.

## Files

- `matrix_M1.csv`, `matrix_M2.csv`: full matrices.
- `matrix_M1_train_entries.csv`, `matrix_M1_test_entries.csv`.
- `matrix_M2_train_entries.csv`, `matrix_M2_test_entries.csv`.

Entry files have columns `row`, `col`, `value`.

## Blind-use rules

Fit completion/reconstruction models only on train entries, then score once on test
entries. Compare against shuffled-entry or matched-noise nulls.
