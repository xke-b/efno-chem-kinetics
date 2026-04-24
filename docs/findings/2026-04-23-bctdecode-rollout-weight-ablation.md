# Corrected-decode rollout-weight ablation: rollout-aware training remains crucial after the decode fix, and the best current H2 branch stays at self-rollout weight 0.1 with predicted-main-BCT features

_Date: 2026-04-23_

## Why this was the next step

After the BCT-state decode fix, the old rollout-training conclusions were no longer reliable.

The next necessary step was to re-check a nearby design question under the corrected decode regime:

> How much rollout-consistency weight is actually needed now, and does the corrected best branch remain the best after re-baselining against a no-rollout corrected-decode model?

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_bctdecode_rollout_weight_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_bctdecode_rollout_weight_ablation/summary.json`

Compared cases:
1. `baseline_norollout_bctdecode`
2. `teacherforced_rollout0p1_bctdecode`
3. `self_rollout0p01_bctdecode`
4. `self_rollout0p1_bctdecode`
5. `self_rollout0p01_predicted_main_bct_bctdecode`
6. `self_rollout0p1_predicted_main_bct_bctdecode`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- corrected decode: `species_decode_mode = "bct_state_addition"`
- `target_mode = "temperature_species"`
- `species_data_space = "bct_delta"`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`
- `lambda_elements = 0.0`
- `lambda_mass = 0.0`

## Main results

### Corrected no-rollout baseline
- one-step species MAE: `1.123e-04`
- one-step temperature MAE: `1.430e-01 K`
- one-step element-mass MAE: `1.615e-04`
- rollout species MAE @1000: `9.898e-02`
- rollout temperature MAE @1000: `1.901e+03 K`
- rollout element-mass MAE @1000: `1.980e-01`

### Corrected teacher-forced rollout 0.1
- one-step species MAE: `8.253e-05`
- one-step temperature MAE: `1.210e-01 K`
- one-step element-mass MAE: `1.556e-04`
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`
- rollout element-mass MAE @1000: `5.777e-02`

### Corrected self-rollout 0.01
- one-step species MAE: `1.258e-04`
- one-step temperature MAE: `1.363e-01 K`
- one-step element-mass MAE: `2.397e-04`
- rollout species MAE @1000: `9.602e-03`
- rollout temperature MAE @1000: `8.956e+01 K`
- rollout element-mass MAE @1000: `9.703e-03`

### Corrected self-rollout 0.1
- one-step species MAE: `1.023e-04`
- one-step temperature MAE: `1.240e-01 K`
- one-step element-mass MAE: `1.980e-04`
- rollout species MAE @1000: `1.017e-02`
- rollout temperature MAE @1000: `9.598e+01 K`
- rollout element-mass MAE @1000: `1.034e-02`

### Corrected self-rollout + predicted-main-BCT 0.01
- one-step species MAE: `1.207e-04`
- one-step temperature MAE: `1.364e-01 K`
- one-step element-mass MAE: `2.277e-04`
- rollout species MAE @1000: `8.505e-03`
- rollout temperature MAE @1000: `8.651e+01 K`
- rollout element-mass MAE @1000: `6.216e-03`

### Corrected self-rollout + predicted-main-BCT 0.1
- one-step species MAE: `9.903e-05`
- one-step temperature MAE: `1.235e-01 K`
- one-step element-mass MAE: `1.894e-04`
- rollout species MAE @1000: `7.715e-03`
- rollout temperature MAE @1000: `7.352e+01 K`
- rollout element-mass MAE @1000: `6.237e-03`

## Main interpretation

### 1. Rollout-aware training is still essential after the decode fix
The corrected no-rollout baseline is much better than the old bug-contaminated branches, but it is still clearly worse than the rollout-aware corrected branches.

Compared with the best corrected branch, the no-rollout baseline is much worse on:
- rollout species MAE (`0.09898` vs `0.007715`)
- rollout temperature MAE (`1900.7 K` vs `73.5 K`)
- rollout element-mass MAE (`0.1980` vs `0.00624`)

So multi-step training remains genuinely useful even after the decode bug is fixed.

### 2. Corrected self-rollout is still much better than corrected teacher forcing on rollout
Teacher forcing remains strong, but corrected self-rollout dominates it on long-horizon behavior.

### 3. The best current branch remains stable under this re-baselining
The top rollout branch is still:
- `self_rollout0p1_predicted_main_bct_bctdecode`

The lower rollout-consistency weight `0.01` is competitive, especially on rollout element-mass, but `0.1` remains the strongest overall tradeoff and best rollout-species / rollout-temperature setting in this small corrected-decode sweep.

## Bottom line

The decode fix did not make rollout-aware training unnecessary.
After re-baselining under corrected decoding, rollout-consistency training still delivers large real gains, and the best current H2 EFNO branch remains corrected self-rollout with predicted-main-BCT features at rollout weight `0.1`.
