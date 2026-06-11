# Adversarial Review — The Relational Program (Batches 5–7 + First Run)

**Date**: 2026-06-11 · **Reviewer**: the same agent that built the program
(itself Finding C2) · **Method**: attack each published claim's registration,
design, execution, and verification; run new checks where words alone cannot
settle the question. New evidence produced for this review:
`results/sensitivity_655_suspicious.json` and the meta-uniformity check (§Bias).

---

## CRITICAL findings

### C1 — Registration has no commitment device
Every "registered before execution" claim rests on same-session file-write
ordering by the same agent that then ran the experiments. There is no hash, no
commit, no independent custody, no timestamping beyond file mtimes. The batch-5
"all-games amendment declared before any result was viewed" is *unverifiable*
— and the agent had already seen 6/55 results from the first run, which
informed the amendment's expectations. **Impact**: the A6/A7 guarantees are
procedural claims, not enforced properties. **Remediation**: git-commit every
registration before the run script exists; better, have a second system hold
the registration hash.

### C2 — Total role concentration
One agent played onboarder, analyst, editor, *and* verifier — the exact
configuration AGENT_WORKFLOW exists to prevent. The verification script checks
that documents transcribe JSONs faithfully; it cannot catch wrong nulls, wrong
claim types, or leakage, because its author shares every blind spot with the
experiment author. The one design bug it caught (B7-1 permutation floor) was
luck: the design error happened to surface as a transcription mismatch.
**Remediation**: external review (see `EXTERNAL_REVIEW_BRIEF.md`); independent
re-implementation of at least one positive and one null result.

### C3 — Claim-type mismatch in the presence-recovery test
`presence_point` regenerates the *entire dataset* from the uniform generator as
its null. That tests "are the draws uniform?" (goodness-of-fit), not "does a
subset predict the held-out remainder better than the marginal?"
(subset-to-whole, §1.2). A stable year-long bias would appear as "recovery
skill" — which is exactly why the #45 games showed mildly positive z. The
published verdict (null) stands, but under the wrong claim label; framework
§1.2 calls this conflation the primary source of manufactured relationships.
**Remediation**: re-specify with the marginal-baseline + permuted-H null the
framework's own table demands; relabel the existing result as a uniformity
test that joins the chi-square family (it is a function of hit counts — C3/C9
duties apply, which the mild #45 z confirms).

---

## MAJOR findings

### M1 — Admission power is tuned-to-pass
R1's gating effect size was raised (0.5→1.0) after observing power 0.60; R5's
statistic was replaced (full spectrum → bottom-12) and its planted contrast
strengthened (0.15/0.03 → 0.30/0.02) after power 0.125. All documented, all on
synthetic data — but the consequence is that the seven "power 1.00" rows are
**tautological**: instruments were adjusted until the positive control passed.
The credible half of admission is the untuned FPR calibration. **Remediation**:
report admission power as a *curve over effect sizes fixed in advance*, with
the instrument frozen first.

### M2 — Shape gates have almost no power
n=40 trials ⇒ the "FPR within 3·SE" band spans ±0.103: a truly miscalibrated
instrument with FPR 0.14 passes. The batch-6 gate "passed" with observed FPR
0.15. The GW gate used n=20. These gates can detect catastrophe, not
miscalibration. **Remediation**: ≥200 trials per gate (cost was a sandbox
timeout constraint, never a statistical choice — see m2).

### M3 — Conclusions resting on permutation floors
B7-1's original m=99 made the corrected rejection *mathematically unreachable*
(floor 0.01 > Šidák 0.0085) — caught and rerun, but the same tension exists
elsewhere: batch-5 per-game λ_max (floor 0.01 vs threshold 0.0102, resolvable
by 0.0002), and the GW positive control whose entire verdict is "p = 0.05 at
m=19," i.e. the observed value merely beat 19 nulls. **Remediation**: rule —
m must satisfy floor ≤ threshold/2 before a run is admissible.

### M4 — Data quality ignored: 576/776 rows single-source, 3 suspicious rows used everywhere — and it matters
Every batch consumed `data_draws_1yr_audited.csv` unfiltered. The 3
`suspicious_or_needs_review` rows (archive conflicts) are all 6/55, all in the
2025 #45 era. **New sensitivity run for this review**: excluding just those 3
rows drops the 6/55 half-vs-half hot-number correlation from **0.251
(p=0.035) to 0.154 (p=0.11)** — a large fraction of the residual #45 shadow in
batch 6 may be data-quality artifact, not machine behavior. No batch performed
this sensitivity check before publishing. **Remediation**: all hit-count
statistics rerun under {all rows / verified-only / ex-suspicious} as standard
output; adjudicate the 3 rows against PCSO official records.

### M5 — Correlated repeats presented as rejection rates
Recovery-curve "rej = 10/10" aggregates 10 subset draws of the *same* observed
dataset — they share the data and are not independent trials; the number reads
like power but is closer to a stability diagnostic. **Remediation**: relabel as
seed-stability; power claims only from synthetic replicates.

### M6 — No global multiplicity ledger
~95 lotto-side real-data tests were published with only within-run Šidák
corrections; A3 demands a global class-level m. Run for this review: the
pooled distribution of all 95 lotto-side p-values gives **KS-vs-uniform
p = 0.070, fraction ≤ 0.05 = 0.063** — globally consistent with the null, with
the mild low-p excess concentrated in the already-adjudicated #45 shadow
family. This check should have been in every batch. **Remediation**: add the
meta-uniformity panel to the standard output contract; update the lab's m
registry with the relational classes.

### M7 — Single-split CCA
All held-out CCA verdicts use one time-ordered 60/40 split. p=0.17 vs p=0.03
differences between games are within split-choice noise. **Remediation**:
blocked time-series cross-validation or at minimum 3 split points.

---

## MINOR findings

- **m1**: the verification script's later sections reset `ok`, so the exit
  code reflected only the final section. *Fixed during this review.*
- **m2**: nearly every statistical parameter (m, trials, repeats, GW subsample
  120, SoftImpute iterations) was set by the 45-second sandbox timeout, not by
  power analysis — never disclosed as such until now.
- **m3**: the GW pressure↔tidal "anti-similar" narrative is post-hoc; the
  matched-Gaussian null conflates "different shapes" with "second cloud more
  Gaussian-like." Registered as exploratory, narrated like a finding.
- **m4**: the pressure dataset's provenance is a user-uploaded file accepted
  without checksum or fetch log; grid-cell coordinates differ from the
  registered request (UI default vs API coords); single-source ERA5.
- **m5**: A5 era-gating noted but not enforced — 6/55 tests pooled across the
  declared Feb-2026 era boundary.
- **m6**: rng streams shared between subset selection and null generation;
  admission JSON merges runs from two code versions (documented seeds make it
  reproducible, but fragile).

---

## The bias question (raised by the lab owner, examined both ways)

**Could the process be biased toward null results on the lotto?** Three
mechanisms are real:

1. *Registration asymmetry* — every lotto expectation was registered as
   "null," inherited from prior lab verdicts. Expectations shape design.
2. *Power allocation* — the chosen instruments (temporal k-NN, delay-embedding
   topology, seasonal MMD) are physics-shaped; they have demonstrated power
   against gross, mechanism-like structure only. The admission effects are
   large; a subtle bias (e.g. 0.1% per-number) is far below detection at
   n≈155 and **no test run here could have seen it**. The nulls are honest at
   their resolution but the resolution was never headlined.
3. *Theory anchoring* — "Doob says no edge" (C8) predisposes the analyst to
   accept nulls quickly and stress-test positives slowly.

**Against the bias hypothesis**: the same pipeline, same day, detected every
known-mechanism structure it touched (tidal loop p=0.01, seasons 6/6 corrected,
sun/moon ρ₁=0.567/0.9977, tidal↔moon GW); the #45 anomaly was surfaced and
traced *four times* rather than buried; the pooled p-distribution (KS p=0.070,
6.3% ≤ 0.05) is what an unbiased procedure run on null data produces; and this
review itself just *weakened* an anomaly (M4) — the direction a pro-null bias
would resist. **Verdict**: no evidence of evidence-handling bias; a real
structural tilt in power allocation and registration asymmetry, with the
remediations above (power-matched designs, adversarial registrations that
specify what *would* falsify the null, external review).

## What survives this review

The headline conclusions stand — with sharper caveats: (a) no relational
structure in the lotto **at the tested resolutions** (gross effects excluded;
subtle effects untested and largely untestable at n≈155); (b) positive
controls confirm the instruments detect mechanism-scale structure; (c) the #45
excess remains exactly one era-bounded anomaly, now *more* likely to be partly
data-artifact than machine behavior (M4). The decision-layer verdict (no edge,
no stake) is unchanged and was never in danger — it rests on Doob and the
entropy floor, not on any single batch.

## Remediation queue (priority order)

1. Git-commit registrations before runs (C1); external review (C2 →
   `EXTERNAL_REVIEW_BRIEF.md`).
2. Adjudicate the 3 suspicious 6/55 rows; rerun all hit-count statistics in
   the three data regimes (M4).
3. Re-specify the presence test with the correct subset-to-whole null (C3).
4. Floor rule m ≥ 2/threshold (M3); gate sizes ≥200 (M2).
5. Frozen-instrument power curves (M1); CV for CCA (M7); meta-uniformity panel
   in every batch (M6); relabel stability numbers (M5).
