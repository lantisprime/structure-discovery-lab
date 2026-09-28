"""Frozen, byte-stable PCSO laws and a reference evaluator."""
import base64
import ctypes
from fractions import Fraction
import hashlib
import json
import math

import mpmath as mp
import numpy as np
from scipy.special import logsumexp
from mpmath.libmp import from_float, mpf_cmp
from mpmath.ctx_iv import MPIntervalContext

_ivc = MPIntervalContext()
_ivc.prec = 113

import pcso_model_registry as R
from pcso_sparse_switch import THETA as SPARSE_THETA, SparseLaw, _logcomb

_MASS_CACHE = {}
# Committed ticket tie rule (clarification C3): the ticket is this float algorithm's output, an approximate maximum-inclusion set; tickets are descriptive.
TIE_RTOL = 1e-12


def _array(x, dtype):
    return np.array(x, dtype=dtype, copy=True)


def freeze(law, P) -> dict:
    """Copy a supported native law into a plain graph of arrays and scalars."""
    if isinstance(law, R.Law):
        if np.any(~np.isfinite(law.a)) or np.any(law.a < 0):
            raise ValueError("component weights must be finite and nonnegative")
        active = np.asarray(law.a) > 0
        if not np.any(active):
            raise ValueError("zero-weight components are not allowed in committed laws")
        return {"type": "cp", "P": P, "logw": _array(law.logw[active], np.float64),
                "a": _array(law.a[active], np.float64), "loge6": _array(law.loge6[active], np.float64)}
    if isinstance(law, R.MixLaw):
        if np.any(~np.isfinite(law.v)) or np.any(law.v < 0):
            raise ValueError("mixture weights must be finite and nonnegative")
        active = np.asarray(law.v) > 0
        if not np.any(active):
            raise ValueError("zero-weight components are not allowed in committed laws")
        return {"type": "mix", "P": P, "v": _array(law.v[active], np.float64),
                "children": [freeze(child, P) for child, keep in zip(law.laws, active) if keep]}
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
        arr = np.asarray(value, dtype=dtype).copy(order="C")
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
    lo, hi = certified_mass(graph, _validated=True)
    if Fraction(lo) < 1 - Fraction(1, 10**12) or Fraction(hi) > 1 + Fraction(1, 10**12):
        raise ValueError("law mass not certified within 1e-12 of 1")
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
        if np.any(a <= 0) or abs(float(a.sum()) - 1) > 1e-12:
            raise ValueError("zero-weight components are not allowed in committed laws; a must be positive and sum to 1")
        expected = np.empty(n, dtype=np.float64)
        for i, row in enumerate(lw):
            m = float(np.max(row))
            e6_scaled = float(R.esp(np.exp(row - m)[None, :])[0, R.K])
            if e6_scaled >= np.finfo(np.float64).tiny:
                expected[i] = 6 * m + math.log(e6_scaled)
            else:
                loge = np.full(R.K + 1, -math.inf)
                loge[0] = 0.0
                for x in row - m:
                    for k in range(R.K, 0, -1):
                        loge[k] = np.logaddexp(loge[k], x + loge[k - 1])
                expected[i] = 6 * m + loge[R.K]
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
        if np.any(v <= 0) or abs(float(v.sum()) - 1) > 1e-12:
            raise ValueError("zero-weight components are not allowed in committed laws; v must be positive and sum to 1")
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
        feasible = counts > 0
        q = (np.arange(R.K + 1) - 3.0) ** 2 + 6
        p0 = counts / counts.sum()
        expected_g = (q - p0 @ q) / math.sqrt(p0 @ (q - p0 @ q) ** 2)
        if np.any(np.abs(stat - expected_g) > 1e-12):
            raise ValueError("g does not match its construction")
        expected_cnt = np.log(np.maximum(counts, 1e-300))
        if (np.any(np.abs(cnt[feasible] - np.log(counts[feasible])) > 1e-10)
                or np.any(cnt[~feasible] != math.log(1e-300))):
            raise ValueError("logcnt does not match its construction")
        expected_z = logsumexp(np.where(feasible, expected_cnt[None, :] + np.outer(theta, stat), -math.inf), axis=1)
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
            if np.any(np.diff(supports.astype(np.int64), axis=1) <= 0):
                raise ValueError("support rows must be strictly increasing")
            if np.unique(supports, axis=0).shape[0] != supports.shape[0]:
                raise ValueError("support rows must be unique")
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
    """Raw formula value log r(S). The committed law is q = r/M (amendment 2, C1);
    decode's mass gate keeps |log M| <= ~1e-12; certified decisions use D_interval/score_bounds."""
    if not _validated:
        validate(g)
        S = _validate_S(g, S)
    return _logq(g, S)


def _cp_raw_inclusion(g):
    p = g["P"]
    active = g["a"] > 0
    rows, a, loge6 = g["logw"][active], g["a"][active], g["loge6"][active]
    n = rows.shape[0]
    shift = rows.max(axis=1)
    logx = rows - shift[:, None]
    # Log-domain prefix/suffix elementary symmetric sums, vectorized over rows.
    prefix = np.full((n, p + 1, R.K + 1), -math.inf, dtype=np.float64)
    suffix = np.full((n, p + 1, R.K + 1), -math.inf, dtype=np.float64)
    prefix[:, 0, 0] = suffix[:, p, 0] = 0.0
    for i in range(p):
        prefix[:, i + 1] = prefix[:, i]
        prefix[:, i + 1, 1:] = np.logaddexp(prefix[:, i, 1:], logx[:, i, None] + prefix[:, i, :-1])
    for i in range(p - 1, -1, -1):
        suffix[:, i] = suffix[:, i + 1]
        suffix[:, i, 1:] = np.logaddexp(suffix[:, i + 1, 1:], logx[:, i, None] + suffix[:, i + 1, :-1])
    logfactor = np.log(a) + 6 * shift - loge6
    row_logmass = logfactor + prefix[:, p, R.K]
    with np.errstate(divide="ignore"):
        # e5 without ball i: sum_k prefix[i][k] * suffix[i+1][5-k]
        loge5 = logsumexp(prefix[:, :p, :R.K] + suffix[:, 1:, :R.K][:, :, ::-1], axis=2)
        log_numerator = logsumexp(logfactor[:, None] + logx + loge5, axis=0)
    return log_numerator, float(logsumexp(row_logmass))


def _sparse_raw_inclusion(g):
    p = g["P"]
    numerator = np.zeros(p, dtype=np.float64)
    mass = np.float64(0)
    outside_mass = math.exp(_scalar(g, "logoutside", finite=False))
    outside_scale = math.comb(p, R.K) / math.exp(_scalar(g, "logC"))
    numerator += outside_mass * outside_scale * (R.K / p)
    mass += outside_mass * outside_scale
    for expert in g["experts"]:
        k = expert["k"]
        supports = expert["supports"].astype(np.int64)
        bits = np.array(np.meshgrid(*([[0, 1]] * k), indexing="ij")).reshape(k, -1).T
        hits = bits.sum(axis=1)
        terms = expert["theta"] @ bits.T + np.array(
            [_logcomb(p-k, R.K-int(h)) for h in hits])
        logz = logsumexp(terms, axis=1)
        inside = np.exp(terms - logz[:, None]) @ bits
        outside_terms = expert["theta"] @ bits.T + np.array(
            [_logcomb(p-k-1, R.K-1-int(h)) for h in hits])
        outside = np.exp(logsumexp(outside_terms, axis=1) - logz)
        weights = np.exp(expert["logweights"])
        row_weights = weights.sum(axis=1)
        row_scale = np.exp(logz - expert["logz_ratio"] - _scalar(g, "logC"))
        mass += np.sum(row_scale * row_weights)
        numerator += np.sum(row_scale * row_weights * outside)
        for j in range(k):
            correction = weights * (inside[:, j, None] - outside[:, None])
            numerator += np.bincount(supports[:, j], weights=(row_scale[:, None] * correction).sum(axis=0), minlength=p)
    # Correction terms can round a mathematically nonnegative numerator slightly below zero.
    with np.errstate(divide="ignore"):
        return np.log(np.maximum(numerator, 0.0)), math.log(mass)


def _raw_inclusion(g):
    kind = g["type"]
    if kind == "cp":
        return _cp_raw_inclusion(g)
    if kind == "mix":
        log_numerator_terms = []
        log_mass_terms = []
        for weight, child in zip(g["v"], g["children"]):
            if weight > 0:
                child_num, child_mass = _raw_inclusion(child)
                logweight = math.log(float(weight))
                log_numerator_terms.append(logweight + child_num)
                log_mass_terms.append(logweight + child_mass)
        return logsumexp(log_numerator_terms, axis=0), float(logsumexp(log_mass_terms))
    if kind == "parity":
        p = g["P"]
        odd = (p + 1) // 2
        even = p - odd
        r_m = np.zeros(R.K + 1, dtype=np.float64)
        counts = [0] * (R.K + 1)
        for m in range(R.K + 1):
            if 0 <= m <= odd and 0 <= R.K-m <= even:
                counts[m] = math.comb(odd, m) * math.comb(even, R.K-m)
                r_m[m] = math.exp(_lse(g["lp"] + g["theta"] * g["g"][m] - g["logZ"]))
        mass = sum(counts[m] * r_m[m] for m in range(R.K + 1))
        numerator = np.zeros(p, dtype=np.float64)
        for i in range(p):
            if i % 2 == 0:
                count_fn = lambda m: (math.comb(odd-1, m-1) * math.comb(even, R.K-m)
                                      if 0 <= m-1 <= odd-1 and 0 <= R.K-m <= even else 0)
            else:
                count_fn = lambda m: (math.comb(odd, m) * math.comb(even-1, R.K-1-m)
                                      if 0 <= m <= odd and 0 <= R.K-1-m <= even-1 else 0)
            numerator[i] = sum(count_fn(m) * r_m[m] for m in range(R.K + 1))
        return np.log(numerator), math.log(mass)
    if kind == "sparse":
        return _sparse_raw_inclusion(g)
    raise TypeError(f"unsupported graph type: {kind}")


def _inclusion(g):
    log_numerator, log_mass = _raw_inclusion(g)
    return np.minimum(1.0, np.exp(log_numerator - log_mass))

def inclusion(g, _validated=False):
    if not _validated:
        validate(g)
    return _inclusion(g)


def top6(g, tie_rtol=TIE_RTOL):
    return ticket_from_inclusion(inclusion(g), tie_rtol)


def ticket_from_inclusion(pi, tie_rtol=TIE_RTOL):
    """Maximum-inclusion ticket (clause 18) under the committed tie rule: at each pick, balls whose
    inclusion is within relative tie_rtol of the remaining maximum are tied; ties favour lower numbers."""
    remaining = list(range(len(pi)))
    chosen = []
    for _ in range(R.K):
        top = max(pi[i] for i in remaining)
        pick = min(i for i in remaining if pi[i] >= top * (1 - tie_rtol))
        chosen.append(pick)
        remaining.remove(pick)
    return sorted(i + 1 for i in chosen)


def _iv(x):
    """Create an exact interval input from a stored binary64 value."""
    return _ivc.mpf(float(x))


def _iv_lse(values):
    values = list(values)
    values = [v for v in values if not (float(v.a) == -math.inf and float(v.b) == -math.inf)]
    if not values:
        return _ivc.mpf("-inf")
    pivot_value = values[0]
    for value in values[1:]:
        if mpf_cmp(value._mpi_[1], pivot_value._mpi_[1]) > 0:
            pivot_value = value
    pivot = float(pivot_value.b)
    p = _iv(pivot)
    return p + _ivc.log(sum((_ivc.exp(v - p) for v in values), _ivc.mpf(0)))


def _iv_lse_grouped(groups):
    """Log-sum-exp of (interval term, integer multiplicity) pairs."""
    groups = [(term, int(count)) for term, count in groups if count]
    if not groups:
        return _ivc.mpf("-inf")
    pivot_value = groups[0][0]
    for term, _ in groups[1:]:
        if mpf_cmp(term._mpi_[1], pivot_value._mpi_[1]) > 0:
            pivot_value = term
    pivot = float(pivot_value.b)
    p = _iv(pivot)
    total = sum((_ivc.mpf(count) * _ivc.exp(term - p) for term, count in groups), _ivc.mpf(0))
    return p + _ivc.log(total)


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
    cmp = mpf_cmp(from_float(f, 53, "n"), endpoint._mpi_[0 if lower else 1])
    if lower and cmp > 0:
        f = math.nextafter(f, -math.inf)
    elif not lower and cmp < 0:
        f = math.nextafter(f, math.inf)
    return f


def _score_bounds_iv(g):
    kind = g["type"]
    p = g["P"]
    logc = _ivc.log(_ivc.mpf(math.comb(p, R.K)))
    if kind == "cp":
        low, high = [], []
        for row, a, e6 in zip(g["logw"], g["a"], g["loge6"]):
            if a == 0:
                continue
            vals = sorted(float(x) for x in row)
            lw = _ivc.log(_iv(a))
            low.append(lw + sum((_iv(x) for x in vals[:R.K]), _ivc.mpf(0)) - _iv(e6))
            high.append(lw + sum((_iv(x) for x in vals[-R.K:]), _ivc.mpf(0)) - _iv(e6))
        return _iv_lse(low) + logc, _iv_lse(high) + logc
    if kind == "mix":
        bounds = [_score_bounds_iv(child) for v, child in zip(g["v"], g["children"]) if v > 0]
        lows, highs = [], []
        weights = [float(v) for v in g["v"] if v > 0]
        for v, (lo, hi) in zip(weights, bounds):
            lv = _ivc.log(_iv(v))
            lows.append(lv + lo - logc)
            highs.append(lv + hi - logc)
        return _iv_lse(lows) + logc, _iv_lse(highs) + logc
    if kind == "parity":
        odd = (p + 1) // 2
        feasible = [m for m in range(R.K + 1)
                    if 0 <= m <= odd and 0 <= R.K - m <= p - odd]
        values = []
        for m in feasible:
            values.append(_iv_lse([_iv(lp) + _iv(t) * _iv(g["g"][m]) - _iv(z)
                                   for lp, t, z in zip(g["lp"], g["theta"], g["logZ"])]))
        lo, hi = values[0], values[0]
        for value in values[1:]:
            if mpf_cmp(value._mpi_[0], lo._mpi_[0]) < 0:
                lo = value
            if mpf_cmp(value._mpi_[1], hi._mpi_[1]) > 0:
                hi = value
        return lo + logc, hi + logc
    if kind == "sparse":
        low, high = [_iv(_scalar(g, "logoutside", finite=False))], [_iv(_scalar(g, "logoutside", finite=False))]
        for expert in g["experts"]:
            tmin, tmax = [], []
            for row in expert["theta"]:
                tmin.append(sum((_iv(x) if x < 0 else _ivc.mpf(0) for x in row), _ivc.mpf(0)))
                tmax.append(sum((_iv(x) if x > 0 else _ivc.mpf(0) for x in row), _ivc.mpf(0)))
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
            terms.append(_ivc.log(_iv(a)) + sum((_iv(row[i - 1]) for i in S), _ivc.mpf(0)) - _iv(e6))
        return _iv_lse(terms)
    if kind == "mix":
        terms = [_ivc.log(_iv(v)) + _logq_iv(child, S)
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
                    tilt = sum((_iv(row[i]) for i in mask), _ivc.mpf(0))
                    terms.append(_iv(lw) + tilt - _iv(logz) + _ivc.log(_ivc.mpf(count)))
        return _iv_lse(terms) - _iv(g["logC"])
    raise TypeError(f"unsupported graph type: {kind}")


def _mass_interval(g):
    lo, hi = certified_mass(g, _validated=True)
    return _ivc.mpf([lo, hi])


def score_bounds(g, _validated=False) -> tuple[float, float]:
    """Certified D enclosure.
    Stored float64 values are exact rational inputs, and iv arithmetic rounds outward.
    Selection and sorting are exact operations on the stored float64 values.
    Final binary64 conversion rounds the interval endpoints outward.
    """
    if not _validated:
        validate(g)
    bounds = _score_bounds_iv(g)
    if (not math.isfinite(float(bounds[0].a)) or not math.isfinite(float(bounds[1].b))):
        raise ValueError("score bounds must have finite endpoints")
    log_mass = _ivc.log(_mass_interval(g))
    lo, hi = _outward(bounds[0] - log_mass, True), _outward(bounds[1] - log_mass, False)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError("score bounds must have finite endpoints")
    return lo, hi


def D_interval(g, S, _validated=False):
    if not _validated:
        validate(g)
        S = _validate_S(g, S)
    value = (_logq_iv(g, S) - _ivc.log(_mass_interval(g))
             + _ivc.log(_ivc.mpf(math.comb(g["P"], R.K))))
    lo, hi = _outward(value, True), _outward(value, False)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError("D interval endpoints must be finite")
    return lo, hi


def _certified_mass_cp_reference(g):
    """Pure interval-recursion reference for CP mass certification."""
    total = _ivc.mpf(0)
    for row, a, loge6 in zip(g["logw"], g["a"], g["loge6"]):
        if a == 0:
            continue
        shift = max(float(x) for x in row)
        e = [_ivc.mpf(1)] + [_ivc.mpf(0)] * R.K
        for x in row:
            xv = _ivc.exp(_iv(x) - _iv(shift))
            for k in range(R.K, 0, -1):
                e[k] += xv * e[k - 1]
        total += _iv(a) * _ivc.exp(6 * _iv(shift) - _iv(loge6)) * e[R.K]
    return total


def _round_to_nearest_available():
    """Return whether the process floating-point mode is known to be round-to-nearest."""
    try:
        getround = ctypes.CDLL(None).fegetround
        getround.restype = ctypes.c_int
        return getround() == 0  # FE_TONEAREST on supported NumPy platforms.
    except (AttributeError, OSError):
        return False


def _certified_mass_cp_fast(g):
    """Certified x endpoints feed monotone float64 ESP recurrences for x_lo/x_hi.
    Each e6 path has at most 2P roundings; Higham (2002), Lemma 3.1, gives gamma_n,
    n=2P+2 and u=2**-53; the exact e6 lies in [c/(1+gamma), c/(1-gamma)] (gamma in iv).
    Remaining a, shift and loge6 factors are enclosed by interval arithmetic.
    """
    rows = g["logw"]
    active = g["a"] > 0
    if not np.any(active):
        return _ivc.mpf(0)
    rows = rows[active]
    weights = g["a"][active]
    loge6s = g["loge6"][active]
    shifts = np.max(rows, axis=1)
    x_lo = np.empty(rows.shape, dtype=np.float64)
    x_hi = np.empty(rows.shape, dtype=np.float64)
    for i, (row, shift) in enumerate(zip(rows, shifts)):
        for j, x in enumerate(row):
            bounds = _ivc.exp(_iv(x) - _iv(shift))
            x_lo[i, j] = _outward(bounds, True)
            x_hi[i, j] = _outward(bounds, False)
    tiny = np.finfo(np.float64).tiny
    if np.any(x_hi < tiny):
        return None

    def esp_float(xs):
        e = np.zeros((len(xs), R.K + 1), dtype=np.float64)
        e[:, 0] = 1.0
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            for col in range(xs.shape[1]):
                for k in range(R.K, 0, -1):
                    prod = xs[:, col] * e[:, k - 1]
                    # Any product or sum below the normal range voids the relative-error model.
                    if np.any((e[:, k - 1] > 0) & (prod < tiny)):
                        return None
                    e[:, k] += prod
                    if np.any((e[:, k] > 0) & (e[:, k] < tiny)):
                        return None
        return e[:, R.K]

    p = rows.shape[1]
    nu = _ivc.mpf(2 * p + 2) * _ivc.mpf(2.0 ** -53)
    gamma = nu / (1 - nu)
    e_low, e_high = esp_float(x_lo), esp_float(x_hi)
    if e_low is None or e_high is None:
        return None
    total = _ivc.mpf(0)
    for a, shift, loge6, low, high in zip(weights, shifts, loge6s, e_low, e_high):
        # computed = exact * (1 + theta), |theta| <= gamma  =>  exact in [c/(1+gamma), c/(1-gamma)].
        low_bound = _iv(low) / (1 + gamma)
        high_bound = _iv(high) / (1 - gamma)
        e6 = _ivc.mpf([max(0.0, _outward(low_bound, True)),
                       _outward(high_bound, False)])
        total += (_iv(a) * _ivc.exp(6 * _iv(shift) - _iv(loge6)) * e6)
    return total


def _certified_mass_iv(g):
    kind = g["type"]
    if kind == "cp":
        if _round_to_nearest_available():
            fast = _certified_mass_cp_fast(g)
            if fast is not None:
                return fast
        return _certified_mass_cp_reference(g)
    if kind == "mix":
        return sum((_iv(v) * _certified_mass_iv(child)
                    for v, child in zip(g["v"], g["children"]) if v > 0), _ivc.mpf(0))
    if kind == "parity":
        p = g["P"]
        odd = (p + 1) // 2
        total = _ivc.mpf(0)
        for m in range(R.K + 1):
            if not (0 <= m <= odd and 0 <= R.K - m <= p - odd):
                continue
            count = math.comb(odd, m) * math.comb(p - odd, R.K - m)
            for lp, theta, logz in zip(g["lp"], g["theta"], g["logZ"]):
                total += (_ivc.mpf(count) * _ivc.exp(
                    _iv(lp) + _iv(theta) * _iv(g["g"][m]) - _iv(logz)))
        return total
    if kind == "sparse":
        count = math.comb(g["P"], R.K)
        denom = _ivc.mpf(count)
        scale = denom / _ivc.exp(_iv(_scalar(g, "logC")))
        total = scale * _ivc.exp(_iv(_scalar(g, "logoutside", finite=False)))
        for expert in g["experts"]:
            k = expert["k"]
            bits = np.array(np.meshgrid(*([[0, 1]] * k), indexing="ij")).reshape(k, -1).T
            hits = bits.sum(axis=1)
            for theta, logz, lwrow in zip(expert["theta"], expert["logz_ratio"], expert["logweights"]):
                u = _ivc.mpf(0)
                for mask, h in zip(bits, hits):
                    count = math.comb(g["P"] - k, R.K - int(h)) if 0 <= R.K - int(h) <= g["P"] - k else 0
                    if count:
                        tilt = sum((_iv(t) for t, bit in zip(theta, mask) if bit), _ivc.mpf(0))
                        u += _ivc.exp(tilt) * count / denom
                weight_counts = _float_counts(lwrow)
                weight_total = _iv_lse_grouped(
                    (_iv(lw), count) for lw, count in weight_counts.items())
                weight_total = _ivc.exp(weight_total)
                total += scale * weight_total * u / _ivc.exp(_iv(logz))
        return total
    raise TypeError(f"unsupported graph type: {kind}")


def certified_mass(g, _validated=False) -> tuple[float, float]:
    """Enclose the total mass of the stored law.
    Uses interval arithmetic with outward rounding.
    Does not enumerate six-subsets.
    """
    if not _validated:
        validate(g)
    key = hashlib.sha256(encode(g)).digest()
    if key in _MASS_CACHE:
        return _MASS_CACHE[key]
    mass = _certified_mass_iv(g)
    lo, hi = _outward(mass, True), _outward(mass, False)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError("certified mass endpoints must be finite")
    _MASS_CACHE[key] = (lo, hi)
    return _MASS_CACHE[key]
