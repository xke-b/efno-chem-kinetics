# EFNO self-rollout oracle-species ablation: replacing the full self-generated species feature block collapses the gap almost exactly to teacher forcing

_Date: 2026-04-23_

## Why this was the next step

The previous causal ablation showed that fixing only the worst single feature channel—the closure-reconstructed final species feature—did **not** rescue self-fed rollout training.

That suggested a sharper next diagnostic:

> If the full self-generated **species** feature block is replaced by the teacher-forced species feature block, while keeping the self-rollout training path otherwise intact, does the self-fed failure disappear?

This directly tests whether the self-fed instability is fundamentally a **species second-step feature construction** problem rather than a broader autoregressive or temperature-input problem.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added parameter:
- `rollout_species_feature_mode`
  - `"self"`
  - `"teacher_forced"`

Behavior in self-rollout mode:
- build the self-generated second-step feature vector as before
- optionally replace the entire species-feature block (`[:, 2:]`) with the teacher-forced second-step feature block

This is an oracle diagnostic, not a deployable training recipe.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_oracle_species_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_oracle_species_ablation/summary.json`

Compared:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_oracle_species`

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

### Pure teacher-forced reference
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

### Self-rollout with oracle species features
- one-step species MAE: `8.251e-05`
- one-step temperature MAE: `1.211e-01 K`
- one-step element-mass MAE: `1.555e-04`
- rollout species MAE @1000: `2.970e-02`
- rollout temperature MAE @1000: `7.044e+02 K`
- rollout element-mass MAE @1000: `5.776e-02`

## Main interpretation

### 1. This is the clearest causal result so far
Replacing the **entire species second-step feature block** with the teacher-forced version makes the self-rollout branch behave almost identically to the pure teacher-forced branch.

That is much stronger than the earlier last-species-only ablation.

### 2. The self-fed failure is therefore overwhelmingly a species-feature-construction failure
This result says the problem is not mainly:
- temperature second-step input
- pressure input
- optimizer instability in the abstract
- multi-step supervision itself

Instead, the failure is overwhelmingly caused by the **self-generated species feature block** used in the second-step input.

### 3. The last-species pathology was real but incomplete
The previous component-gap analysis correctly identified the reconstructed final species as the worst single channel.

But this experiment shows the broader truth:
- the whole self-generated species block is the decisive issue
- not only the last-species closure channel by itself

## What this changes

This substantially narrows the next structural search.

The next useful intervention should now target the **species second-step feature representation / re-encoding contract itself**, because that is the part carrying almost all of the damaging train-time self-exposure mismatch.

## Bottom line

This was a strong causal ablation.

It shows that if the self-rollout trainer is given teacher-forced species features at the second step, the catastrophic self-rollout degradation essentially disappears.

So the central bottleneck is now much more specifically identified as:
- the construction of the **self-generated species second-step feature block**

rather than autoregression in general.
