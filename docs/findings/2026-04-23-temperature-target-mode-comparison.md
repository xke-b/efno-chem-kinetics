# Temperature target-mode comparison: absolute `T_next` does not solve the mixed-target problem, and missing seed control is now an evidence issue

_Date: 2026-04-23_

## Why this was the next step

The strongest open hypothesis was that the current mixed-target EFNO-style path might be using the wrong **temperature target parameterization**.

So I compared two temperature targets on the same H2 holdout benchmark:
- `temperature_species`
  - predict `delta_T` plus species targets
- `temperature_next_species`
  - predict absolute `T_next` plus species targets

I evaluated both under:
1. `supervised_physics`
2. the better EFNO-style branch with stronger mixed-target weighting and reduced mass penalty

## Experiment

Script:
- `/root/workspace/scripts/run_h2_temperature_target_mode_comparison.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_temperature_target_mode_comparison/summary.json`
- per-case eval JSONs in the same directory

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs

Cases:
1. `supervised_deltaT_25ep`
2. `supervised_Tnext_25ep`
3. `efno_lowmass_deltaT_25ep`
4. `efno_lowmass_Tnext_25ep`

## Main result

### Ranked by one-step species MAE

| case | one-step species MAE | one-step temp MAE (K) | one-step element-mass MAE | rollout species MAE @1000 | rollout temp MAE @1000 (K) |
|---|---:|---:|---:|---:|---:|
| `supervised_deltaT_25ep` | `6.36e-05` | `1.92e-01` | `1.28e-04` | `7.86e-01` | `8.32e+03` |
| `supervised_Tnext_25ep` | `7.01e-05` | `1.97e+01` | `1.40e-04` | `6.54e-01` | `1.83e+04` |
| `efno_lowmass_Tnext_25ep` | `3.55e-04` | `1.64e+01` | `7.27e-04` | `3.11e-02` | `1.08e+03` |
| `efno_lowmass_deltaT_25ep` | `3.81e-04` | `1.66e-01` | `7.51e-04` | `8.15e-01` | `4.81e+04` |

## What this teaches us

### 1. Predicting absolute `T_next` is not a clean fix
For both trainers, the `T_next` target caused very large one-step temperature errors:
- supervised `T_next` temperature MAE: about `19.7 K`
- EFNO `T_next` temperature MAE: about `16.4 K`

So absolute `T_next` is not a good drop-in replacement for `delta_T` in the current setup.

### 2. The tradeoff is stranger than expected
The EFNO `T_next` case had poor one-step temperature MAE but comparatively good rollout species MAE:
- rollout species MAE @1000: `3.11e-02`

Meanwhile the EFNO `delta_T` case kept strong one-step temperature MAE but had catastrophic rollout:
- rollout temperature MAE @1000: `4.81e+04 K`

This suggests the temperature target parameterization does interact with rollout behavior, but not in a simple or uniformly helpful way.

### 3. Reproducibility is now an active issue
A more important meta-result appeared here:
- the new `supervised_deltaT_25ep` result is much worse in rollout than the earlier `supervised_physics_25ep` result from the previous comparison
- the training code currently does **not** set or record a fixed random seed for these trainer runs

That means some of the observed differences across recent experiments are now confounded by training stochasticity.

This is no longer a small nuisance. It is affecting interpretation.

## Most useful conclusion

This experiment produced two valuable outcomes:
1. **technical negative evidence**
   - absolute `T_next` is not the easy temperature-target fix
2. **workflow diagnosis**
   - seed control is now necessary for credible comparison of nearby mixed-target settings

## Best next step

Before more target-parameterization variations, the most useful next improvement is likely:
1. add explicit seed control to the training/comparison scripts
2. rerun the strongest recent baselines under fixed seeds
3. only then compare additional temperature target designs

## Bottom line

The target-design hypothesis did produce information, but it also exposed a bigger methodological problem: nearby mixed-target comparisons are now sensitive enough that uncontrolled training randomness is interfering with interpretation. That is useful progress because it tells us the next step should improve **experimental reliability**, not just add another modeling variant.
