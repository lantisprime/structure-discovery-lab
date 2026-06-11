# Per Bak Self-Organized Criticality & Universality Analysis

**Domain face**: cross-sectional/physical

**Statement**: Self-organized criticality (Bak, Tang, Wiesenfeld 1987): certain driven dissipative dynamical systems evolve toward a critical point as an attractor, without tuning of control parameters, and there display the scale invariance of a continuous phase transition: power-law (avalanche) size distributions P(s) ~ s^{-tau}, 1/f^a power spectra, and long-range correlations (Hurst H != 0.5). Universality/RG framework: near a critical fixed point, observables collapse onto scaling functions under rescaling (data collapse), block-coarse-grained statistics flow under the RG map, and dimensionless cumulant ratios such as the Binder cumulant U = 1 - <m^4>/(3<m^2>^2) are scale-invariant at criticality (curves for different system sizes cross), while off-critical systems flow to trivial fixed points (Gaussian/infinite-temperature: U -> 0 for a symmetric disordered phase, kurtosis flow to the Gaussian value).

**Assumptions**: a driven system with separation of timescales (slow drive, fast relaxation) and local interaction; for the diagnostics — stationarity, sufficient dynamic range to identify power laws, and finite-size scaling regime reached.

**Null value under i.i.d. uniform**: no SOC signatures: flat (white) spectrum, exponential/geometric avalanche-analog size distributions, H = 0.5 after estimator calibration, no data collapse beyond trivial CLT collapse, Binder-type cumulant ratios flowing to the trivial (infinite-temperature / Gaussian) fixed-point values at all block sizes.

**Detects / blind to**: detects critical-point physics in the data-generating mechanism — scale-free bursts, long memory, scale invariance — were the lottery machinery to behave like a driven threshold system. Blind to non-scale-invariant structure (a simple periodic bias or order-1 Markov stickiness is not SOC and is caught by other cards' instruments).

**Finite-sample cautions**: every SOC signature has an i.i.d. finite-sample mimic: R/S Hurst is biased upward (see hurst-rs-analysis card), short power-law-looking stretches arise in small log-log plots, and the Binder cumulant on few/short blocks can show a pseudo-plateau that imitates the size-independent crossing of criticality — in this project that pseudo-plateau appeared and was exposed as small-sample bias by calibration against simulated i.i.d. draws of identical length. All RG-flow diagnostics must be read relative to the simulated null flow, not absolute theoretical values.

**Reference summary** (distilled from fetched source — https://en.wikipedia.org/wiki/Self-organized_criticality):
Self-organized criticality is a property of dynamical systems that have a critical point as an attractor: their macroscopic behavior displays the spatial and temporal scale-invariance characteristic of a phase-transition critical point, but without any need to tune control parameters — the system effectively tunes itself as it evolves toward criticality. Bak, Tang and Wiesenfeld proposed the concept in 1987 ("Self-organized criticality: an explanation of the 1/f noise", PRL 59, 381) based on their sandpile model, where slowly added grains trigger avalanches of all sizes with power-law statistics.

The Wikipedia treatment emphasizes two cautions directly relevant here. First, despite enormous research output there is "no general agreement with regards to its mechanisms in abstract mathematical form" — SOC is identified through its signatures (avalanche power laws, 1/f-type spectra, long-range correlations), not a sharp theorem. Second, the signatures themselves are slippery: it was argued the BTW sandpile actually produces 1/f^2 rather than 1/f noise, with rigorous analysis showing 1/f^a with a < 2 and only the accumulated-stress dynamics exhibiting true 1/f; and claimed 1/f scaling in EEG has been argued to be inconsistent with critical states, leaving SOC-in-nature claims controversial. The lesson adopted in this project: each claimed signature must be tested against a calibrated null, since signature-mimicry is the norm.

For the lottery question, the SOC battery asks whether the draw mechanism behaves like a driven threshold system (it has no physical reason to, but the hypothesis was tested rather than dismissed): spectra were flat, avalanche-analog statistics geometric, calibrated Hurst at 0.5, and the RG-flow diagnostics (data collapse, block-kurtosis flow, Binder cumulant) all flowed to the trivial fixed point.

**Canonical references**:
- https://en.wikipedia.org/wiki/Self-organized_criticality
- Bak, Tang & Wiesenfeld, Phys. Rev. Lett. 59, 381 (1987).
- https://en.wikipedia.org/wiki/Binder_parameter
- https://en.wikipedia.org/wiki/Universality_(dynamical_systems)
- Jensen, *Self-Organized Criticality*, Cambridge (1998).

**Use in this project**: Full SOC-signature battery (1/f spectra, avalanche statistics, Hurst), plus universality diagnostics: data collapse, RG flow of block statistics, Binder cumulant. Verdict: the lottery sits at the trivial/infinite-temperature fixed point (no criticality). A Binder pseudo-plateau initially mimicked criticality and was caught as small-sample bias by null calibration. Scripts: perbak_soc_analysis.py, universality_collapse.py.
