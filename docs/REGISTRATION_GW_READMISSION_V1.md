# REGISTRATION — GW (R2) null redesign readmission run v1

**Committed BEFORE execution** (hashed into results/commitment_ledger.txt;
snapshot label "Registration GW_READMISSION_V1"). Source approval:
`docs/PROPOSAL_GW_NULL_REDESIGN.md` approved by the lab owner 2026-07-07.
Synthetic calibration only — **no real data touched, no multiplicity charge**.
No outcome expectation is stated anywhere in this document (A-series
discipline); every verdict branch is pre-declared.

## Instrument under test

`gw_distortion` exactly as frozen in `src/relational_admission.py` R2
(POT exact GW, square loss, Euclidean distance matrices scale-normalized by
their mean, uniform measures), statistic = −distortion, p via the lab's
`p_perm` convention (1 + #{null ≥ obs}) / (m + 1).

## Registered null (primary — the ONE null under test)

**Coupling-label permutation**: pool the two point sets (2n rows in a common
ambient space; the 2-D cloud is zero-padded to 3-D, an isometry of its
distance matrix), draw a label permutation, split back into two n-row sets,
recompute the full statistic. Exchangeability under H₀ (independent draws
from the same process) holds by construction; both empirical geometries are
conditioned on. This replaces the M2-failed moment-matched Gaussian
regeneration null.

*Design note (recorded, not run):* the proposal's option 2 (row permutation
within one side) is withdrawn at design time — GW with uniform measures is
invariant to row order, so that null statistic is degenerate by construction.
Option 3 (entropic GW) is a new instrument requiring onboarding, out of scope.

## Parameters (binding)

- n = 200 points per cloud, d = 3; m_perm = 99 → p_floor = 0.01 ≤ α/2 = 0.025
  (floor rule satisfied; single registered α = 0.05, no family pooling —
  synthetic calibration carries no multiplicity charge)
- Seeds: `numpy.random.default_rng(20260707 + k)` with k = 0 for the
  FPR/uniformity gate, k = 1000 + i for power grid point i (declared scheme)
- **Gate 1 — FPR**: 300 H₀ trials (A, B independent N(0, I₃)); pass iff
  FPR@0.05 ∈ [0.028, 0.078] (exact binomial 95% band for 300 trials at 0.05)
- **Gate 2 — p-uniformity** (the gate that failed in M2, so the gate that
  readmits): over the same 300 H₀ p-values, KS-vs-uniform p ≥ 0.01 AND
  lattice χ² p ≥ 0.01 across the 100 attainable p-levels {k/100}
- **Gate 3 — power** (frozen M1 reference: 0.95 @ noise 0.1 → 0.15 @ 0.5):
  shared circle geometry, A ∈ ℝ² (padded), B ∈ ℝ³ (random rotation), noise
  grid {0.1, 0.2, 0.3, 0.5}, 50 trials per point; pass iff power@0.05 at
  noise 0.1 ≥ 0.85 (within binomial 2σ of the frozen 0.95); the full curve is
  reported regardless
- Reproducibility: the run executes twice with identical seeds; the two
  output JSONs must be byte-identical (diff recorded)

## Pre-declared verdict rule

- all three gates pass → **READMIT_CANDIDATE** (final instrument-status
  change remains a governance action by the lab owner)
- gates 1–2 pass, gate 3 fails → **CALIBRATED_BUT_POWERLESS** — per the
  approved proposal, recommend retiring R2 to the conflict registry (the
  dead end is the result; CLAUDE.md: dead ends are logged, not hidden)
- gate 2 fails → **NULL_STILL_MISCALIBRATED** — same recommendation
- any gate un-runnable → **ABORTED_INCOMPLETE**, nothing ledgered as a verdict

## Ledger plan

One run-ledger row `gw_readmission_v1` (script `src/gw_readmission_v1.py`,
output `results/gw_readmission_v1.json` + sha256), three admission-log lines
(one per gate), zero multiplicity-ledger rows. Executor: maintenance session
(single-session run; synthetic calibration — the role-separation requirement
binds real-data claims).
