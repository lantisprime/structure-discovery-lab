# REGISTRATION — eq.tidal-manila.phase.moondist.v3

**STATUS: APPROVED 2026-06-12 (Cha, lab owner — §10). Committed pre-execution;
the commitment-ledger line is the binding hash.**

No fit has been run. No data values have been inspected in this dispatch
beyond what `docs/RESULTS_EQ_TIDAL_V2.md` and `results/eq_tidal_v2.json`
already publish. This registration must be human-approved and
commitment-hashed into `results/commitment_ledger.txt` BEFORE any execution
(EQUATION_DISCOVERY.md §6; equation-analyst hard rule 3).

Drafted: 2026-06-11 by equation-analyst (Fable, design-only dispatch).
Pipeline position: Phase 5 follow-up — **re-adjudication of claim B's R1
residual gate ONLY**. NEW registration with its own m charge (§10), per the
v2 §7 closing rule: structured-residual adjudication changes go through a
new registration, never a quiet extension.

## 0. Scope — what this registration does and does not do

| In scope | Out of scope |
|---|---|
| Re-evaluation of the v2 claim-B **R1 whitelist-attribution gate** on a declared fine ω-grid | ANY refitting (B1 is frozen; byte-equivalent deterministic re-fit only, not recharged) |
| Adjudication of the v2 learning-3 **spectral-leakage hypothesis** | — (claim A's single unattributed 36.625 d peak INCLUDED by approver amendment, §8 option (b), at +0 charge) |
| Same whitelist, same Rayleigh-merge rule, same R3 gate (re-stated, deterministic) | Any change to whitelist membership, merge rule, α, R3 threshold, splits, or data |

### The hypothesis under test

v2 claim B (`eq.tidal-manila.phase.moondist.v2`) returned
FAILED_EQUATION_SEARCH with R1 reporting an unattributed residual ladder:
24.42, 36.63, 41.86, 48.83, 58.6, 73.25, 97.67 d (plus 22.54, 20.93, 19.53,
18.31, 17.24, 16.28 d). The v2 periodogram was evaluated on the **natural
Fourier grid of the 293-row train+validation span**, whose ordinates are
P = 293/k d. Every single unattributed peak sits exactly on a low-k ordinate:

| k | 293/k (d) | v2 unattributed peak (d) |
|---|---|---|
| 3 | 97.667 | 97.67 |
| 4 | 73.250 | 73.25 |
| 5 | 58.600 | 58.6 |
| 6 | 48.833 | 48.83 |
| 7 | 41.857 | 41.86 |
| 8 | 36.625 | 36.625 |
| 12 | 24.417 | 24.42 |
| 13–18 | 22.54 … 16.28 | 22.54 … 16.28 |

A near-complete consecutive ladder of coarse-grid ordinates is the classic
signature of **spectral leakage**: a few off-grid lines (the whitelist
inequalities at 31.812, 29.531, 14.765, 13.777 d, none of which lies on the
293/k grid) spill power across many coarse ordinates. The alternative — that
Moon Dist genuinely contains a dozen distinct unmodeled constituents on a
harmonic ladder — is physically implausible but is NOT assumed away: it is
the declared FAIL branch (§6, outcome 2). v2's registered single-ordinate
deletion could not distinguish the two at this n; that is the instrument
defect v3 fixes.

## 1. Source claim and gate check (unchanged from v2)

Identical to v2 §1: source structure claim
`tidal-manila.tda-h1-delay-embed.batch5`, STRUCTURED, attribution on file,
eligibility §2 row 1 (calibration target). Independence (rule 2): executing
analyst ≠ batch5 detection analyst; additionally the v3 executor must not be
the v2 same-claim independent verifier. Gate failure at execution →
NO_EQUATION_ATTEMPTED.

## 2. Data and frozen fit (no new fit)

| Field | Value |
|---|---|
| File | `datasets/tidal-manila/tidal_derived.csv` (unchanged; n = 366, 2025-06-11..2026-06-11) |
| Target | `Moon Dist (km)` only |
| Splits | unchanged: train rows [0,220), validation [220,293), test [293,366) |
| Frozen equation | v2-selected **B1** (`results/eq_tidal_v2.json`): ŷ = 385294.7950098205 + (−19039.87882118035)·sin(2πt/P) + 11488.61399772309·cos(2πt/P), P = 27.60387627151598 d, t = days since 2025-06-11 (row index) |
| Re-fit rule | the executor re-derives B1 by re-running the v2 registered fit path deterministically and MUST verify byte-equivalence of coefficients to the JSON above before proceeding. Any discrepancy → abort, NO_EQUATION_ATTEMPTED, escalate. This re-fit is uncharged (deterministic repeat of an already-charged test, same rule as v2's A2 comparator). |
| data_regimes | [all_rows] (unchanged) |

Residual series for adjudication: r_t = x_t − ŷ_t on train+validation
(rows 0–292), exactly as v2 §7.2 — identical bytes to the v2 residuals.

## 3. Registration contract (EQUATION_DISCOVERY.md §6 YAML)

```yaml
equation_claim_id: eq.tidal-manila.phase.moondist.v3
source_structure_claim: tidal-manila.tda-h1-delay-embed.batch5
structure_verdict: STRUCTURED
equation_type: latent_phase_harmonic          # frozen B1; no candidate search
candidate_family: [B1_harmonic_1freq_k1]      # FROZEN from v2 — verification re-fit only
inputs: [t]
target: ["Moon Dist (km)"]
fit_split: {train: first_60pct, validation: next_20pct, test: final_20pct}  # unchanged
null_baseline: []                              # no new fit ⇒ no new null race; v2 null
                                               # results stand untouched
selection_rule: none_frozen
metrics: [residual_line_attribution_fine_grid, leakage_collapse_count]
data_regimes: [all_rows]
multiplicity_charge: {family_id: eq.tidal-manila.harmonic, m_delta: 1}  # §10
public_claim_allowed: false_until_confirmed
seed_base: 20260613      # stage offsets {residuals: 0, diagnostics_boot: 1};
                         # distinct from v1 (20260611) and v2 (20260612)
```

## 4. The fine ω-grid R1 procedure (the only redesigned instrument)

Declared in full before execution. Three steps; significance machinery is
UNCHANGED from v2 — only peak **location** and **attribution** change.

1. **Detection (unchanged):** iterative Fisher-g on the natural Fourier grid
   of the 293-point residual series, window 4–120 d, max-ordinate deletion,
   stop at p ≥ 0.01, iteration cap 20 — byte-identical to the v2 R1 detector
   (Fisher-g's exact null requires independent natural-grid ordinates;
   significance is therefore NOT computed on the oversampled grid).
2. **Fine-grid location refinement (new):** the residual periodogram is
   additionally evaluated on a **16× zero-padded grid** — frequency step
   Δf = 1/(16·T), T = 293 d, i.e. ordinates at j/(16·293) cyc/d over the
   same 4–120 d window. Each significant natural-grid peak from step 1 is
   assigned its **refined location**: the fine-grid local maximum within
   ±1 natural Fourier bin (±1/293 cyc/d) of the coarse ordinate.
3. **Attribution on refined locations (rule otherwise unchanged):**
   - Whitelist (identical to v2): evection 31.812 d, synodic 29.531 d,
     variation 14.765 d, anomalistic 2nd harmonic 13.777 d.
   - A peak is attributed iff its REFINED period lies within one Rayleigh
     bandwidth (ΔP = P²/T, T = 292 d as implemented in v2) of a whitelist
     period, or inside a merge zone between two whitelist periods separated
     by < 2 Rayleigh bandwidths (claim-B merge reading carried from the v2
     declared-deviation 2: NO merge allowance for claim B — the stricter
     reading stands; flagged for the approver).
   - **Leakage-collapse rule (new, declared):** significant natural-grid
     peaks whose refined locations fall within one Rayleigh bandwidth of
     EACH OTHER, or of an already-attributed refined line, collapse into a
     single line for adjudication (they are one spectral feature sampled at
     several coarse ordinates / its sidelobes). R1 adjudicates **distinct
     refined lines**, not grid ordinates.

R1 verdict rule: every distinct refined line attributed → **R1 PASS**; any
distinct refined line unattributed → **R1 FAIL**.

Anti-tuning guard: the oversampling factor (16), window, α = 0.01, cap,
whitelist, ΔP formula, and collapse rule are all fixed by this document. No
parameter may be adjusted after the residual spectrum is seen (M1).

## 5. R2/R3/R4 and diagnostics (unchanged, deterministic, re-stated)

The residuals are byte-identical to v2's, so these gates are re-computed
verifications of already-published deterministic values, not new tests:

- **R2 CUSUM changepoint (gating):** v2 claim B PASSED (stat 0.930,
  p = 0.378). Expected to reproduce exactly.
- **R3 TDA H₁ absorption < 0.562 (gating, UNCHANGED):** v2 claim B FAILED
  (residual persistence 0.886, absorption 21.2%). The threshold is not
  revisited. Expected to reproduce exactly — see §6 for the consequence.
- **R4 compression:** diagnostic-only for claim B (as v2).
- Non-gating diagnostics (Ljung–Box, MMD, Breusch–Pagan): re-published.

## 6. Pre-declared outcomes — BOTH branches, declared now

**Binding fact declared up front:** because R3 is unchanged and the
residuals are frozen, R3 will FAIL (0.886 > 0.562) on either branch.
Therefore **v3 cannot upgrade claim B's verdict above
FAILED_EQUATION_SEARCH under any outcome.** What v3 adjudicates is the R1
attribution question and the leakage hypothesis — i.e. WHICH
FAILED_EQUATION_SEARCH the lab has, and what a future v4 must do.

1. **Outcome 1 — ladder dissolves (R1 PASS path).** All distinct refined
   lines attribute to the whitelist. Recorded result: R1 → PASS; the v2
   learning-3 "unattributed ladder" finding is **reclassified as a
   coarse-grid leakage artifact** (instrument note appended to the v2
   learnings, original text preserved); claim-B verdict remains
   FAILED_EQUATION_SEARCH **on R3 alone**. Consequence for the program: the
   correct v4 route is "model the whitelist inequalities explicitly to pass
   R3", NOT "explain a mystery ladder"; the residual-spectrum instrument is
   amended (fine-grid location refinement becomes the standing R1 method for
   deterministic-remainder targets, subject to approval).
2. **Outcome 2 — ladder persists (FAIL stands).** At least one distinct
   refined line remains > 1 Rayleigh bandwidth from every whitelist period
   and outside every merge zone. Recorded result: R1 → FAIL stands;
   **the leakage hypothesis is DEAD and is logged as such** (CLAUDE.md:
   dead ends are results); the unattributed line(s) are published with
   refined periods as a genuine discovery-grade anomaly in
   ephemeris-derived data — escalation to human review before any v4,
   since unmodeled genuine lines in a DE441-derived series most plausibly
   indicate an error in OUR derivation/whitelist, not new physics.

Either way: verdict vocabulary per hard rule 7; this run can output only
FAILED_EQUATION_SEARCH (with the branch recorded) or NO_EQUATION_ATTEMPTED
(gate/abort). No verdict here touches the batch5 detection verdict (hard
rule 1). Doob separation: no action license; Phase 6 unchanged.

## 7. Reproducibility

Two-run rule unchanged: two separate full executions, byte-identical JSON
required (`results/_eq_tidal_v3_run{1,2}.json`); seed base 20260613 (the
procedure is deterministic except optional diagnostic bootstraps). Results
to `docs/RESULTS_EQ_TIDAL_V3.md` + `results/eq_tidal_v3.json`.

## 8. Multiplicity charge — m_delta = 1, justified

`{family_id: eq.tidal-manila.harmonic, m_delta: 1}`

| Item | Charge | Reasoning |
|---|---|---|
| B1 verification re-fit | 0 | deterministic repeat of an already-charged fit (same rule as v2's A2 comparator) |
| R1 re-adjudication under fine grid | 1 | the FIT gets no new flexibility, but the R1 gate gets a **fresh chance to pass under a redesigned rule — a new test in verdict space**, exactly the reasoning that charged v2's claim-B re-adjudication +1. Charged once, honestly. |

Cumulative family charge if approved: 8 + 1 = 9. Reviewer options — RESOLVED
by approver 2026-06-12: (a) REJECTED — the +1 charge stands (a fresh look in
verdict space is a look, upside or not); (b) ACCEPTED — scope extended to
claim A's single unattributed 36.625 d peak (also exactly 293/8) at +0 extra
charge under the same redesigned rule (same run, same fine grid, same
leakage-collapse rule; claim A's verdict likewise cannot improve — R2/R4
remain failed — so this is symmetric diagnostics, not a new chance).

## 9. Proposed ledger deltas (PROPOSED — NOT APPLIED)

1. `results/commitment_ledger.txt`: append SHA-256 of this file
   post-approval, pre-execution, claim id `eq.tidal-manila.phase.moondist.v3`.
2. `results/run_ledger.jsonl`: new entry run_id `eq_tidal_v3`, phase 5,
   source run `batch5`, predecessor `eq_tidal_v2`, equation_analyst_id
   (≠ batch5 analyst, ≠ v2 verifier), registration hash, seed base 20260613.
3. `results/multiplicity_ledger.jsonl`: append
   `{family_id: "eq.tidal-manila.harmonic", m_delta: 1, reason: "Phase 5 v3: claim-B R1 re-adjudication on declared fine omega-grid (v2 learning 3, leakage hypothesis)"}`.

None applied. This document is the only artifact of this dispatch.

## 10. Human approval

```
APPROVED BY: Cha (lab owner) — in-session approval
DATE:        2026-06-12
AMENDMENTS:  §8 option (a) rejected (+1 charge stands); §8 option (b)
             accepted (claim A's 36.625 d peak in scope, +0 charge)
COMMITMENT HASH (post-approval): <appended to results/commitment_ledger.txt
             immediately after this edit; the ledger line is authoritative>
```
