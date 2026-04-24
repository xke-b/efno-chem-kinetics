# EFNO teacher-forced noise ablation: mild next-feature perturbations preserve the gains but do not materially change the picture

_Date: 2026-04-23_

## Why this was the next step

After the teacher-forced two-step EFNO branch beat the earlier EFNO baselines and overtook the seeded supervised MLP on rollout metrics, the next unresolved question was about **exposure-bias robustness**.

Teacher forcing uses true next-step inputs during training, but inference is still self-fed. So the next useful probe was:

> If the teacher-forced second-step input is mildly perturbed during training, do the gains disappear, or are they robust?

This is not a full scheduled-sampling solution, but it is a small, controlled step toward bridging teacher-forced and self-fed conditions.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added trainer param:
- `rollout_feature_noise_std`

Behavior:
- when rollout consistency is active, optional Gaussian noise is added to the normalized second-step input before the second forward pass

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_teacher_forced_noise_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_teacher_forced_noise_ablation/summary.json`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- teacher-forced two-step EFNO with:
  - `target_mode = "temperature_species"`
  - `species_data_space = "bct_delta"`
  - `temperature_loss_weight = 0.1`
  - `species_loss_weight = 4.0`
  - `rollout_consistency_weight = 0.1`
  - `rollout_consistency_mode = "teacher_forced"`

Cases:
1. `noise0p0`
2. `noise0p05`
3. `noise0p1`

## Aggregated results

### `noise0p0`
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`
- rollout element-mass MAE @1000: `5.78e-02`

### `noise0p05`
- one-step species MAE: `8.18e-05`
- one-step temperature MAE: `1.20e-01 K`
- one-step element-mass MAE: `1.54e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.14e+02 K`
- rollout element-mass MAE @1000: `5.84e-02`

### `noise0p1`
- one-step species MAE: `7.99e-05`
- one-step temperature MAE: `1.18e-01 K`
- one-step element-mass MAE: `1.49e-04`
- rollout species MAE @1000: `2.95e-02`
- rollout temperature MAE @1000: `7.12e+02 K`
- rollout element-mass MAE @1000: `5.77e-02`

## Main interpretation

### 1. The teacher-forced gains are robust to mild second-step input perturbation
The good news is that adding moderate noise did **not** collapse the teacher-forced branch back toward the bad self-fed result.

That means the teacher-forced improvement is not a vanishingly brittle artifact of perfectly clean next-step inputs.

### 2. Mild noise did not materially change the overall ranking
The differences across `0.0`, `0.05`, and `0.1` noise were small.

There was a slight improvement in one-step metrics and rollout species/element metrics at `0.1`, but rollout temperature MAE did not improve meaningfully.

So this looks more like **robustness confirmation** than a new breakthrough.

### 3. Exposure-bias mitigation remains unsolved, but the search is narrowed further
This result suggests:
- teacher-forced two-step supervision is robust enough to be a credible training signal
- simply injecting small Gaussian noise into teacher-forced second-step inputs is **not** the missing bridge to self-fed training

## Bottom line

The best current EFNO branch remains the teacher-forced two-step family, and its gains survive mild second-step input perturbations.

That is useful evidence, but it also says the next real structural step should be stronger than simple noisy teacher forcing—most likely a more explicit mixed teacher/self feeding strategy.
