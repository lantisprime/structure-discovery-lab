# Concentration of Measure & Sparse Recovery (Compressed Sensing)

**Domain face**: marginal/geometric — and the lab's only *exclusion* instrument

**Statement**:
- Hoeffding (1963): for n i.i.d. bounded variables, P(|p̂ − p| ≥ t) ≤ 2exp(−2nt²);
  with a union bound over P balls, simultaneous deviations of order
  sqrt(log(P)/n) are exponentially unlikely.
- Concentration of measure (Lévy, Milman): Lipschitz functions of many weakly
  dependent coordinates concentrate sharply around their means — the geometric engine
  behind "high dimension ⇒ rigidity".
- Candès–Romberg–Tao / Donoho (2006): if a bias vector β is s-sparse and the design
  satisfies RIP (which random designs do, *by concentration*), then ℓ₁-penalized
  estimation recovers its support from ~ s·log(P) observations.

**Assumptions**: bounded observations (indicator counts: yes); for the lasso, approximate
sparsity of any real bias (physically plausible: a defective ball or chamber slot
affects few numbers, not all).

**Null value under i.i.d. uniform**: every per-ball frequency lies inside the
simultaneous MC band around 6/P; the lasso at null-calibrated λ returns the empty
support on ≥ 99% of null replicates.

**Detects / blind to**: A1 *bounds* — it converts non-detection into the strongest
honest statement: "any persistent per-ball bias exceeds ε with probability < 5%",
with ε shrinking as ~1/√n. A2 detects sparse marginal bias constructively (names the
biased balls). Both are blind to temporal and combinatorial structure with exact
uniform marginals.

**Finite-sample cautions**: closed-form Hoeffding bands are loose for the constrained
6-of-P draw (negative dependence helps concentration); per A1 the simultaneous band is
simulated from the constrained ensemble, with Hoeffding kept only as an analytic sanity
ceiling. The lasso λ must be fixed on null simulations *before* seeing real data
(null-trial admission); λ tuned on real data is multiplicity laundering. The ε bound is
about per-ball marginals; EV translation assumes the bias acts through marginals.

**Canonical references**:
- https://en.wikipedia.org/wiki/Concentration_of_measure
- https://en.wikipedia.org/wiki/Compressed_sensing
- Hoeffding, JASA 58 (1963). Boucheron–Lugosi–Massart, *Concentration Inequalities*, OUP (2013).
- Candès, Romberg & Tao, IEEE Trans. IT 52 (2006).

**Use in this project**: Instrument A (concentration_exclusion.py): A1 simultaneous
95% exclusion bound ε per game + EV impact; A2 null-calibrated lasso support recovery.
The standing "no structure" verdict of Case Study 1 becomes quantitative: structure,
if any, is smaller than ε — and ε is worth less than the corresponding EV margin.
