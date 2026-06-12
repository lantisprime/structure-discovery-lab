"""lab core — domain-neutral instrument library.

This package is the forward-facing API for ALL new experiments. It contains
no domain vocabulary: no dataset names, no application strings. Domain
coupling lives exclusively in src/domains/<domain>.py.

The implementations are re-exported from the frozen historical modules to
guarantee zero behavior drift against ledgered results; new generic utilities
are defined here directly. Enforced by src/lint_domain_neutrality.py.
"""
from .stats import p_perm, gate_summary, sidak
from .discrete_draws import (fast_draws, presence, chi2_counts, mean_overlap,
                             half_deviation_corr, cooccurrence, uniform_draws,
                             DrawEnsembleSpec, std_spectrum, pair_test)
from .recovery import recovery_point, knn2_fast, fast_recovery_point
from .paired import ridge_cca_heldout, mmd_pvalue
from .geometry import (delay_embed, max_h1, embed_series, gw_test,
                       gw_distortion, matched_gaussian)
from .graphs import lap_spectrum, rewired, sbm_graph, spectral_distance
from .completion import soft_impute, col_permuted
