# Pre-Registration — Synthetic Batch 1, Experiments C & D (expectation-free)

Status: **APPROVED WITH AMENDMENTS by Cha, 2026-06-13 — FROZEN.** No run script
exists yet; this registration is git-committed (and its sha256 recorded) before
any C/D code produces results (C1 rule); the results commit will reference this
file's SHA.
Analyst: Claude (with Cha). Class: **CALIBRATION / EXPLORATION** — synthetic data
only, no claim about any real lottery. Ground truth is planted.

## Amendments applied at approval (Cha, 2026-06-13)

Five conditions from the approval, all applied below (none introduces a predicted
outcome; each tightens calibration or specification):
1. **C τ = ∞ validity control** — retargeted from an absolute "power ≥ 0.8" floor
   (miscalibrated for the n_c = 200 confirmation window) to agreement with the
   firing instrument's independently-computed α = 0.05 power at n = n_c (§C.5).
2. **C multi-fire confirmation rule** — when several exploration instruments fire,
   exactly one is carried to confirmation: smallest exploration p, ties broken
   I2 → I1 → I3 (§C.3).
3. **C S(τ) denominator rule** — denominator = count of exploration firings (all
   true positives under planted bias); M5 guard for denominator < 20 (§C.5).
4. **D ball sets** — enumerated and nested in-registration, with **c = 0** added
   as the explicit zero-mass negative control (§D.4).
5. **D consistency tolerance** — restated as a two-proportion 2-SE band, replacing
   the erroneous "±0.05 ≈ ±1 of R = 200" parenthetical (§D.5).

## Scope and supersession

This document registers Experiments **C** (era half-life) and **D** (instrument
power map) under the amended, **expectation-free** protocol
(`RELATIONAL_RUNBOOK.md` Phase 1, amended 2026-06-11; `REMEDIATION_LOG.md`
"Protocol change first"). It **supersedes §C and §D of
`REGISTRATION_SYNTHETIC_BATCH1.md`** (sha256 `edc59240deef22ed`), whose C/D
sections carried registered *predicted outcomes* now forbidden in discovery
registrations. Experiment A stands exactly as run; nothing in A is re-opened.
Predicted results appear nowhere below — the only mechanism statements are
clearly-labeled **instrument-validity controls** (calibration: "the pipeline
must do X or the pipeline is broken"), never discovery expectations.

## Carried-over setup (unchanged from the parent registration)

- Pool P = 55, k = 6 (Synthetic 6/55), generator
  `src/domains/synthetic_lottery.py` (Gumbel top-k weighted without-replacement).
- Null simulator (A1): i.i.d. uniform 6-of-55 `core.discrete_draws.fast_draws`;
  the fair mode of the generator is provably identical to it.
- Master seed 20260612; per-cell seeds `master*10**6 + cell_index`, recorded in
  the results JSON. +1-corrected MC p-values throughout (`stats.p_perm`).
- **δ₀ for Experiment C** is fixed by A's grid, not chosen post hoc: the smallest
  registered r detectable at n_e = 400 with family power ≥ 0.8. From
  `RESULTS_SYNTHETIC_BATCH1.md` that is **r = 0.8** (power_any = 0.885 at
  n = 400; r = 0.4 gives 0.28). δ₀ = the MC-realized δ̂ of the r = 0.8 single-ball
  spec (hot ball 17), δ̂_hot ≈ 0.0828.
- **I2 is the max-deviation / sparse-scan statistic** as committed
  (`maxdev = |cnt − e|.max()`), per the logged registration deviation in
  `RESULTS_SYNTHETIC_BATCH1.md` — *not* a lasso. Any future lasso instrument is a
  separate I2′ requiring its own onboarding and run.

---

## Experiment C — Era half-life (decay τ)

**1. Claim type.** Predictive generalization (exploration → confirmation
survival): an operating-characteristic measurement of the confirmation protocol
as a function of the bias decay constant τ. No similarity/causal claim is made.

**2. Representation bundle.** Presence matrix only
(`core.discrete_draws.presence`). One representation; no extras charged.

**3. Instruments + statistics (sidedness declared, all upper-tail).**
- Exploration detector: the A family {I1 per-ball χ², I2 max-deviation, I3
  graphon spectral norm}, detection = any test ≤ Šidák α′ = 0.01695, exactly as
  in A.
- Confirmation re-test: a **single** instrument carried from exploration,
  recomputed on confirmation draws only, at α = 0.05 (the family was spent by the
  exploration hit, A6). **Multi-fire rule (amendment 2):** when more than one
  exploration instrument is below α′, the one with the **smallest exploration
  p-value** is carried to confirmation; exact ties (e.g. identical permutation p
  at the MC floor) break by the fixed priority order **I2 → I1 → I3** (I2 is A's
  dominant single-ball detector). Exactly one instrument is ever re-tested,
  preserving the single-test α = 0.05 confirmation and the A6 family-spend logic.
  The carried instrument's identity is recorded per replicate in the results JSON.
- I4 rolling-window persistence (cross-window deviation correlation,
  `half_deviation_corr` generalization), upper-tail, computed over the full
  n_e + n_c span as the registered persistence instrument for era structure.

**4. Matched null.** Fair continuation: the A1 uniform generator run for the same
n_e + n_c with the decay clock attached to a *zero-amplitude* spec — preserves
the draw constraints and the exploration→confirmation split timing, destroys only
the persistent bias. Confirmation-survival and I4 are both calibrated against this
null with K = 2000 MC replicates, +1-corrected. Floor rule: 1/(K+1) ≤ α/2 for
every threshold used (satisfied: α = 0.05 → need K ≥ 39; α′ → need K ≥ 117).

**5. Decision rule & falsification criteria.**
- Reported statistic (**amendment 3, S(τ) denominator**): confirmation-survival
  rate
  S(τ) = (# replicates whose exploration fired **and** whose carried-instrument
  confirmation re-test has p ≤ α = 0.05) / (# replicates whose exploration fired).
  Every replicate in C carries the planted r = 0.8 bias, so every exploration
  firing is a true positive — the denominator is the count of exploration
  detections, with no false-positive contamination (the fair-continuation null
  run measures the false-survival rate separately, not in this denominator).
  **Denominator guard (M5):** if the denominator < 20 (sparse firing, e.g. at
  small τ), S(τ) is reported as *undefined / under-powered* with its raw
  (numerator, denominator) shown — never as a point rate — and such cells cannot
  define τ_min. τ_min = the smallest registered τ with denominator ≥ 20 and
  S(τ) ≥ 0.8. I4 persistence power vs τ is reported alongside under the same guard.
- Against the null: S(τ) and I4 indistinguishable from the fair-continuation null
  band across all τ ⇒ no detectable persistence; logged as an honest negative,
  not retried.
- **Instrument-validity control (amendment 1; calibration, not a prediction):**
  the τ = ∞ cell (no decay; the full r = 0.8 persistent process runs through both
  windows) calibrates the confirmation wiring against the **n_c = 200 confirmation
  window**, not against an absolute floor. The confirmation re-test is one
  instrument at α = 0.05 on only n_c = 200 draws, so its achievable power is
  bounded by that window — A shows the firing instrument (I2) at ≈ 0.48 at
  n = 200, α′ — and an absolute "≥ 0.8" would be miscalibrated. Instead: (a)
  compute once, on the side, the firing instrument's single-test α = 0.05 power at
  n = n_c = 200 under the r = 0.8 process, S_ref; (b) S(∞) must agree with S_ref
  within a two-proportion 2-SE band (≈ ±0.10 at R = 200); and (c) S(∞) must exceed
  the fair-continuation false-survival rate (≈ 0.05) by at least that band. If
  S(∞) collapses toward the null rate, the confirmation protocol — not the signal
  — is broken and C is inadmissible until fixed. Symmetric calibration: the
  fair-continuation null must show confirmation false-survival ≤ α = 0.05 and
  family FPR ≤ 0.05 (honest re-test).

**6. Multiplicity charge.** Power/operating-characteristic study: each τ cell's
rule is the unit being measured, so τ cells are **not** a testing family — no
cross-τ correction. Per replicate the only multiplicity is the m = 3 Šidák
exploration family plus one α = 0.05 confirmation re-test (family fixed by the
exploration hit). I4, if reported as a detector rather than a descriptor, is its
own single test at α = 0.05 and is labeled as such.

**7. Era / freeze declaration.** Exploration = first n_e = 400 draws;
confirmation = next n_c = 200 draws, generated by *continuing the same decay
process* (decay clock keeps running, `biased_draws(..., t0=n_e)`). Confirmation
draws are never seen by the exploration detection step. τ ∈ {25, 50, 100, 200,
400, 800, ∞}; R = 200 replicates per τ.

---

## Experiment D — Instrument power map (bias spread c)

**1. Claim type.** Instrument power map: a calibration measurement of per-
instrument detection probability as a fixed total bias mass is spread across more
balls. Descriptive operating characteristics, no discovery claim.

**2. Representation bundle.** Presence matrix only. One representation.

**3. Instruments + statistics (upper-tail).** I1 per-ball χ², I2 max-deviation /
sparse scan, I3 graphon co-occurrence spectral norm — each evaluated
*separately* (per-instrument power, not the any-of family), at Šidák α′ over the
m = 3 family so curves are comparable to A.

**4. Matched null + bias spread (amendment 4, explicit ball sets incl. c = 0).**
A1 uniform 6-of-55, K = 2000 MC, +1-corrected, floor rule as in C. The bias mass
is spread evenly over c balls for **c ∈ {0, 1, 2, 4, 8, 16}**. The ball sets are
fixed here, **nested**, and chosen before any run:

- **c = 0: { }** — zero-mass **negative control** (fair generator; no hot balls).
- c = 1: {17} — same hot ball as A, anchoring the c = 1 consistency control.
- c = 2: {17, 38}
- c = 4: {17, 38, 9, 46}
- c = 8: {17, 38, 9, 46, 3, 22, 31, 52}
- c = 16: {17, 38, 9, 46, 3, 22, 31, 52, 7, 14, 25, 33, 41, 48, 54, 11}

For c ≥ 1 the total realized bias mass is held fixed at the realized mass of A's
r = 0.40 single-ball cell and split evenly (per-ball nominal excess = total / c);
the multi-ball realized δ̂ is measured by MC (≈ −10 % nominal→realized gap, per
parent §Bias injection) and is what any frontier comparison uses. n = 800,
R = 200 per c cell.

**5. Decision rule & falsification criteria.**
- Reported statistic: per-instrument detection probability vs c (three power
  curves). No single threshold verdict — the map *is* the deliverable.
- Against the null: any instrument whose c = 0/zero-mass FPR exceeds 0.05 is
  miscalibrated and pulled from the map.
- **Instrument-validity control (amendment 5; calibration, not a prediction):**
  at c = 1 (single hot ball 17, same realized mass as A's r = 0.40 cell) D's
  per-instrument powers *must* agree with A's r = 0.40 / n = 800 cell
  (I1 ≈ 0.235, I2 ≈ 0.495, I3 ≈ 0.155) within a **two-proportion 2-SE band**:
  |p_D − p_A| ≤ 2·√(p̂(1−p̂)(1/R_D + 1/R_A)), with R_D = R_A = 200 and p̂ the
  pooled rate — i.e. ≈ ±0.10 per instrument near p ≈ 0.5, tightening to ≈ ±0.05
  near p ≈ 0.15. (Both A and D estimate these rates from R = 200 replicates, so
  the tolerance is the sampling spread of a *difference of two* such estimates,
  not of one — the earlier "±0.05 ≈ ±1 of R = 200" was wrong: ±0.05 at R = 200 is
  ±10 replicates.) A mismatch beyond this band means D's generator or wiring
  disagrees with A and D is inadmissible until reconciled. This control fixes
  cross-experiment consistency; it asserts nothing about c > 1.

**6. Multiplicity charge.** Power study: c cells are the unit measured, not a
family — no cross-c correction. Per cell the three instruments are reported
individually at the same α′ used in A.

**7. Era / freeze declaration.** No exploration/confirmation split in D (single-
shot power measurement); all n = 800 draws are the measurement window. Fixed ball
sets (enumerated in §D.4) and per-cell seeds recorded in the results JSON.

---

## Governance checklist

1. This document is the one-page registration, written before any C/D outcome
   data and before any C/D run script exists (C1).
2. Expectation-free: no predicted outcomes; the three mechanism statements above
   are labeled instrument-validity controls (calibration) per the amended Phase 1.
3. Null simulator declared (A1 uniform / fair continuation); +1-corrected MC;
   floor rule stated and satisfied; design verifier (`src/design_verifier.py`)
   must PASS before any C/D results doc is published.
4. Detection and action stay separated: the A7 actionability gate remains a
   labeled synthetic worked example, computed from A + C outputs only.
5. Meta-uniformity panel: N/A — synthetic batch, no real-data p-values to append.
6. Results commit will cite this registration's git SHA.

**Human approval required before any run.** Approved by: **Cha** — conditional on
amendments 1–5, all applied above. Date: **2026-06-13**. Frozen for commit; no
C/D run script may be created or executed until this file is committed and its
sha256 recorded (per Cha's directive + C1).
