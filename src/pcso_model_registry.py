#!/usr/bin/env python3
"""PCSO model registry: reusable prediction models behind one interface, one deterministic harness,
and CP-NEST (nested conditional-Poisson tilts, online Laplace posterior, fixed-share mixing).
Design and theory: docs/plans/PCSO_MODEL_REGISTRY_PLAN.md. G0 exploratory until registered.

Interface. A model exposes `name`, `theory`, `dim`, `predict(P) -> Law` and `update(P, S)`, called in
that order for every draw (predictive first, then learning). A Law is a finite mixture of
conditional-Poisson laws on 6-subsets of {1..P}:  q(S) = sum_m a_m prod_{i in S} w_{m,i} / e_6(w_m),
stored as log-weights `logw` (M x P) and mixture weights `a` (M). Every q is normalized and built
from past draws only, so prod_t q_t(S_t)/p0(S_t) is an evidence process against uniform draws
(Ville), whatever approximation the model uses.

Reads  datasets/pcso-lotto/data_draws_1yr.csv
Writes results/pcso_model_leaderboard_<run_date>.json  (byte-deterministic for a given seed)
Usage: python3 src/pcso_model_registry.py [--run-date 2026-09-21] [--null-sims 100] [--power-sims 20] [--verify]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "datasets" / "pcso-lotto" / "data_draws_1yr.csv"
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}
K = 6
FREEZE = "2026-06-10"
ALPHA = 0.01


# ------------------------------------------------------------------ conditional-Poisson algebra
def esp(w: np.ndarray, k: int = K) -> np.ndarray:
    """e_0..e_k of each row of w (M x P) -> (M x (k+1))."""
    E = np.zeros((w.shape[0], k + 1))
    E[:, 0] = 1.0
    for i in range(w.shape[1]):
        E[:, 1:] = E[:, 1:] + w[:, i:i + 1] * E[:, :-1]
    return E


def inclusion(w: np.ndarray) -> np.ndarray:
    """pi_i = w_i e_5(w_-i) / e_6(w) for each row (M x P); rows sum to 6."""
    E = esp(w)
    out = np.empty_like(w)
    for i in range(w.shape[1]):
        em = np.ones(w.shape[0])
        for j in range(1, K):
            em = E[:, j] - w[:, i] * em
        out[:, i] = w[:, i] * em / E[:, K]
    return out


class Law:
    def __init__(self, logw: np.ndarray, a: np.ndarray):
        self.logw, self.a = logw, a / a.sum()
        self.loge6 = np.log(esp(np.exp(logw))[:, K])

    def logq(self, S) -> float:
        idx = np.asarray(S) - 1
        lt = np.log(self.a + 1e-300) + self.logw[:, idx].sum(1) - self.loge6
        m = lt.max()
        return float(m + math.log(np.exp(lt - m).sum()))

    def inclusion(self) -> np.ndarray:
        return self.a @ inclusion(np.exp(self.logw))

    def top6(self) -> list[int]:
        return top6(self.inclusion())


def top6(pi: np.ndarray) -> list[int]:
    """Predicted 6-set: the six largest predictive inclusion probabilities (ties -> lower ball number)."""
    return sorted(int(i) + 1 for i in np.lexsort((np.arange(len(pi)), -pi))[:K])


def mix(laws: list[Law], v: np.ndarray) -> Law:
    """Mixture of conditional-Poisson laws as one Law (vectorised)."""
    return Law(np.vstack([L.logw for L in laws]), np.concatenate([vi * L.a for vi, L in zip(v, laws)]))


class MixLaw:
    """Mixture of arbitrary laws (any objects with logq / inclusion): used by the ensemble."""

    def __init__(self, laws, v: np.ndarray):
        self.laws, self.v = laws, v / v.sum()

    def logq(self, S) -> float:
        lt = np.array([math.log(vk + 1e-300) + L.logq(S) for vk, L in zip(self.v, self.laws)])
        m = lt.max()
        return float(m + math.log(np.exp(lt - m).sum()))

    def inclusion(self) -> np.ndarray:
        return sum(vk * L.inclusion() for vk, L in zip(self.v, self.laws))

    def top6(self) -> list[int]:
        return top6(self.inclusion())


# ------------------------------------------------------------------ features (fixed a priori)
def features(P: int) -> np.ndarray:
    """(6 x P): Legendre P1, 1[i>31], P2, 1[i odd], P3, P4 on x = 2u-1, u = (i-1/2)/P; standardised."""
    i = np.arange(1, P + 1, dtype=float)
    x = 2 * (i - 0.5) / P - 1
    raw = [x, (i > 31).astype(float), (3 * x**2 - 1) / 2, (i % 2 == 1).astype(float),
           (5 * x**3 - 3 * x) / 2, (35 * x**4 - 30 * x**2 + 3) / 8]
    out = []
    for f in raw:
        sd = f.std()
        out.append((f - f.mean()) / sd if sd > 0 else np.zeros(P))
    return np.array(out)


# ------------------------------------------------------------------ models
class Uniform:
    name, theory, dim = "uniform", "M0: i.i.d. uniform 6-sets", 0

    def predict(self, P):
        return Law(np.zeros((1, P)), np.ones(1))

    def update(self, P, S):
        pass


class DirichletCP:
    """Product-weight model, Dirichlet(a) prior per game, exact posterior by importance sampling
    (proposal Dir(a + c), weights z(w)^-T) — the lab's src/pcso_next_draw_posterior.py predictor."""
    theory = "conditional-Poisson product weights, Dirichlet prior (RESULTS_PCSO_REFRESH §8)"

    def __init__(self, a=100.0, samples=2000, seed=0):
        self.a, self.samples, self.rng = a, samples, np.random.default_rng(seed)
        self.name, self.dim, self.c = f"dirichlet_cp_a{int(a)}", "P-1", {}

    def predict(self, P):
        c = self.c.setdefault(P, np.zeros(P))
        T = int(c.sum() // K)
        w = self.rng.gamma(self.a + c, 1.0, size=(self.samples, P))
        w /= w.sum(1, keepdims=True)
        logz = np.log(esp(w)[:, K]) + K * math.log(P) - math.log(math.comb(P, K))
        lw = -T * logz
        return Law(np.log(w), np.exp(lw - lw.max()))

    def update(self, P, S):
        self.c.setdefault(P, np.zeros(P))[np.asarray(S) - 1] += 1


THETA = np.linspace(-0.4, 0.4, 161)
LOG_PRIOR = -0.5 * (THETA / 0.1) ** 2
LOG_PRIOR -= np.logaddexp.reduce(LOG_PRIOR)


class GridModel:
    """Shared machinery for one-parameter models with an N(0, 0.1^2) prior on the 161-point grid,
    theta shared by all games. Tracks the cumulative log-likelihood ll(theta) so the exact
    anytime-valid confidence sequence C_t(alpha) = {theta0 : M_t(theta0) < 1/alpha},
    M_t(theta0) = sum_theta pi(theta) L_t(theta) / L_t(theta0), follows by inversion
    (Lindon & Malek, NeurIPS 2022, Thm 2.4; team proposal Kimi P1)."""
    dim = 1

    def __init__(self):
        self.ll = np.zeros(len(THETA))

    @property
    def lp(self):
        lp = LOG_PRIOR + self.ll
        return lp - np.logaddexp.reduce(lp)

    def cs(self, alpha: float):
        log_marg = float(np.logaddexp.reduce(LOG_PRIOR + self.ll))
        inside = THETA[log_marg - self.ll < math.log(1 / alpha)]
        return [round(float(inside.min()), 4), round(float(inside.max()), 4)] if len(inside) else None

    def state(self):
        post = np.exp(self.lp)
        return {"theta_posterior_mean": round(float(post @ THETA), 5),
                "cs_95": self.cs(0.05), "cs_99": self.cs(0.01)}


class TiltGrid(GridModel):
    """One-parameter tilt w_i = exp(theta g_i) (src/pcso_lowdim_eprocess.py, registration draft
    pcso.lowdim-tilt.seq1)."""
    theory = "one-parameter conditional-Poisson tilt; exact grid posterior"

    def __init__(self, k: int, label: str):
        super().__init__()
        self.k, self.name = k, f"tilt_{label}"

    def predict(self, P):
        lp = self.lp
        self.last = Law(np.outer(THETA, features(P)[self.k]), np.exp(lp - lp.max()))
        return self.last

    def update(self, P, S):
        L = self.last
        self.ll = self.ll + L.logw[:, np.asarray(S) - 1].sum(1) - L.loge6


class ParityLaw:
    """q(S) = sum_theta pi(theta) exp(theta g(m(S))) / Z(theta); m(S) = #odd balls in S."""

    def __init__(self, P, lp, g, logcnt, logZ):
        self.P, self.lp, self.g, self.logcnt, self.logZ = P, lp, g, logcnt, logZ

    def logq(self, S) -> float:
        m = sum(1 for i in S if i % 2 == 1)
        return float(np.logaddexp.reduce(self.lp + THETA * self.g[m] - self.logZ))

    def inclusion(self) -> np.ndarray:
        pm = np.exp(self.lp[:, None] + np.outer(THETA, self.g) + self.logcnt[None, :] - self.logZ[:, None]).sum(0)
        Em = float(pm @ np.arange(K + 1))
        i = np.arange(1, self.P + 1)
        Po = int((i % 2 == 1).sum())
        return np.where(i % 2 == 1, Em / Po, (K - Em) / (self.P - Po))

    def top6(self) -> list[int]:
        return top6(self.inclusion())


class ParityPair(GridModel):
    """Second-order (within-draw pairwise) tilt in the same-parity direction: sufficient statistic
    q(m) = C(m,2) + C(6-m,2) = (m-3)^2 + 6 same-parity pairs, standardised under the exact null law of
    m; exact 7-term normalisation Z(theta) = sum_m C(Po,m) C(Pe,6-m) exp(theta g(m)). A log-linear
    model outside the first-order (product-weight) class (Fienberg & Rinaldo, Ann. Statist. 2012;
    team proposal GLM P1)."""
    theory = "second-order parity-pair log-linear tilt; exact 7-term normalisation"
    name = "pair_parity"

    def __init__(self):
        super().__init__()
        self.cache = {}

    def _pool(self, P):
        if P not in self.cache:
            Po = (P + 1) // 2
            cnt = np.array([math.comb(Po, m) * math.comb(P - Po, K - m) for m in range(K + 1)], dtype=float)
            p0 = cnt / cnt.sum()
            q = (np.arange(K + 1) - 3.0) ** 2 + 6
            g = (q - p0 @ q) / math.sqrt(p0 @ (q - p0 @ q) ** 2)
            logcnt = np.log(np.maximum(cnt, 1e-300))
            logZ = np.logaddexp.reduce(logcnt[None, :] + np.outer(THETA, g), axis=1)
            self.cache[P] = (g, logcnt, logZ)
        return self.cache[P]

    def predict(self, P):
        self.last = ParityLaw(P, self.lp, *self._pool(P))
        return self.last

    def update(self, P, S):
        g, _, logZ = self._pool(P)
        m = sum(1 for i in S if i % 2 == 1)
        self.ll = self.ll + THETA * g[m] - logZ


class CPNest:
    """CP-NEST: levels d = 0..6 of nested conditional-Poisson tilts on the ordered feature basis,
    theta shared across games, N(0, tau^2 I) prior, online Laplace posterior with the exact null
    Fisher information, antithetic Gaussian predictive samples, fixed-share mixing over levels
    (Herbster & Warmuth 1998). docs/plans/PCSO_MODEL_REGISTRY_PLAN.md §2."""
    name, theory, dim = "cp_nest", "nested CP tilts + online Laplace + fixed-share (PCSO_MODEL_REGISTRY_PLAN §2)", "0..6"
    D, TAU, RHO = 6, 0.05, 1e-3

    def __init__(self, seed=0, M=128):
        self.rng, self.M = np.random.default_rng(seed), M
        self.mu = {d: np.zeros(d) for d in range(1, self.D + 1)}
        self.Lam = {d: np.eye(d) / self.TAU**2 for d in range(1, self.D + 1)}
        v = 2.0 ** -np.arange(self.D + 1)
        self.v = v / v.sum()
        self.feat, self.fisher = {}, {}

    def _feat(self, P):
        if P not in self.feat:
            F = features(P)
            self.feat[P] = F
            self.fisher[P] = 6 * (P - 6) / (P - 1) * (F @ F.T) / P      # Cov_0(sum_{i in S} phi_i)
        return self.feat[P]

    def predict(self, P):
        F = self._feat(P)
        laws = [Law(np.zeros((1, P)), np.ones(1))]
        zf = self.rng.standard_normal((self.M // 2, self.D))       # common random numbers across levels
        for d in range(1, self.D + 1):
            Lc = np.linalg.cholesky(np.linalg.inv(self.Lam[d]))
            z = zf[:, :d] @ Lc.T
            th = np.vstack([self.mu[d] + z, self.mu[d] - z])
            laws.append(Law(th @ F[:d], np.ones(self.M)))
        self.last = laws
        return mix(laws, self.v)

    def update(self, P, S):
        F, idx = self._feat(P), np.asarray(S) - 1
        lq = np.array([L.logq(S) for L in self.last])                    # level predictive log-likelihoods
        vt = np.log(self.v) + lq
        vt = np.exp(vt - vt.max())
        vt /= vt.sum()
        self.v = (1 - self.RHO) * vt + self.RHO / (self.D + 1)
        for d in range(1, self.D + 1):
            Fd = F[:d]
            pi = inclusion(np.exp(self.mu[d] @ Fd)[None, :])[0]
            self.Lam[d] = self.Lam[d] + self.fisher[P][:d, :d]
            self.mu[d] = self.mu[d] + np.linalg.solve(self.Lam[d], Fd[:, idx].sum(1) - Fd @ pi)

    def state(self):
        return {"level_weights": [round(float(x), 5) for x in self.v],
                "cond_precision_d6": round(float(np.linalg.cond(self.Lam[self.D])), 2),
                "theta_mean": {str(d): [round(float(x), 5) for x in self.mu[d]] for d in self.mu},
                "theta_sd": {str(d): [round(float(x), 5) for x in np.sqrt(np.diag(np.linalg.inv(self.Lam[d])))] for d in self.mu}}


class Ensemble:
    """Prequential Bayesian mixture over registered models (equal prior weights): regret <= log(#models)
    against the best model; an average of evidence processes, so validity is preserved."""
    theory, dim = "prequential Bayesian model averaging", "mixture"

    def __init__(self, models):
        self.models, self.name = models, "ensemble"
        self.logv = np.full(len(models), -math.log(len(models)))

    def predict(self, P):
        self.last = [m.predict(P) for m in self.models]
        return MixLaw(self.last, np.exp(self.logv - self.logv.max()))

    def update(self, P, S):
        self.logv = self.logv + np.array([L.logq(S) for L in self.last])
        self.logv -= np.logaddexp.reduce(self.logv)
        for m in self.models:
            m.update(P, S)


def roster(seed):
    base = [Uniform(), DirichletCP(seed=seed + 1), TiltGrid(1, "high31"), TiltGrid(0, "linear"), ParityPair(),
            CPNest(seed=seed + 2)]
    return base, Ensemble([Uniform(), DirichletCP(seed=seed + 11), TiltGrid(1, "high31"), TiltGrid(0, "linear"),
                           ParityPair(), CPNest(seed=seed + 12)])


def rank_gate(rows):
    """Sufficient condition for existence of the product-weight MLE (Fienberg & Rinaldo 2012, Cor. 6,
    specialised by team proposal GLM P1): the incidence matrix of distinct observed 6-sets has rank P."""
    out = {}
    for P in sorted({P for _, P, _ in rows}):
        sets = sorted({S for _, Q, S in rows if Q == P})
        A = np.zeros((len(sets), P))
        for r, S in enumerate(sets):
            A[r, np.asarray(S) - 1] = 1
        out[str(P)] = {"distinct_sets": len(sets), "rank": int(np.linalg.matrix_rank(A)), "mle_exists_sufficient": bool(np.linalg.matrix_rank(A) == P)}
    return out


# ------------------------------------------------------------------ harness
def hyp(P):
    C = math.comb(P, K)
    return np.array([math.comb(K, k) * math.comb(P - K, K - k) / C for k in range(K + 1)])


def exact_p(items):
    obs = sum(m for _, m in items)
    dist = np.array([1.0])
    for P, _ in items:
        dist = np.convolve(dist, hyp(P))
    mean = float(np.dot(np.arange(len(dist)), dist))
    return obs, mean, float(dist[np.abs(np.arange(len(dist)) - mean) >= abs(obs - mean) - 1e-9].sum())


def run(models, rows, warmup=30, track_sup=False):
    """rows: [(date, P, S)] in date order. Returns per-model log-evidence by window, walk-forward matches,
    and the weighted Shiryaev-Roberts e-detector M_t = L_t (M_{t-1} + w_t), w_t = 1/(t(t+1)), on the
    model's exact increments L_t = q_t(S_t)/p0(S_t) (Shin, Ramdas & Rinaldo, NEJSDS 2023, Defs 2.8-2.11 and
    Remark 2.7: weights summing to <= 1 give P(sup_t M_t >= 1/alpha) <= alpha; team proposal Kimi P2)."""
    seen = {}
    res = {m.name: {"log_e_full": 0.0, "log_e_post_freeze": 0.0, "wf": [], "sup": 0.0, "sr": 0.0, "sr_max": 0.0}
           for m in models}
    for t, (date, P, S) in enumerate(rows, start=1):
        n = seen.get(P, 0)
        for m in models:
            law = m.predict(P)
            le = law.logq(S) + math.log(math.comb(P, K))
            r = res[m.name]
            r["log_e_full"] += le
            if date > FREEZE:
                r["log_e_post_freeze"] += le
            r["sr"] = math.exp(le) * (r["sr"] + 1.0 / (t * (t + 1)))
            r["sr_max"] = max(r["sr_max"], r["sr"])
            if track_sup:
                r["sup"] = max(r["sup"], r["log_e_full"])
            if n >= warmup:
                r["wf"].append((P, len(set(law.top6()) & set(S)), date > FREEZE))
            m.update(P, S)
        seen[P] = n + 1
    return res


def load():
    rows = []
    for r in csv.DictReader(io.StringIO(DRAWS.read_bytes().decode("utf-8-sig"))):
        if r["Game"] in POOL:
            rows.append((r["Date"], r["Game"], POOL[r["Game"]], tuple(sorted(int(r[f"N{i}"]) for i in range(1, 7)))))
    rows.sort()
    return [(d, P, S) for d, _, P, S in rows]


def sample_cp(rng, logw):
    """Exact draw from f_w on 6-sets (sequential scan with suffix elementary symmetric polynomials)."""
    w = np.exp(logw)
    P = len(w)
    suf = np.zeros((P + 1, K + 1))
    suf[P, 0] = 1.0
    for j in range(P - 1, -1, -1):
        suf[j] = suf[j + 1]
        suf[j, 1:] += w[j] * suf[j + 1, :-1]
    S, k = [], K
    for j in range(P):
        if k == 0:
            break
        if rng.random() < w[j] * suf[j + 1, k - 1] / suf[j, k]:
            S.append(j + 1)
            k -= 1
    return tuple(S)


def synthetic(rng, schedule, theta1=0.0):
    """Same (date, pool) schedule as the real data; draws uniform (theta1 = 0) or tilted on feature phi_1."""
    return [(d, P, sample_cp(rng, theta1 * features(P)[0])) for d, P in schedule]


def _null_rep(job):
    """One simulated uniform stream (C1, C3); seeded per replicate, so results do not depend on scheduling.
    M = 32: validity does not depend on M (design review, Kimi K3, item 6)."""
    seed, s, schedule = job
    syn = synthetic(np.random.default_rng([seed, 100, s]), schedule)
    cp = CPNest(seed=seed + 1000 + s, M=32)
    r0 = run([cp], syn, warmup=10**9, track_sup=True)["cp_nest"]
    return r0["sup"], r0["sr_max"], float(cp.v[0])


def _power_rep(job):
    """One planted-tilt stream (C2): pooled draws to first crossing of 1/alpha for CP-NEST and for the
    exact one-parameter grid process on phi_1 (-1 if no crossing within the horizon)."""
    seed, th, s, schedule = job
    syn = synthetic(np.random.default_rng([seed, 200, int(round(th * 1000)), s]), schedule, th)
    hits = {}
    for m in (CPNest(seed=seed + 2000 + s, M=32), TiltGrid(0, "linear")):
        le, hit = 0.0, -1
        for t, (_, P, S) in enumerate(syn):
            le += m.predict(P).logq(S) + math.log(math.comb(P, K))
            m.update(P, S)
            if le >= math.log(1 / ALPHA):
                hit = t + 1
                break
        hits[m.name] = hit
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--run-date", default="2026-09-21")
    ap.add_argument("--null-sims", type=int, default=400)
    ap.add_argument("--power-sims", type=int, default=50)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    rows = load()
    base, ens = roster(args.seed)
    res = run(base + [ens], rows)
    board = {}
    for m in base + [ens]:
        r = res[m.name]
        wf_all = [(P, k) for P, k, _ in r["wf"]]
        wf_post = [(P, k) for P, k, post in r["wf"] if post]
        o, e, p = exact_p(wf_all)
        o2, e2, p2 = exact_p(wf_post)
        board[m.name] = {"theory": m.theory, "dim": m.dim,
                         "evidence_full_history": round(math.exp(r["log_e_full"]), 6),
                         "evidence_post_freeze": round(math.exp(r["log_e_post_freeze"]), 6),
                         "walk_forward_matches": {"all": [o, round(e, 1), round(p, 4)], "post_freeze": [o2, round(e2, 1), round(p2, 4)]},
                         "sr_edetector_max": round(r["sr_max"], 6)}
        if hasattr(m, "state"):
            board[m.name]["state"] = m.state()
    board["ensemble"]["model_weights"] = {m.name: round(float(x), 5) for m, x in zip(ens.models, np.exp(ens.logv))}
    for name, b in board.items():
        print(f"[real data] {name:20s} evidence full={b['evidence_full_history']:.4g} post-freeze={b['evidence_post_freeze']:.4g} "
              f"SR max={b['sr_edetector_max']:.4g} walk-forward all={b['walk_forward_matches']['all']}", flush=True)
    schedule = [(d, P) for d, P, _ in rows]
    long_schedule = [(f"sim-{k:05d}", P) for k, (_, P) in enumerate(schedule * 3)]
    from concurrent.futures import ProcessPoolExecutor
    workers = max(1, (os.cpu_count() or 2) - 1)
    # C1 (implementation regression test of Ville control) and C3 (collapse to d = 0 under M0).
    sups, srs, v0 = [], [], []
    with ProcessPoolExecutor(workers) as ex:
        for i, (a, b, c) in enumerate(ex.map(_null_rep, [(args.seed, s, schedule) for s in range(args.null_sims)]), 1):
            sups.append(a)
            srs.append(b)
            v0.append(c)
            if i % 50 == 0:
                print(f"[null] {i}/{args.null_sims} crossing so far {np.mean(np.array(sups) >= math.log(1 / ALPHA)):.4f}", flush=True)
        # C2: CP-NEST vs the exact d = 1 grid process on the same direction (phi_1), planted theta_1.
        power = {}
        for th in (0.05, 0.10):
            cross = {"cp_nest": [], "tilt_linear": []}
            for hits in ex.map(_power_rep, [(args.seed, th, s, long_schedule) for s in range(args.power_sims)]):
                for k, v in hits.items():
                    cross[k].append(v)
            print(f"[power] theta1={th} done", flush=True)
            power[f"theta1_{th:.2f}"] = {k: {"fraction_crossed": round(float(np.mean(np.array(v) > 0)), 3),
                                          "median_draws_to_cross": (int(np.median([x for x in v if x > 0])) if any(x > 0 for x in v) else None)}
                                      for k, v in cross.items()}
    out = {"_meta": {"schema_version": 1, "script": "src/pcso_model_registry.py", "run_date": args.run_date, "seed": args.seed,
                     "design": "docs/plans/PCSO_MODEL_REGISTRY_PLAN.md", "freeze": FREEZE, "alpha": ALPHA,
                     "evidence": "prod_t q_t(S_t)/p0(S_t); post-freeze window conditions on earlier draws",
                     "walk_forward": "[observed matches, expected under M0, exact two-sided p]; predicted set = maximum-inclusion set (six largest predictive inclusion probabilities; equals the mode of a single CP law, the mixture mode to first order)",
                     "claims": "C1 null crossing <= alpha (regression test); C2 CP-NEST vs exact d=1 grid on phi_1 (simulation claim); C3 fixed-share bound is a theorem, collapse = P0(v_T(0) >= 0.9) simulated; C4 null part = walk-forward exact test",
                     "input_sha256": {str(DRAWS.relative_to(ROOT)): hashlib.sha256(DRAWS.read_bytes()).hexdigest()},
                     "grade": "G0 exploratory"},
           "leaderboard": board,
           "mle_existence_gate": rank_gate(rows),
           "cp_nest_null_check": {"replicates": args.null_sims, "draws_per_replicate": len(rows),
                                  "fraction_sup_ge_1_over_alpha": round(float(np.mean(np.array(sups) >= math.log(1 / ALPHA))), 4),
                                  "ville_bound": ALPHA, "median_sup_evidence": round(float(np.exp(np.median(sups))), 4),
                                  "sr_edetector_fraction_max_ge_1_over_alpha": round(float(np.mean(np.array(srs) >= 1 / ALPHA)), 4),
                                  "M_samples": 32,
                                  "collapse_fraction_v0_ge_0p9": round(float(np.mean(np.array(v0) >= 0.9)), 4),
                                  "median_final_v0": round(float(np.median(v0)), 4)},
           "power_planted_tilt_phi1": {"replicates": args.power_sims, "horizon_pooled_draws": len(long_schedule),
                                       "comparator": "exact one-parameter grid process on phi_1 (tilt_linear)", **power}}
    payload = (json.dumps(out, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    dst = ROOT / "results" / f"pcso_model_leaderboard_{args.run_date}.json"
    if args.verify:
        if dst.read_bytes() != payload:
            raise SystemExit(f"VERIFY MISMATCH: {dst}")
        print(f"PASS sha256={hashlib.sha256(payload).hexdigest()}; wrote=none")
        return
    dst.write_bytes(payload)
    print(f"wrote {dst.relative_to(ROOT)} sha256={hashlib.sha256(payload).hexdigest()}")
    print(json.dumps({k: out[k] for k in ("leaderboard", "cp_nest_null_check", "power_planted_tilt_phi1")}, indent=1))


if __name__ == "__main__":
    main()
