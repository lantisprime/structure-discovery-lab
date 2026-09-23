# RESULTS — Exploratory MLX backend, fix round 1 (2026-09-23)

Status: exploratory, not registered. All requested review findings are ACCEPT. Four ported models: tilt_high31, tilt_linear, pair_parity, cp_nest. Uniform is an analytic reference (no GPU computation).

Source JSON: `results/exploratory/pcso_mlx_null_calibration_2026-09-23.json`; SHA-256 `d2768b8bd8e2bcc13800cd62c63965b8ec8a9fe6d8b011fe7ef4e6a81d428bc5`.
Generator: `tools/pcso_mlx_report.py`; SHA-256 `32755a451672fd6181fd6c378e671ed059e6a9b4a886468c1bd94f4035c5974a`. The JSON includes every source-JSON and script hash.

Base: `86ba523408ca246266fdeb8a09d64f712711a7ca`. The registered CPU source is unchanged. The new base has 999 draws; this review pins the requested 994-draw prefix through 2026-09-20, with schedule digest and pool counts in each artifact.

```text
$ git diff origin/master -- src/pcso_model_registry.py
```
(stdout empty; exit 0.)

Primary validation uses the same cp_streams draws and float32-quantised Gaussians on the unchanged CPU models and MLX; the CPU casts those exact values back to float64. The measured residual excludes Gaussian input quantisation but includes all float32 arithmetic and device kernels. Host schedule constants and evidence/SR accumulation remain float64.

Full-horizon matched checks use 16 streams per configuration on both MLX devices. Delta means MLX minus registered CPU. OLS fits cumulative delta per stream against t; the reported bound is max(|intercept| + 994|slope|), required <1e-4 nats; max per-draw error <=1e-5 and sup error <=1e-3.

| Model / M | Device | max absolute delta le_t | Mean OLS slope | Max absolute slope | t=994 bound | Max sup error |
|---|---|---:|---:|---:|---:|---:|
| tilt_high31_m32 | gpu | 1.16841e-06 | -1.34973e-09 | 7.9186e-09 | 8.63086e-06 | 5.75225e-06 |
| tilt_high31_m32 | cpu | 2.14547e-07 | -1.70273e-10 | 1.87633e-09 | 2.29807e-06 | 9.31943e-07 |
| tilt_linear_m32 | gpu | 9.38534e-07 | -8.60938e-10 | 1.77595e-09 | 2.66589e-06 | 3.7746e-06 |
| tilt_linear_m32 | cpu | 1.60366e-07 | -2.78362e-10 | 5.76631e-10 | 6.41995e-07 | 9.76431e-07 |
| pair_parity_m32 | gpu | 9.93783e-07 | 6.14637e-10 | 8.68769e-09 | 1.23107e-05 | 5.31256e-06 |
| pair_parity_m32 | cpu | 2.65926e-07 | 1.14407e-10 | 1.00792e-09 | 1.38212e-06 | 3.16487e-07 |
| cp_nest_m32 | gpu | 2.91105e-06 | 1.86e-08 | 4.66509e-08 | 5.03478e-05 | 3.50114e-05 |
| cp_nest_m32 | cpu | 5.386e-07 | -2.25727e-09 | 9.53519e-09 | 1.1271e-05 | 7.65633e-06 |
| cp_nest_m128 | gpu | 2.86088e-06 | 1.87444e-08 | 4.84899e-08 | 5.26195e-05 | 3.5941e-05 |
| cp_nest_m128 | cpu | 5.02463e-07 | -2.25634e-09 | 1.04757e-08 | 1.23117e-05 | 8.31522e-06 |

Primary paired distribution: 400 full-horizon streams per configuration, GPU versus registered CPU. Bounds (mean absolute / q99 absolute / max absolute): sup and final log-evidence = 1e-4 / 3e-4 / 1e-3 nats; v_T(0) = 1e-5 / 3e-5 / 1e-4. Signed means and all stream values are also in JSON.

| Model / M | Statistic | Mean absolute delta | q99 absolute delta | Max absolute delta |
|---|---|---:|---:|---:|
| tilt_high31_m32 | sup | 1.28988e-06 | 4.98098e-06 | 7.41281e-06 |
| tilt_high31_m32 | final_log_e | 1.45433e-06 | 7.664e-06 | 1.04389e-05 |
| tilt_linear_m32 | sup | 1.21078e-06 | 3.98673e-06 | 5.84561e-06 |
| tilt_linear_m32 | final_log_e | 1.20749e-06 | 6.27781e-06 | 1.48481e-05 |
| pair_parity_m32 | sup | 1.62133e-06 | 1.03026e-05 | 1.59385e-05 |
| pair_parity_m32 | final_log_e | 3.59267e-06 | 1.59786e-05 | 2.54162e-05 |
| cp_nest_m32 | sup | 7.73112e-06 | 3.21833e-05 | 3.89762e-05 |
| cp_nest_m32 | final_log_e | 1.69048e-05 | 3.66343e-05 | 5.11158e-05 |
| cp_nest_m32 | v0_final | 5.41396e-06 | 1.12331e-05 | 1.31929e-05 |
| cp_nest_m128 | sup | 7.68915e-06 | 3.29177e-05 | 4.17333e-05 |
| cp_nest_m128 | final_log_e | 1.69013e-05 | 3.60181e-05 | 4.94822e-05 |
| cp_nest_m128 | v0_final | 5.4362e-06 | 1.11247e-05 | 1.2835e-05 |

Final level-zero weight distributions (400 streams):

| Model / M | Backend | Mean | q50 | q90 | q99 | Fraction >=0.9 |
|---|---|---:|---:|---:|---:|---:|
| cp_nest_m32 | cpu | 0.47497606 | 0.5101844 | 0.60995818 | 0.6479875 | 0 |
| cp_nest_m32 | gpu | 0.47497064 | 0.51017866 | 0.60995482 | 0.64798402 | 0 |
| cp_nest_m128 | cpu | 0.47479413 | 0.50981927 | 0.60920344 | 0.6482632 | 0 |
| cp_nest_m128 | gpu | 0.47478869 | 0.50981528 | 0.60919945 | 0.64826019 | 0 |

Device comparison on identical matched inputs:

| Model / M | max per-draw GPU minus MLX CPU | max final log-evidence difference |
|---|---:|---:|
| tilt_high31_m32 | 1.19209e-06 | 6.40235e-06 |
| tilt_linear_m32 | 9.23872e-07 | 2.15957e-06 |
| pair_parity_m32 | 1.01328e-06 | 9.46778e-06 |
| cp_nest_m32 | 2.92063e-06 | 3.86813e-05 |
| cp_nest_m128 | 2.80142e-06 | 3.91878e-05 |

The residual is not purely device-independent float32 rounding: the CPU and GPU kernels give different errors. Both devices must satisfy the same empirical bounds. CP-NEST uses a normalized ESP recurrence to avoid the rounded C(55,6) denominator and large-integer cancellation.

Gross screens (M=32, 400 independent CPU versus 10000 MLX streams): KS at 1e-5-nat resolution for sup and SR, plus Fisher on crossings; the verdict includes all three p-values. Values below 0.10 receive a warning; below 0.05 indicate a discrepancy.

| Model | sup KS p | SR KS p | Fisher p | CPU / MLX crossings | Verdict |
|---|---:|---:|---:|---|---|
| uniform | 1 | 1 | 1 | 0 / 0 | no gross discrepancy detected |
| tilt_high31 | 0.947048 | 0.994962 | 0.452694 | 3 / 49 | no gross discrepancy detected |
| tilt_linear | 0.472765 | 0.52513 | 0.520822 | 1 / 65 | no gross discrepancy detected |
| pair_parity | 0.0961998 | 0.145007 | 1 | 1 / 28 | warning: marginal screen |
| cp_nest | 0.170019 | 0.212023 | 0.627583 | 0 / 29 | no gross discrepancy detected |

KS critical D is approximately 0.0692499; a conservative sufficient CDF separation for 80% power is 0.142682 (DKW union bound). Fisher's approximate 80%-power minimum detectable rate difference is 0.0179769, assuming CPU rate 0.005; this is a normal approximation, and discrete exact power can differ substantially with only two expected CPU events. These screens cannot establish arithmetic equivalence.

Unrounded KS distinguishes disjoint point masses separated by host roundoff (~1e-15 nats); the old 5e-324 p-value measured that tie, not a model discrepancy. Raw point-mass KS removed; rounded SR is included in verdict.

The 400-stream and 10000-stream benchmark artifacts are disjoint samples (different generator seeds); neither is a prefix of the other.

POWER: theta1=0.05, M=128, 200 matched CPU/MLX streams (seed 20260927) plus 2000 independent MLX streams (seed 20260928), horizon 994, prior initialisation (not registered-window conditioning). Non-crossers are right-censored at 994; the censored median uses the full cohort, and an unreached median means >994 draws.

| Model | Backend | Streams | Crossed | Fraction | Censored median | Horizon |
|---|---|---:|---:|---:|---|---:|
| cp_nest | CPU | 200 | 108 | 0.54 | 945 | 994 |
| cp_nest | MLX GPU (matched) | 200 | 108 | 0.54 | 945 | 994 |
| cp_nest | MLX GPU (independent) | 2000 | 1060 | 0.53 | 952 | 994 |
| tilt_linear | CPU | 200 | 124 | 0.62 | 805 | 994 |
| tilt_linear | MLX GPU (matched) | 200 | 124 | 0.62 | 805 | 994 |
| tilt_linear | MLX GPU (independent) | 2000 | 1226 | 0.613 | 832 | 994 |

POWER paired errors:

| Model | Statistic | Mean absolute | q99 absolute | Max absolute |
|---|---|---:|---:|---:|
| cp_nest | sup | 2.82133e-05 | 5.82971e-05 | 6.22678e-05 |
| cp_nest | final_log_e | 3.13347e-05 | 6.03911e-05 | 6.2063e-05 |
| cp_nest | v0_final | 9.90686e-07 | 6.94056e-06 | 8.49846e-06 |
| tilt_linear | sup | 2.7692e-06 | 1.30207e-05 | 2.61212e-05 |
| tilt_linear | final_log_e | 2.81894e-06 | 1.52633e-05 | 2.73378e-05 |

Timing in seconds (M5; CPU uses eight workers; includes sampling, worker startup/compilation and accumulation, excludes imports/serialization):

| Model | CPU 400 | MLX 400 | MLX 10000 |
|---|---:|---:|---:|
| uniform | 8.300 | 0.376 | 4.761 |
| tilt_high31 | 21.087 | 0.661 | 8.809 |
| tilt_linear | 21.021 | 0.658 | 8.772 |
| pair_parity | 6.162 | 0.634 | 8.537 |
| cp_nest | 138.782 | 2.004 | 37.208 |

Verification: local 276 passed, 20 skipped in 364.58s (0:06:04); M5 26 passed in 49.27s.

Every M5 command, including rsync, runs under the repository Python supervisor with a <=300-second deadline and process-group cleanup. Cleanup evidence is in `results/exploratory/pcso_mlx_m5_leftovers_2026-09-23.log`.

Reproduction (each M5 job is separately bounded; --check regenerates aggregate/narrative bytes from saved JSON, while raw rerun timings naturally vary):

```sh
python tools/pcso_mlx_remote.py sync
python tools/pcso_mlx_bench_all.py matched
python tools/pcso_mlx_bench_all.py paired
python tools/pcso_mlx_bench_all.py power
python tools/pcso_mlx_bench_all.py bench
python tools/pcso_mlx_bench_all.py tests
python tools/pcso_mlx_remote.py pull
python -m pytest tests/ -q -p no:cacheprovider > results/exploratory/pcso_mlx_tests_local_2026-09-23.log
python src/pcso_mlx_benchmark.py --model cp_nest --backend cpu --streams 2 --workers 1 --max-draws 4 --out results/exploratory/pcso_mlx_cpu_without_mlx.json
python tools/pcso_mlx_remote.py leftovers > results/exploratory/pcso_mlx_m5_leftovers_2026-09-23.log
python tools/pcso_mlx_report.py
python tools/pcso_mlx_report.py --check
```

snapshot_commitment.py hashes docs/RESULTS_*; the picker narrative appears in its snapshot-format blocks at ledger lines 1287/1349. results/ is excluded. Use the existing snapshot tool, never a hand-edited row.

Sensitivity grid: **not run**; the lead will pre-declare it separately. Dirichlet and ensemble remain CPU-only.

Limitations: Float32 residual is device-dependent; equivalence bounds are empirical on the specified inputs, not a proof for all inputs. Independent review CLI was unavailable in the prior round: pi --help reported EPERM creating its settings lock. It was not retried; this continuation received self-review only. No alternate permissions or credentials attempted.

Script hashes:

| Path | SHA-256 |
|---|---|
| `src/pcso_mlx_sim.py` | `d3d38e5d16f78647ec75803bfaa709556f9b6546f29092ba826457aa8694535e` |
| `src/pcso_mlx_benchmark.py` | `0d1f9ac01d517dcbce3a14cbb0d9ae5954184a0c0115071d4810b305500ec765` |
| `src/pcso_model_registry.py` | `8bab01838bbe18667cb5de387e23fff3d22192150b761166c92bd7d4d2d785ea` |
| `tests/test_pcso_mlx_sim.py` | `38169905641016067dd32c05f6e5040646fa1667429455fcf681242cbbea6db1` |
| `tools/pcso_mlx_validate.py` | `f47465d737bca104999e797f33eb85ad49ae8d677b9c495b349af3c6df02163d` |
| `tools/pcso_mlx_bench_all.py` | `e5de05d5c973025a56e57c0bdab2183aaf28c3c34ca0306a42dcef3fb8b945b6` |
| `tools/pcso_mlx_remote.py` | `70781087264bd5ba5c3e980bf2054502b67acf7cc551b140da97940f6fb642aa` |
| `tools/pcso_mlx_report.py` | `32755a451672fd6181fd6c378e671ed059e6a9b4a886468c1bd94f4035c5974a` |
| `tools/snapshot_commitment.py` | `ec3181c79ec0c307b699f585216484081eeb637463975a6cc9670f0b19fa139f` |

Source JSON hashes:

| Path | SHA-256 |
|---|---|
| `results/exploratory/pcso_mlx_matched_tilt_high31_m32.json` | `6dc0c34d2b97ea070402e01e17d548d1356ed55f91acddec0b6a858f9e795ca4` |
| `results/exploratory/pcso_mlx_paired_tilt_high31_m32.json` | `efc1eb94ffd3da714e8a9a2437a18d86c9da102da2b014dd0a24e20175a2dc99` |
| `results/exploratory/pcso_mlx_matched_tilt_linear_m32.json` | `73f920685b890bb5a28152dcb78695b8c8c55ec3edc763e608099fdb14aecd25` |
| `results/exploratory/pcso_mlx_paired_tilt_linear_m32.json` | `37f816862fd0f43980fd446d62f4fdf55d6cc7e22bd1bf7c6cccab779a0ec125` |
| `results/exploratory/pcso_mlx_matched_pair_parity_m32.json` | `1bec1cef6c238384129098aa9c6f5a980551a828aff74c98d83061bf4ff0a4da` |
| `results/exploratory/pcso_mlx_paired_pair_parity_m32.json` | `a2887709840cf81bc709d4097a1b1cf8ed00241eea7720137eea9de61bd5efdf` |
| `results/exploratory/pcso_mlx_matched_cp_nest_m32.json` | `6a053a700758b898975fd1a6b569f511df3f9031bb6890b05b89502942c45a18` |
| `results/exploratory/pcso_mlx_paired_cp_nest_m32.json` | `d5698fc0a93e7fd216351a9aa10244820266f2cbc4103cc7ff5301aae9817e07` |
| `results/exploratory/pcso_mlx_matched_cp_nest_m128.json` | `07de1189994b173c53996450487c6e62c5225568ccd5af98b1a5b4aae702cb43` |
| `results/exploratory/pcso_mlx_paired_cp_nest_m128.json` | `2aeb6cbf163b96afe05c6cbbf70671d666d876a2f346b8132308faff615f0207` |
| `results/exploratory/pcso_mlx_power_cp_nest_m128.json` | `de8c81747fae9643e9df72c748b3a8abbb333dcb6673d85f4b05a233d27321dc` |
| `results/exploratory/pcso_mlx_power_cp_nest_mlx_2000.json` | `715bc12408391298f7de39753e0aa7c9a221411a16ec57936140d55a16c0edff` |
| `results/exploratory/pcso_mlx_power_tilt_linear_m128.json` | `79e6faa261de12444e04fe1284910f3468e3f5f0c3cb023e813d2c4144512596` |
| `results/exploratory/pcso_mlx_power_tilt_linear_mlx_2000.json` | `2eb04e2c50e838f2838c3082ab8c165191eb47f0eae984d74d6bfe6f1b7097b9` |
| `results/exploratory/pcso_mlx_bench_uniform_cpu_400.json` | `17459d21ac238fb2a604605ccd87ef9378980a52d8f5d961e3c505e13118468d` |
| `results/exploratory/pcso_mlx_bench_uniform_mlx_400.json` | `f3ddf6a63a2656c86a5a9c7caae195372081ed9efaa7e49c22f0f35fa5d9d4b5` |
| `results/exploratory/pcso_mlx_bench_uniform_mlx_10000.json` | `a676d76f7bcb48a6c53c50597255e0e94aa96fb689f2f9e793cd364002b6a37f` |
| `results/exploratory/pcso_mlx_bench_tilt_high31_cpu_400.json` | `41b7ec90ce555dc3477107083077a88af3b9c3af4c4895d744bdeff4c6f23188` |
| `results/exploratory/pcso_mlx_bench_tilt_high31_mlx_400.json` | `315ac0e68bca1ebbc3d5b8e2330f52bc10acb839234b0ff2307d7abe9a1a9508` |
| `results/exploratory/pcso_mlx_bench_tilt_high31_mlx_10000.json` | `51e38d162212be936b60f1bf9ba5762edd5776d17cd72d9d1f424729e235a06f` |
| `results/exploratory/pcso_mlx_bench_tilt_linear_cpu_400.json` | `48b3c5c2e75ac95b63b016aa9f83bf040d919847cc6e37e88a043cc26d17786e` |
| `results/exploratory/pcso_mlx_bench_tilt_linear_mlx_400.json` | `66bc5ad57df823bbeee79760ee6666589e86b4f4226fc9c4cfcc868fb6929105` |
| `results/exploratory/pcso_mlx_bench_tilt_linear_mlx_10000.json` | `09a0154b83a9f8f98bc9ecb23b3f5560165b721e4244acdf55c6b02d04898afb` |
| `results/exploratory/pcso_mlx_bench_pair_parity_cpu_400.json` | `1045fcbe79fbc41178b5a75598d4a5bc0eb04d9181a0d8f8afcdce31a21eb96d` |
| `results/exploratory/pcso_mlx_bench_pair_parity_mlx_400.json` | `6f54a827a8e86e018def3aafef41811fecf0b97c3def74794bf5705f936c2cd5` |
| `results/exploratory/pcso_mlx_bench_pair_parity_mlx_10000.json` | `732141080a62de62e54eed4b2b388ce8172077e6832605f86ae26f337787553f` |
| `results/exploratory/pcso_mlx_bench_cp_nest_cpu_400.json` | `3a65d034a63ba29a3818e50cd6bb43f5e23466eb813967e713ce1a80ff8638d9` |
| `results/exploratory/pcso_mlx_bench_cp_nest_mlx_400.json` | `1aeff2e372337155afea7b7b9a42ac58e060fef90c763cbd45f224e6f190f49c` |
| `results/exploratory/pcso_mlx_bench_cp_nest_mlx_10000.json` | `0f3309f9a0748138addf2980c336a305e3c3cbee1675fff8e1ca2b3f6d16cf0c` |
| `results/exploratory/pcso_mlx_equivalence_2026-09-23.json` | `838cf2c2da2628172a47a3498a49bac33e9d44dc977b4b7a7adad45cc2ff87d1` |
| `results/exploratory/pcso_mlx_cpu_without_mlx.json` | `154afa4fef1b72c28b99a7af7cdda9dcc1a5afae15cf0ce93496c0f02ad42b4d` |
