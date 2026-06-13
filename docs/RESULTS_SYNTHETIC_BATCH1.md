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
single-ball bias I2 (max per-ball deviation) dominates I1 and I3 in the
detectable sparse-bias regime and determines the practical frontier; low-power
cells fluctuate at Monte Carlo noise levels (where which instrument is nominally
"highest" flips between I1/I2/I3 within ±0.02, i.e. ≤ 1 R=200 replicate). The
family frontier is therefore I2's frontier wherever there is power to speak of.

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

## Experiment C — Era half-life (complete → `RESULTS_SYNTHETIC_BATCH1_CD.md`)

Run under the expectation-free re-registration `REGISTRATION_SYNTHETIC_BATCH1_CD.md`
(git `69d39e2`), which supersedes the parent registration's §C. Outcome:
**τ_min = none** — no registered τ reaches confirmation-survival 0.8, and the
no-decay ceiling itself is only S(∞) = 0.526, bound by the n_c = 200 confirmation
window rather than the decay. The τ=∞ validity control PASSED. Full grid, I4
persistence curve, and carried-instrument distribution in the C/D results doc.

## Experiment D — Instrument power map (complete → `RESULTS_SYNTHETIC_BATCH1_CD.md`)

Same re-registration (supersedes parent §D). Outcome: at fixed r=0.40 mass the
sparse/dense instrument ranking **inverts** with spread (I2 max-dev leads at c=1,
I1 omnibus χ² overtakes by c=2), and detectability dies by c ≥ 4–8. c=0 FPR and
c=1 cross-experiment consistency controls both PASSED. Full table in the C/D doc.

## Registration deviations (logged, not tuned away)

The approved registration `REGISTRATION_SYNTHETIC_BATCH1.md`
(sha256 `edc59240deef22ed`) is left **byte-for-byte unmodified** — per the
project rule that the registered past stays honestly labeled. The two gaps
between that registration and what actually ran are recorded here instead.

1. **I2 instrument identity.** Registration §Instruments calls I2
   "Lasso sparse-bias support (`concentration_exclusion.py` A2 pattern)". The
   committed run script `src/synthetic_batch1_expA.py` implements **max per-ball
   count deviation** (`maxdev = |cnt − e|.max()`), a sparse-scan / max-deviation
   statistic, not a lasso. No lasso was fit in this batch. All results text and
   the derived frontier (§Diagnosis, item 3) therefore refer to I2 as
   **"max-deviation / sparse scan"**; the registered "lasso" label is treated as
   an unfulfilled intent, not a description of the run. A genuine lasso-support
   instrument, if added later, would be onboarded as a separate I2′ and rerun —
   it is not interchangeable with the committed max-deviation statistic.

2. **Derived-frontier reproducibility.** The df-corrected (df-54, noncentral-χ²
   inversion) and sparse-scan frontier fields in `synthetic_batch1_expA.json`
   were originally added out-of-band (the checkpoint records the addition, but
   the committed `theory()` did not compute them). `theory()` has now been
   patched to compute all three frontiers, and `src/verify_synthetic_batch1.py`
   recomputes the JSON's frontier fields from scratch and asserts agreement
   (28/28 fields PASS). The published numbers are unchanged: the 1-df oracle,
   sparse-scan, λ₁, and δ̂ fields reproduce bit-for-bit; the df-54 omnibus values
   (λ\*=38.09 and the three `n_min_theory_df54`) match to machine precision
   (≤5×10⁻¹⁶ relative — a single float ULP, the only difference between the
   original out-of-band ncx2 solve and the in-code `brentq`). Regenerating also
   filled in df-54 / sparse-scan fields for the r=0.05 and 0.10 cells, which the
   out-of-band pass had left blank; no existing value moved. The patch only makes
   the frontiers regenerable from source.

Neither deviation touches the retained registered-prediction failure (empirical
n_min ≈ 2.7× the 1-df oracle), which stands as the batch's primary yield.

## Ledger / synthesis updates

**C and D are now complete** (`RESULTS_SYNTHETIC_BATCH1_CD.md`, git `856322c`;
both validity controls PASS). Candidate ledger rows, now supported across A+C+D
and itemized in the C/D doc — **flagged for review, not yet promoted**:
sparse-scan vs df-54 omnibus frontier crossover (A varying n, D varying spread),
λ\* df correction (amends KB card 19 interpretation), the n_c-bound on era
confirmation (τ_min governed by confirmation-window size, not decay alone), and
I4 persistence as a τ-monotone complement to the single-window family.
