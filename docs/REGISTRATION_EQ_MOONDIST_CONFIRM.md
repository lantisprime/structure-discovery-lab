# REGISTRATION — eq.tidal-manila.phase.moondist.confirm1

**STATUS: APPROVED 2026-06-12 (Cha, lab owner — §11). Committed pre-fetch;
the commitment-ledger line is the binding hash.**

No fetch has been performed and no fit will EVER be performed under this
registration. This document must be human-approved and commitment-hashed
into `results/commitment_ledger.txt` BEFORE the fresh-data fetch
(EQUATION_DISCOVERY.md §6; equation-analyst hard rule 3 — here the
"register before fitting" rule binds the fetch+scoring, since scoring a
frozen equation on data chosen after seeing it would be the same M1 hole).

Drafted: 2026-06-11 by equation-analyst (Fable, design-only dispatch).
Pipeline position: EQUATION_DISCOVERY.md verdict-ladder **fresh-data
confirmation step** (§7: "fresh-data confirmation before any label above
PREDICTIVE_EQUATION") for the FROZEN claim-B equation of
`eq.tidal-manila.phase.moondist.v2`.

## 0. CRITICAL equivalence-class note — read first

`datasets/tidal-manila/tidal_derived.csv` column `Moon Dist (km)` is
**COMPUTED FROM** `datasets/jpl-horizons-sun-moon/sun_moon_daily.csv` — both
files are written by the same deterministic parser
(`datasets/jpl-horizons-sun-moon/parse_horizons.py`) from the same parsed
Horizons delta values (`mkm = mdelta × AU_KM`, identical bytes to both
outputs; verified this session). Consequences, declared so nobody
double-counts:

1. **No new detection claim.** A "confirmation" against fresh Horizons Moon
   Dist data is a forecast test of the SAME series extended in time — it is
   NOT an independent second data source, NOT a new structure detection, and
   it creates no new kb claim about sun_moon_daily.
2. **No new fit.** The equation is frozen (§2). Any parameter touched after
   this registration voids the run.
3. **What it IS:** the ladder's fresh-data gate — does the frozen equation,
   fitted on data ending 2026-06-11 and registered before the fresh data
   existed, forecast genuinely post-freeze ephemeris values?

## 1. Source claim and gate check

| Field | Value |
|---|---|
| source_structure_claim | `tidal-manila.tda-h1-delay-embed.batch5` (STRUCTURED, p = 0.01, attribution on file) |
| equation under confirmation | v2 claim-B selected family **B1** (`docs/RESULTS_EQ_TIDAL_V2.md`; `results/eq_tidal_v2.json`, sha256 `fdc12e7251b59fec…`) |
| v2 status of that equation | period-recovery calibration **PASS** (27.604 d vs 27.555 d anomalistic, 0.18% err, CI ∋ truth); all three nulls beaten (binding surrogate p = 0.00995 ≤ 0.01); bootstrap stable; verdict **FAILED_EQUATION_SEARCH on residual gates R1/R3 only** (unmodeled known inequalities) |
| Eligibility | §2 row 1 calibration target; fresh-confirmation step per §7 ladder |
| Independence (rule 2) | scoring executor ≠ batch5 detection analyst ≠ v2 execution analyst; recorded in run_ledger before execution. Fetch is performed by the orchestrator/data path, not by the equation analyst. |

Gate failure, fetch-protocol mismatch (§4 guard), or byte-equivalence
failure (§2) at execution → **NO_EQUATION_ATTEMPTED**.

## 2. The frozen equation (exact values from results/eq_tidal_v2.json)

```
ŷ(t) = a0 + a·sin(2πt/P) + b·cos(2πt/P)

a0 = 385294.7950098205        km
a  = −19039.87882118035       km   (sin coefficient)
b  =  11488.61399772309       km   (cos coefficient)
P  =  27.60387627151598       d
amplitude √(a²+b²) = 22237.47371249511 km
t  = days since 2025-06-11 (row index of tidal_derived.csv; t=0 at the
     2025-06-11 13:00 UT-request sample — src/eq_tidal_v2.py, t = arange(n))
```

Reference figures (rounded, as published): a0 ≈ 385295 km, amp ≈ 22237 km
@ P = 27.604 d; **v2 test RMSE = 4119.801539200268 km** (rows 293–365,
2026-03-31..2026-06-11) — the benchmark for §5.

Freeze verification at execution: the executor recomputes B1 via the v2
registered path and checks byte-equivalence against the values above and
against `results/eq_tidal_v2.json` BEFORE the fresh data are scored. This
is a deterministic verification, not a recharged fit. Mismatch → abort,
NO_EQUATION_ATTEMPTED.

Forecast extension: fresh rows are scored at t = 366 … 451 (2026-06-12 →
t = 366; 2026-09-05 → t = 451; 86 rows). No re-anchoring of phase, no
intercept adjustment, no per-span recentering — the 2025-06-11 origin and
the coefficients above are used verbatim.

## 3. Fresh data — span and provenance

| Field | Value |
|---|---|
| Span | **2026-06-12 .. 2026-09-05** inclusive, daily — 86 rows, ~3.1 anomalistic cycles, strictly post-freeze (original data end 2026-06-11; v2 registration approved+hashed 2026-06-11; this registration hashed before fetch) |
| Source | NASA/JPL Horizons API (same source of record as the original; API reachability verified by orchestrator this session) |
| Fetched by | orchestrator/data path at execution time — NOT the drafting analyst, NOT now |

### 3.1 Exact fetch protocol (MUST match parse_horizons.py provenance)

Original provenance (header of `_raw_horizons_moon.txt` + parse_horizons.py
docstring): Horizons API v1.2, Target Moon (301) {DE441}, observer
ephemeris, Center `coord@399` GEODETIC `121.0359, 14.5794, 0.02` (PCSO
Mandaluyong; lon E, lat N, alt km), daily at the 13:00 UT request time
(Horizons stamps 13:00:02.880), airless apparent, delta in AU.

Declared fresh-fetch parameters:

```
format=text
COMMAND='301'
EPHEM_TYPE='OBSERVER'
CENTER='coord@399'
COORD_TYPE='GEODETIC'
SITE_COORD='121.0359,14.5794,0.02'     # identical to original — REQUIRED
START_TIME='2026-Jun-12 13:00'
STOP_TIME='2026-Sep-05 13:00'
STEP_SIZE='1 d'
QUANTITIES='20'                        # observer range delta (AU) + deldot
                                       # (original used 4,10,20; only 20 is
                                       # needed and is the scored quantity)
ANG_FORMAT/refraction: airless apparent defaults, as original
```

Unit conversion (identical to parse_horizons.py): km = delta_AU ×
149597870.700, written/compared at 0.1 km precision (`f"{mkm:.1f}"`).

### 3.2 Protocol guards (any failure → NO_EQUATION_ATTEMPTED, no improvising)

1. Exactly 86 rows, every calendar day 2026-06-12..2026-09-05 present
   (continuity assert as in parse_horizons.py).
2. Output stamps must show the same 13:00:02.880-pattern UT times and
   delta in AU; ephemeris DE441 (or Horizons' then-current successor —
   if the DE version differs, STOP and escalate to the human rather than
   score: a DE change is a declared protocol deviation requiring sign-off).
3. Raw response saved verbatim to
   `datasets/jpl-horizons-sun-moon/_raw_horizons_moon_confirm1.txt` before
   any parsing; its sha256 goes in the results JSON.
4. The fresh rows are NEVER appended to `sun_moon_daily.csv` /
   `tidal_derived.csv` before scoring is complete and verified (no chance
   of any code path seeing them early).

## 4. Registration contract (EQUATION_DISCOVERY.md §6 YAML)

```yaml
equation_claim_id: eq.tidal-manila.phase.moondist.confirm1
source_structure_claim: tidal-manila.tda-h1-delay-embed.batch5
structure_verdict: STRUCTURED
equation_type: latent_phase_harmonic
candidate_family: [B1_frozen_from_v2]      # zero free parameters at this stage
inputs: [t]                                # t = days since 2025-06-11; fresh t = 366..451
target: ["Moon Dist (km)"]                 # computed from fresh Horizons delta, §3.1
fit_split: none                            # no fitting; single forward evaluation
null_baseline: []                          # no new search ⇒ no null race; the v2
                                           # null results already license B1
selection_rule: none_frozen
metrics: [forecast_RMSE_fresh, max_abs_residual_fresh, residual_diagnostics_nongating]
data_regimes: [all_rows]
multiplicity_charge: {family_id: eq.tidal-manila.harmonic, m_delta: 1}   # §7
public_claim_allowed: false_until_confirmed
seed_base: 20260614      # diagnostics-only resampling; scoring itself is deterministic
```

## 5. Pre-declared pass criterion (fixed NOW, before any fresh value exists)

Let r_t = x_t − ŷ(t) over the 86 fresh rows.

1. **C1 (primary, gating): RMSE_fresh ≤ 1.5 × RMSE_test,v2 = 1.5 ×
   4119.801539200268 = 6179.70 km.** Rationale for the multiple, declared:
   the fresh span's far edge sits at t = 451, where the recovered period's
   0.18% error alone accumulates ≈ 0.029 cycle ≈ 0.18 rad of phase drift,
   contributing up to ≈ amp × 0.18 ≈ 4.1e3 km of additional pointwise error
   on top of the ≈ 4.1e3 km of known unmodeled inequalities already present
   in the v2 test RMSE; 1.5× covers the quadrature sum (≈ 5.8e3 km) with
   minimal slack. A tighter multiple would test the period's fourth decimal,
   not the equation; a looser one would be unfalsifiable.
2. **C2 (secondary, gating): max_t |r_t| ≤ 3 × RMSE_test,v2 = 12359.40 km.**
   Guards against a passing RMSE hiding a localized blow-up (e.g. phase
   slip late in the span).
3. **C3 (sanity, gating): no NaN/missing scored rows; exactly 86 residuals.**

Reported non-gating diagnostics: residual mean and trend over the fresh
span, Fisher-g top peaks of the fresh residuals (n = 86 is too short to
gate; reported for continuity with v2 learning 3 and v3), drift of |r_t|
vs t. NO residual gate from v2 §7 is applied here — completeness of the
equation was adjudicated (and failed) in v2/v3; this registration tests
FORECAST SKILL only, and says so to prevent verdict-shopping between the
two axes.

Anti-tuning guard: 1.5×, 3×, the span, and the t-convention are fixed by
this document; nothing may be adjusted after any fresh value is seen.

## 6. Pre-declared verdict consequences (both branches)

1. **PASS (C1 ∧ C2 ∧ C3) → MECHANISM_SUPPORTED** for
   `eq.tidal-manila.phase.moondist.confirm1` — the lab's first. Reasoning
   against the §7 ladder: B1 is stable (v2 bootstrap), interpretable (single
   line at the anomalistic month), the mechanism is **externally known
   physics** (lunar perigee–perigee anomalistic cycle, 27.555 d, standard
   orbital mechanics — independent corroboration in the strongest available
   form short of intervention), and the fresh-data confirmation requirement
   of §7 ("nothing above PREDICTIVE_EQUATION without fresh-data
   confirmation") is satisfied by this very test on post-registration data.
   - **Declared scope carve-out (judgment call flagged for the approver):**
     MECHANISM_SUPPORTED here attaches to the frozen B1 equation **as a
     forecast-grade description of the dominant anomalistic line, with
     declared error envelope ≤ 6.2e3 km RMSE** — it does NOT overturn,
     soften, or relabel `eq.tidal-manila.phase.moondist.v2`'s
     FAILED_EQUATION_SEARCH, which adjudicated a different question
     (residual completeness; R1/R3). Both verdicts stand simultaneously,
     each on its own claim id. RESOLVED by approver 2026-06-12: the
     coexisting-verdict reading is ACCEPTED — PASS yields
     **MECHANISM_SUPPORTED** on this claim id; the PREDICTIVE_EQUATION cap
     fallback is STRUCK.
   - **GOVERNING_LAW_CONFIRMED is out of scope, and the drafter agrees it
     must be.** Declared reasons: (i) §7 level-3 requires mechanism evidence
     of the intervention/invariance kind — none exists or can exist here
     (we cannot intervene on the Moon); (ii) B1 is a one-line truncation of
     lunar theory, not the governing law — v2's own R1 proved known
     inequalities (evection, variation, synodic) remain unmodeled, so
     calling the truncation a confirmed law would be false on the lab's own
     published evidence; (iii) the data are themselves the output of a DE441
     integration of the actual governing law — "confirming" against them
     can never discriminate the law from its truncations beyond forecast
     skill, which is exactly the MECHANISM_SUPPORTED rung and no higher.
2. **FAIL (any of C1–C2 fails on validly fetched data) → the claim records
   FAILED_EQUATION_SEARCH** (fresh-data confirmation failed): the frozen
   equation is **rejected on fresh data**, the v2 calibration PASS is
   flagged as non-predictive out-of-span, the equation layer's
   instrument-miscalibration flag is extended to single-line targets, and
   the failure is logged with the full residual trace (CLAUDE.md: dead ends
   are results, not embarrassments). No retroactive editing of v2 results.
3. C3 fails / fetch-protocol guard trips → NO_EQUATION_ATTEMPTED (the test
   did not occur; it may be re-attempted under the same hash once the
   protocol issue is fixed, with the re-attempt logged).

Hard rule 1 (verdicts never modify the batch5 detection verdict) and rule 8
(Doob separation — no action license; Phase 6 computes EV/sizing, not this
analyst) apply verbatim.

## 7. Multiplicity charge — m_delta = 1, justified

`{family_id: eq.tidal-manila.harmonic, m_delta: 1}`

One new test in verdict space: the frozen equation gets one shot at a
ladder promotion on data it has never seen. The fit itself adds zero search
flexibility (zero free parameters), so the charge is for the confirmation
attempt, not the model — the same verdict-space-charge convention as v2 §10
item 3 (confirmation family). Cumulative family charge if v3 and this are
both approved: 8 + 1 (v3) + 1 = 10. Reviewer option, noted before hashing:
judge the charge 0 on the ground that a pre-registered out-of-sample
evaluation with a declared two-sided consequence is self-policing; drafter
recommends keeping +1 — promotion attempts are exactly the kind of look
multiplicity accounting exists for.

## 8. Reproducibility

Scoring is deterministic given the raw fetch file: two-run rule = two
independent parse+score executions from the SAME saved raw response
(`_raw_horizons_moon_confirm1.txt`), byte-identical JSON required
(`results/_eq_moondist_confirm1_run{1,2}.json`). Seed base 20260614 for
diagnostic resampling only. Results to
`docs/RESULTS_EQ_MOONDIST_CONFIRM.md` + `results/eq_moondist_confirm1.json`
(raw-file sha256 embedded).

## 9. Sequencing note (declared, non-binding)

This confirmation is logically independent of
`eq.tidal-manila.phase.moondist.v3` (residual re-adjudication): C1/C2 do
not depend on the R1 grid question. The two may execute in either order;
executing v3 first is recommended only because its outcome refines the
interpretation section of this claim's results doc, not its gates.
Earliest valid fetch date — AMENDED by approver 2026-06-12: fetch-now is
APPROVED. Rationale: the data source is a deterministic DE441 integration;
future-dated ephemeris rows cannot be influenced by the fitted equation, and
the §5 DE-version guard voids the run if the integration changes. The
strict realized-dates reading (2026-09-06+) was considered and declined.

## 10. Proposed ledger deltas (PROPOSED — NOT APPLIED)

1. `results/commitment_ledger.txt`: append SHA-256 of this file
   post-approval, pre-fetch, claim id
   `eq.tidal-manila.phase.moondist.confirm1`.
2. `results/run_ledger.jsonl`: new entry run_id `eq_moondist_confirm1`,
   phase 5 (confirmation step), source run `batch5`, predecessor
   `eq_tidal_v2`, equation_analyst_id (≠ batch5 analyst, ≠ v2 executor),
   fetch executed by orchestrator/data path, registration hash, seed base
   20260614.
3. `results/multiplicity_ledger.jsonl`: append
   `{family_id: "eq.tidal-manila.harmonic", m_delta: 1, reason: "fresh-data confirmation attempt of frozen v2 B1 (verdict-ladder promotion test)"}`.

None applied. This document is the only artifact of this dispatch.

## 11. Human approval

```
APPROVED BY: Cha (lab owner) — in-session approval
DATE:        2026-06-12
AMENDMENTS:  §7 PREDICTIVE_EQUATION cap fallback STRUCK (MECHANISM_SUPPORTED
             ceiling stands); §9 fetch-now approved (deterministic-ephemeris
             rationale recorded in §9)
COMMITMENT HASH (post-approval): <appended to results/commitment_ledger.txt
             immediately after this edit; the ledger line is authoritative>
```
