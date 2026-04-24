# Longer training clarifies the mixed-target picture: supervised improves strongly, EFNO-style temperature stays good but species still lag

_Date: 2026-04-23_

## Why this was the next step

After the mixed-target loss sweeps, the most useful unresolved question was whether the best-looking settings were simply undertrained.

So I ran a longer-training comparison on the same H2 holdout split using `25` epochs instead of `10`.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_temp_species_longer_training_comparison.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_temp_species_longer_training_comparison/summary.json`
- per-case eval JSONs under the same directory

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `target_mode = temperature_species`
- `25` epochs

Cases compared:
1. `supervised_physics_25ep`
2. `efno_best_weighted_25ep`
   - `temperature_loss_weight = 0.1`
   - `species_loss_weight = 2.0`
   - `lambda_elements = 1.0`
   - `lambda_mass = 1.0`
3. `efno_best_weighted_lowmass_25ep`
   - `temperature_loss_weight = 0.1`
   - `species_loss_weight = 2.0`
   - `lambda_elements = 2.0`
   - `lambda_mass = 0.1`

## Main results

| case | one-step species MAE | one-step temp MAE (K) | one-step element-mass MAE | rollout species MAE @1000 | rollout temp MAE @1000 (K) |
|---|---:|---:|---:|---:|---:|
| `supervised_physics_25ep` | `7.21e-05` | `1.97e-01` | `1.50e-04` | `4.31e-02` | `5.52e+01` |
| `efno_best_weighted_lowmass_25ep` | `3.28e-04` | `1.53e-01` | `6.08e-04` | `8.89e-02` | `3.71e+02` |
| `efno_best_weighted_25ep` | `3.56e-04` | `1.43e-01` | `6.63e-04` | `1.55e-01` | `4.11e+03` |

## What this teaches us

### 1. Longer training helps the supervised baseline a lot
This is the most important outcome.

Compared with the earlier `10`-epoch supervised temp+species run, the `25`-epoch supervised baseline improved substantially:
- one-step temperature MAE dropped to about `0.197 K`
- rollout species MAE @1000 dropped to about `4.31e-02`
- rollout temperature MAE @1000 dropped to about `5.52e+01 K`

So the supervised temp+species baseline is now clearly stronger than before.

### 2. EFNO-style still gives very strong one-step temperature accuracy
Both EFNO-style runs beat the supervised baseline on one-step temperature MAE:
- best EFNO-style one-step temperature MAE: `1.43e-01 K`
- supervised one-step temperature MAE: `1.97e-01 K`

So there is still a real temperature-modeling signal in the EFNO-style objective.

### 3. Species fidelity remains the main blocker
Despite the better temperature numbers, both EFNO-style runs still lag badly on one-step species accuracy and element-mass accuracy.

That makes the overall picture much clearer:
- **temperature is not the main failure now**
- **species accuracy and balanced multi-target tradeoff are the main failure**

### 4. Reduced mass weighting is still preferable inside EFNO-style
The lower-mass-penalty EFNO-style run was clearly better than the default-weight EFNO-style run in rollout:
- `efno_best_weighted_lowmass_25ep`
  - rollout species MAE @1000: `8.89e-02`
  - rollout temperature MAE @1000: `3.71e+02 K`
- `efno_best_weighted_25ep`
  - rollout species MAE @1000: `1.55e-01`
  - rollout temperature MAE @1000: `4.11e+03 K`

So the low-mass variant remains the more credible EFNO-style branch.

## Most useful conclusion

Longer training did **not** rescue EFNO-style into a better overall baseline.

Instead, it sharpened the diagnosis:
- the supervised temp+species baseline is stronger and more stable than before
- EFNO-style can achieve better one-step temperature MAE
- but it still cannot match supervised on species fidelity or total tradeoff

This makes the next research question more precise:

> how should the target or loss be redesigned so EFNO-style temperature gains do not come at the expense of species accuracy?

## Best next step

The most useful next experiment is probably **target-design focused**, not more brute-force training:
1. test an alternative temperature target parameterization
   - e.g. normalized `T_next`, transformed temperature target, or scaled `delta_T`
2. keep the better EFNO-style branch
   - stronger mixed-target data weighting
   - reduced mass penalty
3. compare whether that changes the species/temperature tradeoff

## Bottom line

Longer training gave a stronger answer, not just more numbers: the current EFNO-style mixed-target path is not merely undertrained. Its remaining problem is structural, and it is most visible in species accuracy.
