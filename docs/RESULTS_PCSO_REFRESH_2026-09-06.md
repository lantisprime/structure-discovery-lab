# RESULTS — PCSO refresh 2026-09-06: official data, monitoring, conscious-selection instrument, strategy backtest

Grade: **G0 exploratory** throughout (no REGISTRATION_*.md was opened; nothing here enters the
confirmation family). **Revision r2 (same day):** an independent read-only mathematical review by
Codex gpt-6-astra (`results/codex_review_2026-09-06.md`) was applied in full — see §3, §4 and §8;
the superseded first-pass values are kept in the ledger with `superseded_by`. Executor: Claude Fable 5.1 session (author of the three scripts); verification:
two-run byte-identical for every output, cross-model execute-only re-run recorded in
`results/verification_pcso_refresh_2026-09-06.md`. Commitment snapshot before execution:
`results/commitment_ledger.txt` digest `83b4bcdc3df1ad58…` (pre-run); a closeout snapshot follows.

## 1. Data refresh (Part 4 D3/D4/D8)

| Item | Value |
|---|---|
| New draws appended | 128 (2026-07-08 … 2026-09-05; 6/42 26 · 6/45 26 · 6/49 25 · 6/55 26 · 6/58 25) |
| Primary source | **pcso.gov.ph** `SearchLottoResult.aspx` date-range search, per game, raw HTML retained (`datasets/pcso-lotto/provenance/raw_2026-09-06/`, 22 gzipped captures) |
| Cross-checks | lottopcso.com 128/128 agree; pcsodraw.com 100/100 agree (its 20-draw window); draw-number continuity consistent for all five games across the 28 draws pcsodraw does not cover |
| Conflicts | 0 |
| Full-year official re-verification | all **834** rows previously on file re-fetched from the official page: **834 exact matches (exit order included), 0 mismatches, 0 missing** — including the three `suspicious_or_needs_review` 6/55 rows (M4) |
| Canonical rows now | `data_draws_1yr.csv` 962 · `data_draws.csv` 380 · audited 962 (`official_verified` for the new rows) · astro 380 dated rows (PyEphem 4.2.1; generator parity 54/58 exact, 4 rows differ by 0.001 in Moon Illum — the §10 rounding artifact) |
| New file | `data_official_draws_jackpots.csv` — 984 official draws (Jun 1 2025 … Sep 5 2026) with jackpot (PHP) and number of winning bets: the payout-layer input |
| Manifest | `datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json` (`expected_new_draws` 128, per-draw sources, jackpot, winners, continuity) |
| Not done | the Excel workbook was not extended (its invariants are verified unchanged); Kp backfill still open, so the registered Kp test stays non-computable |

## 2. Registered m=9 monitoring family on the confirmation set (n=186 draws after 2026-06-10)

Script `src/pcso_monitoring_run.py` (validators and family imported from the July closeout module),
seed 20260906, MC 10,000 / permutations 20,000, Bonferroni threshold 0.05/9 = 0.005556.
Output `results/pcso_confirmation_2026-09-06.json` (two-run SHA-256 `baff97e8ed93d8e7…`).

| Test | n | statistic | p | flag |
|---|---|---|---|---|
| chi-square MC, Lotto 6/42 | 38 | χ²=48.68 | 0.0662 | no |
| chi-square MC, Mega 6/45 | 37 | χ²=38.68 | 0.4981 | no |
| chi-square MC, Super 6/49 | 37 | χ²=58.76 | 0.0457 | no |
| chi-square MC, Grand 6/55 | 37 | χ²=51.51 | 0.3758 | no |
| chi-square MC, Ultra 6/58 | 37 | χ²=64.34 | 0.1069 | no |
| mean-drawn vs moon altitude (perm.) | 186 | r=−0.015 | 0.833 | no |
| mean-drawn vs moon illumination (perm.) | 186 | r=+0.005 | 0.950 | no |
| mean-drawn vs Kp | — | not computable (Kp blank) | — | — |
| 6/55 ball #45 binomial | 37 | 2 hits vs 4.04 expected | 0.427 | no |

**Verdict: 0 flags; minimum p = 0.046 > 0.0056.** The 2025 #45 excess remains dead (2 hits in 37
post-freeze 6/55 draws). Repeated-look caveat unchanged: weekly cumulative looks are G0 monitoring
without a sequential alpha-spending rule.

## 3. Strategy backtest — does any selection rule change P(match)? (family `strategy-backtest`, m=7)

Script `src/pcso_strategy_backtest.py`, 834 draws after a 30-draw warm-up, 2 tickets per play,
300 replicates per draw for the three pickers (100 for the "prediction" rules), seed 20260906.
Unit of independence = the draw (replicate tickets scored on one draw are correlated through it);
statistic = D_t = Σᵢ a_{t,i} X_{t,i}, the per-draw difference in mean matches per ticket versus the
uniform-disjoint baseline on the **same** draws, with a = q_s − q₀ the difference in ticket inclusion
fractions. **Null (r2, codex review §6):** conditional on the generated tickets, uniform draws give
E[D_t]=0 and Var₀(D_t) = 6(P−6)/(P(P−1))·Σᵢ a²_{t,i}; calibration regenerates the 834 draws uniformly
9,999 times with the tickets held fixed (add-one MC p, floor 1e-4). The sign-flip null of the first
pass was withdrawn (E[D_t]=0 does not imply sign symmetry). Multiplicity: **Holm** over the 7 rules.
Output `results/pcso_strategy_backtest_2026-09-06.json` (SHA-256 `67ddd1d039711995…`).

| Strategy | mean matches/ticket (H₀ 0.7333) | Δ vs uniform, same draws | conditional-null z | MC p | Holm p |
|---|---|---|---|---|---|
| uniform disjoint pair (baseline) | 0.7320 | — | — | — | — |
| picker v1 (four pattern filters, the previous web page) | 0.7360 | +0.0040 | +2.66 | 0.0078 | 0.055 |
| picker v2 (CSI-filtered) | 0.7401 | +0.0081 | +2.46 | 0.0134 | 0.067 |
| hot top-6 (trailing 50 draws) | 0.7440 | +0.0120 | +0.74 | 0.46 | 1 |
| cold bottom-6 (trailing 50) | 0.6912 | −0.0408 | −2.54 | 0.0106 | 0.064 |
| overdue (longest gap) | 0.7310 | −0.0010 | −0.06 | 0.96 | 1 |
| repeat last draw | 0.7285 | −0.0035 | −0.31 | 0.76 | 1 |
| Markov order-1 pair proxy | 0.7390 | +0.0070 | +0.43 | 0.66 | 1 |

Best result in 1.67 million backtested tickets: one 5-match (three strategies), never a jackpot.
Fixed 3-match return ₱0.67–0.92 per ₱25 ticket.

**Verdict: no rule differs from uniform after Holm (min Holm p = 0.055).** Descriptive trace,
retained without any multiplicity charge: the v1/v2 filters lean on numbers above 31, which this
sample over-drew (1,912 vs 1,844.4 expected, z = +2.12); per-draw v1/v2 differences correlate at
0.40, v1/cold at 0.07. The first pass's "charged once as one equivalence class" reading was withdrawn
per the review: these correlations do not establish a single hypothesis. Power: with 834 paired
draws the conditional-null test resolves shifts of ≈0.004 matches/ticket at |z|≈2.7.

## 4. Conscious-selection instrument — first run (kb card 28, family `payout-sharing`, m=2)

Script `src/csi_popularity.py`, 984 official draws, 77 draws with ≥1 winning bet (94 bets).
**Stratification is essential**: pool size drives both the CSI level (6/42 tickets are mostly ≤31 by
construction) and the win rate (1/C(42,6) is 27× 1/C(58,6)). The first null trial, run pooled,
returned a null mean of +0.004 for T1 (7 standard errors from 0) — the Step-4 gate did its job and
the statistics were re-specified within game before any real-data claim was written down.

Step 4 null trial (500 simulated datasets of the real shape, uniform draws, Poisson winners
independent of the combination): T1 null mean 0.0010, sd 0.112 (499 distinct values); T2 null mean
0.0002, sd 0.031 — non-degenerate, centred on theory. C3 null correlation with the chi-square
frequency statistic on the same simulated draws: −0.03 / −0.05 (new equivalence class).

Step 6 first run (winners permuted within game, m=19,999, floor 5e-5; **Holm** over m=2 — Šidák
withdrawn per review §5):

| Statistic | observed | null (Step 4) | z | perm. p | Holm p |
|---|---|---|---|---|---|
| T1: mean within-game-standardized CSI, winner draws − winner-less draws | **+0.736 sd** | 0.001 ± 0.112 | 6.6 | 5e-05 (floor) | **1e-04** |
| T2: rank correlation (within-game CSI rank, winning bets) | **+0.162** | 0.000 ± 0.031 | 5.2 | 1e-04 | **1e-04** |

Poisson pseudo-MLE with game fixed effects, **HC1 sandwich** inference (information-matrix SE
retained as descriptive only): winning bets ∝ exp(0.519 · z_CSI), HC1 SE 0.077 (Wald z 6.7),
**count ratio per within-game SD of CSI 1.68 [1.44, 1.95]**; log-jackpot slope +0.33 (HC1 SE 0.19);
dispersion 2.2 (overdispersed, as Baker & McHale predict). Ticket sales N_t are not published, so
this is a count contrast at equal game and jackpot, not popularity per purchased bet. Within-game
tertiles, descriptive only: share of draws with a winner 5.0% / 5.8% / 13.5% (bottom / middle / top).
Model-conditional post-hoc power at the observed slope: 1.00 (not independent validation).

**Verdict: both tests reject after Holm — the popularity proxy predicts jackpot sharing on PCSO
data.** This is a statement about *players*, not about the draw (A7: decision layer only). It changes
expected payout, never P(win). Caveats (card 28): winners are winning *bets* (one bettor can hold
several), only the jackpot tier is observable, weights are literature proxies that were fixed before
this run and must not be tuned on these draws, one era (Feb-2026 restructure inside the window).
Promotion (Step 8) requires a reset boundary and fresh draws.

## 5. Consequences for the web picker (`lotto_picker.html`, v2.2 / r3)

A second read-only Codex gpt-6-astra review of the page (`results/codex_review_page_2026-09-06.md`)
listed 12 required edits; all are applied:

- Per game the page shows ticket A = maximum-predictive set with R, CrI, R_mix and P(next = A | M₁),
  ticket B = posterior ranks 7–12 with its **own** R/CrI/R_mix (from the JSON's
  `second_disjoint_set_ranks_7_12`), P(A or B wins) = (R_mix(A)+R_mix(B))/C, BF₀₁, the equal-odds
  deviation probability, and the overlap test labelled as absolute-deviation.
- Random pair: exact-uniform 12-sample (rejection sampling on 32-bit words), acceptance at or below
  the full-precision q40 cutoffs of the backtest JSON, failure reported instead of rejected tickets.
- z_CSI uses the fitted within-game mean/SD of the observed draws (exported by `csi_popularity.py`);
  the CSI count contrast e^{βz}/E_U[e^{βz}] is displayed as an association only.
- EV is a single uniform-draw scenario for all tickets and tiers, with the 20% tax applied to each
  realized individual share above ₱10k inside the expectation; R_mix values are shown beside it, not
  folded in; the Kelly line and the undocumented jackpot-growth constants are removed.
- Text: Bayes-factor direction corrected (all BF₀₁ < 1 at a=100, reversed at a=10), CrI lower ends
  0.98–1.07, serial-dependence scope narrowed to the tested statistics, backtest totals corrected
  (2,335,200 evaluations, 42 five-matches, 0 six) with replicate counts and the adaptive-history
  limitation, archive coverage stated as 128/128 and 100/100, within-look monitoring caveat, prize
  matrix sourced to the archived official game pages, and a technical appendix with the omitted
  formulas and the bottom/hot/last-draw R tables.

## 6. Reproduction

```
.venv/bin/python src/pcso_monitoring_run.py --manifest datasets/pcso-lotto/provenance/pcso_refresh_2026-09-06.json --verify
.venv/bin/python src/csi_popularity.py --verify
.venv/bin/python src/pcso_strategy_backtest.py --verify
.venv/bin/python src/pcso_next_draw_posterior.py --verify
```
Each prints `PASS sha256=…; wrote=none` when the regenerated bytes equal the committed file.

## 7. Monitoring addendum (r2)

Within-game permutation variant of the two lunar tests (review §7: permute within game, not
globally), reported beside the registered global-permutation family without altering it:
moon altitude r = −0.015, p = 0.836; moon illumination r = +0.005, p = 0.952. Same verdict.

## 8. Next-draw posterior predictive (r2; `src/pcso_next_draw_posterior.py`)

Model (review §1): 6-without-replacement product-weight draw, f_w(S) = ∏_{i∈S} w_i / e₆(w);
likelihood ∏ᵢ w_i^{c_i} / e₆(w)^T; prior Dirichlet(a) with a **fixed a priori** (a=100; sensitivity
a=10, 1000); posterior by importance sampling from Dirichlet(a+c) with weights z(w)^{−T}, 200,000
samples per game (effective size ≥ 195,000). The first-pass predictor (Dirichlet-multinomial on ball
counts, empirical-Bayes a, product of posterior means) was withdrawn: it omits the e₆ normalizer, its
conjugacy does not survive, and it let the data choose the prior. Output
`results/pcso_next_draw_posterior_2026-09-06.json`. Codex's independent reconstruction uses the same
model and reaches the same conclusions; its point estimates differ from the stored integration at the
third decimal (e.g. 6/55 R 1.641 vs 1.640) and its order-1 test uses likelihood-ratio ordering,
whereas this script orders by absolute deviation of the total overlap (6/49 p 0.041 vs 0.045; 6/55
0.053 vs 0.048). The two are kept distinct; the page reports the stored values.

| Game | maximum-predictive set S* | R = C(P,6)·E[f_w(S*)] [95% CrI] | BF₀₁ (a=10 / 100 / 1000) | R_mix (equal model odds) | order-1 overlap exact p (absolute deviation) |
|---|---|---|---|---|---|
| 6/42 | 03 06 12 36 39 41 (6 tied with 18, 35) | 1.48 [0.99, 2.13] | 6976 / 0.95 / 0.95 | 1.25 | 0.65 |
| 6/45 | 04 05 08 24 25 27 | 1.50 [0.99, 2.16] | 1237 / 0.59 / 0.90 | 1.32 | 0.14 |
| 6/49 | 08 14 16 26 36 44 | 1.56 [1.03, 2.26] | 3514 / 0.69 / 0.91 | 1.33 | 0.041 |
| 6/55 | 05 42 44 45 48 50 | 1.64 [1.07, 2.38] | 46 / 0.22 / 0.80 | 1.52 | 0.053 |
| 6/58 | 12 15 17 43 50 57 | 1.50 [0.98, 2.20] | 557 / 0.49 / 0.89 | 1.34 | 0.17 |

P(any ball's inclusion probability deviates >10% from 6/P | data, M₁(100)) ≈ 1 in every game, which is
a property of the conditional model, not evidence for it; at equal model odds it is 0.51–0.82, and
under a=1000 it is 0.012–0.029. Under the uniform model every history-based rule has R = 1 and
Δ = 0 exactly. Reading the Bayes factors correctly: at a=100 every BF₀₁ is below 1, i.e. the data
lean toward unequal weights in all five games, most in 6/55 and least in 6/42, and the direction
reverses at a=10 — the evidence is weak and prior-sensitive, not a verdict for either model.
**Verdict: the maximum-predictive sets and their multipliers are the complete mathematically derived
prediction this repository supports; the evidence for unequal weights is weak and prior-sensitive,
and neither tested serial-dependence statistic rejects after Bonferroni (other transition
alternatives were not exhausted). G0 exploratory.**

## 9. Addendum r4 — anytime-valid e-process monitor (2026-09-06, exploratory G-labeled)

Motivation: §2's registered m=9 family controls error within a single look; the page itself
recorded that "weekly cumulative looks are exploratory monitoring without a sequential
alpha-spending rule". The stochastic-prediction literature survey (operator-directed; see
`docs/kb/arxiv-stochastic-prediction-survey.md`) identified the standard fix in Ramdas, Grünwald,
Vovk, Shafer, *Game-Theoretic Statistics and Safe Anytime-Valid Inference* (arXiv:2210.01948).

Construction (their §1.2/§2.2/§3.2.2–3.2.3, applied to our simple null M₀), in statistical terms: for each
draw, form the prequential (one-step-ahead, past-only) posterior-predictive density
q_t(S) = E_{w∼Dir(100+counts_{<t})}[f_w(S)] and take the predictive likelihood ratio
Λ_t = q_t/p₀ with p₀(S) = 1/C(P,6). The evidence process M_t = ∏Λ_s is a nonnegative martingale
with unit expectation under M₀, so Ville's inequality gives P(sup_t M_t ≥ 1/α) ≤ α at every
monitoring instant — a sequential test with anytime-valid type-I error control. The predictive
prior Dirichlet(100) is the same fixed a-priori prior as §8 (their §6.4: the analysis plan must be
fixed before the data; never selected after seeing outcomes). This tests uniformity (simple null),
not full exchangeability (their §5.5: the latter admits no nontrivial evidence martingale in the
data filtration). Functionally, this layer is the self-correction feedback of the prediction
pipeline: the earliest statistically valid detection of a departure from uniformity is exactly the
moment the model-averaged predictor is justified in shifting weight toward M₁.

Results (`src/pcso_eprocess_monitor.py --verify` → `results/pcso_eprocess_monitor_2026-09-06.json`,
seed 20260906, 4,000 Dirichlet samples per draw, byte-deterministic):

| Process | 6/42 | 6/45 | 6/49 | 6/55 | 6/58 | product |
|---|---|---|---|---|---|---|
| full-history e (final / running max) | 1.19 / 1.32 | 1.70 / 5.48 | 1.29 / 1.58 | 4.61 / 7.63 | 2.02 / 3.56 | 24.4 |
| confirmation-set e (final / running max) | 1.37 / 1.55 | 0.39 / 1.23 | 2.50 / 2.97 | 0.70 / 1.16 | 1.11 / 1.23 | 1.04 |

Coherence check: the full-history evidence value is a Bayes-factor process, and 6/55 gives 4.61 vs
BF₁₀(100) = 1/0.221 = 4.52 — agreement to within Monte Carlo error, cross-validating §8.
Ville threshold at the family level α = 0.05/9 = 0.0056 is 1/α ≈ 178.6: **no game and no product
crosses it — the uniform-draw null is not rejected at any monitoring instant** (anytime p ≥ 0.131 per
game; 0.041 on the full-history product, which is exploratory and not multiplicity-corrected
across the two processes). This monitor is G-labeled exploratory, sits outside the frozen m=9
family, and is the inference/self-correction layer of the prediction pipeline rather than a change
to the ticket generator; it closes the sequential-validity gap for future weekly looks. The picker
page's monitoring paragraph cites it.

### 9.1 Addendum r5 — v2: mixture-prior evidence process and e-detector (2026-09-06, exploratory G-labeled)

v2 (`src/pcso_eprocess_monitor_v2.py` → `results/pcso_eprocess_monitor_v2_2026-09-06.json`, seed
20260906, 4,000 samples per draw for the evidence process, 600 for the e-detector,
byte-deterministic, `--verify` PASS) upgrades the sequential inference layer on two points from
the surveyed literature:

1. **Mixture-prior prequential evidence process** (arXiv:2210.01948 §3.2.2–3.2.4 mixture method /
   REGROW robustness): the predictive prior is R = uniform over Dir(a), a ∈ {10, 30, 100, 300,
   1000}, fixed a priori. This removes by construction the single-concentration prior-sensitivity
   documented in §8 (BF₀₁ direction reverses between a=10 and a=100): the evidence grows whenever
   any component alternative fits, and no concentration is selected post hoc (§6.4).
2. **e-Detector for draw-mechanism drift** (§5.7, Shin–Ramdas–Rinaldo): the running sum of
   mixture evidence processes restarted every 13 draws over the confirmation set. Under a
   stationary null the expected run length to a false alarm at threshold 1/α is ≥ 1/α.

| Layer | 6/42 | 6/45 | 6/49 | 6/55 | 6/58 | product |
|---|---|---|---|---|---|---|
| mixture e, full history (final / max) | 0.50 / 1.29 | 2.18 / 13.23 | 1.22 / 1.84 | 11.56 / 32.55 | 3.17 / 8.66 | 48.4 |
| mixture e, confirmation (final / max) | 1.36 / 1.72 | 0.22 / 1.31 | 3.77 / 5.26 | 0.45 / 1.03 | 1.11 / 1.33 | 0.55 |
| e-detector max (confirmation) | 3.98 | 2.35 | 6.80 | 3.26 | 6.44 | — |

Readings: (i) the mixture is strictly more informative than the fixed a=100 process of §9
(6/55: 11.56 vs 4.61 full-history; product 48.4 vs 24.4) because it accumulates evidence at
whichever concentration fits, as the robustness theory predicts; (ii) 6/42 now leans toward the
uniform model (e = 0.50), which the single-a process could not express; (iii) **no game, no
product, and no detector crosses the Ville threshold 1/0.0056 ≈ 178.6** — the uniform-draw null
is not rejected at any monitoring instant, and no draw-mechanism changepoint is detected
(detector maxima 2.4–6.8 vs 178.6); (iv) strongest single-game evidence remains 6/55 at anytime
p = 1/32.5 ≈ 0.031, below the registered level. Implementation note: an initial detector run over
the full history with pre-freeze counts double-counted the pre-freeze draws (they appeared both in
the conditioning counts and as new evidence), inflating D_max to ~10⁶; the detector must run on
the confirmation set only — verified against a synthetic uniform null (D_max ≈ 128, below
threshold, at both sample budgets). G-labeled exploratory; outside the frozen m=9 family.
