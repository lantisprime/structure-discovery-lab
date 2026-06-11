# Covering Designs & the Lottery Problem

**Domain face**: algorithmic

**Statement**: The lottery number L(n, k, p, t) is the minimum number of tickets (k-subsets of an n-set) needed to guarantee that, whatever p-subset is drawn, at least one ticket matches it in at least t numbers. Equivalently a covering-design problem: the tickets must form a set system such that every p-subset of [n] is t-intersected by some ticket. Cushing & Stewart (2023) proved L(59, 6, 6, 2) = 27 for the UK National Lottery: 27 tickets suffice (constructed from three Fano-plane-based blocks on a partition of the 59 numbers) and 26 do not (lower bound via partitioning arguments). Trivial pairwise bound: two disjoint tickets both jackpot-miss-able; the probability that a fixed pair of disjoint tickets both hit anything is constrained by the disjoint-pair rule — each ticket individually wins the jackpot with probability 1/C(n,6), and disjoint tickets give combined jackpot probability exactly 2/C(n,6) (no overlap synergy).

**Assumptions**: pure combinatorics — no probabilistic assumptions at all; the guarantee is worst-case over all possible draws. Guarantees concern *matching counts*, not prize value.

**Null value under i.i.d. uniform**: not applicable as a statistical test — covering designs are deterministic guarantees. Under a fair draw, every individual ticket retains jackpot probability 1/C(n,6) regardless of how cleverly the ticket set covers; covering only reshapes the joint distribution of small-match counts.

**Detects / blind to**: not a detector. It answers "what is the cheapest guarantee of a t-match?" Blind to (and silent about) expected value: guaranteeing a 2-match says nothing about profit, because 2-matches pay little or nothing.

**Finite-sample cautions**: exact lottery numbers are known only for limited parameter ranges (Cushing–Stewart cover n <= 70 for k = p = 6, t = 2); for other PCSO pool sizes only upper bounds from explicit partition-based constructions and lower bounds from counting arguments are available, so quoted ticket counts for PCSO games are estimates between bounds, not proven optima. The guarantee collapses if even one ticket is mis-specified.

**Reference summary** (distilled from fetched source — https://arxiv.org/abs/2307.12430, Cushing & Stewart, "You need 27 tickets to guarantee a win on the UK National Lottery"):
Cushing and Stewart "develop and deploy a set of constraints for the purpose of calculating minimal sizes of lottery designs. Specifically, we find the minimum number of tickets of size six which are needed to match at least two balls on any draw of size six, whenever there are at most 70 balls." For the UK lottery's 59-ball game the answer is exactly 27: their construction partitions the 59 numbers into structured groups and builds tickets from Fano plane (PG(2,2)) incidence structures, whose property that every pair of points lies on a line translates into every drawn pair within a group being captured by some ticket; matching lower-bound arguments show 26 tickets always leave an uncovered draw.

The headline irony, emphasized by the authors, is decision-theoretic: the guaranteed win is a 2-match, which in the UK game pays a free lucky dip (and in PCSO games pays little or nothing), so the guarantee is essentially worthless — one can guarantee *a* win but not a profit. Covering designs optimize the worst case of match counts, while expected value is fixed by the prize structure and is negative per ticket regardless of the design.

Adapted to this project, partition-based constructions in the Cushing–Stewart style give estimated minimal ticket counts of roughly 13, 15, 19, 23, and 26 tickets for the PCSO pool sizes (6/42 through 6/58) to guarantee a 2-match — each guaranteeing only a worthless outcome. The disjoint-pair rule (combined jackpot probability of two disjoint tickets is exactly 2/C(n,6)) makes the complementary point: spreading tickets adds probabilities linearly and can never manufacture an edge.

**Canonical references**:
- Cushing & Stewart, "You need 27 tickets to guarantee a win on the UK National Lottery", https://arxiv.org/abs/2307.12430
- https://en.wikipedia.org/wiki/Lottery_mathematics
- https://en.wikipedia.org/wiki/Covering_design
- La Jolla Covering Repository: https://www.dmgordon.org/cover/
- https://en.wikipedia.org/wiki/Fano_plane

**Use in this project**: Cushing–Stewart 2023 (arXiv 2307.12430): L(59,6,6,2) = 27 via Fano planes. Partition-based estimates for PCSO pools: roughly 13/15/19/23/26 tickets to guarantee a (worthless) 2-match across the game sizes. Disjoint-pair rule: two disjoint tickets give jackpot probability exactly 2/C(n,6) — coverage cannot create expected value.
