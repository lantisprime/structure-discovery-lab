# Console Redesign — Repo Grounding

**Added:** 2026-07-04. **Purpose:** ground the `webapp/` operator-console redesign in the
lab's real governance standards, pipeline scripts, data artifacts, and the design prototype —
so every UI string, badge, and number is traceable rather than invented.

**Scope / guardrails.**
- The design references (`Structure Lab Console.dc.html`, `support.js`, screenshots) live
  *outside* this repo in `~/Developer/projects/design_handoff_structure_lab_console/`. They are
  spec only; the prototype runtime is **not** ported.
- The redesign writes only `webapp/static/index.html` and a **read-only** enrichment of
  `webapp/server.py` (`experiment_options`). It never edits frozen artefacts (sealed
  `results/*.json`, committed `docs/REGISTRATION_*.md`, eval keys, frozen modules).
- Every number renders from a live endpoint; the prototype's values are placeholders.

This document consolidates four repo-reading passes (governance, `src/` pipeline, data schemas +
dataset stats, prototype copy). Facts are cited `file:line`.

---

## 0. Grounding corrections to the plan (the deltas that matter)

1. **Honesty meter p is `p_meta_discrete`, real value `0.032`, not the prototype's `0.385`.**
   It is the Monte-Carlo tail of a KS statistic against the *discrete* add-one lattice null
   (not a continuous-uniform KS p): `src/meta_uniformity.py:15-17,88-102,114`; on-disk
   `results/meta_uniformity.json` → `p_meta_discrete = 0.03248`, `ks_stat = 0.1246`,
   `frac_le_05 = 0.1061` (14/132), `sim_frac_le_05_q05_q95 = [0.0227, 0.0833]`. The observed
   `frac_le_05` sits *above* the simulated band → the panel is mildly "hot," consistent with the
   low meta-p. This excess is the already-adjudicated **#45 shadow family**, not a new discovery
   (`docs/ADVERSARIAL_REVIEW.md:96-99,163-164`). The console governance doc quotes an older panel
   at `p=0.044` (`docs/RESPONSE_EXTERNAL_REVIEW.md:20`) — the UI must render the **live artifact
   value** via `server.py`, never a literal, and its caption must be derived from the data
   (honest either way). This is the "honesty is honest / a null is a real result" non-negotiable.

2. **G0–G6 grades are hand-authored strings, not computed.** They are string literals in
   `src/build_run_ledger.py` transcribed into `results/run_ledger.jsonl`'s `grade` field
   (`docs/RESPONSE_EXTERNAL_REVIEW.md:30-39` defines the ladder). Values are compound and some
   runs have **no grade at all** (the `eq_*`/`synthetic_*` runs carry `phase`+`status` instead).
   UI rule: badge = first `G\d` token (mirror `build_run_ledger.py:189` `grade.split()[0]`),
   full string in the `title=` tooltip, neutral fallback when there is no `Gn` token.

3. **Gap A (wizard dataset sparklines) needs a small read-only server loader.** The 4 astro/geo
   series reuse `load_csv_col` directly; the 5 PCSO lottery sets are interleaved in one file and
   have no single numeric column (sparkline = derived draw-sum `N1..N6`, filtered by `Game`).
   See §3B.

4. **Recon B (wizard "Run" step is honest).** The wizard only *drafts* a registration
   (`webapp/server.py:353 create_experiment`); it never executes. Step 5's pipeline UI is
   illustrative — Step 6 hands the draft to Approvals, and nothing runs until signed. The
   self-gated executor enforces this (`src/corrected_rerun_registered.py:28-39`).

---

## 1. Governance standards (the copy vocabulary)

Most authoritative docs — cite these in UI copy:
`docs/PLAYBOOK_THEOREM_HARMONIZATION.md` (mechanized constitution: S-1…S-8, H-1…H-5, family/Šidák/floor math),
`docs/RELATIONAL_RUNBOOK.md` (cross-dataset procedure, Phases 0–6),
`docs/RUNBOOK.md` (within-dataset cycle, Phases 0–6 — **different pipeline, same numbering; label them**),
`docs/RESPONSE_EXTERNAL_REVIEW.md` (G0–G6 ladder),
`docs/ADVERSARIAL_REVIEW.md` (#45 / honesty-meter caveats),
and the **already-shipped console copy** in `webapp/server.py` + `webapp/static/index.html` (reuse verbatim).

### 1.1 Phases 0–6
**RELATIONAL_RUNBOOK** (cross-dataset): 0 Eligibility gates (`:12`) · 1 Hypothesis registration,
committed before results, no outcome expectation (`:24,:44`) · 2 Execution, seeded + add-one
corrected (`:54`) · 3 Mandatory §6.3 checks before any verdict (`:111`) · 4 Reporting, negatives
first-class (`:126`) · 5 Ledger + synthesis (`:180`) · 6 Decision layer, one-way, "no strategy,
no stake" (`:188`).
**RUNBOOK** (within-dataset): 0 Acquire + define null (`:27`) · 1 Validate/row-audit (`:36`) ·
2 Explore, MC-calibrated, four faces, count every test (`:49`) · 3 Adversarial review + register,
freeze exploration (`:74`) · 4 Confirm on held-out post-freeze data (`:87`) · 5 Equation discovery,
`FAILED_EQUATION_SEARCH` publishable (`:96,:111`) · 6 Decide (Doob/EV/Kelly) (`:114`).

### 1.2 Playbook algorithms S-5/S-6/S-7 and M4 (all in `PLAYBOOK_THEOREM_HARMONIZATION.md`)
- **S-5 Verdict tiers** (`:328`) — deterministic decision table mapping (raw p, corrected α,
  floor, admission, registered, era-clean) → tier. "The tier is computed from the numbers, no
  human opinion."
- **S-6 Row-trace attribution** (`:346,:366`) — leave-one-out leverage finds the rows driving a
  flag; Jaccard > 0.5 overlap with a known anomaly charges nothing new. Mechanizes "k co-firing
  flags collapse to the number of DISTINCT anomalies."
- **S-7 Era quarantine** (`:370`) — re-runs per era segment; a pooled p that isn't era-clean is
  QUARANTINED, never promoted past ERA_BOUNDED_FLAG.
- **M4 Data-regime sensitivity** (`RELATIONAL_RUNBOOK.md:82`; `RESPONSE_EXTERNAL_REVIEW.md:18`) —
  every hit-count statistic reports three variants {all / ex-suspicious / verified-only}. "A flag
  has to survive dropping the questionable rows."
- (Related: S-3 = MC p is the only p allowed; S-4 = two-run byte-identical; S-8 = honesty meter.)

### 1.3 Evidence grades G0–G6 (`RESPONSE_EXTERNAL_REVIEW.md:30-39`)
G0 exploratory, no claim · G1 calibrated instrument · G2 internal/registered result · G3 auditable
(hash-committed) registration · G4 independent reproduction (different agent identity) · G5 held-out
confirmation · G6 decision-grade. Shipped tooltip copy to reuse: `index.html:334-336`.

### 1.4 Multiplicity model
- **Šidák:** `α_fam = 1 − (1−0.05)^(1/m)`, m = number of **families** engaged (not instruments):
  `PLAYBOOK:208,157`; `src/core/stats.py:19`. Base α=0.05 ratified
  (`RESULTS_EQ_READJUDICATION.md:6,14`). Two conventions: detection = families engaged; accumulating
  claim families = cumulative charged m (`PLAYBOOK:212-220`).
- **Floor rule (M3):** permutation count m large enough that `p_floor = 1/(m+1) ≤ α_corrected/2`,
  else inadmissible: `RELATIONAL_RUNBOOK.md:75`, `PLAYBOOK:311,201`, enforced
  `src/design_verifier.py:129-133`. Equivalent: `m_null ≥ ceil(2/α_fam) − 1` (`PLAYBOOK:209`).
  Console phrasing `server.py:1361`.
- **Families are measured, not assumed** — H0 Spearman corr, single-linkage merge at ρ=0.90,
  couplings reported for ρ∈[0.5,0.90) → `families.json` (algorithm H-2, `PLAYBOOK:130-152`).
- **k same-family co-fires = ONE flag** (`PLAYBOOK:159`; `RUNBOOK.md:70`; `server.py:1363`).
  Standing example: #45 seen through 6 correlated statistics (`RUNBOOK.md:135`).

### 1.5 Honesty meter / meta-uniformity panel (S-8)
Algorithm S-8 (`PLAYBOOK:382`), implemented `src/meta_uniformity.py`. Reports a **discrete
(lattice-aware) meta-p** (`p_meta_discrete`), not continuous KS, because add-one MC p-values on
m=19..1199 lattices are stochastically ≥ U(0,1). The panel is **descriptive, not a calibrated
test** (entries share draws). "Looks honest" = flat histogram, frac ≤ .05 inside the simulated
band, and `p_meta ≥ .05`; alarms when frac is outside the band or `p_meta < .05`
(`PLAYBOOK:392-393`). Console histogram copy `server.py:1320`. The residual low-p excess is
concentrated in the already-adjudicated #45 shadow family — one era-bounded anomaly
(`ADVERSARIAL_REVIEW.md:79-81,96-99,163-164`).

### 1.6 Expectation-free & the "no X, no Y" rules
Discovery tests carry **no outcome expectations**; predicted results are forbidden in
registrations (`RELATIONAL_RUNBOOK.md:39-46`; `RESPONSE_EXTERNAL_REVIEW.md:43-47`;
`server.py:1310`). "**No card, no test — but also: no gate, no data.**" — an instrument needs
(1) a theorem card, (2) a ≥200-trial null-calibration gate, (3) a families.json placement, and a
registration before touching real data (`server.py:1140,1298,1347`; `index.html:836`).

### 1.7 Canonical copy (reuse verbatim)
- Nulls first-class: `RELATIONAL_RUNBOOK.md:133`; `index.html:342,608`; `server.py:1362`;
  NULL tier "below detection at these shapes, not proof of absence" (`RELATIONAL_RUNBOOK.md:145`);
  `FAILED_EQUATION_SEARCH is publishable` (`RUNBOOK.md:111`).
- Human gate: `server.py:1289`; `approved_by_human: true # HUMAN-GATE` (`PLAYBOOK:290`).
- Registration-before-run: `RELATIONAL_RUNBOOK.md:44`; `server.py:1361`.
- **Golden-rules block (single best source), `server.py:1361-1364`:** "registration before run;
  every p in the ledger; the floor rule (m large enough that 1/(m+1) ≤ corrected alpha/2); nulls
  are published proudly; k same-family co-fires = ONE flag; sandbox results are never evidence."

**Vocabulary cautions:** (1) the two runbooks share Phase 0–6 numbering but describe different
pipelines — label relational vs within-dataset. (2) The RELATIONAL five-tier reporting taxonomy
(`RELATIONAL_RUNBOOK.md:136`: STRUCTURED / NULL / NEAR_MISS_REGISTERED_SIGNAL / EXPLORATORY_ONLY /
OUT_OF_SCOPE) differs name-for-name from the S-5 mechanical tokens (FLAG / NULL_CONFIRMED /
NEAR_MISS / FLAG_AT_FLOOR / ERA_BOUNDED_FLAG / EXPLORATORY_ONLY) — pick one set per surface.

---

## 2. `src/` pipeline (what the Run-centre jobs do)

- **`design_verifier.py`** — logic gate. Reads `multiplicity_ledger.jsonl` + `run_ledger.jsonl`
  (+ `families.json`, audited lotto CSV); 7 checks incl. permutation-floor (`:124-135`), schema
  validity, p-lattice integrity `raw_p*(m_perm+1)∈ℤ` (`:95-108`), family-registry consumption,
  run↔test-ledger reconciliation (`:176-207`). Writes `results/design_verifier_report.json`
  (`verdict PASS/FAIL`), exits 1 on any violation.
- **`verify_relational_docs.py`** — numeric gate. Re-derives every number quoted in ADMISSION/
  FIRSTRUN/SYNTHESIS docs from raw JSONs (`:11-15`); prints `MISMATCH` and exits nonzero on drift.
  Writes no artifact.
- **`lint_frozen_imports.py`** — two-truths guard. Auto-detects FROZEN modules by header
  (`:22-29`); `src/core/` must not import frozen at module level; other importers must be on
  ALLOWLIST (`:35-48`). Exits 1 on violation.
- **`meta_uniformity.py`** — the honesty meter (panel v2). See §1.5. Emits `p_meta_discrete`,
  `frac_le_05`, `sim_frac_le_05_q05_q95`, `composition_sensitivity`, `ks_stat` →
  `results/meta_uniformity.json` + `results/figures/fig9_meta_uniformity.png`.
- **`build_multiplicity_ledger.py`** — rebuilds `results/multiplicity_ledger.jsonl`, one row per
  real-data lotto-side test. Keys (`:24-30`): `run_id, dataset, claim_type, method, raw_p, m_perm,
  p_floor, family_id, within_run_m, global_m, row_type`. Charge rows use `m_delta` (no `raw_p`).
  `global_m` = count of live tests (excludes `superseded_by` + `exploratory`, `:166-176`).
  Append-only / non-destructive (aborts rather than drop a row). Field is `family_id` (not
  `family`).
- **`measure_equivalence.py`** — H0 Spearman corr between per-game stats, union-find merge at
  |ρ|≥0.90 (`:65-101`). Writes `results/families.json`: `families{}` (keyed by `family_id` →
  `{members, class, status}`) + `reported_couplings` (0.5≤|ρ|<0.90) + `measured_matrix`.
- **`corrected_rerun_registered.py`** — self-gated executor. `approval_gate()` (`:28-39`) parses
  `docs/REGISTRATION_CORRECTED_RERUN.md` and `raise SystemExit` if `approved_by_human` is blank or
  the doc still says DRAFT. Writes `results/corrected_rerun_r1.json`.
- **`readmit_r1_r7.py`** — re-admits R1–R7 under tighter gates (n_neg=200, m≥39, lattice-aware
  chi²). Verdicts `ADMITTED_V2 / EXPLORATORY_ONLY / SMOKE_ONLY` (`:191-193`). Chunk-resumable →
  `results/readmission_v2.json`.
- **`grade_agent_eval.py`** — *not* the G0–G6 grader; a mechanical PASS/FAIL grader for agent evals
  (`agents/evals/EVAL_SET.md`), only V-1 implemented.

**server.py field-contract check (all confirmed):** `meta_uniformity.json` has
`p_meta_discrete / frac_le_05 / sim_frac_le_05_q05_q95 / composition_sensitivity`
(read `server.py:151-152`); `families.json` has `families{}` + `reported_couplings`
(`server.py:153-154,338`); `run_ledger.jsonl` rows have `grade / status / datasets /
real_data_tests`. Caveat: `grade` is free-text/compound and sometimes absent — handle in UI.

---

## 3. Data schemas, live values, and dataset stats

### 3A. Current artifact values (wire these live; do not hardcode)
- **`run_ledger.jsonl` — 22 runs.** Newest: `corrected_rerun_r1` (2026-07-03, `G2 registered`,
  "joint NULL everywhere; positive control intact; attribution fire dissolves"). Runs 13–18
  (`eq_*`, `synthetic_*`) have **no `grade`** — carry `phase`+`status`.
- **`multiplicity_ledger.jsonl` — 271 rows** (267 `test` + 4 `family_charge`). **Live = 195**
  (test, no `superseded_by`, not exploratory); `global_m = 195` uniform on live rows;
  live `raw_p ≤ .05` = 19/194 ≈ **9.8%**.
- **`meta_uniformity.json`:** `panel_version 2`, `n_tests 132`, **`p_meta_discrete 0.03248`**,
  `frac_le_05 0.1061`, `sim_frac_le_05_q05_q95 [0.0227, 0.0833]`, `composition_sensitivity`
  {keep_first_dedup 0.1061 / eq_rows_included 0.1119 / miscalibrated_presence_included 0.1061 /
  drop_655_lambda_max_family 0.0923}. (Panel n=132 ≠ ledger-live 195: panel excludes `eq_`,
  superseded, family_charges, gate-based, median-based methods.)
- **`families.json` — 9 families:** hit-count-cooc [lambda-max, graphon-b1-attribution]
  (measured ρ=0.988); hit-count-temporal [half-corr]; recovery [knn-recovery, matrix-completion];
  two-sample [mmd]; graph [cooc-spectra] (measured 2026-07-03, anti-shadow); tda [delay-embed-H1];
  cca [cca-covariates + splits]; eq.tidal-manila.harmonic (cumulative m=10). `reported_couplings`:
  (lambda_max, graphon_b1)=0.987; (lambda_max, half_corr)=0.642; (graphon_b1, half_corr)=0.645.
- **Equation candidates** (`eq_tidal_v2.json` + `eq_readjudication_2026-07-02.json`), data
  `datasets/tidal-manila/tidal_derived.csv` (366 rows, 2025-06-11..2026-06-11):
  - `eq.tidal-manila.phase.moondist.v2` → Moon Dist, B1_harmonic_1freq_k1, 27.555 d (anomalistic),
    frozen `FAILED_EQUATION_SEARCH`, corrected **FAIL_corrected**.
  - `eq.tidal-manila.phase.v2` → Total tidal accel, A2_harmonic_2freq_k1, 27.555 + 31.812 d,
    frozen `FAILED_EQUATION_SEARCH`, corrected **FAIL_corrected**.
  - v1 readjudication: `phase.v1` FAIL_corrected; `moondist.v1` AT_FLOOR_RESOLUTION_LIMITED;
    `confirm1` MECHANISM_SUPPORTED but corrected UNCONFIRMED (pending v4). **RATIFIED** by Cha
    2026-07-02.

### 3B. Dataset stats for the wizard cards (Gap A)

**4 astro/geo datasets** — already in `SERIES` (`server.py:200-209`), all `date_col="Date"`,
one row/day, reusable via `load_csv_col(path, col)`:

| SERIES key | rows | span | sparkline col |
|---|---|---|---|
| moon_distance | 366 | 2025-06-11→2026-06-11 | `Moon Dist (km)` |
| tidal_accel | 366 | 2025-06-11→2026-06-11 | `Total tidal accel (g)` |
| pressure | 366 | 2025-06-11→2026-06-11 | `P_msl_mean_hPa` |
| kp_index | **365** | 2025-06-11→**2026-06-10** | `Kp_daily_mean` |

*Only oddity:* kp is 365 rows and ends a day earlier — don't assume a shared axis.

**5 PCSO lottery sets** — NOT in `SERIES`. Canonical file `datasets/pcso-lotto/data_draws_1yr.csv`
(cols `Game,Date,N1..N6`, 806 rows, all games interleaved). Sparkline value = **draw sum
N1+…+N6**, filtered by exact `Game` string:

| Game | rows | span | draw-sum min/mean/max |
|---|---|---|---|
| Lotto 6/42 | 160 | 2025-06-12→2026-06-23 | 42/130/197 |
| Mega Lotto 6/45 | 162 | 2025-06-11→2026-06-24 | 54/137/207 |
| Super Lotto 6/49 | 161 | 2025-06-12→2026-06-23 | 52/147/252 |
| Grand Lotto 6/55 | 162 | 2025-06-11→2026-06-24 | 88/171/263 |
| Ultra Lotto 6/58 | 161 | 2025-06-13→2026-06-23 | 92/179/294 |

**Server plan (read-only enrichment of `experiment_options`):** for astro/geo call existing
`load_csv_col`, then `rows=len`, `first=dates[0]`, `last=dates[-1]`, sparkline = stride
`step=max(1,len//24)` → `values[::step][:24]`. For lottery add a tiny sibling loader (do **not**
extend `SERIES`, whose values are `(path,col,label)` triples): `DictReader` over
`data_draws_1yr.csv`, keep `row["Game"]==game`, `s=sum(int(row[f"N{i}"]) for i in 1..6)`, sort by
date, same stride-downsample. Returns the same `{rows, first_date, last_date, sparkline}` contract.
Note: the prototype's card numbers (e.g. "1,240 rows · 2019–2026") are placeholders — real spans
are ~160–366 rows over 2025–2026.

---

## 4. Prototype copy & structure (per view)

Verbatim strings the redesign must match. Full per-view digest — abridged here to the load-bearing
copy; the prototype `Structure Lab Console.dc.html` is the exhaustive source.

**Global chrome.** Sticky header `rgba(245,245,247,.82)` + `blur(16px)`, `max-width:1080px`,
`padding:13px 24px`. Logo = 29×29 accent square (radius 8) + inline SVG waveform + Newsreader-600
wordmark **"Structure Lab"**. Desktop nav pills: **Overview · Experiments · Equations · Theorems ·
Ledger** then **More ▾** (holds **Agents · Approvals · Admin · Help**). Right: **✦ Companion**
button. Guide banner ("Why this page exists") on every view except Overview + Wizard: accent-soft,
radius 16, `ƒ` glyph + bold accent label + one line (`#4a545e`) + optional CTA pill.

**1 · Overview (`home`).** Eyebrow date `new Date().toLocaleDateString('en-US',{weekday,month,day})`
→ "Saturday, July 4". Greeting (pending approval): **"One decision is waiting for you. Everything
else is calm."** (else "The lab is quiet — a good moment to start something new.").
Next-action card (dark): eyebrow **"Right now, the lab needs one thing"**, title **"Approve the
corrected-rerun registration"**, detail **"A registered, corrected-instrument rerun is drafted and
waiting on your signature. Nothing runs until you sign — that's the lab's integrity."**, CTA
**"Review & approve →"**. Sub-caption **"When you're unsure what to do, come back here — this card
always shows the single next step."** 3 stat tiles: `{runs}` "experiments in the run ledger" ·
`{p_meta}` "honesty-meter p (looks honest)" [green] · `{priced}` "p-values priced into the global
correction". "Where the lab is" 5-stage timeline (Correctness audit ✓ / Verdicts ratified ✓ /
Corrected rerun now / Blind eval pack next / Equation v4 later). "Latest result" card (run id,
grade badge, interpreted status, "Read the interpreted result →"). "Start something new" accent
card ("A six-step wizard drafts the registration and does the governance math for you.",
"New experiment"). 3 help cards → open Companion: 📖 "What a null means" / 🧭 "How the lab works" /
⚖️ "The honesty meter".

**2 · Wizard (6 steps).** Header: **"← Overview"** · serif step H1 · sub · **"Step N / 6"**.
Stepper + titles: 1 Choose data / **"Which stochastic dataset?"** · 2 Frame question / **"What are
you asking?"** · 3 Instruments / **"Which instruments?"** · 4 Register / **"Register & approve"** ·
5 Run / **"Run the experiment"** · 6 Results / **"Make sense of it"**. Nav labels: Continue×3,
"Continue to run", "See results", "Back to Overview".
- Step 1: dataset cards (kind tag, name, hint, sparkline, mono `{rows} rows · {span}`; selected =
  accent ring + ✓).
- Step 2: "Experiment id" (ph "e.g. b8_pressure_memory"), "The question under test" (ph "Do the
  6/49 draw sums share distributional structure across quarters?"), ✦ tip **"State what you're
  *asking*, not what you hope to find. The lab is expectation-free — you commit to publishing
  either outcome before any data is touched."**, "Drafted by" (default "Cha (lab owner)").
- Step 3: face-group cards (Statistical/Dynamical/Cross-sectional/Relational) with instrument
  toggle chips (mono id + claim type). Sticky dark summary bar: **Claims · Families · Šidák α′ ·
  Min m** + note **"The lab does the multiplicity math. Same-family instruments count once."**
  Live math: families = distinct `FAMILY_OF` selected; α′ = `1−0.95^(1/nf)` (4dp);
  min m = `ceil(2/α′)−1`.
- Step 4: mono header **"docs/REGISTRATION_{RUNID}.md · DRAFT"**; review rows; "Both outcomes,
  declared up front" (NULL / REJECT); checkbox **"I accept both branches and won't edit this
  registration after approval."**; "Human-gate signature" + button **"Approve & sign"** →
  **"Approved ✓"**; note **"✓ Signed into the append-only audit log. Ready to run."**
- Step 5: **"Agent pipeline"** + `{pct}%` bar; role-separated agent rows (research-scout·sonnet …
  independent-verifier·haiku …). CTA **"Run experiment"** → "Running…" → "Completed".
- Step 6: verdict banner (eyebrow "Verdict" + serif label; "Evidence grade" + mono grade tooltip);
  "What this means" ✦ card (null copy: "Across all five faces … indistinguishable from a
  constrained-uniform null …", "This is a successful, publishable result … 'no effect ≥ ε at this
  n.'", "Decision layer: the Doob gate holds and Kelly sizing returns f*=0"); per-face result
  cards; bottom 2-up: "Equation discovery" + "Honesty meter" (big mono p + "meta-panel p" + note).

**3 · Experiments (`results`).** H1 **"Experiments"**. Guide: **"Every past run, newest first —
the lab's memory. Tap a run for its plain-language interpretation and evidence grade."** CTA
**"＋ New experiment"**. Rows grid `1.3fr 1.4fr auto`: mono run_id + date · status · grade badge
(color-coded, `title=` tooltip). Grade tooltips G0–G6 as §1.3.

**4 · Equations.** H1 **"Equations"**. Guide: **"Left: the equation program's real candidates and
what survived scrutiny. Right: a safe sandbox — pick a series, type periods, press Fit to test a
hypothesis. It charges nothing and can't contaminate the lab."** CTA **"Try the moon-distance
candidate →"**. Left "Candidate equations" (mono id + verdict badge + `{target} · periods {p} d` +
"Try it →"); collapsible "▸ Why statuses changed (readjudication)". Right "Try a hypothesis":
"Series" select, "Periods (days, comma-separated)" (default 27.555), "include linear trend"
checkbox, **"Fit hypothesis"**, disclaimer **"Descriptive fit + 80/20 hold-out. 0 multiplicity,
never citable."** Result card "Fit — {label}" + segmented **Data + fit / Residuals / Residual
spectrum** (mobile **Fit / Resid. / Spectrum**) + captions + 3 mono stats (hold-out RMSE,
climatology baseline, beats/loses).

**5 · Theorems.** H1 **"Theorem arsenal"** (nav label "Theorems"). Guide: **"The lab's rulebook —
an instrument may only touch data if its card exists here. Search, filter by face, or tap a card to
read it."** CTA **"＋ Propose a card"**. Search ph **"Search theorems, statistics, blind spots…"**.
Face chips: **All · Statistical · Dynamical · Algorithmic · Cross-sectional · Relational ·
Decision** (face colors: Statistical `#0071e3`, Dynamical `#248a3d`, Algorithmic `#b0670a`,
Cross-sectional `#8e5bd0`, Relational `#c2643a`, Decision `#3a5a8c`). Card → modal + "Export to
PDF". "Propose a theorem card" modal fields: Title, Face, Statement, Null value under H₀, Detects,
Blind to.

**6 · Ledger.** H1 **"Ledger"**. Guide: **"The lab's accounting: every real-data p-value, what
counts toward the global correction, and the honesty meter watching the whole population."**
(no CTA). Chart header **"Explore the p-values"** + segmented **Histogram · By family · In
sequence**; captions (hist: "Recent live p-values in 0.05 bins. Honest nulls look roughly flat; the
small left excess traces to the known #45 family — not a new discovery."). 3 tiles (test rows /
live toward global m / exploratory). "Recent test rows" table (dataset / method / p / flag).
*Note:* the standalone Honesty-meter card lives in **Wizard Step 6**, not Ledger — on Ledger the
honesty framing is the histogram caption.

**7 · Agents ("Run centre").** H1 **"Run centre"**. Guide: **"The cockpit — launch gates,
executors, analysis jobs and standalone agents, then watch their live logs."** CTA **"Run the three
gates"**. Four group cards: 🛡 Gates & health (Design verifier / Numeric verifier / Frozen-import
lint), ▶ Registered executors (Corrected-instrument rerun / Re-admit R1–R7), 📊 Analysis (Rebuild
honesty meter / Re-measure families), 🧹 Maintenance (Git status / Rebuild multiplicity ledger).
"Launch a standalone agent" accent card (textarea + "Launch agent"). Dark job-log panel.

**8 · Approvals.** H1 **"Approvals"**. Guide: **"You are the lab's human gate: nothing registered
runs without your signature here."** CTA **"Sign the pending registration"**. "Awaiting your
signature" (pending row + "Approve"; empty **"✓ Nothing pending — all registrations are
signed."**); "Sign as" input; "Audit log" rows.

**9 · Admin.** H1 **"Admin"**. Guide: **"Set up how agents authenticate and which model each role
uses. Everything sensitive stays on this machine and is served masked."** §1 "How should agents
authenticate?" toggle **Use an API key / Use a subscription**; provider search ph **"Search
providers (e.g. deepseek, groq, mini)…"**. §2 "Who does what — agent roles" (Analyst 🔬 / Executor
⚙️ / Reviewer 🛡 / Companion ✦; Provider · Model · effort fast/balanced/deep · Test). "Data sources"
(local/keyless) + "Add a dataset (validated)". "Lab settings".

**Companion drawer.** Bottom-right, `width:min(360px,100vw−40px)`, radius 20, slides via fadeUp.
Header ✦ **"Lab companion"** + ✕. Bubbles: user = accent/white (bottom-right radius 4); assistant =
`#f0f0f3`/`#2a2a2c` (bottom-left radius 4). Seed: "Hi — I'm your lab companion. The Overview always
shows the single next step; ask me anytime what something means." Quick-ask chips: **"What should I
do next?" · "What does a null mean?" · "Explain the honesty meter"**. Input ph **"Ask about the
lab…"** + ↑ send.

### Design tokens (confirmed)
Accent `#0071e3` / soft `#e8f0fd` (accent-dark text `#0058b0`, `#3a5a8c`). App bg `#f5f5f7`; card
`#fff` border `#e8e8ed`; input border `#e2e2e7`; hairlines `#f0f0f3`. Dark surface `#1d1d1f`;
on-dark `#f5f5f7`, muted `#c9c9ce`/`#a1a1a6`. Text primary `#1d1d1f`, secondary `#424245`, muted
`#6e6e73`/`#86868b`, faint `#a1a1a6`; guide-body `#4a545e`. Green `#248a3d`; amber `#b0670a`;
neutral-badge `#8e8e93`. Badge: `padding:3px 11px; radius:999px; font-size:11.5px; weight:600`;
grade/verdict badges use `color+'22'` bg over solid color. Segmented: inactive `#86868b`, active
`#fff` + `box-shadow:0 1px 4px rgba(0,0,0,.1)`, track `#ededf0`. Fonts: Newsreader (500/600)
headings, Hanken Grotesk 15px base, IBM Plex Mono data/eyebrows/counters. Radius: inputs/chips 11,
cards 16, hero 20, buttons 10–12, pills 999.

### Responsive
≤960px: 3-col→2-col. ≤820px: wizard/sidebar + `1fr 1fr` collapse to single col; sticky aside +
summary bar unstick; header reorders. ≤600px: →1 col, H1 25px. ≤720px (`isMobile`, JS from
`window.innerWidth<=720` + resize): inline pills hide → everything into `More` as a 38×38 ☰ button
(→ ✕ accent when open) listing all nine tabs; Companion → ✦ icon only; phone header order logo ·
spacer · ✦ · ☰; segmented labels shorten. Animations: `fadeUp` (opacity + 10px rise, 0.3–0.4s).
