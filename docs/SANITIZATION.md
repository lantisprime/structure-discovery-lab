# Sanitization — Domain-Neutral Core (lab-owner directive, 2026-06-11)

**Principle**: this is a general structure-discovery laboratory. Domain
vocabulary is allowed in exactly four places: `src/domains/<domain>.py`
(config), frozen historical records, domain datasets/results, and domain
deliverables (e.g. the picker page). Everywhere else is a neutral zone,
enforced mechanically by `src/lint_domain_neutrality.py` (currently **PASS,
16 files clean**; word list includes the application's game names and
gambling vocabulary, with word boundaries).

## What changed

| Layer | Action |
|---|---|
| **`src/core/`** (new) | Domain-neutral instrument library — the forward-facing API for all new experiments: `stats` (Phipson–Smyth p, gates, Šidák), `discrete_draws` (k-of-P ensembles, presence matrices, count/overlap/half-deviation statistics, co-occurrence spectra), `recovery` (temporal k-NN, recovery curves), `paired` (held-out CCA, MMD), `geometry` (delay embeddings, persistence, GW — with its standing G0 flag), `graphs` (spectra, degree-preserving nulls, SBM), `completion` (SoftImpute). Implementations re-export the battle-tested functions from frozen modules → **zero behavior drift**, verified by rerunning blind-eval stages after the repoint: outputs byte-identical |
| **`src/domains/pcso_lotto.py`** (new) | The single coupling point: draw-ensemble registry, loaders with data-quality regimes, covariate bundle, ANOMALY_REGISTRY (for C9 row-trace duties), ERA_REGISTRY (A5). A new domain = a new file with the same interface; core never changes |
| **21 historical scripts** | Stamped `FROZEN HISTORICAL RECORD` — they reproduce hash-ledgered results (rows 1–39) and are domain-specific *by nature*; rewriting them would break the reproducibility chain, which would be falsifying history, not sanitizing code |
| **5 domain artifacts** | Stamped `DOMAIN ARTIFACT` — verify/transcribe this domain's recorded results (`verify_relational_docs`, ledger builders, `meta_uniformity`, figures); domain vocabulary is their job |
| **Agent definitions** | Scrubbed to neutral: editor's deliverables → "the active domain's web deliverables"; analyst's anomaly check → "the active domain's ANOMALY_REGISTRY"; decision-logic rule generalized. All 7 agent defs now lint-clean |
| **Blind-eval runner** | Repointed to `core` (it was already conceptually generic); duplicated helpers single-sourced; **output identity verified** (draws_marg, draws_mem, series_rec re-run → identical to committed values) |

## What deliberately did NOT change

- `datasets/pcso-lotto/`, `results/*.json`, `docs/RESULTS_*`, `REGISTRATION_*`,
  `lotto_picker.html`, KB-card "use in this project" fields — these are the
  domain *application* and its evidentiary record. The lab studies domains;
  its records of doing so are supposed to name them.
- The governance documents (A1–A7, C1–C10, Part 3/4) were already
  domain-portable by design (the RUNBOOK's market-porting notes predate this).

## Going forward (added to the runbook output contract)

New experiment scripts import **only** `core` + one `domains.<domain>` module;
`lint_domain_neutrality.py` must PASS alongside the numeric and design
verifiers before any results doc is published. Onboarding a new domain
(markets, sensors, …) = one domain module + Part 4 dataset onboarding; every
instrument, null, gate, ledger, and agent works unchanged.
