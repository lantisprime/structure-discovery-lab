# Equation-Discovery Evaluation Set v1

Sealed benchmark for the lab's Phase-5 equation pipeline (v4 machinery,
`src/eq_selection_v4.py`; playbook Q-1..Q-8). Companion to
structure_eval_set_v1, which benchmarks detection but contains no equation
units (RESULTS_EVAL_RERUN_2026-07-02.md §4.1). Prerequisite for v4's first
real-data publication.

| folder / file | contents |
|---|---|
| `blind/` | 12 datasets + lab instructions + registration template — the only part a run may read |
| `answer_key/` | SEALED ground truth + scoring rubric |
| `src/generate_eq_eval.py` | SEALED deterministic generator (seed 20260702) |
| `src/score_eq_eval.py` | scorer (run after verdicts are hash-committed) |
| `manifest.json` | sha256 of every file; recorded in the lab commitment ledger |
| `SEAL_NOTICE.md` | seal + role-separation rules |

What it scores: refusal on nulls (2 units), absorption of colored noise /
random walks / chaos (3), period recovery with honest CIs across an SNR
ladder (3, one deliberately borderline), close-pair identifiability (1),
trend separation (1), residual-scan behavior with and without whitelist (1),
era-bounded nonstationarity handling (1).

Workflow: fresh executor agent gets `blind/` only → registers via the
template (human approval) → runs → hash-commits
`results/eq_eval_verdicts.json` → unseals → `src/score_eq_eval.py`.
Pass targets: 0 false positives, 0 false recoveries, 0 overclaims,
≥3 of 4 detect-class recoveries (two ladder units are declared-borderline), correct scan behavior on the hidden-line unit.
