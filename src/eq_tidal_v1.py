#!/usr/bin/env python3
"""
eq_tidal_v1.py — Phase 5 registered equation fit (EXECUTE-ONLY).

Registration: docs/REGISTRATION_EQ_TIDAL.md
  sha256 9df78eca25e20ab5... (approved 2026-06-11, pre-fit, commitment-hashed).
Claims:
  A: eq.tidal-manila.phase.v1           target "Total tidal accel (g)"
  B: eq.tidal-manila.phase.moondist.v1  target "Moon Dist (km)"

Everything below executes the registered contract verbatim:
  - families A1/A2/A3 (claim A), B1/B2 (claim B); sin/cos pairs only, no free phase
  - chronological splits 60/20/20; omega estimation on train ONLY
  - period window 4-120 d; grid step = Rayleigh/4 of train span; NLS refine
  - complexity = (#linear coeffs) + 2*(#free freqs); lambda = ln(n_train)/2 (fixed)
  - J = NLL_validation + lambda*complexity; min-J selection; single test evaluation
  - null-equation generator: B=200 per null type per claim
    (permutation, phase_randomized_surrogate, AR(p<=5 by AIC))
  - moving-block bootstrap, block 15 d, B_boot=500
  - residual checks 1-7 of registration section 7
  - detectability floor: amplitude >= 4*sigma_hat*sqrt(2/n_train)
  - seed scheme (run_ledger eq_tidal_v1): base 20260611, +1 per stage in ledger
    stage order [null_equation_generator,+0][fit,+1][nulls,+2][bootstrap,+3][residuals,+4]
  - two-run rule: full pipeline executed twice in-process; canonical JSON bytes compared

Declared (conservative) deviations from registration text: none in procedure.
Implementation notes recorded in results JSON "implementation_notes".
"""
import csv, json, math, zlib, sys, os
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import chi2
from scipy.special import gammaln
from ripser import ripser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "datasets", "tidal-manila", "tidal_derived.csv")
OUT = os.path.join(ROOT, "results", "eq_tidal_v1.json")

BASE_SEED = 20260611
STAGE = {"null_equation_generator": 0, "fit": 1, "nulls": 2, "bootstrap": 3, "residuals": 4}

PMIN, PMAX = 4.0, 120.0
B_NULLS = 200
B_BOOT = 500
BLOCK = 15
ALPHA_NULL = 0.01          # registered acceptance threshold per null type
ALPHA_RESID = 0.05         # declared residual-check alpha (stricter alpha = easier to
                           # demote = conservative; raw p-values reported regardless)
GROUND = {"spring_neap": 14.765, "anomalistic": 27.555}
TOL = {  # registered section 8 tolerance bands (+-5%)
    "A": {"spring_neap": (14.03, 15.50), "anomalistic": (26.18, 28.93)},
    "B": {"anomalistic": (26.18, 28.93)},
}
FAMILIES = {  # family id -> (n_free_freqs, K harmonics per base freq), complexity
    "A": [("A1_harmonic_1freq_k1", 1, 1), ("A2_harmonic_2freq_k1", 2, 1), ("A3_harmonic_2freq_k2", 2, 2)],
    "B": [("B1_harmonic_1freq_k1", 1, 1), ("B2_harmonic_1freq_k2", 1, 2)],
}

def complexity(nf, K):
    return (1 + 2 * K * nf) + 2 * nf  # linear coeffs (a0 + K sin/cos pairs per freq) + 2/freq

def design(t, freqs, K):
    cols = [np.ones_like(t)]
    for f in freqs:
        for k in range(1, K + 1):
            w = 2 * np.pi * k * f * t
            cols.append(np.sin(w)); cols.append(np.cos(w))
    return np.column_stack(cols)

def lsq(t, y, freqs, K):
    X = design(t, freqs, K)
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    rss = float(np.sum((y - X @ coef) ** 2))
    return coef, rss

def nll(rss, n):
    rss = max(rss, 1e-300)
    return 0.5 * n * (math.log(2 * math.pi * rss / n) + 1.0)

def grid_rss(t, y, grid):
    """Vectorized profiled RSS for design [1, sin, cos] at each grid frequency."""
    n = len(t)
    S = np.sin(2 * np.pi * np.outer(grid, t)); C = np.cos(2 * np.pi * np.outer(grid, t))
    ones = np.ones(n)
    A = np.empty((len(grid), 3, 3)); b = np.empty((len(grid), 3))
    A[:, 0, 0] = n
    A[:, 0, 1] = A[:, 1, 0] = S @ ones
    A[:, 0, 2] = A[:, 2, 0] = C @ ones
    A[:, 1, 1] = np.einsum("ij,ij->i", S, S)
    A[:, 2, 2] = np.einsum("ij,ij->i", C, C)
    A[:, 1, 2] = A[:, 2, 1] = np.einsum("ij,ij->i", S, C)
    b[:, 0] = y.sum(); b[:, 1] = S @ y; b[:, 2] = C @ y
    coef = np.linalg.solve(A + 1e-12 * np.eye(3), b[:, :, None])[:, :, 0]
    return float(np.dot(y, y)) - np.einsum("ij,ij->i", coef, b)

def refine_one(t, y, freqs, K, idx, df):
    """NLS-refine frequency idx (coeffs profiled out) within +-df of current value."""
    f0 = freqs[idx]
    def obj(f):
        fr = list(freqs); fr[idx] = f
        return lsq(t, y, fr, K)[1]
    lo, hi = max(f0 - df, 1.0 / PMAX), min(f0 + df, 1.0 / PMIN)
    r = minimize_scalar(obj, bounds=(lo, hi), method="bounded",
                        options={"xatol": 1e-10})
    return float(r.x)

def discover(t_tr, y_tr, t_va, y_va, t_te, y_te, claim, lam):
    """Registered section 4 procedure. All omega estimation on train only.
    Returns per-family records and the J-selected family."""
    span = float(t_tr[-1] - t_tr[0])
    df = 1.0 / (4.0 * span)
    grid = np.arange(1.0 / PMAX, 0.25 + df / 2, df)
    rss_grid = grid_rss(t_tr, y_tr, grid)
    f1g = float(grid[int(np.argmin(rss_grid))])
    # second frequency (2-freq families): grid on residual of refined-f1 K=1 fit
    f2g = None
    if any(nf == 2 for _, nf, _ in FAMILIES[claim]):
        f1r = refine_one(t_tr, y_tr, [f1g], 1, 0, df)
        c, _ = lsq(t_tr, y_tr, [f1r], 1)
        resid = y_tr - design(t_tr, [f1r], 1) @ c
        rg2 = grid_rss(t_tr, resid, grid)
        mask = np.abs(grid - f1r) < 1.0 / span  # exclude within one Rayleigh of f1
        rg2[mask] = np.inf
        f2g = float(grid[int(np.argmin(rg2))])
    fam_records = {}
    for fam, nf, K in FAMILIES[claim]:
        freqs = [f1g] if nf == 1 else [f1g, f2g]
        # per-family NLS refinement with that family's own design (coordinate descent)
        for _ in range(3 if nf == 2 else 1):
            for i in range(nf):
                freqs[i] = refine_one(t_tr, y_tr, freqs, K, i, df)
        coef, rss_tr = lsq(t_tr, y_tr, freqs, K)
        rss_va = float(np.sum((y_va - design(t_va, freqs, K) @ coef) ** 2))
        J = nll(rss_va, len(y_va)) + lam * complexity(nf, K)
        rss_te = float(np.sum((y_te - design(t_te, freqs, K) @ coef) ** 2))
        fam_records[fam] = {
            "freqs": [float(f) for f in freqs], "periods_d": [float(1 / f) for f in freqs],
            "K": K, "coef": [float(c) for c in coef], "complexity": complexity(nf, K),
            "rss_train": rss_tr, "nll_val": nll(rss_va, len(y_va)), "J_val": float(J),
            "rmse_val": math.sqrt(rss_va / len(y_va)),
            "nll_test": nll(rss_te, len(y_te)), "rmse_test": math.sqrt(rss_te / len(y_te)),
        }
    fstar = min(fam_records, key=lambda k: fam_records[k]["J_val"])
    return fam_records, fstar

def standardize_splits(y, i1, i2, t):
    mu, sd = float(np.mean(y[:i1])), float(np.std(y[:i1]))
    z = (y - mu) / sd
    return (t[:i1], z[:i1], t[i1:i2], z[i1:i2], t[i2:], z[i2:], mu, sd)

# ---------- null series generators (full length; procedure restandardizes) ----------
def gen_permutation(y, rng):
    return y[rng.permutation(len(y))]

def gen_phase_surrogate(y, rng):
    n = len(y)
    Z = np.fft.rfft(y)
    mag = np.abs(Z)
    ph = rng.uniform(0, 2 * np.pi, len(Z))
    ph[0] = 0.0
    if n % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(mag * np.exp(1j * ph), n)

def fit_ar_train(y_tr):
    """Yule-Walker AR(p), p in 1..5 by AIC."""
    x = y_tr - y_tr.mean()
    n = len(x)
    acov = np.array([np.dot(x[:n - k], x[k:]) / n for k in range(6)])
    best = None
    for p in range(1, 6):
        R = np.array([[acov[abs(i - j)] for j in range(p)] for i in range(p)])
        r = acov[1:p + 1]
        phi = np.linalg.solve(R + 1e-12 * np.eye(p), r)
        s2 = max(acov[0] - phi @ r, 1e-300)
        aic = n * math.log(s2) + 2 * p
        if best is None or aic < best[0]:
            best = (aic, p, phi, s2)
    return best[1], best[2], best[3], float(y_tr.mean())

def gen_ar(n, phi, s2, mu, rng):
    p = len(phi)
    burn = 200
    e = rng.normal(0, math.sqrt(s2), n + burn)
    x = np.zeros(n + burn)
    for i in range(p, n + burn):
        x[i] = phi @ x[i - p:i][::-1] + e[i]
    return x[burn:] + mu

# ---------- residual checks ----------
def ljung_box(r, lags=40):
    n = len(r); x = r - r.mean()
    denom = float(np.dot(x, x))
    Q = 0.0
    for k in range(1, lags + 1):
        rho = float(np.dot(x[:n - k], x[k:]) / denom)
        Q += rho * rho / (n - k)
    Q *= n * (n + 2)
    return float(Q), float(chi2.sf(Q, lags))

def fisher_g(r):
    n = len(r); x = r - r.mean()
    F = np.fft.rfft(x)
    I = (np.abs(F) ** 2)[1:(n // 2 + (0 if n % 2 == 0 else 1))]
    fr = np.fft.rfftfreq(n, 1.0)[1:len(I) + 1]
    win = (fr >= 1.0 / PMAX) & (fr <= 1.0 / PMIN)
    Iw = I[win]
    m = len(Iw)
    g = float(Iw.max() / Iw.sum())
    pk = float(1.0 / fr[win][int(np.argmax(Iw))])
    # exact Fisher upper tail
    p, j = 0.0, 1
    while j <= min(m, int(1.0 / g)) and j <= 60:
        term = math.exp(gammaln(m + 1) - gammaln(j + 1) - gammaln(m - j + 1)
                        + (m - 1) * math.log1p(-j * g)) if 1 - j * g > 0 else 0.0
        p += term if j % 2 == 1 else -term
        j += 1
    return g, float(min(max(p, 0.0), 1.0)), pk, m

def mmd_test(r, rng, B=200):
    z = (r - r.mean()) / r.std()
    n = len(z)
    gph = rng.normal(0, 1, n)
    pool = np.concatenate([z, gph])
    D = (pool[:, None] - pool[None, :]) ** 2
    med = np.median(D[D > 0])
    Kk = np.exp(-D / med)
    def stat(idx):
        a, b = idx[:n], idx[n:]
        return (Kk[np.ix_(a, a)].mean() + Kk[np.ix_(b, b)].mean() - 2 * Kk[np.ix_(a, b)].mean())
    obs = stat(np.arange(2 * n))
    cnt = 0
    for _ in range(B):
        idx = rng.permutation(2 * n)
        if stat(idx) >= obs:
            cnt += 1
    return float(obs), float((1 + cnt) / (B + 1))

def breusch_pagan(r, t):
    u = r ** 2
    X = np.column_stack([np.ones_like(t), t])
    beta, _, _, _ = np.linalg.lstsq(X, u, rcond=None)
    fit = X @ beta
    ssr = float(np.sum((fit - u.mean()) ** 2)); sst = float(np.sum((u - u.mean()) ** 2))
    R2 = ssr / sst if sst > 0 else 0.0
    LM = len(r) * R2
    return float(LM), float(chi2.sf(LM, 1))

def cusum_test(r, rng, B=200):
    def stat(x):
        s = np.cumsum(x - x.mean())
        return float(np.max(np.abs(s)) / (x.std() * math.sqrt(len(x))))
    obs = stat(r)
    cnt = sum(stat(r[rng.permutation(len(r))]) >= obs for _ in range(B))
    return obs, float((1 + cnt) / (B + 1))

def delay_embed(y, tau=3, dim=3):
    n = len(y) - (dim - 1) * tau
    return np.column_stack([y[i * tau:i * tau + n] for i in range(dim)])

def max_h1(X):
    dgm = ripser(X, maxdim=1)["dgms"][1]
    return float((dgm[:, 1] - dgm[:, 0]).max()) if len(dgm) else 0.0

def tda_check(r, rng, B=99):
    z = (r - r.mean()) / r.std()
    obs = max_h1(delay_embed(z))
    cnt = sum(max_h1(delay_embed(z[rng.permutation(len(z))])) >= obs for _ in range(B))
    return obs, float((1 + cnt) / (B + 1))

def compression_check(r, rng, B=200):
    def size(x):
        z = (x - x.mean()) / x.std()
        q = np.clip((z / 8.0 + 0.5) * 255, 0, 255).astype(np.uint8)
        return len(zlib.compress(q.tobytes(), 9))
    obs = size(r)
    cnt = sum(size(rng.normal(0, 1, len(r))) <= obs for _ in range(B))
    return obs, float((1 + cnt) / (B + 1))

# ---------- helpers ----------
def amp_phase(coef, K, nf):
    out = []
    for i in range(nf):
        for k in range(1, K + 1):
            a = coef[1 + 2 * (i * K + k - 1)]; b = coef[2 + 2 * (i * K + k - 1)]
            out.append({"freq_index": i, "harmonic": k,
                        "amplitude": float(math.hypot(a, b)),
                        "phase_rad": float(math.atan2(a, b)),
                        "a_sin": float(a), "b_cos": float(b)})
    return out

def match_period(p, claim):
    best, bd = None, None
    for name, gt in GROUND.items():
        if name not in TOL[claim]:
            continue
        d = abs(p - gt)
        if bd is None or d < bd:
            best, bd = name, d
    return best

# ---------- the full registered pipeline ----------
def run_pipeline():
    dates, cols = [], {"Moon Dist (km)": [], "Total tidal accel (g)": []}
    with open(DATA) as f:
        for row in csv.DictReader(f):
            dates.append(row["Date"])
            for c in cols:
                cols[c].append(float(row[c]))
    n = len(dates)
    t = np.arange(n, dtype=float)
    i1, i2 = int(round(0.6 * n)), int(round(0.8 * n))
    lam = math.log(i1) / 2.0

    results = {"registration": "docs/REGISTRATION_EQ_TIDAL.md sha256 9df78eca25e20ab5 (approved pre-fit)",
               "script": "src/eq_tidal_v1.py", "data_file": "datasets/tidal-manila/tidal_derived.csv",
               "n_rows": n, "date_range": [dates[0], dates[-1]],
               "splits": {"train": [0, i1], "validation": [i1, i2], "test": [i2, n]},
               "lambda": lam, "data_regimes": ["all_rows"],
               "seed_scheme": {"base": BASE_SEED, "stage_offsets": STAGE},
               "alpha_null": ALPHA_NULL, "alpha_resid_declared": ALPHA_RESID,
               "implementation_notes": [
                   "scipy unavailable at dispatch -> installed scipy+ripser (same stack as batch5)",
                   "all series standardized by their own train mean/std inside the discovery procedure (identical for real and null series); coefficients reported back in original units",
                   "residual-check alpha declared 0.05 (stricter than 0.01 -> easier to demote -> conservative); raw p-values reported",
                   "frozen f* = selected family with train-fitted coefficients; residual checks on train+validation",
               ],
               "claims": {}}

    claim_meta = {"A": ("eq.tidal-manila.phase.v1", "Total tidal accel (g)"),
                  "B": ("eq.tidal-manila.phase.moondist.v1", "Moon Dist (km)")}

    for ci, (claim, (claim_id, target)) in enumerate(claim_meta.items()):
        y = np.array(cols[target])
        t_tr, z_tr, t_va, z_va, t_te, z_te, mu, sd = standardize_splits(y, i1, i2, t)

        # ---- stage: fit (deterministic) ----
        fams, fstar = discover(t_tr, z_tr, t_va, z_va, t_te, z_te, claim, lam)
        rec = fams[fstar]
        obs_test = rec["nll_test"]

        # ---- stage: null-equation generator (B=200 per type) ----
        ar_p, ar_phi, ar_s2, ar_mu = fit_ar_train(y[:i1])
        null_out = {}
        for ti, ntype in enumerate(["permutation", "phase_randomized_surrogate", "AR_null"]):
            sel, freqs_rec, comps, jvals, tests = [], [], [], [], []
            for b in range(B_NULLS):
                rng = np.random.default_rng(np.random.SeedSequence(
                    [BASE_SEED + STAGE["null_equation_generator"], ci, ti, b]))
                if ntype == "permutation":
                    yn = gen_permutation(y, rng)
                elif ntype == "phase_randomized_surrogate":
                    yn = gen_phase_surrogate(y, rng)
                else:
                    yn = gen_ar(n, ar_phi, ar_s2, ar_mu, rng)
                a, b1, c, d, e, f2, _, _ = standardize_splits(yn, i1, i2, t)
                nf, ns = discover(a, b1, c, d, e, f2, claim, lam)
                nr = nf[ns]
                sel.append(ns); freqs_rec.extend(nr["periods_d"])
                comps.append(nr["complexity"]); jvals.append(nr["J_val"]); tests.append(nr["nll_test"])
            tests = np.array(tests)
            p_null = float((1 + int(np.sum(tests <= obs_test))) / (B_NULLS + 1))
            null_out[ntype] = {
                "B": B_NULLS, "null_adjusted_p": p_null,
                "observed_test_nll": obs_test,
                "null_test_nll": {"min": float(tests.min()), "q05": float(np.quantile(tests, .05)),
                                  "median": float(np.median(tests)), "q95": float(np.quantile(tests, .95)),
                                  "max": float(tests.max())},
                "null_selected_family_counts": {k: sel.count(k) for k in sorted(set(sel))},
                "null_complexity_mean": float(np.mean(comps)),
                "null_J_val_median": float(np.median(jvals)),
                "null_recovered_period_quantiles_d": {
                    "q05": float(np.quantile(freqs_rec, .05)), "median": float(np.median(freqs_rec)),
                    "q95": float(np.quantile(freqs_rec, .95))},
            }
            if ntype == "AR_null":
                null_out[ntype]["ar_order_p"] = ar_p

        # ---- stage: bootstrap (moving-block, B=500, block 15 d) ----
        t_tv, z_tv = t[:i2], np.concatenate([z_tr, z_va])
        Xstar = design(t_tv, rec["freqs"], rec["K"])
        coef_tv_for_curve = np.array(rec["coef"])
        fit_curve = Xstar @ coef_tv_for_curve
        resid_tv = z_tv - fit_curve
        nb = i2
        sel_boot, periods_boot, amps_boot = [], [], []
        nfree = [nf for fam, nf, K in FAMILIES[claim] if fam == fstar][0]
        for b in range(B_BOOT):
            rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED + STAGE["bootstrap"], ci, b]))
            nblocks = math.ceil(nb / BLOCK)
            starts = rng.integers(0, nb - BLOCK + 1, nblocks)
            rb = np.concatenate([resid_tv[s:s + BLOCK] for s in starts])[:nb]
            zb = fit_curve + rb
            a1, b1, c1, d1 = t_tv[:i1], zb[:i1], t_tv[i1:], zb[i1:]
            bf, bs = discover(a1, b1, c1, d1, t_te, z_te, claim, lam)
            sel_boot.append(bs)
            # refit the FROZEN family f* on the replicate for parameter CIs
            br = bf[fstar]
            periods_boot.append(br["periods_d"])
            amps_boot.append([h["amplitude"] for h in amp_phase(br["coef"], br["K"], nfree)])
        sel_frac = sel_boot.count(fstar) / B_BOOT
        periods_boot = np.array(periods_boot)  # (B, nfree)
        amps_boot = np.array(amps_boot)

        # match each observed base period to its ground-truth constituent
        const_report = {}
        for i, p in enumerate(rec["periods_d"]):
            name = match_period(p, claim)
            # align bootstrap column to same constituent by nearest period per replicate
            colvals = []
            for row in periods_boot:
                j = int(np.argmin([abs(pp - p) for pp in row]))
                colvals.append(row[j])
            ci95 = [float(np.quantile(colvals, .025)), float(np.quantile(colvals, .975))]
            gt = GROUND[name]
            lo, hi = TOL[claim][name]
            const_report[f"freq{i + 1}"] = {
                "matched_constituent": name, "ground_truth_d": gt,
                "recovered_period_d": float(p),
                "period_recovery_error_pct": float(100 * abs(p - gt) / gt),
                "bootstrap_CI95_d": ci95,
                "within_tolerance_band": bool(lo <= p <= hi),
                "CI_contains_ground_truth": bool(ci95[0] <= gt <= ci95[1]),
                "CI_within_tolerance_band": bool(ci95[0] >= lo and ci95[1] <= hi),
                "tolerance_band_d": [lo, hi],
            }

        # ---- detectability floor & coefficients (original units) ----
        coef = np.array(rec["coef"])
        resid_tr = z_tr - design(t_tr, rec["freqs"], rec["K"]) @ coef
        sig_tr = float(resid_tr.std())
        floor_z = 4.0 * sig_tr * math.sqrt(2.0 / i1)
        harmonics = amp_phase(coef, rec["K"], nfree)
        coef_report = []
        for hi_, h in enumerate(harmonics):
            amp_orig = h["amplitude"] * sd
            acis = [float(np.quantile(amps_boot[:, hi_], .025) * sd),
                    float(np.quantile(amps_boot[:, hi_], .975) * sd)]
            cv = float(np.std(amps_boot[:, hi_]) / np.mean(amps_boot[:, hi_]))
            coef_report.append({
                "base_freq_index": h["freq_index"] + 1, "harmonic": h["harmonic"],
                "period_d": float(rec["periods_d"][h["freq_index"]] / h["harmonic"]),
                "amplitude_orig_units": amp_orig, "amplitude_CI95_orig_units": acis,
                "amplitude_cv_bootstrap": cv,
                "a_sin_orig": h["a_sin"] * sd, "b_cos_orig": h["b_cos"] * sd,
                "above_floor": bool(h["amplitude"] >= floor_z),
            })
        a0_orig = float(mu + coef[0] * sd)
        reported = [c for c in coef_report if c["above_floor"]]

        # ---- stage: residual checks (train+validation, frozen model) ----
        rng_res = np.random.default_rng(np.random.SeedSequence([BASE_SEED + STAGE["residuals"], ci]))
        r = resid_tv
        lbQ, lbp = ljung_box(r)
        g, gp, gpk, gm = fisher_g(r)
        mmd, mmdp = mmd_test(r, rng_res)
        bpLM, bpp = breusch_pagan(r, t_tv)
        cs, csp = cusum_test(r, rng_res)
        h1, h1p = tda_check(r, rng_res)
        cz, czp = compression_check(r, rng_res)
        resid_table = {
            "1_ljung_box_lag40": {"Q": lbQ, "p": lbp, "pass": bool(lbp >= ALPHA_RESID)},
            "2_fisher_g_4_120d": {"g": g, "p": gp, "peak_period_d": gpk, "m_ordinates": gm,
                                  "pass": bool(gp >= ALPHA_RESID)},
            "3_mmd_vs_gaussian": {"mmd2": mmd, "p": mmdp, "pass": bool(mmdp >= ALPHA_RESID)},
            "4_breusch_pagan": {"LM": bpLM, "p": bpp, "pass": bool(bpp >= ALPHA_RESID)},
            "5_cusum_changepoint": {"stat": cs, "p": csp, "pass": bool(csp >= ALPHA_RESID)},
            "6_tda_h1_residuals": {"max_h1_persistence": h1, "p_perm": h1p,
                                   "loop_gone": bool(h1p >= ALPHA_RESID), "pass": bool(h1p >= ALPHA_RESID)},
            "7_compression": {"zlib_bytes": cz, "p_more_compressible": czp,
                              "pass": bool(czp >= ALPHA_RESID)},
        }
        residuals_pass = all(v["pass"] for v in resid_table.values())

        # ---- verdict per registration section 11 ----
        nulls_beaten = all(null_out[k]["null_adjusted_p"] <= ALPHA_NULL for k in null_out)
        boot_stable = (sel_frac >= 0.90
                       and all(c["CI_within_tolerance_band"] for c in const_report.values())
                       and all(c["amplitude_cv_bootstrap"] < 0.20 for c in coef_report
                               if c["above_floor"]))
        expected = list(TOL[claim].keys())
        recovered_names = {c["matched_constituent"] for c in const_report.values()
                           if c["within_tolerance_band"] and c["CI_contains_ground_truth"]}
        periods_in_tol = all(name in recovered_names for name in expected)
        sub4d_flag = any(c["recovered_period_d"] < 4.0 for c in const_report.values())
        if not nulls_beaten or not residuals_pass or not boot_stable:
            verdict = "FAILED_EQUATION_SEARCH"
        elif not periods_in_tol or sub4d_flag:
            verdict = "FAILED_EQUATION_SEARCH"  # + calibration-fail flag below
        else:
            verdict = "PREDICTIVE_EQUATION"
        calib = "PASS" if (periods_in_tol and not sub4d_flag) else "FAIL"

        results["claims"][claim_id] = {
            "target": target, "family_records": fams, "selected_family": fstar,
            "selected_complexity": rec["complexity"],
            "rmse_test_std_units": rec["rmse_test"], "rmse_test_orig_units": rec["rmse_test"] * sd,
            "intercept_orig_units": a0_orig,
            "train_residual_sigma_orig_units": sig_tr * sd,
            "detectability_floor_amplitude_orig_units": floor_z * sd,
            "coefficients_all": coef_report, "coefficients_above_floor": reported,
            "constituents": const_report,
            "nulls": null_out, "nulls_beaten_all_three": nulls_beaten,
            "bootstrap": {"B": B_BOOT, "block_d": BLOCK,
                          "selected_family_fraction": sel_frac, "stable": boot_stable},
            "residual_checks": resid_table, "residuals_pass": residuals_pass,
            "periods_within_tolerance": periods_in_tol, "sub_4d_constituent_flag": sub4d_flag,
            "calibration": calib, "verdict": verdict,
        }
    return results

def canonical(d):
    return json.dumps(d, sort_keys=True, indent=1, allow_nan=False).encode()

if __name__ == "__main__":
    r1 = run_pipeline()
    r2 = run_pipeline()
    diff = "byte-identical (in-process double run, identical seeds)" if canonical(r1) == canonical(r2) \
        else "MISMATCH — NOT REPRODUCIBLE"
    r1["two_run_diff"] = diff
    with open(OUT, "wb") as f:
        f.write(canonical(r1))
    print(diff)
    for cid, c in r1["claims"].items():
        print(cid, "| family:", c["selected_family"], "| verdict:", c["verdict"],
              "| calibration:", c["calibration"],
              "| periods:", [round(p, 3) for p in c["family_records"][c["selected_family"]]["periods_d"]])
