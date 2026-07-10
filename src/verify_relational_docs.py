#!/usr/bin/env python3
# DOMAIN ARTIFACT (pcso-lotto application): verifies/transcribes this domain's recorded
# results; domain vocabulary expected here. Neutral instruments live in src/core.
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

# ---- Remediation R1 checks (REMEDIATION_LOG.md, ledger rows 38-39) ---------
M = json.load(open('results/remediation_r1.json'))
chk('rem presence min_p', round(M['presence_mc']['min_p'], 3), 0.23, 5e-3)
chk('rem presence joint null', M['presence_mc']['joint_verdict_null'], True)
chk('rem lmax 655', round(M['floors_lmax']['per_game']['Grand Lotto 6/55']['p'], 4), 0.0010, 5e-5)
chk('rem lmax 645', round(M['floors_lmax']['per_game']['Mega Lotto 6/45']['p'], 4), 0.0150, 5e-5)
chk('rem lmax corrected rejections', M['floors_lmax']['n_corrected_rejections'], 1)
chk('rem gw tidal-moon p', M['floors_gw']['pairs']['tidal|moon']['p'], 0.01)
chk('rem gw pressure-lotto p', round(M['floors_gw']['pairs']['pressure|lotto655_sum']['p'], 2), 0.28, 5e-3)
chk('gate quarter fpr', M['gate_quarter']['fpr_at_alpha'], 0.035)
chk('gate quarter passed', M['gate_quarter']['gate_passed'], True)
chk('gate gw fpr', M['gate_gw']['fpr_at_alpha'], 0.055)
chk('gate gw FAILED (the flag)', M['gate_gw']['gate_passed'], False)
chk('pc r1 power@0.25', M['pc_r1']['power_by_shift']['0.25'], 0.2)
chk('pc r5 power@0.10', M['pc_r5']['power_by_p_in']['0.1'], 0.08)
sens = M['sensitivity']
chk('sens 655 all corr', sens['Grand Lotto 6/55']['all']['corr'], 0.251)
chk('sens 655 ex corr', sens['Grand Lotto 6/55']['ex_suspicious']['corr'], 0.154)
chk('sens 655 lmax ex-suspicious p', round(sens['lambda_max_655_ex_suspicious']['p'], 4), 0.0025, 5e-5)
U = json.load(open('results/meta_uniformity.json'))
# panel v2.1 (audit M-5/M-6 + adversarial review M5, 2026-07-02):
# ledger-driven; median-based, superseded, exploratory (separate stratum),
# eq, and miscalibrated-null rows excluded; alias-normalized dedup;
# discrete-lattice reference; composition sensitivity published.
chk('meta panel version', U['panel_version'], 2)
chk('meta panel sha', U['panel_sha'], '8c7891b558ab8a28')  # v2.2: corrected_rerun_r1 rows re-admitted
chk('meta n', U['n_tests'], 132)
chk('meta p discrete', round(U['p_meta_discrete'], 3), 0.032, 5e-4)
chk('meta frac05', round(U['frac_le_05'], 3), 0.106, 5e-4)
chk('meta frac05 above band (concentrates in #45 family)',
    U['frac_le_05'] > U['sim_frac_le_05_q05_q95'][1], True)
chk('meta sensitivity: flag robust across compositions',
    all(v['frac_le_05'] >= 0.088 for v in U['composition_sensitivity'].values()),
    True)
chk('meta exploratory stratum reported', U['exploratory_stratum']['n'], 7)
IV = json.load(open('results/independent_verification.json'))
blind_key = json.load(open('results/blind/_key.json'))
conc = 0
for L, truth in blind_key.items():
    v = IV['task1'][f'series_{L}']['verdict']
    conc += (v == 'NO DETECTED STRUCTURE') == truth.startswith('drawsum')
chk('blind concordance', conc, 9)
chk('indep replication corr all', round(IV['task2']['with_all_rows']['corr'], 3), 0.251, 5e-4)
chk('indep replication corr ex', round(IV['task2']['excluding_suspicious']['corr'], 3), 0.154, 5e-4)

print("REMEDIATION VERIFIED" if ok else "REMEDIATION FAILURES FOUND")

# ---- External-review adoptions (ledger schema v2, audit C-1 2026-07-02) ----
L = [json.loads(l) for l in open('results/multiplicity_ledger.jsonl')]
T = [r for r in L if r.get('row_type', 'test') == 'test']
LIVE = [r for r in T if 'superseded_by' not in r and not r.get('exploratory')]
chk('ledger rows', len(L), 271)
chk('ledger test rows', len(T), 267)
chk('ledger live test rows', len(LIVE), 195)
chk('ledger exploratory rows', sum(1 for r in T if r.get('exploratory')), 7)
chk('ledger charge rows', len(L) - len(T), 4)
chk('ledger global_m pinned', {r.get('global_m') for r in LIVE}, {195})
chk('ex-suspicious lmax row at m=399 (review B1)',
    next((r['m_perm'], r['p_floor'], r.get('at_floor')) for r in T
         if r.get('method') == 'lambda-max'
         and r.get('data_filter') == 'ex_suspicious'), (399, 0.0025, True))
chk('live frac<=.05', round(sum(r['raw_p'] <= 0.05 for r in LIVE
                                if r.get('raw_p') is not None)/len(LIVE), 3),
    0.097, 5e-4)
D = json.load(open('results/design_verifier_report.json'))
chk('design verifier verdict', D['verdict'], 'PASS')
chk('design verifier violations', len(D['violations']), 0)
chk('design verifier reconciliation', D['reconciliation']['run_ledger_declared'],
    D['reconciliation']['test_rows'])
import os
chk('environment captured', os.path.exists('results/environment.json'), True)
RL = [json.loads(l) for l in open('results/run_ledger.jsonl')]
required_run_ids = {
    'admission', 'firstrun', 'batch5', 'allgames', 'batch6', 'pressure',
    'remediation', 'blind_verification', 'cross_executor_verification_1',
    'blind_methodology_eval_v1', 'batch67_r2', 'r8_admission_attempt',
    'eq_tidal_v1', 'eq_tidal_v2', 'eq_tidal_v3',
    'eq_moondist_confirm1', 'synthetic_batch1_expA',
    'synthetic_batch1_expCD', 'audit_shadow_2026-07-02', 'readmission_v2',
    'blind_eval_r2', 'corrected_rerun_r1', 'pcso_weekly_2026_07_08',
}
run_ids = [r['run_id'] for r in RL]
chk('run ledger ids unique', len(run_ids), len(set(run_ids)))
chk('run ledger required ids', required_run_ids - set(run_ids), set())
chk('run/test ledger reconcile', sum(r['real_data_tests'] for r in RL), len(T))
import json as _j
BS=open('results/blind_eval_score.md').read()
chk('blind eval zero FP', 'FP=0' in BS and 'specificity 1.000' in BS, True)
print("EXTERNAL-REVIEW ADOPTIONS VERIFIED" if ok else "ADOPTION FAILURES")

# ---- batch67_r2 rerun checks ------------------------------------------------
RR = json.load(open('results/rerun_batch67.json'))
chk('r2 mmd joint null', RR['b6_mmd']['joint_verdict_null'], True)
chk('r2 mmd min_p', round(RR['b6_mmd']['min_p'], 3), 0.049, 5e-4)
chk('r2 spectra joint null', RR['b6_spectra']['joint_verdict_null_so_far'], True)
chk('r2 halves 6/55 corr', RR['b6_halves']['per_game']['Grand Lotto 6/55']['all']['corr'], 0.251)
chk('r2 halves 6/55 ex corr', RR['b6_halves']['per_game']['Grand Lotto 6/55']['ex_suspicious']['corr'], 0.154)
chk('r2 seasons 6/6 corrected', RR['b7_seasons']['n_corrected_rejections'], 6)
chk('r2 sunmoon median p', RR['b7_cca']['tests']['pressure_vs_sunmoon']['median_p'], 0.005)
chk('r2 kp median p', round(RR['b7_cca']['tests']['pressure_vs_kp']['median_p'], 2), 0.43, 5e-3)
chk('r2 gw status is G0', 'G0 EXPLORATORY' in RR['b7_gw']['status'], True)
print("BATCH67_R2 VERIFIED" if ok else "BATCH67_R2 FAILURES")

R8 = json.load(open('results/r8_admission.json'))
chk('r8 NOT admitted', R8['admission']['ADMITTED'], False)
chk('r8 negative passed', R8['negative_E1_independent_AR1']['passed'], True)
chk('r8 gate power', R8['positive_gate_sigma1.0']['power_at_alpha'], 0.58)
chk('r8 posthoc S1|S2', R8['benchmark_posthoc']['pairs']['S1|S2'], 0.69)
print("R8 ATTEMPT VERIFIED" if ok else "R8 FAILURES")
sys.exit(0 if ok else 1)
