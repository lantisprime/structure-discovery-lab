"""k-of-P without-replacement draw ensembles: generators, presence matrices,
count statistics, co-occurrence spectra. Fully domain-neutral."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relational_batch5 import (cooccurrence, uniform_draws, std_spectrum,
                               pair_test, GameSpec as DrawEnsembleSpec)


def fast_draws(rng, T, P, k=6):
    """Vectorized T draws of k-of-P without replacement (argsort trick)."""
    return np.argsort(rng.random((T, P)), axis=1)[:, :k] + 1


def presence(nums, P):
    """T x P boolean presence matrix from draw rows (values 1..P)."""
    T = len(nums)
    Z = np.zeros((T, P), bool)
    Z[np.arange(T)[:, None], nums - 1] = True
    return Z


def chi2_counts(Z, P, k=6):
    cnt = Z.sum(0).astype(float)
    e = len(Z) * k / P
    return float(((cnt - e) ** 2 / e).sum())


def mean_overlap(Z):
    """Mean shared elements between consecutive draws."""
    return float((Z[:-1] & Z[1:]).sum() / (len(Z) - 1))


def half_deviation_corr(Z, P, k=6):
    """Correlation of per-element frequency deviations, first vs second half."""
    h = len(Z) // 2
    def dev(z): return z.sum(0) - len(z) * k / P
    return float(np.corrcoef(dev(Z[:h]), dev(Z[h:]))[0, 1])
