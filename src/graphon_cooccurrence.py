#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Instrument B — Graphon limit test on the ball co-occurrence graph.
Registered: docs/REGISTRATION_BATCH4.md. Theorem card: docs/kb/graphons-cut-norm.md.

B1  Under H0 the weighted co-occurrence graph converges to the constant graphon
    W = c (Lovasz-Szegedy; Aldous-Hoover). Statistic: spectral norm of the
    centered co-occurrence matrix (Frieze-Kannan: ||A||_cut <= ||A||_2 / n, so
    lambda-based detection is a conservative cut-norm proxy). Null from the
    constrained ensemble (exactly 6 per draw), K=2000, two... one-sided upper
    (structure inflates the norm).
H-PROTOCOL  On the same null replicates compute the MP statistic lambda_max of
    the indicator correlation matrix; null-correlation rho(B1, MP) >= 0.90 =>
    B1 joins the MP equivalence class and adds 0 tests to the batch family.

Deterministic: SEED=37. Output contract: one row per game + class verdict.
"""
import csv, os
import numpy as np

SEED = 37
K = 2000
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "datasets", "pcso-lotto", "data_draws_1yr.csv")
POOL = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
        "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load():
    games = {g: [] for g in POOL}
    with open(DATA) as f:
        for row in csv.DictReader(f):
            games[row["Game"]].append([int(row[f"N{i}"]) for i in range(1, 7)])
    return {g: np.array(v) - 1 for g, v in games.items()}   # 0-indexed

def indicators(draws, P):
    X = np.zeros((len(draws), P))
    X[np.arange(len(draws))[:, None], draws] = 1.0
    return X

def stats_pair(X, P):
    """(B1 spectral norm of centered co-occurrence, MP lambda_max of corr)."""
    T = len(X)
    C = X.T @ X
    np.fill_diagonal(C, 0.0)
    c = T * 30.0 / (P * (P - 1))                  # E[C_ij] under H0
    A = C - c
    np.fill_diagonal(A, 0.0)
    b1 = np.abs(np.linalg.eigvalsh(A)).max()
    Xc = X - X.mean(axis=0)
    sd = Xc.std(axis=0); sd[sd == 0] = 1.0
    R = (Xc / sd).T @ (Xc / sd) / T
    mp = np.linalg.eigvalsh(R).max()
    return b1, mp

def analyze(name, draws, rng, label=""):
    T, P = len(draws), POOL[name]
    b1_obs, mp_obs = stats_pair(indicators(draws, P), P)
    nb1 = np.empty(K); nmp = np.empty(K)
    for j in range(K):
        m = rng.random((T, P)).argsort(axis=1)[:, :6]
        nb1[j], nmp[j] = stats_pair(indicators(m, P), P)
    p_b1 = (np.sum(nb1 >= b1_obs) + 1) / (K + 1)
    rho = np.corrcoef(nb1, nmp)[0, 1]
    print(f"{label}{name:18s} B1={b1_obs:7.2f} null[{nb1.mean():6.2f}±{nb1.std():5.2f}] "
          f"p={p_b1:.4f} | null-corr(B1,MP)={rho:+.3f}")
    return p_b1, rho

def attribute(name, draws, rng):
    """Driving-row attribution for a fire: top eigenvector loadings, then
    re-test with the top ball's draws removed (K=500 null at reduced T)."""
    T, P = len(draws), POOL[name]
    X = indicators(draws, P)
    C = X.T @ X; np.fill_diagonal(C, 0.0)
    A = C - T * 30.0 / (P * (P - 1)); np.fill_diagonal(A, 0.0)
    w, v = np.linalg.eigh(A)
    vec = v[:, np.abs(w).argmax()]
    top = np.argsort(-np.abs(vec))[:3]
    print(f"  ATTRIBUTION {name}: top loadings " +
          ", ".join(f"ball {b+1}:{vec[b]:+.3f}" for b in top))
    lead = top[0]
    mask = ~(draws == lead).any(axis=1)
    sub = draws[mask]; T2 = len(sub)
    b1, _ = stats_pair(indicators(sub, P), P)
    # note: E-centering uses T2; stats_pair centers internally via its own T
    nulls = np.empty(500)
    for j in range(500):
        m = rng.random((T2, P)).argsort(axis=1)[:, :6]
        nulls[j], _ = stats_pair(indicators(m, P), P)
    p2 = (np.sum(nulls >= b1) + 1) / 501
    print(f"  without ball {lead+1} ({T-T2} rows removed): B1={b1:.2f}, p={p2:.4f} "
          f"-> {'fire persists: NEW structure' if p2 < 0.0025 else 'fire dissolves: same driving rows as the leading ball'}")

def main():
    rng = np.random.default_rng(SEED)
    games = load()
    print(f"INSTRUMENT B — graphon co-occurrence. K={K}, SEED={SEED}\n")
    print("— Null-trial admission (synthetic H0 year; must be silent at p>0.0025) —")
    ok = True
    for g in games:
        T, P = len(games[g]), POOL[g]
        synth = rng.random((T, P)).argsort(axis=1)[:, :6]
        p, _ = analyze(g, synth, rng, label="[H0] ")
        ok &= p > 0.0025
    print(f"Admission: {'PASS' if ok else 'FAIL — instrument rejected'}\n")
    if not ok:
        return
    print("— Real data —")
    res = [(g, *analyze(g, d, rng)) for g, d in games.items()]
    rhos = [r for _, _, r in res]
    same = np.mean(rhos) >= 0.90
    print(f"\nH-PROTOCOL: mean null-corr(B1, MP lambda_max) = {np.mean(rhos):+.3f} -> "
          f"{'SAME equivalence class as MP (adds 0 tests)' if same else 'distinct class (counts 5 tests)'}")
    fired = [g for g, p, _ in res if p < 0.0025]
    if fired:
        print(f"VERDICT B1: fired in {fired} — running driving-row attribution:")
        for g in fired:
            attribute(g, games[g], rng)
        print("  NOTE: a fire whose driving rows are the adjudicated 6/55 #45 excess")
        print("  (THEOREM_SYNTHESIS sec. 4b — incl. the pair-affinity flag) is a")
        print("  RE-DETECTION: same anomaly, 0 new discoveries. Arbiter: registered")
        print("  confirmation set (REGISTRATION_BATCH4.md).")
    else:
        print("VERDICT B1: all games inside null band — co-occurrence graph is the constant graphon.")

if __name__ == "__main__":
    main()
