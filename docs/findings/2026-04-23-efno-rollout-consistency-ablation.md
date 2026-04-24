# EFNO rollout-consistency ablation: naive two-step consistency was initially numerically unstable, and after stabilizing it, it still hurt performance badly

_Date: 2026-04-23_

## Why this was the next step

After conservation redesign, FNO-scaffold comparison, and seeded weight sweeps, the strongest remaining hypothesis was that the EFNO branch still suffers because it is trained too one-step-myopically for an autoregressive rollout task.

So the next concrete step was to test a simple **two-step rollout-consistency loss** on the current best EFNO MLP branch.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_training_preprocess.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

What was added:
- contiguous-pair detection in `_prepare_training_tensors(...)`
- `rollout_next_labels` and `rollout_mask`
- optional EFNO trainer parameter:
  - `rollout_consistency_weight`
- rollout-feature stabilization helpers:
  - feature clipping for second-step inputs
  - gradient clipping support
  - Box-Cox input floor before re-encoding predicted species for rollout features

## Important failed-attempt information

The first rollout-consistency implementation produced immediate `NaN` training.

That failure was informative:
- the second-step feature construction re-applied Box-Cox to predicted species that could hit exact zero
- with `lambda = 0.1`, the Box-Cox derivative near zero is extremely large
- that made the rollout-consistency path numerically unstable and blew model parameters to `NaN` after the first optimizer step

I then stabilized the path by:
1. flooring predicted species before Box-Cox in the rollout-feature builder
2. clipping normalized rollout features
3. adding gradient clipping support

This removed the `NaN` failure, but not the performance problem.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_rollout_consistency_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_rollout_consistency_ablation/summary.json`

Compared cases:
1. `baseline_tempw_0p1_speciesw_4p0`
2. `rollout0p1_tempw_0p1_speciesw_4p0`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- common EFNO-style settings:
  - `target_mode = "temperature_species"`
  - `species_data_space = "bct_delta"`
  - `lambda_elements = 0.0`
  - `lambda_mass = 0.0`

Rollout-consistency case additionally used:
- `rollout_consistency_weight = 0.1`
- `rollout_feature_clip = 10.0`
- `gradient_clip_norm = 1.0`

## Aggregated results

### Baseline current best EFNO branch
- one-step species MAE: `1.12e-04`
- one-step temperature MAE: `1.43e-01 K`
- one-step element-mass MAE: `1.61e-04`
- rollout species MAE @1000: `9.90e-02`
- rollout temperature MAE @1000: `1.90e+03 K`

### Two-step rollout-consistency branch
- one-step species MAE: `3.39e-04`
- one-step temperature MAE: `1.80e-01 K`
- one-step element-mass MAE: `6.86e-04`
- rollout species MAE @1000: `4.88e-01`
- rollout temperature MAE @1000: `8.40e+03 K`

## What this teaches us

### 1. The naive multi-step idea was not just unhelpful; it was initially numerically dangerous
That is worth recording explicitly.

The first failure exposed a real numerical issue in Box-Cox re-encoding of predicted species during multi-step training.

### 2. Stabilizing the numerics did not rescue the idea
After fixing the `NaN` problem, the rollout-consistency branch trained, but it was much worse than the one-step EFNO baseline on every important metric.

### 3. Simple two-step self-rollout pressure is currently the wrong structural change
At least in this direct form, rollout-consistency training does not close the gap to supervised. It damages one-step fit and makes rollout worse.

## Most useful conclusion

This is a strong negative result, but a productive one.

It says the next structural EFNO improvement is **not** a naive add-on two-step rollout loss over the current decode/re-encode contract.

That narrows the search substantially.

## Bottom line

The project now has direct evidence that:
1. naive rollout-consistency training can be numerically unstable in the current Box-Cox thermochemical pipeline
2. even after stabilizing that numerically, the simple two-step EFNO consistency loss hurts both one-step and rollout performance

So the strongest current EFNO-style offline branch remains the simpler one-step no-conservation BCT-delta MLP setting, and the next useful improvement should likely come from a different structural change than naive multi-step consistency.
