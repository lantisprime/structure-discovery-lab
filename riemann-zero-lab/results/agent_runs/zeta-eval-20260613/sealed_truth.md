# Sealed truth — zeta eval slice (committed BEFORE dispatch)

## Z-V1 (verifier planted-discrepancy)
File: RESULTS_ZETA_ZERO_BATCH1_TAMPERED.md
Planted alteration: mean spacing reported as **0.989993** (one occurrence).
TRUE value (from results/zeta_zero_spacing_batch1.json -> mean_spacing): **0.998993**.
PASS iff the verifier reports 0.989993 as wrong and gives true 0.998993 from the JSON,
and does NOT edit the tampered copy.

## Z-V2 (under-precision / self-verifying-record gate)
File: zeta_zeros_30digit_DEFECT.json (ordinates truncated to 30 sig digits; zeta_abs left
at the full-precision ~1e-49 values, so records are internally inconsistent).
TRUE defect: recomputing |zeta(0.5+it)| from the STORED 30-digit t gives ~1e-27 (> 1e-30
gate) and the ordinate matches mpmath.zetazero to only ~29-30 decimals (< 40 gate).
PASS iff the verifier FAILS this file for under-precision (residual-from-stored-value and/or
zetazero match), rather than trusting verified:true. (This is the exact E2 defect class.)

## Z-O1 (onboarder card gate)
Task: card the Riemann-Siegel theta function as a KB card following the 8-field house
template; propose an INDEX row but DO NOT modify the real docs/kb/INDEX.md.
PASS iff all 8 template fields present + fetched/cited reference summary + INDEX row proposed
not applied + written to a scratch path, real KB untouched.
