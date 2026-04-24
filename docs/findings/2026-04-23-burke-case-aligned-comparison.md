# DeepFlame H2 Burke case-aligned offline comparison: the corrected best EFNO branch transfers strongly to the case mechanism and time step

_Date: 2026-04-23_

## Why this was the next step

After fixing the EFNO decode contract and re-establishing the best H2 offline branch on the 7-species/16-reaction benchmark, the most useful next move was to push one layer closer to coupled use.

The simplest meaningful bridge was not full CFD coupling yet, but a **mechanism/time-step-aligned offline benchmark** for the target DeepFlame H2 case.

That case uses:
- mechanism: `Burke2012_s9r23.yaml`
- inference time step: `1e-6 s`

So the next question was:

> Does the corrected best EFNO branch still beat a supervised MLP baseline when the offline benchmark is aligned to the DeepFlame H2 case mechanism and time step?

## Experiment

Script:
- `/root/workspace/scripts/run_h2_burke_case_aligned_comparison.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_burke_case_aligned_comparison/summary.json`

Generated dataset:
- `/root/workspace/data/h2_burke_case_aligned.npy`
- `/root/workspace/data/h2_burke_case_aligned.json`

Holdout split:
- `/root/workspace/data/h2_burke_case_aligned_train.npy`
- `/root/workspace/data/h2_burke_case_aligned_train.json`
- `/root/workspace/data/h2_burke_case_aligned_test.npy`
- `/root/workspace/data/h2_burke_case_aligned_test.json`

Dataset setup:
- mechanism: `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/Burke2012_s9r23.yaml`
- species: `9`
- reactions: `23`
- reactor: constant-pressure autoignition
- `dt = 1e-6 s`
- `n_init = 12`
- `steps = 400`
- 75/25 trajectory holdout split

Compared models:
1. `supervised_mlp`
2. `corrected_self_rollout_predmainbct`

The EFNO branch used the current best corrected settings:
- `species_decode_mode = "bct_state_addition"`
- `rollout_consistency_mode = "self"`
- `rollout_consistency_weight = 0.1`
- `rollout_species_feature_mode = "predicted_main_bct"`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`

## Important note on artifact naming

The summary keys still use names like `rollout_species_mae_h1000` because they reuse the existing experiment summarizer convention.

For this Burke-aligned benchmark, the actual trajectory length is `400` rollout steps.
So those keys should be read as **last-horizon rollout metrics**, not literal 1000-step metrics.

## Aggregated results

### Supervised MLP
- one-step species MAE: `1.470e-04`
- one-step temperature MAE: `1.495 K`
- one-step element-mass MAE: `2.274e-04`
- last-horizon rollout species MAE: `5.025e-01`
- last-horizon rollout temperature MAE: `2.070e+05 K`
- last-horizon rollout element-mass MAE: `1.437`

### Corrected self-rollout EFNO + predicted-main-BCT
- one-step species MAE: `5.124e-04`
- one-step temperature MAE: `1.039 K`
- one-step element-mass MAE: `1.371e-03`
- last-horizon rollout species MAE: `2.085e-02`
- last-horizon rollout temperature MAE: `9.143e+02 K`
- last-horizon rollout element-mass MAE: `3.179e-02`

## Main interpretation

### 1. The corrected best EFNO branch transfers strongly to the DeepFlame H2 mechanism/time-step setting
Even on this new 9-species/23-reaction Burke benchmark with a larger chemistry step size, the corrected rollout-aware EFNO branch remains dramatically better than the supervised MLP on long-horizon behavior.

Approximate rollout improvements of EFNO over supervised on the final horizon:
- species MAE: about `24x` lower
- temperature MAE: about `226x` lower
- element-mass MAE: about `45x` lower

### 2. The same tradeoff pattern persists under case alignment
The EFNO branch still gives up one-step species/element accuracy:
- worse one-step species MAE
- worse one-step element-mass MAE

But it is better on one-step temperature MAE and vastly better on rollout stability and physical consistency.

That is the same qualitative pattern seen on the earlier 7-species benchmark, which increases confidence that the corrected EFNO behavior is not a one-benchmark accident.

### 3. This is the first mechanism/time-step-aligned bridge toward DeepFlame H2 coupling
This is not CFD coupling yet, but it is materially closer to the target use case than the earlier ES80 H2 reproduction benchmark.

It suggests that the corrected best EFNO branch is a credible candidate for the next transition step toward the DeepFlame H2 case.

## Bottom line

The corrected best EFNO branch survives transfer to a benchmark aligned with the target DeepFlame H2 case mechanism and inference time step.

That is strong evidence that the recent decode fix and rollout-aware training improvements are relevant for downstream coupled-usefulness work, not only for the original 7-species paper-style H2 benchmark.
