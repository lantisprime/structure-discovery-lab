# REGISTRATION AMENDMENT — 2026-09-27 — pcso.picker.prospective1

**STATUS: APPROVED 2026-09-27 (lab owner, in session: "agree to 1 and 2").** Drafted by GPT Astra 6 (peer mathematician seat) from its A1/B review (I1 item 2). This file is commitment-hashed into `results/commitment_ledger.txt` before any prospective scoring.

**Authorization:** lab owner, 2026-09-27. This amendment replaces clauses 20–22 and the advantage-bound Definitions of `pcso.picker.prospective1`, effective upon prospective anchoring under clause 24, before any prospective scoring.

Everything else remains unchanged. In particular, clause 19 retains the ensemble uniform-null rule \(E_n^{\mathrm{ensemble}}\ge200\), its separate 0.005 allocation, and its existing certification requirements. The advantage family retains allocation 0.005, boundary 1,400, and exactly seven models: `dirichlet_cp_a100`, `tilt_high31`, `tilt_linear`, `pair_parity`, `cp_nest`, `ensemble`, and `cp_sparse_switch`.

**20.** Allocate 0.005 equally to those seven model-versus-uniform comparisons. Replace the Hoeffding mixture with exactly the empirical-Bernstein mixture and inversion below. Grid points and mixture weights are fixed; outcome-dependent grid selection, restarting killed terms, and weight renormalization are prohibited.

**21.** The estimand remains the mean conditional expected log-score improvement over every scored target, including uniform fallbacks. Report positive validated advantage for model \(m\) only at a certified prefix with \(L_n^m>0\). Uniform’s improvement remains identically zero.

**22.** Before each covered draw, commit finite score bounds enclosing every possible six-subset. Scores, centers, bounds, residual penalties, accumulations, mixture evaluations, and inversion require conservative numerical enclosures supported by interval arithmetic or proved error bounds, addressing A1 finding F3. A numerical interval straddling a decision threshold cannot authorize a claim. Certification failure never authorizes retrospective omission or replacement of a locked forecast.

**Replacement Definitions.** All logarithms are natural. Let \(\mathcal F_{t-1}\) contain the information preceding scored draw \(t\), including its locked law and committed bounds. For each model:
\[
D_t^m=\log\frac{q_t^m(S_t)}{p_{0,t}(S_t)},\quad
A_n^m=\sum_{t=1}^nD_t^m,\quad
\mu_t^m=\mathbb E[D_t^m\mid\mathcal F_{t-1}],\quad
\bar\mu_n^m=\frac1n\sum_{t=1}^n\mu_t^m.
\]

Fix the center to the committed law’s own expected improvement:
\[
\widehat D_t^m=\sum_{S:\,|S|=6}q_t^m(S)\log\frac{q_t^m(S)}{p_{0,t}(S)}.
\]
This exact finite sum, or a mathematically equivalent certified evaluation, defines the center; neither a running mean nor a fitted substitute is permitted. It is predictable and belongs to every valid score enclosure because it averages possible scores under the normalized committed law. Validity does not assume that this law is the true conditional distribution.

Let \([\ell_t^m,h_t^m]\) be the committed, certified enclosure returned by `score_bounds` for that locked full law, and define \(c_t^m=h_t^m-\ell_t^m\). Widths may vary predictably across targets. They are not observed-score ranges.

Register the numerical grid scale \(c_\star=1\) nat, independent of all data; it is a grid scale, not an asserted universal range bound. The exact grid, in inverse nats, is
\[
(\lambda_1,\ldots,\lambda_{13})
=(1/2,1/4,1/8,1/16,1/32,1/64,1/128,1/256,1/512,1/1024,1/2048,1/4096,1/8192).
\]
Every term has fixed weight \(w_j=1/13\). Define \(\psi(u)=-\log(1-u)-u\) for \(0\le u<1\).

Before observing draw \(t\), permanently kill term \(j\) for model \(m\) if \(\lambda_jc_t^m\ge1\). Its contribution becomes zero forever; its original weight is neither redistributed nor replaced. Let
\[
J_n^m=\{j:\lambda_jc_t^m<1\text{ for every }1\le t\le n\}.
\]
For surviving terms define
\[
H_{j,n}^m=\sum_{t=1}^n
\begin{cases}
\psi(\lambda_jc_t^m)(D_t^m-\widehat D_t^m)^2/(c_t^m)^2,&c_t^m>0,\\
0,&c_t^m=0.
\end{cases}
\]
Zero width makes the score conditionally constant and the residual zero. Uniform fallbacks have \(D_t^m=\widehat D_t^m=c_t^m=0\); they remain included in \(n\).

Define
\[
G_{\mathrm{EB},n}^m(x)=\frac1{13}\sum_{j\in J_n^m}\exp\{\lambda_jx-H_{j,n}^m\}.
\]
Initially all terms are alive, \(A_0^m=H_{j,0}^m=0\), and \(G_{\mathrm{EB},0}^m(0)=1\). If \(J_n^m\ne\varnothing\), let \(u_n^m\) be the unique real solution of \(G_{\mathrm{EB},n}^m(u_n^m)=1400\), and set
\[
L_n^m=(A_n^m-u_n^m)/n,\qquad n\ge1.
\]
If no term survives, set \(u_n^m=+\infty\) and \(L_n^m=-\infty\). Positive validated advantage requires a certified \(L_n^m>0\), equivalently a certified \(G_{\mathrm{EB},n}^m(A_n^m)>1400\).

**Validity and proof sketch.**
The residual inequality is from [Howard, Ramdas, McAuliffe and Sekhon (2021), *Time-uniform, nonparametric, nonasymptotic confidence sequences*, Appendix A.8](https://arxiv.org/pdf/1810.08240).
For \(c_t>0\), put \(R_t=(D_t-\widehat D_t)/c_t\in[-1,1]\) and \(v=\lambda c_t<1\).
The inequality \(\exp\{vR-\psi(v)R^2\}\le1+vR\) implies, with \(a=\lambda(\mu_t-\widehat D_t)\),
\[
\mathbb E_{t-1}\exp\{\lambda(D_t-\mu_t)-\psi(\lambda c_t)R_t^2\}\le e^{-a}(1+a)\le1.
\]
Zero-width increments contribute factor one; predictable permanent killing only decreases nonnegative capital.
Thus \(G_{\mathrm{EB},n}^m(A_n^m-\sum_{t\le n}\mu_t^m)\) is a nonnegative supermartingale starting at one.
Ville’s inequality and the seven-model union bound give \(\Pr(\forall m,n\ge1:L_n^m\le\bar\mu_n^m)\ge1-7/1400=0.995\).
Each \(\lambda_j\) is constant across time, so inversion targets the unchanged unweighted conditional-mean average; centering affects only the residual penalty.
Together with clause 19’s allocation, the combined false-claim probability remains at most 0.01.

**Registered score-bound defaults.** Any valid finite predictable enclosure of \(D_t^m\) is permitted as a non-inferential implementation choice, with its procedure and endpoints committed before the covered draw. Intersect the following applicable constructions with the existing componentwise bounds; numerical certification remains mandatory. Write \(s_6^-\) and \(s_6^+\) for sums of the six smallest and largest coordinates.

- **Sparse supports of size at most two:** expand the likelihood ratio exactly as \(r(x)=b+d^\top x+\sum_{i<j}J_{ij}x_ix_j\), where \(x_i\in\{0,1\}\), \(\sum_i x_i=6\), and \(J\) is symmetric with zero diagonal. Let \(l_i,u_i\) sum the five smallest/largest off-diagonal entries of row \(i\). Then \(b+s_6^-(d+l/2)\le r(x)\le b+s_6^+(d+u/2)\), because each selected vertex has five selected neighbours. Intersect in likelihood-ratio space with existing bounds before taking logs; a nonpositive proposed lower endpoint supplies no logarithmic improvement.
- **CP mixtures:** write \(F(x)=\log\sum_j a_j e^{z_j(x)}\), with affine component log-ratios \(z_j\). Default to \(x_0=(6/P)\mathbf1\), \(g=\nabla F(x_0)\); convexity gives lower bound \(F(x_0)-g^\top x_0+s_6^-(g)\). For each component, obtain its exact affine range by selecting six extreme coefficients. Replace its exponential by the secant on that interval, using the constant exponential for a singleton interval. If the weighted secants sum to \(\beta+v^\top x\), the upper score bound is \(\log[\beta+s_6^+(v)]\). Other predictable tangent points are permitted. Propagate improved child intervals through ensemble weighted log-sum-exp.
- **Scalar-statistic laws:** enumerate all attainable ball sums \(21,\ldots,6P-15\) for linear laws, feasible high-ball counts for `high31`, and feasible odd counts for parity; take the minimum and maximum scores. Ball-sum enumeration also applies to signshare representations without adding signshare to this family. Single-component CP extrema use the six smallest/largest log-weights. Equivalent certified convexity-based shortcuts are permitted.

**Disclosed planning calculations; not inferential claims.** For each pool separately, let both truth and oracle forecast be \(q_\theta(S)\propto\exp\{\theta\sum_{i\in S}g_P(i)\}\), where \(\theta=0.05\) and \(g_P(i)=[i-(P+1)/2]/\sqrt{(P^2-1)/12}\). Exact integer subset-sum counting followed by numerical evaluation gives \(\mu=0.006581\)–\(0.006837\), variance \(\sigma^2=0.013153\)–\(0.013665\), and exact algebraic range width \(c_P=0.05\,6(P-6)/\sqrt{(P^2-1)/12}\).

Substitute \(A_n=n\mu\), \(V_n=nc_P^2\) into the registered Hoeffding mixture; for this amendment substitute \(A_n=n\mu\), \(H_{j,n}=n\psi(\lambda_jc_P)\sigma^2/c_P^2\). The center equals \(\mu\) in this oracle scenario. First integer mean-trajectory crossings strictly above 1,400 are:

| Pool | Registered Hoeffding | This fixed-grid EB rule |
|---|---:|---:|
| 42 | 89,568 | 8,337 |
| 45 | 89,711 | 8,275 |
| 49 | 89,903 | 8,204 |
| 55 | 90,178 | 8,119 |
| 58 | 90,308 | 8,083 |

These recomputed planning trajectories suggest approximately an elevenfold reduction for this oracle. They are not expected stopping times, simulated power, prospective evidence, or claims about the seven fitted models.