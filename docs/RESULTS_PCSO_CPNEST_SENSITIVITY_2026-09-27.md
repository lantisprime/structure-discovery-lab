# RESULTS — pcso.cpnest.sensitivity1 (2026-09-27)

**Verdict: ROBUST.** The registered CP-NEST point (τ 0.05, ρ 10⁻³, v₀ ∝ 2^-d, M 128) detects a planted tilt as fast as
the best gate-passing cell of the 18-cell grid, and every cell passes the defect gate. Grade G0 exploratory, simulation only:
no real draw is scored and `pcso.registry.seq1` is unchanged (spec `docs/STUDY_PCSO_CPNEST_SENSITIVITY.md`, APPROVED
2026-09-25; runner ledger-hashed at `dc19c67` before any shard).

## Provenance

- Full output (M5 git checkout, `results/exploratory/pcso_cpnest_sensitivity_2026-09-27.json`, 43,963,837 bytes):
  sha256 `78129aed25be7de2701be23da115873826f55eb3c3600af83d22aeb75b0d1e73`. Committed here:
  `results/exploratory/pcso_cpnest_sensitivity_2026-09-27_summary.json` = the same JSON without its `artifacts` map
  (7,010 per-shard hashes), which carries the full file's sha256.
- Code hashes in the output equal the ledger snapshot (`tools/pcso_cpnest_sensitivity.py` ca6c8a15…,
  `src/pcso_mlx_sim.py` 060077e8…); input `data_draws_1yr.csv` 5a34f0c1…; schedule pin `1ce8541`
  (sha256 7ebcf8f0…); seed 20260923; bootstrap 2,000 resamples.
- Runner verification (#DV, 2026-09-27): `tests/test_pcso_cpnest_sensitivity.py` 61 passed, `tests/test_pcso_mlx_sim.py`
  26 passed, 0 skipped on the MLX GPU host.
- Execution: 1,060 planned shard commands (50 data, 110 check64, 900 cell), run as 1,200 shard jobs (slow shapes
  pre-split), 0 failures, 0 timeouts, 11:39–19:45 PHT.

## Defect gate (§6) — all 18 cells PASS

N1: fraction of 20,000 uniform null streams with sup E ≥ 100 (Ville bound 0.01). N2: fixed-share loss-bound check
(must be 1.0). Float64 paired checks (check64, six arms): max |Δ log E| between CPU float64 and MLX ≤ 1.6 × 10⁻⁴ nats
(tolerance 10⁻³); no failed check.

## Power (planted tilt on φ₁; 2,000 streams per cell per θ₁; horizon 3,003 pooled draws)

P2 = censoring-aware median pooled draws to reach E ≥ 100; P1 = fraction crossing by the horizon.

| Cell (τ, ρ, v₀, M) | gate | null crossing (N1) | N2 | P2 θ₁=.025 | P2 θ₁=.05 | P2 θ₁=.10 | P1 θ₁=.05 |
|---|---|---|---|---|---|---|---|
| 0.01, 0, geom, 128 | PASS | 0.0 | 1.0 | not reached | 1551 | 625 | 0.9885 |
| 0.01, 0.001, geom, 128 | PASS | 0.0 | 1.0 | not reached | 1488 | 611 | 0.99 |
| 0.01, 0.01, geom, 128 | PASS | 0.00005 | 1.0 | not reached | 1469 | 591 | 0.9905 |
| 0.025, 0, geom, 128 | PASS | 0.00055 | 1.0 | not reached | 1025 | 339 | 0.9955 |
| 0.025, 0.001, geom, 128 | PASS | 0.00095 | 1.0 | not reached | 1012 | 336 | 0.995 |
| 0.025, 0.01, geom, 128 | PASS | 0.0014 | 1.0 | not reached | 996 | 323 | 0.994 |
| 0.05, 0, geom, 128 | PASS | 0.0021 | 1.0 | not reached | 954 | 258 | 0.9945 |
| **0.05, 0.001, geom, 128 (registered)** | PASS | 0.0026 | 1.0 | not reached | **946** | 256 | 0.9945 |
| 0.05, 0.01, geom, 128 | PASS | 0.00405 | 1.0 | not reached | 952 | 248 | 0.993 |
| 0.1, 0, geom, 128 | PASS | 0.0034 | 1.0 | not reached | 1013 | 236 | 0.992 |
| 0.1, 0.001, geom, 128 | PASS | 0.00445 | 1.0 | not reached | 998 | 235 | 0.994 |
| 0.1, 0.01, geom, 128 | PASS | 0.00555 | 1.0 | not reached | 1008 | 233 | 0.9895 |
| 0.2, 0, geom, 128 | PASS | 0.00345 | 1.0 | not reached | 1118 | 250 | 0.9895 |
| 0.2, 0.001, geom, 128 | PASS | 0.00425 | 1.0 | not reached | 1077 | 247 | 0.9935 |
| 0.2, 0.01, geom, 128 | PASS | 0.00595 | 1.0 | not reached | 1086 | 244 | 0.988 |
| 0.05, 0.001, geom, **32** | PASS | 0.0025 | 1.0 | not reached | 946 | 256 | 0.9945 |
| 0.05, 0.001, geom, **512** | PASS | 0.00255 | 1.0 | not reached | 946 | 256 | 0.9945 |
| 0.05, 0.001, **uniform v₀**, 128 | PASS | 0.00545 | 1.0 | not reached | 960 | 242 | 0.993 |

Comparator `tilt_linear` (exact one-parameter grid on the true direction φ₁): P2 821 at θ₁ = .05, 203 at .10, and
P1 only 0.3785 at .025 (median not reached by 3,003 draws).

## Verdict (§6, primary θ₁ = 0.05, split sample)

- Selection half (streams 0–999): best gate-passing cell **B = (τ 0.05, ρ 0.01, geom, 128)**, P2 928.
- Evaluation half (streams 1,000–1,999): registered P2 **968**, P1 0.994; B P2 978, P1 0.991.
  P2 ratio registered/B = **0.990**, 95% paired bootstrap interval [0.968, 1.000].
- Rule: ROBUST if registered P2 ≤ 1.25 × B's and registered P1 ≥ B's − 0.05 → **ROBUST**. `pcso.registry.seq1`
  continues unchanged; no seq2 proposal is triggered.

## Findings

1. **τ is the only consequential constant.** Detection at θ₁ = .05 slows by ~55–65% at τ = 0.01 and ~14–18% at
   τ = 0.2; ρ, M (32/128/512 identical to the reported precision) and v₀ change P2 by ≤ 1.5%.
2. **The registered point sits at the optimum of this grid**; tuning CP-NEST's constants cannot materially speed
   detection. Improvement must come from new model structure or more data.
3. **Cost of not knowing the direction:** CP-NEST needs ~15% more draws than the oracle-direction comparator at θ₁ = .05.
4. **Weak tilts are out of reach at this horizon:** at θ₁ = .025 no cell (and not the oracle comparator) reaches a
   median crossing within 3,003 pooled draws (~3.9 years of PCSO draws at the current cadence).
5. Null crossing fractions rise with τ and ρ (max 0.6%) but stay below the 1% Ville bound in every cell.

## Deviations from the spec

- **Committed output:** the committed JSON omits the per-shard `artifacts` hash map; the full 44 MB file stays on the
  M5 checkout and is identified by its sha256 above (the spec's §8 names the full file).
- **Execution layout:** shards ran 4 at a time from a lab driver (not in the repo), with phases ordered
  data → first cell's power shards (fills the shared comparator cache) → the rest, to avoid concurrent writes of the
  same per-stream comparator file; slow shapes were pre-split. Per-stream seeding makes results shard-invariant (spec §4).
- **Tie order over M:** the aggregator's convention is the declared grid order (M 32 before 512); M = 32, 128 and 512
  gave identical P2 at the reported precision, so the tie order did not affect B or the verdict.

## Disclosure

Scientific framing: detection time of an anytime-valid sequential test (E-value ≥ 100) under planted structure; no
statement here concerns real PCSO draws.
