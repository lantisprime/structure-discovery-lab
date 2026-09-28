"""Hierarchical sign-sharing reset filter, registered as pcso.signshare.seq1."""
import itertools
import math

import numpy as np
from scipy.special import logsumexp

import pcso_model_registry as R


POOLS = (42, 45, 49, 55, 58)
AMPS = (0.0, 0.025, -0.025, 0.05, -0.05, 0.10, -0.10)
PI_A = (0.10, 0.09, 0.09, 0.27, 0.27, 0.09, 0.09)
HAZ = (0.0, 1 / 256, 1 / 1024)
PI_H = (0.8, 0.1, 0.1)
SIGNS = [(1,) + rest for rest in itertools.product((1, -1), repeat=4)]
PI_S = np.asarray([0.8 * (s == 0) + 0.2 / 16 for s in range(16)])
C7 = tuple(sorted(set(AMPS)))


class SignShareFilter:
    name = "signshare_seq1"

    def __init__(self):
        self.w = np.einsum("h,s,a->hsa", PI_H, PI_S, PI_A)
        self.phi = {P: R.features(P)[0] for P in POOLS}
        self.coef = {
            P: np.asarray([[AMPS[a] * SIGNS[s][POOLS.index(P)] for a in range(len(AMPS))]
                           for s in range(len(SIGNS))])
            for P in POOLS
        }
        self.logw_c = {}
        self.loge6_c = {}
        for P in POOLS:
            self.logw_c[P] = {c: c * self.phi[P] for c in C7}
            self.loge6_c[P] = {
                c: math.log(R.esp(np.exp(self.logw_c[P][c][None, :]))[0, R.K])
                for c in C7
            }

    def _collapse(self, w, P):
        weights = np.asarray([
            w[:, self.coef[P] == c].sum() for c in C7
        ])
        return R.Law(np.vstack([self.logw_c[P][c] for c in C7]), weights)

    def predict(self, P):
        self._validate_pool(P)
        return self._collapse(self.w, P)

    def predict_batch(self, P, j):
        self._validate_pool(P)
        self._validate_count(j, minimum=1)
        wj = self._transition_power(self.w, j - 1)
        return self._collapse(wj, P)

    def update(self, P, S):
        self._validate_pool(P)
        if S is None:
            self.w = self._transition_power(self.w, 1)
            return
        try:
            draws = tuple(S)
        except TypeError as exc:
            raise ValueError("S must contain six distinct integers") from exc
        if (len(draws) != 6
                or any(not isinstance(x, (int, np.integer)) or isinstance(x, (bool, np.bool_)) for x in draws)
                or len(set(draws)) != 6
                or any(x < 1 or x > P for x in draws)):
            raise ValueError("S must contain six distinct integers in 1..P")
        idx = np.asarray(draws) - 1
        logf = np.asarray([
            self.logw_c[P][self.coef[P][s, a]][idx].sum()
            - self.loge6_c[P][self.coef[P][s, a]]
            for s in range(len(SIGNS)) for a in range(len(AMPS))
        ]).reshape(len(SIGNS), len(AMPS))
        w_new = self.w * np.exp(logf)[None, :, :]
        w_new /= w_new.sum()
        self.w = self._transition_power(w_new, 1)

    @staticmethod
    def _transition_power(w, j):
        SignShareFilter._validate_count(j, minimum=0)
        tot = w.sum(axis=2, keepdims=True)
        decay = (1 - np.asarray(HAZ)) ** j
        return (decay[:, None, None] * w
                + (1 - decay)[:, None, None] * np.asarray(PI_A)[None, None, :] * tot)

    @staticmethod
    def _validate_pool(P):
        try:
            valid = P in POOLS
        except TypeError:
            valid = False
        if not valid:
            raise ValueError("P must be one of the registered pools")

    @staticmethod
    def _validate_count(j, minimum):
        if (not isinstance(j, (int, np.integer)) or isinstance(j, (bool, np.bool_))
                or j < minimum):
            raise ValueError(f"j must be an integer >= {minimum}")

    def advance(self, k=1):
        self._validate_count(k, minimum=0)
        self.w = self._transition_power(self.w, k)

    def checkpoint(self):
        return self.w.copy()

    def restore(self, ckpt):
        message = "checkpoint must be a finite float64 probability array of shape (3, 16, 7)"
        if not isinstance(ckpt, np.ndarray) or ckpt.dtype != np.dtype(np.float64):
            raise ValueError(message)
        w = ckpt.copy()
        if (w.shape != (3, 16, 7) or not np.all(np.isfinite(w)) or np.any(w < 0)
                or abs(math.fsum(w.ravel()) - 1.0) > 1e-12):
            raise ValueError(message)
        self.w = w

    def replay(self, ckpt, events):
        """Replay observations from a saved checkpoint.
        Events must be in event order; availability/refresh timing is the caller's responsibility.
        Never append a late outcome after later events.
        """
        self.restore(ckpt)
        for P, S in events:
            self.update(P, S)

    def marginals(self):
        return {"hazard": self.w.sum(axis=(1, 2)),
                "sign_all_positive": self.w[:, 0, :].sum()}
