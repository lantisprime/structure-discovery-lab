# Remediation Log — Fixes for ADVERSARIAL_REVIEW Findings (Critical + Major)

**Date**: 2026-06-11 · **Scripts**: `src/remediation_r1.py`, `src/meta_uniformity.py`,
independent agent outputs in `results/independent_verification.json` ·
**Raw outputs**: `results/remediation_r1.json`, `results/meta_uniformity.json`,
`results/gw_symmetric_gate_pilot.json` · **Figure**: `fig9_meta_uniformity.png`.

## Protocol change first (the bias fix, lab-owner directive)

**Registrations no longer declare outcome expectations for discovery tests.**
A registration now contains: claim type, representation, instrument, null,
decision rule, and falsification criteria — never a predicted result.
Mechanism-based predictions survive only as *instrument-validity controls*
(e.g. "if the pipeline cannot detect the tidal loop, the pipeline is broken"),
which calibrate tools, not outcomes. Codified in `RELATIONAL_RUNBOOK.md`
Phase 1 (amended). Every test in this remediation batch ran expectation-free.

| Finding | Status | What was done | Outcome |
|---|---|---|---|
| **C1** registration unverifiable | **FIXED (forward)** | git repo initialized; baseline commit `e1bc32b` explicitly marks all prior "registered" labels as retroactive/unverifiable; rule added: registration committed before its run script exists | enforced from now on; the past stays honestly labeled |
| **C2** role concentration | **FIXED (this round)** | independent agent, own code, forbidden from lab code/docs/key, given **blinded** standardized series (9 series, neutral names, no dates) | **9/9 concordance**: all 4 physical series STRUCTURED, all 5 lotto series NO DETECTED STRUCTURE — with zero expectations. Numerical replication: half-corr 0.251/0.154 matches published to 3 decimals |
| **C3** presence-test claim mismatch | **FIXED** | re-specified as R7 matrix completion: skill over column-marginal baseline vs permuted-within-column null, m=29 | all 5 games null (min p=0.467 vs Šidák 0.0102); old test relabeled a frequency-bias test joining the chi-square family |
| **M1** tuned-to-pass power | **FIXED** | frozen-instrument power curves over pre-declared effect grids | detection floors now public: R1 MMD power 0.20@shift0.25→1.00@1.0; R4 TDA dies at circle-noise 0.5 (0.10); R5 spectra 0.08@p_in=0.10→1.00@0.30; R2 GW 0.95@noise0.1→0.15@0.5; R7 1.00 across grid; R3 1.00 across grid; R6 0.92→0.32 |
| **M2** powerless gates | **FIXED — and it caught something** | both shape gates rerun at n=200 | quarter-shape gate genuinely passes (FPR 0.035, KS p=0.20). **GW gate FAILS**: FPR@0.05 fine (0.055) but p-distribution non-uniform (lattice χ² p=0.002); symmetric-null variant also fails (p=0.005) → moment-matched regeneration nulls for GW are inherently miscalibrated in distribution. **GW demoted to exploratory-only** pending null redesign (A4: the flag stands). No published verdict relied on GW alone |
| **M3** floor violations | **FIXED** | per-game λ_max rerun at m=399 (floor 0.0025); GW pairs at m=99; floor rule added to runbook (floor ≤ threshold/2) | resolvable results: 6/55 p=0.0025 (known #45 shadow — **survives** removing suspicious rows, p=0.0025) and **6/45 p=0.0100 — at the Šidák threshold 0.0102, a new corrected exploratory flag** (see below). GW pairs: tidal\|moon p=0.010, pressure\|lotto p=0.280, pressure\|tidal p=1.0 (now exploratory per M2) |
| **M4** data quality unexamined | **PARTIALLY FIXED** | three-regime sensitivity (all / ex-suspicious / verified-only) for half-corr ×5 games + 6/55 λ_max; independent agent replicated | 6/55 half-corr signal drops 0.251→0.154 (p 0.05→0.11) without the 3 suspicious rows, **but** the 6/55 λ_max co-occurrence flag survives (p=0.0025) — the #45 shadow is not purely a data artifact. Verified-only regimes (n≈21–24 for most games) are too small to interpret (two raw p<0.05 at those n are noise-prone; power statement applies). **PENDING**: adjudication of the 3 rows against PCSO official records (needs external source access) |
| **M5** correlated repeats as power | **FIXED** | docs relabeled: per-seed rates are *seed-stability diagnostics*, not power | language corrected in RESULTS_BATCH5/FIRSTRUN |
| **M6** no global ledger | **FIXED** | `src/meta_uniformity.py` panel, now part of the output contract | **126 lotto-side real-data p-values: KS vs uniform p=0.385, 6.3% ≤0.05, 0.8% ≤0.01 (refreshed after m=999 reruns)** — globally consistent with honest null testing (fig9) |
| **M7** single-split CCA | **FIXED** | 3 split points (50/60/70%), all games, full covariate bundle | medians across splits: all games null (per-split excursions p=0.04–0.10 appear and vanish across splits — demonstrating exactly the split-noise the finding warned about) |

## The 6/45 flag — opened at m=399, closed at m=999 (reported expectation-free)

At m=399 the 6/45 co-occurrence λ_max landed exactly at the corrected threshold
(p=0.0100 vs 0.0102). The design verifier (built later this session) flagged
that family pooling pushed the required floor below m=399's resolution, forcing
a rerun at m=999 — where the estimate settled at **p=0.0150, above the
threshold**. The two estimates are statistically compatible; the higher-
resolution one governs. Disposition: **exploratory watch only — the corrected
flag did not survive**. (Loadings remain diffuse: #4 0.351, #24 0.314,
#27 0.309.) By contrast 6/55 hardened at m=999 to **p=0.0010** (and p=0.0025
ex-suspicious at m=399) — the #45 co-occurrence shadow is resolution-stable and
not a data-quality artifact. Corrected rejections in the λ_max family: **1**
(6/55, the known anomaly). This sequence — flag opened by a borderline
estimate, closed by the floor rule it triggered — is retained as the worked
example of why the floor rule exists.

## Verdict-impact summary

No published verdict flips. Three claims gained strength (blind 9/9
replication; quarter-gate now genuinely calibrated; presence null now under the
correct claim type). Two claims weakened honestly (GW results demoted to
exploratory; 6/55 half-corr partially attributable to suspicious rows). One
new exploratory flag opened (6/45 λ_max) under the expectation-free protocol.
