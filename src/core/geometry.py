"""Intrinsic-geometry instruments: delay embeddings, persistence, GW.
NOTE: GW carries a standing calibration flag (exploratory-only, G0)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_batch5 import delay_embed, max_h1
from relational_batch7 import gw_test, embed_series
from relational_admission import gw_distortion, matched_gaussian
