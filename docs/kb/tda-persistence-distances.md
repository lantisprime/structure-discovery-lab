# Persistence Diagrams & Bottleneck Distance — Coordinate-Free Shape Comparison

**Domain face**: relational (topological correspondence; also subset-to-whole via witness complexes)

**Statement**:
- Persistent homology tracks connected components (H₀), loops (H₁), and voids (H₂)
  across a filtration (Vietoris–Rips here); each feature is a (birth, death) point in a
  persistence diagram.
- Stability theorem (Cohen-Steiner, Edelsbrunner & Harer 2007):
  d_B(D(f), D(g)) ≤ ‖f − g‖_∞ — small perturbations of the data move the diagram only
  a little. This is what makes diagrams *statistics* rather than artifacts.
- Diagrams are compared by bottleneck distance d_B (max matching cost) or
  q-Wasserstein distance (sum); both admit permutation/null calibration.
- de Silva & Carlsson (2004): witness complexes compute the topology of a landmark
  *subset* against the full data as witnesses — the subset-to-whole topology instrument.

**Assumptions**: the filtration scale is meaningful (distances comparable across
datasets after declared normalization); sampling density sufficient and *comparable* —
density differences alone create or destroy apparent loops. Point clouds only (here);
time series enter via declared delay embeddings (the embedding is a representation
choice, charged per A3).

**Null value under independence (relational H₀)**: against a matched-density random
geometric null (same n, same ambient dimension, same marginal scale), the observed
diagram-to-diagram distance between two unrelated datasets sits inside the null band;
"shared shape" requires the cross-dataset diagram distance to fall below the null's α
quantile. Noise clouds still produce many short-lived H₁ features — short bars are not
signal; only persistence relative to the null band is.

**Detects / blind to**: detects shared global shape — cycles (periodic orbits in delay
embeddings), branching, voids, component structure — without any shared coordinates.
Blind to identity: distinct spaces share diagrams (similarity ≠ isometry); blind to
density/geometry information not visible to homology; H₂ at small n is mostly noise.

**Finite-sample cautions**: Rips complexes are O(n²)–O(n³); subsample above n ≈ 1000.
Maximal filtration radius truncates bars (document it). Bottleneck distance is driven
by the single longest bar — robust to clutter, fragile to one spurious persistent
feature; report Wasserstein alongside. Witness-complex landmark choice (random vs
farthest-first) changes the diagram; both run in admission.

**Reference summary**: homology counts holes; persistence makes the count
scale-indexed and stable; diagram distances make it metric. The instrument answers
exactly one relational question: "do these two datasets (or this subset and its whole)
share global shape beyond what matched-density noise shows?" — never "are they the
same data?".

**Canonical references**:
- Cohen-Steiner, Edelsbrunner & Harer, "Stability of Persistence Diagrams," DCG 37 (2007).
- Edelsbrunner & Harer, "Persistent Homology — A Survey," Contemp. Math. 453 (2008).
- de Silva & Carlsson, "Topological Estimation Using Witness Complexes," SPBG 2004.
- https://en.wikipedia.org/wiki/Persistent_homology · Ripser.py: https://ripser.scikit-tda.org

**Use in this project**: relational instrument R4 (`relational_admission.py`):
admission E3 (circle vs matched-density blob: H₁ separation above null; blob vs blob:
silence) using Ripser. Intended real use: delay-embedded tidal series (strong loop
expected — the positive control on real data) vs delay-embedded draw features (no loop
expected — the i.i.d. control); witness-complex recovery curves in the §4 protocol.
