# EFNO BCT-state decode ablation: the self-rollout collapse was largely caused by a decode-contract bug, and correcting it makes self-fed training dramatically better than teacher forcing on H2

_Date: 2026-04-23_

## Why this was the next step

The previous rollout-diagnosis thread had narrowed the failure to the self-generated species second-step path, but the remaining behavior was becoming suspiciously pathological.

The key code-level observation was this:
- labels in the thermochemical branch are **species deltas in Box-Cox space**
- but the legacy decode path was adding those BCT-space deltas to a **mass-fraction-space** base state before applying `inverse_BCT_torch(...)`

That is dimensionally inconsistent.

Concretely, the legacy path was effectively doing:
- `pred_bct_state = current_mass_fraction + predicted_bct_delta`

instead of the consistent update:
- `pred_bct_state = current_bct_state + predicted_bct_delta`

This was a strong candidate root cause for the off-simplex self-generated species states seen in the earlier diagnostics.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added parameter:
- `species_decode_mode`
  - `"legacy_mass_fraction_addition"`
  - `"bct_state_addition"`

The corrected mode now adds species deltas in the same space they are predicted:
- current BCT state + predicted BCT delta

## Experiments

Main ablation script:
- `/root/workspace/scripts/run_h2_efno_bct_state_decode_ablation.py`

Geometry diagnostic:
- `/root/workspace/scripts/analyze_h2_species_decode_geometry.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_efno_bct_state_decode_ablation/summary.json`
- `/root/workspace/artifacts/experiments/h2_efno_bct_state_decode_ablation/decode_geometry_seed0.json`

Compared against legacy references:
- legacy teacher-forced rollout
- legacy self-rollout
- legacy self-rollout + predicted-main-BCT

New corrected-decode cases:
1. `teacherforced_rollout0p1_bctdecode`
2. `self_rollout0p1_bctdecode`
3. `self_rollout0p1_predicted_main_bct_bctdecode`

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

## Decode-geometry diagnostic

Representative seed-0 geometry:

### Legacy decode
- pre-normalization species-sum mean: `6.3043`
- min: `6.2631`
- max: `6.3318`
- fraction with sum `> 1 + 1e-6`: `1.0`

### Corrected BCT-state decode
- pre-normalization species-sum mean: `1.0`
- min: `0.99999988`
- max: `1.00000012`
- fraction with sum `> 1 + 1e-6`: `0.0`
- fraction with sum `< 1 - 1e-6`: `0.0`

This is the clearest mechanistic confirmation so far:
- the legacy decode was generating grossly off-simplex species states
- the corrected decode restores a physically coherent species-state geometry almost exactly

## Aggregated performance results

### Legacy teacher-forced reference
- one-step species MAE: `8.253e-05`
- one-step temperature MAE: `1.210e-01 K`
- one-step element-mass MAE: `1.556e-04`
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`
- rollout element-mass MAE @1000: `5.777e-02`

### Legacy self-rollout reference
- one-step species MAE: `3.392e-04`
- one-step temperature MAE: `1.802e-01 K`
- one-step element-mass MAE: `6.861e-04`
- rollout species MAE @1000: `4.881e-01`
- rollout temperature MAE @1000: `8.403e+03 K`
- rollout element-mass MAE @1000: `1.050e+00`

### Legacy self-rollout + predicted-main-BCT reference
- one-step species MAE: `3.264e-04`
- one-step temperature MAE: `1.846e-01 K`
- one-step element-mass MAE: `6.525e-04`
- rollout species MAE @1000: `3.627e-01`
- rollout temperature MAE @1000: `6.457e+03 K`
- rollout element-mass MAE @1000: `7.801e-01`

### Corrected-decode teacher-forced
- one-step species MAE: `8.253e-05`
- one-step temperature MAE: `1.210e-01 K`
- one-step element-mass MAE: `1.556e-04`
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`
- rollout element-mass MAE @1000: `5.777e-02`

### Corrected-decode self-rollout
- one-step species MAE: `1.023e-04`
- one-step temperature MAE: `1.240e-01 K`
- one-step element-mass MAE: `1.980e-04`
- rollout species MAE @1000: `1.017e-02`
- rollout temperature MAE @1000: `9.598e+01 K`
- rollout element-mass MAE @1000: `1.034e-02`

### Corrected-decode self-rollout + predicted-main-BCT
- one-step species MAE: `9.903e-05`
- one-step temperature MAE: `1.235e-01 K`
- one-step element-mass MAE: `1.894e-04`
- rollout species MAE @1000: `7.715e-03`
- rollout temperature MAE @1000: `7.352e+01 K`
- rollout element-mass MAE @1000: `6.237e-03`

## Main interpretation

### 1. The self-rollout collapse was mostly self-inflicted by a decode-contract error
This is the most important result.

The earlier catastrophic self-rollout behavior was not primarily evidence that self-fed training is intrinsically worse than teacher forcing on this benchmark.
A large fraction of that collapse came from decoding species updates with a **space-mismatched update rule**.

### 2. Correcting the decode geometry almost completely changes the picture
With the corrected BCT-state decode:
- self-rollout no longer collapses
- self-rollout becomes highly stable
- self-rollout actually beats the teacher-forced branch on the major rollout metrics

### 3. Why teacher forcing barely changed
Teacher-forced rollout was already using teacher features at the second step, so the self-generated species feature path mattered much less there.
Also, with `species_data_space = "bct_delta"` and zero conservation weights, the corrected decode mainly affects the self-fed second-step path rather than the main supervised objective.

### 4. The earlier diagnostics were still useful—but they were diagnosing a bug-contaminated regime
The previous species-gap analyses were not wasted effort.
They correctly pointed at the self-generated species path.
But the new evidence shows that much of that pathology came from a specific decode inconsistency rather than an unavoidable exposure-bias barrier.

## What this changes

This is a major update to the program state.

The current best offline EFNO-style branch on the H2 benchmark is no longer the teacher-forced rollout variant.
It is now:
- **corrected-decode self-rollout + predicted-main-BCT**

This branch is both non-oracle and decisively stronger on rollout metrics than the earlier teacher-forced reference.

## Bottom line

A core decode-contract bug was found and tested directly.
Correcting species updates in **BCT state space** rather than adding BCT deltas to a mass-fraction base state repairs the self-generated species geometry and transforms rollout performance.

This is one of the strongest progress steps so far because it converts a long diagnostic thread into a concrete mechanism-level fix with large empirical gains.
