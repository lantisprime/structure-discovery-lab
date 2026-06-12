"""Generic inference utilities (Phipson-Smyth correction, gates, corrections)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_batch5 import p_perm                      # +1-corrected permutation p
from remediation_r1 import gate_summary                    # n-trial FPR/uniformity gate


def sidak(alpha, m):
    """Family-corrected per-test threshold."""
    return 1 - (1 - alpha) ** (1.0 / m)
