# EFNO self-rollout species-block decomposition: the directly predicted main-species channels carry most of the self-fed damage, but full recovery still requires fixing the whole species block

_Date: 2026-04-23_

## Why this was the next step

The previous oracle-species ablation showed that replacing the **entire** self-generated species second-step feature block with the teacher-forced block makes the self-rollout branch collapse almost exactly to teacher-forced performance.

That localized the failure to the species block, but it still left one useful mechanistic question open:

> Within that bad species block, is the dominant problem mostly the closure-reconstructed final species channel, or the directly predicted main-species channels, or both?

We already knew that:
- last-species-only replacement did **not** rescue self-fed training
- full-species replacement **did** rescue it

So the missing decomposition was to test an intermediate oracle:
- replace only the **directly predicted main-species** feature channels
- keep the final closure species channel self-generated

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added rollout species-feature mode:
- `"teacher_forced_main_only"`

Behavior in self-rollout mode:
- build self-generated second-step features as usual
- overwrite only `[:, 2:-1]` with teacher-forced species features
- leave the last species channel self-generated unless separately overridden

This is still an oracle diagnostic, not a deployable method.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_species_block_decomposition.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_species_block_decomposition/summary.json`

Cases:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_oracle_last_species`
4. `self_rollout0p1_oracle_main_species_only`
5. `self_rollout0p1_oracle_species`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds `0,1,2`
- `target_mode = "temperature_species"`
- `species_data_space = "bct_delta"`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`
- `lambda_elements = 0.0`
- `lambda_mass = 0.0`
- `rollout_consistency_weight = 0.1`

## Aggregated results

### Teacher-forced reference
- one-step species MAE: `8.253e-05`
- one-step temperature MAE: `1.210e-01 K`
- one-step element-mass MAE: `1.556e-04`
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`
- rollout element-mass MAE @1000: `5.777e-02`

### Pure self-rollout
- one-step species MAE: `3.392e-04`
- one-step temperature MAE: `1.802e-01 K`
- one-step element-mass MAE: `6.861e-04`
- rollout species MAE @1000: `4.881e-01`
- rollout temperature MAE @1000: `8.403e+03 K`
- rollout element-mass MAE @1000: `1.050e+00`

### Oracle last species only
- one-step species MAE: `2.971e-04`
- one-step temperature MAE: `1.848e-01 K`
- one-step element-mass MAE: `6.259e-04`
- rollout species MAE @1000: `5.294e-01`
- rollout temperature MAE @1000: `7.364e+03 K`
- rollout element-mass MAE @1000: `1.172e+00`

### Oracle main species only
- one-step species MAE: `1.639e-04`
- one-step temperature MAE: `1.521e-01 K`
- one-step element-mass MAE: `3.009e-04`
- rollout species MAE @1000: `2.080e-01`
- rollout temperature MAE @1000: `2.073e+03 K`
- rollout element-mass MAE @1000: `4.760e-01`

### Oracle full species block
- one-step species MAE: `8.251e-05`
- one-step temperature MAE: `1.211e-01 K`
- one-step element-mass MAE: `1.555e-04`
- rollout species MAE @1000: `2.970e-02`
- rollout temperature MAE @1000: `7.044e+02 K`
- rollout element-mass MAE @1000: `5.776e-02`

## Main interpretation

### 1. The directly predicted main-species channels carry most of the self-fed damage
Replacing only the main-species channels gives a **large partial recovery**:
- rollout species MAE improves from `0.488` to `0.208`
- rollout temperature MAE improves from `8403 K` to `2073 K`
- one-step metrics improve substantially too

That is much larger than the benefit from replacing only the last species.

So the dominant self-fed pathology is not just the closure-reconstructed final species channel.
It is concentrated more heavily in the **directly predicted main-species feature channels**.

### 2. The last-species channel still matters, but as a secondary part of the remaining gap
Main-species-only replacement does **not** reach teacher-forced performance.
There is still a clear residual gap between:
- oracle main species only
- oracle full species block

So the final species channel still contributes materially to the failure, but it is not the main story by itself.

### 3. The failure is distributed across the species re-encoding contract, with a strong emphasis on the directly predicted channels
Putting the recent diagnostics together:
- last-species-only replacement: not enough
- main-species-only replacement: large partial rescue
- full-species replacement: near-complete rescue

This is the cleanest decomposition so far.

## What this changes

This result sharpens the next structural target again.

The next non-oracle intervention should prioritize the construction of the **main predicted species features** in the second-step self-fed path, rather than focusing only on the closure-reconstructed last species.

The most plausible design direction now is to change the self-generated species feature contract itself—especially how the directly predicted species channels are formed and normalized before the second model call.

## Bottom line

The self-fed rollout problem is not caused mainly by the last closure species alone.

Most of the damage comes from the **main self-generated species feature channels**, while the last species contributes a smaller but still real residual part of the gap.

So future rollout-aware EFNO work should target the broader self-generated species feature representation, with first priority on the directly predicted species channels.
