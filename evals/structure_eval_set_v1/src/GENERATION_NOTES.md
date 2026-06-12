# Generation Notes

Evaluation set generated deterministically with NumPy default_rng seed `20260611`.

This folder intentionally contains the answer key, so do not include it when running a
blind lab evaluation. Use `structure_eval_set_v1_blind.zip` for blind runs.

High-level generators:

- Draw streams: 360 daily 6-of-60 draws per stream.
- Stream A: constrained-uniform.
- Stream B: first-half weighted marginal bias on two numbers.
- Stream C: exact-balanced per-number counts with elevated consecutive-overlap memory.
- Streams D/E: constrained draws whose sums depend on a shared bounded latent state.
- Sensor panel: four anonymized date-aligned channels, including a noisy latent proxy
  and a null channel.
- Series: periodic, periodic-related, iid noise, and regime/changepoint series.
- Clouds: noisy circle in 2D, nonlinear 5D embedding of same circle with row shuffle,
  and matched Gaussian blob.
- Graphs: two independent graphs from the same 4-block SBM and one density-matched ER
  control.
- Matrices: rank-3 plus noise and iid Gaussian, with fixed train/test entry masks.
