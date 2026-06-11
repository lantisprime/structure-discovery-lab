# Graphons, Cut Norm & the Regularity Lemma

**Domain face**: cross-sectional/combinatorial limit

**Statement**:
- Lovász–Szegedy (2006): dense graph sequences (Gₙ) convergent in subgraph densities
  have a limit object, a graphon W: [0,1]² → [0,1], symmetric measurable. The space of
  graphons is compact under the cut metric δ□ — this compactness *is* Szemerédi's
  Regularity Lemma in analytic form.
- An Erdős–Rényi sequence G(n, p) converges a.s. to the constant graphon W ≡ p. Any
  exchangeable random graph is a W-random graph for some W (Aldous–Hoover).
- Cut norm ‖A‖□ = max_{S,T} |Σ_{i∈S,j∈T} A_ij| / n²; for symmetric matrices it is
  bounded above by the spectral norm: ‖A‖□ ≤ ‖A‖₂ / n (Frieze–Kannan), making λ_max of
  the centered adjacency a tractable, conservative proxy.

**Assumptions**: dense regime (edge density bounded away from 0); vertex-exchangeable
sampling for the W-random interpretation. Both hold for the co-occurrence graph here
(density 6·5 / (P(P-1)) per draw, accumulated over T draws → dense weighted graph).

**Null value under i.i.d. uniform**: the weighted co-occurrence graph of T draws
converges to the constant graphon W ≡ c with c = 30/(P(P-1)) per draw; the centered
co-occurrence matrix is a generalized Wigner-type noise matrix whose spectral norm has
a simulation-calibrated null band. The exactly-6-per-draw constraint induces a known
negative within-draw dependence (one trivial direction), so the null is drawn from the
constrained ensemble, never from G(n,p) formulas (A1).

**Detects / blind to**: detects block/community structure among balls — sets of numbers
that co-occur above or below rate (a non-constant limiting graphon), the discrete
trace of regularity-lemma structure. Blind to time-ordering (pools draws), and to
structure invisible in pairwise co-occurrence (higher-order only).

**Finite-sample cautions**: T ≈ 155 draws per game is far from the limit; the cut-norm
proxy via λ_max is conservative (can miss sparse cut structure the SDP relaxation would
see). Overlap with the MP/Tracy–Widom certificate is expected a priori — both are
spectral statistics of pairwise co-occurrence objects; the H-protocol null-correlation
measurement decides whether this instrument adds an independent test or joins the MP
equivalence class (registered in REGISTRATION_BATCH4.md).

**Canonical references**:
- https://en.wikipedia.org/wiki/Graphon
- Lovász & Szegedy, J. Combin. Theory B 96 (2006).
- Lovász, *Large Networks and Graph Limits*, AMS (2012).
- Frieze & Kannan, Combinatorica 19 (1999).

**Use in this project**: Instrument B (graphon_cooccurrence.py): B1 spectral norm of
centered co-occurrence matrix vs constrained null, plus equivalence-class measurement
against MP λ_max.
