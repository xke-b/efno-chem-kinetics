# EFNO self-rollout oracle-last-species ablation: fixing the worst single feature channel alone does not rescue self-fed training

_Date: 2026-04-23_

## Why this was the next step

The component-level second-step feature-gap analysis showed the clearest mechanistic clue so far:
- the self-vs-teacher mismatch is overwhelmingly a species-BCT problem
- the largest single pathology is the final closure-reconstructed species feature (`N2` on this H2 benchmark)

That suggested a direct targeted diagnostic:

> If the self-fed rollout trainer is allowed to keep its own second-step features everywhere **except** for the final species channel, which is replaced by the teacher-forced value, does self-fed training recover?

This is not meant as a deployable method. It is a causal ablation to test whether the dominant last-species feature pathology is the main bottleneck or only part of it.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added parameter:
- `rollout_last_species_feature_mode`
  - `"self"`
  - `"teacher_forced"`

Behavior in self-rollout mode:
- build the self-generated next-step feature vector as before
- optionally replace only its final species feature channel with the teacher-forced next-step feature channel

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_last_species_oracle_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_last_species_oracle_ablation/summary.json`

Compared:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_oracle_last_species`

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
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`

### Pure self-rollout
- one-step species MAE: `3.39e-04`
- one-step temperature MAE: `1.80e-01 K`
- one-step element-mass MAE: `6.86e-04`
- rollout species MAE @1000: `4.88e-01`
- rollout temperature MAE @1000: `8.40e+03 K`

### Self-rollout with oracle last-species feature
- one-step species MAE: `2.97e-04`
- one-step temperature MAE: `1.85e-01 K`
- one-step element-mass MAE: `6.26e-04`
- rollout species MAE @1000: `5.29e-01`
- rollout temperature MAE @1000: `7.36e+03 K`

## Main interpretation

### 1. The last-species channel is important, but not sufficient to explain the whole failure
Replacing only the final species feature channel with the teacher-forced value did **not** rescue self-fed rollout training.

That means the dominant `N2` feature-gap signal identified earlier is real, but it is not the sole cause of the self-fed failure.

### 2. The ablation produced mixed effects, not a clean recovery
Relative to pure self-rollout:
- one-step species improved a little
- one-step element-mass improved a little
- rollout temperature improved somewhat
- rollout species actually got worse

So this is not a coherent repair. It is a partial perturbation of the failure mode.

### 3. The broader species-BCT path remains the problem
This result fits the component-gap analysis:
- the final species channel is the worst single offender
- but several other species channels also have large gaps (`H2`, `H`, `O`, `OH`)

So the problem appears distributed across the self-generated species re-encoding path, even if one channel is especially bad.

## What this changes

This is a useful narrowing result.

It tells us the next structural change should **not** focus only on the final closure-reconstructed species feature. That channel matters, but patching it alone does not restore good self-fed behavior.

The more credible next intervention target is now the **broader species second-step feature construction**, especially the Box-Cox re-encoding contract under self-generated composition updates.

## Bottom line

This was a productive causal ablation.

It showed that the worst single second-step feature channel is not the whole story. The self-fed failure is more distributed across the species-feature path, so the next useful experiment should target the full species re-encoding contract rather than only the last-species closure channel.
