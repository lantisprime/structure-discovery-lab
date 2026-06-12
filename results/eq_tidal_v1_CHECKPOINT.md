# CHECKPOINT — eq_tidal_v1 (Phase 5 calibration run)

Executor: equation-analyst (execute dispatch), NOT batch5 detection analyst (independence OK).
Registration: docs/REGISTRATION_EQ_TIDAL.md, sha256 9df78eca25e20ab5... — verified against
results/commitment_ledger.txt line (match). Approved pre-fit. Binding.

Gate check (rule 1): source claim tidal-manila TDA H1 STRUCTURED (batch5), attribution on
file, registration approved+hashed pre-fit → PROCEED.

## Step plan
1. [done] Write src/eq_tidal_v1.py -> src/eq_tidal_v1.py (scipy+ripser installed, same stack as batch5)
2. [done] Full registered pipeline executed (fit, 1200 null discoveries, 1000 bootstrap
       discoveries, residual checks 1-7) -> results/eq_tidal_v1.json
3. [done] Outputs persisted -> results/eq_tidal_v1.json sha256 a239f13a2cd1d4db
4. [done] Two-run rule: in-process double run byte-identical AND two external executions
       byte-identical (cmp empty, same sha256)
5. [done] RESULTS doc -> docs/RESULTS_EQ_TIDAL.md

## Outcome
- Claim A (Total tidal accel): FAILED_EQUATION_SEARCH + miscalibration flag; calibration
  FAIL (anomalistic 27.487 d PASS 0.25% err; spring-neap NOT recovered — 2nd freq took the
  evection-band line 30.64 d; 14.65 d peak sits in residual Fisher g p=8.6e-21).
  Phase-surrogate null not beaten (p=0.209).
- Claim B (Moon Dist): FAILED_EQUATION_SEARCH (structured residuals — deterministic
  ephemeris data vs declared Gaussian noise model); calibration PASS
  (27.604 d, 0.18% err, CI [27.371,27.846] contains 27.555; all 3 nulls beaten p=0.005).
- RUN COMPLETE; ledger deltas proposed in RESULTS doc, not applied (orchestrator).

Deviations declared: scipy unavailable -> numpy-only implementations (LS via lstsq,
golden-section/parabolic refine on omega; chi2/F p-values via numpy incomplete gamma
series implemented in-script; TDA H1 via same approach as batch5 if lightweight, else
sparse Rips on subsample). All conservative.
