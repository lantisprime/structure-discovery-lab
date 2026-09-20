---
code: R4DRIFT
title: R4 source-drift fixtures and stale-hash detection for upstream inputs
version: 1
created: 2026-09-20
summary: >
  Add fixtures that simulate an upstream pcso.gov.ph HTML / GFZ Kp API
  structure change and a verifier that catches the drift at the adapter
  layer, not at a downstream instrument. Builds on the M4 substrate already
  shipped in PR #20/#24 (raw captures + sha256 manifests); does not redo
  that work. Acceptance: a simulated upstream structure change opens a
  FAIL row in the outcome ledger attributed to the parser/adapter file,
  not to a downstream instrument script.
---

# R4DRIFT — Source-drift fixtures for upstream pcso.gov.ph / GFZ Kp inputs

## Goal

When pcso.gov.ph HTML structure or the GFZ Kp JSON shape changes, the lab
must detect the change at the **adapter/parser** layer and emit a
ledger FAIL row whose `artifact` names the parser/adapter file — not a
downstream statistical instrument. Today the lab has no such detector: the
PCSO parser lives out-of-band (a one-shot in-session parse during PR #20)
and `make_kp_daily.py` would raise `KeyError` on a renamed GFZ key without
a typed message naming itself.

## Non-goals

- No live HTTP fetcher for pcso.gov.ph or GFZ Kp (the lab already declares
  this is manual; see `datasets/pcso-lotto/DATASET.md` §8).
- No rewrite of `pcso_weekly_update.py` / `pcso_monitoring_run.py` — they
  read CSVs, not HTML; their drift detection stays at the CSV/manifest
  level.
- No M4 mechanisms that are still PLANNED (holdout seal, role enforcement,
  second-implementation review, etc.).
- No change to the lab's R3 gate mechanics. The drift detector becomes
  one more `--verify` entry point (existing mechanism).

## Acceptance criteria

| id | criterion | how verified |
|---|---|---|
| AC-1 | A GFZ Kp raw JSON fixture with a renamed key (e.g. `Kp` → `kp_index`) is rejected by a typed adapter check whose error message names `make_kp_daily.py` and the missing key. | `pytest tests/test_source_drift.py::test_gfz_kp_drift_renames_key` exits 0 with the assertion; the captured `stderr` contains both substrings. |
| AC-2 | A PCSO manifest fixture with a tampered `sha256_uncompressed` against the captured raw bytes is rejected by a typed manifest check that names the capture id and the file. | `pytest tests/test_source_drift.py::test_pcso_manifest_drift_tampered_sha` exits 0; the captured `stderr` names `pcso_refresh_2026-09-06.json` and the offending capture id. |
| AC-3 | The same adapter checks against the **known-good** fixtures pass silently. | `pytest tests/test_source_drift.py::test_known_good_fixtures_pass` exits 0; both sub-cases produce no error. |
| AC-4 | A new verifier script `src/source_drift_check.py --verify` runs both checks against the live (committed) raw captures and exits 0; with a deliberate drift applied to a fixture copy it exits 1 with the typed error. | `src/source_drift_check.py --verify` exit 0 on HEAD; fixture copy drift → exit 1; exit code captured in `tests/test_source_drift.py::test_verifier_cli`. |
| AC-5 | The verifier is registered in `src/outcome_collect.VERIFY_ENTRYPOINTS`. A `replay` run that simulates a drift opens a ledger row whose `artifact` field is `src/source_drift_check.py` (the parser/adapter), NOT a downstream instrument like `src/meta_uniformity.py`. | `tests/test_source_drift.py::test_verifier_attributed_to_adapter` patches `VERIFY_ENTRYPOINTS`, runs `outcome_collect.run(["verify_entrypoint"])`, asserts the new FAIL row's `artifact == "src/source_drift_check.py"`. |
| AC-6 | The fixtures live in `tests/fixtures/source-drift/`, are committed to git, and are byte-stable (no timestamps). | `git ls-files tests/fixtures/source-drift/` returns the expected files; `find tests/fixtures/source-drift -newer .plans/R4DRIFT/spec.md -print` is empty. |
| AC-7 | The full test suite stays green: `pytest -q` exits 0 with the new tests passing alongside the existing 152+ tests. | `pytest -q` output captured, 0 failed. |

## Boundaries

- New files: `tests/fixtures/source-drift/{gfz_kp_known_good.json,gfz_kp_drifted_renamed_key.json,pcso_manifest_known_good.json,pcso_manifest_drifted_tampered_sha.json}`, `src/source_drift_check.py`, `tests/test_source_drift.py`.
- Edited files: `src/outcome_collect.py` (add one line to `VERIFY_ENTRYPOINTS`).
- Untouched: `make_kp_daily.py`, `pcso_weekly_update.py`, `pcso_monitoring_run.py`, `datasets/pcso-lotto/DATASET.md`, the raw provenance captures themselves.

## Acceptance gate R4 (the slice)

From LAB_IMPROVEMENT_PLAN v1.7 §5 Milestone R / R4:

> Gate R4: a simulated upstream HTML change and a simulated lockfile drift
> each end in a merged repair or an owner-routed decision.

This spec covers the upstream HTML/API slice. The lockfile-drift slice
belongs to M1 (scheduled clean-checkout replay) and stays in R4REPLAY-1.

## Amendments

(none)
