# Second-opinion review brief — change set 8 (R4/R5 full), structure-discovery-lab

Sent 2026-09-08 to kimi-k3 via pi/LiteLLM (`pi -p --no-session --no-tools --no-extensions
--no-skills --no-prompt-templates --no-context-files --provider litellm --model kimi-k3`), followed
by the diff `git diff e7ebb96 HEAD -- src tests tools docs/AGENT_WORKFLOW.md` (78 KB, not
reproduced here). Reply: `R45_ROUND1_kimi-k3_2026-09-08.md`.

You are a READ-ONLY reviewer of a different model family than the author (Claude). Review the
code diff below for correctness, safety of the loop, and faithfulness to the plan. Do not edit.

## Context
Constitution A0 (prime directive): autonomous, self-learning, self-correcting, self-healing
recursive self-improvement. The loop: observe (outcome ledger, R0) -> attribute (bisection, R1)
-> heal (registered proposer in a git worktree, R4) -> gate (mechanical checks + different-family
verifier + owner-reserved routing, R3) -> learn (lessons ledger, R5). Constraint 6: constitution
edits, registrations, G3+ grade promotion and the gate's own machinery are owner-reserved; the gate
may not approve changes to itself. Frozen results under results/ are immutable; ledgers are
append-only.

## The plan's requirements (change set 8)
REQ-1 `outcome_collect.REPLAY_TARGETS` (script, args, outputs); source `replay` regenerates each in a
      temporary detached worktree at HEAD and byte-compares declared outputs: PASS / FAIL (both sha
      prefixes in evidence) / ERROR; subject = platform; working tree never modified.
REQ-2 `src/replay_check.py` reproduces the check in any checkout and restores the files;
      `check_command` maps `replay` to it so bisection, the healer's gate and the R3 gate run the
      same command. NOTE the author's deliberate deviation: the comparison is against the
      checkout's own copy of the output (not `git show HEAD:`), because in the healer's worktree
      the proposer's regeneration is uncommitted and IS the candidate; and the checker is invoked
      by absolute path from the lab root so a probe worktree at an old commit can run it.
REQ-3 A modified tracked results/ file is exempt from the frozen-results rejection iff it is a
      declared output of the defect's artefact — in the healer (`scope_violations`) and the gate
      (`scope_reasons`); a deleted declared output is still a rewrite.
REQ-4 `lab_gate.route_unhealable`: route to the owner as soon as the latest heal row is REJECTED at
      stage owner-reserved (notes in the issue); attempt-cap route stays; idempotent. The gate's
      OWNER-RESERVED check reads a flag LINE (not substring). The healer skips routed occurrences.
REQ-5 Heal row + agent.txt carry `lessons_sha256` (sha256 of the injected lessons' JSON lines,
      verbatim, in order — deviation from "lesson ids": lessons have no ids); record gets lessons.txt.
REQ-6 `agent_eval_dispatch --rolls N`; `src/lab_tier.py --recommend`: latest <= 5 rolls per (eval,
      tier); a tier is proven when EVERY eval of the agent has >= 3 rolls at it, all PASS; recommend
      a proven cheaper tier, or a proven higher tier when the current fails; < 3 rolls =
      "insufficient rolls"; the recommendation is a `tier` lesson, the frontmatter edit stays a PR.
REQ-7 Loop: `--all` includes replay; `lab_tier.py --recommend` after learn.
REQ-8 Append-only discipline unchanged.

## Live evidence so far (2026-09-08)
- replay observed the real stale results/meta_uniformity.json (committed 021c37dd, regenerated
  3d696051, byte-stable across runs); bisection attributed it in 9 steps to 9488a9a (a ledger
  append that never regenerated the panel).
- The sonnet proposer regenerated the panel inside the declared scope AND updated a pinned
  expected value (exploratory stratum n 7 -> 16) in src/verify_relational_docs.py, whose own
  comment had asked for exactly that rerun. The healer's gate passed; PR #34 opened.
- The R3 gate ROUTED PR #34 to the owner (issue #35): `src/verify_` is in GATE_MACHINERY_PREFIXES,
  so the loop may not self-approve a verifier change. The defect stays open until the owner decides.

## Questions
Q1 Correctness bugs in the diff (state a concrete failing input for each).
Q2 Does any change weaken a guardrail (frozen results, append-only ledgers, self-approval bar,
   different-family verifier), or open a way for a proposal to rewrite a results/ file it does not own?
Q3 The two deviations (checkout-copy comparison; absolute checker path): sound, or name the case
   they break.
Q4 The tier rules: any way a single lucky roll, or a stale old roll, produces a recommendation?
Q5 Is routing an owner-reserved stop on the first attempt the right behaviour, given the healer used
   to retry it up to the cap?
Q6 Anything in the diff you would not merge as is.

Answer with numbered findings, each: severity (MUST/SHOULD/NIT), file:line or function, the issue,
why it matters, the concrete change. End with one line: VERDICT: APPROVE | APPROVE-WITH-CHANGES | REJECT.
