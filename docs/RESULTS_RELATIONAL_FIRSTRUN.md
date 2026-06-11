# First Registered Relational Run — Results

**Date**: 2026-06-11 · **Script**: `src/relational_first_run.py` ·
**Raw output**: `results/relational_first_run.json` · seed 20260611 ·
**Protocols**: CROSS_DATASET_FRAMEWORK §4 (subset-to-whole) and §5/§3.2 (paired CCA).

## Registered expectations (declared in the script header before execution, A6)

- **H-R1** — subset-to-whole recovery curves rise above the matched temporal null for
  the three physical series (tidal acceleration, moon distance, Kp daily mean).
- **H-R2** — the lotto draw-sum series and the 6/55 presence matrix sit on the null
  line at every subset fraction (the i.i.d. control / entropy-floor prediction).
- **H-R3** — date-paired CCA between 6/55 draw features and physical covariates is
  null under the shuffled-pairing null (relational replication of ledger row 2).
- **H-R4** — date-paired CCA between tidal accelerations and sun/moon ephemerides is
  strongly positive (known mechanism: the tidal columns are *derived* from those
  ephemerides — a real-data positive control, not a discovery).

## 1. Recovery curves (model: k-NN(2) on the time index; null: within-series value permutation; 10 repeats × m=49; series standardized)

Null-adjusted z (mean over repeats) by subset fraction:

| Series (n) | 1% | 2% | 5% | 10% | 20% | 40% | Curve shape (§4.5 taxonomy) |
|---|---|---|---|---|---|---|---|
| tidal_total_accel (366) | +0.16 | −0.19 | +0.73 | **+4.65** | **+12.10** | **+19.68** | strong structure from k=10% |
| moon_distance_km (366) | −0.32 | +0.26 | +0.76 | **+3.47** | **+11.55** | **+19.29** | strong structure from k=10% |
| kp_daily_mean (365) | −0.00 | +0.03 | +0.40 | +0.99 | **+1.95** | **+3.65** | smooth rise — real but noisy |
| lotto655_draw_sum (156) | −0.25 | +0.56 | −0.06 | −0.14 | −0.40 | +0.13 | **flat at the null line** |

Median permutation p reaches the floor (0.02 at m=49) for tidal and moon from k=10%
and for Kp from k=20%; the lotto draw-sum median p stays in 0.34–0.64 at every k.

**H-R1 confirmed; H-R2 (draw-sum) confirmed.** The two ephemeris-driven series are
nearly deterministic given a 10% subset; Kp recovers more slowly (storm bursts are
not smooth); the lotto series is statistically indistinguishable from its own
permutation at every subset size — the honest negative the framework predicts for
i.i.d. data, and the relational restatement of the entropy floor.

## 2. Lotto 6/55 presence-matrix recovery (null: 6-of-55 uniform constrained generator, A1; m=199)

| k | 1% | 2% | 5% | 10% | 20% | 40% |
|---|---|---|---|---|---|---|
| median p | 0.265 | 0.075 | 0.355 | 0.122 | 0.503 | 0.360 |
| mean z | +0.18 | +1.02 | +0.57 | +0.77 | +0.28 | +0.38 |

No point reaches significance at any subset fraction. **H-R2 (presence) confirmed.**
The uniformly mildly positive z (≈ +0.2 to +1.0 at every k) is consistent with the
known era-bounded 6/55 #45 excess present in these rows — the C9 shadow, noted and
not double counted: under C9 it joins the existing #45 equivalence class and adds no
new multiplicity-adjusted evidence.

## 3. Date-paired CCA (ridge γ=0.1, time-ordered 60/40 split, shuffled-pairing null m=199)

| Pairing | held-out ρ₁ | null 95% quantile | p |
|---|---|---|---|
| 6/55 draw features vs physical covariates (H-R3) | 0.110 | 0.203 | 0.17 |
| tidal accelerations vs sun/moon ephemerides (H-R4) | **0.9977** | 0.140 | **0.005** (floor at m=199) |

**H-R3 confirmed null** — the relational instrument agrees with the 12 covariate
permutation tests (ledger row 2): no draw–physics coupling. **H-R4 confirmed
positive** — the pipeline detects the one relationship in these datasets with a known
mechanism, at the maximum strength the permutation resolution allows. Together they
show the instrument detects real relations and stays silent otherwise, *on real
data*, completing the positive/negative-control pair at the dataset level.

## Verdict

The relational face behaves exactly as the constitution predicts: structure where
physics puts it, silence where the entropy floor is. The lotto datasets serve as the
lab's certified real-data negative control for all future relational instruments.
No relational edge exists to feed the decision layer: Doob still gates, Kelly still
sizes at zero (THEOREM_SYNTHESIS §3 and §6 unchanged).

*Limitations*: single-game presence test (6/55 only); recovery model is k-NN
smoothness only (a richer model class would need its own multiplicity charge, A3);
CCA split is a single time-ordered fold; admission shapes ≠ these data shapes for
R2/R4/R5/R7 (those instruments have not yet touched real data — their first real runs
must re-run negative controls at matched shape, Part 4 D7).
