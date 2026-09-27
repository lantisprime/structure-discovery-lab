"""Frozen, byte-stable PCSO laws and a reference evaluator."""
import base64
import json
import math

import numpy as np
from scipy.special import logsumexp

import pcso_model_registry as R
from pcso_sparse_switch import SparseLaw


def freeze(law, P) -> dict:
    """Copy a supported native law into a plain graph of arrays and scalars."""
    if isinstance(law, R.Law):
        return {"type": "cp", "P": P, "logw": np.asarray(law.logw, dtype=np.float64),
                "a": np.asarray(law.a, dtype=np.float64), "loge6": np.asarray(law.loge6, dtype=np.float64)}
    if isinstance(law, R.MixLaw):
        return {"type": "mix", "P": P, "v": np.asarray(law.v, dtype=np.float64),
                "children": [freeze(child, P) for child in law.laws]}
    if isinstance(law, R.ParityLaw):
        return {"type": "parity", "P": law.P, "lp": np.asarray(law.lp, dtype=np.float64),
                "theta": np.asarray(R.THETA, dtype=np.float64), "g": np.asarray(law.g, dtype=np.float64),
                "logcnt": np.asarray(law.logcnt, dtype=np.float64), "logZ": np.asarray(law.logZ, dtype=np.float64)}
    if isinstance(law, SparseLaw):
        experts = []
        for expert, lw in zip(law.experts, law.logweights):
            experts.append({"k": int(expert.supports.shape[1]),
                            "supports": np.asarray(expert.supports, dtype=np.uint16),
                            "theta": np.asarray(expert.theta, dtype=np.float64),
                            "logz_ratio": np.asarray(expert.logz_ratio, dtype=np.float64),
                            "outside": np.asarray(expert.outside, dtype=np.float64),
                            "correction": np.asarray(expert.correction, dtype=np.float64),
                            "logweights": np.asarray(lw, dtype=np.float64)})
        return {"type": "sparse", "P": law.P, "logoutside": float(law.logoutside),
                "logC": float(law.logC), "experts": experts}
    raise TypeError(f"unsupported law type: {type(law).__name__}")


def _encode_arrays(value):
    if isinstance(value, np.ndarray):
        dtype = np.dtype("<u2") if value.dtype == np.dtype(np.uint16) else np.dtype("<f8")
        arr = np.ascontiguousarray(value, dtype=dtype)
        return {"dtype": dtype.str, "shape": list(arr.shape),
                "b64": base64.b64encode(arr.tobytes()).decode("ascii")}
    if isinstance(value, dict):
        return {key: _encode_arrays(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode_arrays(item) for item in value]
    return value


def encode(graph) -> bytes:
    """Encode a graph as canonical UTF-8 JSON with a final newline."""
    return (json.dumps(_encode_arrays(graph), sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("utf-8")


def _decode_arrays(value):
    if isinstance(value, dict):
        if set(value) == {"dtype", "shape", "b64"}:
            dtype = np.dtype(value["dtype"])
            raw = base64.b64decode(value["b64"])
            return np.frombuffer(raw, dtype=dtype).reshape(value["shape"]).copy()
        return {key: _decode_arrays(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode_arrays(item) for item in value]
    return value


def decode(data: bytes) -> dict:
    """Restore arrays from canonical or equivalent JSON bytes."""
    return _decode_arrays(json.loads(data.decode("utf-8")))


def _lse(values):
    values = np.asarray(values, dtype=np.float64)
    m = values.max()
    return float(m + math.log(np.exp(values - m).sum()))


def logq(g, S):
    kind = g["type"]
    if kind == "cp":
        idx = np.asarray(S) - 1
        lt = np.log(g["a"] + 1e-300) + g["logw"][:, idx].sum(1) - g["loge6"]
        return _lse(lt)
    if kind == "mix":
        lt = [math.log(vk + 1e-300) + logq(child, S)
              for vk, child in zip(g["v"], g["children"])]
        return _lse(lt)
    if kind == "parity":
        m_odd = sum(int(i) % 2 == 1 for i in S)
        return float(np.logaddexp.reduce(g["lp"] + g["theta"] * g["g"][m_odd] - g["logZ"]))
    if kind == "sparse":
        present = np.zeros(g["P"], dtype=bool)
        present[np.asarray(S) - 1] = True
        component_terms = []
        for expert in g["experts"]:
            hits = present[expert["supports"]]
            ratio = np.zeros((len(expert["theta"]), len(expert["supports"])))
            for i in range(expert["k"]):
                ratio += expert["theta"][:, i, None] * hits[None, :, i]
            ratio -= expert["logz_ratio"][:, None]
            term = expert["logweights"] + ratio
            component_terms.append(logsumexp(term))
        logratio = float(logsumexp([g["logoutside"], *component_terms]))
        return logratio - g["logC"]
    raise TypeError(f"unsupported graph type: {kind}")


def inclusion(g):
    kind = g["type"]
    if kind == "cp":
        return g["a"] @ R.inclusion(np.exp(g["logw"]))
    if kind == "mix":
        return sum(vk * inclusion(child) for vk, child in zip(g["v"], g["children"]))
    if kind == "parity":
        pm = np.exp(g["lp"][:, None] + np.outer(g["theta"], g["g"])
                    + g["logcnt"][None, :] - g["logZ"][:, None]).sum(0)
        Em = float(pm @ np.arange(R.K + 1))
        i = np.arange(1, g["P"] + 1)
        Po = int((i % 2 == 1).sum())
        return np.where(i % 2 == 1, Em / Po, (R.K - Em) / (g["P"] - Po))
    if kind == "sparse":
        pi = np.full(g["P"], math.exp(g["logoutside"]) * R.K / g["P"])
        for expert in g["experts"]:
            weights = np.exp(expert["logweights"])
            pi += weights.sum(axis=1) @ expert["outside"]
            for i in range(expert["k"]):
                correction = (weights * expert["correction"][:, i, None]).sum(axis=0)
                pi += np.bincount(expert["supports"][:, i], weights=correction, minlength=g["P"])
        return pi
    raise TypeError(f"unsupported graph type: {kind}")


def top6(g):
    return R.top6(inclusion(g))


def score_bounds(g) -> tuple[float, float]:
    """Bound D(S) for every six-subset.

    The log of a convex combination is bounded by the log-sum of component bounds.
    For a CP component, log f(S) = sum_{i in S} logw_i - loge6 is extremal at
    the 6 smallest or 6 largest logw values.
    Parity bounds enumerate feasible odd-ball counts.
    Sparse bounds each expert by its coordinate-wise tilt extrema.
    Adding log C(P,6) puts log q in D units; sparse subtracts logC first.
    """
    kind = g["type"]
    logC = math.log(math.comb(g["P"], R.K))
    if kind == "cp":
        lo_j = np.sort(g["logw"], axis=1)[:, :R.K].sum(1) - g["loge6"]
        hi_j = np.sort(g["logw"], axis=1)[:, -R.K:].sum(1) - g["loge6"]
        alo = np.log(g["a"] + 1e-300)
        return _lse(alo + lo_j) + logC, _lse(alo + hi_j) + logC
    if kind == "mix":
        bounds = [score_bounds(child) for child in g["children"]]
        lv = np.log(g["v"] + 1e-300)
        return (_lse(lv + np.array([b[0] - logC for b in bounds])) + logC,
                _lse(lv + np.array([b[1] - logC for b in bounds])) + logC)
    if kind == "parity":
        feasible = np.isfinite(g["logcnt"])
        values = [float(np.logaddexp.reduce(g["lp"] + g["theta"] * g["g"][m] - g["logZ"]))
                  for m in np.flatnonzero(feasible)]
        return min(values) + logC, max(values) + logC
    if kind == "sparse":
        low_terms, high_terms = [g["logoutside"]], [g["logoutside"]]
        for expert in g["experts"]:
            tmin = np.zeros(len(expert["theta"]))
            tmax = np.zeros_like(tmin)
            for i in range(expert["k"]):
                tmin += np.minimum(0, expert["theta"][:, i])
                tmax += np.maximum(0, expert["theta"][:, i])
            low_terms.append(logsumexp(expert["logweights"]
                                       + (tmin - expert["logz_ratio"])[:, None]))
            high_terms.append(logsumexp(expert["logweights"]
                                        + (tmax - expert["logz_ratio"])[:, None]))
        return float(logsumexp(low_terms)), float(logsumexp(high_terms))
    raise TypeError(f"unsupported graph type: {kind}")
