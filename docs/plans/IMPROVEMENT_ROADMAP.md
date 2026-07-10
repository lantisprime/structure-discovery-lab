# Improvement Roadmap — executable plan (2026-07-08)

Written so ANY executor (human, or a small model with file+shell access) can
pick an item and complete it without repo archaeology. Rules for every item:
work from repo root on a branch; NEVER edit `FROZEN HISTORICAL RECORD`
scripts or existing ledger lines; after changes run `./tools/check.sh` and
require ALL CHECKS PASSED; commit with a message explaining WHY; open a PR.
Definition of done (DoD) is listed per item — do not stop before it.

## P1 — engineering, bounded, do first

### 1. UTF-8 the webapp I/O layer (Windows console gap)
Why: `webapp/server.py` helpers `rd()` (~line 48), `jl()` (~56), `jd()` (~63)
and direct `open()` calls (~612, 642, 826, 1447, 1791) read UTF-8 repo files
with the platform codec; on Windows (cp1252) `/api/doc`, approvals and
dataset meta crash on `→ λ ½` characters.
Steps: in `webapp/server.py`, add `encoding="utf-8"` to every text-mode
`open(` (display-only reads also get `errors="replace"`). Do NOT touch
binary `"rb"`/`"wb"` opens. Then remove the Windows skip in
`tests/test_webapp_smoke.py` (the `pytest.skip("console not certified on
Windows...")` block in the `server` fixture) so the smoke suite runs on the
Windows CI job.
DoD: `grep -n 'open(' webapp/server.py` shows no text open without
encoding; `python3 -m pytest tests/ webapp/test_server.py -q` green;
Windows CI job green (it is informational — check its log, not just the tick).

### 2. Joblog rotation
Why: `run_job` (webapp/server.py ~657, 784-788) writes
`webapp/joblogs/<ts>-<name>.log` forever; UI trims to 20 but disk grows
unbounded.
Steps: at job start, list `webapp/joblogs/*.log` sorted by mtime; delete all
but the newest 100 (constant `KEEP_LOGS = 100` near JOB_DEFS). Add a unit
test in `tests/test_webapp_smoke.py` that creates 105 dummy logs in a tmp
joblogs dir and asserts ≤100 survive a rotation call.
DoD: test green; full battery green.

### 3. Retire the CORE_SHIM_DEBT (6 files)
Why: `src/core/{recovery,completion,geometry,discrete_draws,graphs,paired}.py`
import frozen modules at module level (allowlist in
`src/lint_frozen_imports.py:36-38`) — live code inheriting frozen defects.
Steps: for ONE file at a time: copy the needed functions from the frozen
module into the core module verbatim (with a provenance comment naming the
frozen source), delete the frozen import, run
`python3 src/lint_frozen_imports.py` + `./tools/check.sh`. When all 6 are
done, empty `CORE_SHIM_DEBT` and change its handling from warning to
violation. NEVER edit the frozen modules themselves.
DoD: `CORE_SHIM_DEBT = set()`; lint reports 0 warnings; full battery green.

## P2 — data integrity & freshness (needs a network-enabled machine)

### 4. Finish nasa-power-manila onboarding (opens the pressure-claim gate)
Steps (laptop): `python3 datasets/nasa-power-manila/fetch_nasa_power.py`,
then `python3 datasets/nasa-power-manila/crosscheck_sources.py`; record the
printed overlap/r/mean-delta numbers in DATASET.md section 4; if r > 0.95
flip `Status:` to ACTIVE; snapshot:
`python3 tools/snapshot_commitment.py "nasa-power-manila ACTIVE"`.
DoD: card ACTIVE with recorded numbers; ledger integrity OK.

### 5. M4 closure — adjudicate the 3 suspicious PCSO rows (standing PENDING)
Why: `docs/REMEDIATION_LOG.md` M4 is the only open data-integrity item:
rows 2025-08-13 / 2025-09-03 / 2025-10-29 (6/55) need checking against
official PCSO records.
Steps (laptop): fetch the three official draw results from pcso.gov.ph (or
newspaper archives); write findings + source URLs into
`datasets/pcso-lotto/DATASET.md` section 7 and a short
`docs/RESULTS_M4_ADJUDICATION.md`; update REMEDIATION_LOG M4 status;
snapshot. Do NOT edit the audited CSV — the three-regime sensitivity
already handles inclusion/exclusion.
DoD: M4 marked FIXED with evidence links; docs verifier green.

### 6. Dataset refresh scripts + honest claims
Why: all covariate datasets end 2026-06-10/11; `datasets/pcso-lotto/DATASET.md`
claims a `pcso-weekly-update` scheduled task that DOES NOT EXIST in the repo.
Steps: (a) either commit a real `datasets/pcso-lotto/update_weekly.py`
(fetch → append to canonical CSV, never edit rows → print appended count) or
edit the DATASET.md claim to match reality; (b) add `refresh.py` to
gfz-kp-geomagnetic, jpl-horizons-sun-moon, openmeteo-pressure-manila reusing
their existing make_*/parse_* logic with an extended end date. Each refresh
appends; section 8 of each card documents the command.
DoD: no dataset card claims automation that isn't in the repo; refresh
scripts run (on laptop) or are clearly marked network-required.

### 7. tidal-manila: real fetch (it is a single-sample stub)
Steps (laptop): retry UHSLC/IOC bulk endpoints per the card's section 8;
if still empty, document the dead end in the card and mark Status
accordingly. Same pattern as item 4.

### 8. Pin the ephemeris constants derivation
Why: `datasets/pcso-lotto/make_astro_geomagnetic_1yr.py` hard-codes
empirically-recovered constants (C_moon, C_sun) + PyEphem 4.2.1; a version
bump silently drifts appended rows.
Steps: add a self-check to the script: recompute one known historical row
and `assert` byte-equal output before appending; document the constants'
derivation in a comment; add `ephem==4.2.1` to `constraints-recorded.txt`
if absent.
DoD: running the script on the recorded window reproduces the existing CSV
byte-identically.

## P3 — research program (each = its own registered run; follow the
GW template: PROPOSAL → owner approval → REGISTRATION → snapshot →
deterministic script → two byte-identical runs → ledger row → RESULTS doc)

### 9. PCSO refresh → first G5 confirmation decision
After item 6: refresh draws past 2026-06; when held-out ≥ the registered
threshold, present the owner the confirmation-family spend decision
(m=9, α′=0.0056). Never run confirmation without explicit owner approval.

### 10. R8 redesign (lag-max cross-correlation failed admission)
`docs/kb/INDEX.md` card #27 names the direction: coherence / Fourier-CCA.
Write PROPOSAL_R8_REDESIGN.md following PROPOSAL_GW_NULL_REDESIGN.md's
structure (problem-on-file, candidate designs, admission gates, decision
rule). Do not run anything before owner approval.

### 11. riemann-zero-lab batch 2 (fully offline-capable)
`riemann-zero-lab/README.md:90-98` lists five flagged next steps; the two
that run in this sandbox: (a) larger-N spacing for a Montgomery
pair-correlation test, (b) Li-coefficient positivity check. Register under
the module's own docs/, run deterministically, append to ITS run ledger.

### 12. Fresh eval set v2
Both blind sets are single-use (SEAL_NOTICE: unsealing voids them) and
eq_eval_set_v1 has no recorded run. Author `evals/structure_eval_set_v2/`
with a NEW sealed key (hash committed to the commitment ledger before any
dispatch), so the agent roster can be re-evaluated after any definition or
provider change. Verify the v1 verdict-hash commit actually landed.

### 13. Blind CLOUD-GW follow-through
`results/blind_eval_score.md:142`: CLOUD-GW-X|Y sensed signal at p=0.01 but
was G0-gated. With R2 now RETIRED (C12), write a one-paragraph note in the
blind-eval docs resolving that thread against C12 (the instrument family is
retired; the sensed signal stands as unverdictable exploratory) so no
reader mistakes it for a pending upgrade.

## Explicitly NOT planned
Windows as a supported platform (informational CI only); entropic-GW
onboarding (needs a fresh proposal); README restructure (works as is).
