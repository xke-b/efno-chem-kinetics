# EFNO self-rollout current-last-species ablation: replacing the final species feature with the current-state value does not help, and can actively interfere with better main-species fixes

_Date: 2026-04-23_

## Why this was the next step

After the direct-main-BCT intervention, the remaining obvious non-oracle target was the final species channel.

The earlier diagnostics had shown:
- the closure-reconstructed last species was the worst single feature-gap component
- but fixing only that channel with an oracle did not rescue self-fed rollout training
- most of the damage still came from the main predicted species channels

So the next realistic question was:

> If the last species is problematic because the self-generated next-step closure value is poor, would it help to use the **current-state** last-species feature instead?

This is a deployable-style idea on this benchmark because the final species (`N2`) is relatively inert and often changes slowly.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added rollout last-species mode:
- `"current_state"`

Behavior in self-rollout mode:
- build self-generated second-step features as usual
- optionally overwrite the final species feature with the **current input state's** last-species feature

This was tested both:
- by itself
- and together with the non-oracle `predicted_main_bct` main-species intervention

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_current_last_species_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_current_last_species_ablation/summary.json`

Cases:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_current_last_species`
4. `self_rollout0p1_predicted_main_bct`
5. `self_rollout0p1_predicted_main_bct_current_last`

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

### Self-rollout with current-state last species only
- one-step species MAE: `2.971e-04`
- one-step temperature MAE: `1.848e-01 K`
- one-step element-mass MAE: `6.259e-04`
- rollout species MAE @1000: `5.294e-01`
- rollout temperature MAE @1000: `7.364e+03 K`
- rollout element-mass MAE @1000: `1.172e+00`

### Self-rollout with predicted-main-BCT only
- one-step species MAE: `3.264e-04`
- one-step temperature MAE: `1.846e-01 K`
- one-step element-mass MAE: `6.525e-04`
- rollout species MAE @1000: `3.627e-01`
- rollout temperature MAE @1000: `6.457e+03 K`
- rollout element-mass MAE @1000: `7.801e-01`

### Self-rollout with predicted-main-BCT + current-state last species
- one-step species MAE: `3.168e-04`
- one-step temperature MAE: `1.746e-01 K`
- one-step element-mass MAE: `6.607e-04`
- rollout species MAE @1000: `5.918e-01`
- rollout temperature MAE @1000: `9.952e+03 K`
- rollout element-mass MAE @1000: `1.331e+00`

## Main interpretation

### 1. Current-state last-species replacement is not a useful fix
By itself, it gives a mixed picture:
- slight one-step species / element improvement
- somewhat better rollout temperature than pure self-rollout
- but **worse** rollout species and **worse** rollout element-mass error

So this is not a coherent recovery.

### 2. It can actively hurt a better main-species intervention
The stronger result is the combined case.

When paired with `predicted_main_bct`, the current-state last-species feature makes the model **much worse** than `predicted_main_bct` alone:
- rollout species MAE: `0.363 -> 0.592`
- rollout temperature MAE: `6457 K -> 9952 K`
- rollout element-mass MAE: `0.780 -> 1.331`

So the current-state last-species channel is not just insufficient; it can interfere destructively with a better main-species representation.

### 3. The last species still cannot be treated as a simple inert carryover channel
Even on this H2 benchmark, where the last species is relatively inert, simply freezing that feature at its current-state value is not a valid substitute for a coherent next-step species representation.

## What this changes

This failed attempt is useful because it rules out another plausible simplified contract:
- **do not** treat the last species feature as a simple copied current-state channel in self-fed rollout training

The remaining evidence now points more strongly to a need for a **coherent full-species second-step representation**, not an ad hoc patch on only the last feature.

## Bottom line

This intervention did not help.
Using the current-state last-species feature is not a viable bridge from the bad self-fed species block toward teacher-forced behavior, and it can even damage a better main-species encoding.

So the next structural work should move away from one-channel patches and toward redesigning the **full self-generated second-step species feature contract**.
