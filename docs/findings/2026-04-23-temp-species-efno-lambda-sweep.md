# EFNO-style conservation-weight sweep from the best mixed-target setting: rollout stability changes a lot, but one-step species accuracy still lags

_Date: 2026-04-23_

## Why this was the next step

The previous mixed-target weight sweep suggested that the most promising EFNO-style setting was:
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 2.0`

The next unresolved question was whether the remaining EFNO-style weakness came from the conservation-loss balance:
- `lambda_elements`
- `lambda_mass`

So I ran a focused holdout sweep around that setting.

## Sweep setup

Script:
- `/root/workspace/scripts/run_h2_temp_species_efno_lambda_sweep.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_temp_species_efno_lambda_sweep/summary.json`
- per-case eval JSONs under the same directory

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `efno_style`
- `target_mode = temperature_species`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 2.0`
- `lambda_data = 1.0`
- `10` epochs

Swept cases:
1. `elem_1p0_mass_1p0`
2. `elem_0p1_mass_1p0`
3. `elem_1p0_mass_0p1`
4. `elem_0p1_mass_0p1`
5. `elem_2p0_mass_0p1`

## Main results

### Ranking by one-step species MAE

| case | one-step species MAE | one-step temp MAE (K) | one-step element-mass MAE | rollout species MAE @1000 | rollout temp MAE @1000 (K) |
|---|---:|---:|---:|---:|---:|
| `elem_1p0_mass_0p1` | `3.20e-04` | `2.10e-01` | `5.83e-04` | `7.02e-01` | `1.20e+04` |
| `elem_0p1_mass_0p1` | `3.67e-04` | `2.20e-01` | `6.96e-04` | `5.18e-01` | `3.12e+04` |
| `elem_2p0_mass_0p1` | `3.84e-04` | `2.20e-01` | `7.85e-04` | `1.14e-01` | `2.13e+02` |
| `elem_1p0_mass_1p0` | `4.27e-04` | `2.31e-01` | `9.04e-04` | `6.72e-01` | `4.19e+04` |
| `elem_0p1_mass_1p0` | `5.00e-04` | `2.10e-01` | `1.03e-03` | `1.69e-01` | `3.18e+03` |

## What this teaches us

### 1. Lowering `lambda_mass` is necessary in this region
The cases with `lambda_mass = 1.0` were generally poor, especially in rollout temperature stability.

That suggests the current mass-sum penalty is too aggressive once the model already reconstructs a normalized species vector and also has to learn temperature.

### 2. Better one-step species MAE can hide terrible rollout behavior
The nominally best one-step-species case was:
- `elem_1p0_mass_0p1`

But it had:
- rollout species MAE @1000: `7.02e-01`
- rollout temperature MAE @1000: `1.20e+04 K`

So it is not actually a good setting.

### 3. `lambda_elements = 2.0`, `lambda_mass = 0.1` is the most interesting tradeoff in this sweep
This case was not best on one-step species MAE, but it was by far the best-balanced rollout case in this sweep:
- one-step species MAE: `3.84e-04`
- one-step temperature MAE: `2.20e-01 K`
- rollout species MAE @1000: `1.14e-01`
- rollout temperature MAE @1000: `2.13e+02 K`

This is still not better than the supervised baseline on one-step species accuracy, but it is much more interesting than the other EFNO-style lambda settings because the rollout no longer explodes as badly.

## Comparison to earlier best EFNO-style mixed-target setting
From the previous mixed-target weight sweep, the best one-step-species case was:
- `tempw_0p1_speciesw_2p0`
  - one-step species MAE: `2.65e-04`
  - rollout species MAE @1000: `8.40e-02`
  - rollout temperature MAE @1000: `6.12e+01 K`

So this new lambda sweep did **not** beat that earlier setting overall.

That is still useful information:
- adjusting `lambda_elements` and `lambda_mass` alone does not seem enough
- the earlier data-loss weighting change was more impactful than this conservation-weight sweep

## Comparison to supervised temp+species baseline
Supervised temp+species baseline:
- one-step species MAE: `5.98e-05`
- one-step temperature MAE: `3.74e-01 K`
- rollout species MAE @1000: `6.96e-02`
- rollout temperature MAE @1000: `4.27e+02 K`

Interpretation:
- EFNO-style still loses badly on one-step species accuracy
- but some EFNO-style settings now have **better one-step temperature** and **better rollout temperature** than supervised
- the main remaining barrier is still species fidelity and consistent overall tradeoff

## Most useful conclusion

This focused lambda sweep is mostly **negative evidence**, but good negative evidence:
- the most promising gain still comes from mixed-target data weighting, not conservation-weight tuning alone
- lowering `lambda_mass` seems helpful
- very strong element weighting can help rollout stability somewhat
- but none of these lambda settings surpassed the earlier best EFNO-style weighted-data setting

## Best next step

The next useful experiment should probably be:
1. return to the earlier strongest EFNO-style setting
   - `temperature_loss_weight = 0.1`
   - `species_loss_weight = 2.0`
   - `lambda_elements = 1.0`
   - `lambda_mass = 1.0`
2. test **longer training**
3. or try a small variant with
   - `lambda_mass = 0.1`
   - while keeping the stronger mixed-target data weighting

## Bottom line

This sweep improved understanding more than performance. It suggests the current EFNO-style mixed-target path is not primarily blocked by conservation-weight choice; it is more sensitive to the structure of the mixed-target data loss itself.
