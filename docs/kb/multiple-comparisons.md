# Multiple Comparisons: Bonferroni, Benjamini-Hochberg, Forking Paths

**Domain face**: statistical

**Statement**:
- Bonferroni: testing m hypotheses, rejecting when p_i <= alpha/m controls the family-wise error rate FWER <= alpha for arbitrary dependence (union bound).
- Benjamini–Hochberg: order p_(1) <= ... <= p_(m); reject all hypotheses up to the largest k with p_(k) <= (k/m) * alpha; controls the false discovery rate FDR = E[V/max(R,1)] <= alpha under independence or positive regression dependence.
- Equivalence-class accounting: m must count *independent hypothesis classes actually entertained*, not raw statistics — statistics that are deterministic transforms or near-duplicates of one another belong to one class.
- Garden of forking paths (Gelman & Loken): even with one reported test, data-dependent analysis choices implicitly multiply m; the remedy is pre-registration of statistic, family, and decision rule before looking.

**Assumptions**: valid marginal p-values; for BH, independence or PRDS dependence (BH-Yekutieli with sum 1/k correction covers arbitrary dependence). Honest enumeration of the family, including informal looks.

**Null value under i.i.d. uniform**: each p_i ~ Uniform(0,1); expected number of p < 0.05 among m tests is 0.05m; minimum p among m independent tests has distribution 1-(1-p)^m, so min-p ~ 1/m is typical, not surprising.

**Detects / blind to**: this is a control framework, not a detector — it preserves error guarantees when many instruments are run. It is "blind" (loses power) when m is inflated by counting redundant statistics as separate hypotheses, hence equivalence-class counting; conversely it fails silently when m undercounts paths actually explored.

**Finite-sample cautions**: Bonferroni is conservative under strong positive dependence among tests (common here: overlapping statistics on the same 776 draws); permutation-based max-statistic calibration (see scan-statistics card) is sharper. BH guarantees average FDR, not per-experiment; with small m and discrete Monte Carlo p-values, the BH step-up can be granular.

**Reference summary**:
When many hypotheses are tested, the probability of at least one false positive grows toward 1; with m = 25 instrument families at alpha = 0.05 one expects ~1.25 "significant" results from pure noise. Bonferroni's union-bound correction is the simplest valid control of the family-wise error rate and is robust to any dependence, at a cost in power. Benjamini and Hochberg (1995) introduced the false discovery rate — the expected fraction of rejections that are false — as a less stringent, more powerful target appropriate for screening regimes.

A subtler issue, articulated by Gelman and Loken as the "garden of forking paths," is that multiplicity arises not just from tests reported but from analysis decisions contingent on the data: which statistic to use, which subgroup to examine, which transform to apply. A single reported p-value at the end of such a path does not have its nominal distribution. The defenses are pre-registration (fixing the statistic family and decision thresholds before analysis) and global calibration of the whole search procedure (the scan-statistic approach).

Counting m correctly requires equivalence-class accounting: m is the number of genuinely distinct hypothesis classes, not the number of computed numbers. E.g., a Zipf rank-frequency slope and a chi-square uniformity statistic on the same counts are one class (see power-laws card: Zipf slope is chi-square in disguise); counting both as separate tests would double-penalize, while treating ad-hoc variants of one idea as one pre-registered test would under-penalize.

**Canonical references**:
- https://en.wikipedia.org/wiki/Bonferroni_correction
- https://en.wikipedia.org/wiki/False_discovery_rate (Benjamini & Hochberg 1995)
- Gelman & Loken, "The garden of forking paths" (2013), http://www.stat.columbia.edu/~gelman/research/unpublished/p_hacking.pdf
- https://en.wikipedia.org/wiki/Multiple_comparisons_problem

**Use in this project**: Bonferroni/BH applied with equivalence-class accounting (m counts hypothesis classes, not statistics), explicit garden-of-forking-paths discipline, and pre-registration of confirmation tests. Family sizes used: m = 9 (confirmation battery), m = 15 (Markov family), m = 18 (scaling-law family).
