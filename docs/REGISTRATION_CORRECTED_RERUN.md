# Registration — Corrected-Instrument Rerun (presence-MC v2, standardized CCA, attribution v2)

**Status: APPROVED by the lab owner (Cha), 2026-07-03, via Cowork session
("approved"). Committed before execution; sha recorded in
results/commitment_ledger.txt.**

Date drafted: 2026-07-03 · Protocol: RELATIONAL_RUNBOOK Phase 1,
expectation-free (no outcome expectations for any discovery test).
Purpose: convert the exploratory shadow indications of
`results/corrected_reruns_2026-07-02.json` into citable registered results
(AUDIT_RESOLUTION M-2/M-3/M-4; adversarial review M-B conditions).

## 0. Prior-look disclosure (mandatory, review M-B rule 2)

The corrected instruments were executed once on this same real data on
2026-07-02 as an unregistered shadow (run_id `audit_shadow_2026-07-02`,
ledgered exploratory, seed 20260702). Observed indications: presence-MC v2
joint NULL (min p 0.28); CCA-std H_R3 NULL (p 0.345) / H_R4 positive
control detects (p 0.005); attribution v2 fire-dissolves (p 0.148). This
registration DISCLOSES that look; the rerun uses a fresh seed and disjoint
permutation randomness. Because data and statistics are identical, the
rerun is confirmatory of instrument behavior, not an independent discovery
test; the look is already charged to the exploratory stratum and this run
charges its own family m below.

## 1. Claim table

| # | claim | instrument (corrected) | statistic | null (invariants preserved) | m_null | family | within-run m → Šidák α' | floor ≤ α'/2 |
|---|---|---|---|---|---|---|---|---|
| 1–5 | subset-to-whole, 5 games | `corrected_reruns.run_presence_mc_v2` | soft-impute skill over marginal | constrained 6-of-P uniform, frozen mask | 399 | recovery | 5 → .0102 | .0025 ≤ .0051 ✓ |
| 6 | latent-sharing, 6/55 draws vs covariates | `corrected_reruns.ridge_cca_heldout_std` | held-out ρ₁ (train-moment z-scored) | shuffled held-out pairing | 399 | cca | 2 → .0253 | .0025 ≤ .0127 ✓ |
| 7 | latent-sharing positive control, tidal vs ephemerides | same | held-out ρ₁ | shuffled held-out pairing | 399 | cca (positive control; not a discovery claim) | — | ✓ |
| 8 | within-game-cooccurrence, 6/55 attribution re-test ex-ball-45 | `corrected_reruns.attribute_v2` | graphon B1 spectral norm, lead row/col removed | constrained 6-of-(P−1), relabeled | 999 | hit-count-cooc | 1 → .05; declared threshold .0025 held from original protocol | .001 ≤ .00125 ✓ |

Data: `datasets/pcso-lotto/data_draws_1yr_audited.csv` (+ tidal/ephemerides/Kp
CSVs for claims 6–7), all_rows regime; 3-regime sensitivity rows for any
hit-count flag per M4.

## 2. Fixed design

- **Seed: 20260711** (fresh; shadow used 20260702; never reuse either).
- Executor: `src/corrected_rerun_registered.py` (thin runner over the
  committed corrected functions; two-run byte-identical JSONs required).
- Correction basis: convention v1 (Šidák .05; families per this run —
  detection battery, not an accumulating claim chain).
- Verdict tiers per playbook S-5, applied in-run. Era gate: 6/55 sample
  intersects the Feb-2026 era registry boundary? No — 1-yr audited window;
  ex_suspicious sensitivity regime still reported for 6/55 rows.
- Every p ledgered (schema v2, row_type test, NOT exploratory); run-ledger
  row `corrected_rerun_r1`; design_verifier + verify_relational_docs must
  PASS before any results doc is published.

## 3. Outcome branches (both declared)

- **NULL everywhere** (min corrected p above threshold): publish as
  registered confirmation that the published relational verdicts are
  ensemble-robust; meta panel v2 re-admits the presence family rows from
  THIS run (replacing the excluded miscalibrated v1 rows).
- **Any corrected rejection**: row-trace (S-6) against ANOMALY_REGISTRY
  before any anomaly language; a 6/55 cooccurrence flag is expected to
  trace to the #45 family (measured ρ=0.988) and charges nothing new if it
  does.

## 4. Multiplicity

Families engaged: 3 (recovery, cca, hit-count-cooc) → run-level charges per
§1. No family_charge rows (no new accumulating claim family).

## 5. Approval

- approved_by_human: Cha (lab owner, via Cowork session)  date: 2026-07-03
- registration_sha (at commit): recorded in results/commitment_ledger.txt
