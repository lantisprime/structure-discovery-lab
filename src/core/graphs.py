"""Graph instruments: spectra, degree-preserving nulls, block models."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_admission import lap_spectrum, rewired, sbm_graph, spectral_distance
