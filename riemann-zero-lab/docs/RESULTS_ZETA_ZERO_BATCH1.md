# Results — Zeta Zero Batch 1 (riemann-zero-lab)

Registration: `docs/REGISTRATION_ZETA_ZERO_BATCH1.md` (sha256 `a3a6e1dad3097f6d`, approved by
Cha 2026-06-13, pre-execution). Raw outputs (written by scripts only):
`results/zeta_zeros_batch1.json` (sha256 `f1b8990d08560b96`),
`results/zeta_zero_count_batch1.json`, `results/zeta_zero_spacing_batch1.json`,
`results/zeta_zero_verification_batch1.json`. Pipeline is deterministic (mpmath dps=80, no
RNG); two independent runs are byte-identical.

> **SCOPE BANNER (binding).** This batch is **numerical zero discovery + structure analysis.
> It does NOT prove, and presents NO evidence for the truth of, the Riemann Hypothesis.** RH
> concerns infinitely many zeros; this touches 200. See §3 and `kb/riemann-hypothesis.md`.

The three layers required by governance are kept in separate sections: **§1 numerical zero
discovery**, **§2 structure analysis**, **§3 proof-related limitations**.

---

## §1 — Numerical zero discovery (primary task: first 200 non-trivial zeros)

Method: Hardy Z-function sign-change bracketing over t > 0 (`src/hardy_z.py`,
`src/find_zeta_zeros.py`), each bracket refined by bisection + an Illinois bracketing solve
kept inside the bracket, residual checked via an independent `mpmath.zeta` code path, duplicate
guard at 10⁻⁶ separation. All 200 zeros located and verified at dps = 80.

| index | t (ordinate, 50 sig. digits shown truncated) | \|ζ(½+it)\| | stable dp |
|---|---|---|---|
| 1 | 14.134725141734693790457251983562470270784257115699 | 1.93e-49 | 57 |
| 2 | 21.022039638771554992628479593896902777334340524903 | 2.48e-49 | 57 |
| 3 | 25.010857580145688763213790992562821818659549672558 | 4.56e-51 | 57 |
| 4 | 30.424876125859513210311897530584091320181560023715 | 5.74e-49 | 57 |
| 5 | 32.935061587739189690662368964074903488812715603517 | 5.39e-50 | 57 |
| … | … | … | … |
| 200 | 396.38185422259218693199945449173052906376159968810 | 5.19e-48 | 57 |

Aggregate: residual \|ζ(½+it)\| ranges **2.67e-51 … 3.06e-47** (all far below the registered
10⁻³⁰ gate; the upper end is the height-scaled rounding floor of the 50-digit stored ordinate,
not a location error). Precision stability (independent re-solve at dps 50 vs 80) is
**56–60 matching decimals** per zero (gate ≥ 40).

### Validation requirements (all six, registration §Validation)

| # | Requirement | Result |
|---|---|---|
| 1 | Trivial zeros at s = −2,−4,…,−16 | **PASS** — \|ζ(−2k)\| = 0 to dps (`test_known_trivial_zeros`) |
| 2 | First non-trivial zero near ½ + 14.134725 i | **PASS** — 14.1347251417346937904572519835624… |
| 3 | First several ordinates match references | **PASS** — γ₁…γ₁₀ match published values ≥ 15 dp; match `mpmath.zetazero` ≥ 49 dp |
| 4 | Increasing precision does not move roots | **PASS** — 56–60 dp stable (dps 50 vs 80) |
| 5 | No duplicate / out-of-order roots | **PASS** — strictly increasing; min consecutive gap 0.498 (idx 186→187); guard unit-tested |
| 6 | Zero count cross-checked | **PASS** — located 200 = N(T) 200 = `mpmath.nzeros` 200; contour ∮ζ′/ζ = 4 over [0,31] = 4 located there |

### Zero-count certificate (validation #6, `argument_principle_check.py`)

Two counts independent of the sign-change search agree with the located count:
the Riemann–von Mangoldt analytic count N(T) = θ(T)/π + 1 + S(T) at T = 396.882 gives
**200.0**; `mpmath.nzeros(T)` (Turing/Gram-based) gives **200**; the contour argument
principle (1/2πi)∮ ζ′/ζ ds around the strip-rectangle [0,1]×[0.5,31] returns
**4.000000 − 4.1e-27 i → 4**, equal to the 4 located zeros below height 31. This certifies
**no zero is missed in that strip up to T₀ = 31, and none on the line up to T = 396.9** (to the
scan resolution) — a *finite verification*, explicitly not an RH statement (§3).

### Reproducibility & precision documentation

Two full runs produced byte-identical JSON (sha256 `f1b8990d08560b96`). Working precision
dps = 80; ordinates serialized to 50 significant digits (see erratum E2); residual gate 10⁻³⁰;
stability protocol dps 50 vs 80, ≥ 40 dp. All per-record settings in the JSON.

---

## §2 — Structure analysis (secondary task: zero-spacing vs GUE/Poisson)

**Status: DESCRIPTIVE / EXPLORATORY, not confirmatory** (N = 199 spacings, low height
t ≤ 396; the asymptotic random-matrix laws hold only approximately here — Article A4).
Method (`src/spacing_analysis.py`): unfold ordinates by w_n = θ(γ_n)/π + 1 (Riemann–von
Mangoldt smooth count), take nearest-neighbour spacings s_n = w_{n+1} − w_n, compare the
empirical distribution to the Poisson (no-repulsion null) and GUE Wigner-surmise baselines.

Unfolding check: mean spacing **0.998993** (≈ 1 as required), std 0.3638, min 0.3244,
max 1.9570. The empirical spacing histogram (bin width 0.25) is
`[0, 10, 48, 53, 39, 29, 13, 7, 0, …]` — **zero counts in [0, 0.25)**: strong small-gap
suppression (level repulsion).

| statistic | empirical | GUE (β=2) | Poisson |
|---|---|---|---|
| P(s < 0.5) | **0.0503** | 0.112 | 0.393 |
| KS distance D | — | **0.0711** (p≈0.26, indicative) | **0.3525** (p≈0.0) |

**Finding (descriptive):** the spacing distribution is **decisively inconsistent with Poisson**
(KS D = 0.35, p ≈ 0) and **consistent with GUE-like level repulsion** (KS D = 0.07,
p ≈ 0.26; no small gaps). This reproduces, on the first 200 zeros, the qualitative
Montgomery–Dyson picture (`kb/zeta-zero-spacing.md`, `kb/random-matrix-gue.md`). The empirical
small-gap fraction (0.050) is actually *below* the asymptotic GUE surmise (0.112) — an expected
small-N / low-height fluctuation, not a discrepancy to over-read. **No claim** of "confirms
GUE/Montgomery" is made from N = 199; the legitimate statement is "GUE-like repulsion, not
Poisson, at this resolution."

---

## §3 — Proof-related limitations (the hard boundary)

This module **does not prove the Riemann Hypothesis and provides no evidence that RH is true.**
Concretely:

1. **Finite vs infinite.** RH is a statement about infinitely many zeros. We verified 200. "All
   200 lie on the line and the count matches N(T)" is a *finite verification* (the same
   operational sense as the historical van de Lune / Odlyzko checks), **not** a proof and
   **not** statistical evidence about uncomputed zeros.
2. **The search is restricted to the line.** Zeros were located as real zeros of Z(t), i.e.
   *on* Re(s) = ½ by construction. Finding them there does not test Re = ½ versus
   Re = ½ ± 10⁻⁴⁰. Off-line exclusion in a strip requires the argument-principle **count** we
   ran (which certifies the *number* of zeros, including any off-line ones, equals the on-line
   count up to T₀ = 31) — a count, not a proof, and only up to a modest height.
3. **No RH-adjacent claim is promoted here.** Li-coefficient positivity, Nyman–Beurling,
   explicit-formula experiments, and Lean proof skeletons are **future, separately governed**
   batches (`kb/riemann-hypothesis.md`), not part of Batch 1.

---

## §4 — Independent verification record (role-ID separation)

Verification was performed by a **different executor instance than the author** of the finder
(`docs/AGENT_WORKFLOW.md` rule: verifier ≠ author). It happened in two passes and is the
batch's main process yield:

- **Pass 1 — FAIL (defect caught).** The independent verifier recomputed residuals and the
  `mpmath.zetazero` cross-check from scratch and reported FAIL: residuals up to 2.78e-27 (gate
  10⁻³⁰) and zetazero match only 29–30 decimals (gate ≥ 40). Root cause: the finder serialized
  ordinates to only **30** significant digits, while the acceptance gates require ~40–50 stored
  digits — the located zeros were correct to every stored digit, but the *record was not
  self-verifying*. The location-integrity signals (count, monotonicity, gaps, trivial zeros,
  spacing) all passed in Pass 1.
- **Fix.** `find_zeta_zeros.py` now serializes 50 significant digits and computes `zeta_abs`
  from the *stored* (rounded) ordinate, so every record reproduces its own residual (erratum
  E2). Pipeline re-run (byte-identical, sha256 `f1b8990d08560b96`).
- **Pass 2 — PASS.** Independent re-verification from scratch: max residual **3.06e-47**
  (0/200 fail), min zetazero match **49 dp** (0/200 below 40), internal consistency of stored
  `zeta_abs` confirmed on a 5-zero sample, count 200 = N(T) = `nzeros`, and the analyst's
  `verify_zeta_zeros.py` returns OVERALL PASS / exit 0.

The two-pass record is retained deliberately: it demonstrates the role-separated verifier
catching a real defect the author's own gates would have silently mis-reported had the residual
been computed from the in-memory root instead of the stored string.

---

## §5 — Registration deviations / errata (logged, not tuned away)

The approved registration (`a3a6e1dad3097f6d`) is left **byte-for-byte unmodified** (project
rule: the registered past stays honestly labelled). Two corrections are recorded here instead.

- **E1 — GUE P(s<0.5) reference constant.** The registration §Multiplicity prose states
  "Poisson ≈ 0.393 vs GUE ≈ 0.04". The **0.04 is wrong**: the GUE (β=2) Wigner-surmise CDF
  gives P(s<0.5) = **0.1120** (verified two ways — closed form
  F(s)=erf(2s/√π) − (4s/π)e^{−4s²/π} and direct quadrature of the surmise, agreeing to ~16
  digits; the surmise integrates to 1 with mean 1). The KB cards `random-matrix-gue.md` and
  `zeta-zero-spacing.md` have been corrected to 0.112; the registration is left as-is with this
  erratum. The substantive finding is unaffected (empirical 0.050 ≪ Poisson 0.393; KS still
  decisively favours GUE).
- **E2 — Ordinate serialization precision.** The registration's example record and validation
  gates were mutually inconsistent: 30-digit serialization (example-record style) cannot pass
  the ≥40-digit zetazero match or the residual-from-stored-value gate. Resolved by storing 50
  significant digits and computing the residual from the stored value (above, §4). The zero
  *locations* never changed; only their on-disk precision did.

---

## §6 — Adversarial review

Strongest objections considered, and their dispositions:

1. **"You only searched the line, so 'on the line' is circular."** Correct, and stated plainly
   (§3.2). The non-circular content is the *count*: N(T), `nzeros`, and the contour ∮ζ′/ζ
   independently agree that the number of zeros in the strip up to height T₀ equals the number
   found on the line there — so no zero hid off the line in that window. This is finite and
   modest-height; it is not RH (§3).
2. **"Hardy-Z sign-change scans miss close (Lehmer) pairs."** True in general. Mitigations:
   the running count is reconciled against N(T) (a missed pair would make located < N(T) — it
   does not), the unfolded min spacing is 0.324 (no near-collision in this range), and Lehmer-
   type near-degeneracies first appear far above height 396. For deeper batches the adaptive
   step + Turing's method must be exercised harder; flagged.
3. **"mpmath.zetazero is not truly independent — same library."** Partially fair: it shares
   mpmath's ζ implementation, but it is a *different algorithm* (its own isolation + refinement)
   than our Z-sign-change finder, and the residual check uses a third path (`mpmath.zeta`
   directly). Full independence would need a second library (e.g. an Odlyzko table or a
   FLINT/arb cross-check); flagged as a hardening step.
4. **"The spacing 'GUE not Poisson' result is over-claimed."** Guarded against: §2 is labelled
   descriptive/exploratory, the small-N and low-height biases are stated, KS p-values are
   marked indicative (consecutive spacings are weakly dependent), and no "confirms Montgomery"
   claim is made. The only firm statement is the robust one (Poisson decisively rejected).
5. **"Deterministic 'two-run' reproducibility is trivial."** Acknowledged — for a deterministic
   pipeline byte-identical output is necessary, not sufficient; the *cross-executor* check
   (independent verifier, §4) is the substantive one, and it caught a real defect.
6. **"Governance mismatch — the lab's MC-null premise (A1) doesn't fit deterministic math."**
   Acknowledged and now **formally reconciled**, not just flagged: registered as conflict
   **C11** and resolved by article **A8** (deterministic-certificate substitution) in
   `docs/THEOREM_GOVERNANCE.md`. Zero existence is admitted by a three-leg certificate (exact
   computation, independent recomputation, analytic invariant count = N(T) = contour integral);
   the MC-null machinery is confined to §2 (Poisson null), where A1–A7 bind unchanged. The
   deterministic-math eval slice (§7) confirmed the discipline transfers (3/3 PASS).

---

## §7 — Ledger / governance

Run ledger row appended to `results/run_ledger.jsonl` (module-local), linking registration →
scripts → output SHA → verifier identity. Governance checklist (registration §Governance) all
satisfied: cards-first, registration pre-execution, JSON-from-scripts, results-from-JSON,
independent verification, scope boundary honoured, adversarial review present.

**Methodology-change eval (CLAUDE.md rule) — RUN, 3/3 PASS.** This module extends the lab from
stochastic datasets to deterministic mathematics, materially changing the A1 null premise. Per
the project rule, a **deterministic-math eval slice was added and run** (Cha approved,
2026-06-13; `agents/evals/EVAL_SET.md` §Z; dispatch record + sealed truth
`results/agent_runs/zeta-eval-20260613/`, sha256 `c1c455c7737ee727`):
- **Z-V1** (verifier planted-discrepancy on a deterministic results doc) — PASS;
- **Z-V2** (self-verifying-record / under-precision gate — the exact E2 defect class) — PASS,
  the independent verifier REJECTED a 30-digit-truncated JSON for residual-from-stored > 1e-30
  and zetazero match < 40 digits;
- **Z-O1** (onboarder card-format gate on the Riemann–Siegel theta function) — PASS.

All graders were instances distinct from the finder author (role-ID separation), and integrity
checks confirm the real INDEX and planted files were untouched. The verification and onboarding
discipline therefore transfers cleanly to the deterministic-math module. No agent *definition*
files changed, so the existing V/D/A/O/R/E/Q/X agent suite was not re-triggered.

### Candidate ledger items (flagged for review, not promoted)

The clean GUE-vs-Poisson separation on only 200 low zeros, the exact N(T)=nzeros=contour count
agreement, and the self-verifying-record requirement (E2) are noted as durable artifacts; none
is promoted to a confirmation-family claim from this batch.
