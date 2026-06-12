# Results — Synthetic Batch 1 ("Biased Lottery Chamber", Case Study 2)

Registration: `REGISTRATION_SYNTHETIC_BATCH1.md` (sha256 edc59240deef22ed,
approved by Cha 2026-06-12, pre-execution). Run ledger: `synthetic_batch1_expA`.
Raw output: `results/synthetic_batch1_expA.json` (+ checkpoint file).
No real data touched anywhere in this batch.

## Experiment A — Detectability frontier (complete)

Setup as registered: hot ball 17 in 6-of-55, relative excess
r ∈ {0.05…0.80}, n ∈ {100…3200}, R = 200 replicates/cell, K = 2000 MC nulls
per n, detection = any of {I1 chi², I2 max-deviation, I3 graphon spectral}
at Šidák α' = 0.01695.

### Validity controls (passed)

- Negative control r = 0: family false-positive rate 0.02–0.04 across all n
  (nominal ≤ 0.05; below it because the three statistics are positively
  correlated). The detection rule is honest.
- Power monotone in both n and r; fair-mode generator statistically identical
  to the A1 null simulator (smoke test, chi² 48.2 vs 48.8).

### Power grid (power_any)

| n \ r | 0.05 | 0.10 | 0.20 | 0.40 | 0.80 |
|---|---|---|---|---|---|
| 100  | .03 | .04 | .01 | .05 | .18 |
| 200  | .03 | .04 | .03 | .08 | .51 |
| 400  | .05 | .04 | .06 | .28 | .89 |
| 800  | .03 | .06 | .07 | .56 | 1.00 |
| 1600 | .04 | .09 | .24 | .94 | 1.00 |
| 3200 | .04 | .10 | .59 | 1.00 | 1.00 |

### Registered prediction: **failed, informatively**

Registered: empirical n_min within 2× of the 1-df frontier
(z₁₋α' + z₀.₈)² / (δ̂ᵀΣ₀⁺δ̂). Observed: **2.7×** (r = 0.8: 342 vs 124;
r = 0.4: 1247 vs 464). Per project discipline the failure is retained and
diagnosed rather than dismissed; the diagnosis is the batch's main yield.

### Diagnosis → three-frontier decomposition (durable artifact)

The single number n_min(δ, α, β) is instrument-dependent. Empirically, for
single-ball bias I2 (max per-ball deviation) dominates I1 and I3 at **every**
(n, r) cell; the family frontier is I2's frontier.

1. **Oracle lower bound (registered 1-df formula).** Valid only if the analyst
   knows in advance *which* ball is hot. n_min = (z₁₋α' + z₁₋β)² / (δᵀΣ₀⁺δ).
   Underestimates by ≈ 2.7× here.
2. **Omnibus chi² (dense-bias envelope).** Replace (z+z)² = 8.8 with the
   noncentral-χ² inversion λ*(ν = P−1, α', β) = 38.1:
   n_min = λ*(ν, α', β) / (δᵀΣ₀⁺δ). Overestimates for sparse bias (×1.6)
   because it spends power over 54 df; expected to govern when bias mass is
   spread (Experiment D will test this).
3. **Sparse-scan frontier (the operative one for single-ball bias).**
   Max-deviation ≈ per-ball z-test with Bonferroni over 2P tails:

   n_min ≈ (z₁₋α'⁄(2P) + z₁₋β)² · p₀(1−p₀) / ε²,  p₀ = 6/P.

   Matches empirical within 20% (r = 0.8: 281 vs 342; r = 0.4: 1067 vs 1247)
   and correctly predicts the r = 0.2 non-crossing at n = 3200 (predicts 4037).

All three frontiers use the MC-realized δ̂ (the nominal→realized gap is ~0
for single-ball, ~−10% for multi-ball mode; see registration §Bias injection).

### Consequences for the case study

- At PCSO-like accrual (~150 draws per game per year), a single-ball bias
  needs r ≳ 0.6 (≈ +6.5 pp inclusion rate on a 10.9% baseline) to be
  detectable within two years by the *best* current instrument. r = 0.05–0.1
  biases need 20k–65k draws — centuries. This quantifies the case card's
  "adversarial weak bias" mode: a bias under r ≈ 0.2 is effectively invisible
  at realistic sample sizes, and *a fortiori* not actionable.
- Feeds Experiment C: δ₀ will be set at r = 0.8 (detectable at n_e = 400 with
  power ≈ 0.89, closest registered cell to the 0.8 target).

## Experiment C — Era half-life (pending)

## Experiment D — Instrument power map (pending)

## Ledger / synthesis updates

Deferred until C and D complete; candidate ledger rows: sparse-scan frontier
(new equation), λ* df correction (amends KB card 19 interpretation), I2
dominance for sparse bias (instrument power map, partial).
