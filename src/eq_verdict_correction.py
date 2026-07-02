#!/usr/bin/env python3
"""AUDIT E-1/E-2/E-3 remediation: the verdict-time multiplicity correction
step that every eq registration deferred ("the orchestrator applies the
global ledger correction at verdict time") and that no artifact ever executed.

Reads: results/multiplicity_ledger.jsonl (family charges + eq test rows),
       results/eq_tidal_v1.json, eq_tidal_v2.json (stored binding p's and
       family_records — no refit, pure arithmetic on frozen outputs).
Writes: results/eq_readjudication_2026-07-02.json

Correction basis: family-wise Sidak at base alpha 0.05 over the family's
CUMULATIVE charged m at the run's verdict time (the ledger is the declared
authority; charges: v1 +5, v2 +3, v3 +1, confirm1 +1). Floor rule from the
relational program (floor <= alpha_corrected/2) applied to B=200 nulls.
Also re-selects each claim's family under the corrected criterion
(pure held-out validation NLL — audit E-1) from stored family_records.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
R = lambda f: json.load(open(os.path.join(ROOT, "results", f)))
ALPHA = 0.05
FAMILY = "eq.tidal-manila.harmonic"

# run -> (claims: {label: binding null-adjusted p}, B nulls per generator)
RUNS = [
    ("eq_tidal_v1", "2026-06-11", {
        "claimA_tidal_phase": ("eq.tidal-manila.phase.v1", 0.208955223880597),
        "claimB_moondist": ("eq.tidal-manila.phase.moondist.v1",
                            0.004975124378109453)}, 200),
    ("eq_tidal_v2", "2026-06-11", {
        "claimA_tidal_phase": ("eq.tidal-manila.phase.v2", 0.19402985074626866),
        "claimB_moondist": ("eq.tidal-manila.phase.moondist.v2",
                            0.009950248756218905)}, 200),
]


def sidak(alpha, m):
    return 1 - (1 - alpha) ** (1 / m)


def cumulative_m():
    rows = [json.loads(l) for l in
            open(os.path.join(ROOT, "results", "multiplicity_ledger.jsonl"))]
    charges = [r for r in rows if r.get("row_type") == "family_charge"
               and r["family_id"] == FAMILY]
    order = ["REGISTRATION_EQ_TIDAL.md", "REGISTRATION_EQ_TIDAL_V2.md",
             "REGISTRATION_EQ_TIDAL_V3.md", "REGISTRATION_EQ_MOONDIST_CONFIRM.md"]
    cum, out = 0, {}
    for reg in order:
        c = next(x for x in charges if reg in x["registration"])
        cum += c["m_delta"]
        out[reg] = cum
    return out                       # v1: 5, v2: 8, v3: 9, confirm1: 10


def b_required(a):
    """Smallest B with 1/(B+1) <= a/2 (matches eq_selection_v4.b_required;
    the earlier int(2/a)+1 was off by one — adversarial review minor 1)."""
    import math
    return math.ceil(2 / a) - 1


def adjudicate(p, a, B):
    """Single adjudicator, shared semantics with eq_selection_v4.adjudicate
    (review minor 2): a failing p is FAIL regardless of resolution (more B
    cannot rescue p > alpha); the floor matters only for passes."""
    floor = 1 / (B + 1)
    if p > a:
        return "FAIL_corrected"
    if abs(p - floor) < 1e-12:
        return "AT_FLOOR_RESOLUTION_LIMITED"
    if floor > a / 2:
        return "UNDER_RESOLVED_DESIGN"
    return "REJECT_H0_corrected"


def basis_grid(p, m_cum, m_final, m_within):
    """Adversarial review B-2: the correction convention was discretionary;
    publish the verdict under every defensible basis."""
    return {
        "sidak_.05_cumulative_m": "pass" if p <= sidak(0.05, m_cum) else "FAIL",
        "sidak_.05_final_m10": "pass" if p <= sidak(0.05, m_final) else "FAIL",
        "bonferroni_.05_cumulative": "pass" if p <= 0.05 / m_cum else "FAIL",
        "bonferroni_declared_.01": "pass" if p <= 0.01 / m_cum else "FAIL",
        "per_run_within_m": "pass" if p <= sidak(0.05, m_within) else "FAIL",
        "playbook_H4_families_engaged_1": "pass" if p <= 0.05 else "FAIL",
    }


def readjudicate():
    cm = cumulative_m()
    m_final = cm["REGISTRATION_EQ_MOONDIST_CONFIRM.md"]
    m_at = {"eq_tidal_v1": cm["REGISTRATION_EQ_TIDAL.md"],
            "eq_tidal_v2": cm["REGISTRATION_EQ_TIDAL_V2.md"]}
    m_within = {"eq_tidal_v1": 5, "eq_tidal_v2": 3}
    out = {"correction_basis": f"PRIMARY: Sidak, base alpha {ALPHA}, cumulative "
                               f"family m at verdict time (ledger charges). "
                               f"DISCRETIONARY — full basis grid published per "
                               f"claim (adversarial review B-2); convention "
                               f"requires HUMAN-GATE ratification.",
           "family": FAMILY, "cumulative_m": cm, "claims": {},
           "ratification": {"status": "PENDING", "required_from": "lab owner",
                            "scope": "correction convention + each status change"}}
    for run, date, claims, B in RUNS:
        m = m_at[run]
        a = sidak(ALPHA, m)
        floor = 1 / (B + 1)
        for label, (cid, p) in claims.items():
            out["claims"][f"{run}.{label}"] = {
                "claim_id": cid, "binding_p": p, "m_family_at_verdict": m,
                "alpha_corrected": a, "floor_B200": floor,
                "floor_rule_ok": floor <= a / 2,
                "B_required_for_floor_rule": b_required(a),
                "raw_verdict_was": "pass raw 0.01" if p <= 0.01 else "fail raw 0.01",
                "corrected_status": adjudicate(p, a, B),
                "basis_sensitivity": basis_grid(p, m, m_final, m_within[run])}
    # E-1: corrected-criterion re-selection from stored family_records
    v2 = R("eq_tidal_v2.json")
    resel = {}
    for cid, c in v2["claims"].items():
        recs = {f: d["nll_val"] for f, d in c["family_records"].items()}
        best = min(recs, key=recs.get)
        resel[cid] = {"selected_by_frozen_J": c["selected_family"],
                      "selected_by_pure_val_nll": best,
                      "val_nll": recs,
                      "agrees": best == c["selected_family"]}
    out["e1_reselection_pure_heldout_nll"] = resel
    # E-3: confirm1 status
    b_key = "eq_tidal_v2.claimB_moondist"
    out["confirm1"] = {
        "published_verdict": "MECHANISM_SUPPORTED",
        "pedigree_dependency": "v2 claim B binding surrogate p=0.00995 <= 0.01 "
                               "(REGISTRATION_EQ_MOONDIST_CONFIRM.md:45)",
        "pedigree_corrected_status": out["claims"][b_key]["corrected_status"],
        "additional_defects": ["no registered skill baselines (audit E-3)",
                               "fresh data from same DE441 integrator "
                               "(registration concedes not independent)"],
        "corrected_status": "UNCONFIRMED — pending v4: corrected selection "
                            "criterion, B>=399, verdict-time correction "
                            "in-run, >=2 registered baselines, independent "
                            "source for any MECHANISM_SUPPORTED label"}
    return out


if __name__ == "__main__":
    res = readjudicate()
    path = os.path.join(ROOT, "results", "eq_readjudication_2026-07-02.json")
    json.dump(res, open(path, "w"), indent=2)
    print(json.dumps({k: v for k, v in res["claims"].items()}, indent=1))
    print("confirm1 ->", res["confirm1"]["corrected_status"][:60])
    print("written", os.path.relpath(path, ROOT))
