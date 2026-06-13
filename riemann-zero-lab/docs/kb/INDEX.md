# Knowledge Base Index — riemann-zero-lab

Theorem/methodology cards for the Riemann–Zeta Zero Discovery module. Same Part-3 gate as
the main lab (`docs/THEOREM_GOVERNANCE.md`): **no card, no instrument**. Cards follow the
house template (statement, assumptions, baseline/null value, detects/blind-to, finite-sample
cautions, fetched+cited reference summary, canonical references, use in project), adapted for
a *deterministic* mathematical object — the "null value under i.i.d. uniform" field becomes a
"reference / baseline behaviour" field, except for the spacing cards where a genuine
Poisson-vs-GUE null comparison applies.

## Face classification (module-local)

- **analytic / number-theoretic** — the objects (ζ, ξ) and the conjecture (RH).
- **computational** — the instrument that turns zero-finding into real root bracketing (Z).
- **statistical / cross-sectional** — the spacing structure and its random-matrix baseline.

## Card table

| # | Card | Face | One-line description |
|---|------|------|----------------------|
| 1 | [riemann-zeta.md](riemann-zeta.md) | analytic | ζ(s): series/Euler product, functional equation, trivial zeros at −2,−4,…, non-trivial zeros in the strip, N(T) counting function. |
| 2 | [completed-zeta-xi.md](completed-zeta-xi.md) | analytic | ξ(s)=½s(s−1)π^{−s/2}Γ(s/2)ζ(s); ξ(s)=ξ(1−s); entire; zeros of ξ ≡ non-trivial zeros of ζ; four-fold symmetry. |
| 3 | [hardy-z-function.md](hardy-z-function.md) | computational | Z(t)=e^{iθ(t)}ζ(½+it), real for real t; real zeros of Z ≡ critical-line zeros; Riemann–Siegel; Gram points; the bracketing instrument. |
| 4 | [riemann-hypothesis.md](riemann-hypothesis.md) | number theory | RH scope-boundary card: what numerical zero-finding can (finite verification, N(T) match) and cannot (prove RH) establish. |
| 5 | [zeta-zero-spacing.md](zeta-zero-spacing.md) | statistical | Unfolding via Ñ(t); nearest-neighbour spacings; Montgomery pair correlation 1−(sin πu/πu)²; Poisson vs GUE baselines. |
| 6 | [random-matrix-gue.md](random-matrix-gue.md) | cross-sectional | GUE(N), level repulsion s², Wigner surmise p(s)≈(32/π²)s²e^{−4s²/π}; the expected (not null) spacing law. |

## Relationship to the main lab KB

This module reuses the lab's RMT card `../../../docs/kb/marchenko-pastur-tracy-widom.md`
(Marchenko–Pastur / Tracy–Widom) as prior art for the random-matrix face; cards 5–6 here are
the zero-spacing-specific specialization. All other cards are new objects not present in the
lottery-facing KB. Cross-links use `[[card-name]]`.

## Governance note (deterministic-math adaptation)

The main lab's Article A1 ("one generative null, many lenses, derived by Monte Carlo") was
written for stochastic datasets. ζ is deterministic: there is no sampling null for "is t_n a
zero" — that is settled by computing |ζ(½+it_n)| to declared precision and by the N(T) count.
The MC-null machinery applies **only** to the spacing analysis (cards 5–6), where Poisson is
the genuine null and GUE the alternative. This boundary is stated in
`REGISTRATION_ZETA_ZERO_BATCH1.md` §Governance and is the module's main methodological
departure from the lottery batches — flagged to the lab owner for an eval-set decision.
