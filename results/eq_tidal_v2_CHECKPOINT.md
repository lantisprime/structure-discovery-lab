# CHECKPOINT — eq_tidal_v2 (Phase 5 execute run)

Executor: equation-analyst (fable, v2 execution dispatch). Independence: NOT the
batch5 detection analyst; NOT the v1 same-claim verifier (rule 2 OK — to be
recorded by orchestrator in run_ledger row eq_tidal_v2).

Registration: docs/REGISTRATION_EQ_TIDAL_V2.md sha256
4761403580ba138b4cffd5f6f5febe780e23bcf96158084b69cee459a34bbe76 — VERIFIED
against results/commitment_ledger.txt line "4761403580ba138b ... (APPROVED
2026-06-11, pre-fit)". Gate PASS (source claim STRUCTURED batch5, attribution
on file, run_ledger row exists with PENDING fields).

Seed base 20260612; stage offsets {null_equation_generator:0, fit:1, nulls:2,
bootstrap:3, residuals:4}. B_nulls=200/type/claim, B_boot=500, block 15 d.

## Step plan
1. [done] Gate + ledger + hash + deps + data verification -> (this file)
2. [done] Write src/eq_tidal_v2.py -> src/eq_tidal_v2.py (smoke test of
       deterministic fit stage OK: A selects A2 J=21.12 over A4 40.25 /
       A5 48.26; B selects B1)
3. [done] Execute. Sandbox reaps background processes + 45s/call limit ->
       declared conservative deviation: staged CLI (--single run twice as
       separate processes, --finalize byte-compares and assembles). Runs:
       results/_eq_tidal_v2_run1.json, results/_eq_tidal_v2_run2.json
       (~20 s each).
4. [done] results/eq_tidal_v2.json written; sha256
       fdc12e7251b59fecf33a9301879cb8e5b735673074f79468e1ecb7596bb1a625
5. [done] Two-run rule: run1 vs run2 cmp EMPTY -> byte-identical (two
       separate full process executions, identical seeds)
6. [done] docs/RESULTS_EQ_TIDAL_V2.md written (numbers traceable to JSON)
7. [done] Final rule-10 report returned (no ledger edits — orchestrator
       applies deltas)

## Outcome snapshot
- A eq.tidal-manila.phase.v2: A2 selected (min-J rejects A4/A5);
  FAILED_EQUATION_SEARCH; calibration FAIL (spring-neap not in selected
  model); surrogate p = 0.194 (benchmark 0.209 NOT beaten at <=0.01).
- B eq.tidal-manila.phase.moondist.v2: B1; FAILED_EQUATION_SEARCH
  (R1 whitelist + R3 TDA absorption fail); calibration PASS
  (27.604 d, 0.18% err, CI contains truth); all three nulls beaten
  (surrogate p = 0.00995).

## Declared interpretation choices (conservative, pre-execution)
- §7.2 R1 merge rule: the whitelist parenthetical restricts pairwise Rayleigh
  merges to claim A only; the attribution-rule example mentions claim B. The
  STRICTER reading is adopted: merge attribution allowed for claim A only;
  claim B peaks must sit within one Rayleigh bandwidth of a whitelist period
  directly. (Stricter = easier to FAIL = conservative.)
- "Two whitelist periods separated by < 2 Rayleigh bandwidths" implemented as
  (P2 - P1) < ΔP1 + ΔP2 with ΔPi = Pi²/T_trainval; relevant pairs
  (13.777,14.765) and (29.531,31.812) qualify under either reading.
- Iterative Fisher-g for "every peak significant at p<0.01": test max
  ordinate, if p<0.01 record + attribute, remove that ordinate, retest with
  m-1 ordinates; stop at p≥0.01 (cap 20 iterations).
- Residual gate α = 0.01 per §7.2 (R2 CUSUM, R4 compression); R3 gate is the
  absolute persistence threshold 0.562 (declared), permutation p reported as
  diagnostic.
