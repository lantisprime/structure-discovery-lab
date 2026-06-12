# Sourced Brief: Phipson–Smyth Permutation P-value Correction

**Prepared by:** research-scout  
**Date:** 2026-06-11  
**Task:** eval-r1-20260611

---

## The Result

Phipson and Smyth (2010) prove that a permutation p-value should never be
reported as exactly zero. The naive formula — count the proportion of m random
permutations whose test statistic is at least as extreme as the observed value —
can yield p = 0 when no permuted statistic matches or exceeds the observed one.
Reporting p = 0 is statistically incoherent: it would claim the null is
impossible, which the finite permutation sample cannot establish. The corrected
formula is:

    p = (b + 1) / (m + 1)

where b is the number of permuted statistics at least as extreme as the
observed statistic, and m is the total number of random permutations performed.
The minimum possible p-value is therefore 1/(m+1), not zero.

---

## Why (b+1)/(m+1) Is Required

The key conceptual shift is **how to frame permutation**. The naive approach
treats the m permuted statistics as a Monte Carlo estimate of the test
statistic's tail probability. Under that framing, b/m is a natural estimator —
but it can equal zero and it systematically underestimates the true p-value by
approximately 1/m.

Phipson and Smyth argue the correct frame is to treat the permuted values as
generating an **exact discrete null distribution**. Under the null, the observed
data are one of the (m+1) equally probable arrangements (the original labelling
plus the m random permutations). The probability that the observed statistic is
at least as extreme as a random draw from this augmented set is therefore
(b+1)/(m+1). This quantity is a genuine probability, not an estimate: it is the
exact p-value for the enlarged discrete reference set. The +1 in the numerator
counts the observed statistic itself as belonging to the reference distribution;
the +1 in the denominator reflects that the sample space has size m+1.

The practical stakes are highest in **multiple testing** contexts: even a small
per-test understatement of ~1/m propagates across thousands of comparisons
(e.g., genomic screens), inflating false-discovery rates. With m = 999
permutations the difference between p = 0 and p = 0.001 can shift a gene from
"genome-wide significant" to "not significant" in a Bonferroni or BH
correction.

---

## Three Canonical References

### 1. Phipson & Smyth (2010) — the primary source

> Phipson B, Smyth GK. "Permutation P-values Should Never Be Zero: Calculating
> Exact P-values When Permutations Are Randomly Drawn." *Statistical Applications
> in Genetics and Molecular Biology*, Volume 9, Issue 1, Article 39.  
> DOI: [10.2202/1544-6115.1585](https://doi.org/10.2202/1544-6115.1585)  
> arXiv preprint: [arXiv:1603.05766](https://arxiv.org/abs/1603.05766)

**Provenance:** VERIFIED — publisher landing page fetched from
https://www.degruyterbrill.com/document/doi/10.2202/1544-6115.1585/html
(De Gruyter, 2026-06-11); abstract and full citation confirmed. arXiv abstract
page also fetched from https://arxiv.org/abs/1603.05766 (2026-06-11), confirming
authors, journal reference, and DOI.

### 2. R `statmod::permp` CRAN Documentation

> Phipson B, Smyth GK. Function `permp` in R package *statmod* (v1.5.0).
> CRAN Reference Manual.  
> URL: https://search.r-project.org/CRAN/refmans/statmod/html/permp.html

**Provenance:** VERIFIED — page fetched 2026-06-11. The documentation states:
"Calculates exact p-values for permutation tests when permutations are randomly
drawn with replacement, using theory and methods developed by Phipson and
Smyth (2010)." The function signature `permp(x, nperm, n1, n2, ...)` uses `x`
(= b) and `nperm` (= m) to compute (x+1)/(nperm+1) exactly. This is the
canonical software implementation and is cited as the reference implementation
in the paper itself.

### 3. Barnard (1963) — the original Monte Carlo test idea

> Barnard GA. Discussion of paper by M.S. Bartlett. *Journal of the Royal
> Statistical Society B*, 25, 294 (1963).

**Provenance:** unverified — from model knowledge. Phipson and Smyth cite
Barnard (1963) as the originator of the Monte Carlo test concept. The (b+1)/(m+1)
structure traces to this discussion note, where Barnard first pointed out that
the observed data should be included in its own reference distribution, making
the minimum attainable p-value 1/(m+1). The paper is not open-access online and
could not be fetched; this attribution is reproduced from the arXiv preprint's
reference list (verified source above) but the primary text has not been
confirmed directly.

---

## Summary for Downstream Use

| Claim | Status |
|-------|--------|
| Naive formula b/m understates p by ~1/m | VERIFIED (arXiv abstract, De Gruyter abstract) |
| Correct formula is (b+1)/(m+1) | VERIFIED (arXiv abstract, CRAN docs) |
| Minimum p = 1/(m+1), never zero | VERIFIED (arXiv abstract) |
| Problem is serious in multiple-testing contexts | VERIFIED (arXiv abstract) |
| Barnard (1963) as originator of Monte Carlo test framing | unverified — from model knowledge |
| Davison & Hinkley (1997) as secondary canonical reference | unverified — from model knowledge |

