# Addendum 2026-09-24: conditioning snapshot pin

**Affects:** `docs/REGISTRATION_AMENDMENT_2026-09-23_V2.md`, item A10, which names conditioning pin `bcf39ca`.
**Registered requirement:** `docs/REGISTRATION_PCSO_MODEL_REGISTRY.md` §3 conditions the models on every draw dated on or before 2026-09-23.

## What changed
On 2026-09-24, commit `40c2bf5` changed the pin in `src/pcso_model_registry.py` to `1ce8541` to satisfy that requirement. The refreshed pin includes the newly added 6/45 draw #3000 and 6/55 draw #2491, both dated 2026-09-23.

No statistic, constant, threshold or seed changed. The only other harness change is the reworded `_meta.input_snapshot_note` (payload metadata).

## Evidence
`datasets/pcso-lotto/provenance/pcso_refresh_2026-09-24.json` records the two added draws and their source captures.

## Disposition
- **Registration text kept:** amendment v2 remains unchanged; this addendum records the pin update.
- **Recorded results kept:** the 2026-09-21 and 2026-09-23 leaderboard artifacts retain conditioning pin `bcf39ca` and replay from their recorded harness commits in `results/pcso_model_leaderboard_provenance.json`.
