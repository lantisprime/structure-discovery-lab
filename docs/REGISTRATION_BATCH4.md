# Pre-Registration — Exploration Batch 4 ("Harmonization Instruments")

Registered: 2026-06-11, before any new instrument touched real data (A6).
Analyst: Claude (with Cha). Status: **EXPLORATION** — nothing in this batch can confirm.

## Motivation

Batch 4 onboards three instruments drawn from the five "harmonization bridges"
(Furstenberg/Szemerédi, graphons, free probability, RG, concentration of measure).
Gap analysis against the existing ledger:

| Bridge | Status | Action |
|---|---|---|
| Free probability / free CLT | Same equivalence class as MP certificate (structure_discovery.py II) | **Not onboarded** — would correlate ≥ 0.90 with λ_max by construction |
| Renormalization group | Already implemented (universality_collapse.py) | None |
| Szemerédi / Furstenberg | New | Instrument C + failure-mode card ("Ramsey trap") |
| Graphons / regularity | New (equivalence vs MP to be measured, H-protocol) | Instrument B |
| Concentration / compressed sensing | New | Instrument A (exclusion bounds + sparse recovery) |

## Datasets

- **Exploration**: `datasets/pcso-lotto/data_draws_1yr.csv` — 776 draws, 2025-06-11 → 2026-06-10, five games.
- **Confirmation (held out, registered now)**: all PCSO draws with date ≥ **2026-06-12**.
  Confirmation run fires when ≥ 150 new draws have accrued (≈ 7 weeks), or 2026-09-01,
  whichever comes first. Only statistics that fire in exploration are re-tested, at the
  thresholds below, on confirmation data alone.

## Instruments, statistics, thresholds

All nulls Monte-Carlo–derived from the constrained generative model (i.i.d. uniform
6-without-replacement per game), per A1. K = 2000 null replicates per game per statistic.
Seeds fixed in scripts. Null-trial admission (silence on simulated H₀) required before
any real-data run.

**A. Concentration exclusion (`src/concentration_exclusion.py`)** — primarily a *bound*,
not a test (no p-value, no multiplicity impact):
- A1: simultaneous 95% MC band on per-ball selection frequencies → largest bias ε_ball
  consistent with data, per game; translated to per-ticket EV impact.
- A2: lasso sparse-bias recovery on per-ball counts; λ calibrated so empty support on
  ≥ 99% of null sims (this is its admission trial). Test statistic: support size > 0.
  Family: 5 games.

**B. Graphon co-occurrence (`src/graphon_cooccurrence.py`)**:
- B1: spectral norm of the centered co-occurrence matrix (proxy for cut-norm distance
  from the constant graphon W ≡ p). Family: 5 games.
- H-protocol: null-correlation of B1 with MP λ_max measured on shared null draws;
  if ρ ≥ 0.90, B1 joins the MP equivalence class and adds 0 to the multiplicity count.

**C. Szemerédi arithmetic progressions (`src/szemeredi_ap.py`)**:
- C1: count of 3-term APs within each draw's 6 numbers, summed over draws, vs MC null
  (two-sided: excess *or* deficit is structure).
- C2: 3-term AP count inside the top-10 hot set per rolling 50-draw window, averaged,
  vs MC null (two-sided).
- Family: 2 statistics × 5 games = 10, pending within-family correlation measurement.

## Multiplicity (registered before running)

Counted tests: A2 (5) + B1 (5 or 0 after H-protocol) + C1, C2 (10) = **≤ 20**.
Batch threshold: Bonferroni **p < 0.0025** (0.05/20), applied to the worst case even if
equivalence classes shrink the family. Exploration hits below threshold motivate a
registered confirmation run; they confirm nothing by themselves.

## Predictions (stated for honesty)

Under the lab's standing conclusion (Case Study 1: no exploitable structure), the
expected outcome is: A1 yields ε bounds of order sqrt(log P / n) with negligible EV
impact; A2 returns empty support; B1 sits inside its null band and likely joins the MP
class; C1/C2 sit inside their null bands, and the C-card's documented theorem-forced AP
rate becomes the durable artifact.
