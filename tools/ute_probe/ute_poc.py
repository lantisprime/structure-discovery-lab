"""Feasibility probe: can Euclid-MCP's deterministic engine answer the Unified Theorem
Engine's planning questions over facts compiled from REAL theorem cards?

Facts are transcribed from docs/kb (faces, assumptions, detects/blind-to, cautions) and
from the lab's state (datasets, what has run). Rules encode constitution articles A2
(null-trial admission), A3 (equivalence classes), A4 (passes = coverage), A5 (stationarity
gate) and the KB rule "no card, no test". Every answer carries a proof tree.
"""
import json
import os

os.environ.setdefault("EUCLID_BACKEND", "native")   # pure-Python engine, no SWI-Prolog

KB = r"""
% ---------------- theorem cards (from docs/kb, 6 of 29) ----------------
card(permutation_tests)
card(chi_square_exact_mc)
card(markov_order_tests)
card(hurst_rs)
card(fisher_g_periodogram)
card(cca_family)
face(permutation_tests, statistical)
face(chi_square_exact_mc, statistical)
face(markov_order_tests, dynamical)
face(hurst_rs, dynamical)
face(fisher_g_periodogram, dynamical)
face(cca_family, relational)

% assumptions (one predicate each)
requires(permutation_tests, exchangeability)
requires(chi_square_exact_mc, categorical_counts)
requires(markov_order_tests, stationarity)
requires(markov_order_tests, enough_transitions)
requires(hurst_rs, stationary_increments)
requires(hurst_rs, long_span)
requires(fisher_g_periodogram, stationarity)
requires(cca_family, paired_rows)

% detects / blind to (alternatives)
detects(permutation_tests, covariate_association)
detects(chi_square_exact_mc, marginal_nonuniformity)
detects(markov_order_tests, first_order_dependence)
detects(hurst_rs, long_range_dependence)
detects(fisher_g_periodogram, single_frequency_cycle)
detects(cca_family, shared_latent_factor)
blind(markov_order_tests, long_range_dependence)
blind(hurst_rs, first_order_dependence)
blind(fisher_g_periodogram, broadband_dependence)
blind(chi_square_exact_mc, serial_dependence)

% A3 equivalence classes, A1 null generators
equivalence_class(markov_order_tests, serial_memory)
equivalence_class(hurst_rs, serial_memory)
equivalence_class(fisher_g_periodogram, periodicity)
null_generator(permutation_tests, mc)
null_generator(chi_square_exact_mc, mc)
null_generator(markov_order_tests, mc)
null_generator(hurst_rs, mc)
null_generator(fisher_g_periodogram, mc)
null_generator(cca_family, mc)

% finite-sample cautions as thresholds
min_n(hurst_rs, 2000)
min_n(markov_order_tests, 300)
min_n(fisher_g_periodogram, 200)
min_n(permutation_tests, 50)
min_n(chi_square_exact_mc, 100)
min_n(cca_family, 100)

% ---------------- datasets (lab state) ----------------
dataset(pcso_draws)
n(pcso_draws, 984)
property(pcso_draws, exchangeability)
property(pcso_draws, categorical_counts)
property(pcso_draws, stationarity)
property(pcso_draws, enough_transitions)
property(pcso_draws, stationary_increments)
dataset(jackpot_winners)
n(jackpot_winners, 984)
property(jackpot_winners, exchangeability)
property(jackpot_winners, paired_rows)
dataset(kp_index)
n(kp_index, 984)
property(kp_index, exchangeability)

% ---------------- run history (from ledgers) ----------------
ran(chi_square_exact_mc, pcso_draws, pass)
ran(markov_order_tests, pcso_draws, pass)
ran(permutation_tests, pcso_draws, pass)
ran(fisher_g_periodogram, pcso_draws, pass)
ran(hurst_rs, pcso_draws, pass)
null_trial_done(chi_square_exact_mc)
null_trial_done(markov_order_tests)
null_trial_done(permutation_tests)
null_trial_done(fisher_g_periodogram)
null_trial_done(hurst_rs)

% ---------------- rules: constitution + methodology ----------------
unmet($c, $d) IF requires($c, $p) AND NOT property($d, $p)
assumptions_hold($c, $d) IF card($c) AND dataset($d) AND NOT unmet($c, $d)
large_enough($c, $d) IF min_n($c, $m) AND n($d, $k) AND $k >= $m
admissible($c) IF card($c) AND null_generator($c, mc) AND null_trial_done($c)
applicable($c, $d) IF assumptions_hold($c, $d) AND large_enough($c, $d)
has_run($c, $d) IF ran($c, $d, $v)
gap($c, $d) IF applicable($c, $d) AND admissible($c) AND NOT has_run($c, $d)
blocked_by_a2($c, $d) IF applicable($c, $d) AND NOT admissible($c)
blocked_by_assumption($c, $d, $p) IF card($c) AND dataset($d) AND requires($c, $p) AND NOT property($d, $p)
too_small($c, $d) IF card($c) AND dataset($d) AND NOT large_enough($c, $d)
covered($alt, $d) IF detects($c, $alt) AND ran($c, $d, $v)
named_alternative($alt) IF detects($c, $alt)
named_alternative($alt) IF blind($c, $alt)
blind_spot($alt, $d) IF named_alternative($alt) AND dataset($d) AND NOT covered($alt, $d)
same_family($a, $b) IF equivalence_class($a, $f) AND equivalence_class($b, $f) AND $a != $b
"""

QUERIES = [
    "gap($card, $dataset)",
    "blocked_by_a2($card, $dataset)",
    "blocked_by_assumption($card, $dataset, $missing)",
    "too_small($card, $dataset)",
    "blind_spot($alternative, pcso_draws)",
    "same_family($a, $b)",
]


def compact(proof, depth=0):
    if not isinstance(proof, dict):
        return ""
    t = proof.get("type")
    line = "  " * depth + f"{t}: {proof.get('goal', '')}" + (f"  <- {proof.get('body')}" if proof.get("body") else "")
    out = [line]
    for k in ("subproof", "left", "right"):
        if proof.get(k):
            out.append(compact(proof[k], depth + 1))
    return "\n".join(x for x in out if x)


def main():
    from euclid_mcp.server import reason, diagnose
    for q in QUERIES:
        res = reason(knowledge=KB, query=q, max_solutions=50).model_dump()
        sols = res.get("solutions", [])
        print(f"\n== ? {q}   ({len(sols)} solutions, {res.get('elapsed_ms')} ms, hash {str(res.get('content_hash'))[:12]})")
        if res.get("error"):
            print("   ERROR:", res["error"])
        for s in sols:
            print("  ", s.get("substitutions"))
        if sols and sols[0].get("proof"):
            print("   proof of the first solution:")
            print("\n".join("     " + l for l in compact(sols[0]["proof"]).splitlines()[:12]))
    print("\n== why_not gap(hurst_rs, kp_index)")
    d = diagnose(knowledge=KB, query="gap(hurst_rs, kp_index)", mode="why_not").model_dump()
    print(json.dumps(d, indent=1, default=str)[:3000])
    print("\n== what_needs gap(hurst_rs, kp_index)  (abduction: which facts would make it true?)")
    d = diagnose(knowledge=KB, query="gap(hurst_rs, kp_index)", mode="what_needs").model_dump()
    print(json.dumps({k: d[k] for k in ("holds", "findings", "conclusion", "error")}, indent=1, default=str)[:2500])
    print("\n== what_needs gap(cca_family, jackpot_winners)")
    d = diagnose(knowledge=KB, query="gap(cca_family, jackpot_winners)", mode="what_needs").model_dump()
    print(json.dumps({k: d[k] for k in ("holds", "findings", "conclusion", "error")}, indent=1, default=str)[:2500])
    print("\n== what_needs admissible(cca_family)  (one-level rule)")
    d = diagnose(knowledge=KB, query="admissible(cca_family)", mode="what_needs").model_dump()
    print(json.dumps({k: d[k] for k in ("holds", "findings", "conclusion")}, indent=1, default=str)[:1200])
    print("\n== what_needs large_enough(hurst_rs, pcso_draws)  (arithmetic floor)")
    d = diagnose(knowledge=KB, query="large_enough(hurst_rs, pcso_draws)", mode="what_needs").model_dump()
    print(json.dumps({k: d[k] for k in ("holds", "findings", "conclusion")}, indent=1, default=str)[:1200])
    print("\n== why gap(permutation_tests, kp_index)")
    d = diagnose(knowledge=KB, query="gap(permutation_tests, kp_index)", mode="why").model_dump()
    print(json.dumps({k: d[k] for k in ("holds", "findings", "conclusion")}, indent=1, default=str)[:1500])
    print("\n== explain gap(permutation_tests, kp_index)  (proof tree -> readable steps, deterministic)")
    from euclid_mcp.server import explain, what_if, check_kb
    e = explain(knowledge=KB, query="gap(permutation_tests, kp_index)").model_dump()
    print(json.dumps(e, indent=1, default=str)[:2000])
    print("\n== what_if: the A5 gate passes on kp_index and the CCA null trial is done -> what opens?")
    w = what_if(base_knowledge=KB, modifications="+ property(kp_index, stationarity)\n+ null_trial_done(cca_family)",
                query="gap($c, $d)", max_solutions=50).model_dump()
    print(json.dumps({k: w[k] for k in ("before_count", "after_count", "delta", "conclusion", "error")}, indent=1, default=str)[:2500])
    print("  after:", [s.get("substitutions") for s in w.get("solutions_after", [])])
    print("\n== check_kb (validator: undefined predicates, cycles, duplicates)")
    c = check_kb(knowledge=KB).model_dump()
    print(json.dumps(c, indent=1, default=str)[:1500])
    print("\n== determinism: same KB twice -> same hash and same solution order?")
    a = reason(knowledge=KB, query="gap($c, $d)", max_solutions=50).model_dump()
    b = reason(knowledge=KB, query="gap($c, $d)", max_solutions=50).model_dump()
    print("hash equal:", a.get("content_hash") == b.get("content_hash"),
          "| solutions equal:", [s["substitutions"] for s in a["solutions"]] == [s["substitutions"] for s in b["solutions"]])


if __name__ == "__main__":
    main()
