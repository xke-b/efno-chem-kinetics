# EFNO species data-space ablation: removing reconstruction from the data term helps one-step species fidelity a bit, but does not fix rollout instability

_Date: 2026-04-23_

## Why this was the next step

After adding seed control, the strongest structural hypothesis was that the current EFNO-style mixed-target trainer is being hurt by its **species reconstruction contract**.

In the current branch, the data term for species is computed after:
1. adding predicted Box-Cox deltas to the transformed input state
2. applying inverse Box-Cox
3. reconstructing the final species by complement
4. renormalizing mass fractions

That means the species data loss is not applied directly in the same space the model predicts.

So I tested whether EFNO-style training improves if the species data loss is moved to the **predicted BCT-delta space**, while keeping the element and mass conservation losses in reconstructed mass-fraction space.

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

New trainer parameter:
- `species_data_space`
  - `"mass_fraction"` = current behavior
  - `"bct_delta"` = apply species data loss directly on denormalized BCT deltas

The conservation losses still use reconstructed mass fractions in both cases.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_species_data_space_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_species_data_space_ablation/summary.json`

Setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- common EFNO-style settings:
  - `target_mode = "temperature_species"`
  - `temperature_loss_weight = 0.1`
  - `species_loss_weight = 2.0`
  - `lambda_elements = 2.0`
  - `lambda_mass = 0.1`

Cases:
1. `efno_lowmass_mass_fraction`
2. `efno_lowmass_bct_delta`

## Aggregated results

### Current behavior: `species_data_space="mass_fraction"`
- one-step species MAE: `3.57e-04 ± 8.28e-05`
- one-step temperature MAE: `1.42e-01 ± 3.22e-03 K`
- one-step element-mass MAE: `7.07e-04 ± 2.09e-04`
- rollout species MAE @1000: `3.23e-01 ± 3.67e-01`
- rollout temperature MAE @1000: `4.66e+03 ± 3.80e+03 K`

### Ablation: `species_data_space="bct_delta"`
- one-step species MAE: `3.03e-04 ± 5.02e-05`
- one-step temperature MAE: `1.42e-01 ± 3.55e-03 K`
- one-step element-mass MAE: `5.90e-04 ± 1.32e-04`
- rollout species MAE @1000: `3.51e-01 ± 4.07e-01`
- rollout temperature MAE @1000: `4.57e+03 ± 4.31e+03 K`

## What this teaches us

### 1. The reconstruction-heavy data term is part of the one-step species problem
Moving the species data loss into BCT-delta space improved mean one-step species MAE:
- from `3.57e-04`
- to `3.03e-04`

It also improved one-step element-mass MAE:
- from `7.07e-04`
- to `5.90e-04`

So the current reconstruction-based species data term is likely contributing some avoidable optimization difficulty.

### 2. But this does **not** fix the main failure mode
The rollout metrics did not improve in a convincing way.

In fact, mean rollout species MAE @1000 got slightly worse:
- `3.23e-01` → `3.51e-01`

Mean rollout temperature MAE @1000 changed only marginally:
- `4.66e+03 K` → `4.57e+03 K`

Given the large seed variance, this is not evidence of a real rollout gain.

### 3. The species reconstruction contract is not the whole story
This is the most useful conclusion.

The ablation says:
- yes, the choice of species data-loss space matters somewhat for one-step fitting
- no, simply removing reconstruction from the data term is not enough to recover stable rollout behavior

That means the EFNO-style gap is probably broader than one local loss-space mismatch.

More likely remaining causes include:
- interaction between weighted data loss and conservation penalties
- instability from autoregressive temperature-species coupling
- limitations of the current target formulation itself
- model capacity / inductive-bias mismatch in the current MLP baseline

## Bottom line

This was a useful partial negative result.

Changing EFNO-style species supervision from reconstructed mass-fraction space to direct BCT-delta space improves **one-step species and element-mass accuracy a little**, but it does **not** solve the central problem of unstable long-horizon rollout.

So the reconstruction-heavy data term is part of the issue, but not the dominant explanation for the current mixed-target EFNO gap.
