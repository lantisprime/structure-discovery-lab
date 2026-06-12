# CHECKPOINT — eq_tidal_v3 + eq_moondist_confirm1 (executor dispatch 2026-06-12)

Executor: equation-analyst (Fable), execute-only dispatch.
Independence recorded: this instance != batch5 detection analyst,
!= v2 executor (ae5be394c9693908c), != v2 verifier (af632a92025624f8a).
Registrations (APPROVED, hashed): REGISTRATION_EQ_TIDAL_V3.md (4fc27d0e621d4250),
REGISTRATION_EQ_MOONDIST_CONFIRM.md (9b0626c12f6f273b). Amendments honored:
v3 +1 charge stands, claim A 36.625 d in scope at +0; confirm1
MECHANISM_SUPPORTED ceiling, fetch-now approved.

## Step plan

1. Verify fresh raw file sha256 == 4724920d212aa85f... and registration hashes
   in commitment ledger; inspect raw Horizons file vs §3.2 guards (86 rows,
   DE441, 13:00:02.880 stamps, delta AU).
2. Write src/eq_tidal_v3.py: deterministic B1 (and A2) re-derivation +
   byte-equivalence check vs results/eq_tidal_v2.json; v2-identical R1
   detection on natural grid; 16x zero-padded fine-grid relocation (+-1
   natural bin); whitelist + Rayleigh attribution on refined locations
   (merge: claim A only, as v2); leakage-collapse clustering (1 Rayleigh bw
   = 1/T cyc/d, T=292 as implemented in v2); R2/R3/R4 + diagnostics
   re-verified with the exact v2 rng stream (seed 20260612+4 per claim) to
   check exact reproduction; v3 seed base 20260613 recorded (procedure
   deterministic; no new stochastic stage needed).
3. Run v3 twice (separate processes) -> results/_eq_tidal_v3_run{1,2}.json;
   finalize byte-diff -> results/eq_tidal_v3.json.
4. Write src/eq_moondist_confirm1.py: §3.2 guards on the raw file; parse
   (km = AU*149597870.700, 0.1 km precision); B1 freeze verification
   (byte-equivalence); score t=366..451 verbatim, no re-anchoring; C1/C2/C3;
   non-gating diagnostics; seed base 20260614.
5. Run confirm1 twice from the same raw file ->
   results/_eq_moondist_confirm1_run{1,2}.json; finalize ->
   results/eq_moondist_confirm1.json.
6. Write docs/RESULTS_EQ_TIDAL_V3.md and docs/RESULTS_EQ_MOONDIST_CONFIRM1.md.
7. Final rule-10 report (both runs).

## Pre-scoring adjudications (declared BEFORE any residual/score is computed)

1. Raw sha256 verified: 4724920d212aa85fadb6c391d89d813048616aa379eef07159bab4ad2585dc30
   == committed ledger line. Registration hashes verified (4fc27d0e..., 9b0626c1...).
2. Raw header guards: 86 rows SOE..EOE; DE441 ("Target: Moon (301) {source: DE441}");
   "1 au = 149597870.700 km | delta in AU"; span 2026-Jun-12..2026-Sep-05; CENTER/
   SITE_COORD/STEP/QUANTITIES match §3.1. PASS pending in-script continuity assert.
3. STAMP-PRECISION DEVIATION (declared now, pre-score): fresh stamps display
   "13:00" (minute precision); original raw displays "13:00:02.880" (FRACSEC
   display). The fresh header records the registered request time
   START_TIME='2026-06-12 13:00' — same 13:00 UT request convention; the
   displayed-minute stamp is CONSISTENT with (but does not verify) the
   .880-pattern instant. Worst-case sampling-instant offset 2.88 s; bounded
   value impact |ddelta| <= max|deldot| (0.48 km/s) x 2.88 s ~= 1.4 km.
   DECLARED DECISION RULE (before seeing any score): proceed and score; if
   EITHER gate (C1 or C2) lands within 2 km of its threshold, STOP, no
   verdict, escalate to human (the deviation could then be decisive).
   Otherwise the deviation is recorded as outcome-invariant. This is the
   only §3.2 guard component not literally verifiable from the fresh file.
4. v3 leakage-collapse implemented in frequency space: lines collapse iff
   |f_i - f_j| <= 1/292 cyc/d (single linkage; cluster attributed iff any
   member attributed) — the unambiguous Rayleigh-bandwidth reading, T=292
   as implemented in v2. Declared before the fine spectrum is seen.
5. R2/R3/R4 + non-gating diagnostics re-verified with the EXACT v2 rng
   stream (SeedSequence [20260612+4, ci], draw order cusum->tda->compression->mmd)
   so published values must reproduce byte-exactly; v3 seed base 20260613
   recorded but governs no stochastic stage (fine grid deterministic).

## Log
[done] 13:05 step 1: registrations + v2 json/doc/script read; raw + ledger hashes verified; original provenance compared -> pre-scoring adjudications 1-5 above
[done] 13:09 step 2: src/eq_tidal_v3.py written (imports v2 machinery verbatim) -> src/eq_tidal_v3.py
[done] 13:10 step 2b: src/eq_moondist_confirm1.py written (guards, freeze check, C1/C2/C3, tripwire) -> src/eq_moondist_confirm1.py
[done] 13:12 step 3: v3 run1 (4.3 s): refit byte-equal TRUE (B1+A2); coarse R1 reproduced byte-exact; R2/R3/R4+diags reproduce v2 byte-exact; claim B 20 coarse peaks -> 8 distinct refined lines, 5 unattributed -> outcome 2 -> results/_eq_tidal_v3_run1.json
[done] 13:13 step 3b: v3 run2 + finalize, cmp byte-identical -> results/_eq_tidal_v3_run2.json, results/eq_tidal_v3.json (sha256 efd521758eb5fa3c)
[done] 13:13 step 4: confirm1 run1 (0.7 s): ALL guards pass; freeze byte-equal TRUE; RMSE_fresh 5243.525413 km (C1 thr 6179.702309, margin +936.18) PASS; max|r| 9729.031155 km (C2 thr 12359.404618, margin +2630.37) PASS; C3 PASS; tripwire NOT tripped (margins >> 2 km; stamp deviation outcome-invariant) -> MECHANISM_SUPPORTED -> results/_eq_moondist_confirm1_run1.json
[done] 13:14 step 5: confirm1 run2 + finalize, cmp byte-identical -> results/_eq_moondist_confirm1_run2.json, results/eq_moondist_confirm1.json (sha256 7c36abea9fae21ec)
[done] 13:15 step 6: detail extraction for docs (fine-grid table, edge-pin flags, clusters, fresh diagnostics)
[done] 13:20 step 7: docs/RESULTS_EQ_TIDAL_V3.md + docs/RESULTS_EQ_MOONDIST_CONFIRM1.md written; ledger deltas PROPOSED (not applied)
