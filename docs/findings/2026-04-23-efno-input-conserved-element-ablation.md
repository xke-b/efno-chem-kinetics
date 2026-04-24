# EFNO input-conserved element-loss ablation: targeting conserved input elements avoids the damage caused by reconstructed-next-state element loss, but adds no measurable benefit on this benchmark

_Date: 2026-04-23_

## Why this was the next step

The previous conservation ablation showed two important things:
1. the current EFNO-style element-conservation loss is the main source of degradation in the mixed-target branch
2. the current mass-loss term is effectively inactive

That raised a more precise design question:

> is the problem the **presence** of element conservation, or the **target used for the element loss**?

The current implementation penalized predicted element mass against the **reconstructed next-state target** `y_true`.

A more physics-native alternative is to penalize predicted element mass against the **input-state element mass**, because element totals should be conserved from the current state forward.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

New EFNO trainer parameter:
- `element_loss_mode`
  - `"true_next"` = existing behavior
  - `"input_conserved"` = compare predicted element mass to the input state's element mass

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_input_conserved_element_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_input_conserved_element_ablation/summary.json`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- common EFNO-style settings:
  - `target_mode = "temperature_species"`
  - `temperature_loss_weight = 0.1`
  - `species_loss_weight = 2.0`
  - `species_data_space = "bct_delta"`
  - `lambda_data = 1.0`
  - `lambda_mass = 0.0`

Cases:
1. `bctdelta_no_conservation`
2. `bctdelta_true_next_elem0p1`
3. `bctdelta_input_conserved_elem0p1`
4. `bctdelta_input_conserved_elem1p0`

## Aggregated results

### No conservation
- one-step species MAE: `1.16e-04 ± 6.31e-06`
- one-step temperature MAE: `1.43e-01 ± 3.34e-03 K`
- one-step element-mass MAE: `1.69e-04 ± 1.25e-05`
- rollout species MAE @1000: `1.00e-01 ± 1.14e-01`
- rollout temperature MAE @1000: `1.97e+03 ± 2.69e+03 K`

### Reconstructed-next-state element loss, `lambda_elements=0.1`
- one-step species MAE: `1.26e-04 ± 8.81e-06`
- one-step temperature MAE: `1.43e-01 ± 3.45e-03 K`
- one-step element-mass MAE: `2.01e-04 ± 2.80e-05`
- rollout species MAE @1000: `1.53e-01 ± 1.63e-01`
- rollout temperature MAE @1000: `2.97e+03 ± 4.08e+03 K`

### Input-conserved element loss, `lambda_elements=0.1`
- one-step species MAE: `1.16e-04 ± 6.31e-06`
- one-step temperature MAE: `1.43e-01 ± 3.34e-03 K`
- one-step element-mass MAE: `1.69e-04 ± 1.25e-05`
- rollout species MAE @1000: `1.00e-01 ± 1.14e-01`
- rollout temperature MAE @1000: `1.97e+03 ± 2.69e+03 K`

### Input-conserved element loss, `lambda_elements=1.0`
- effectively identical to the `0.1` case and to `no_conservation`

## What this teaches us

### 1. The damaging part was not “physics” in general; it was the reconstructed-next-state element target
Even a small reconstructed-next-state element penalty (`lambda_elements = 0.1`) worsened performance relative to no-conservation:
- species worsened
- element-mass worsened
- rollout worsened

So the previous degradation was not just because physics constraints are inherently bad here. It was specifically tied to **where the element target came from**.

### 2. Using the input state's conserved element mass removes that damage
When the element target was switched from reconstructed `y_true` to input-state conserved mass, the degradation disappeared.

That is the most important result from this step.

### 3. But the input-conserved element penalty also added no measurable benefit on this benchmark
The `input_conserved` runs were effectively identical to `no_conservation`, even when `lambda_elements` increased from `0.1` to `1.0`.

So, on this H2 holdout benchmark, the input-conserved element term is at best benign but not yet useful.

### 4. Most plausible interpretation
The reconstructed-next-state target appears to inject inconsistency from the current decode/reconstruction path.

In contrast, the input-conserved element target is physically aligned and does not fight the learned fit. But under the current setup, it is also mostly redundant with what the data term already learns.

## Most useful conclusion

This result sharpens the diagnosis again:
- **bad conservation target choice** was a real source of EFNO degradation
- a more principled input-conserved element target removes that harm
- but it does not yet improve the benchmark over the simpler no-conservation branch

## Bottom line

This was a useful structural result.

The harmful part of the prior EFNO conservation design was not merely “having an element penalty,” but targeting the penalty to the reconstructed next state. Switching the target to conserved input elements makes the penalty effectively harmless on this benchmark, but still not performance-improving. That means the best current mixed-target EFNO branch remains the simpler no-conservation BCT-delta variant, and any future conservation design should be judged against that stronger baseline rather than the older degraded one.
