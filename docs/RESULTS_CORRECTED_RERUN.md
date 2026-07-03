# RESULTS — Registered Corrected-Instrument Rerun (corrected_rerun_r1)

2026-07-03 · registration: REGISTRATION_CORRECTED_RERUN.md (sha
6668daa4bd5f38a5, approved by Cha, committed pre-run at 4ff1076) · artifact:
`results/corrected_rerun_r1.json` · seed 20260711 · two-run rule:
byte-identical PASS · prior shadow look disclosed in registration §0.

## Verdicts (NULL branch of §3 — all corrected thresholds respected)

| claim | statistic | raw p | corrected α | verdict |
|---|---|---|---|---|
| presence completion, 6/42 | skill 0.0034 | 0.0475 | .0102 (Šidák m=5) | NULL (raw sub-.05, above corrected; unremarkable at m=5) |
| presence completion, 6/45 | | 0.2625 | .0102 | NULL |
| presence completion, 6/49 | | 0.585 | .0102 | NULL |
| presence completion, 6/55 | | 0.2875 | .0102 | NULL |
| presence completion, 6/58 | | 0.9575 | .0102 | NULL |
| CCA std, 6/55 draws vs covariates | ρ₁ = 0.068 | 0.30 | .0253 (m=2) | NULL |
| CCA std, tidal vs ephemerides (positive control) | ρ₁ = 0.992 | 0.005 (floor) | — | mechanism detected — pipeline power intact under standardization |
| graphon attribution, 6/55 ex-ball-45 | B1 = 24.50 | 0.12 | declared .0025 | fire dissolves — #45-family attribution stands |

## What this settles

1. The three corrected instruments (audit M-2/M-3/M-4) are now REGISTERED
   evidence, replacing the uncitable 2026-07-02 shadow: the published
   relational verdicts are **ensemble-robust** — fixing the null ensemble,
   the standardization, and the attribution bias changes no conclusion.
2. The meta panel re-admits the presence family via this run's rows
   (panel v2.2, sha 8c7891b558ab8a28: 132 tests, discrete meta p = 0.032,
   10.6% ≤ .05 vs band [2.3%, 8.3%]) — the small-p excess persists and
   still concentrates in the known #45 family; no new anomaly language is
   licensed (attribution p = 0.12 re-confirms same-driving-rows).
3. Ledger: 7 test rows (row_type test), global_m recomputed 188 → 195;
   run-ledger row `corrected_rerun_r1` (G2 registered); reconciliation and
   all gates PASS.

Consistency note: shadow (seed 20260702) vs registered (seed 20260711)
p-values agree within Monte Carlo noise on every claim (e.g. attribution
0.148 → 0.12; HR3 0.345 → 0.30) — no seed-sensitivity signal.
