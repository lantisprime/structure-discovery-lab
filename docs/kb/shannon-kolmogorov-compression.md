# Shannon Source Coding, Kolmogorov Complexity & Compression Tests

**Domain face**: algorithmic

**Statement**:
- Shannon source coding theorem (1948): N i.i.d. symbols from a source of entropy H bits/symbol cannot be losslessly compressed below N*H bits on average; any code achieving fewer bits on typical sequences fails to be decodable.
- For a fair lottery on pool size P, each draw is uniform over C(P,6) combinations, so H = log2 C(P,6) bits/draw — for the PCSO pools, 22.3–25.3 bits/draw.
- Kolmogorov complexity K(x): the length of the shortest program producing x; a sequence is Martin-Löf random iff it is incompressible (K(x) >= |x| - O(1) for all prefixes). K is uncomputable; practical compressors give computable upper bounds on K.

**Assumptions**: for the entropy bound — the null model (i.i.d. uniform over combinations) is correct; for compression tests — the compressor's model class (e.g., DEFLATE: LZ77 repeats + Huffman symbol skew) covers the alternatives of interest; container/header overhead is removed or the comparison is against an identically-encoded null.

**Null value under i.i.d. uniform**: compressed size >= N * log2 C(P,6) bits minus o(N); empirical compression ratio of properly encoded draws matches that of simulated random draws; no compressor achieves systematic savings.

**Detects / blind to**: a one-sided certificate. If a compressor *does* shrink the data significantly below the entropy bound, structure exists (any structure the compressor's model class can represent: repeats, symbol bias, local correlations). Failure to compress proves nothing absolute — there could be structure outside the compressor's model class (K is uncomputable, so incompressibility can never be certified, only compressibility). Blind to structure invisible to LZ77/Huffman, e.g., parity constraints or permutation-invariant statistics, unless the encoding exposes them.

**Finite-sample cautions**: container formats (gzip headers, zlib checksums, block padding) add fixed overhead that swamps small files — raw DEFLATE streams must be used and compared against identically processed simulated nulls. Encoding choices change what is detectable (sorted vs unsorted numbers, delta coding, byte packing); each encoding is a separate hypothesis. Compression differences of a few bytes on ~776 draws are within null fluctuation; calibrate with Monte Carlo.

**Reference summary**:
Shannon's 1948 source coding theorem ties the best achievable lossless compression of a data stream to the entropy of its source: random data drawn uniformly from C(P,6) equally likely combinations carries exactly log2 C(P,6) bits per draw, and no representation can beat that on average without losing information. This converts "is the lottery random?" into an operational question: can any general-purpose compressor represent the draw history in fewer bits than the entropy bound?

Kolmogorov complexity deepens the link: the algorithmic information K(x) is the length of the shortest program generating x, and the Martin-Löf/Levin/Schnorr characterization identifies the algorithmically random sequences with the incompressible ones — those passing every effective statistical test. Since K is uncomputable, real compressors only provide upper bounds on K, making compression a one-sided certificate: significant compression certifies structure; incompressibility under a particular compressor merely fails to find structure of that compressor's kind.

In practice the test is: encode the draws compactly, compress with a raw DEFLATE stream (avoiding gzip/zlib container overhead that dominates at this data size), and compare the compressed size to the entropy bound and to the distribution of compressed sizes of simulated i.i.d. draws under identical encoding. Matching the null distribution across encodings is consistent with (but can never prove) algorithmic randomness.

**Canonical references**:
- https://en.wikipedia.org/wiki/Shannon%27s_source_coding_theorem
- https://en.wikipedia.org/wiki/Kolmogorov_complexity
- https://en.wikipedia.org/wiki/Algorithmically_random_sequence (Martin-Löf randomness)
- Li & Vitányi, *An Introduction to Kolmogorov Complexity and Its Applications*, Springer.
- Cover & Thomas, *Elements of Information Theory*, Ch. 5, 14.

**Use in this project**: Source coding bound H = log2 C(P,6) = 22.3–25.3 bits/draw across PCSO games; incompressibility interpreted via Martin-Löf randomness as a one-sided certificate; raw DEFLATE used to avoid container overhead. Compressed sizes matched the simulated null — no compressible structure found. Script: structure_discovery.py.
