"""Independent blind structure classification. Written from scratch.
Tests per series (all against permutation/Monte-Carlo nulls, m=999, seed fixed):
  T1 acf_lb   : Ljung-Box-style statistic, sum_{k=1..10} n*acf_k^2
  T2 runs     : Wald-Wolfowitz runs test above/below median, two-sided via permutation
  T3 spectral : Fisher's g = max periodogram ordinate / sum (detects periodicity)
  T4 lag1_spear: |Spearman autocorrelation at lag 1| (rank-based, robust)
Permutation null: shuffle the values (exchangeable null preserves marginal exactly).
p = (1 + #{null >= obs}) / (m + 1).
Verdict rule (pre-registered before looking at results):
  STRUCTURED            if any raw p < 0.0125 (Bonferroni 0.05/4) OR >=2 tests raw p < 0.05.
  BORDERLINE            if exactly one test has 0.0125 <= raw p < 0.05.
  NO DETECTED STRUCTURE otherwise.
"""
import numpy as np, pandas as pd, json, glob, os

RNG_SEED = 12345
M = 999
NLAGS = 10

def acf_stat(x, nlags=NLAGS):
    n = len(x)
    xc = x - x.mean()
    denom = np.dot(xc, xc)
    s = 0.0
    for k in range(1, nlags + 1):
        r = np.dot(xc[:-k], xc[k:]) / denom
        s += n * r * r
    return s

def runs_count(x):
    med = np.median(x)
    s = x > med
    return 1 + int(np.sum(s[1:] != s[:-1]))

def fisher_g(x):
    xc = x - x.mean()
    f = np.fft.rfft(xc)
    p = (f.real**2 + f.imag**2)[1:]  # drop DC
    return p.max() / p.sum()

def spearman_lag1(x):
    r = pd.Series(x).rank().values
    a, b = r[:-1], r[1:]
    a = a - a.mean(); b = b - b.mean()
    return abs(np.dot(a, b) / np.sqrt(np.dot(a, a) * np.dot(b, b)))

def analyze(x, rng):
    obs = {
        'acf_lb': acf_stat(x),
        'runs': runs_count(x),
        'fisher_g': fisher_g(x),
        'lag1_spear': spearman_lag1(x),
    }
    null = {k: np.empty(M) for k in obs}
    for i in range(M):
        xp = rng.permutation(x)
        null['acf_lb'][i] = acf_stat(xp)
        null['runs'][i] = runs_count(xp)
        null['fisher_g'][i] = fisher_g(xp)
        null['lag1_spear'][i] = spearman_lag1(xp)
    p = {}
    for k in ('acf_lb', 'fisher_g', 'lag1_spear'):
        p[k] = (1 + np.sum(null[k] >= obs[k])) / (M + 1)
    mu = null['runs'].mean()
    p['runs'] = (1 + np.sum(np.abs(null['runs'] - mu) >= abs(obs['runs'] - mu))) / (M + 1)
    obs['runs_null_mean'] = float(mu)
    return obs, p

def verdict(p):
    raw = [p['acf_lb'], p['runs'], p['fisher_g'], p['lag1_spear']]
    n_sig_bonf = sum(1 for v in raw if v < 0.0125)
    n_sig = sum(1 for v in raw if v < 0.05)
    if n_sig_bonf >= 1 or n_sig >= 2:
        return 'STRUCTURED'
    if n_sig == 1:
        return 'BORDERLINE'
    return 'NO DETECTED STRUCTURE'

base = '/sessions/exciting-trusting-heisenberg/mnt/structure-discovery-lab/results/blind'
out = {}
for f in sorted(glob.glob(os.path.join(base, 'series_*.csv'))):
    name = os.path.basename(f).replace('.csv', '')
    df = pd.read_csv(f).sort_values('t')
    x = df['value'].values.astype(float)
    rng = np.random.default_rng(RNG_SEED)
    obs, p = analyze(x, rng)
    out[name] = {
        'n': int(len(x)),
        'verdict': verdict(p),
        'tests': {
            'acf_lb_lags1_10': {'stat': round(float(obs['acf_lb']), 4), 'p': round(float(p['acf_lb']), 4)},
            'runs_test': {'runs': int(obs['runs']), 'null_mean_runs': round(obs['runs_null_mean'], 2),
                          'p_two_sided': round(float(p['runs']), 4)},
            'spectral_fisher_g': {'stat': round(float(obs['fisher_g']), 5), 'p': round(float(p['fisher_g']), 4)},
            'lag1_spearman_abs': {'stat': round(float(obs['lag1_spear']), 4), 'p': round(float(p['lag1_spear']), 4)},
        },
    }
    print(name, out[name]['verdict'],
          {k: (v.get('p') if 'p' in v else v.get('p_two_sided')) for k, v in out[name]['tests'].items()})

with open('/sessions/exciting-trusting-heisenberg/mnt/structure-discovery-lab/results/_indep_task1.json', 'w') as fh:
    json.dump(out, fh, indent=1)
print('done')
