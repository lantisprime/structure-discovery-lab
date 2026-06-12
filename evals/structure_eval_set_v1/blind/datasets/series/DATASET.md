# DATASET.md — Synthetic Series Panel

## Purpose

Random-looking scalar time series for subset-to-whole, topology, spectral, and
regime-partition tests.

## Files

- `series_wide.csv`: one row per time index, columns `S1`–`S4`.
- `series_panel.csv`: long format with `t`, `series_id`, `value`.

## Suggested experiment families

- Subset-to-whole recovery over k = 1, 2, 5, 10, 20, 40%.
- Delay-embedding persistent homology.
- Cross-segment MMD / energy tests.
- Pairwise CCA/correlation using time alignment.
- Permutation or block-permutation nulls.
