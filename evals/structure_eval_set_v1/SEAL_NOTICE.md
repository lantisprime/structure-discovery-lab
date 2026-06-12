# SEAL NOTICE — 2026-06-11
answer_key/, src/GENERATION_NOTES.md, src/quick_probe.py, and manifest.json are
SEALED until the lab's verdicts are hash-committed (results/blind_eval_verdicts.json
+ commitment ledger entry). Unsealing before that voids the eval. Scoring happens
only after the verdict hash is recorded. This eval is a permanent part of the lab's
eval suite (methodology level, complementing agents/evals/ at the agent level).
