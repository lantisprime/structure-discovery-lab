# Results — Exploration Batch 4 ("Harmonization Instruments")

Run: 2026-06-11, per docs/REGISTRATION_BATCH4.md (registered before any real-data run).
Scripts: `src/concentration_exclusion.py` (SEED=31), `src/graphon_cooccurrence.py`
(SEED=37), `src/szemeredi_ap.py` (SEED=41). K=2000 throughout. Dataset:
`datasets/pcso-lotto/data_draws_1yr.csv` (776 draws). All three instruments passed
null-trial admission before touching real data.

## Headline

No new structure. One registered test fired (B1 on 6/55, p=0.0005; A2's flag of ball
45 is the same event) and driving-row attribution identifies it as a **re-detection of
the already-adjudicated 6/55 #45 excess** (THEOREM_SYNTHESIS §4b) — now flagged by an
eighth and ninth correlated statistic, still counting as **one anomaly, zero new
discoveries**. Everything else sat inside its null band.

## Instrument A — concentration exclusion

| Game | A1 max dev (counts) | q95 | verdict | ε bound on \|p_i−6/P\| | A2 support | p |
|---|---|---|---|---|---|---|
| 6/42 | 11.0 | 14.0 | inside | 0.16234 (114% of 6/P) | empty | 0.4793 |
| 6/45 | 13.2 | 14.2 | inside | 0.17564 (132%) | empty | 0.1124 |
| 6/49 | 11.0 | 14.0 | inside | 0.16155 (132%) | empty | 0.3543 |
| 6/55 | 18.0 | 13.0 | **outside** | 0.19848 (182%) | **{45}** | **0.0020** |
| 6/58 | 12.0 | 13.0 | inside | 0.16085 (156%) | empty | 0.1644 |

- Ball 45 in 6/55: 35 appearances vs 17.0 expected — the adjudicated anomaly's hit
  counts; A2 is a deterministic function of those counts → same driving rows, same
  equivalence class, re-detection.
- **Honesty finding (the real lesson of Instrument A):** at ~155 draws/game the 95%
  simultaneous exclusion bound cannot rule out even a 100% relative per-ball bias.
  The 1/√n schedule implies ~130–330 *years* of draws for a 10% relative bound.
  Per-ball bias exclusion at decision-relevant precision is unreachable at lottery
  data rates; the EV-impact translation (registered) is therefore vacuous at any n
  the lab will ever see. Logged as a capability boundary, not a failure.

## Instrument B — graphon co-occurrence

| Game | B1 | null mean ± sd | p |
|---|---|---|---|
| 6/42 | 27.06 | 26.38 ± 2.72 | 0.3703 |
| 6/45 | 32.60 | 25.90 ± 2.56 | 0.0070 (n.s. at 0.0025) |
| 6/49 | 25.68 | 25.04 ± 2.32 | 0.3723 |
| 6/55 | **32.74** | 24.17 ± 2.16 | **0.0005** |
| 6/58 | 26.16 | 23.64 ± 2.12 | 0.1309 |

- **H-protocol surprise:** mean null-correlation(B1, MP λ_max) = **+0.113** — the
  registration predicted ρ ≥ 0.90 (same class); measurement says **distinct class**.
  The centered co-occurrence spectral norm and the indicator-correlation λ_max see
  different fluctuation modes (raw count deviations vs standardized correlations).
  B1 therefore counts its full 5 tests in the family — and is a genuinely new
  instrument for the kit. Prediction wrong, measurement kept; that is the H-protocol
  working as designed.
- **Attribution of the 6/55 fire:** leading eigenvector loads on ball 45 (+0.447) and
  ball 42 (+0.425) — the pair-affinity face of the adjudicated anomaly. Removing the
  35 ball-45 rows: B1 32.74 → 26.36, p 0.0005 → 0.0080 (n.s. at threshold). Fire
  dissolves with the known driving rows ⇒ re-detection.
- 6/45 at p=0.0070 is above threshold and consistent with the null p-value
  distribution across 20 tests; noted, not flagged.

## Instrument C — Szemerédi APs

| Game | C1 obs | C1 null | p | C2 obs | C2 null | p |
|---|---|---|---|---|---|---|
| 6/42 | 142 | 112.9 ± 10.1 | 0.0110 | 6.40 | 4.51 ± 0.94 | 0.0850 |
| 6/45 | 89 | 106.0 ± 9.8 | 0.0910 | 3.60 | 4.12 ± 0.91 | 0.6897 |
| 6/49 | 111 | 96.7 ± 9.4 | 0.1339 | 4.80 | 3.88 ± 0.89 | 0.3308 |
| 6/55 | 88 | 86.8 ± 8.7 | 0.9355 | 2.80 | 3.43 ± 0.85 | 0.5477 |
| 6/58 | 91 | 81.4 ± 8.9 | 0.3088 | 3.00 | 3.29 ± 0.83 | 0.8826 |

- Nothing fires (min p=0.011 ≫ 0.0025 with m=20; the ten p-values are
  null-distributed). AP abundance sits exactly at the theorem-forced rate.
- **Ramsey-trap baselines** (E[3-term APs in a random 10-subset], simulated, for the
  failure-mode card): P=42: 4.39, P=45: 4.04, P=49: 3.79, P=55: 3.32, P=58: 3.19.
  A hot-set "progression pattern" must beat these numbers, two-sided, after
  multiplicity — otherwise it is Szemerédi (1975), not the lottery.

## Multiplicity accounting (final)

Registered worst case m=20, threshold p<0.0025. Actual family: A2 (5) + B1 (5,
distinct class confirmed) + C1,C2 (10) = 20. Fires below threshold: B1-6/55
(p=0.0005) and A2-6/55 (p=0.0020) — same driving rows as each other *and* as the
adjudicated anomaly ⇒ **1 anomaly re-detected, 0 new**. Confirmation arbiter:
registered held-out set (draws ≥ 2026-06-12), unchanged.

## Ledger deltas

- THEOREM_SYNTHESIS results ledger: rows 26–28 added (instruments A, B, C).
- Failure-mode gallery: + the Ramsey trap (theorem-forced patterns); + the vacuous
  exclusion bound (instrument whose registered translation is unreachable at any
  feasible n).
- kb: + szemeredi-furstenberg-ap.md, graphons-cut-norm.md,
  concentration-sparse-recovery.md (INDEX rows 17–19).
- Equivalence-class registry: B1 measured *out* of the MP class (ρ=+0.113) — first
  instrument predicted into a class and measured out of it.
