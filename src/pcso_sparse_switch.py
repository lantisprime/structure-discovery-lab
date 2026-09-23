#!/usr/bin/env python3
"""Exact sparse conditional-Poisson experts with summable prior switching.

Approved dictionary: PCSO_MODEL_REGISTRY_PLAN.md §3c (research round 2).
The no-switch uniform path gives log E_T >= -log(2) - sum_{1 <= t < T} tau(t).
This module does not change the registered harness or its model roster.
"""
from __future__ import annotations

import argparse
from itertools import combinations, product
import math

import numpy as np
from scipy.special import logsumexp

from pcso_model_registry import K, POOL, top6

POOLS = tuple(POOL.values())
THETA = (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)
SIZE_PRIOR = {1: 2 / 3, 2: 1 / 3}


def _logcomb(n, k):
    return math.log(math.comb(n, k)) if 0 <= k <= n else -math.inf


def _log_prior(P, k):
    return math.log(0.1 * SIZE_PRIOR[k]) - _logcomb(P, k) - k * math.log(len(THETA))


def _tau(t):
    # Algebraically the specified difference; log1p avoids cancellation at large t.
    x = t + math.e - 1
    return math.log1p(1 / x) / (math.log(x) * math.log(x + 1))


class _Experts:
    """Rows share (k, theta); columns enumerate supports, with at most two indices."""

    def __init__(self, P, k):
        self.supports = np.array(list(combinations(range(P), k)))
        self.theta = np.array(list(product(THETA, repeat=k)))
        bits = np.array(list(product((0, 1), repeat=k)))
        hits = bits.sum(axis=1)
        tilt = self.theta @ bits.T
        terms = tilt + np.array([_logcomb(P - k, K - int(h)) for h in hits])
        logz = logsumexp(terms, axis=1)
        self.logz_ratio = logz - _logcomb(P, K)
        inside = np.exp(terms - logz[:, None]) @ bits
        outside_terms = tilt + np.array([_logcomb(P - k - 1, K - 1 - int(h)) for h in hits])
        self.outside = np.exp(logsumexp(outside_terms, axis=1) - logz)
        self.correction = inside - self.outside[:, None]
        self.logprior = _log_prior(P, k)

    @property
    def shape(self):
        return (len(self.theta), len(self.supports))

    def log_ratio(self, present):
        hits = present[self.supports]
        result = np.zeros(self.shape)
        for i in range(self.supports.shape[1]):
            result += self.theta[:, i, None] * hits[None, :, i]
        return result - self.logz_ratio[:, None]


class _GameState:
    """Deferred affine sharing: v_j = exp(scale) b_j + exp(inject) w_j.

    On other games every expert has likelihood ratio one. Its posterior update
    needs only these two scalars and the game's total mass, not its expert arrays.
    """

    def __init__(self, P):
        self.experts = tuple(_Experts(P, k) for k in SIZE_PRIOR)
        self.reset()

    def reset(self):
        self.base = [np.full(e.shape, e.logprior) for e in self.experts]
        self.scale, self.inject, self.mass = 0.0, -math.inf, math.log(0.1)

    def log_weights(self):
        return [np.logaddexp(b + self.scale, e.logprior + self.inject)
                for e, b in zip(self.experts, self.base)]

    def defer(self, factor, log_rho):
        self.scale += factor
        self.inject = float(np.logaddexp(self.inject + factor, log_rho))
        self.mass = float(np.logaddexp(self.mass + factor, math.log(0.1) + log_rho))


class SparseLaw:
    """Snapshot of one game's exact mixture, including all uniform contributions."""

    def __init__(self, P, experts, logweights, logoutside):
        self.P, self.experts = P, experts
        self.logweights, self.logoutside = logweights, logoutside
        self.logC = _logcomb(P, K)

    def _score(self, S):
        present = np.zeros(self.P, dtype=bool)
        present[np.asarray(S) - 1] = True
        terms = [lp + e.log_ratio(present) for e, lp in zip(self.experts, self.logweights)]
        logratio = float(logsumexp([self.logoutside, *(logsumexp(a) for a in terms)]))
        return logratio, terms

    def logq(self, S):
        return self._score(S)[0] - self.logC

    def inclusion(self):
        pi = np.full(self.P, math.exp(self.logoutside) * K / self.P)
        for e, lp in zip(self.experts, self.logweights):
            weights = np.exp(lp)
            pi += float(weights.sum(axis=1) @ e.outside)
            for i in range(e.supports.shape[1]):
                correction = (weights * e.correction[:, i, None]).sum(axis=0)
                pi += np.bincount(e.supports[:, i], weights=correction, minlength=self.P)
        return pi

    def top6(self):
        return top6(self.inclusion())


class CPSparseSwitch:
    name = "cp_sparse_switch"
    theory = "exact sparse conditional-Poisson mixture; summable switching (Koolen & de Rooij 2013, eq. 14)"
    dim = 2

    def __init__(self):
        self._games = {P: _GameState(P) for P in POOLS}
        self.t, self.log_uniform = 0, -math.log(2)

    def reset(self):
        self.t, self.log_uniform = 0, -math.log(2)
        for game in self._games.values():
            game.reset()

    def predict(self, P):
        game = self._games[P]
        outside = float(logsumexp([self.log_uniform,
                                  *(g.mass for Q, g in self._games.items() if Q != P)]))
        return SparseLaw(P, game.experts, game.log_weights(), outside)

    def update(self, P, S):
        logratio, terms = self.predict(P)._score(S)
        self.t += 1
        tau = _tau(self.t)
        log_rho = math.log(-math.expm1(-tau))
        factor = -tau - logratio
        self.log_uniform = float(np.logaddexp(self.log_uniform + factor, log_rho - math.log(2)))
        for Q, game in self._games.items():
            if Q != P:
                game.defer(factor, log_rho)
                continue
            game.base = [np.logaddexp(a + factor, log_rho + e.logprior)
                         for e, a in zip(game.experts, terms)]
            game.scale, game.inject = 0.0, -math.inf
            game.mass = float(logsumexp([logsumexp(a) for a in game.base]))


def _hit_logpmf(P, k, theta):
    terms = np.array([_logcomb(k, h) + _logcomb(P - k, K - h) + theta * h
                      for h in range(k + 1)])
    logz = float(logsumexp(terms))
    # Here Z_k is E_0 exp(theta H), unlike the unscaled expert partition.
    return terms - logz, logz - _logcomb(P, K)


def crossing_lower_bound(P, k, theta, n, threshold=100, pooled_T=1000):
    """Exact terminal-event lower bound on crossing, from the fixed expert path.

    All k support coordinates equal the specified grid value. H is the sum of n
    tilted hypergeometric support-hit counts (binomial for k=1). The prior pays
    for all k grid coordinates separately. The switch cost uses 1 <= t < pooled_T.
    """
    if k not in SIZE_PRIOR or theta not in THETA:
        raise ValueError("the crossing bound requires k in {1, 2} and theta in the approved grid")
    logpmf, logz = _hit_logpmf(P, k, theta)
    distribution = np.array([0.0])
    for _ in range(n):
        updated = np.full(len(distribution) + k, -math.inf)
        for h, probability in enumerate(logpmf):
            updated[h:h + len(distribution)] = np.logaddexp(
                updated[h:h + len(distribution)], distribution + probability)
        distribution = updated
    switch_cost = 1 - 1 / math.log(pooled_T + math.e - 1)
    required = math.log(threshold) - _log_prior(P, k) + switch_cost
    event = theta * np.arange(len(distribution)) - n * logz >= required
    return float(np.exp(logsumexp(distribution[event])))


def bw_second_moment(P, k, delta, n):
    """Exact E_0 W_n^2 for a uniform k-support mixture (reader equation G).

    Each support coordinate has log-weight delta. The overlap distribution of
    two independently uniform supports reduces the second moment to k+1 terms.
    """
    _, logz = _hit_logpmf(P, k, delta)
    terms = []
    for j in range(k + 1):
        logh = _logcomb(k, j) + _logcomb(P - k, k - j) - _logcomb(P, k)
        joint = [_logcomb(j, r) + _logcomb(2 * (k - j), s)
                 + _logcomb(P - 2 * k + j, K - r - s) + delta * (2 * r + s)
                 for r in range(j + 1) for s in range(2 * (k - j) + 1)]
        logg = float(logsumexp(joint)) - _logcomb(P, K) - 2 * logz
        terms.append(logh + n * logg)
    return float(np.exp(logsumexp(terms)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="print exact small-pool normalization checks")
    args = parser.parse_args()
    if args.selftest:
        # The law algebra is identical for small pools; no study is run here.
        for P in (8, 9, 10):
            game = _GameState(P)
            law = SparseLaw(P, game.experts, game.log_weights(), math.log(0.9))
            total = math.fsum(math.exp(law.logq(S)) for S in combinations(range(1, P + 1), K))
            pi = law.inclusion().sum()
            print(f"P={P}: sum q(S)={total:.15f}; sum inclusion={pi:.15f}")
            if abs(total - 1) > 1e-12 or abs(pi - K) > 1e-12:
                raise SystemExit("normalization check failed")


if __name__ == "__main__":
    main()
