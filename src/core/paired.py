"""Paired/relational instruments: held-out CCA, kernel two-sample."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_first_run import ridge_cca_heldout
from relational_admission import mmd_pvalue
