#!/usr/bin/env python3
"""
eq_moondist_confirm1.py — fresh-data confirmation scoring (EXECUTE-ONLY).

Registration: docs/REGISTRATION_EQ_MOONDIST_CONFIRM.md
  sha256 9b0626c12f6f273b62c6905a8b93481aa6e690854e1e06d94743189abf05ea06
  (APPROVED 2026-06-12 pre-fetch; ledger line 9b0626c12f6f273b).
  Amendments honored: fetch-now approved; MECHANISM_SUPPORTED ceiling stands
  (PREDICTIVE_EQUATION cap fallback struck).

ZERO free parameters. The frozen v2 B1 equation (registration Section 2,
byte-verified against results/eq_tidal_v2.json via the v2 registered fit
path BEFORE scoring) is evaluated verbatim at t = 366..451
(t = days since 2025-06-11; no re-anchoring, no refit) against fresh
Horizons rows 2026-06-12..2026-09-05 fetched by the orchestrator under the
registered protocol (raw committed pre-parse, sha256 4724920d212aa85f...).

Section 3.2 guards enforced here; any failure -> NO_EQUATION_ATTEMPTED.
Declared pre-scoring deviation + tripwire (results/eq_v3_confirm1_CHECKPOINT.md):
fresh stamps display minute precision ('13:00') vs original FRACSEC
('13:00:02.880'); worst-case sampling-instant offset 2.88 s bounds the value
impact at ~1.4 km; if any gate (C1/C2) margin < 2 km the run STOPS with
NO_EQUATION_ATTEMPTED and escalates instead of issuing a verdict.

Gates (Section 5, fixed pre-fetch):
  C1: RMSE_fresh <= 1.5 * 4119.801539200268 km
  C2: max|r|     <= 3.0 * 4119.801539200268 km
  C3: exactly 86 residuals, none NaN
PASS all -> MECHANISM_SUPPORTED; any C1/C2 fail -> FAILED_EQUATION_SEARCH.
Seed base 20260614 (diagnostics-only; scoring deterministic).
Two-run rule: --single/--finalize from the SAME raw file, byte-identical.
"""
import datetime, hashlib, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eq_tidal_v2 as v2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "eq_confirm1_raw_horizons.txt")
V2_JSON = os.path.join(ROOT, "results", "eq_tidal_v2.json")
OUT = os.path.join(ROOT, "results", "eq_moondist_confirm1.json")

RAW_SHA_COMMITTED = "4724920d212aa85fadb6c391d89d813048616aa379eef07159bab4ad2585dc30"
AU_KM = 149597870.700
RMSE_V2_TEST = 4119.801539200268
C1_THR = 1.5 * RMSE_V2_TEST
C2_THR = 3.0 * RMSE_V2_TEST
TRIPWIRE_KM = 2.0
SEED_BASE = 20260614
REG_B1 = {"a0": 385294.7950098205, "a_sin": -19039.87882118035,
          "b_cos": 11488.61399772309, "P": 27.60387627151598}
SPAN0 = datetime.date(2026, 6, 12)
SPAN1 = datetime.date(2026, 9, 5)
T0_OFFSET = 366  # 2026-06-12 = day 366 since 2025-06-11
MON = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def parse_raw():
    """Parse the raw fetch; enforce Section 3.2 guards. Returns (rows, guards)."""
    raw_bytes = open(RAW, "rb").read()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    guards = {"raw_sha256": sha,
              "G_raw_hash_matches_committed": bool(sha == RAW_SHA_COMMITTED)}
    text = raw_bytes.decode()
    header = text.split("$$SOE")[0]
    guards["G_DE441"] = "{source: DE441}" in header
    guards["G_delta_in_AU"] = "delta in AU" in header
    guards["G_au_km_constant"] = "1 au = 149597870.700 km" in header
    rows = []
    stamps_ok = True
    in_block = False
    for line in text.splitlines():
        if line.startswith("$$SOE"):
            in_block = True
            continue
        if line.startswith("$$EOE"):
            break
        if not in_block or not line.strip():
            continue
        toks = line.split()
        date_str, time_str = toks[0], toks[1]
        if time_str != "13:00":
            stamps_ok = False
        nums = []
        for tk in toks[2:]:
            try:
                nums.append(float(tk))
            except ValueError:
                pass  # solar/lunar presence flag column (preserved as-is in raw)
        assert len(nums) == 2, ("row field count", line)
        y, mo, d = date_str.split("-")
        iso_date = datetime.date(int(y), MON[mo], int(d))
        delta_au, deldot = nums
        rows.append((iso_date, delta_au, deldot))
    guards["G_row_count_86"] = (len(rows) == 86)
    cont = all(rows[i][0] == SPAN0 + datetime.timedelta(days=i) for i in range(len(rows)))
    guards["G_day_continuity"] = bool(cont and rows[0][0] == SPAN0 and rows[-1][0] == SPAN1)
    guards["G_stamp_13_00_minute_display"] = bool(stamps_ok)
    guards["stamp_precision_deviation_declared"] = (
        "fresh stamps display '13:00' (minute precision) vs original raw '13:00:02.880' (FRACSEC); "
        "request convention identical (START_TIME 13:00 UT); worst-case instant offset 2.88 s "
        "-> <=~1.4 km value impact (max|deldot| ~0.48 km/s); declared pre-scoring in "
        "results/eq_v3_confirm1_CHECKPOINT.md with a 2 km gate-margin escalation tripwire")
    return rows, guards


def verify_frozen_b1():
    """Registration Section 2 freeze verification: re-derive B1 via the v2
    registered path; byte-equivalence to eq_tidal_v2.json AND Section 2."""
    import csv
    with open(V2_JSON) as f:
        frozen = json.load(f)
    dates, ys = [], []
    with open(v2.DATA) as f:
        for row in csv.DictReader(f):
            dates.append(row["Date"])
            ys.append(float(row["Moon Dist (km)"]))
    n = len(dates)
    assert n == 366 and dates[0] == "2025-06-11" and dates[-1] == "2026-06-11"
    t = np.arange(n, dtype=float)
    i1, i2 = int(round(0.6 * n)), int(round(0.8 * n))
    lam = math.log(i1) / 2.0
    y = np.array(ys)
    t_tr, z_tr, t_va, z_va, t_te, z_te, mu, sd = v2.standardize_splits(y, i1, i2, t)
    fams, fstar = v2.discover(t_tr, z_tr, t_va, z_va, t_te, z_te, "B", lam)
    rec = fams[fstar]
    fr = frozen["claims"]["eq.tidal-manila.phase.moondist.v2"]
    frec = fr["family_records"][fr["selected_family"]]
    a0 = float(mu + rec["coef"][0] * sd)
    a_s = float(rec["coef"][1] * sd)
    b_c = float(rec["coef"][2] * sd)
    P = float(rec["periods_d"][0])
    ok = (fstar == fr["selected_family"] == "B1_harmonic_1freq_k1"
          and rec["freqs"] == frec["freqs"] and rec["coef"] == frec["coef"]
          and rec["periods_d"] == frec["periods_d"]
          and a0 == REG_B1["a0"] and a_s == REG_B1["a_sin"]
          and b_c == REG_B1["b_cos"] and P == REG_B1["P"]
          and fr["rmse_test_orig_units"] == RMSE_V2_TEST)
    return {"selected_family": fstar, "byte_equal": bool(ok),
            "orig_units": {"a0": a0, "a_sin": a_s, "b_cos": b_c, "P_d": P}}


def run_pipeline():
    results = {
        "registration": "docs/REGISTRATION_EQ_MOONDIST_CONFIRM.md sha256 9b0626c12f6f273b (approved pre-fetch 2026-06-12; fetch-now amendment; MECHANISM_SUPPORTED ceiling)",
        "equation_claim_id": "eq.tidal-manila.phase.moondist.confirm1",
        "script": "src/eq_moondist_confirm1.py",
        "raw_file": "results/eq_confirm1_raw_horizons.txt",
        "frozen_equation_source": "results/eq_tidal_v2.json (B1, v2 claim B)",
        "t_convention": "t = days since 2025-06-11; fresh rows t = 366..451; no re-anchoring",
        "seed_base": SEED_BASE,
        "gates": {"C1_rmse_thr_km": C1_THR, "C2_maxabs_thr_km": C2_THR,
                  "C3": "exactly 86 residuals, none NaN",
                  "tripwire_km": TRIPWIRE_KM},
    }
    rows, guards = parse_raw()
    results["guards"] = guards
    freeze = verify_frozen_b1()
    results["freeze_verification"] = freeze
    hard_guards = [k for k in guards if k.startswith("G_")]
    if not all(guards[k] for k in hard_guards) or not freeze["byte_equal"]:
        results["verdict"] = "NO_EQUATION_ATTEMPTED"
        results["abort_reason"] = "Section 3.2 guard or Section 2 freeze verification failed"
        return results

    # ---- deterministic forward evaluation of frozen B1 ----
    t = np.arange(T0_OFFSET, T0_OFFSET + 86, dtype=float)
    x = np.array([float(f"{delta * AU_KM:.1f}") for _, delta, _ in rows])  # parser convention: 0.1 km precision
    w = 2.0 * np.pi * t / REG_B1["P"]
    yhat = REG_B1["a0"] + REG_B1["a_sin"] * np.sin(w) + REG_B1["b_cos"] * np.cos(w)
    r = x - yhat
    results["fresh_rows"] = [
        {"date": rows[i][0].isoformat(), "t_d": float(t[i]), "x_km": float(x[i]),
         "yhat_km": float(yhat[i]), "residual_km": float(r[i])} for i in range(86)]

    rmse = float(np.sqrt(np.mean(r ** 2)))
    maxabs = float(np.max(np.abs(r)))
    c3 = bool(len(r) == 86 and not np.any(np.isnan(r)))
    c1 = bool(rmse <= C1_THR)
    c2 = bool(maxabs <= C2_THR)
    m1 = float(C1_THR - rmse)
    m2 = float(C2_THR - maxabs)
    results["scores"] = {
        "rmse_fresh_km": rmse, "max_abs_residual_km": maxabs,
        "n_residuals": len(r), "any_nan": bool(np.any(np.isnan(r))),
        "C1_pass": c1, "C1_margin_km": m1,
        "C2_pass": c2, "C2_margin_km": m2,
        "C3_pass": c3,
        "v2_test_rmse_benchmark_km": RMSE_V2_TEST,
        "rmse_ratio_vs_v2_test": rmse / RMSE_V2_TEST,
    }

    # ---- non-gating diagnostics (Section 5) ----
    A = np.column_stack([np.ones_like(t), t - t.mean()])
    beta_r, _, _, _ = np.linalg.lstsq(A, r, rcond=None)
    beta_ar, _, _, _ = np.linalg.lstsq(A, np.abs(r), rcond=None)
    Iw, periods = v2.periodogram_window(r)
    work = Iw.copy()
    tops = []
    for _ in range(5):
        if len(work) < 3:
            break
        g = float(work.max() / work.sum())
        k = int(np.argmax(work))
        tops.append({"period_d": float(periods[np.argsort(-Iw)[len(tops)]]),
                     "fisher_g": g, "p": v2.fisher_p_exact(g, len(work))})
        work = np.delete(work, k)
    results["diagnostics_nongating"] = {
        "residual_mean_km": float(np.mean(r)),
        "residual_trend_km_per_d": float(beta_r[1]),
        "abs_residual_drift_km_per_d": float(beta_ar[1]),
        "fisher_g_top_peaks_fresh": tops,
        "note": "n=86 too short to gate; reported for continuity with v2 learning 3 / v3",
    }

    # ---- verdict (Section 6) with declared tripwire ----
    if abs(m1) < TRIPWIRE_KM or abs(m2) < TRIPWIRE_KM:
        results["verdict"] = "NO_EQUATION_ATTEMPTED"
        results["abort_reason"] = ("declared stamp-precision tripwire: gate margin < 2 km; "
                                   "the 2.88 s sampling-instant ambiguity could be decisive; escalate to human")
    elif c1 and c2 and c3:
        results["verdict"] = "MECHANISM_SUPPORTED"
        results["verdict_note"] = ("ceiling per approved registration (GOVERNING_LAW_CONFIRMED out of scope); "
                                   "scope carve-out: attaches to frozen B1 as forecast-grade description of the "
                                   "dominant anomalistic line, error envelope <= 6.2e3 km RMSE; v2 "
                                   "FAILED_EQUATION_SEARCH (residual completeness) stands on its own claim id")
    elif not c3:
        results["verdict"] = "NO_EQUATION_ATTEMPTED"
        results["abort_reason"] = "C3 sanity failed"
    else:
        results["verdict"] = "FAILED_EQUATION_SEARCH"
        results["verdict_note"] = ("fresh-data confirmation FAILED: frozen equation rejected on fresh data; "
                                   "v2 calibration PASS flagged non-predictive out-of-span per Section 6.2")
    return results


def canonical(d):
    return json.dumps(d, sort_keys=True, indent=1, allow_nan=False).encode()


def summarize(r):
    s = r.get("scores", {})
    print("guards:", {k: v for k, v in r["guards"].items() if k.startswith("G_")})
    print("freeze byte-equal:", r["freeze_verification"]["byte_equal"])
    if s:
        print("RMSE_fresh = %.6f km (C1 thr %.6f, margin %.3f) -> %s"
              % (s["rmse_fresh_km"], C1_THR, s["C1_margin_km"], s["C1_pass"]))
        print("max|r|     = %.6f km (C2 thr %.6f, margin %.3f) -> %s"
              % (s["max_abs_residual_km"], C2_THR, s["C2_margin_km"], s["C2_pass"]))
        print("C3:", s["C3_pass"])
    print("VERDICT:", r["verdict"])


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--single":
        r = run_pipeline()
        with open(sys.argv[2], "wb") as f:
            f.write(canonical(r))
        summarize(r)
    elif len(sys.argv) >= 4 and sys.argv[1] == "--finalize":
        b1 = open(sys.argv[2], "rb").read()
        b2 = open(sys.argv[3], "rb").read()
        diff = ("byte-identical (two separate full process executions from the same raw file)"
                if b1 == b2 else "MISMATCH — NOT REPRODUCIBLE")
        r = json.loads(b1)
        r["two_run_diff"] = diff
        with open(OUT, "wb") as f:
            f.write(canonical(r))
        print(diff)
        summarize(r)
    else:
        print("usage: --single OUT | --finalize RUN1 RUN2")
        sys.exit(2)
