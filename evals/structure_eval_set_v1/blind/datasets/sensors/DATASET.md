# DATASET.md — Synthetic Sensor Panel

## Purpose

Generic date-aligned sensor panel for paired relational tests against the draw streams.

## Schema

`sensor_panel.csv`

| column | meaning |
|---|---|
| `date` | daily ISO date |
| `sensor_01`–`sensor_04` | anonymized scalar sensor channels |

## Blind-use rules

Use only date pairing. Do not infer causal direction. Use shuffled-pairing nulls for
CCA/correlation tests.
