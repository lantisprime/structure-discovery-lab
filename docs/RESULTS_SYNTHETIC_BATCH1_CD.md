# Results — Synthetic Batch 1, Experiments C & D

Registration: `REGISTRATION_SYNTHETIC_BATCH1_CD.md` (git `69d39e2`,
sha256 `380cc263da70e124…`, approved by Cha 2026-06-13 with amendments 1–5,
pre-execution). Run script: `src/synthetic_batch1_expCD.py`. Raw output:
`results/synthetic_batch1_expCD.json` (+ checkpoint). Instrument identity is
shared with Experiment A (A's `stats3` / `p_mc` imported verbatim). **No real
data touched anywhere in this batch.** Reported expectation-free: the only
mechanism statements registered were instrument-validity controls; outcomes
below are measurements, not confirmations of a prediction.

## Validity controls (both experiments admissible)

- **C, fair-continuation calibration:** exploration family FPR = 0.045 (≤ 0.05);
  confirmation false-survival = 0.0 over the 9 false exploration fires. Honest.
- **C, τ = ∞ control (amend 1):** S(∞) = 0.526 vs the carried-instrument-weighted
  standalone reference 0.498 — agree within the 2-SE band; and S(∞) exceeds the
  fair false-survival (0.0) by > 2 SE. **PASS.** (This is exactly why the floor
  was retargeted off "≥ 0.8": the n_c = 200 confirmation window caps achievable
  survival near 0.5 for this effect, so an absolute 0.8 would have falsely failed
  a correctly-wired protocol.)
- **D, c = 0 negative control:** per-instrument FPR I1 = 0.025, I2 = 0.005,
  I3 = 0.020 (all ≤ 0.05). **PASS.**
- **D, c = 1 cross-experiment consistency (amend 5):** D's single-ball powers
  (I1 = 0.255, I2 = 0.450, I3 = 0.160) agree with A's r = 0.40 / n = 800 cell
  (0.235 / 0.495 / 0.155) within the two-proportion 2-SE band for every
  instrument (diffs 0.020, 0.045, 0.005 vs tolerances 0.086, 0.100, 0.073).
  **PASS** — D's generator and wiring reproduce A.

## Experiment C — Era half-life (complete)

δ₀ = A's r = 0.8 single-ball process (hot ball 17); n_e = 400, n_c = 200,
R = 200; exploration detector = any of {I1, I2, I3} at Šidák α′ = 0.01695; one
α = 0.05 confirmation re-test of the carried (smallest-p, ties I2→I1→I3)
instrument on continuation draws.

| τ | explore power | fired | survived | S(τ) | I4 persistence | carried I1/I2/I3 |
|---|---|---|---|---|---|---|
| 25  | 0.025 | 5   | 0  | guard (<20) | 0.060 | 1/3/1 |
| 50  | 0.045 | 9   | 1  | guard (<20) | 0.045 | 4/4/1 |
| 100 | 0.040 | 8   | 0  | guard (<20) | 0.050 | 3/3/2 |
| 200 | 0.120 | 24  | 1  | 0.042 | 0.045 | 2/15/7 |
| 400 | 0.350 | 70  | 1  | 0.014 | 0.125 | 7/59/4 |
| 800 | 0.595 | 119 | 8  | 0.067 | 0.265 | 8/110/1 |
| ∞   | 0.875 | 175 | 92 | 0.526 | 0.560 | 2/173/0 |

**τ_min = none.** No registered τ reaches the S ≥ 0.8 bar — and the no-decay
ceiling itself is only S(∞) = 0.526, set by the n_c = 200 confirmation window
(standalone reference ≈ 0.50 for the dominant instrument), not by the decay.
What the grid *does* show, descriptively:

- Confirmation survival collapses steeply once the decay constant drops below the
  exploration window: S falls 0.526 (∞) → 0.067 (τ = 800) → 0.014 (τ = 400), and
  by τ ≤ 200 the exploration step itself rarely fires (denominator < 20, M5
  guard active — no point rate reported).
- **I4 rolling-window persistence is monotone in τ** (0.05 at τ ≤ 100 → 0.265 at
  τ = 800 → 0.560 at ∞), behaving as a persistence detector: it gains power as
  the signal lives longer, complementing the single-window exploration detector.
- The carried instrument is **overwhelmingly I2 (max-deviation)** — 173/175 at
  τ = ∞ — consistent with A's single-ball sparse-scan frontier.

Operational reading (synthetic, calibration only): for a single-ball bias at this
amplitude, a two-stage exploration→confirmation protocol with a 200-draw
confirmation window cannot reach 0.8 confirmation survival even with no decay; the
binding constraint is confirmation-window size, and any decay with τ ≲ n_e erases
the signal before confirmation.

## Experiment D — Instrument power map (complete)

Total bias mass fixed at A's r = 0.40 single-ball realized mass, spread evenly
over c balls (nested registered sets); n = 800, R = 200; per-instrument power at
Šidák α′.

| c | balls | I1 χ² | I2 max-dev | I3 graphon | max realized δ̂ |
|---|---|---|---|---|---|
| 0  | 0  | 0.025 | 0.005 | 0.020 | 0.00000 |
| 1  | 1  | 0.255 | 0.450 | 0.160 | 0.04247 |
| 2  | 2  | 0.115 | 0.080 | 0.065 | 0.02181 |
| 4  | 4  | 0.060 | 0.015 | 0.040 | 0.01187 |
| 8  | 8  | 0.035 | 0.005 | 0.025 | 0.00666 |
| 16 | 16 | 0.030 | 0.015 | 0.025 | 0.00407 |

Descriptive findings (expectation-free):

- **The sparse/dense instrument ranking inverts with spread.** At c = 1 (mass
  concentrated) I2 max-deviation leads (0.450 vs I1 0.255) — A's sparse-scan
  regime. At c = 2 the per-ball deviation has already halved and I2 falls *below*
  I1 (0.080 vs 0.115): the omnibus χ², which pools deviations across balls,
  becomes the relatively stronger instrument as soon as the bias is no longer
  single-ball. This is the empirical counterpart of A's two-frontier story
  (sparse-scan governs concentrated bias; the df-54 omnibus governs spread bias).
- **Detectability dies fast at fixed mass.** By c = 4 every instrument is at
  0.015–0.060 and by c = 8 all three sit at the c = 0 false-positive floor: with
  the r = 0.40 mass spread over ≥ 8 balls, no current instrument retains usable
  power at n = 800. The realized per-ball δ̂ at c = 8 (0.0067) is in A's
  r ≈ 0.06 single-ball regime — A already showed that needs tens of thousands of
  draws.

## Ledger / synthesis candidates (now that A, C, D are complete)

For promotion review (not yet promoted): (1) sparse-scan vs df-54 frontier
crossover, now supported from both A (single-ball, varying n) and D (fixed n,
varying spread); (2) confirmation-window bound on era confirmation — τ_min is
governed by n_c, not decay alone, when n_c is small relative to the effect's
single-window n_min; (3) I4 persistence as a τ-monotone complement to the
single-window family. Each is a calibration result on synthetic data — structure,
not actionable edge (A7 gate unchanged).

## Recompute snippet

```python
import json
d = json.load(open("results/synthetic_batch1_expCD.json"))
print(d["C"]["tau_min"], d["C"]["validity_tau_inf"]["PASS"])      # None True
print({k: v["S"] for k, v in d["C"]["cells"].items()})            # S(tau) grid
print(d["D"]["validity"]["PASS"])                                  # True
print({c: d["D"]["cells"][c]["power_I2"] for c in ["0","1","2","4","8","16"]})
```
