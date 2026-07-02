# eq_eval_set_v1 — ground truth (SEALED)

| unit | truth | key params | expected |
|---|---|---|---|
| unit_01 | white_noise | {"sigma": 1.0} | FAILED_EQUATION_SEARCH or REFUSED_NULL_DETECTION |
| unit_02 | white_noise_scaled | {"sigma": 3.7} | FAILED_EQUATION_SEARCH or REFUSED_NULL_DETECTION |
| unit_03 | ar1 | {"phi": 0.85} | FAILED_EQUATION_SEARCH (AR/surrogate nulls must absorb) |
| unit_04 | random_walk | {"sigma": 1.0} | FAILED_EQUATION_SEARCH (1/f^2 spectrum is the classic trap) |
| unit_05 | logistic_map_r3.97 | {"r": 3.97, "obs_noise": 0.1} | FAILED_EQUATION_SEARCH for the harmonic menu (deterministic but non-harmonic; overclaim test) |
| unit_06 | single_harmonic | {"period_d": 27.3, "amp": 1.2, "sigma": 1.0, "detectability_ratio": 8.01} | CANDIDATE_EQUATION, period within profile CI |
| unit_07 | single_harmonic | {"period_d": 14.9, "amp": 0.45, "sigma": 1.0, "detectability_ratio": 1.13} | borderline: either CANDIDATE (period correct) or FAILED labeled below-power |
| unit_08 | single_harmonic | {"period_d": 33.1, "amp": 0.12, "sigma": 1.0, "detectability_ratio": 0.08} | borderline: either CANDIDATE (period correct) or FAILED labeled below-power |
| unit_09 | two_close_harmonics | {"periods_d": [27.3, 24.9], "amps": [1.0, 0.8], "sigma": 1.0, "rayleigh_separation": 1.41} | CANDIDATE with 2 lines (joint refinement) OR 1 line with residual scan firing on the second — merged single line with a CI excluding both truths = the v1 30.64d failure |
| unit_10 | harmonic_plus_trend | {"period_d": 21.7, "amp": 0.9, "trend_per_day": 0.004, "sigma": 1.0} | CANDIDATE with trend term (or detrended fit); period correct |
| unit_11 | harmonic_plus_hidden_line | {"main_period_d": 29.5, "main_amp": 1.1, "hidden_period_d": 9.3, "hidden_amp": 0.5, "sigma": 1.0} | CANDIDATE/PARTIAL_MODEL: main line recovered; residual scan (Q-5, no whitelist) must fire near 9.3 d; with 9.3 d whitelisted the scan must go silent |
| unit_12 | era_bounded_harmonic | {"period_d": 18.4, "amp": 1.0, "active_rows": [0, 199], "sigma": 1.0} | NOT a clean CANDIDATE: stationarity/era checks (S-7, R2-cusum class) must flag; acceptable outcomes are ERA_BOUNDED flag or PARTIAL with segment attribution |
