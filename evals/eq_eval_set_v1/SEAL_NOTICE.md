# SEAL NOTICE — eq_eval_set_v1

Sealed at build time (2026-07-02): `answer_key/` (ground_truth.json,
GROUND_TRUTH.md), `src/generate_eq_eval.py` (contains all planted
parameters), and `manifest.json` (sha256 of every pack file, including the
generator — so the key provably predates any run).

## Seal rules

1. The blind run's executor must NOT read the sealed files. Because this
   pack was authored by the same agent lineage that built the v4 machinery,
   the executor MUST be a fresh agent/session with no memory of this build
   (role separation; the same rule the lab used for blind_verification).
   The builder session may never execute or score its own run of this pack.
2. Unsealing is permitted only after `results/eq_eval_verdicts.json` is
   hash-committed (commitment ledger + git).
3. Scoring uses `src/score_eq_eval.py`; the score doc records the verdicts
   file's sha256 next to the manifest's.
4. Any regeneration (rerunning the generator) is detectable: manifest hashes
   are recorded in `results/commitment_ledger.txt` at the lab root. A
   changed hash voids the pack (issue eq_eval_set_v2 with a new seed).

## Contents summary (unsealed knowledge)

12 univariate daily series, n=400, mixture of: pure nulls, structured
non-equation processes, recoverable harmonic laws across an SNR ladder, and
traps (close line pairs, trends, hidden residual lines, era-bounded lines).
Proportions, parameters and per-unit labels are sealed.
