# REGISTRATION CLARIFICATION C3 — 2026-09-28 — pcso.picker.prospective1 headline ticket

**STATUS: APPROVED 2026-09-28 (lab owner, in session: "Register float algorithm").** Prompted by GPT Astra 6's round-4 review of the frozen-law layer (finding R4-C). This file is commitment-hashed into `results/commitment_ledger.txt` before any prospective batch is anchored. No artifact has been anchored; nothing below reinterprets a locked forecast.

Clauses 6 and 18 require each artifact to commit tickets and their tie rules; clause 18 describes the headline ticket as the maximum-inclusion set, with ties favouring lower ball numbers. This clarification pins the arithmetic semantics.

**C3.** The committed headline ticket of a law is the output of the registered deterministic algorithm `ticket_from_inclusion` in `src/pcso_frozen_law.py`, at the code hash recorded in the artifact:

1. compute the binary64 inclusion probabilities π_i of the committed law q = r/M (amendment 2, C1) with the reference evaluator's `inclusion`;
2. make six sequential picks; each pick takes the lowest-numbered remaining ball whose π_i is at least (1 − 10⁻¹²) times the largest π among the remaining balls.

The result is an **approximate** maximum-inclusion set under a stated floating-point algorithm. Ties are decided on the **computed** binary64 inclusions: computed values within the tolerance are tied and resolve to lower ball numbers. Exact mathematical ties (for example the odd/even-symmetric parity law when the pool has equal numbers of odd and even balls, or identical log-weights) usually fall within the tolerance, but are not guaranteed to resolve to lower numbers when their computed values straddle the tolerance boundary; conversely, inclusions that differ by less than about one part in 10¹² may be treated as ties. The ticket is not certified to maximize exact expected overlap.

Tickets, their inclusion probabilities and overlap outcomes remain **descriptive** (clause 23). They enter no evidence process, confidence sequence, allocation or decision rule; all inference uses the complete committed law.
