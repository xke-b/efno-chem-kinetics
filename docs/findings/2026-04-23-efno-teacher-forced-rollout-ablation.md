# EFNO teacher-forced two-step ablation: future supervision helps when self-fed rollout does not

_Date: 2026-04-23_

## Why this was the next step

The previous rollout-consistency experiment taught two things:

1. **self-fed two-step EFNO training was numerically fragile** in the current Box-Cox thermochemical path
2. even after numerical stabilization, that **self-fed** rollout loss hurt both one-step fit and long-horizon rollout metrics

That left an important unresolved question:

> Is multi-step supervision itself harmful, or was the damage coming specifically from feeding the model its own reconstructed next-step features during training?

To answer that, I ran the next most useful diagnostic: a **teacher-forced two-step loss**.

Instead of building second-step inputs from the model's own first-step predictions, this variant feeds the **true normalized next-step features from the training trajectory** into the second forward pass, while still supervising the next-step target.

That isolates the effect of extra future supervision from the effect of self-generated rollout inputs.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_training_preprocess.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added:
- `rollout_next_features` to `_prepare_training_tensors(...)`
- new EFNO trainer param:
  - `rollout_consistency_mode`
    - `"self"` (existing self-fed behavior)
    - `"teacher_forced"` (new diagnostic mode)

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_teacher_forced_rollout_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_teacher_forced_rollout_ablation/summary.json`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- `target_mode = "temperature_species"`
- `species_data_space = "bct_delta"`
- `lambda_elements = 0.0`
- `lambda_mass = 0.0`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`

Cases:
1. `baseline_tempw_0p1_speciesw_4p0`
2. `teacherforced_rollout0p01_tempw_0p1_speciesw_4p0`
3. `teacherforced_rollout0p1_tempw_0p1_speciesw_4p0`

## Aggregated results

### Baseline current best EFNO branch
- one-step species MAE: `1.12e-04`
- one-step temperature MAE: `1.43e-01 K`
- one-step element-mass MAE: `1.61e-04`
- rollout species MAE @1000: `9.90e-02`
- rollout temperature MAE @1000: `1.90e+03 K`

### Teacher-forced rollout weight = 0.01
- one-step species MAE: `1.05e-04`
- one-step temperature MAE: `1.36e-01 K`
- one-step element-mass MAE: `1.96e-04`
- rollout species MAE @1000: `6.03e-02`
- rollout temperature MAE @1000: `7.12e+02 K`

### Teacher-forced rollout weight = 0.1
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`

## Main interpretation

### 1. Multi-step supervision itself is **not** the problem
This is the main new conclusion.

The teacher-forced two-step loss improved both:
- one-step thermochemical accuracy
- long-horizon rollout behavior

So the earlier failure was **not** evidence that “future supervision hurts EFNO.”

### 2. The harmful part was the **self-fed next-feature reconstruction path**
The contrast is now very strong:
- self-fed rollout loss: catastrophic degradation
- teacher-forced rollout loss: substantial improvement

That points directly at the real bottleneck:
- the model benefits from being trained against future-step targets
- but the current self-generated Box-Cox/reconstruction path is too inaccurate or too distribution-shifting to use as the second-step input during training

### 3. This is the clearest structural improvement found so far on the EFNO branch
The `teacherforced_rollout0p1_tempw_0p1_speciesw_4p0` case beat the previous EFNO baseline on:
- one-step species MAE
- one-step temperature MAE
- rollout species MAE
- rollout temperature MAE

And it did so with a fairly simple change.

## Comparison to the earlier self-fed rollout result

The immediately previous self-fed rollout-consistency branch had:
- one-step species MAE: `3.39e-04`
- one-step temperature MAE: `1.80e-01 K`
- rollout species MAE @1000: `4.88e-01`
- rollout temperature MAE @1000: `8.40e+03 K`

So the diagnostic split is now sharp:
- **self-fed two-step loss**: bad
- **teacher-forced two-step loss**: good

That is highly informative.

## What this changes in the project understanding

Before this step, the working hypothesis was drifting toward:
- “maybe one-step EFNO is as good as this branch gets”
- “maybe multi-step training is inherently unhelpful here”

After this step, the evidence supports a more specific and more actionable view:
- **future-step supervision is useful**
- the real issue is **how second-step inputs are formed**, not whether future-step losses are present at all

## Practical next step implied by this result

The next best experiment is now much better defined:

1. treat teacher-forced two-step EFNO as the new strongest EFNO-style offline branch
2. compare it directly against the seeded supervised MLP reference under the same reporting protocol
3. if it holds up, investigate whether more careful exposure-bias mitigation can bridge the gap between teacher-forced training and self-fed autoregressive use
   - e.g. scheduled/self-mix strategies rather than all-or-nothing self-fed rollout construction

## Bottom line

This experiment materially improved understanding.

It showed that the previous rollout-consistency failure was **not** a dead end for multi-step EFNO training. Instead, it isolated the real problem to the **self-fed next-state feature construction**.

That is a much more useful diagnosis, and it produced a new best EFNO-style result in the process.
