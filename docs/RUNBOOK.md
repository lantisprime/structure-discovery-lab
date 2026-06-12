# RUNBOOK — Structure Discovery & Decision Pipeline

The reusable workflow developed in the PCSO lotto project (Jun 2026). Domain-agnostic:
applies to any sequence suspected of hiding structure — lottery draws, asset returns,
sensor noise, RNG outputs. The lottery files in this folder are the worked example.

```
PHASE 0          PHASE 1            PHASE 2             PHASE 3           PHASE 4
ACQUIRE   ───►   VALIDATE    ───►   EXPLORE      ───►   REGISTER   ───►   CONFIRM
& define         (row-level         (instrument         (freeze +         (held-out
the null          audit)             suite, MC-          pre-commit)       data only)
                                     calibrated)              │                │
                                          │                   │                ▼
                                          ▼                   │           PHASE 5
                                     ADVERSARIAL ◄────────────┘           EQUATION
                                     REVIEW (always)                      (candidate
                                                                           governing eqs)
                                                                                │
                                                                                ▼
                                                                           PHASE 6
                                                                           DECIDE
                                                                           (EV/Kelly layer)
```

---

## Phase 0 — Acquire data & define the null

1. **State H₀ in one sentence before touching data.** (Lottery: "i.i.d. uniform on
   C(P,6)." Markets: "returns are a martingale difference w.r.t. public info.")
   Everything downstream tests deviations from this sentence.
2. Pull data from a primary source; identify ≥2 independent secondary sources up front.
3. Store as flat CSV with stable schema (one row = one event, ISO dates).
   *Lottery artifacts: `data_draws_1yr.csv`.*

## Phase 1 — Validate (no analysis before this gate)

4. **Row-level audit table**: every row tagged `official_verified` /
   `two_source_verified` / `single_source_only` / `suspicious_or_needs_review`.
   *Artifact: `data_draws_1yr_audited.csv`.*
5. Structural integrity scan: schema/range checks, duplicates, near-duplicate
   signatures (adjacent-row similarity), schedule/calendar consistency, gap analysis
   vs known suspensions/holidays, sequence-number continuity where available.
6. **Adjudicate every flag before proceeding** — fetch the disputed rows from
   independent sources (we found 3 archive-side errors this way; 2 "anomalies"
   were verified genuine). Rule: *no anomaly is interesting until the rows driving
   it are verified.*

## Phase 2 — Explore (hypothesis generation, MC-calibrated)

7. Run the instrument suite. Four faces, every face covered:
   - **Statistical**: frequency chi-square (exact MC, never asymptotic when expected
     counts < 5), scan statistics for hot runs (look-elsewhere built in), rolling-window
     persistence, covariate permutation tests.
   - **Dynamical**: Markov order-0 vs order-1 (overlap, stickiness, G-test, |λ₂|),
     Hurst R/S, walk-forward predictive models.
   - **Algorithmic**: compression vs Shannon bound, sequence-learnability MLE (β).
   - **Cross-sectional/physical**: Marchenko–Pastur eigenvalue escape, Fisher g
     periodicity, SOC scan (1/f, avalanches), CSN power-law vs exponential (Vuong),
     universality machinery (data collapse, RG flow, Binder cumulant).
   *Artifacts: `src/markov_analysis.py`, `structure_discovery.py`,
   `montecarlo_certification.py`, `cross_theorem_correlation.py`,
   `perbak_soc_analysis.py`, `universality_collapse.py`, `explore_batch2.py`.*
8. **Iron rules of Phase 2**:
   - Every p-value Monte Carlo / permutation calibrated against the *constrained* null.
     (Uncalibrated physics estimators lied twice here: Hurst and Binder.)
   - Count every test; track the family size m; report the Bonferroni/BH threshold.
   - Expect ~m/20 nominal "hits" by chance; check whether the p-value *distribution*
     matches the null (true randomness passes at exactly the predicted rate).
   - One anomaly seen through k correlated statistics is ONE anomaly, not k.
     Trace every flag to its driving rows before counting it.
   - Seed everything; one script per instrument; scripts standalone & reproducible.

## Phase 3 — Adversarial review & register

9. **Adversarial review** (or ask a second model): attack data provenance, statistic
   validity, family accounting, estimator bias, backtest leakage. Fix all severities;
   log every finding and disposition. *Artifact: RESEARCH_NOTES.md §7 review log.
   Caught here: 0.5-centered smoothing that manufactured a backtest edge; degenerate
   KS under ties; T1/T2 double-counting; container overhead in compression test.*
10. **Freeze the exploration set.** Nothing found in it can ever confirm itself.
11. **Pre-register** the confirmation family: exact tests, exact thresholds
    (α/m), decision rule, and the held-out data definition. No additions without
    resetting the confirmation set. *Artifact: RESEARCH_NOTES.md §3b/§6b; lottery
    family m=9, p<0.0056.*

## Phase 4 — Confirm (automated, held-out only)

12. Schedule automated updates: append new data WITH two-source validation, run ONLY
    the registered family on post-freeze data, report exact p-values.
    *Artifact: scheduled task `pcso-weekly-update`, Wednesdays 10:00.*
13. A flag means "replicate on further fresh data," never "act."
    Sequential testing without alpha-spending guarantees eventual false positives —
    the fixed registered family is the protection.

## Phase 5 — Equation discovery (candidate governing equations)

Full specification: `docs/EQUATION_DISCOVERY.md`. Summary:

13a. **Gate**: only confirmed STRUCTURED claims enter; everything else is
     `NO_EQUATION_ATTEMPTED`. Detection verdicts are never upgraded by a good fit.
13b. Register the candidate equation family BEFORE fitting (human-approved,
     commitment-hashed, multiplicity-charged) including a **null-equation
     generator**: the same discovery procedure run on matched synthetic nulls —
     equation searches on noise return equations, so only the null distribution of
     recovered-equation scores calibrates the claim.
13c. Select by held-out skill + MDL penalty (λ declared at registration); require
     bootstrap parameter stability, clean residuals, and per-data-regime
     coefficient reports. Verdict labels: CANDIDATE_EQUATION →
     PREDICTIVE_EQUATION → MECHANISM_SUPPORTED → GOVERNING_LAW_CONFIRMED;
     FAILED_EQUATION_SEARCH is publishable.
13d. A PREDICTIVE_EQUATION confers no action license — Phase 6 still gates.

## Phase 6 — Decide (the theorems about action)

14. Convert verdicts to decisions through the decision layer, never directly:
    - **Doob / optional stopping**: fair process ⇒ no strategy. Full stop.
    - **EV decomposition**: payout-relevant expectation with honest input ranges and
      sensitivity analysis (our EV stayed negative under all scenarios).
    - **Kelly / St. Petersburg**: even a real edge prices a stake; f* bounds how much.
    - **Payout-relevant backtesting**: score models in the unit that pays (3+ matches,
      net-of-cost returns), never in proxy units (single-number hits flattered the
      Markov model until prize-weighting showed −71% ROI).
15. Publish derived values, not narratives. (The webpage shows formulas and computed
    quantities only — every claim checkable by hand.)

---

## Failure-mode gallery (all caught live in this project — check for them every time)

| # | Failure | Where it appeared | Defense |
|---|---|---|---|
| 1 | Estimator bias read as signal | Laplace smoothing → fake repeat-bias; Hurst Ĥ=0.7; Binder plateau | MC-calibrate every estimator |
| 2 | Look-elsewhere effect | "hot #45" naive p=0.001 → corrected p=0.148 | scan statistics; count the search space |
| 3 | One anomaly counted k times | #45 flagged by 6 correlated statistics | trace flags to driving rows |
| 4 | Degenerate statistic | KS on tied discrete gaps (p≡1.0) | sanity-check the null distribution itself |
| 5 | Proxy-metric backtests | single-hit z=+2.1 → payout ROI −71% | score in the unit that pays |
| 6 | Garden of forking paths | retroactive test family | freeze + pre-register |
| 7 | Source-data corruption | 3 archive errors, 2 pseudo-anomalies | row-level multi-source audit |
| 8 | Sequential peeking | weekly re-testing | fixed registered family on held-out data |

## Porting to markets (next application — adjustments required)

- H₀ becomes the martingale/EMH null; expect REJECTIONS (fat tails, volatility
  clustering, MP eigenvalue escapes are known facts) — the suite's job shifts from
  "certify randomness" to "map which structure exists, then test whether any of it
  survives costs out-of-sample."
- Non-stationarity is worse than lotteries: regimes die like hot-45 did. Rolling-window
  persistence (Phase 2) becomes the central instrument, not a side check.
- Phase 6 gains a costs model (spread/fees/slippage) before EV, and Kelly fractions
  shrink under estimation error (use fractional Kelly).
- Decision output is information for the human; not personalized financial advice.

## Lottery-project maintenance (standing)

- `lotto_picker.html` — keep; update jackpot defaults from latest verified draws and
  the constants block whenever a new instrument family reports. Mobile: copy to iCloud
  Drive → open via Files app (full JS works), or host for a URL.
- Weekly task `pcso-weekly-update` — runs Wednesdays 10:00; two-source appends + the
  m=9 registered family incl. the 6/55 #45 binomial test.
- Workbook `PCSO_Lotto_Analysis_Mar-Jun_2026.xlsx` — Future Draws sheet regenerates on
  request (protocol pairs); EV Calculator yellow cells need official prize updates.
- Open items: 6/55 2025-10-29 row needs a third source; lower-tier prize values
  pending official PCSO figures.
```
File inventory: RESEARCH_NOTES.md (evidence log) · THEOREM_SYNTHESIS.md (theory map) ·
RUNBOOK.md (this) · data_draws_1yr[_audited].csv · 8 instrument scripts ·
lotto_picker.html · workbook · requirements.txt
```
