"""Frozen, byte-stable PCSO laws and a reference evaluator."""
import base64
import json
import math

import mpmath as mp
import numpy as np
from scipy.special import logsumexp

import pcso_model_registry as R
from pcso_sparse_switch import THETA as SPARSE_THETA, SparseLaw, _logcomb


def _array(x, dtype):
    return np.array(x, dtype=dtype, copy=True)


def freeze(law, P) -> dict:
    """Copy a supported native law into a plain graph of arrays and scalars."""
    if isinstance(law, R.Law):
        return {"type": "cp", "P": P, "logw": _array(law.logw, np.float64),
                "a": _array(law.a, np.float64), "loge6": _array(law.loge6, np.float64)}
    if isinstance(law, R.MixLaw):
        return {"type": "mix", "P": P, "v": _array(law.v, np.float64),
                "children": [freeze(child, P) for child in law.laws]}
    if isinstance(law, R.ParityLaw):
        return {"type": "parity", "P": law.P, "lp": _array(law.lp, np.float64),
                "theta": _array(R.THETA, np.float64), "g": _array(law.g, np.float64),
                "logcnt": _array(law.logcnt, np.float64), "logZ": _array(law.logZ, np.float64)}
    if isinstance(law, SparseLaw):
        experts = []
        for expert, lw in zip(law.experts, law.logweights):
            experts.append({"k": int(expert.supports.shape[1]),
                            "supports": _array(expert.supports, np.uint16),
                            "theta": _array(expert.theta, np.float64),
                            "logz_ratio": _array(expert.logz_ratio, np.float64),
                            "outside": _array(expert.outside, np.float64),
                            "correction": _array(expert.correction, np.float64),
                            "logweights": _array(lw, np.float64)})
        outside = float(law.logoutside)
        if not math.isfinite(outside):
            outside = np.array(outside, dtype="<f8")
        return {"type": "sparse", "P": law.P, "logoutside": outside,
                "logC": float(law.logC), "experts": experts}
    raise TypeError(f"unsupported law type: {type(law).__name__}")


def _encode_arrays(value):
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "f":
            dtype = np.dtype("<f8")
        elif value.dtype.kind in "ui" and value.dtype.itemsize == 2 and np.all(value >= 0) and np.all(value <= 65535):
            dtype = np.dtype("<u2")
        else:
            raise TypeError(f"unsupported array dtype: {value.dtype}")
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
                       ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


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


def _reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def decode(data: bytes) -> dict:
    """Restore and validate arrays from canonical or equivalent JSON bytes."""
    graph = _decode_arrays(json.loads(data.decode("utf-8"), parse_constant=_reject_constant))
    validate(graph)
    return graph


def _lse(values):
    values = np.asarray(values, dtype=np.float64)
    if np.any(np.isnan(values)):
        raise ValueError("logsumexp input must not contain NaN")
    values = values[values != -math.inf]
    if values.size == 0:
        return -math.inf
    return float(logsumexp(values))


def _fields(g, expected):
    if set(g) != expected:
        raise ValueError(f"{g.get('type', 'graph')} keys must be {sorted(expected)}")


def _float_array(g, key, shape=None, allow_neginf=False):
    x = g[key]
    if not isinstance(x, np.ndarray) or x.dtype != np.dtype(np.float64):
        raise ValueError(f"{key} must be a float64 array")
    if shape is not None and x.shape != shape:
        raise ValueError(f"{key} must have shape {shape}")
    valid = np.isfinite(x) | ((x == -math.inf) if allow_neginf else False)
    if not np.all(valid):
        raise ValueError(f"{key} must contain finite values" + (" or -inf" if allow_neginf else ""))
    return x


def _scalar(g, key, finite=True):
    value = g[key]
    if isinstance(value, np.ndarray) and value.shape == () and value.dtype == np.dtype(np.float64):
        value = float(value)
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{key} must be a scalar")
    value = float(value)
    if finite and not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    if not finite and not (math.isfinite(value) or value == -math.inf):
        raise ValueError(f"{key} must be finite or -inf")
    return value


def _P(g):
    p = g.get("P")
    if isinstance(p, bool) or not isinstance(p, (int, np.integer)) or int(p) < R.K:
        raise ValueError("P must be an integer >= 6")
    return int(p)


def _close(actual, expected, name):
    if not math.isfinite(float(actual)) or abs(float(actual) - float(expected)) > 1e-10:
        raise ValueError(f"{name} does not match its construction")


def _validate(g):
    if not isinstance(g, dict) or not isinstance(g.get("type"), str):
        raise ValueError("graph must have a type")
    kind = g["type"]
    p = _P(g)
    if kind == "cp":
        _fields(g, {"type", "P", "logw", "a", "loge6"})
        lw = g["logw"]
        if not isinstance(lw, np.ndarray) or lw.dtype != np.dtype(np.float64) or lw.ndim != 2 or lw.shape[1] != p:
            raise ValueError("logw must be a float64 (n,P) array")
        _float_array(g, "logw", lw.shape)
        n = lw.shape[0]
        a = _float_array(g, "a", (n,))
        _float_array(g, "loge6", (n,))
        if np.any(a < 0) or abs(float(a.sum()) - 1) > 1e-12:
            raise ValueError("a must be nonnegative and sum to 1")
        expected = np.log(R.esp(np.exp(lw))[:, R.K])
        if not np.all(np.isfinite(expected)):
            raise ValueError("logw produces invalid loge6")
        if np.any(np.abs(g["loge6"] - expected) > 1e-10):
            raise ValueError("loge6 does not match its construction")
    elif kind == "mix":
        _fields(g, {"type", "P", "v", "children"})
        children = g["children"]
        if not isinstance(children, list):
            raise ValueError("children must be a list")
        v = _float_array(g, "v", (len(children),))
        if np.any(v < 0) or abs(float(v.sum()) - 1) > 1e-12:
            raise ValueError("v must be nonnegative and sum to 1")
        for child in children:
            if not isinstance(child, dict) or child.get("P") != p:
                raise ValueError("children must share the parent's P")
            child_width = (child["logw"].shape[1] if child.get("type") == "cp"
                           and isinstance(child.get("logw"), np.ndarray)
                           and child["logw"].ndim == 2 else child.get("P"))
            if child_width != p:
                raise ValueError("children must share the parent's P")
            _validate(child)
    elif kind == "parity":
        _fields(g, {"type", "P", "lp", "theta", "g", "logcnt", "logZ"})
        lp = _float_array(g, "lp", allow_neginf=True)
        theta = _float_array(g, "theta")
        stat = _float_array(g, "g", (R.K + 1,))
        cnt = _float_array(g, "logcnt", (R.K + 1,), allow_neginf=True)
        logz = _float_array(g, "logZ", theta.shape)
        if (lp.ndim != 1 or theta.ndim != 1 or lp.shape != theta.shape
                or theta.shape != np.asarray(R.THETA).shape
                or not np.array_equal(theta, np.asarray(R.THETA, dtype=np.float64))):
            raise ValueError("parity lp and theta must be matching vectors")
        lp_norm = _lse(lp)
        if not math.isfinite(lp_norm) or abs(lp_norm) > 1e-12:
            raise ValueError("exp(lp) must sum to 1")
        odd = (p + 1) // 2
        counts = np.array([math.comb(odd, m) * math.comb(p - odd, R.K - m)
                           if 0 <= m <= odd and 0 <= R.K - m <= p - odd else 0
                           for m in range(R.K + 1)], dtype=np.float64)
        # ParityPair._pool floors infeasible counts before taking their logarithms.
        expected_cnt = np.log(np.maximum(counts, 1e-300))
        if np.any(np.abs(cnt[np.isfinite(cnt)] - expected_cnt[np.isfinite(cnt)]) > 1e-10) or not np.array_equal(np.isneginf(cnt), np.isneginf(expected_cnt)):
            raise ValueError("logcnt does not match its construction")
        expected_z = logsumexp(expected_cnt[None, :] + np.outer(theta, stat), axis=1)
        if not np.all(np.isfinite(expected_z)):
            raise ValueError("parity normalizer is invalid")
        if np.any(np.abs(logz - expected_z) > 1e-10):
            raise ValueError("logZ does not match its construction")
    elif kind == "sparse":
        _fields(g, {"type", "P", "logoutside", "logC", "experts"})
        outside = _scalar(g, "logoutside", finite=False)
        logc = _scalar(g, "logC")
        _close(logc, math.log(math.comb(p, R.K)), "logC")
        experts = g["experts"]
        if not isinstance(experts, list):
            raise ValueError("experts must be a list")
        for e in experts:
            if not isinstance(e, dict):
                raise ValueError("expert must be an object")
            _fields(e, {"k", "supports", "theta", "logz_ratio", "outside", "correction", "logweights"})
            k = e["k"]
            if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or k < 1 or k > p:
                raise ValueError("expert k must be in 1..P")
            supports = e["supports"]
            if not isinstance(supports, np.ndarray) or supports.dtype != np.dtype(np.uint16) or supports.ndim != 2 or supports.shape[1] != k:
                raise ValueError("supports must be a uint16 (n_supp,k) array")
            if supports.shape[0] != math.comb(p, k):
                raise ValueError("supports must enumerate the expert's full support set")
            if np.any(supports >= p):
                raise ValueError("support index must be in [0,P-1]")
            theta = _float_array(e, "theta")
            if theta.ndim != 2 or theta.shape != (len(SPARSE_THETA)**k, k):
                raise ValueError("theta must have shape (n_theta,k)")
            ntheta, nsupp = theta.shape[0], supports.shape[0]
            lzr = _float_array(e, "logz_ratio", (ntheta,))
            _float_array(e, "outside", (ntheta,))
            _float_array(e, "correction", (ntheta, k))
            lw = _float_array(e, "logweights", (ntheta, nsupp), allow_neginf=True)
            # Match _Experts: sum over all hit masks, then subtract log C(P,6).
            bits = np.array(np.meshgrid(*([[0, 1]] * k), indexing="ij")).reshape(k, -1).T
            hits = bits.sum(axis=1)
            terms = theta @ bits.T + np.array([_logcomb(p-k, R.K-int(h)) for h in hits])
            expected = logsumexp(terms, axis=1) - math.log(math.comb(p, R.K))
            if np.any(np.abs(lzr - expected) > 1e-10):
                raise ValueError("logz_ratio does not match its construction")
            logz = logsumexp(terms, axis=1)
            inside = np.exp(terms - logz[:, None]) @ bits
            outside_terms = theta @ bits.T + np.array([_logcomb(p-k-1, R.K-1-int(h)) for h in hits])
            expected_outside = np.exp(logsumexp(outside_terms, axis=1) - logz)
            expected_correction = inside - expected_outside[:, None]
            if np.any(np.abs(e["outside"] - expected_outside) > 1e-10):
                raise ValueError("outside does not match its construction")
            if np.any(np.abs(e["correction"] - expected_correction) > 1e-10):
                raise ValueError("correction does not match its construction")
            if np.any(np.isnan(lw)) or np.any(np.isposinf(lw)):
                raise ValueError("logweights must be finite or -inf")
        # Each tilted expert term has uniform expectation one (logz_ratio), so the law's
        # total mass is exp(logoutside) + sum exp(logweights).
        mass = float(np.exp(logsumexp([outside] + [logsumexp(e["logweights"]) for e in experts])))
        if abs(mass - 1) > 1e-12:
            raise ValueError("sparse mixture mass must sum to 1")
    else:
        raise ValueError(f"unsupported graph type: {kind}")


def validate(g) -> None:
    """Validate a frozen law graph and its reconstructible cached quantities."""
    _validate(g)


def _validate_S(g, S):
    p = int(g["P"])
    try:
        values = list(S)
    except TypeError as exc:
        raise ValueError("S must contain exactly six distinct integers in 1..P") from exc
    if len(values) != R.K:
        raise ValueError("S must contain exactly six distinct integers in 1..P")
    if any(isinstance(i, (bool, np.bool_)) or not isinstance(i, (int, np.integer)) for i in values):
        raise ValueError("S must contain exactly six distinct integers in 1..P")
    if any(int(i) < 1 or int(i) > p for i in values) or len(set(map(int, values))) != R.K:
        raise ValueError("S must contain exactly six distinct integers in 1..P")
    return tuple(map(int, values))


def _logq(g, S):
    kind = g["type"]
    if kind == "cp":
        idx = np.asarray(S, dtype=int) - 1
        active = g["a"] > 0
        if not np.any(active):
            return -math.inf
        with np.errstate(divide="ignore"):
            loga = np.log(g["a"][active])
        lt = loga + g["logw"][active][:, idx].sum(1) - g["loge6"][active]
        return _lse(lt)
    if kind == "mix":
        terms = [_logq(child, S) + math.log(float(v)) for v, child in zip(g["v"], g["children"]) if v > 0]
        return _lse(terms)
    if kind == "parity":
        m_odd = sum(int(i) % 2 == 1 for i in S)
        return _lse(g["lp"] + g["theta"] * g["g"][m_odd] - g["logZ"])
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
            component_terms.append(_lse(term.ravel()))
        logratio = _lse([_scalar(g, "logoutside", finite=False), *component_terms])
        return logratio - float(g["logC"])
    raise TypeError(f"unsupported graph type: {kind}")


def logq(g, S, _validated=False):
    if not _validated:
        validate(g)
        S = _validate_S(g, S)
    return _logq(g, S)


def _inclusion(g):
    kind = g["type"]
    if kind == "cp":
        return g["a"] @ R.inclusion(np.exp(g["logw"]))
    if kind == "mix":
        return sum(vk * _inclusion(child) for vk, child in zip(g["v"], g["children"]) if vk > 0)
    if kind == "parity":
        pm = np.exp(g["lp"][:, None] + np.outer(g["theta"], g["g"])
                    + g["logcnt"][None, :] - g["logZ"][:, None]).sum(0)
        Em = float(pm @ np.arange(R.K + 1))
        i = np.arange(1, g["P"] + 1)
        Po = int((i % 2 == 1).sum())
        return np.where(i % 2 == 1, Em / Po, (R.K - Em) / (g["P"] - Po))
    if kind == "sparse":
        pi = np.full(g["P"], math.exp(_scalar(g, "logoutside", finite=False)) * R.K / g["P"])
        for expert in g["experts"]:
            weights = np.exp(expert["logweights"])
            pi += weights.sum(axis=1) @ expert["outside"]
            for i in range(expert["k"]):
                correction = (weights * expert["correction"][:, i, None]).sum(axis=0)
                pi += np.bincount(expert["supports"][:, i], weights=correction, minlength=g["P"])
        return pi
    raise TypeError(f"unsupported graph type: {kind}")


def inclusion(g, _validated=False):
    if not _validated:
        validate(g)
    return _inclusion(g)


def top6(g):
    return R.top6(inclusion(g))


def _iv(x):
    """Create an exact interval input from a stored binary64 value."""
    return mp.iv.mpf(float(x))


def _iv_lse(values):
    values = list(values)
    values = [v for v in values if not (float(v.a) == -math.inf and float(v.b) == -math.inf)]
    if not values:
        return mp.iv.mpf("-inf")
    pivot = max(float(v.b) for v in values)
    p = _iv(pivot)
    return p + mp.iv.log(sum((mp.iv.exp(v - p) for v in values), mp.iv.mpf(0)))


def _iv_lse_grouped(groups):
    """Log-sum-exp of (interval term, integer multiplicity) pairs."""
    groups = [(term, int(count)) for term, count in groups if count]
    if not groups:
        return mp.iv.mpf("-inf")
    pivot = max(float(term.b) for term, _ in groups)
    p = _iv(pivot)
    total = sum((mp.iv.mpf(count) * mp.iv.exp(term - p) for term, count in groups), mp.iv.mpf(0))
    return p + mp.iv.log(total)


def _float_counts(values):
    counts = {}
    for value in values:
        value = float(value)
        if value != -math.inf:
            counts[value] = counts.get(value, 0) + 1
    return counts


def _outward(x, lower):
    endpoint = x.a if lower else x.b
    f = float(endpoint)
    exact_f = mp.mpf(f)
    exact_x = mp.make_mpf(endpoint._mpi_[0 if lower else 1])
    if lower and exact_f > exact_x:
        f = math.nextafter(f, -math.inf)
    elif not lower and exact_f < exact_x:
        f = math.nextafter(f, math.inf)
    return f


def _score_bounds_iv(g):
    kind = g["type"]
    p = g["P"]
    logc = mp.iv.log(mp.iv.mpf(math.comb(p, R.K)))
    if kind == "cp":
        low, high = [], []
        for row, a, e6 in zip(g["logw"], g["a"], g["loge6"]):
            if a == 0:
                continue
            vals = sorted(float(x) for x in row)
            lw = mp.iv.log(_iv(a))
            low.append(lw + sum((_iv(x) for x in vals[:R.K]), mp.iv.mpf(0)) - _iv(e6))
            high.append(lw + sum((_iv(x) for x in vals[-R.K:]), mp.iv.mpf(0)) - _iv(e6))
        return _iv_lse(low) + logc, _iv_lse(high) + logc
    if kind == "mix":
        bounds = [_score_bounds_iv(child) for v, child in zip(g["v"], g["children"]) if v > 0]
        lows, highs = [], []
        weights = [float(v) for v in g["v"] if v > 0]
        for v, (lo, hi) in zip(weights, bounds):
            lv = mp.iv.log(_iv(v))
            lows.append(lv + lo - logc)
            highs.append(lv + hi - logc)
        return _iv_lse(lows) + logc, _iv_lse(highs) + logc
    if kind == "parity":
        feasible = np.flatnonzero(np.isfinite(g["logcnt"]))
        values = []
        for m in feasible:
            values.append(_iv_lse([_iv(lp) + _iv(t) * _iv(g["g"][m]) - _iv(z)
                                   for lp, t, z in zip(g["lp"], g["theta"], g["logZ"])]))
        return min(values, key=lambda v: float(v.a)) + logc, max(values, key=lambda v: float(v.b)) + logc
    if kind == "sparse":
        low, high = [_iv(_scalar(g, "logoutside", finite=False))], [_iv(_scalar(g, "logoutside", finite=False))]
        for expert in g["experts"]:
            tmin, tmax = [], []
            for row in expert["theta"]:
                tmin.append(sum((_iv(x) if x < 0 else mp.iv.mpf(0) for x in row), mp.iv.mpf(0)))
                tmax.append(sum((_iv(x) if x > 0 else mp.iv.mpf(0) for x in row), mp.iv.mpf(0)))
            for output, extremes in ((low, tmin), (high, tmax)):
                groups = []
                for lwrow, logz, ext in zip(expert["logweights"], expert["logz_ratio"], extremes):
                    groups.extend((_iv(lw) + ext - _iv(logz), count)
                                  for lw, count in _float_counts(lwrow).items())
                output.append(_iv_lse_grouped(groups))
        return (_iv_lse(low) - _iv(_scalar(g, "logC")) + logc,
                _iv_lse(high) - _iv(_scalar(g, "logC")) + logc)
    raise TypeError(f"unsupported graph type: {kind}")


def _logq_iv(g, S):
    kind = g["type"]
    if kind == "cp":
        terms = []
        for row, a, e6 in zip(g["logw"], g["a"], g["loge6"]):
            if a == 0:
                continue
            terms.append(mp.iv.log(_iv(a)) + sum((_iv(row[i - 1]) for i in S), mp.iv.mpf(0)) - _iv(e6))
        return _iv_lse(terms)
    if kind == "mix":
        terms = [mp.iv.log(_iv(v)) + _logq_iv(child, S)
                 for v, child in zip(g["v"], g["children"]) if v > 0]
        return _iv_lse(terms)
    if kind == "parity":
        m = sum(i % 2 == 1 for i in S)
        return _iv_lse([_iv(lp) + _iv(t) * _iv(g["g"][m]) - _iv(z)
                        for lp, t, z in zip(g["lp"], g["theta"], g["logZ"])])
    if kind == "sparse":
        present = np.zeros(g["P"], dtype=bool)
        present[np.asarray(S) - 1] = True
        terms = [_iv(_scalar(g, "logoutside", finite=False))]
        for expert in g["experts"]:
            for row, lwrow, logz in zip(expert["theta"], expert["logweights"], expert["logz_ratio"]):
                grouped = {}
                for supports, lw in zip(expert["supports"], lwrow):
                    if np.isneginf(lw):
                        continue
                    mask = tuple(i for i, ball in enumerate(supports) if present[ball])
                    key = (float(lw), mask)
                    grouped[key] = grouped.get(key, 0) + 1
                for (lw, mask), count in grouped.items():
                    tilt = sum((_iv(row[i]) for i in mask), mp.iv.mpf(0))
                    terms.append(_iv(lw) + tilt - _iv(logz) + mp.iv.log(mp.iv.mpf(count)))
        return _iv_lse(terms) - _iv(g["logC"])
    raise TypeError(f"unsupported graph type: {kind}")


def score_bounds(g, _validated=False) -> tuple[float, float]:
    """Certified D enclosure.
    Stored float64 values are exact rational inputs, and iv arithmetic rounds outward.
    Selection and sorting are exact operations on the stored float64 values.
    Final binary64 conversion rounds the interval endpoints outward.
    """
    if not _validated:
        validate(g)
    mp.iv.prec = 113
    bounds = _score_bounds_iv(g)
    lo, hi = _outward(bounds[0], True), _outward(bounds[1], False)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError("score bounds must have finite endpoints")
    return lo, hi


def D_interval(g, S, _validated=False):
    if not _validated:
        validate(g)
        S = _validate_S(g, S)
    mp.iv.prec = 113
    value = _logq_iv(g, S) + mp.iv.log(mp.iv.mpf(math.comb(g["P"], R.K)))
    lo, hi = _outward(value, True), _outward(value, False)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError("D interval endpoints must be finite")
    return lo, hi
