# DATASET.md — Synthetic Draw Streams

## Purpose

Synthetic lottery-like streams for testing whether a structure-discovery lab can separate
true null streams from hidden marginal, dynamical, and cross-dataset relationships.

## Schema

`draws_all.csv`

| column | meaning |
|---|---|
| `date` | daily ISO date |
| `stream_id` | anonymized stream A–E |
| `pool_size` | number pool size; all streams use 60 |
| `n1`–`n6` | sorted 6-without-replacement draw values |

## Blind-use rules

Do not inspect `answer_key/` before running the lab. Treat each stream as a candidate
random 6-of-60 generator. Use matched nulls that preserve pool size, draw count, and
6-without-replacement constraints.

## Suggested experiment families

- Per-stream marginal frequency tests.
- Per-stream order-0 vs order-1 memory tests.
- Per-stream stationarity / era split tests.
- Cross-stream paired CCA on date-aligned draw features.
- Draws-vs-sensors CCA using `../sensors/sensor_panel.csv`.
- Subset-to-whole recovery on draw-sum and presence representations.
