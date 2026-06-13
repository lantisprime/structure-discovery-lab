# VERIFICATION REPORT — synthetic_batch1_expCD

**Verifier:** author mechanical verification (deterministic recompute; not the
independent-verifier agent — an independent pass can be added if desired).
**Date:** 2026-06-13
**Run:** synthetic_batch1_expCD (Experiments C + D)
**Registration:** `docs/REGISTRATION_SYNTHETIC_BATCH1_CD.md` sha256 `380cc263da70e124`
(git `69d39e2`, approved pre-execution by Cha with amendments 1–5)
**Output:** `results/synthetic_batch1_expCD.json` (sha256 `979b1fefa4d5a6a9`)

---

## CHECK 1: Reproducibility (two-run rule)

**Result: PASS — byte-identical.**

The script is fully seeded/deterministic (`MASTER = 20260612`). Two independent
fresh executions of `C` then `D` were run into isolated paths (output redirected
to sandbox `/tmp`, because the repo mount blocks `unlink` so the committed file
cannot be removed for an in-place rerun):

- run 1 sha256: `979b1fefa4d5a6a9…`
- run 2 sha256: `979b1fefa4d5a6a9…`
- committed   : `979b1fefa4d5a6a9…`
- **run1 == run2 == committed: YES.** The committed JSON is regenerable from
  source bit-for-bit.

## CHECK 2: Cross-check results doc vs JSON

**Result: PASS — every cited number matches.**

`docs/RESULTS_SYNTHETIC_BATCH1_CD.md` was checked programmatically against the
JSON (tolerance ±0.0005 on rates, ±0.0001 on δ̂). Coverage:

- C validity block: fair FPR 0.045, confirmation false-survival 0.0, S(∞) 0.526,
  carried-weighted reference 0.498, PASS flag, ref power (0.355/0.500/0.270),
  τ_min = none.
- C grid (all 7 τ): explore power, n_fired, n_survive, S(τ), I4 persistence, and
  carried-instrument counts I1/I2/I3 — all rows exact.
- D grid (all 6 c): per-instrument power (I1/I2/I3) and max realized δ̂ — exact.
- D validity: PASS flag and the c=1 consistency diffs/tolerances.

No mismatch (0 of the checked fields).

## CHECK 3: Validity controls (admissibility)

**Result: PASS — both experiments admissible.**

- **C, fair-continuation calibration:** exploration family FPR 0.045 ≤ 0.05;
  confirmation false-survival 0.0. Honest re-test.
- **C, τ=∞ control (amendment 1):** S(∞) = 0.526 within the two-proportion 2-SE
  band of the carried-weighted standalone reference 0.498, and exceeds the fair
  false-survival (0.0) by > 2 SE. `validity_tau_inf.PASS = true`.
- **D, c=0 negative control:** per-instrument FPR 0.025 / 0.005 / 0.020, all
  ≤ 0.05.
- **D, c=1 cross-experiment consistency (amendment 5):** single-ball powers
  0.255 / 0.450 / 0.160 agree with A's r=0.40/n=800 cell 0.235 / 0.495 / 0.155
  for every instrument within the 2-SE band (diffs 0.020 / 0.045 / 0.005 vs
  tolerances 0.086 / 0.100 / 0.073). `validity.PASS = true`.

## CHECK 4: Registration conformance

**Result: PASS.**

- Instrument identity is shared with Experiment A — `stats3` and `p_mc` are
  imported verbatim from `synthetic_batch1_expA`, so I1/I2/I3 are bit-identical
  across A/C/D (no reimplementation drift).
- D ball sets in the JSON match the nested sets enumerated in registration §D.4,
  including c=0 = {} (zero-mass control).
- C multi-fire rule (amendment 2: smallest exploration p, ties I2→I1→I3) and the
  S(τ) denominator + M5 guard (amendment 3: denominator < 20 → no point rate) are
  implemented as registered; the τ ≤ 100 cells correctly report `S = null`
  (under-powered guard active).
- Expectation-free: no predicted outcomes are asserted; the only mechanism
  statements exercised are the registered instrument-validity controls.

---

## VERDICT

**PASS (4/4 checks).** Run `synthetic_batch1_expCD` is reproducible
(byte-identical), its results doc is faithful to the JSON, both validity controls
pass (C and D admissible), and execution conforms to the frozen registration.
Reported expectation-free. No rerun recommended.

Recompute (from repo root):

```bash
python3 -c "import json;d=json.load(open('results/synthetic_batch1_expCD.json'));\
print(d['C']['tau_min'], d['C']['validity_tau_inf']['PASS'], d['D']['validity']['PASS'])"
# -> None True True
```
