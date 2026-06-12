# RESULTS — eq.tidal-manila.phase.moondist.v3 (R1 fine-grid re-adjudication)

Registration: `docs/REGISTRATION_EQ_TIDAL_V3.md`, sha256
`4fc27d0e621d425003b15d47712390a4fd4e90b782f6470b21bcebd836b6a11c` (verified
against `results/commitment_ledger.txt`; APPROVED 2026-06-12 pre-execution;
amendments honored: §8(a) +1 charge stands, §8(b) claim A's 36.625 d peak in
scope at +0). Script: `src/eq_tidal_v3.py` (imports `src/eq_tidal_v2.py`
verbatim — coarse detector and refit path byte-identical by construction).
Machine output: `results/eq_tidal_v3.json` (sha256 `efd521758eb5fa3c…`).
Executed 2026-06-12 by equation-analyst (v3 execute dispatch; ≠ batch5
detection analyst, ≠ v2 same-claim verifier). Seed base 20260613 (no
stochastic stage exercised; see Reproducibility).

## Headline

| Claim | Question | Result | Verdict |
|---|---|---|---|
| B `eq.tidal-manila.phase.moondist.v3` | does the v2 unattributed residual ladder dissolve on a 16× fine grid under the leakage-collapse rule? | **NO — partially.** 20 coarse peaks collapse to **8 distinct refined lines**, but **5 remain unattributed** | **FAILED_EQUATION_SEARCH** — §6 **outcome 2** (R1 FAIL stands **and** R3 fails: attribution "R1 + R3") |
| A (diagnostic, +0) | does claim A's 36.625 d peak attribute under the same rule? | **NO.** It refines to an **interior (non-edge) line at 36.341 d**, absorbs the coarse 32.556 d ordinate, and stays unattributed | no verdict (diagnostic only; claim A's R2/R4 remain failed) |

**The leakage hypothesis, as operationalized by the registered rule, is DEAD
and logged as such** (CLAUDE.md: dead ends are results). Per §6 outcome 2 the
unattributed refined lines below are published as a discovery-grade anomaly in
ephemeris-derived data, and **execution of any v4 is gated on human review** —
the most plausible reading remains an error in our derivation/whitelist, not
new physics. Registered binding fact honored: R3 (0.886 > 0.562) pins the
verdict at FAILED_EQUATION_SEARCH on every branch; this run adjudicated WHICH
failure, and the answer is R1+R3, not R3 alone. Hard rule 1: batch5 STRUCTURED
detection verdict untouched. Doob separation: no action license.

## Frozen-refit byte-check (uncharged, §2)

| Claim | Family | Byte-equal to v2 JSON | Matches registration §2 constants |
|---|---|---|---|
| B | B1 | **TRUE** (freqs, coef, periods) | **TRUE** (a0 385294.7950098205, a −19039.87882118035, b 11488.61399772309, P 27.60387627151598) |
| A | A2 | **TRUE** | n/a |

Coarse R1 detector output reproduced the v2 published peak lists
**byte-exactly** for both claims (20 peaks B, 7 peaks A) before any v3 step ran.

## Claim B — per-peak fine-grid attribution table (§4 steps 2–3)

16× zero-padded grid (Δf = 1/4688 cyc/d); refinement window ±1 natural bin
(±1/293 cyc/d) ∩ [4, 120] d; attribution on refined period, Rayleigh
ΔP = P²/292 (no merge for claim B, as registered). "edge" = refined location
pinned at the window boundary (instrument note below).

| Coarse P (d) | Refined P (d) | Edge-pinned | Attributed (refined) | Match |
|---|---|---|---|---|
| 29.300 | 30.842 | — | YES | evection |
| 32.556 | 30.842 | — | YES | evection |
| 14.650 | 14.742 | — | YES | variation |
| 26.636 | 29.300 | lo | YES | evection |
| 24.417 | 26.636 | lo | YES | synodic |
| 36.625 | 32.556 | hi | YES | evection |
| 41.857 | 36.625 | hi | no | — |
| 22.538 | 24.165 | — | no | — |
| 48.833 | 42.234 | hi | no | — |
| 15.421 | 14.742 | — | YES | variation |
| 58.600 | 48.833 | hi | no | — |
| 73.250 | 58.600 | hi | no | — |
| 20.929 | 22.218 | — | no | — |
| 97.667 | 73.250 | hi | no | — |
| 13.318 | 13.206 | — | YES | anomalistic_2nd_harmonic |
| 19.533 | 20.652 | — | no | — |
| 13.952 | 14.650 | lo | YES | variation |
| 18.313 | 19.292 | — | no | — |
| 16.278 | 15.946 | — | no | — |
| 17.235 | 16.924 | — | no | — |

### Distinct refined lines after leakage collapse (|f_i−f_j| ≤ 1/292, single-linkage)

| Line (representative, d) | Members (coarse, d) | Attributed | Match |
|---|---|---|---|
| 30.842 | 29.30, 32.56, 26.64, 24.42, 36.62, 41.86 | **YES** | evection, synodic |
| 14.742 | 14.65, 15.42, 13.95 | **YES** | variation |
| 13.206 | 13.32 | **YES** | anomalistic_2nd_harmonic |
| **24.165** | 22.54 | **NO** | — |
| **22.218** | 20.93, 19.53, 18.31 | **NO** | — |
| **42.234** | 48.83, 58.60, 73.25, 97.67 | **NO** | — |
| **15.946** | 16.28 | **NO** | — |
| **16.924** | 17.24 | **NO** | — |

R1 v3: 8 distinct lines, 5 unattributed → **FAIL stands** (§6 outcome 2).

The collapse rule DID do real work: the v2 "ladder" of 13 unattributed coarse
ordinates is not 13 constituents — six ordinates (24.42–41.86 d) are one
attributed evection/synodic complex, and the entire long-period arm
(48.8–97.7 d) is a single feature. But that feature (42.2 d) and four shorter
lines (24.2, 22.2, 15.9, 16.9 d) sit > 1 Rayleigh bandwidth from every
whitelist period, so the FAIL is genuine under the registered instrument.

## Claim A diagnostic (approver amendment, +0)

7 coarse peaks → 3 distinct refined lines: 14.650 d (variation, attributed),
30.842 d (evection, attributed), and **36.341 d — unattributed**, absorbing
both the 36.625 d mystery peak AND the coarse 32.556 d ordinate (which v2 had
attributed to evection at coarse resolution). The 36.341 d refined location is
an **interior fine-grid maximum, not edge-pinned** — the strongest evidence yet
that this is a real off-grid line, present in BOTH targets (claim B's coarse
36.625 ordinate refines toward the same region but is chain-absorbed into the
attributed evection complex). Claim A's verdict is unchanged (R2/R4 remain
failed; this was symmetric diagnostics, not a new chance).

## R2/R3/R4 + diagnostics re-verification (claim B; exact v2 rng stream)

| Check | Value | v2 byte-equal | Pass |
|---|---|---|---|
| R2 CUSUM (gating) | stat 0.9297, p 0.3781 | **TRUE** | PASS |
| R3 TDA H₁ absorption (gating) | persistence 0.8856 > 0.562 (absorption 21.2%) | **TRUE** | **FAIL** |
| R4 compression (diagnostic for B) | 296 bytes, p 0.00498 | **TRUE** | (n/a) |
| Ljung–Box / MMD / Breusch–Pagan (non-gating) | Q 3768.76 p≈0 / 0.0214 p 0.0199 / LM 12.53 p 0.0004 | **TRUE** | — |

Claim A's table likewise reproduced byte-exactly (all `byte_equal_v2` TRUE in
the JSON).

## What was learned (logged, not dismissed)

1. **Leakage hypothesis dead as registered, but it was half right:** the
   ladder is not 13 constituents. Collapse + refinement reduce it to 5
   distinct unattributed lines (24.2, 22.2, 42.2, 15.9, 16.9 d). The v2
   learning-3 text stands; this sharpens it.
2. **Instrument note (for any future registration, NOT applied here):** 9 of
   20 claim-B refined locations are pinned at the ±1-bin window edge, each
   pointing one bin toward the dominant 30.8 d feature — the classic signature
   of leakage whose true source lies BEYOND ±1 bin. The registered window
   cannot chase it (anti-tuning guard: 16×, ±1 bin fixed). A v4 wanting to
   adjudicate the 42.2 d arm needs either explicit modeling of the whitelist
   inequalities before the scan, or a registered multi-bin/CLEAN-style
   relocation rule. New registration + new m charge required; human review
   gates any v4 per §6 outcome 2.
3. **The 36.34 d line is the cleanest anomaly:** interior (non-edge) fine-grid
   maximum, present in both targets, > 1 Rayleigh bandwidth from every
   whitelist period. Candidate explanations for human review: a missing lunar
   inequality in our 4-line whitelist (e.g. lines near 1/(1/27.555 − 1/31.812)
   ≈ 36.6 d-scale beat terms of anomalistic×evection), or a derivation
   artifact in `tidal_derived.csv`. Not adjudicated here.
4. **Multiplicity:** m_delta = +1 as registered (§8(a) rejected by approver);
   claim A diagnostic +0. Cumulative family charge eq.tidal-manila.harmonic:
   8 + 1 = 9 — orchestrator applies.

## Reproducibility

- Two-run rule: two separate full process executions
  (`results/_eq_tidal_v3_run{1,2}.json`); `cmp` empty — **byte-identical**;
  `two_run_diff` recorded in the JSON. Final sha256
  `efd521758eb5fa3c78bca7767766516885fed4a2aa3c96fd3dca1c7a07d53022`.
- Seed note (declared pre-execution in the checkpoint): the v3 procedure is
  fully deterministic; R2/R3/R4 + diagnostics were re-verified under the EXACT
  v2 rng stream (base 20260612, residuals offset +4) because the goal is
  byte-verification of published values. v3 seed base 20260613 is recorded in
  the JSON and governs no draw.
- Declared implementation decisions (pre-execution, checkpoint §4–5): collapse
  rule in frequency space (|Δf| ≤ 1/292, single-linkage, cluster attributed
  iff any member attributes); fine window intersected with [4, 120] d.

## Proposed ledger deltas (PROPOSED — not applied; orchestrator to apply)

1. run_ledger `eq_tidal_v3`: status → executed; output sha256
   `efd521758eb5fa3c`; predecessor eq_tidal_v2; independence as recorded.
2. multiplicity_ledger: `{family_id: "eq.tidal-manila.harmonic", m_delta: 1,
   reason: "Phase 5 v3: claim-B R1 re-adjudication on declared fine omega-grid"}`.
3. Instrument note appended to v2 learnings (original text preserved):
   learning 3's ladder is 5 distinct lines after declared collapse, not ~13;
   leakage hypothesis as operationalized: dead.
4. Independent-verifier task: re-derive the 8-cluster partition and the five
   unattributed refined periods; check the claim-A 36.341 d interior maximum.
