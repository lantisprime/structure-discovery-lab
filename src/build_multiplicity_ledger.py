#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
"""External-review Priority 3: persistent global multiplicity ledger.
One JSONL row per real-data lotto-side test across the relational program,
with within-run family size and the global count. Also captures the
environment (external-review m1) to results/environment.json."""

import json
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
R = lambda f: json.load(open(os.path.join(ROOT, "results", f)))

LEDGER = os.path.join(ROOT, "results", "multiplicity_ledger.jsonl")


def rows():
    out = []

    def add(run, dataset, claim, method, p, m_perm, family, within_m,
            data_filter="all_rows"):
        out.append({"run_id": run, "dataset": dataset, "claim_type": claim,
                    "method": method, "raw_p": round(float(p), 4),
                    "m_perm": m_perm, "p_floor": round(1 / (m_perm + 1), 4),
                    "family_id": family, "within_run_m": within_m,
                    "data_filter": data_filter})

    F = R("relational_first_run.json")
    for c in F["recovery_curves"]["lotto655_draw_sum"]["curve"]:
        add("firstrun", "6/55", "subset-to-whole", "knn-recovery",
            c["median_p"], 49, "recovery", 6)
    add("firstrun", "6/55", "latent-sharing", "cca-covariates",
        F["paired_cca"]["H_R3_draws_vs_covariates"]["p_shuffled_pairing"],
        199, "cca", 1)
    B5 = R("relational_batch5.json")
    for k, v in B5["crossgame"]["pairs"].items():
        add("batch5", k, "cross-dataset-similarity", "cooc-spectra",
            v["p"], 99, "graph", 10)
    G = R("relational_allgames.json")
    for k in ["g42", "g45", "g49", "g55", "g58"]:
        g = G[k]
        add("allgames", g["game"], "topological", "delay-embed-H1",
            g["topology_h1"]["p"], 99, "tda", 5)
        add("allgames", g["game"], "latent-sharing", "cca-covariates",
            g["cca_vs_covariates"]["p_shuffled_pairing"], 199, "cca", 5)
        for c in g["drawsum_recovery"]:
            add("allgames", g["game"], "subset-to-whole", "knn-recovery",
                c["median_p"], 49, "recovery", 30)
    S = R("relational_subsets.json")
    for gname, pairs in S["mmd"]["per_game"].items():
        for q, p in pairs.items():
            add("batch6", f"{gname} {q}", "distributional", "mmd",
                p, 99, "two-sample", 30)
    for gname, pairs in S["spectra"]["per_game"].items():
        for q, p in pairs.items():
            add("batch6", f"{gname} {q}", "cross-dataset-similarity",
                "cooc-spectra", p, 99, "graph", 30)
    for gname, v in S["halves"]["per_game"].items():
        add("batch6", gname, "frequency-bias-generalization", "half-corr",
            v["p"], 199, "hit-count-temporal", 5)
    P = R("relational_pressure.json")
    for gname, v in P["HP2_per_game"].items():
        add("pressure", gname, "latent-sharing", "cca-pressure",
            v["cca_p"], 199, "cca", 5)
        add("pressure", gname, "scalar-correlation", "corr-sum-pressure",
            v["p_scalar"], 199, "cca", 5)   # sub-statistic of the CCA (C3: one class)
    M = R("remediation_r1.json")
    for gname, v in M["presence_mc"]["per_game"].items():
        add("remediation", gname, "subset-to-whole", "matrix-completion",
            v["p"], 199, "recovery", 5)
    for gname, v in M["floors_lmax"]["per_game"].items():
        add("remediation", gname, "within-game-cooccurrence", "lambda-max",
            v["p"], 999, "hit-count-cooc", 5)
    # NOTE on equivalence classes: sensitivity regimes and split variants are
    # the SAME test on overlapping data (one class member each), not extra
    # multiplicity; lambda-max vs half-corr held as separate hit-count classes
    # provisionally, pending H-protocol null-correlation measurement.
    for gname, splits in M["cca_splits"]["per_game"].items():
        for tf, s in splits.items():
            add("remediation", gname, "latent-sharing", f"cca-split-{tf}",
                s["p"], 199, "cca", 5, data_filter=f"split_{tf}")
    sens = M["sensitivity"]
    for gname, regimes in sens.items():
        if gname.startswith("lambda"):
            add("remediation", "6/55", "within-game-cooccurrence",
                "lambda-max", regimes["p"], 399, "hit-count-cooc", 5,
                "ex_suspicious")
            continue
        for regime, x in regimes.items():
            if "p" in x:
                add("remediation", gname, "frequency-bias-generalization",
                    "half-corr", x["p"], 199, "hit-count-temporal", 5, regime)
    RR = R("rerun_batch67.json")
    for gname, pairs in RR["b6_mmd"]["per_game"].items():
        for q, pp in pairs.items():
            add("batch67_r2", f"{gname} {q}", "distributional", "mmd",
                pp, 1199, "two-sample", 30)
    for gname, pairs in RR["b6_spectra"]["per_game"].items():
        for q, pp in pairs.items():
            add("batch67_r2", f"{gname} {q}", "cross-dataset-similarity",
                "cooc-spectra", pp, 1199, "graph", 30)
    for gname, regimes in RR["b6_halves"]["per_game"].items():
        for regime, x in regimes.items():
            if "p" in x:
                add("batch67_r2", gname, "frequency-bias-generalization",
                    "half-corr", x["p"], 199, "hit-count-temporal", 5, regime)
    return out


def main():
    # AUDIT G-1 (2026-07-02): this builder used to truncate-and-rewrite the
    # ledger, deleting every row appended after the backfill (equation family
    # charges, schema-v2 migration fields). It is now NON-DESTRUCTIVE:
    #   - if a ledger exists on disk, it must be a superset of rows(); rows
    #     not reproducible from rows() are preserved verbatim, and any
    #     conflict on a reproducible row aborts the rebuild.
    #   - the rebuild goes to a temp file and only replaces the ledger after
    #     the invariant check passes.
    out = rows()

    def key(r):
        return (r.get("run_id"), r.get("dataset"), r.get("method"),
                r.get("data_filter"), r.get("family_id"), r.get("m_delta"))

    preserved, disk_by_key = [], {}
    if os.path.exists(LEDGER):
        disk = [json.loads(l) for l in open(LEDGER)]
        built_keys = {key(r) for r in out}
        for r in disk:
            if key(r) in built_keys:
                disk_by_key.setdefault(key(r), []).append(r)
            else:
                preserved.append(r)     # appended rows (charges, eq tests, ...)
        cursor = {k: 0 for k in disk_by_key}   # positional match within key group
        for i_r, r in enumerate(out):
            group = disk_by_key.get(key(r), [])
            i = cursor.get(key(r), 0)
            if i < len(group):
                d = group[i]
                cursor[key(r)] = i + 1
                if abs(d.get("raw_p", -1) - r.get("raw_p", -1)) > 1e-9:
                    raise SystemExit(
                        f"ABORT: rebuilt row disagrees with ledger on disk for "
                        f"{key(r)}: {d.get('raw_p')} != {r.get('raw_p')} — "
                        f"append-only invariant would be violated")
                # adversarial review B3: carry forward ALL disk fields (disk is
                # the annotated record — corrections, quarantines, flags);
                # rebuilt values win only for nothing: disk wins on conflicts
                # except global_m which is recomputed below.
                merged = {**r, **{k: v for k, v in d.items()
                                  if k != "global_m"}}
                out[i_r] = merged
        # unconsumed disk rows in a key group are legitimately appended
        # reruns sharing a key — preserve them (review B3 test 1)
        for k, group in disk_by_key.items():
            for d in group[cursor.get(k, 0):]:
                preserved.append(d)
    for r in out:
        r.setdefault("row_type", "test")
    # shared live definition (review M1): superseded and exploratory rows do
    # NOT count toward global m — same rule as design_verifier/meta panel
    live = [r for r in out + preserved
            if r.get("row_type") == "test" and "superseded_by" not in r
            and not r.get("exploratory")]
    g = len(live)
    tmp = LEDGER + ".tmp"
    final = out + preserved
    with open(tmp, "w") as f:
        for r in final:
            if r.get("row_type") == "test" and not r.get("exploratory"):
                r["global_m"] = g
            f.write(json.dumps(r) + "\n")
    # superset assertion (review B3): every disk row must survive the rebuild
    if os.path.exists(LEDGER):
        disk_ids = [(key(d), d.get("raw_p"), d.get("data_filter"))
                    for d in (json.loads(l) for l in open(LEDGER))]
        new_ids = [(key(d), d.get("raw_p"), d.get("data_filter")) for d in final]
        missing = [t for t in disk_ids if disk_ids.count(t) > new_ids.count(t)]
        if missing:
            os.remove(tmp)
            raise SystemExit(f"ABORT: rebuild would lose {len(missing)} disk "
                             f"row(s), e.g. {missing[0]}")
    os.replace(tmp, LEDGER)
    print(f"preserved {len(preserved)} appended rows; global_m={g} live tests")
    small = [r for r in out if r["raw_p"] <= 0.05]
    print(f"ledger: {g} tests | raw p<=0.05: {len(small)} "
          f"({100*len(small)/g:.1f}%, expectation {0.05*g:.1f})")
    for r in sorted(small, key=lambda r: r["raw_p"])[:8]:
        print("  ", r["run_id"], r["dataset"], r["method"], r["raw_p"], r["data_filter"])
    env = {"python": sys.version.split()[0], "platform": platform.platform()}
    for mod in ["numpy", "scipy", "pandas", "ot", "ripser", "networkx",
                "persim", "matplotlib", "sklearn"]:
        try:
            m = __import__(mod)
            env[mod] = getattr(m, "__version__", "?")
        except Exception:
            env[mod] = "absent"
    json.dump(env, open(os.path.join(ROOT, "results", "environment.json"), "w"),
              indent=2)
    print("environment captured")


if __name__ == "__main__":
    main()
