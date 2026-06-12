#!/usr/bin/env python3
"""
eq_tidal_v3.py — Phase 5 re-adjudication (EXECUTE-ONLY), v3.

Registration: docs/REGISTRATION_EQ_TIDAL_V3.md
  sha256 4fc27d0e621d425003b15d47712390a4fd4e90b782f6470b21bcebd836b6a11c
  (APPROVED 2026-06-12 pre-execution; ledger line 4fc27d0e621d4250).
  Amendments honored: Section 8 option (a) REJECTED (+1 charge stands);
  option (b) ACCEPTED (claim A's 36.625 d peak in scope, +0 charge).

Scope: claim-B R1 whitelist-attribution re-adjudication on a declared 16x
zero-padded fine omega-grid with the registered leakage-collapse rule, plus
claim A's unattributed 36.625 d peak under the same rule (symmetric
diagnostic). NO refitting: B1 (and A2, needed for claim-A residuals) are
re-derived deterministically via the v2 registered path (imported verbatim
from src/eq_tidal_v2.py) and MUST be byte-equal to results/eq_tidal_v2.json
before anything else runs. Binding fact (registration Section 6): R3 is
unchanged and FAILS on every branch; v3 adjudicates WHICH
FAILED_EQUATION_SEARCH, never an upgrade.

Declared implementation decisions (results/eq_v3_confirm1_CHECKPOINT.md,
pre-execution):
  - leakage collapse in frequency space: |f_i - f_j| <= 1/292 cyc/d
    (single-linkage; cluster attributed iff any member's refined location
    attributes), T = 292 d exactly as implemented in v2's R1;
  - fine grid: rfft zero-padded to 16*293 = 4688 points, refinement window
    +-1 natural bin (1/293 cyc/d) around each significant coarse ordinate,
    intersected with the 4-120 d window;
  - R2/R3/R4 + non-gating diagnostics re-verified with the EXACT v2 rng
    stream (SeedSequence [20260612+4, ci], draw order cusum -> tda ->
    compression -> mmd) — published v2 values must reproduce byte-exactly;
  - v3 seed base 20260613 recorded; the v3-specific procedure is fully
    deterministic (no new stochastic stage is exercised).
Two-run rule: --single/--finalize, separate processes, byte-identical JSON.
"""
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eq_tidal_v2 as v2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2_JSON = os.path.join(ROOT, "results", "eq_tidal_v2.json")
OUT = os.path.join(ROOT, "results", "eq_tidal_v3.json")

SEED_BASE_V3 = 20260613
T_RAYLEIGH = 292.0          # as implemented in v2 (t_tv[-1] - t_tv[0])
OVERSAMPLE = 16

CLAIM_IDS = {"A": "eq.tidal-manila.phase.v2", "B": "eq.tidal-manila.phase.moondist.v2"}
REG_B1 = {  # registration Section 2 frozen values (exact)
    "a0": 385294.7950098205, "a_sin": -19039.87882118035,
    "b_cos": 11488.61399772309, "P": 27.60387627151598,
}


def fine_refine(r, coarse_peaks):
    """Registration Section 4 step 2: 16x zero-padded periodogram; each
    significant natural-grid peak gets the fine-grid local maximum within
    +-1 natural Fourier bin (1/293 cyc/d) of its coarse ordinate."""
    n = len(r)
    x = r - r.mean()
    nfft = OVERSAMPLE * n
    I = np.abs(np.fft.rfft(x, nfft)) ** 2
    fr = np.fft.rfftfreq(nfft, 1.0)
    out = []
    for pk in coarse_peaks:
        fc = 1.0 / pk["peak_period_d"]
        lo = max(fc - 1.0 / n, 1.0 / v2.PMAX)
        hi = min(fc + 1.0 / n, 1.0 / v2.PMIN)
        idx = np.where((fr >= lo) & (fr <= hi))[0]
        j = int(idx[int(np.argmax(I[idx]))])
        out.append({"refined_freq_cyc_d": float(fr[j]),
                    "refined_period_d": float(1.0 / fr[j]),
                    "fine_power": float(I[j])})
    return out


def collapse_clusters(refined, allow_merge):
    """Registration Section 4 step 3: attribution on refined locations +
    declared leakage-collapse rule (|f_i - f_j| <= 1/T_RAYLEIGH,
    single-linkage; cluster attributed iff any member attributed)."""
    npk = len(refined)
    parent = list(range(npk))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(npk):
        for j in range(i + 1, npk):
            if abs(refined[i]["refined_freq_cyc_d"] - refined[j]["refined_freq_cyc_d"]) <= 1.0 / T_RAYLEIGH:
                parent[find(i)] = find(j)
    attr = [v2.attribute_peak(rf["refined_period_d"], T_RAYLEIGH, allow_merge) for rf in refined]
    groups = {}
    for i in range(npk):
        groups.setdefault(find(i), []).append(i)
    clusters = []
    for members in groups.values():
        rep = max(members, key=lambda i: refined[i]["fine_power"])
        matches = sorted({attr[i][1] for i in members if attr[i][0]})
        clusters.append({
            "members_coarse_period_d": [refined[i]["coarse_period_d"] for i in members],
            "members_refined_period_d": [refined[i]["refined_period_d"] for i in members],
            "n_members": len(members),
            "representative_refined_period_d": refined[rep]["refined_period_d"],
            "representative_fine_power": refined[rep]["fine_power"],
            "attributed": bool(any(attr[i][0] for i in members)),
            "whitelist_matches": matches,
        })
    clusters.sort(key=lambda c: -c["representative_fine_power"])
    return clusters, attr


def run_pipeline():
    with open(V2_JSON) as f:
        frozen = json.load(f)

    # ---- data + splits, identical to v2 ----
    import csv
    dates, cols = [], {"Moon Dist (km)": [], "Total tidal accel (g)": []}
    with open(v2.DATA) as f:
        for row in csv.DictReader(f):
            dates.append(row["Date"])
            for c in cols:
                cols[c].append(float(row[c]))
    n = len(dates)
    t = np.arange(n, dtype=float)
    i1, i2 = int(round(0.6 * n)), int(round(0.8 * n))
    lam = math.log(i1) / 2.0
    assert (n, i1, i2) == (366, 220, 293) and dates[0] == "2025-06-11" and dates[-1] == "2026-06-11"

    results = {
        "registration": "docs/REGISTRATION_EQ_TIDAL_V3.md sha256 4fc27d0e621d4250 (approved pre-execution 2026-06-12; claim-A 36.625d amendment in scope at +0)",
        "predecessor": "eq_tidal_v2 (results/eq_tidal_v2.json)",
        "script": "src/eq_tidal_v3.py", "data_file": "datasets/tidal-manila/tidal_derived.csv",
        "n_rows": n, "splits": {"train": [0, i1], "validation": [i1, i2], "test": [i2, n]},
        "seed_base_v3": SEED_BASE_V3,
        "seed_note": "v3 procedure deterministic; R2/R3/R4+diagnostics re-verified under the exact v2 rng stream (base 20260612, residuals offset 4) for byte-verification of published values",
        "oversample_factor": OVERSAMPLE, "rayleigh_T_d": T_RAYLEIGH,
        "alpha_resid_gating": v2.ALPHA_RESID,
        "whitelist_periods_d": v2.WHITELIST,
        "leakage_collapse_rule": "refined lines collapse iff |f_i-f_j| <= 1/292 cyc/d (single-linkage); cluster attributed iff any member's refined period attributes (direct Rayleigh or, claim A only, merge zone)",
        "independence": "executor is equation-analyst v3 execute dispatch; != batch5 detection analyst; != v2 same-claim independent verifier",
        "claims": {},
    }

    for ci, claim in enumerate(["A", "B"]):  # ci order identical to v2 claim_meta
        claim_id = CLAIM_IDS[claim]
        target = frozen["claims"][claim_id]["target"]
        y = np.array(cols[target])
        t_tr, z_tr, t_va, z_va, t_te, z_te, mu, sd = v2.standardize_splits(y, i1, i2, t)

        # ---- frozen-refit byte-check (uncharged deterministic repeat) ----
        fams, fstar = v2.discover(t_tr, z_tr, t_va, z_va, t_te, z_te, claim, lam)
        frec = frozen["claims"][claim_id]["family_records"][frozen["claims"][claim_id]["selected_family"]]
        rec = fams[fstar]
        byte_equal = (fstar == frozen["claims"][claim_id]["selected_family"]
                      and rec["freqs"] == frec["freqs"] and rec["coef"] == frec["coef"]
                      and rec["periods_d"] == frec["periods_d"])
        refit = {"selected_family": fstar, "byte_equal_to_v2_json": bool(byte_equal)}
        if claim == "B":
            a0 = float(mu + rec["coef"][0] * sd)
            a_s = float(rec["coef"][1] * sd)
            b_c = float(rec["coef"][2] * sd)
            P = float(rec["periods_d"][0])
            refit["orig_units"] = {"a0": a0, "a_sin": a_s, "b_cos": b_c, "P_d": P}
            refit["matches_registration_section2"] = bool(
                a0 == REG_B1["a0"] and a_s == REG_B1["a_sin"]
                and b_c == REG_B1["b_cos"] and P == REG_B1["P"])
            byte_equal = byte_equal and refit["matches_registration_section2"]
        if not byte_equal:
            results["claims"][claim_id] = {"frozen_refit": refit,
                                           "verdict": "NO_EQUATION_ATTEMPTED",
                                           "abort_reason": "frozen-refit byte-equivalence FAILED (registration Section 2 abort rule)"}
            continue

        # ---- residuals (byte-identical to v2: standardized, train+validation) ----
        coef = np.array(rec["coef"])
        t_tv, z_tv = t[:i2], np.concatenate([z_tr, z_va])
        r = z_tv - v2.design(t_tv, rec["freqs"], rec["K"]) @ coef
        T_span = float(t_tv[-1] - t_tv[0])
        assert T_span == T_RAYLEIGH

        # ---- step 1: coarse detector, byte-identical to v2; verify vs published ----
        allow_merge = (claim == "A")
        peaks, r1_coarse_pass = v2.r1_whitelist_scan(r, T_span, allow_merge=allow_merge)
        v2_peaks = frozen["claims"][claim_id]["residual_checks"]["R1_whitelist_attribution"]["significant_peaks"]
        coarse_verified = (
            [{k: p[k] for k in ("peak_period_d", "fisher_g", "p", "m_ordinates", "attributed", "whitelist_match")} for p in peaks]
            == [{k: p[k] for k in ("peak_period_d", "fisher_g", "p", "m_ordinates", "attributed", "whitelist_match")} for p in v2_peaks])
        if not coarse_verified:
            results["claims"][claim_id] = {"frozen_refit": refit,
                                           "verdict": "NO_EQUATION_ATTEMPTED",
                                           "abort_reason": "coarse R1 detector did not reproduce v2 published peaks byte-exactly"}
            continue

        # ---- step 2: fine-grid location refinement ----
        refined = fine_refine(r, peaks)
        for pk, rf in zip(peaks, refined):
            rf["coarse_period_d"] = pk["peak_period_d"]
            rf["coarse_attributed_v2"] = pk["attributed"]
            rf["coarse_p"] = pk["p"]
            ok, name = v2.attribute_peak(rf["refined_period_d"], T_RAYLEIGH, allow_merge)
            rf["refined_attributed"] = bool(ok)
            rf["refined_whitelist_match"] = name

        # ---- step 3: leakage collapse + adjudication on distinct lines ----
        clusters, _ = collapse_clusters(refined, allow_merge)
        n_unattr = sum(1 for c in clusters if not c["attributed"])
        r1_v3_pass = (n_unattr == 0)

        # ---- R2/R3/R4 + diagnostics, exact v2 rng stream, byte-verification ----
        rng_res = np.random.default_rng(np.random.SeedSequence([20260612 + 4, ci]))
        cs, csp = v2.cusum_test(r, rng_res)
        h1, h1p = v2.tda_check(r, rng_res)
        cz, czp = v2.compression_check(r, rng_res)
        lbQ, lbp = v2.ljung_box(r)
        mmd, mmdp = v2.mmd_test(r, rng_res)
        bpLM, bpp = v2.breusch_pagan(r, t_tv)
        rc = frozen["claims"][claim_id]["residual_checks"]
        reverify = {
            "R2_cusum": {"stat": cs, "p": csp,
                         "byte_equal_v2": bool(cs == rc["R2_cusum_changepoint"]["stat"] and csp == rc["R2_cusum_changepoint"]["p"]),
                         "pass": bool(csp >= v2.ALPHA_RESID), "gating": True},
            "R3_tda_h1_absorption": {"max_h1_persistence_residual": h1, "p_perm_diagnostic": h1p,
                                     "threshold_50pct": v2.TDA_ABSORB_THRESHOLD,
                                     "absorption_fraction": float(1.0 - h1 / 1.124),
                                     "byte_equal_v2": bool(h1 == rc["R3_tda_h1_absorption"]["max_h1_persistence_residual"] and h1p == rc["R3_tda_h1_absorption"]["p_perm_diagnostic"]),
                                     "pass": bool(h1 < v2.TDA_ABSORB_THRESHOLD), "gating": True},
            "R4_compression": {"zlib_bytes": cz, "p_more_compressible": czp,
                               "byte_equal_v2": bool(cz == rc["R4_compression"]["zlib_bytes"] and czp == rc["R4_compression"]["p_more_compressible"]),
                               "gating": claim == "A"},
            "diag_ljung_box_lag40": {"Q": lbQ, "p": lbp, "gating": False,
                                     "byte_equal_v2": bool(lbQ == rc["diag_ljung_box_lag40"]["Q"] and lbp == rc["diag_ljung_box_lag40"]["p"])},
            "diag_mmd_vs_gaussian": {"mmd2": mmd, "p": mmdp, "gating": False,
                                     "byte_equal_v2": bool(mmd == rc["diag_mmd_vs_gaussian"]["mmd2"] and mmdp == rc["diag_mmd_vs_gaussian"]["p"])},
            "diag_breusch_pagan": {"LM": bpLM, "p": bpp, "gating": False,
                                   "byte_equal_v2": bool(bpLM == rc["diag_breusch_pagan"]["LM"] and bpp == rc["diag_breusch_pagan"]["p"])},
        }
        all_reverified = all(v["byte_equal_v2"] for v in reverify.values())

        entry = {
            "target": target,
            "frozen_refit": refit,
            "coarse_R1_reproduced_byte_equal": bool(coarse_verified),
            "coarse_R1_pass_v2_rule": bool(r1_coarse_pass),
            "fine_grid_peaks": refined,
            "distinct_refined_lines": clusters,
            "n_significant_coarse_peaks": len(peaks),
            "n_distinct_refined_lines": len(clusters),
            "n_unattributed_distinct_lines": n_unattr,
            "R1_v3_pass": bool(r1_v3_pass),
            "residual_checks_reverified": reverify,
            "reverification_all_byte_equal": bool(all_reverified),
        }

        if claim == "B":
            if not all_reverified:
                entry["verdict"] = "NO_EQUATION_ATTEMPTED"
                entry["abort_reason"] = "R2/R3/R4/diagnostic re-verification not byte-equal to v2 (environment drift); escalate"
            else:
                entry["outcome_branch"] = ("outcome1_ladder_dissolves_leakage_confirmed" if r1_v3_pass
                                           else "outcome2_ladder_persists_leakage_hypothesis_dead")
                entry["failure_attribution"] = ("R3 alone (R1 reclassified as coarse-grid leakage artifact)"
                                                if r1_v3_pass else "R1 (unattributed distinct lines) + R3")
                entry["verdict"] = "FAILED_EQUATION_SEARCH"
                entry["verdict_note"] = "registration Section 6 binding fact: R3 fails (0.886 > 0.562) on every branch; no upgrade possible; batch5 detection verdict untouched"
            results["claims"]["eq.tidal-manila.phase.moondist.v3"] = entry
        else:
            entry["scope_note"] = "claim A in scope by approver amendment (Section 8 option b, +0 charge): symmetric diagnostic on the 36.625 d peak; claim A verdict CANNOT improve (R2/R4 remain failed); no verdict issued here"
            peak36 = [c for c in clusters if any(abs(p - 36.625) < 1e-9 for p in c["members_coarse_period_d"])]
            entry["claimA_36p625_adjudication"] = peak36[0] if peak36 else None
            results["claims"]["eq.tidal-manila.phase.v2.fine_grid_diagnostic"] = entry

    return results


def canonical(d):
    return json.dumps(d, sort_keys=True, indent=1, allow_nan=False).encode()


def summarize(r):
    for cid, c in r["claims"].items():
        print(cid, "| refit byte-equal:", c.get("frozen_refit", {}).get("byte_equal_to_v2_json"),
              "| distinct lines:", c.get("n_distinct_refined_lines"),
              "| unattributed:", c.get("n_unattributed_distinct_lines"),
              "| R1_v3:", c.get("R1_v3_pass"),
              "| reverified:", c.get("reverification_all_byte_equal"),
              "| verdict:", c.get("verdict", "(diagnostic only)"))
        for cl in c.get("distinct_refined_lines", []):
            print("   line %.4f d  members(coarse)=%s  attributed=%s %s"
                  % (cl["representative_refined_period_d"],
                     [round(p, 2) for p in cl["members_coarse_period_d"]],
                     cl["attributed"], cl["whitelist_matches"]))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--single":
        r = run_pipeline()
        with open(sys.argv[2], "wb") as f:
            f.write(canonical(r))
        summarize(r)
    elif len(sys.argv) >= 4 and sys.argv[1] == "--finalize":
        b1 = open(sys.argv[2], "rb").read()
        b2 = open(sys.argv[3], "rb").read()
        diff = ("byte-identical (two separate full process executions, identical seeds)"
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
