# DATASET.md — Synthetic Graphs

## Purpose

Three unlabeled edge-list graphs for graph-spectral, graph-matching, community, and
Gromov-Wasserstein-on-graph-distance tests.

## Files

- `graph_A_edges.csv`
- `graph_B_edges.csv`
- `graph_C_edges.csv`

Each file has columns `source,target`. Node IDs are arbitrary and not aligned across
graphs.

## Suggested nulls

Use density-preserving and degree-preserving graph nulls. Plain Erdős–Rényi can be a
screening baseline, but it is not sufficient for strong claims.
