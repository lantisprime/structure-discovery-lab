#!/usr/bin/env python3
"""Equation-discovery v4 machinery — corrected per AUDIT E-1..E-6 and
PLAYBOOK_THEOREM_HARMONIZATION.md Q-1..Q-8. This module supplies the
corrected components; the v4 executor (pending REGISTRATION_EQ_TIDAL_V4,
HUMAN-GATE) assembles them. Nothing here fits real data on import.

E-1  select_family()      pure held-out NLL with TRAIN-estimated sigma^2;
                          optional pre-registered 1-SE parsimony tie-break.
                          NO complexity penalty stacked on held-out loss.
E-2  b_required(),        Monte Carlo budget scaled to the corrected alpha;
     corrected_alpha()    verdict-time correction applied IN-RUN.
E-4  profile_ci_omega()   profile-RSS confidence interval on a frequency
                          (residual bootstrap only after a whiteness gate).
E-6  residual_scan_mc()   pre-whiten declared lines, then ONE max-ordinate
                          spectral test against AR-matched surrogate nulls
                          (replaces iterative Fisher-g deletion).
E-3  confirmation gates   beat_baselines(): climatology + textbook a-priori
                          model, both registered; same-source data caps the
                          label at MECHANISM_CONSISTENT.
"""
import numpy as np


# ---- E-1: selection ---------------------------------------------------------
def heldout_nll(y_true, y_pred, sigma2_train):
    """Gaussian NLL of a held-out segment scored with TRAIN sigma^2
    (the frozen pipeline's nll() profiled sigma from the scored segment,
    making 'heldout_loglik' a mislabeled RMSE transform — audit E-1/F8)."""
    r = np.asarray(y_true) - np.asarray(y_pred)
    n = len(r)
    return 0.5 * (n * np.log(2 * np.pi * sigma2_train)
                  + np.sum(r ** 2) / sigma2_train)


def select_family(records, one_se_rule=False):
    """records: {name: {"nll_val": float, "nll_val_se": float|None,
                        "complexity": int}}
    Pure held-out selection. With one_se_rule (must be pre-registered),
    the least complex model within one SE of the minimum wins."""
    best = min(records, key=lambda k: records[k]["nll_val"])
    if not one_se_rule:
        return best
    se = records[best].get("nll_val_se")
    if se is None:
        raise ValueError("1-SE rule requires nll_val_se (e.g. from "
                         "block-bootstrap of the validation segment)")
    cands = [k for k, v in records.items()
             if v["nll_val"] <= records[best]["nll_val"] + se]
    return min(cands, key=lambda k: records[k]["complexity"])


# ---- E-2: multiplicity, applied in-run --------------------------------------
def corrected_alpha(alpha, m_family):
    return 1 - (1 - alpha) ** (1 / m_family)


def b_required(alpha_corrected):
    """Smallest null count B with floor 1/(B+1) <= alpha_corrected/2.
    At alpha=.05, m=10 -> alpha_c=.00512 -> B >= 390 (use 399)."""
    return int(np.ceil(2 / alpha_corrected)) - 1


def null_equation_p(J_obs, J_nulls):
    return (1 + int(np.sum(np.asarray(J_nulls) <= J_obs))) / (len(J_nulls) + 1)


def adjudicate(binding_p, alpha, m_family, B):
    """The verdict-time step the v1-v3 registrations deferred and never ran.
    Shared semantics with eq_verdict_correction.adjudicate (review minor 2):
    p > alpha is FAIL regardless of resolution — more B cannot rescue a
    failing p; the floor matters only for passes."""
    a = corrected_alpha(alpha, m_family)
    floor = 1 / (B + 1)
    if binding_p > a:
        return "FAIL_corrected"
    if abs(binding_p - floor) < 1e-12:
        return "AT_FLOOR_RESOLUTION_LIMITED"    # rerun at larger B
    if floor > a / 2:
        return "UNDER_RESOLVED_DESIGN"          # B too small for this m
    return "REJECT_H0_corrected"


# ---- E-6: calibrated residual spectral scan ----------------------------------
def _design(t, freqs):
    cols = [np.ones_like(t)]
    for f in freqs:
        cols += [np.cos(2 * np.pi * f * t), np.sin(2 * np.pi * f * t)]
    return np.stack(cols, 1)


def prewhiten(t, r, whitelist_freqs):
    """Fit-and-subtract the DECLARED whitelist lines (single joint LSQ)."""
    if not whitelist_freqs:
        return r
    X = _design(np.asarray(t, float), whitelist_freqs)
    beta, *_ = np.linalg.lstsq(X, r, rcond=None)
    return r - X @ beta


def _ar1_surrogate(r, rng):
    r = np.asarray(r, float)
    mu = r.mean()
    x = r - mu
    rho = float(np.corrcoef(x[:-1], x[1:])[0, 1])
    rho = np.clip(rho, -0.99, 0.99)
    e = x[1:] - rho * x[:-1]
    s = np.empty_like(x)
    s[0] = x[rng.integers(len(x))]
    innov = rng.choice(e, size=len(x) - 1, replace=True)
    for i in range(1, len(x)):
        s[i] = rho * s[i - 1] + innov[i - 1]
    return s + mu


def residual_scan_mc(t, resid, whitelist_freqs, rng, B=999):
    """ONE spectral test after pre-whitening: statistic = max periodogram
    ordinate share; null = AR(1)-matched bootstrap surrogates of the
    pre-whitened residuals, identical statistic. Replaces iterative Fisher-g
    with max-ordinate deletion (wrong conditional null; white-noise
    assumption false on fitted-model residuals — audit E-6)."""
    r = prewhiten(t, np.asarray(resid, float), whitelist_freqs)

    def stat(x):
        f = np.abs(np.fft.rfft(x - x.mean())[1:]) ** 2
        return float(f.max() / f.sum())

    obs = stat(r)
    nulls = [stat(_ar1_surrogate(r, rng)) for _ in range(B)]
    p = (1 + sum(v >= obs for v in nulls)) / (B + 1)
    return {"stat_max_ordinate_share": obs, "p": p, "B": B,
            "prewhitened_lines": list(map(float, whitelist_freqs))}


# ---- E-4: profile CI on a frequency ------------------------------------------
def profile_ci_omega(t, y, freqs, idx, level=0.95, grid_halfwidth=None,
                     n_grid=201):
    """Profile-RSS CI for freqs[idx]: grid the frequency, refit all linear
    coefficients (and keep other freqs fixed), invert the chi2 threshold.
    Avoids the residual-bootstrap CI, which treats unmodeled coherent lines
    as exchangeable noise (audit E-4)."""
    from scipy import stats as st
    t = np.asarray(t, float); y = np.asarray(y, float)
    freqs = list(freqs)
    span = t.max() - t.min()
    hw = grid_halfwidth if grid_halfwidth else 1.0 / span   # 1 Rayleigh
    grid = np.linspace(freqs[idx] - hw, freqs[idx] + hw, n_grid)

    def rss_at(f):
        fs = list(freqs); fs[idx] = f
        X = _design(t, fs)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return float(np.sum((y - X @ beta) ** 2))

    rss = np.array([rss_at(f) for f in grid])
    # +1: the profiled frequency itself is a fitted parameter
    n, k = len(y), 2 * len(freqs) + 1 + 1
    rss_min = rss.min()
    # finite-sample F-form of the profile bound (unknown variance):
    # (n-k) * (RSS/RSS_min - 1) <= F_{1, n-k}(level).
    # The asymptotic chi2 form (n*log(RSS/RSS_min) <= chi2_1) undercovers
    # (~90% at n=300 in the persisted smoke test); the F-form restores
    # nominal coverage (results/v4_smoke.json).
    thr = st.f.ppf(level, 1, n - k)
    ok = (n - k) * (rss / rss_min - 1) <= thr
    # widen by half a grid step: the true boundary lies between grid points
    # (grid discreteness alone cost ~5% coverage in the smoke test)
    step = grid[1] - grid[0]
    lo, hi = grid[ok].min() - step / 2, grid[ok].max() + step / 2
    edge_pinned = bool(ok[0] or ok[-1])
    return {"freq_hat": float(grid[rss.argmin()]), "ci": [float(lo), float(hi)],
            "level": level, "edge_pinned_widen_grid": edge_pinned,
            "identifiable_vs": None}


# ---- E-3: confirmation baselines ---------------------------------------------
def beat_baselines(rmse_frozen, y_new, baseline_preds, delta=0.0):
    """baseline_preds: {"B0_climatology": pred_array,
                        "B1_textbook_apriori": pred_array} — both REGISTERED
    before seeing the new data. Frozen equation must beat B0 strictly and be
    within (1+delta) of B1 (delta pre-registered)."""
    y = np.asarray(y_new, float)
    out, ok = {}, True
    for name, pred in baseline_preds.items():
        r = float(np.sqrt(np.mean((y - np.asarray(pred, float)) ** 2)))
        out[name] = r
    ok = rmse_frozen < out["B0_climatology"] and \
        rmse_frozen <= out["B1_textbook_apriori"] * (1 + delta)
    return {"rmse_frozen": rmse_frozen, "baseline_rmse": out,
            "passes": bool(ok)}


def confirmation_label(passes, independent_source):
    if not passes:
        return "CONFIRMATION_FAILED"
    return "MECHANISM_SUPPORTED" if independent_source else \
        "MECHANISM_CONSISTENT"     # same-generator data caps the label (E-3)
