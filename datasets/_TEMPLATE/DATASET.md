# DATASET CARD — <dataset-id>

Onboarded: <date> · Status: <ONBOARDING | ACTIVE | FROZEN | RETIRED> · Owner: <name>

> Fill every section BEFORE any instrument runs (Governance Part 4). A dataset without
> a completed card is not admissible. Copy this folder to `datasets/<dataset-id>/`.

## 1. Identity & generative null (H₀)
What the data is, who generates it, and **H₀ in one sentence**. Then the **null
simulator**: the exact constrained generative model every instrument's Monte Carlo must
use (sampling scheme, constraints, sequence lengths). If you cannot write the simulator,
you do not yet understand the null (markets: a permutation/block-bootstrap scheme).

## 2. Files in this folder
Table: file, rows, role. One canonical file; raw extraction stages kept as provenance;
audited variant alongside. Never edit canonical files in place — append or version.

## 3. Schema (canonical)
Exact columns, types, units, ordering semantics (does row/field order carry physical
meaning? e.g. PCSO exit order), key constraints (uniqueness, ranges). Freeze it; schema
changes require re-onboarding.

## 4. Provenance & audit status
Primary source, independent verification sources, row-level audit census
(official / two-source / single-source / suspicious counts), and the unresolved-row
list. Rule: **no anomaly is reportable until its driving rows are multi-source verified.**

## 5. Era registry (stationarity boundaries)
Every known regime event (rule changes, equipment cycles, market-structure changes,
sensor recalibrations) with dates and analytic consequences. Pooled statistics across
a listed boundary are quarantined (Governance A5/C5).

## 6. Frozen/holdout structure (BINDING)
Exploration-set boundary date; confirmation-set definition; the registered test family,
its size m, and threshold. State the reset rule.

## 7. Known anomalies & dispositions
Each anomaly: rows driving it, verification status, look-elsewhere-corrected
significance, persistence behavior, disposition (artifact / era-bounded / live /
under monitoring), and the list of correlated statistics it surfaces in (count once).

## 8. Update pipeline & instruments
How new rows arrive (manual/scheduled), validation requirements on append, which
scripts consume the canonical file, where results are ledgered.

## 9. Loading snippet
Minimal copy-paste code that loads the canonical file correctly.

## 10. Domain cautions (delete what does not apply)
Costs/frictions to apply before EV (markets: spread, fees, slippage); legal/ethical
notes; expected-structure prior (certify-randomness vs map-structure mission);
sensitive-data handling.
