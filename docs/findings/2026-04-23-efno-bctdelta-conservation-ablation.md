# EFNO BCT-delta conservation ablation: element loss is the main source of degradation, and current mass loss appears effectively inactive

_Date: 2026-04-23_

## Why this was the next step

The previous species-data-space ablation showed that moving EFNO species supervision into direct BCT-delta space helps one-step species fitting a bit, but does not rescue rollout.

That shifted the next structural question to the **conservation penalties**:
- are they helping rollout?
- are they hurting one-step fit?
- which penalty is actually doing work?

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_bctdelta_conservation_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_bctdelta_conservation_ablation/summary.json`

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

Cases:
1. `bctdelta_no_conservation`
   - `lambda_elements = 0.0`
   - `lambda_mass = 0.0`
2. `bctdelta_elements_only`
   - `lambda_elements = 2.0`
   - `lambda_mass = 0.0`
3. `bctdelta_elements_lowmass`
   - `lambda_elements = 2.0`
   - `lambda_mass = 0.1`

## Aggregated results

### No conservation
- one-step species MAE: `1.16e-04 ± 6.31e-06`
- one-step temperature MAE: `1.43e-01 ± 3.34e-03 K`
- one-step element-mass MAE: `1.69e-04 ± 1.25e-05`
- rollout species MAE @1000: `1.00e-01 ± 1.14e-01`
- rollout temperature MAE @1000: `1.97e+03 ± 2.69e+03 K`
- rollout element-mass MAE @1000: `1.98e-01 ± 2.71e-01`

### Elements only
- one-step species MAE: `3.03e-04 ± 5.02e-05`
- one-step temperature MAE: `1.42e-01 ± 3.55e-03 K`
- one-step element-mass MAE: `5.90e-04 ± 1.32e-04`
- rollout species MAE @1000: `3.51e-01 ± 4.07e-01`
- rollout temperature MAE @1000: `4.57e+03 ± 4.31e+03 K`
- rollout element-mass MAE @1000: `7.95e-01 ± 9.66e-01`

### Elements + low mass
- one-step species MAE: `3.03e-04 ± 5.02e-05`
- one-step temperature MAE: `1.42e-01 ± 3.55e-03 K`
- one-step element-mass MAE: `5.90e-04 ± 1.32e-04`
- rollout species MAE @1000: `3.51e-01 ± 4.07e-01`
- rollout temperature MAE @1000: `4.57e+03 ± 4.31e+03 K`
- rollout element-mass MAE @1000: `7.95e-01 ± 9.66e-01`

## What this teaches us

### 1. The element-conservation penalty is currently hurting, not helping, this benchmark
This is the strongest result.

Removing conservation penalties improved EFNO-style performance substantially:
- one-step species MAE improved from about `3.03e-04` to `1.16e-04`
- one-step element-mass MAE improved from about `5.90e-04` to `1.69e-04`
- rollout species MAE @1000 improved from about `3.51e-01` to `1.00e-01`
- rollout temperature MAE @1000 improved from about `4.57e+03 K` to `1.97e+03 K`

So, in the current mixed-target BCT-delta branch, the element-loss term appears to be the main source of degradation.

### 2. The current mass-loss term appears effectively inactive
`bctdelta_elements_only` and `bctdelta_elements_lowmass` produced essentially identical metrics.

That is consistent with the current trainer implementation:
- `y_pred` is explicitly normalized to sum to `1`
- then `mass_loss = L1(y_pred.sum(dim=1), 1)` is computed

So the current mass-loss term is likely near-zero by construction and is not meaningfully shaping training.

This is not just a tuning result. It is a **structural implementation finding**.

### 3. Conservation-off EFNO still does not beat the supervised baseline on one-step species, but it narrows the gap a lot
Compared with the seeded supervised temp+species baseline mean:
- supervised one-step species MAE: about `6.23e-05`
- EFNO no-conservation one-step species MAE: about `1.16e-04`

That is still worse, but much closer than the earlier EFNO variants.

### 4. Rollout variance is still high
The no-conservation branch still had large seed spread, especially in rollout temperature:
- min `4.48e+01 K`
- max `5.77e+03 K`

So removing conservation penalties improves the center of the distribution, but does not by itself make rollout reliably stable.

## Most useful conclusion

This experiment changes the diagnosis materially.

The main mixed-target EFNO bottleneck now looks less like:
- “species data-loss space is wrong”

and more like:
- “the current element-conservation penalty is misaligned with this target/reconstruction setup”
- while the mass-loss penalty is probably ineffective as currently implemented

## Bottom line

This was a high-value result.

On the seeded H2 temp+species holdout benchmark, the best EFNO-style branch improved sharply when conservation penalties were removed, and the apparent mass penalty had essentially no effect. That means the next useful thread is no longer generic loss tweaking; it is **redesigning or relocating the conservation terms so they constrain the right quantities without destroying species fit and rollout behavior**.
