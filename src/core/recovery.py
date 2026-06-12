"""Subset-to-whole recovery instruments (temporal k-NN, recovery curves)."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_first_run import recovery_point


def knn2_fast(tS, yS, tH):
    """Vectorized 2-NN inverse-distance regression on a sorted time index."""
    idx = np.searchsorted(tS, tH)
    cand = np.clip(np.stack([idx - 1, idx, idx + 1]), 0, len(tS) - 1)
    d = np.abs(tS[cand] - tH[None, :]).astype(float)
    order = np.argsort(d, axis=0)[:2]
    cols = np.arange(len(tH))
    c2 = cand[order, cols]; d2 = d[order, cols]
    w = 1.0 / (d2 + 1.0)
    return (w * yS[c2]).sum(0) / w.sum(0)


def fast_recovery_point(y, frac, rng, m=199):
    n = len(y); t = np.arange(n)
    k = max(3, int(round(frac * n)))
    S = np.sort(rng.choice(n, size=k, replace=False))
    H = np.setdiff1d(t, S)
    def rmse(yy):
        return float(np.sqrt(np.mean((knn2_fast(S, yy[S], H) - yy[H]) ** 2)))
    obs = -rmse(y)
    nulls = [-rmse(y[rng.permutation(n)]) for _ in range(m)]
    return (1 + sum(x >= obs for x in nulls)) / (m + 1)
