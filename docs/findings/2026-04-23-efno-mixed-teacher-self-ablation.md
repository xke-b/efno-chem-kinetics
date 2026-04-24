# EFNO mixed teacher/self two-step ablation: partial self-feeding quickly degrades the current best teacher-forced branch

_Date: 2026-04-23_

## Why this was the next step

The strongest current diagnosis is now:
- pure self-fed two-step training is harmful
- pure teacher-forced two-step training is strongly helpful
- mild noise on teacher-forced next-step inputs does not materially bridge that gap

That made the next most useful experiment straightforward:

> What happens if the second-step training input is an explicit mix of true next-step features and self-generated next-step features?

This is a direct exposure-bias probe. If the teacher-forced branch were robust enough to tolerate some self-fed content during training, that would be a plausible bridge toward inference conditions.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added trainer param:
- `rollout_self_mix_ratio`

Added rollout mode:
- `rollout_consistency_mode = "mixed_teacher_self"`

Behavior:
- build self-fed next-step normalized features from the model prediction
- linearly mix them with the true normalized next-step features
- use that mixed tensor for the second forward pass

Mix definition:
- `next_features = (1 - mix_ratio) * teacher_features + mix_ratio * self_features`

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_mixed_teacher_self_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_mixed_teacher_self_ablation/summary.json`

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
2. `mixed_teacher_self_ratio0p25`
3. `mixed_teacher_self_ratio0p5`

## Aggregated results

### Pure teacher-forced reference
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`
- rollout element-mass MAE @1000: `5.78e-02`

### Mixed teacher/self, ratio `0.25`
- one-step species MAE: `2.09e-04`
- one-step temperature MAE: `1.68e-01 K`
- one-step element-mass MAE: `4.01e-04`
- rollout species MAE @1000: `2.34e-01`
- rollout temperature MAE @1000: `2.15e+03 K`
- rollout element-mass MAE @1000: substantially worse than teacher-forced (see artifact summary)

### Mixed teacher/self, ratio `0.5`
- one-step species MAE: `2.31e-04`
- one-step temperature MAE: `1.69e-01 K`
- one-step element-mass MAE: `4.70e-04`
- rollout species MAE @1000: `2.23e-01`
- rollout temperature MAE @1000: `2.12e+04 K`
- rollout element-mass MAE @1000: `4.83e-01`

## Main interpretation

### 1. The current teacher-forced EFNO branch is not yet robust to partial self-feeding
This is the main result.

Even introducing `25%` self-fed content into the second-step input caused a large degradation relative to pure teacher forcing.

At `50%`, the branch became much worse and extremely unstable across seeds.

### 2. Exposure bias is real and strong in the current thermochemical reconstruction path
This result reinforces the earlier diagnosis:
- future-step supervision is useful
- but the self-generated next-step feature path remains poor enough to poison training quickly once it is mixed in nontrivially

### 3. The problem is not solved by simple convex mixing
This is useful negative evidence.

A naive teacher/self interpolation is not the missing bridge. In this form, it gives up most of the teacher-forced gains while still inheriting self-fed instability.

## What this updates

Before this step, one plausible story was:
- perhaps a modest amount of self-fed exposure during training will preserve the teacher-forced gains while reducing mismatch

After this step, that story looks too optimistic for the current implementation.

The evidence now says:
- the self-fed feature-construction path is poor enough that even partial mixing damages the strong teacher-forced branch

## Bottom line

This was a useful failure.

The experiment did **not** find a simple bridge from teacher-forced training to self-fed robustness. Instead, it sharpened the diagnosis:
- the central bottleneck remains the quality of self-generated second-step features, not the absence of multi-step supervision

So the next structural change should probably be more selective or state-aware than a global fixed-ratio teacher/self blend.
