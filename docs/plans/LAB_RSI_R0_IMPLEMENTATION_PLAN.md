# LAB-RSI-R0 Outcome Ledger (Observe) Implementation Plan

## §1 Status

Current stage: **IN PROGRESS (2026-09-06)** -- authored and executed in one
autonomous session under constitution article A0 (lab owner: "be autonomous").

| Field | Value |
|---|---|
| Parent requirements | `LAB-RELIABILITY-2026Q3` v1.3 Milestone R stage R0; controls `C11`, `C6`, `C10`; baseline `B9` |
| Governing article | `docs/THEOREM_GOVERNANCE.md` A0 (immutable), preserving A1--A8 |
| Workplan checkpoint | PR #23, merge commit `92dec2d487b90bb72370e866747736127f71ddf7` |
| Target branch | `feature/rsi-r0-outcome-ledger` |
| Pull request | filled at closeout (§15) |
| Executor altitude | `low` -- every MUST has a falsifiable test |

## §2 Episode Search Summary

Session-start trigger index (`em-trigger-index.mjs --merged`) returned no
critical entries for this project. Relevant standing lessons applied here:
always check the artefacts, never a tool's self-report (rows are derived from
verdict lines and exit codes, then cross-checked against files); a test that
runs code under a different runtime than production cannot catch runtime bugs
(the collector's tests drive the real scripts as subprocesses, not mocks, for
the fast sources).

Freshness checks performed: `src/grade_agent_eval.py` exposes `RECORDS`,
`GRADERS`, `grade_one()`; `src/design_verifier.py` prints
`design verifier: PASS|FAIL | ...` and exits 1 on violations;
`src/verify_ledger_integrity.py` prints `LEDGER INTEGRITY: OK|FAIL` and a
`N pass · N warn · N fail` line; five scripts expose `--verify` and print
`PASS sha256=<64 hex>; ...; wrote=none` on success; `tools/check.sh` and
`.github/workflows/ci.yml` run the same battery; agent definitions under
`agents/*.md` last changed in `6da211a` (2026-06-12) and `e1bc32b`
(2026-06-11), and the eval record directories were **added in the same commit
`6da211a`**, so `git show 6da211a:agents/<name>.md` hashes equal the working
tree today: the staleness check finds no stale definition at bootstrap. (An
earlier draft of this plan assumed seven stale definitions from the dates
alone; the blob hashes, not the dates, are the evidence.)

## §3 Objective

Deliver one append-only, schema-versioned outcome ledger that every existing
defect-signal source writes to through a single collector, plus a mechanical
gate that turns CI red when a new defect appears or an agent definition changes
without a fresh eval. R0 observes; it does not attribute (R1), propose (R2), or
merge (R3).

## §4 Requirements (Ground Truth)

| ID | Requirement (concrete, testable) | Parent | Test(s) | Priority |
|---|---|---|---|---|
| REQ-1 | `results/outcome_ledger.jsonl` rows conform to schema v1 (§8.1); `src/outcome_ledger.py --verify` exits 1 on any malformed row, non-monotonic `ts`, or unknown `source`/`signal`/`artifact_class`. | `C11`, `C6` | `test_schema_accepts_valid_row`, `test_schema_rejects_each_missing_field`, `test_verify_rejects_out_of_order_ts`, `test_verify_rejects_unknown_enum` | MUST |
| REQ-2 | Appends are atomic per batch (write to same-directory temp, `fsync`, `os.replace` of the full file) and never rewrite or drop an existing row. | `C6` | `test_append_preserves_prior_bytes`, `test_append_failure_leaves_prior_file_intact` | MUST |
| REQ-3 | A row is appended only when its state key `(source, artifact, signal, detail_hash)` differs from the latest row for the same `(source, artifact)`; repeated identical observations do not grow the ledger. | `C11` | `test_dedup_skips_identical_state`, `test_dedup_appends_on_state_change` | MUST |
| REQ-4 | The collector produces a row for every signal source in §8.3: each recorded agent eval, the design verifier, ledger integrity, each `--verify` entry point, and each pytest suite. | `C11`, R0.2 | `test_collect_fast_sources_emit_rows` (real subprocesses), `test_collect_verify_sources_parse_fixture_stdout` | MUST |
| REQ-5 | Each agent-eval row carries `agent_sha256_now` and `agent_sha256_at_eval`; when they differ the collector emits a `STALE_EVAL` defect row for that agent definition. | R0.3, `AGENT_WORKFLOW` eval gate | `test_stale_eval_detected_when_definition_changes`, `test_no_stale_row_when_hashes_match` | MUST |
| REQ-6 | `--gate` exits 1 iff at least one **new** defect row was appended in this run (a defect whose state key is absent from the ledger before the run); known open defects do not fail the gate. | R0 gate, plan §6 "fails on a new FAIL" | `test_gate_fails_on_new_defect`, `test_gate_passes_on_known_defect`, `test_gate_passes_when_clean` | MUST |
| REQ-7 | The collector never writes anywhere except the ledger path; the `--verify` entry points are invoked unchanged and leave `git status` bytes unchanged. | M0 REQ-1, `C6` | `test_collector_writes_only_ledger` | MUST |
| REQ-8 | `LAB_OUTCOME_LEDGER=<path>` redirects the ledger; CI sets it to a runner-temp path, uploads the file as a workflow artifact, and never dirties the checkout. | `C10` | `test_env_override_path`; CI run artifact present | MUST |
| REQ-9 | `tools/check.sh` and `.github/workflows/ci.yml` run `outcome_ledger.py --verify` and `outcome_collect.py --all --gate`; a deliberately altered agent definition turns the gate red with no human action. | R0 gate | `test_altered_agent_definition_turns_gate_red`; CI run on the PR | MUST |
| REQ-10 | Existing verifiers, tests, result hashes, ledgers, and `G0` wording are unchanged; `./tools/check.sh` passes before and after. | constraints 1-2 | `./tools/check.sh` output in §15 | MUST |

## §5 Non-Goals

- Attribution to an introducing commit (R1), any proposal or repair (R2--R4),
  lessons or re-tiering (R5).
- Re-dispatching agent evals (needs an LLM executor; any stale-eval rows this
  stage emits are the input to R2). At bootstrap no definition is stale (§2);
  five eval records grade `INCOMPLETE_RECORD` (thin 2026-06-11 records, info
  severity), also left for R2.
- Fixing defects the bootstrap surfaces. They are recorded as **known open
  defects** in the committed ledger (§15) with a diagnosis note; the fix is R2
  work unless it is a one-line, evidence-backed correction.
- Editing any instrument, verifier, or grader. The collector wraps them.
- A new JSON Schema framework (M2); schema v1 is a hand-checked dict contract.
- Committing ledger rows from CI. CI observes into an artifact; the committed
  ledger is appended by local closeouts, like the run ledger.

## §6 Token Budget

Three slices, one session, ~150k tokens total; §11 cut order applies if S2
parsing grows.

## §7 Safety / Security

| Threat | Mitigation | Test |
|---|---|---|
| Ledger rewrite hides a defect | Full-file atomic replace that must begin with the prior bytes; `--verify` checks monotonic `ts`; rows are never edited | `test_append_preserves_prior_bytes` |
| Silence closes a signal | Every source in §8.3 is enumerated in `SOURCES`; a source that fails to run yields an `ERROR` defect row rather than no row | `test_missing_source_yields_error_row` |
| Gate weakened by a stale baseline | Gate keys on state, not on exit code history; known defects stay visible as open rows in the committed ledger and in CI artifacts | `test_gate_passes_on_known_defect` (also asserts the row is still present) |
| Secrets in rows | Rows contain paths, hashes, verdict lines, counts; stdout is never stored whole | `test_row_contains_no_raw_stdout` |
| CI dirties the tree | `LAB_OUTCOME_LEDGER` points at `$RUNNER_TEMP` in CI | REQ-8 |

## §8 Design

### 8.1 Row schema v1

```json
{"schema_version": 1,
 "ts": "2026-09-06T09:12:33Z",
 "source": "agent_eval | design_verifier | ledger_integrity | verify_entrypoint | pytest | collector",
 "artifact": "agents/data-reader.md",
 "artifact_class": "agent | instrument | ledger | design | suite | collector",
 "signal": "PASS | FAIL | WARN | INCOMPLETE_RECORD | STALE_EVAL | ERROR",
 "severity": "info | defect",
 "evidence": "verdict line or record path (<= 300 chars)",
 "detail": {"...": "source-specific, JSON-serialisable"},
 "commit": "short sha or unknown",
 "executor": "LAB_EXECUTOR env, else user@host, else github-actions:<run_id>"}
```

`severity` is derived: `FAIL`, `STALE_EVAL`, `ERROR` -> `defect`; the rest
`info`. `detail_hash` (state key component) is SHA-256 of the canonical JSON of
`detail`.

### 8.2 Append and dedup

`append_rows(path, rows)` reads the existing file, computes the latest state
key per `(source, artifact)`, drops rows whose key matches, writes
`existing_bytes + new_lines` to a temp file, `fsync`, `os.replace`. Returns the
appended rows. Ledger order is append order; `ts` monotonic within a run.

### 8.3 Sources

| source | how | artifact | signal rule |
|---|---|---|---|
| `agent_eval` | import `grade_agent_eval`, iterate `RECORDS`, call `grade_one` (never `--write-rerun`) | `agents/<name>.md` from the eval-id prefix map (V, D, A, O, R, E, Q, X); Z-slice rows use `riemann-zero-lab/results/agent_runs/zeta-eval-20260613` as artifact, class `agent` | grade verbatim; `detail` = checks, recorded grade, record path, `agent_sha256_now`, `agent_sha256_at_eval` |
| `agent_eval` (staleness) | `git show <record-commit>:agents/<name>.md` hashed; record commit = first commit adding the record dir; if history is unavailable, the last ledger row's `agent_sha256_at_eval` | `agents/<name>.md` | `STALE_EVAL` when hashes differ |
| `design_verifier` | subprocess `src/design_verifier.py` | `docs/design_map` (the verifier's subject) | `PASS`/`FAIL` from the verdict line, `ERROR` if the line is missing |
| `ledger_integrity` | subprocess `src/verify_ledger_integrity.py` | `results/run_ledger.jsonl` | `OK`->`PASS`, `FAIL`, `WARN` when warnings > 0 and no fail |
| `verify_entrypoint` | subprocess each of the five scripts with `--verify` (`pcso_monitoring_run.py` with the refresh manifest) | the script path | `PASS` iff exit 0 and `^PASS sha256=[0-9a-f]{64}`; `detail.sha256` |
| `pytest` | subprocess the three suites from `check.sh` | suite path | exit 0 -> `PASS`; `detail.summary` = the `N passed` line |
| `collector` | self | `src/outcome_collect.py` | `ERROR` if any source raised |

Flags: `--sources a,b`, `--all`, `--gate`, `--ledger PATH` (or env), `--dry-run`
(print rows, append nothing).

## §10 Slice Ladder

| Slice | Objective | Primary files | Tests | Hard stops |
|---|---|---|---|---|
| `R0-S1` | Ledger library: schema, validate, atomic append, dedup, `--verify` | `src/outcome_ledger.py`, `tests/test_outcome_ledger.py` | REQ-1..3 | No collector, no CI. |
| `R0-S2` | Collector with all sources, staleness, gate; check.sh step; bootstrap ledger | `src/outcome_collect.py`, `tests/test_outcome_collect.py`, `tools/check.sh`, `results/outcome_ledger.jsonl` | REQ-4..7, 9 (local) | No CI edit; no instrument edits. |
| `R0-S3` | CI step + artifact; docs (workflow gates list, plan checkboxes, README ledger line) | `.github/workflows/ci.yml`, `docs/AGENT_WORKFLOW.md`, `docs/LAB_IMPROVEMENT_PLAN.md`, `README.md` | REQ-8, 9 (CI), 10 | No behavior change to existing jobs. |

`R0-S1 -> R0-S2 -> R0-S3`, one commit each.

## §11 Cut Order

1. `pytest` source rows (check.sh already fails on them) -- retain the other sources.
2. Z-slice agent-eval rows -- retain the eight `agents/*.md` rows.
3. `--dry-run` -- retain `--gate`.

Do not cut: atomic append, dedup, stale-eval detection, new-defect gate, CI
artifact, the bootstrap ledger with whatever known open defects it surfaces.

## §12 Contracts

- `validate_row(row) -> None` raises `ValueError` naming the first bad field.
- `state_key(row) -> tuple[str, str, str, str]`.
- `append_rows(path, rows) -> list[dict]` returns the rows actually appended.
- `verify_ledger(path) -> list[str]` returns problems (empty = OK).
- `collect(sources, root) -> list[dict]` never raises for a failing source; it
  returns an `ERROR` row for it.
- CLI exit codes: `outcome_ledger.py --verify` 0/1; `outcome_collect.py`
  0 unless `--gate` and a new defect was appended (1), or a usage error (2).

## §13 Edge Cases

- Empty or missing ledger: append creates it; `--verify` on a missing file is OK
  (no rows), on an empty file OK.
- Shallow CI checkout: `git show <commit>:path` fails -> fall back to the last
  ledger value; if none, emit `INCOMPLETE_RECORD` (info), never a guess.
- Grader raises for one record: that record's row is `ERROR`, others proceed.
- Two runs in the same second: `ts` ties are allowed (monotonic non-decreasing).
- A `--verify` entry point prints `PASS` but exits non-zero (or vice versa):
  `ERROR`, evidence names the contradiction.

## §14 Test Case Catalog

Named in §4. Fixtures: temp ledger paths, a temp copy of one agent definition
with one byte changed (REQ-5, REQ-9), captured stdout strings for the slow
`--verify` sources (REQ-4 parser test), a fake source script that exits 3
(§7 silence test). Fast sources run for real.

## §15 Verification Ledger (filled at closeout)

| Check | Command | Result |
|---|---|---|
| S1 unit suite | `.venv/bin/python -m pytest tests/test_outcome_ledger.py -q` | |
| S2 unit suite | `.venv/bin/python -m pytest tests/test_outcome_collect.py -q` | |
| Ledger verify | `.venv/bin/python src/outcome_ledger.py --verify` | |
| Bootstrap collect | `.venv/bin/python src/outcome_collect.py --all` | |
| Gate on known defects | `.venv/bin/python src/outcome_collect.py --all --gate; echo $?` | |
| Altered-definition red | temp edit of `agents/data-reader.md`, `--gate` -> 1, revert | |
| Full battery | `./tools/check.sh` | |
| CI | PR checks | |

## §17 Open Decisions

1. Whether local `check.sh` runs should append to the committed ledger (chosen:
   yes, dedup keeps it a state-transition log) or only to a scratch path.
2. Whether stale-eval defects should block merges once R2 can re-dispatch
   (deferred to R2; R0 records them as known open).
3. `check.sh` keeps its own verifier and pytest lines (hard failures) and adds
   the collector with `--all --gate` at the end, so the fast verifiers and the
   three suites run twice (~+60 s measured). Chosen over replacing the lines:
   the collector's gate is a ratchet and must not weaken `check.sh`.
4. CI seeds a runner-temp copy of the committed ledger before collecting, so
   "known" means known on the branch under test, and uploads the copy as the
   `outcome-ledger-<os>` artifact. Committing rows from CI is deliberately not
   done (§5).

## §18 Done Criteria

- [ ] Every MUST in §4 has its mapped test passing.
- [ ] Bootstrap ledger committed with one row per source observation and every
      defect it surfaced left visible as a known open row.
- [ ] `check.sh` and CI run the verify + collect steps; CI artifact uploaded.
- [ ] `./tools/check.sh` ALL CHECKS PASSED at closeout.
- [ ] §15 filled with real outputs; §19 records the review disposition.

## §19 Review Consensus

Filled at closeout.

## §20 Lessons Encoded

- Wrap, do not edit: instruments keep their `--verify` no-write contract; the
  collector is the only new writer.
- Ratchet, do not reset: the gate fails on new defects; known defects remain
  visible until a later stage closes them.
