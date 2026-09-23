"""Exact mode of a predictive law on 6-subsets of {1..P}: argmax_S q(S) under the fitted law q.

A single conditional-Poisson law is a product-weight distribution, so its mode is the six largest
weights — exactly Law.top6(). For a mixture of laws (MixLaw, the ensemble's predictive law) top6()
is the mode only to first order in the mixture weights (design review, Kimi K3, item 5); the exact
argmax of the predictive law is recovered here by 2-swap local search with exact logq evaluations.
mode_gap() reports the first-order shortfall log q(mode) / q(max-inclusion set) of the
maximum-inclusion estimate. Works for any object exposing logq(S) and top6() (Law, MixLaw,
ParityLaw).
"""
from __future__ import annotations

import itertools

K = 6


def mode(law, P: int, max_rounds: int = 50) -> tuple[list[int], float]:
    """Mode of law by 2-swap local search: start from the maximum-inclusion set top6(); each round
    evaluate law.logq for every swap (one ball of S out, one ball outside S in) exactly and move to
    the best improving swap; stop at a 2-swap local optimum or after max_rounds. Each accepted move
    strictly increases logq, so the search terminates and never returns a set worse than the
    starting set. Ties break toward the lexicographically smallest set (deterministic output)."""
    S = law.top6()
    lq = law.logq(S)
    cur = set(S)
    for _ in range(max_rounds):
        cands = []
        for out in sorted(cur):
            for inn in range(1, P + 1):
                if inn in cur:
                    continue
                T = tuple(sorted(cur - {out} | {inn}))
                cands.append((law.logq(T), T))
        best = min(cands, key=lambda c: (-c[0], c[1]))
        if best[0] <= lq:
            break
        S, lq = list(best[1]), best[0]
        cur = set(S)
    return sorted(S), lq


def brute_mode(law, P: int) -> tuple[list[int], float]:
    """Exact mode by exhaustive argmax over all C(P,6) sets (small P only). Same tie-break as mode()
    (largest logq, then lexicographically smallest set)."""
    lq, S = min((-law.logq(S), S) for S in itertools.combinations(range(1, P + 1), K))
    return list(S), -lq


def mode_gap(law, P: int) -> dict:
    """Compare the maximum-inclusion set with the exact mode of the predictive law: log_ratio =
    log q(mode) - log q(top6) measures how much the first-order (maximum-inclusion) estimate falls
    short of the exact argmax for mixtures."""
    t = law.top6()
    tl = law.logq(t)
    m, ml = mode(law, P)
    return {"max_inclusion_set": t, "max_inclusion_logq": tl,
            "mode_set": m, "mode_logq": ml, "log_ratio": ml - tl}
