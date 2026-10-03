# REGISTRATION CLARIFICATION C4 — 2026-10-03 — pcso.picker.prospective1 parity posterior normalization

**STATUS: APPROVED 2026-10-03 (lab owner, in session: "Approve both" — C4 and true-C3 next-draw
tickets).** Prompted by the 2026-10-03 frozen-law review (GPT Astra 6): the registered native parity
posterior has log-sum-exp 9.189538019427346e-12 after conditioning through 2026-10-02, exceeding the
frozen-law posterior-normalization tolerance. This file is commitment-hashed into
`results/commitment_ledger.txt` before its implementation is committed and before an artifact using
it is anchored. It applies to new snapshots only; no locked artifact is changed or reinterpreted (no
prospective artifact has been anchored).

Clause 6 and its Canonical law format require complete realized laws and native/reference agreement.
Amendment 2, C1 defines the committed law exactly as q = r/M and retains a certified
construction-quality mass gate. This clarification specifies the parity snapshot convention and the
corresponding native/reference comparison.

**C4.** When `freeze` snapshots a native `ParityLaw`, it copies the native posterior log-weights into
a binary64 array x, computes c = `_lse(x)` using the versioned reference implementation, and stores
the componentwise binary64 subtraction x' = x - c as the graph's `lp`. This operation applies
recursively to every embedded parity child. Allowed negative-infinity entries remain inactive. Native
model state, native registry classes, theta, the parity statistic, cached component normalizers,
mixture coefficients and the other realized children are unchanged.

The raw formula r is evaluated from the stored x', including its subtraction rounding. The committed
law remains exactly q = r/M, where M is the mathematical mass of that stored graph, enclosed by
`certified_mass`. Neither c nor a rounded mass or interval endpoint defines the committed law's exact
normalization. The existing parity posterior check and C1's certified mass interval requirement
[1 − 10⁻¹², 1 + 10⁻¹²] remain in force, as do all other eligibility and certified-score requirements.
Decoding validates stored bytes without renormalizing them.

In exact arithmetic, removing a common posterior scale leaves a standalone parity law r/M unchanged.
Binary64 subtraction can perturb relative posterior weights slightly. Within an ensemble, removing the
scale of a parity child also changes that child's raw contribution relative to the other children.
The prospective ensemble is expressly defined using these canonicalized embedded children, followed by
the whole graph's exact normalization under C1. This convention does not redefine the native ensemble
or any result of `pcso.registry.seq1`.

For clause 6's 1e-12 native/reference agreement check, the native comparison uses a shadow copy of
the same realized law with this normalization applied to each parity child, recursively, and with the
same mixture coefficients and other realized children. No new predictive samples are drawn. Raw log r
is compared with raw log r; certified committed-law scores use log r − log M. Agreement with the
uncanonicalized native parity or native ensemble raw score is not required.

C3 is unchanged: the committed ticket is `ticket_from_inclusion` applied to the reference evaluator's
binary64 inclusions of the stored graph's q = r/M. Native tickets do not substitute for that
calculation.

All evidence-process definitions, allocations, boundaries, the empirical-Bernstein center zero,
permanent-killing rules, estimands and descriptive-only treatment of tickets remain unchanged.
Snapshot normalization uses only information available before commitment.
