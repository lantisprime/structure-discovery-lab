"""Domain config: synthetic biased lottery chamber (Case Study 2).

Generates k-of-P without-replacement draws with *planted* inclusion-rate bias,
per docs/REGISTRATION_SYNTHETIC_BATCH1.md. Ground truth is known by
construction, so ANOMALY_REGISTRY holds the planted spec of the run at hand,
not adjudicated findings.

Mechanism: Gumbel top-k weighted sampling without replacement. With equal
weights this is exactly a uniform random permutation (matches the A1 null
simulator `core.discrete_draws.fast_draws`). Nominal bias is mapped to weights
at first order; the *realized* inclusion deviation must be measured with
`realized_delta()` and used in any frontier equation (see registration,
"Bias injection").

Interface (domain contract, see src/domains/pcso_lotto.py):
  DRAW_ENSEMBLES, DRAW_K, load_draws(...), covariates(),
  ANOMALY_REGISTRY, ERA_REGISTRY
"""

import numpy as np

DRAW_K = 6
DRAW_ENSEMBLES = {"Synthetic 6/55": 55}

ANOMALY_REGISTRY = []   # populated per-run with the planted spec (ground truth)
ERA_REGISTRY = []       # era structure is a property of each bias spec (tau)

MASTER_SEED = 20260612  # registered


# ---------------------------------------------------------------- bias specs

def fair_spec(P=55):
    return {"mode": "fair", "P": P}


def single_ball_spec(P, ball, eps):
    """One hot ball with nominal inclusion excess eps; mass-conserving
    (every other ball gives up eps/(P-1))."""
    return {"mode": "single", "P": P, "balls": [ball], "eps": float(eps)}


def multi_ball_spec(P, balls, total_eps):
    """Total nominal excess mass spread evenly over `balls`."""
    return {"mode": "multi", "P": P, "balls": list(balls),
            "eps": float(total_eps) / len(balls)}


def with_decay(spec, tau):
    """Wrap a spec with exponential amplitude decay: delta_t ~ exp(-t/tau).
    tau is in draws; tau=None or inf means no decay."""
    out = dict(spec)
    out["tau"] = None if tau in (None, float("inf")) else float(tau)
    return out


# ---------------------------------------------------------------- generator

def _base_weights(spec):
    """Nominal first-order weight vector w (length P), t=0 amplitude."""
    P = spec["P"]
    w = np.ones(P)
    if spec["mode"] == "fair":
        return w
    p0 = DRAW_K / P
    eps = spec["eps"]
    hot = np.asarray(spec["balls"], int) - 1
    w[hot] = (p0 + eps) / p0
    cold = np.setdiff1d(np.arange(P), hot)
    give = eps * len(hot) / len(cold)
    w[cold] = (p0 - give) / p0
    return w


def biased_draws(rng, T, spec, k=DRAW_K, t0=0):
    """T draws of k-of-P via Gumbel top-k with (possibly decaying) weights.

    t0: starting value of the decay clock, so a confirmation block can
    continue the same process (registration, "Datasets").
    Returns T x k int array, values 1..P, each row sorted-free (argsort order).
    """
    P = spec["P"]
    w = _base_weights(spec)
    logw = np.log(w)[None, :]                      # (1, P)
    tau = spec.get("tau")
    if tau is not None and spec["mode"] != "fair":
        amp = np.exp(-(t0 + np.arange(T)) / tau)[:, None]   # (T, 1)
        logw = amp * logw                          # log w scales ~ delta to 1st order
    g = -np.log(-np.log(rng.random((T, P))))       # Gumbel(0,1)
    return np.argsort(-(logw + g), axis=1)[:, :k] + 1


def realized_delta(spec, K=200_000, seed=None, k=DRAW_K):
    """MC estimate of realized per-ball inclusion-rate deviation from k/P,
    at t=0 amplitude (decay off). This — not the nominal eps — enters
    n_min(delta, alpha, beta)."""
    frozen = dict(spec, tau=None)
    rng = np.random.default_rng(MASTER_SEED if seed is None else seed)
    draws = biased_draws(rng, K, frozen, k=k)
    P = spec["P"]
    cnt = np.bincount(draws.ravel() - 1, minlength=P)
    return cnt / K - k / P


# ---------------------------------------------------------------- domain API

def load_draws(name, bias_spec=None, T=1000, seed=0, t0=0):
    """Generate T draws for ensemble `name` under `bias_spec` (default fair).
    Deterministic in (bias_spec, T, seed, t0)."""
    P = DRAW_ENSEMBLES[name]
    spec = bias_spec or fair_spec(P)
    assert spec["P"] == P, "spec pool size must match ensemble"
    rng = np.random.default_rng(seed)
    return biased_draws(rng, T, spec, t0=t0)


def covariates():
    """No external covariates in the synthetic chamber (thermal/pressure
    coupling is a future spec mode, not in Batch 1)."""
    import pandas as pd
    return pd.DataFrame(columns=["Date"])
