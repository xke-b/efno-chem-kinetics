# EFNO self-rollout predicted-main-BCT ablation: bypassing the main-species inverse/renormalize/re-encode loop helps, but only modestly

_Date: 2026-04-23_

## Why this was the next step

The previous decomposition established that most of the self-fed rollout damage comes from the **main predicted species channels** in the second-step feature block.

That suggested the first non-oracle structural intervention:

> Instead of decoding the predicted main-species Box-Cox state back to mass fractions, renormalizing with a closure species, and then Box-Cox re-encoding those main channels for the second model call, what happens if we feed the predicted main-species Box-Cox state directly into the second-step feature vector?

This is a realistic intervention because the trainer already predicts species updates in Box-Cox space.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added rollout species-feature mode:
- `"predicted_main_bct"`

Behavior in self-rollout mode:
- compute the self-generated second-step features as usual
- overwrite the main predicted species feature channels `[:, 2:-1]` with the directly predicted next-step Box-Cox state
- keep the last species channel self-generated through the existing closure path

So this intervention bypasses the main-species inverse-BCT → renormalize → BCT roundtrip while leaving the last-species channel unchanged.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_predicted_main_bct_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_predicted_main_bct_ablation/summary.json`

Cases:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_predicted_main_bct`
4. `self_rollout0p1_oracle_main_species_only`

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

### Predicted-main-BCT self-rollout
- one-step species MAE: `3.264e-04`
- one-step temperature MAE: `1.846e-01 K`
- one-step element-mass MAE: `6.525e-04`
- rollout species MAE @1000: `3.627e-01`
- rollout temperature MAE @1000: `6.457e+03 K`
- rollout element-mass MAE @1000: `7.801e-01`

### Oracle main-species-only reference
- one-step species MAE: `1.639e-04`
- one-step temperature MAE: `1.521e-01 K`
- one-step element-mass MAE: `3.009e-04`
- rollout species MAE @1000: `2.080e-01`
- rollout temperature MAE @1000: `2.073e+03 K`
- rollout element-mass MAE @1000: `4.760e-01`

## Main interpretation

### 1. The direct-main-BCT intervention helps, so the roundtrip itself is part of the problem
Compared with pure self-rollout, direct main-BCT features improved:
- rollout species MAE: `0.488 -> 0.363`
- rollout temperature MAE: `8403 K -> 6457 K`
- rollout element-mass MAE: `1.050 -> 0.780`
- one-step species and element metrics also improved slightly

So the current inverse-BCT → mass-fraction normalization → BCT re-encoding path is indeed contributing harm.

### 2. But the gain is only partial and still far from the oracle main-species ceiling
The new mode is still much worse than oracle main-species replacement:
- rollout species MAE: `0.363` vs `0.208`
- rollout temperature MAE: `6457 K` vs `2073 K`

So simply bypassing the main-species roundtrip is not enough to recover the full missing performance.

### 3. The remaining failure is still structural, not just a numeric encoding artifact
This means the main-species problem is not only that we were roundtripping through inverse/encode unnecessarily.

There is still a broader mismatch between:
- the self-generated main-species second-step feature distribution
- and the teacher-forced main-species feature distribution

## What this changes

This experiment converts a plausible implementation idea into evidence:
- **yes**, direct main-BCT injection helps
- **no**, it does not close the gap enough to rescue self-fed rollout training

So the next intervention should probably target a broader species-feature contract, not just the local BCT roundtrip.

## Bottom line

The main predicted species channels remain the right target.
Bypassing their inverse/renormalize/re-encode loop provides a real but modest improvement, which confirms that this roundtrip is part of the pathology.

But most of the self-fed gap remains, so further work should focus on a more substantial redesign of the self-generated second-step species representation rather than treating the roundtrip alone as the full explanation.
