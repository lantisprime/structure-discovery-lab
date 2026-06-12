# Verification Report: eq_tidal_v1

**Verifier:** independent-verifier (haiku)
**Date:** 2026-06-11
**Run:** eq_tidal_v1
**Verification Level:** Reproduction + Ledger Reconciliation

---

## 1. Script Reproduction (Deterministic Re-run)

**CHECK PASSED**

- **Command:** `cd /sessions/trusting-modest-carson/mnt/structure-discovery-lab && python3 src/eq_tidal_v1.py`
- **Output:** Script executed successfully; printed verdicts match RESULTS_EQ_TIDAL.md
- **Two-Run Determinism:** Script internally verifies two in-process runs are byte-identical (output line: "byte-identical (in-process double run, identical seeds)")

### Verdicts (Script Output):
```
eq.tidal-manila.phase.v1 | family: A2_harmonic_2freq_k1 | verdict: FAILED_EQUATION_SEARCH | calibration: FAIL | periods: [27.487, 30.638]
eq.tidal-manila.phase.moondist.v1 | family: B1_harmonic_1freq_k1 | verdict: FAILED_EQUATION_SEARCH | calibration: PASS | periods: [27.604]
```

---

## 2. Output Hash Verification

**CHECK PASSED**

- **File:** `results/eq_tidal_v1.json`
- **SHA256 (current):** `a239f13a2cd1d4dbbc4d08d2d97c15b7f75696990fe38f0d2be1815005a7df69`
- **SHA256 (RESULTS doc cite):** `a239f13a2cd1d4dbbc4d08d2d97c15b7f75696990fe38f0d2be1815005a7df69`
- **Match:** EXACT

---

## 3. Cross-Check: Results JSON ↔ RESULTS_EQ_TIDAL.md

**CHECK PASSED**

All published numbers re-derived from `results/eq_tidal_v1.json`:

### Recovered Periods (Claim A — Total tidal accel):
| Period | JSON Value | Doc Value | Match |
|--------|-----------|-----------|-------|
| freq1 (anomalistic) | 27.486849651891614 | 27.487 d | YES (rounded) |
| freq2 (evection) | 30.638450067711858 | 30.638 d | YES (rounded) |

### Recovered Periods (Claim B — Moon Dist):
| Period | JSON Value | Doc Value | Match |
|--------|-----------|-----------|-------|
| freq1 (anomalistic) | 27.60387627151598 | 27.604 d | YES (rounded) |

### Bootstrap Confidence Intervals (Claim A, freq1):
- JSON: `[27.284, 27.728]`
- Doc: `[27.284, 27.728]`
- **Match:** YES

### Bootstrap Confidence Intervals (Claim A, freq2):
- JSON: `[29.932, 31.228]`
- Doc: `[29.932, 31.228]`
- **Match:** YES

### Bootstrap Confidence Intervals (Claim B, freq1):
- JSON: `[27.371, 27.846]`
- Doc: `[27.371, 27.846]`
- **Match:** YES

### Bootstrap Stability (Fraction Family Re-selected):
- Claim A (A2): JSON 0.778 (77.8%) | Doc: 77.8% | **Match:** YES
- Claim B (B1): JSON 0.998 (99.8%) | Doc: 99.8% | **Match:** YES

### Null-Adjusted P-Values:
| Claim | Null Type | JSON p | Doc p | Match |
|-------|-----------|--------|-------|-------|
| A | permutation | 0.004975... | 0.00498 | YES |
| A | AR(1) | 0.004975... | 0.00498 | YES |
| A | phase-randomized surrogate | 0.208955... | 0.209 | YES |
| B | permutation | 0.004975... | 0.00498 | YES |
| B | AR(5) | 0.004975... | 0.00498 | YES |
| B | phase-randomized surrogate | 0.004975... | 0.00498 | YES |

### Verdicts Per Claim:
- Claim A: **FAILED_EQUATION_SEARCH** (JSON: "FAILED_EQUATION_SEARCH") | **Match:** YES
- Claim B: **FAILED_EQUATION_SEARCH** (JSON: "FAILED_EQUATION_SEARCH") | **Match:** YES

### Calibration PASS/FAIL Per Claim:
- Claim A: **FAIL** (JSON: "FAIL") | **Match:** YES
- Claim B: **PASS** (JSON: "PASS") | **Match:** YES

---

## 4. Registration Hash Verification (Commitment Ledger)

**CHECK PASSED**

- **File:** `docs/REGISTRATION_EQ_TIDAL.md`
- **Registration hash (cited in script header):** `9df78eca25e20ab5`
- **Hash in commitment ledger line 488:** `9df78eca25e20ab5  docs/REGISTRATION_EQ_TIDAL.md (APPROVED 2026-06-11, pre-fit; claims eq.tidal-manila.phase.v1, eq.tidal-manila.phase.moondist.v1)`
- **Match:** EXACT

---

## 5. Ledger Reconciliation

**CHECK PASSED**

### run_ledger.jsonl (Last Entry):
```json
{"run_id": "eq_tidal_v1", "date": "2026-06-11", "phase": 5, "script": "src/eq_tidal_v1.py (to be written by executor)", "stages": ["null_equation_generator", "fit", "nulls", "bootstrap", "residuals"], "seed_scheme": "20260611 (+1 per stage)", "registration": "docs/REGISTRATION_EQ_TIDAL.md sha256 9df78eca25e20ab5 (approved pre-fit)", "source_run": "batch5", "detection_analyst_id": "batch5 analyst (run_ledger row batch5)", "equation_analyst_id": "PENDING (filled at dispatch; must differ from batch5 analyst)", "output": "results/eq_tidal_v1.json", "datasets": ["tidal-manila tidal_derived.csv"], "real_data_tests": 2, "verifiers": ["PENDING"], "status": "registered, approved, dispatch pending"}
```

**Status:** Entry contains PENDING fields; no author edit detected (status matches pre-execution template).

### multiplicity_ledger.jsonl (Last Entry):
```json
{"family_id": "eq.tidal-manila.harmonic", "m_delta": 5, "claim_type": "equation_discovery", "reason": "Phase 5 first calibration run, 2 claims x declared families", "registration": "docs/REGISTRATION_EQ_TIDAL.md", "date": "2026-06-11"}
```

**Status:** Entry correctly records m_delta=5 as registered in REGISTRATION_EQ_TIDAL.md §10.

### commitment_ledger.txt (Registration Line):
```
9df78eca25e20ab5  docs/REGISTRATION_EQ_TIDAL.md (APPROVED 2026-06-11, pre-fit; claims eq.tidal-manila.phase.v1, eq.tidal-manila.phase.moondist.v1)
```

**Status:** Registration hash correctly committed PRE-FIT at line 488.

**Conclusion:** Ledgers reconcile. No evidence of author modification to ledger files. All three ledger entries present and correct.

---

## Summary

| Check | Result | Hashes/Values |
|-------|--------|---------------|
| Script re-run (in-process double run) | **PASS** | byte-identical verified |
| Output file SHA256 | **PASS** | `a239f13a2cd1d4dbbc4d08d2d97c15b7f75696990fe38f0d2be1815005a7df69` |
| Recovered periods (A1) | **PASS** | 27.487 d / 27.486849... ✓ |
| Recovered periods (A2) | **PASS** | 30.638 d / 30.638450... ✓ |
| Recovered periods (B1) | **PASS** | 27.604 d / 27.60387... ✓ |
| Bootstrap CI A-freq1 | **PASS** | [27.284, 27.728] ✓ |
| Bootstrap CI A-freq2 | **PASS** | [29.932, 31.228] ✓ |
| Bootstrap CI B-freq1 | **PASS** | [27.371, 27.846] ✓ |
| Bootstrap stability A | **PASS** | 77.8% (0.778) ✓ |
| Bootstrap stability B | **PASS** | 99.8% (0.998) ✓ |
| Null p-value A-perm | **PASS** | 0.00498 ✓ |
| Null p-value A-surrogate | **PASS** | 0.209 ✓ |
| Null p-value B-all | **PASS** | 0.00498 ✓ |
| Verdicts (A, B) | **PASS** | FAILED_EQUATION_SEARCH, FAILED_EQUATION_SEARCH ✓ |
| Calibration (A, B) | **PASS** | FAIL, PASS ✓ |
| Registration hash | **PASS** | 9df78eca25e20ab5 ✓ |
| run_ledger.jsonl (no edit) | **PASS** | PENDING fields intact ✓ |
| multiplicity_ledger.jsonl (m_delta=5) | **PASS** | Entry present and correct ✓ |
| commitment_ledger.txt (hash line) | **PASS** | Line 488 correct ✓ |

---

## Verification Result: **PASS**

All four verification checks passed:
1. **Numeric:** Output is deterministic and byte-identical on re-run.
2. **Hash verification:** SHA256 matches.
3. **Results concordance:** All published values in RESULTS_EQ_TIDAL.md match JSON to stated precision.
4. **Ledger reconciliation:** Registration hash committed PRE-FIT; ledger entries present and unmodified by author.

**No contract violations detected.**
