# ADMISSION_RELATIONAL v2 — R1–R7 Re-admitted Under Remediation-Era Gates

2026-07-02 · artifact: `results/readmission_v2.json` · harness: `src/readmit_r1_r7.py`
Supersedes the admission *evidence* (not the instruments) of ADMISSION_RELATIONAL.md.
Trigger: AUDIT_CORRECTNESS_2026-07-02.md G-4 — the original admissions predate the
remediation standard (negative n=50–100, m=19 floors at α, continuous KS on lattice
p-values, shared rng streams).

## Gates applied (the r8 standard, plus the adversarial-review fix)

n_neg = 200 per instrument; m ≥ 39 everywhere (floor 0.025 ≤ α/2); FPR band centered
at the exact lattice value of P(p ≤ α) ± 3 SE; uniformity via lattice-exact χ²
(expected bin masses computed from the actual add-one lattice, χ² p Monte-Carlo
calibrated — the first harness draft used flat 20-bin expectations, which would have
falsely demoted a perfectly calibrated instrument 87% of the time at m=39; caught by
adversarial code review B2 and fixed before any full run completed); split per-trial
rng_data/rng_null streams (the m6 fix); positive gate power ≥ 0.8 at the ORIGINAL
declared effect sizes (re-run, not re-tune — M1 discipline). Execution is
chunk-resumable with per-trial seed-derived streams (sandbox constraint; identical
results to a monolithic run by construction).

## Results — all seven re-admitted

| Instrument | FPR@α (exp., ±3SE) | lattice χ² p (MC) | power @ declared effect | verdict |
|---|---|---|---|---|
| R1 MMD/energy | 0.080 (0.050 ± 0.046) | 0.917 | 0.99 | **ADMITTED_V2** |
| R2 Gromov–Wasserstein | 0.075 (0.050 ± 0.046) | 0.483 | 0.98 | **ADMITTED_V2** |
| R3 CCA family | 0.060 (0.050 ± 0.046) | 0.843 | 1.00 | **ADMITTED_V2** |
| R4 TDA persistence | 0.025 (0.050 ± 0.046) | 0.506 | 1.00 | **ADMITTED_V2** |
| R5 graph spectra | 0.050 (0.050 ± 0.046) | 0.194 | 0.99 | **ADMITTED_V2** |
| R6 Nyström landmarks | 0.030 (0.040 ± 0.042) | 0.060 | 0.94 | **ADMITTED_V2** |
| R7 matrix completion | 0.045 (0.050 ± 0.046) | 0.894 | 1.00 | **ADMITTED_V2** |

Notes: every FPR sits inside its band; every lattice-χ² p > 0.01; every power ≥ 0.94
at the originally declared gating effects. R6's expected FPR is 0.04 (m=49 lattice
has no point in (0.04, 0.05]) — the exact-lattice centering matters, exactly as the
review argued. R2, previously the weakest admission (n=50, m=19), now carries
200-trial evidence at m=39; note this re-admits the *instrument's calibration on its
synthetic controls* — the separate GW G0 demotion for real-data distributional
miscalibration at n=200 (REMEDIATION M2) remains in force and is untouched by this
result.

## Ledger

Synthetic-control run: 0 real-data tests charged; run-ledger row
`readmission_v2` (G1 instrument validation). ADMISSION_RELATIONAL.md and
docs/kb/INDEX.md rows 20–26 should be read through this document (see
docs/SUPERSEDED_LABELS.md).
