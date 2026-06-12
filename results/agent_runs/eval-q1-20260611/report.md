Report to orchestrator (rule-10 format, fields marked n/a where the gate stopped the run):

**Source claim + gate check**: Dispatch asked for a marginal-bias fit P(i ∈ D_t) = 6/49 + δ_i on PCSO Super Lotto 6/49. The Phase-5 hard gate (docs/EQUATION_DISCOVERY.md §1–§2; agent rule 1) requires a confirmed STRUCTURED source claim, post-freeze, with attribution on file. The 6/49 claim fails all three prongs:
- Detection verdict is **NULL**, not STRUCTURED — explicitly listed in EQUATION_DISCOVERY.md §2: "All PCSO lotto claims (5 games, all faces) | NULL | — | NO_EQUATION_ATTEMPTED". Corroborated by docs/RESULTS_BATCH4.md (6/49: faces inside null band, suspicious set empty, χ² p=0.3543, pair-sum p=0.3723) and docs/THEOREM_SYNTHESIS.md §5 (lotto null on all instruments; blind 9/9 verification returned NO STRUCTURE for all 5 lotto series).
- No human-approved REGISTRATION, commitment hash, declared λ/splits/nulls, or multiplicity charge exists for any eq.pcso-649 claim (rule 3).
- No attribution exists to consume — NULL verdicts produce none (failure mode #2).

**Registered family + hash**: none — registration was not created and must not be, since the source verdict gate fails upstream of registration.
**Null-equation generator**: not run (B = 0) — nulls are only run for admitted searches.
**Fitted equation(s)**: none. The dataset was not loaded. Any fitted |δ̂_i| would sit below the card-19 detectability floor (ε ≈ 0.162 ≈ 132% of 6/49 at n ≈ 155 draws) and is barred from being reported (rule 5); a good fit cannot upgrade a NULL detection verdict regardless (rule 1).
**Held-out vs null / residual checks / two-run reproducibility diff**: n/a — no fit executed.

**Verdict: NO_EQUATION_ATTEMPTED** (full stop, per rule 1).

Recorded in `docs/RESULTS_EQ_pcso-649-marginal.md`, including a **proposed** (not applied) run_ledger delta with multiplicity_charge 0 (a gate refusal is not a search). Dead-end log included per CLAUDE.md: the only PCSO anomaly on file is the era-bounded 6/55 #45 transient, which itself fails the gate (died Feb 2026, no post-freeze confirmation) and is not a 6/49 claim. The currently eligible Phase-5 work remains the three §2 calibration targets (tidal M2 ≈ 12.42 h, anomalistic month ≈ 27.55 d, pressure annual/diurnal).
