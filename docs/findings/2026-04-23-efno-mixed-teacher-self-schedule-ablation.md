# EFNO scheduled mixed teacher/self ablation: gradual self-exposure is less damaging than fixed mixing, but still worse than pure teacher forcing

_Date: 2026-04-23_

## Why this was the next step

The fixed-ratio mixed teacher/self experiment showed that simple convex blending quickly damaged the strong teacher-forced EFNO branch.

That still left one reasonable hypothesis alive:

> Maybe the problem is not self-exposure itself, but introducing it too abruptly.

So the next concrete step was to test a small curriculum:
- start from pure teacher forcing
- linearly ramp the self-mix ratio upward over epochs

This is the minimal scheduled-sampling-style variant that could still preserve the teacher-forced gains while exposing the model gradually to its own second-step inputs.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added:
- `rollout_self_mix_schedule`
  - `"constant"`
  - `"linear_warmup"`

Behavior:
- for `linear_warmup`, the self-mix ratio starts at `0` and ramps linearly to the configured final `rollout_self_mix_ratio` by the last epoch

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_mixed_teacher_self_schedule_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_mixed_teacher_self_schedule_ablation/summary.json`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- `target_mode = "temperature_species"`
- `species_data_space = "bct_delta"`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`
- `lambda_elements = 0.0`
- `lambda_mass = 0.0`
- `rollout_consistency_weight = 0.1`

Cases:
1. `teacherforced_rollout0p1`
2. `mixed_teacher_self_ratio0p25_linearwarmup`
3. `mixed_teacher_self_ratio0p5_linearwarmup`

## Aggregated results

### Pure teacher-forced reference
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`
- rollout element-mass MAE @1000: `5.78e-02`

### Linear warmup to self-mix ratio `0.25`
- one-step species MAE: `2.16e-04`
- one-step temperature MAE: `1.46e-01 K`
- one-step element-mass MAE: `4.11e-04`
- rollout species MAE @1000: `6.51e-02`
- rollout temperature MAE @1000: `9.77e+02 K`
- rollout element-mass MAE @1000: improved over the fixed-ratio `0.25` case, but still much worse than pure teacher forcing

### Linear warmup to self-mix ratio `0.5`
- one-step species MAE: `3.54e-04`
- one-step temperature MAE: `1.64e-01 K`
- one-step element-mass MAE: `6.21e-04`
- rollout species MAE @1000: `2.97e-01`
- rollout temperature MAE @1000: `4.49e+04 K`
- rollout element-mass MAE @1000: `5.61e-01`

## Main interpretation

### 1. Gradual self-exposure helps relative to fixed mixing at low ratio
This is the main new positive result.

Compared with fixed-ratio `0.25` mixing, the linear-warmup `0.25` version is much better, especially on rollout:
- rollout species MAE improves from roughly `2.34e-01` to `6.51e-02`
- rollout temperature MAE improves from roughly `2.15e+03 K` to `9.77e+02 K`

So abrupt self-mixing was indeed part of the problem.

### 2. But pure teacher forcing still remains clearly best
Even the improved scheduled `0.25` branch is still worse than pure teacher forcing on all key metrics.

So a simple linear curriculum softens the damage, but does not produce a better bridge than staying teacher-forced.

### 3. Higher final self-mix remains destructive
At `0.5` final self-mix, even with warmup, the branch becomes badly unstable again.

That reinforces the earlier conclusion that the current self-generated second-step features are still not good enough to support substantial self-feeding during training.

## What this changes in understanding

This experiment gives a more precise view than before:
- fixed-ratio mixing was too harsh
- gradual introduction is less harmful
- but the current self-fed feature path is still weak enough that the best practical branch remains pure teacher forcing

So the next useful search should move away from blunt global schedules and toward more selective strategies, such as:
- state-dependent gating
- confidence/error-triggered self exposure
- improving the self-generated second-step feature representation itself

## Bottom line

This was a productive partial-negative result.

A linear warmup schedule is better than fixed mixing, which is useful evidence. But it still does not beat pure teacher forcing, and high self-mix remains unstable.

So the current best EFNO branch is still the teacher-forced two-step setting, and the self-generated second-step feature path remains the central bottleneck.
