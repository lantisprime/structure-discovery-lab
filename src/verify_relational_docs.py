#!/usr/bin/env python3
"""Re-derives every number quoted in ADMISSION_RELATIONAL.md,
RESULTS_RELATIONAL_FIRSTRUN.md and THEOREM_SYNTHESIS rows 29-31 from the raw
result JSONs. Exits nonzero on any mismatch. Run after any rerun of the
admission suite or first run."""
import json, math, sys

ok = True
def chk(label, actual, expected, tol=1e-9):
    global ok
    good = abs(actual-expected) <= tol if isinstance(expected, float) else actual == expected
    if not good:
        ok = False; print("MISMATCH", label, actual, "!=", expected)

A = json.load(open('results/relational_admission.json'))
exp = {
 'R1_mmd_energy': (0.040, 0.268, 200, 1.00),
 'R2_gromov_wasserstein': (0.060, 0.434, 50, 1.00),
 'R3_cca_family': (0.050, 0.562, 200, 1.00),
 'R4_tda_persistence': (0.050, 0.518, 100, 1.00),
 'R5_graph_matching_spectra': (0.083, 0.121, 60, 1.00),
 'R6_coresets_landmarks_nystrom': (0.080, 0.843, 100, 1.00),
 'R7_matrix_completion': (0.010, 0.685, 100, 1.00),
}
for k, (fpr, ksp, n, pw) in exp.items():
    neg = [x for x in A[k] if x.startswith('negative')][0]
    pos = [x for x in A[k] if x.startswith('positive')][0]
    chk(k+' fpr', round(A[k][neg]['fpr_at_alpha'], 3), fpr, 5e-4)
    chk(k+' ksp', round(A[k][neg]['ks_p'], 3), ksp, 5e-4)
    chk(k+' n', A[k][neg]['n_trials'], n)
    chk(k+' power', A[k][pos]['power_at_alpha'], pw)
    chk(k+' admitted', A[k]['admission']['ADMITTED'], True)
    se = math.sqrt(.05*.95/n)
    chk(k+' fpr_within_3se', abs(A[k][neg]['fpr_at_alpha']-.05) <= 3*se+1e-12, True)
chk('R1 power@0.5', A['R1_mmd_energy']['powercurve_E4_mean_shift_0.5']['power_at_alpha'], 0.55)
chk('R3 in-sample rho', round(A['R3_cca_family']['in_sample_rho1_on_independent_data_mean'], 3), 0.674, 5e-4)
chk('R4 bottleneck', A['R4_tda_persistence']['bottleneck_sanity_circle_pair_closer'], '20/20')

F = json.load(open('results/relational_first_run.json'))
rc = F['recovery_curves']
exp_z = {
 'tidal_total_accel': [0.16, -0.19, 0.73, 4.65, 12.10, 19.68],
 'moon_distance_km': [-0.32, 0.26, 0.76, 3.47, 11.55, 19.29],
 'kp_daily_mean': [-0.00, 0.03, 0.40, 0.99, 1.95, 3.65],
 'lotto655_draw_sum': [-0.25, 0.56, -0.06, -0.14, -0.40, 0.13],
}
for s, zs in exp_z.items():
    for c, z in zip(rc[s]['curve'], zs):
        chk(f'{s} z@{c["frac"]}', round(c['mean_null_adjusted_z'], 2), z, 5e-3)
ps = [c['median_p'] for c in rc['lotto655_draw_sum']['curve']]
chk('lotto p min', round(min(ps), 2), 0.34, 5e-3)
chk('lotto p max', round(max(ps), 2), 0.64, 5e-3)
pres = F['lotto655_presence_recovery']['curve']
for c, (p, z) in zip(pres, [(0.265, 0.18), (0.075, 1.02), (0.355, 0.57),
                            (0.122, 0.77), (0.503, 0.28), (0.360, 0.38)]):
    chk(f'presence p@{c["frac"]}', round(c['median_p'], 3), p, 5e-4)
    chk(f'presence z@{c["frac"]}', round(c['mean_null_adjusted_z'], 2), z, 5e-3)
cca = F['paired_cca']
chk('HR3 rho', round(cca['H_R3_draws_vs_covariates']['heldout_rho1'], 3), 0.110, 5e-4)
chk('HR3 p', round(cca['H_R3_draws_vs_covariates']['p_shuffled_pairing'], 2), 0.17, 5e-3)
chk('HR3 q95', round(cca['H_R3_draws_vs_covariates']['null_q95'], 3), 0.203, 5e-4)
hr4 = cca['H_R4_tidal_vs_ephemerides_positive_control']
chk('HR4 rho', round(hr4['heldout_rho1'], 4), 0.9977, 5e-5)
chk('HR4 p', hr4['p_shuffled_pairing'], 0.005)
chk('HR4 q95', round(hr4['null_q95'], 3), 0.140, 6e-4)

print("FIRST-RUN + ADMISSION VERIFIED" if ok else "FAILURES FOUND")

# ---- Batch 5 + all-games checks (RESULTS_BATCH5.md, ledger rows 32-34) ----
B = json.load(open('results/relational_batch5.json'))
chk('shapegate fpr', B['shapegate']['fpr_at_alpha'], 0.075)
chk('shapegate ksp', round(B['shapegate']['ks_p'], 3), 0.997, 5e-4)
chk('shapegate passed', B['shapegate']['gate_passed'], True)
cg = B['crossgame']
chk('min pair p', cg['min_pair_p'], 0.05)
chk('sidak', round(cg['sidak_threshold'], 4), 0.0051, 5e-5)
chk('joint null', cg['joint_verdict_null'], True)
exp_lmax = {'Lotto 6/42': (16.93, 16.32, 1.57, 0.33),
            'Mega Lotto 6/45': (21.14, 17.46, 1.62, 0.02),
            'Super Lotto 6/49': (18.92, 18.31, 1.70, 0.37),
            'Grand Lotto 6/55': (26.26, 19.76, 1.67, 0.01),
            'Ultra Lotto 6/58': (22.69, 20.02, 1.81, 0.10)}
for g, (lm, nm, ns, p) in exp_lmax.items():
    v = cg['per_game_lambda_max'][g]
    chk(g+' lmax', round(v['lambda_max'], 2), lm, 5e-3)
    chk(g+' nullmean', round(v['null_mean'], 2), nm, 5e-3)
    chk(g+' nullstd', round(v['null_std'], 2), ns, 5e-3)
    chk(g+' p', round(v['p'], 2), p, 5e-3)
tp = B['topology']['series']
exp_topo = {'tidal_total_accel': (1.124, 0.478, 0.01),
            'moon_distance_km': (1.201, 0.484, 0.01),
            'kp_daily_mean': (0.290, 0.509, 0.98),
            'lotto655_draw_sum': (0.427, 0.518, 0.25)}
for s, (h, q, p) in exp_topo.items():
    chk(s+' H1', round(tp[s]['max_h1_persistence'], 3), h, 5e-4)
    chk(s+' q95', round(tp[s]['null_q95'], 3), q, 5e-4)
    chk(s+' p', round(tp[s]['p'], 2), p, 5e-3)
rec = B['recovery']['curves']
exp_land = {'tidal_total_accel': [0.350, 0.070, 0.020, 0.020],
            'lotto655_draw_sum': [0.430, 0.510, 0.570, 0.740]}
for s, ps in exp_land.items():
    for c, p in zip(rec[s], ps):
        chk(f'{s} landmark p@{c["frac"]}', round(c['median_p'], 3), p, 5e-4)

T = json.load(open('results/batch5_c9_trace.json'))
chk('6/55 trace top number', T['Grand Lotto 6/55'][0][0], 45)
chk('6/55 trace loading', T['Grand Lotto 6/55'][0][1], 0.439, 5e-4)
chk('6/45 trace top number', T['Mega Lotto 6/45'][0][0], 4)

G = json.load(open('results/relational_allgames.json'))
exp_ag = {'g42': (0.53, 0.077, 0.295), 'g45': (0.86, -0.002, 0.490),
          'g49': (0.76, 0.029, 0.375), 'g55': (0.36, 0.110, 0.190),
          'g58': (0.13, -0.010, 0.560)}
for k, (tpp, rho, ccap) in exp_ag.items():
    g = G[k]
    chk(k+' topo p', round(g['topology_h1']['p'], 2), tpp, 5e-3)
    chk(k+' cca rho', round(g['cca_vs_covariates']['heldout_rho1'], 3), rho, 5e-4)
    chk(k+' cca p', round(g['cca_vs_covariates']['p_shuffled_pairing'], 3), ccap, 5e-4)
    zs = [c['mean_null_adjusted_z'] for c in g['drawsum_recovery']] + \
         [c['mean_null_adjusted_z'] for c in g['presence_recovery']]
    chk(k+' all z inside band', all(abs(z) < 2 for z in zs), True)
    chk(k+' no significant median p', all(c['median_p'] > 0.05
        for c in g['drawsum_recovery'] + g['presence_recovery']), True)

print("BATCH5 + ALLGAMES VERIFIED" if ok else "BATCH5 FAILURES FOUND")

# ---- Batch 6 checks (RESULTS_BATCH6.md, ledger row 35) --------------------
S = json.load(open('results/relational_subsets.json'))
chk('b6 gate fpr', S['gate']['fpr_at_alpha'], 0.15)
chk('b6 gate ksp', round(S['gate']['ks_p'], 3), 0.422, 5e-4)
chk('b6 gate passed', S['gate']['gate_passed'], True)
chk('b6 mmd min_p', round(S['mmd']['min_p'], 3), 0.040, 5e-4)
chk('b6 mmd sidak', round(S['mmd']['sidak_threshold'], 4), 0.0017, 5e-5)
chk('b6 mmd joint null', S['mmd']['joint_verdict_null'], True)
raw_flags = [(g, q, p) for g, pairs in S['mmd']['per_game'].items()
             for q, p in pairs.items() if p <= 0.05]
chk('b6 mmd one raw flag', len(raw_flags), 1)
chk('b6 mmd flag is 6/58 Q2|Q4', raw_flags[0][:2],
    ('Ultra Lotto 6/58', 'Q2|Q4'))
chk('b6 spectra min_p', round(S['spectra']['min_p'], 3), 0.070, 5e-4)
chk('b6 spectra joint null', S['spectra']['joint_verdict_null'], True)
chk('b6 spectra no raw flags', sum(p <= 0.05 for g in S['spectra']['per_game'].values()
                                   for p in g.values()), 0)
h = S['halves']
chk('b6 halves min_p', round(h['min_p'], 3), 0.025, 5e-4)
chk('b6 halves sidak', round(h['sidak_threshold'], 4), 0.0102, 5e-5)
chk('b6 halves joint null', h['joint_verdict_null'], True)
exp_h = {'Lotto 6/42': (0.060, 0.360, 19), 'Mega Lotto 6/45': (0.147, 0.210, 26),
         'Super Lotto 6/49': (0.004, 0.435, 44), 'Grand Lotto 6/55': (0.251, 0.025, 45),
         'Ultra Lotto 6/58': (0.060, 0.330, 50)}
for g, (c, p, topn) in exp_h.items():
    v = h['per_game'][g]
    chk(g+' corr', round(v['hot_number_corr'], 3), c, 5e-4)
    chk(g+' p', round(v['p'], 3), p, 5e-4)
    chk(g+' top contributor', v['top_contributors'][0][0], topn)
chk('6/55 #45 contrib', round(h['per_game']['Grand Lotto 6/55']['top_contributors'][0][1], 1), 68.6, 5e-2)
chk('6/55 #42 contrib', round(h['per_game']['Grand Lotto 6/55']['top_contributors'][1][1], 1), 56.1, 5e-2)
chk('6/55 second contributor is 42', h['per_game']['Grand Lotto 6/55']['top_contributors'][1][0], 42)

print("BATCH6 VERIFIED" if ok else "BATCH6 FAILURES FOUND")

# ---- Pressure (baseline + batch 7) checks (RESULTS_PRESSURE.md, rows 36-37) ----
P = json.load(open('results/relational_pressure.json'))
zs = [c['mean_null_adjusted_z'] for c in P['HP1_pressure_recovery']['curve']]
chk('HP1 z@10%', round(zs[3], 1), 4.5, 0.05)
chk('HP1 z@20%', round(zs[4], 1), 7.4, 0.05)
chk('HP1 z@40%', round(zs[5], 1), 10.5, 0.05)
exp_hp2 = {'Lotto 6/42': (0.132, 0.180, 0.044, 0.555),
           'Mega Lotto 6/45': (0.261, 0.030, -0.180, 0.025),
           'Super Lotto 6/49': (0.107, 0.220, 0.009, 0.920),
           'Grand Lotto 6/55': (-0.072, 0.715, -0.063, 0.475),
           'Ultra Lotto 6/58': (-0.208, 0.940, 0.139, 0.075)}
for g, (rho, cp, sc, sp) in exp_hp2.items():
    v = P['HP2_per_game'][g]
    chk(g+' rho', round(v['cca_heldout_rho1'], 3), rho, 5e-4)
    chk(g+' cca p', round(v['cca_p'], 3), cp, 5e-4)
    chk(g+' corr', round(v['corr_sum_pressure'], 3), sc, 5e-4)
    chk(g+' scalar p', round(v['p_scalar'], 3), sp, 5e-4)
chk('HP2 min cca p', round(P['HP2_min_cca_p'], 3), 0.030, 5e-4)
chk('HP2 joint null', P['HP2_joint_null'], True)

B7 = json.load(open('results/relational_batch7.json'))
chk('B7 seasons all floor', all(p == 0.005 for p in B7['seasons']['pairs'].values()), True)
chk('B7 seasons n corrected rejections', B7['seasons']['n_reject_corrected'], 6)
chk('B7 sunmoon rho', round(B7['cca']['pressure_vs_sunmoon']['heldout_rho1'], 3), 0.567, 5e-4)
chk('B7 sunmoon p', B7['cca']['pressure_vs_sunmoon']['p_shuffled_pairing'], 0.005)
chk('B7 kp rho', round(B7['cca']['pressure_vs_kp']['heldout_rho1'], 3), -0.012, 5e-4)
chk('B7 kp p', round(B7['cca']['pressure_vs_kp']['p_shuffled_pairing'], 3), 0.605, 5e-4)
chk('B7 gw gate fpr', B7['gwgate']['fpr_at_alpha'], 0.05)
chk('B7 gw gate passed', B7['gwgate']['gate_passed'], True)
gw = B7['gw']
chk('GW tidal-moon dist', round(-gw['tidal|moon']['score'], 3), 0.023, 5e-4)
chk('GW tidal-moon p', gw['tidal|moon']['p'], 0.05)
chk('GW pressure-lotto p', round(gw['pressure|lotto655_sum']['p'], 2), 0.30, 5e-3)
chk('GW pressure-tidal p', gw['pressure|tidal']['p'], 1.0)
chk('GW pressure-tidal dist', round(-gw['pressure|tidal']['score'], 3), 0.173, 5e-4)

print("PRESSURE + BATCH7 VERIFIED" if ok else "PRESSURE FAILURES FOUND")
sys.exit(0 if ok else 1)
