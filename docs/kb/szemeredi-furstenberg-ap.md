# Szemerédi's Theorem & the Furstenberg Correspondence

**Domain face**: marginal/combinatorial (with an ergodic-theoretic proof route)

**Statement**:
- Szemerédi (1975): every subset A ⊆ ℕ with positive upper density contains arithmetic
  progressions of every finite length k.
- Furstenberg correspondence (1977): statements about dense integer sets translate to
  multiple-recurrence statements about measure-preserving systems; Szemerédi's theorem
  is equivalent to: for any m.p.s. (X, μ, T) and A with μ(A) > 0, there is n with
  μ(A ∩ T⁻ⁿA ∩ … ∩ T⁻⁽ᵏ⁻¹⁾ⁿA) > 0.
- Green–Tao (2008): the primes (density zero, but pseudorandom) contain arbitrarily
  long APs — density *or* sufficient pseudorandomness forces progressions.

**Assumptions**: none beyond density — that is the entire point. The theorem is
unconditional: no randomness, independence, or distributional assumption is needed.

**Null value under i.i.d. uniform**: APs appear at a calculable baseline rate. For a
single draw of 6 distinct numbers from {1..P}, the expected number of 3-term APs
(unordered {a, a+d, a+2d}, d ≥ 1) is C(6,3) · q(P) where q(P) is the probability a
uniform random 3-subset is an AP: q(P) = #AP₃(P) / C(P,3), #AP₃(P) = ⌊(P-1)²/4⌋
rounded per parity (= Σ_d (P - 2d)). Exact null distributions are simulated, not
asymptotic (A1).

**Detects / blind to**: two-sided deviation in AP abundance — excess (additive
structure in the source, e.g. mechanical periodicity in ball selection) or deficit
(an AP-avoiding filter, e.g. human curation of "random-looking" outcomes; genuine
draws are never curated, but data-entry or generation shortcuts can be). Blind to any
structure that preserves AP counts.

**Finite-sample cautions / the Ramsey trap**: Szemerédi *guarantees* progressions in
any dense set. The top-k "hot numbers" of any window are a dense subset of {1..P}
(density k/P ≈ 0.17–0.24 here), so finding APs among hot numbers is theorem-forced,
not evidence of bias. Under H₀ a random 10-subset of {1..42} contains ≈ 3.5 three-term
APs on average (simulated value recorded in the batch-4 log). Any analyst claiming
"the hot numbers form a progression" must beat the *simulated* AP baseline, two-sided,
with multiplicity accounting — otherwise they have rediscovered a 1975 theorem.
This is failure-mode gallery entry: **the Ramsey trap** — patterns that density alone
forces into existence, independent of any mechanism.

**Canonical references**:
- https://en.wikipedia.org/wiki/Szemer%C3%A9di%27s_theorem
- Furstenberg, J. d'Analyse Math. 31 (1977).
- Green & Tao, Ann. of Math. 167 (2008).

**Use in this project**: Instrument C (szemeredi_ap.py): C1 within-draw AP₃ counts,
C2 hot-set AP₃ counts, both MC-calibrated two-sided. Registered in
REGISTRATION_BATCH4.md.
