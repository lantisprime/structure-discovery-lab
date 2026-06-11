# Graph Matching, Spectra & Kernels — Comparing Relational Topology

**Domain face**: relational (graph-structured datasets)

**Statement**:
- Graph spectra: eigenvalues of adjacency/Laplacian are permutation-invariant
  summaries; cospectral ≠ isomorphic, but spectral distance is a usable, fast
  structural distance between graphs of different sizes (compare normalized-Laplacian
  spectral measures).
- Graph matching: find node correspondence π minimizing ‖A − P_π B P_πᵀ‖²_F — a
  quadratic assignment problem (NP-hard; relaxations: spectral, Umeyama, GW on
  shortest-path metrics).
- Community recovery: SBM fitting / modularity; two graphs "share community structure"
  if recovered partitions agree (ARI) above null.
- Like GW and CCA, matchers are optimizers: they **always return a matching**; only
  its position in a degree-preserving null distribution is evidence.

**Assumptions**: the graph encodes the relation of interest (here: co-occurrence of
numbers within draws — inherits the constrained-ensemble caveats of
`graphons-cut-norm.md`); for matching, node semantics are comparable across graphs;
dense-enough regime for spectral concentration.

**Null value under independence (relational H₀)**: spectral/matching/ARI statistics
against **degree-preserving rewiring** (configuration model) and SBM-with-matched-sizes
nulls. Erdős–Rényi at matched density is *forbidden as sole control* — it is too weak
(destroys the degree sequence, so almost anything "beats" it; the relational form of
C2's wrong-baseline error).

**Detects / blind to**: detects shared spectral profile, shared community structure,
shared motif statistics between two graphs. Blind to node identity unless matching is
validated against the null; blind to structure that degree sequence alone already
explains (by construction of the null); spectral distance blind to local differences
that don't move eigenvalues.

**Finite-sample cautions**: label-permutation symmetry means raw matching objectives
are meaningless absolutes. Spectral distances need same-support comparison (interpolate
spectral measures or compare top-k). Community detection has its own multiplicity
(algorithm, resolution parameter) — declare one, charge extras (A3). For weighted
co-occurrence graphs from few draws, eigenvalue noise is large: null bands from the
constrained generator, never asymptotics (C1).

**Reference summary**: a graph's spectrum is its "shape heard, not seen" — fast,
permutation-proof, incomplete. Matching tries to *see* the correspondence and pays for
it in search-space multiplicity, which the degree-preserving null prices. The
graphon/cut-norm instrument (ledger row 27) is the within-dataset ancestor; this card
extends the same machinery to *pairs* of graphs.

**Canonical references**:
- Umeyama, "An Eigendecomposition Approach to Weighted Graph Matching," IEEE TPAMI 10 (1988).
- Wills & Meyer, "Metrics for Graph Comparison: A Practitioner's Guide," PLoS ONE 15 (2020).
- Holland, Laskey & Leinhardt, "Stochastic Blockmodels," Social Networks 5 (1983).
- https://en.wikipedia.org/wiki/Spectral_graph_theory · graspologic: https://graspologic.readthedocs.io

**Use in this project**: relational instrument R5 (`relational_admission.py`):
admission E5 (two graphs from one SBM: spectra/ARI agree above degree-preserving null;
independent configuration-model graphs: silence). Intended real use: cross-game
co-occurrence-graph comparison (do 6/45 and 6/55 share community structure? expected:
no — both constant graphons), with the #45 pair-affinity shadow pre-registered as a
known driver (conflict C9).
