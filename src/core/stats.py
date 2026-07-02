"""Generic inference utilities (Phipson-Smyth correction, gates, corrections).

Audit minor #8 / adversarial review M-E (2026-07-02): this neutral core
module previously imported from frozen domain modules at module level
(remediation_r1 -> pandas/scipy/the whole relational stack), inverting the
dependency direction. The canonical implementations now live HERE; frozen
modules keep their historical copies for reproduction only.
"""
import numpy as np


def p_perm(obs, nulls):
    """Add-one (Phipson-Smyth) permutation p-value — the only sanctioned
    Monte Carlo p. p = (1 + #{null >= obs}) / (m + 1); p=0 is impossible."""
    nulls = np.asarray(nulls)
    return float((1.0 + np.sum(nulls >= obs)) / (len(nulls) + 1.0))


def sidak(alpha, m):
    """Family-corrected per-test threshold."""
    return 1 - (1 - alpha) ** (1.0 / m)


def gate_summary(*args, **kwargs):
    """n-trial FPR/uniformity calibration gate. Lazy import so that core
    does not drag the frozen relational stack in at import time; the
    implementation of record is remediation_r1.gate_summary (frozen)."""
    import os
    import sys
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))
    from remediation_r1 import gate_summary as _g
    return _g(*args, **kwargs)
