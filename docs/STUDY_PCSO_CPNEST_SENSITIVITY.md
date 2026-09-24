# STUDY SPEC — pcso.cpnest.sensitivity1 (pre-declared sensitivity grid for CP-NEST)

**STATUS: DRAFT 2026-09-24 — awaiting referee review and lab-owner approval.** Nothing in §§3–6 is run
before this file is approved and commitment-hashed into `results/commitment_ledger.txt` with
`tools/snapshot_commitment.py`. Grade: G0 exploratory (simulation only).

Design context: `docs/plans/PCSO_MODEL_REGISTRY_PLAN.md` §2 (CP-NEST), `docs/REGISTRATION_PCSO_MODEL_REGISTRY.md`,
`docs/REGISTRATION_AMENDMENT_2026-09-23_V2.md` (A3, A4), `docs/RESULTS_PCSO_MLX_BACKEND_2026-09-23.md`
("Sensitivity grid: not run; the lead will pre-declare it separately").

## 1. Question and scope

`pcso.registry.seq1` froze CP-NEST's constants: basis φ₁…φ₆ in the stated order, prior N(0, τ²I) with τ = 0.05,
fixed-share rate ρ = 10⁻³, level prior v₀(d) ∝ 2^{−d}, M = 128 antithetic predictive samples. This study measures,
on simulated streams only, how CP-NEST's null behaviour and its detection power depend on those constants, and
states in advance what the result means for the registered point.

- **Simulation only.** Every stream is synthetic on the real (date, pool) schedule. No real draw outcome enters any
  cell; the study reports no evidence value on real draws. Constants therefore cannot be tuned to the real data.
- **No change to any registration.** `pcso.registry.seq1`, `pcso.sparse.seq1` and their files (including
  `src/pcso_model_registry.py`) are not edited. seq1 runs unchanged to its fixed terminal analysis (780 registered
  draws). A result here can at most motivate a separate future registration (seq2) approved by the lab owner.
- **Out of scope:** basis order and basis content (a different order is a different nested model class and belongs
  in its own registration); the Dirichlet, grid, parity and ensemble models.

## 2. Schedule

Schedule = the (date, pool) sequence of the 1,001 rows of `datasets/pcso-lotto/data_draws_1yr.csv` at the
conditioning pin `1ce8541` (all dated ≤ 2026-09-23), pooled filtration ordered as in the registry harness.
Null streams use this schedule (T = 1,001). Power streams use it repeated three times (horizon 3,003 pooled draws),
as in the registered C2 arm.

## 3. Grid

**Main grid (15 cells):** τ ∈ {0.01, 0.025, 0.05, 0.10, 0.20} × ρ ∈ {0, 10⁻³, 10⁻²}, with v₀(d) ∝ 2^{−d}, M = 128.
ρ = 0 is the ablation without fixed-share switching (a plain Bayesian mixture over levels).

**One-at-a-time arm at the registered point (τ = 0.05, ρ = 10⁻³), 3 cells:**
- M = 32 and M = 512 (v₀ ∝ 2^{−d});
- v₀ uniform (1/7 per level), M = 128.

Registered point = cell (τ 0.05, ρ 10⁻³, v₀ ∝ 2^{−d}, M 128). Total 18 cells.

## 4. Streams, seeds and pairing

- **Null arm:** 20,000 uniform streams per cell.
- **Power arm:** 2,000 streams per cell for each planted tilt θ₁ ∈ {0.025, 0.05, 0.10} on feature φ₁ (the registered
  C2 construction: `synthetic(rng, schedule, theta1)`). Comparator: `tilt_linear`, the exact one-parameter grid
  process on φ₁, run once per θ₁ on the same streams (it does not depend on τ, ρ, v₀ or M). Power streams are
  split into a **selection half** (streams 0–999) and an **evaluation half** (streams 1000–1999); see §6.
- **Common random numbers.** Stream s's drawn 6-sets depend only on (base seed 20260923, arm, θ₁, s), never on the
  cell, so all cells see identical data and differences between cells are paired. CP-NEST's antithetic predictive
  normals for stream s depend only on (20260923, M, s) and are shared across all cells with the same M (cells with
  different M cannot share them; those comparisons are paired on data only).
- **Seeding requirement (implementation).** Every stream's draws and predictive normals come from its own generator,
  `SeedSequence([20260923, arm, θ₁-index, s])` for data and `[20260923, 1, M, s]` for normals, with s the global
  stream index. The current `src/pcso_mlx_sim.py` does not meet this: `cp_streams` draws all n streams from one
  generator (stream s's data depends on n), and `_mlx_cp` keys normals on `seed + start` with `start` local to the
  call (the MLX docstring: "reproducible for fixed seed AND chunk size"). Sharded calls would therefore repeat or
  shift streams. The extension must seed per global stream index; a test must show that results for stream s are
  identical under two different shardings and chunk sizes. Streams are sharded into jobs that respect the M5
  supervisor's ≤ 300 s deadline.

## 5. Measures (per cell)

Null arm (T = 1,001):
- **N1 validity:** fraction of streams with sup_t E_t ≥ 1/α = 100 (α = 0.01), and its one-sided Clopper–Pearson
  lower bound at level 1 − 0.05/18 (Bonferroni over cells; the implementation passes `alpha=0.05/18` to
  `clopper_pearson_lower`, whose default is 0.05).
- **N2 fixed-share loss bound (theorem check):** fraction of streams with, at every t ≤ T,
  −log E_t ≤ log(1/v₀(0)) + (t − 1)·log(1/(1 − 6ρ/7)),
  the amendment-v2 A4 bound evaluated at the cell's own v₀(0) and ρ (for ρ = 0 the slope term is 0; for v₀ uniform
  the intercept is log 7). Derivation for CP-NEST as implemented (`CPNest.update`): level 0 predicts p₀ exactly, so
  with m_t the mixture ratio at draw t, the posterior level-0 weight is v_t(0)/m_t and fixed-share gives
  v_{t+1}(0) = (1 − ρ)·v_t(0)/m_t + ρ/7 ≥ (1 − 6ρ/7)·v_t(0)/m_t. The first prediction uses v₀ unmixed and
  m_t ≥ v_t(0), so E_t = ∏_{s≤t} m_s ≥ v₀(0)(1 − 6ρ/7)^{t−1}: t − 1 mixing steps precede draw t. The registered
  conservative form (slope 0.0010005 ≥ log(1/(1 − ρ)) per draw, T factors) is weaker and is implied by this one. A
  float64 spot check (2026-09-24, 3 streams each at (τ 0.2, ρ 10⁻²) and (τ 0.01, ρ 0), T = 1,001) found a minimum
  margin of 0.34 nats over all t. A stream fails only if the excess exceeds 10⁻³ nats (float32 tolerance; the
  paired MLX/CPU residual measured on 2026-09-23 was ≤ 6.3 × 10⁻⁵).
- **Descriptive (no pass/fail):** median and 90th percentile of −log E_T (the null cost of the alternative), median
  final level-0 weight v_T(0), median sup E, fraction with sup M ≥ 100 for the Shiryaev–Roberts detector.

Power arm (horizon 3,003), per θ₁:
- **P1:** fraction of streams with sup E ≥ 100 within the horizon, with its one-sided 95% Clopper–Pearson lower bound.
- **P2:** censoring-aware lower median of draws to first crossing (`censored_median`, "not reached by horizon" when
  infinite), as in amendment v2 A3.
- **P3 (descriptive):** P2 ratio to `tilt_linear` on the same streams, with a paired stream-level bootstrap 95%
  interval (2,000 resamples, fixed seed).

## 6. Decision rule (fixed before any run)

**Defect gate (every cell).** A cell passes if N1's Bonferroni lower bound is ≤ 0.01 and N2 = 1.0. Both are
consequences of theorems (Ville's inequality; the fixed-share bound), so a failure is an implementation defect,
not a finding: the run stops, the defect is recorded and fixed, and the affected cells are rerun in full. No power
conclusion is drawn from a cell that fails the gate.

**Verdict on the registered point (primary θ₁ = 0.05).** Selection and evaluation use disjoint streams, so the
chosen comparator's median is not biased downward by having been selected as the minimum.
1. *Selection (streams 0–999):* B = the gate-passing cell with the smallest P2 at θ₁ = 0.05. Ties → larger P1, then
   the registered point, then smaller τ, then smaller ρ, then M = 128 before other M, then v₀ ∝ 2^{−d} before
   uniform. B may be the registered point itself.
2. *Evaluation (streams 1000–1999):* P1 and P2 of the registered point and of B, recomputed on these streams only.
   - **ROBUST** if P2(reg) ≤ 1.25 × P2(B) **and** P1(reg) ≥ P1(B) − 0.05.
   - **SENSITIVE** otherwise.
   - **UNINFORMATIVE** if P2(B) is "not reached by horizon" (then every cell's is).

P2 ordering: "not reached by horizon" counts as +∞, larger than every finite value; 1.25 × ∞ = ∞, and ∞ ≤ ∞ holds.
θ₁ = 0.025 and 0.10 are reported for every cell but do not enter the verdict. Full-sample (2,000-stream) values and
the paired bootstrap interval for P2(reg)/P2(B) on the evaluation half are reported beside the verdict.

**Consequences.** ROBUST → recorded; no action. SENSITIVE → the lead drafts a seq2 proposal naming cell B for the
lab owner's decision; seq1 continues unchanged either way. Nothing in this study changes the picker.

## 7. Backend and validation

- **Production of the grid:** MLX float32 on the M5 GPU (`src/pcso_mlx_sim.py`, extended so τ, ρ and v₀ are
  parameters whose defaults reproduce the registered constants, with §4's seeding). Its CLI guard "POWER uses
  production M=128" (`src/pcso_mlx_sim.py:427`) is relaxed only for the declared one-at-a-time cells M = 32 and
  M = 512.
- **CPU float64 reference:** a `CPNest` subclass defined outside the frozen registry file. τ and ρ are class
  attributes; v₀ is set in `__init__` (`2.0 ** -np.arange(D + 1)`), so the subclass overrides `__init__` to set the
  cell's v₀ and otherwise calls the parent unchanged.
- **Paired float64 check before the grid result is accepted** (max |Δ log E_t| ≤ 10⁻³ nats over all t and streams):
  - null, T = 1,001, 200 streams each: the registered point, (τ 0.01, ρ 0), (τ 0.20, ρ 10⁻²), v₀ uniform;
  - null, T = 1,001, 100 streams: M = 512;
  - power, θ₁ = 0.05, horizon 3,003, 200 streams: the registered point (the verdict's horizon and arm).
  Failure on any check → every cell sharing the failing condition (horizon, M, or v₀) is rerun on CPU float64.
- **Default identity check:** with default parameters the extended MLX path reproduces the 2026-09-23 MLX
  artifacts byte-for-byte on the same inputs.
- **Estimated cost:** about 3–4 GPU hours on the M5 for the grid and about 30 CPU minutes (8 workers) for the
  float64 checks, extrapolated linearly in M and T from the 2026-09-23 timings (CP-NEST, M = 32, T = 994: 10,000
  null streams 37.2 s on MLX; 400 streams 138.8 s on CPU). Not measured; the run log records actual times.

## 8. Outputs and reporting

- `results/exploratory/pcso_cpnest_sensitivity_<run-date>.json` — every cell's measures, seeds, M, schedule hash,
  code and input hashes, MLX version and device.
- `docs/RESULTS_PCSO_CPNEST_SENSITIVITY_<run-date>.md` — tables for all 18 cells, the defect-gate result, the
  verdict as stated in §6, and every deviation from this spec.
- All cells are reported, including any that fail the gate.

## 9. Disclosures

- The main grid values come from the 2026-09-23 lead draft (handoff ep 20260923-075836); the one-at-a-time arm,
  thresholds 1.25× / 0.05 and stream counts are the lead's proposals in this draft.
- The registered C2 result (v2 leaderboard, 50 streams: CP-NEST median 918 vs `tilt_linear` 707 at θ₁ = 0.05) was
  known when this grid was written; it is a simulation result, not a real-data result.
- No simulation for any cell of this grid has been run. The only computation so far is the 6-stream float64 N2
  spot check in §5, made to settle a referee question about the bound's form.
- Referee review 2026-09-24 (one adversarial agent, APPROVE-WITH-CHANGES): accepted — float64 coverage of the power
  horizon, M = 512 and v₀ uniform; split-sample selection of B; ordering of "not reached"; the M = 128 CLI guard;
  per-stream seeding; tie order over M and v₀; the Bonferroni α passed to `clopper_pearson_lower`. Rejected — "use
  T, not T − 1, in N2": T − 1 is the valid (tighter) bound for the implemented update order (derivation in §5).
