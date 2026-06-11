# EVALUATION PROTOCOL — Deterministic, Repeatable, LLM-Executable

Machine-followable specification for evaluating any onboarded dataset. Every step is
deterministic (fixed seeds, fixed parameters, exact formulas, exact decision rules);
two independent executors (human or LLM) following it on the same data MUST produce
identical numbers. Companion: docs/RUNBOOK.md (workflow), docs/THEOREM_GOVERNANCE.md (rules),
docs/kb/ (theorem cards). Lottery instantiation shown in [brackets].

## 0. Fixed constants (do not vary without re-registering)

```
SEED_BASE   = 2026          # script k uses seed SEED_BASE + k (registry below)
NSIM_TEST   = 10000         # MC sims for registered/confirmation tests
NSIM_EXPLORE= 1000          # MC sims for exploratory instruments (min)
NPERM       = 20000         # permutation count for correlation tests
ALPHA       = 0.05          # base significance
EQUIV_RHO   = 0.90          # |null correlation| above which statistics share a class
EXTREME_LO, EXTREME_HI = 0.005, 0.995   # ensemble-rank extremes
```
Determinism rule: all randomness from `random.Random(seed)` / `np.random.default_rng(seed)`
instantiated per-script; never global unseeded state; record seed in every output.

## 1. Null simulator (the root object)

Define S(L) = generator of one synthetic dataset of the same shape as the real one
under H₀. [Lottery: for each game g with pool P_g and observed length T_g, draw T_g
independent uniform 6-subsets: `rng.sample(range(1, P_g+1), 6)`.]
All null distributions below are { stat(S(L)) : i = 1..NSIM }. No textbook asymptotics.

## 2. Deterministic dataset evaluation steps

**E0. Integrity gate** (all must pass before statistics):
- Schema: every row matches DATASET.md §3; ranges 1 ≤ n ≤ P_g; 6 distinct values.
- Duplicates: no (key, date) repeats; conflicting duplicates → HALT, adjudicate.
- Near-duplicate scan: count adjacent same-stream pairs sharing ≥ k values where
  P(share ≥ k) per pair = Σ_{j≥k} C(6,j)C(P−6,6−j)/C(P,6); expected count
  E = Σ_pairs p; flag if Poisson tail P(X ≥ obs | E) < 0.05 → verify driving rows.
- Calendar: every date on its declared schedule; every gap matched to era registry.

**E1. Marginal uniformity** — per stream g:
  χ²_g = Σ_{i=1..P} (O_i − E)² / E,  E = 6·T_g / P_g
  p_g = #{ χ²(S) ≥ χ²_obs } / NSIM    (one-sided MC)

**E2. Memory (order-0 vs order-1)** — per stream:
  δ = P̂(i∈D_t | i∈D_{t−1}) − P̂(i∈D_t | i∉D_{t−1})   (pooled, UNsmoothed)
  G = 2 Σ_{a,b} O_ab ln(O_ab/E_ab) on K-quantile-state transitions, E_ab = R_a C_b / n
  |λ₂| of the K-state empirical transition matrix
  All MC-calibrated; two-sided for δ, one-sided for G and |λ₂|.

**E3. Spectrum & long memory**:
  Periodogram I(f_k) of z-scored stream summary; Fisher g = max I / Σ I with exact
  p = Σ_{j=1..⌊1/g⌋} (−1)^{j−1} C(N,j)(1−jg)^{N−1}.
  Hurst Ĥ via R/S over windows {8,16,32,64} — REPORT ONLY (Ĥ_obs − Ĥ_null), never raw Ĥ.

**E4. Tails & scaling** (CSN procedure):
  α̂ = 1 + n_tail / Σ ln(x_i / x_min), x_min = median (declare in advance)
  Vuong z = √n · mean(ℓᴾᴸ_i − ℓᴱˣᵖ_i) / sd(·);  power law only if z > +2 AND α̂ < 3.
  First digits: χ² against the EXACT H₀-derived digit law (never against Benford
  unless the quantity is multiplicatively generated).

**E5. Cross-sectional factors**: eigenvalues of the standardized presence/return
  correlation matrix; flag count = #{ λ > q99(λ_max under S) }.

**E6. Compression certificate** (one-sided): bit-pack canonical encoding; structure
  iff min(LZMA, bz2, zlib, raw-DEFLATE) bits < T · log₂|Ω| where |Ω| = C(P,6).

**E7. Stationarity gate** (REQUIRED before any pooled interpretation):
  Split into Q=4 equal windows; per-window deviation vectors v_w(i) = O_{w,i} − E_w;
  ρ̄ = mean over pairs (w,w′) of corr(v_w, v_w′); MC-calibrate.
  If p(ρ̄) < ALPHA/Q OR an era-registry boundary falls inside the sample:
  pooled p-values from E1–E6 are QUARANTINED; rerun all per-era.

**E8. Ensemble certification**: B ≥ 10 diverse summary statistics; rank of each
  observed value in its NSIM null → r_b ∈ (0,1). Report (a) extremes
  #{r_b < EXTREME_LO or > EXTREME_HI} vs expectation B·0.01, (b) whether {r_b}
  is U(0,1)-like (KS, indicative only — ranks are correlated).

**E9. Power disclosure** (mandatory with every null result):
  detectable correlation at 80% power: r* = (z_{α′} + 0.84)/√(n−3), α′ = ALPHA/m;
  detectable frequency bias: Δ* ≈ (z_{α′}+0.84)·√(E)/E per number.
  Phrase all conclusions as "no effect ≥ <r*, Δ*> detectable at n=<n>".

## 3. Harmonization steps & formulas (run AFTER instruments, BEFORE conclusions)

**H1. Equivalence-class construction (deterministic):**
  For every statistic pair (s_a, s_b): compute corr over the SAME NSIM_EXPLORE null
  datasets: ρ_ab = corr(s_a(S_i), s_b(S_i)).
  Same class iff |ρ_ab| ≥ EQUIV_RHO or a monotone relation is proven.
  m = number of classes. Threshold: α′ = ALPHA / m (Bonferroni) or BH at level ALPHA
  on class-level minimum p-values — declare which BEFORE looking.

**H2. Verdict aggregation (asymmetric logic):**
  flag(class) = [ min class p < α′ ]
  Dataset verdict = STRUCTURE iff any admissible class flags AND its driving rows are
  multi-source verified AND it survives E7 era attribution.
  Passes never offset flags. Passes contribute scope: record (face, alternative, power).

**H3. Anomaly deduplication:**
  For every flag, compute the driving-row set R(flag) (the rows whose removal drops
  the statistic below threshold, greedy by leverage). Two flags with
  |R₁∩R₂| / min(|R₁|,|R₂|) > 0.5 are ONE anomaly. Report anomalies, not flags.

**H4. Look-elsewhere normalization:**
  Any "hottest X anywhere" claim must be priced by the scan construction: the null
  statistic is max over the FULL search space (all units × windows × streams) computed
  on each S_i. Never report a sub-search p-value.

**H5. Estimator-bias subtraction:**
  For any estimator θ̂ with finite-sample bias (Hurst, Binder, smoothed transition
  probabilities): report θ̂_obs − mean(θ̂(S)) with MC CI; the raw value is inadmissible
  in conclusions.

**H6. Confirmation handoff:**
  Anomalies surviving H1–H5 are REGISTERED, not believed: define the test, the
  held-out data (rows after the freeze date), family m_conf, threshold ALPHA/m_conf;
  write to DATASET.md §6. Sequential rule: the confirmation family runs as-is on each
  update; flags trigger one replication cycle on further fresh data before any claim.

**H7. Decision layer (only after H6 confirms, in this order):**
  gate: Doob — fair ⇒ stop. measure: EV = Σ_k P(match k)·prize_k·(1−tax·1[>10k])
  with split factor E[J/(1+K)], K ~ Poisson(tickets/C(P,6)). size: Kelly
  f* = p − q/b (binary approx), stake = f*·bankroll, fractional-Kelly under
  estimation error. Costs subtracted before EV in domains that have them.

## 4. Output contract (what every run must emit)

Per instrument: { name, class_id, seed, NSIM, observed, null_mean, null_sd, p,
sidedness, power_at_80 }. Per run: integrity-gate result, era-gate result, m, α′,
anomaly list with driving rows + verification status, verdict sentence in the
mandated phrasing, and the protocol version hash. Append-only results ledger.

## 5. Seed registry [lottery]

markov_analysis 2026 · MC-certification 2027 · structure_discovery 3 · cross-theorem 7
· perbak 4 · universality (deterministic) · powerlaw 21 · explore_batch2 99 ·
review_response 11 · picks SystemRandom (intentionally non-deterministic — picks only,
never analysis).

*Version 1.0 — Jun 11, 2026. Changes to constants, formulas, or decision rules bump
the version and reset the confirmation set (Governance A6).*
