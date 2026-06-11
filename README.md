# Structure Discovery Laboratory

**A governed, reproducible research framework for detecting — or rigorously excluding —
structure in stochastic data.** The laboratory combines instruments from five
mathematical traditions (statistics, stochastic processes, information theory, random
matrix theory, statistical physics) under a single calibration discipline, with formal
protocols for onboarding theorems, onboarding datasets, harmonizing their conflicts,
and confirming findings on held-out data.

**Case Study 1 (complete): PCSO lottery draws** — 776 multi-source-validated
observations, 25+ instrument families, a fully adjudicated anomaly, and a positively
identified fixed point. Chosen as the inaugural dataset precisely because its ground
truth is engineered: a system *designed* to be structureless is the ideal instrument
calibrator. Every certificate that stays silent here is demonstrably honest when
pointed at data where structure is expected (Case Study 2, planned: financial returns).

## Research questions the framework answers

1. **Detection** — does this sequence deviate from its declared null model, on any of
   the four faces of randomness (marginal, dynamical, algorithmic, cross-sectional)?
2. **Attribution** — is a detected deviation data corruption, estimator bias,
   look-elsewhere illusion, era-bounded transient, or persistent mechanism?
3. **Decision** — if structure exists, what is it worth under explicit decision theory
   (Doob gate → expected value → Kelly sizing), net of costs?

## Methodological contributions (what this framework adds)

- **Single-null calibration (Article A1):** every instrument's null distribution is
  Monte-Carlo–derived from one executable generative model — never from textbook
  asymptotics. This dissolved four would-be discoveries in Case Study 1 (Hurst bias,
  Binder pseudo-plateau, degenerate KS, smoothing-bias backtest edge), each now
  documented as a worked counterexample.
- **Null-trial admission:** no estimator touches real data before demonstrating
  silence on simulated H₀ of identical shape.
- **Equivalence-class multiplicity accounting:** test families count statistic
  *classes* (null-correlation ≥ 0.90 ⇒ same class), and anomalies are identified by
  driving rows — the Case Study 1 anomaly surfaced in nine correlated statistics and
  was correctly counted once.
- **Era-gated stationarity (A5)** and **registered confirmation on held-out data (A6)**
  — exploration can motivate, never confirm.
- **Deterministic reproducibility:** fixed seeds, fixed constants, an output contract;
  two independent executors (human or LLM) must produce identical numbers.

## Repository guide

### Framework documents (domain-agnostic, reading order)
1. **docs/RUNBOOK.md** — the 6-phase workflow + failure-mode gallery + domain-porting guide
2. **docs/EVALUATION_PROTOCOL.md** — formula-level spec (E0–E9 evaluation, H1–H7
   harmonization); the deterministic guide for human or LLM executors
3. **docs/THEOREM_GOVERNANCE.md** — conflict registry C1–C8, harmonization constitution
   A1–A7, theorem onboarding (Part 3), dataset onboarding (Part 4)
4. **docs/THEOREM_SYNTHESIS.md** — the theory map: four faces of randomness, the implication
   lattice, instrument correlation, the 25-row results ledger
5. **docs/CROSS_DATASET_FRAMEWORK.md** — the *relational* extension (fifth face):
   cross-dataset similarity/alignment and subset-to-whole recovery (D = S ∪ H), folded onto
   the same constitution (A1–A7). Method-by-case taxonomy, matched relational nulls, a
   9-experiment benchmark suite, decision tree, and the structure-recovery curve. Read after
   the four-face map; it overrides nothing and reuses onboarding Parts 3–4 verbatim.
6. **docs/kb/** — methodology knowledge base: 16 theorem cards (statement, assumptions,
   null values, finite-sample cautions, distilled references) + INDEX
7. **docs/AGENT_WORKFLOW.md** — model-routed agent execution: onboarder (Haiku), analyst (Fable design / Haiku execution), editor (Sonnet), fallback chains for non-Claude executors; agent definitions in `agents/`
8. **admin_onboarding.html** — gate-checked wizard generating conformant onboarding
   artifacts for new theorems and datasets

### Case Study 1 artifacts (PCSO lottery)
- **docs/RESEARCH_NOTES.md** — full evidence log: every test, p-value, correction, and the
  adversarial-review trail
- **datasets/pcso-lotto/** — DATASET.md card (H₀ + null simulator, schema, audit
  census, era registry, holdout structure) + canonical/audited/provenance CSVs;
  `datasets/_TEMPLATE/` for new datasets
- **Instrument scripts** (in src/; standalone, seeded; RUN FROM PROJECT ROOT — data paths are root-relative):

```bash
pip install -r requirements.txt
python3 src/montecarlo_certification.py   # marginal uniformity + ensemble certification
python3 src/markov_analysis.py            # dynamical face: order-0 vs order-1
python3 src/structure_discovery.py        # algorithmic + cross-sectional: compression/RMT/spectra
python3 src/powerlaw_sweep.py             # scaling laws: Zipf, Taylor, first-digit, Levy, coverage
python3 src/perbak_soc_analysis.py        # statistical physics: SOC signatures
python3 src/universality_collapse.py      # data collapse, RG flow, Binder cumulant
python3 src/explore_batch2.py             # positional/calendar/pair/scan statistics
python3 src/cross_theorem_correlation.py  # cross-domain coupling detector
python3 src/review_response.py            # audit table, payout-relevant backtest, persistence
python3 src/markov_chain_model.py         # generative model + walk-forward evaluation
```

- **Application layer**: `lotto_picker.html` (derived-values interface: combinatorial
  odds, entropy bounds, EV/Kelly, decision-theory-compliant selections) and
  `PCSO_Lotto_Analysis_Mar-Jun_2026.xlsx` (interactive workbook). A scheduled task
  (`pcso-weekly-update`, Wednesdays) appends validated observations and runs only the
  registered confirmation family (m=9, α′=0.0056).

## Case Study 1 — headline results

| Result | Value |
|---|---|
| Instrument families applied | 25+ across four faces; all MC-calibrated |
| Verdict | indistinguishable from i.i.d. uniform; p-values distributed exactly as H₀ predicts |
| Entropy floor | 22.3–25.3 bits/observation, irreducible (prediction impossible in principle) |
| Fixed point | trivial/infinite-temperature, positively identified via data collapse + RG flow |
| Universality observed | Tracy–Widom (λ_max skew +0.316 vs +0.293), Gaussian, Gumbel — governing the *noise* |
| The one anomaly | 6/55 #45 (2025): verified data, era-bounded, look-elsewhere p=0.148, 9 correlated flags = 1 anomaly, under registered monitoring |
| Methods casualties caught | 4 (smoothing bias, degenerate KS, Hurst bias, Binder plateau) — all by calibration/review |
| Decision layer | EV ₱0.17–0.31/peso at current jackpots; Kelly stake bound f* ≤ 1/C(n,6) |

## Extending the laboratory

- **New theorem/methodology** → `admin_onboarding.html` (Theorem tab) or Governance
  Part 3: KB card + conflict scan + null trial + class assignment, all gated.
- **New dataset** → Admin page (Dataset tab) or copy `datasets/_TEMPLATE/`: card with
  executable null simulator is the admission requirement.
- **New domain** → RUNBOOK porting section. For financial data the mission inverts:
  H₀ rejections are *expected* (heavy tails, volatility clustering, factor structure);
  the framework's job becomes attribution and net-of-costs survival testing — which is
  where its anti-self-deception machinery matters most.

## Scope & ethics note

The lottery case study is a negative-result study by design: it demonstrates the
framework's resistance to false discovery on a system whose ground truth is known.
It neither predicts nor claims to predict lottery outcomes (entropy floor above);
the application layer prices tickets honestly (expected cost ≈ ₱17–20 per ₱25) and
links PCSO responsible-gaming resources. Nothing in this repository is financial
advice; the framework informs decisions, humans make them.

*Protocol v1.0 · Jun 10–11, 2026 · Cha & Claude.
Case Study 1: 776 observations, 25 instrument families, 0 exploitable patterns,
1 fully adjudicated anomaly, 4 estimator artifacts caught and documented.*
