#!/usr/bin/env python3
"""Eval Q-3 equation search — executes REGISTRATION_EVAL_Q3.md (hash 37cffb4899ab994b).

equation-analyst (Phase 5). Blind: never reads answer_key/, GENERATION_NOTES.md, *SEALED*.

Registered contract operationalization (design decisions, declared here BEFORE results
were seen; no post-hoc tuning):
- Family: fourier_k, k in {1,2,3}; canonical identifiable form
  a0 + sum_j [a_j sin(j*w*t) + b_j cos(j*w*t)]. No free phase.
- w: periodogram peak on TRAIN only, refined by least squares (golden-section on train
  SSE within +/-1.5 frequency bins of the peak, per k).
- Selection: minimize BIC on validation = n_v*ln(RMSE_v^2) + (2k+1)*ln(n_v).
  (BIC is monotone in validation RMSE at fixed k; lambda = BIC coefficient, fixed.)
- Null baselines (B=199 each, per type): generate a null series matched to the data
  ((1) permutation of x, (2) phase-randomized surrogate of x, (3) AR(1) fitted on real
  TRAIN), run the IDENTICAL select-and-fit procedure on the null series, then score the
  resulting equation on the REAL test split. p_type = (1 + #{null test-RMSE <= observed
  test-RMSE}) / (B+1). Rationale: nulls are competing equations for the real test data;
  a phase-randomized surrogate retains the amplitude spectrum but scrambles phase, so
  only genuine phase-locked structure beats it.
- Null-equation generator (A1, B=99 permuted series): identical procedure on each
  permuted series, scored on the permuted series' OWN test split (the procedure's
  self-calibration). improvement = perm_null_mean_RMSE - run_RMSE;
  null_adjusted_p = (1 + #{null improvement >= observed improvement}) / (B+1).
- Detectability floor: |c| < 0.10 -> coefficient masked "below_floor", not reportable.
- Bootstrap: moving-block (block=32) resampling of TRAIN residuals around the fitted
  train curve, B=199; re-estimate w (periodogram peak + refine, k fixed at k*) and
  coefficients; percentile 95% CIs. Reportable w requires CI half-width < 5% of w_hat.
- Residual checks on full-series residuals, MC bands at B=199 (the registered B):
  (a) ACF lags 1..10 vs simultaneous 95% band of max|acf| from permuted residuals;
  (b) residual periodogram max peak (Fisher-g style: max/mean power) vs band from
      PERMUTED residuals. DECLARED DEVIATION: phase-randomized surrogates of the
      residuals preserve the residual periodogram exactly (degenerate band); the
      card-12 intent (remaining periodicity vs white residuals) requires a
      spectrum-whitening surrogate, i.e. permutation. Flagged, not hidden.
  (c) CUSUM max|cumsum(r - rbar)|/(sigma*sqrt(n)) vs permuted-residual band.
  Check passes if p > 0.05 (a: observed max|acf| within band, i.e. p > 0.05).
- Verdicts: S3 (detection NULL) -> NO_EQUATION_ATTEMPTED, no code runs on its column.
  PREDICTIVE_EQUATION iff all three baseline p <= 0.05 AND generator null_adjusted_p
  <= 0.05 AND all residual checks clean AND bootstrap-stable (w CI criterion).
  Failed null comparison or structured residuals -> FAILED_EQUATION_SEARCH.
  Nulls+residuals pass but bootstrap unstable -> CANDIDATE_EQUATION (level 1 only).
- Data regimes (M4): eval synthetic series carry no provenance flags; the three
  regimes degenerate to all_rows (recorded per claim).
- Seeds: np.random.default_rng([20260611, claim_idx, stream]) — fully deterministic;
  two independent script runs must be byte-identical.
"""

import json
import sys

import numpy as np

SEED = 20260611
N = 512
TRAIN = slice(0, 307)
VAL = slice(307, 409)
TEST = slice(409, 512)
KS = (1, 2, 3)
FLOOR = 0.10
B_NULL = 199
B_GEN = 99
B_BOOT = 199
BLOCK = 32
DATA = ("/sessions/trusting-modest-carson/mnt/structure-discovery-lab/"
        "evals/structure_eval_set_v1/blind/datasets/series/series_wide.csv")

CLAIMS = [
    ("eq.eval.S1", "S1", "STRUCTURED", "periodogram positive; delay-embed H1 loop"),
    ("eq.eval.S2", "S2", "STRUCTURED", "periodic, related view of S1's cycle"),
    ("eq.eval.S3", "S3", "NULL", None),
    ("eq.eval.S4", "S4", "STRUCTURED", "cross-segment MMD (regime/changepoint type)"),
]

T = np.arange(N, dtype=float)


def design(t, w, k):
    cols = [np.ones_like(t)]
    for j in range(1, k + 1):
        cols.append(np.sin(j * w * t))
        cols.append(np.cos(j * w * t))
    return np.column_stack(cols)


def ols(t, x, w, k):
    X = design(t, w, k)
    beta, _, _, _ = np.linalg.lstsq(X, x, rcond=None)
    return beta


def rmse(r):
    return float(np.sqrt(np.mean(np.asarray(r) ** 2)))


def train_peak_omega(xtr):
    xc = xtr - xtr.mean()
    p = np.abs(np.fft.rfft(xc)) ** 2
    i = int(np.argmax(p[1:])) + 1
    n = len(xtr)
    return 2.0 * np.pi * i / n, 2.0 * np.pi / n


def refine_omega(t, x, w0, half, k, iters=30):
    gr = (np.sqrt(5.0) - 1.0) / 2.0
    a, b = max(w0 - half, 1e-6), min(w0 + half, np.pi)

    def sse(w):
        beta = ols(t, x, w, k)
        r = x - design(t, w, k) @ beta
        return float(r @ r)

    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = sse(c), sse(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = sse(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = sse(d)
    return 0.5 * (a + b)


def fit_procedure(x):
    """Identical select-and-fit pipeline. Returns selected model + per-k table."""
    xtr, ttr = x[TRAIN], T[TRAIN]
    w0, binw = train_peak_omega(xtr)
    table, best = [], None
    n_v = VAL.stop - VAL.start
    for k in KS:
        w = refine_omega(ttr, xtr, w0, 1.5 * binw, k)
        beta = ols(ttr, xtr, w, k)
        rv = x[VAL] - design(T[VAL], w, k) @ beta
        rmse_v = rmse(rv)
        bic = n_v * np.log(max(rmse_v, 1e-12) ** 2) + (2 * k + 1) * np.log(n_v)
        row = {"k": k, "omega": w, "rmse_val": rmse_v, "bic": bic, "beta": beta}
        table.append(row)
        if best is None or bic < best["bic"]:
            best = row
    best = dict(best)
    best["rmse_train"] = rmse(xtr - design(ttr, best["omega"], best["k"]) @ best["beta"])
    best["rmse_test_own"] = rmse(
        x[TEST] - design(T[TEST], best["omega"], best["k"]) @ best["beta"])
    best["table"] = table
    return best


def predict(model, sl):
    return design(T[sl], model["omega"], model["k"]) @ model["beta"]


def phase_surrogate(x, rng):
    F = np.fft.rfft(x)
    ph = rng.uniform(0.0, 2.0 * np.pi, len(F))
    Fs = np.abs(F) * np.exp(1j * ph)
    Fs[0] = F[0]
    Fs[-1] = np.abs(F[-1])  # N even: keep Nyquist real
    return np.fft.irfft(Fs, N)


def ar1_fit(xtr):
    xc = xtr - xtr.mean()
    phi = float(np.dot(xc[1:], xc[:-1]) / np.dot(xc[:-1], xc[:-1]))
    phi = float(np.clip(phi, -0.99, 0.99))
    innov = xc[1:] - phi * xc[:-1]
    return phi, float(np.std(innov)), float(xtr.mean())


def ar1_series(phi, sig, mu, rng):
    e = rng.normal(0.0, sig, N)
    out = np.empty(N)
    out[0] = e[0] / np.sqrt(1.0 - phi ** 2)
    for i in range(1, N):
        out[i] = phi * out[i - 1] + e[i]
    return out + mu


def acf(r, lags):
    rc = r - r.mean()
    den = float(rc @ rc)
    return np.array([float(rc[l:] @ rc[:-l]) / den for l in lags])


def fisher_g(r):
    rc = r - r.mean()
    p = np.abs(np.fft.rfft(rc)[1:]) ** 2
    return float(np.max(p) / np.mean(p))


def cusum_stat(r):
    rc = r - r.mean()
    return float(np.max(np.abs(np.cumsum(rc))) / (np.std(r) * np.sqrt(len(r))))


def mc_p(obs, nulls, ge=True):
    nulls = np.asarray(nulls)
    cnt = int(np.sum(nulls >= obs)) if ge else int(np.sum(nulls <= obs))
    return (1 + cnt) / (len(nulls) + 1)


def coef_names(k):
    names = ["a0"]
    for j in range(1, k + 1):
        names += [f"a{j}_sin{j}wt", f"b{j}_cos{j}wt"]
    return names


def analyze_claim(claim_id, col, x, ci):
    obs = fit_procedure(x)
    k, w, beta = obs["k"], obs["omega"], obs["beta"]
    rmse_test = rmse(x[TEST] - predict(obs, TEST))

    # --- null baselines: identical procedure on null series, scored on REAL test ---
    null_block, null_pass = {}, {}
    phi, sig, mu = ar1_fit(x[TRAIN])
    for si, (name, gen) in enumerate([
            ("permutation", lambda r: r.permutation(x)),
            ("phase_randomized", lambda r: phase_surrogate(x, r)),
            ("ar1_train", lambda r: ar1_series(phi, sig, mu, r))]):
        rng = np.random.default_rng([SEED, ci, 10 + si])
        scores = []
        for _ in range(B_NULL):
            m = fit_procedure(gen(rng))
            scores.append(rmse(x[TEST] - predict(m, TEST)))
        p = mc_p(rmse_test, scores, ge=False)
        null_block[name] = {"B": B_NULL, "null_rmse_on_real_test_mean": float(np.mean(scores)),
                            "null_rmse_on_real_test_q025": float(np.quantile(scores, 0.025)),
                            "p": p}
        null_pass[name] = p <= 0.05

    # --- null-equation generator (A1): B=99 permuted series, own-test scores ---
    rng = np.random.default_rng([SEED, ci, 20])
    gen_scores = []
    for _ in range(B_GEN):
        xs = rng.permutation(x)
        m = fit_procedure(xs)
        gen_scores.append(m["rmse_test_own"])
    perm_mean = float(np.mean(gen_scores))
    impr_obs = perm_mean - rmse_test
    impr_null = perm_mean - np.asarray(gen_scores)
    nap = mc_p(impr_obs, impr_null, ge=True)
    gen_block = {"B": B_GEN, "perm_null_mean_rmse": perm_mean,
                 "null_best_improvement": float(np.max(impr_null)),
                 "observed_improvement": float(impr_obs), "null_adjusted_p": nap}

    # --- bootstrap (moving-block, train residuals, k fixed at k*) ---
    ttr, xtr = T[TRAIN], x[TRAIN]
    fitted = design(ttr, w, k) @ beta
    res_tr = xtr - fitted
    ntr = len(xtr)
    nblocks = int(np.ceil(ntr / BLOCK))
    rng = np.random.default_rng([SEED, ci, 30])
    ws, betas = [], []
    for _ in range(B_BOOT):
        starts = rng.integers(0, ntr - BLOCK + 1, nblocks)
        rb = np.concatenate([res_tr[s:s + BLOCK] for s in starts])[:ntr]
        xb = fitted + rb
        w0b, binb = train_peak_omega(xb)
        wb = refine_omega(ttr, xb, w0b, 1.5 * binb, k)
        ws.append(wb)
        betas.append(ols(ttr, xb, wb, k))
    ws = np.asarray(ws)
    betas = np.asarray(betas)
    w_ci = [float(np.quantile(ws, 0.025)), float(np.quantile(ws, 0.975))]
    w_half = 0.5 * (w_ci[1] - w_ci[0])
    w_stable = bool(w_half < 0.05 * w)
    coefs = []
    for i, nm in enumerate(coef_names(k)):
        lo, hi = float(np.quantile(betas[:, i], 0.025)), float(np.quantile(betas[:, i], 0.975))
        val = float(beta[i])
        coefs.append({"name": nm, "estimate": round(val, 6) if abs(val) >= FLOOR else None,
                      "below_floor": bool(abs(val) < FLOOR),
                      "ci95": [round(lo, 6), round(hi, 6)]})

    # --- residual checks (full-series residuals, B=199 bands) ---
    r = x - np.concatenate([predict(obs, TRAIN), predict(obs, VAL), predict(obs, TEST)])
    lags = list(range(1, 11))
    a_obs = acf(r, lags)
    rng = np.random.default_rng([SEED, ci, 40])
    max_null = [float(np.max(np.abs(acf(rng.permutation(r), lags)))) for _ in range(B_NULL)]
    p_acf = mc_p(float(np.max(np.abs(a_obs))), max_null, ge=True)
    band95 = float(np.quantile(max_null, 0.95))
    rng = np.random.default_rng([SEED, ci, 41])
    g_null = [fisher_g(rng.permutation(r)) for _ in range(B_NULL)]
    p_g = mc_p(fisher_g(r), g_null, ge=True)
    rng = np.random.default_rng([SEED, ci, 42])
    c_null = [cusum_stat(rng.permutation(r)) for _ in range(B_NULL)]
    p_cusum = mc_p(cusum_stat(r), c_null, ge=True)
    resid = {
        "acf_lag1_10": {"values": [round(v, 4) for v in a_obs],
                        "max_abs": round(float(np.max(np.abs(a_obs))), 4),
                        "simultaneous_band95": round(band95, 4), "p": p_acf,
                        "pass": bool(p_acf > 0.05)},
        "periodogram_max_peak": {"fisher_g": round(fisher_g(r), 3), "p": p_g,
                                 "pass": bool(p_g > 0.05),
                                 "note": ("band from PERMUTED residuals; phase-randomized "
                                          "surrogates preserve the periodogram exactly "
                                          "(degenerate) — declared deviation")},
        "cusum": {"stat": round(cusum_stat(r), 4), "p": p_cusum,
                  "pass": bool(p_cusum > 0.05)},
    }
    resid_clean = all(v["pass"] for v in resid.values())
    nulls_ok = all(null_pass.values()) and nap <= 0.05

    if not nulls_ok or not resid_clean:
        verdict = "FAILED_EQUATION_SEARCH"
    elif w_stable:
        verdict = "PREDICTIVE_EQUATION"
    else:
        verdict = "CANDIDATE_EQUATION"

    return {
        "claim_id": claim_id, "series": col, "gate": "STRUCTURED (registered, post-freeze)",
        "verdict": verdict,
        "k_star": k,
        "selection_table": [{"k": r2["k"], "omega": round(r2["omega"], 6),
                             "rmse_val": round(r2["rmse_val"], 6),
                             "bic": round(r2["bic"], 3)} for r2 in obs["table"]],
        "omega_hat": round(w, 8), "period_hat": round(2 * np.pi / w, 4),
        "omega_ci95": [round(w_ci[0], 8), round(w_ci[1], 8)],
        "omega_ci_halfwidth_pct_of_omega": round(100 * w_half / w, 3),
        "omega_reportable": w_stable,
        "coefficients": coefs,
        "rmse": {"train": round(obs["rmse_train"], 6), "val": round(obs["rmse_val"], 6),
                 "test": round(rmse_test, 6)},
        "null_baselines": null_block,
        "null_equation_generator": gen_block,
        "residual_checks": resid,
        "bootstrap": {"B": B_BOOT, "block": BLOCK, "stable_omega": w_stable},
        "data_regimes": "all_rows only (eval synthetic; no provenance flags — regimes degenerate)",
    }


def main(out_path):
    raw = np.genfromtxt(DATA, delimiter=",", names=True)
    results = {"registration": "REGISTRATION_EVAL_Q3.md sha256:37cffb4899ab994b",
               "seed": SEED, "claims": {}}
    for ci, (claim_id, col, det, attr) in enumerate(CLAIMS):
        if det != "STRUCTURED":
            results["claims"][claim_id] = {
                "claim_id": claim_id, "series": col,
                "verdict": "NO_EQUATION_ATTEMPTED",
                "reason": "detection verdict NULL — gate failed; no fit, no code run on this column"}
            continue
        x = np.asarray(raw[col], dtype=float)
        out = analyze_claim(claim_id, col, x, ci)
        out["detection_attribution"] = attr
        results["claims"][claim_id] = out
    with open(out_path, "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", out_path)


if __name__ == "__main__":
    main(sys.argv[1])
