"""Independent replication: Grand Lotto 6/55 half-vs-half frequency deviation correlation."""
import numpy as np, pandas as pd, json

SEED = 2026
M = 199
K = 55

df = pd.read_csv('/sessions/exciting-trusting-heisenberg/mnt/structure-discovery-lab/datasets/pcso-lotto/data_draws_1yr_audited.csv')
g = df[df['Game'] == 'Grand Lotto 6/55'].copy()
g['Date'] = pd.to_datetime(g['Date'])
g = g.sort_values('Date').reset_index(drop=True)

def freq_dev(rows):
    counts = np.zeros(K)
    for _, r in rows.iterrows():
        for c in ['N1','N2','N3','N4','N5','N6']:
            v = int(r[c])
            assert 1 <= v <= K
            counts[v-1] += 1
    exp = len(rows) * 6.0 / K
    return counts - exp

def half_corr(rows):
    n = len(rows)
    h1, h2 = rows.iloc[:n//2], rows.iloc[n//2:]
    d1, d2 = freq_dev(h1), freq_dev(h2)
    return np.corrcoef(d1, d2)[0,1], len(h1), len(h2)

def sim_dev(n_draws, rng):
    counts = np.zeros(K)
    for _ in range(n_draws):
        pick = rng.choice(K, size=6, replace=False)
        counts[pick] += 1
    return counts - n_draws * 6.0 / K

def mc_p(obs_corr, n1, n2, rng):
    null = np.empty(M)
    for i in range(M):
        null[i] = np.corrcoef(sim_dev(n1, rng), sim_dev(n2, rng))[0,1]
    return (1 + np.sum(null >= obs_corr)) / (M + 1), null

results = {}
rng = np.random.default_rng(SEED)
corr_all, n1a, n2a = half_corr(g)
p_all, _ = mc_p(corr_all, n1a, n2a, rng)
results['with_all_rows'] = {'corr': round(float(corr_all), 3), 'p': round(float(p_all), 3),
                            'n_draws': int(len(g)), 'half_sizes': [n1a, n2a]}

g2 = g[g['Status'] != 'suspicious_or_needs_review'].reset_index(drop=True)
rng = np.random.default_rng(SEED)
corr_ex, n1b, n2b = half_corr(g2)
p_ex, _ = mc_p(corr_ex, n1b, n2b, rng)
results['excluding_suspicious'] = {'corr': round(float(corr_ex), 3), 'p': round(float(p_ex), 3),
                                   'n_draws': int(len(g2)), 'half_sizes': [n1b, n2b]}

print(g['Status'].value_counts().to_dict())
print(json.dumps(results, indent=1))
with open('/sessions/exciting-trusting-heisenberg/mnt/structure-discovery-lab/results/_indep_task2.json', 'w') as fh:
    json.dump(results, fh, indent=1)
