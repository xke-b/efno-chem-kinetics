# Seeded replicates show rollout variance is large enough to distort nearby mixed-target comparisons

_Date: 2026-04-23_

## Why this was the next step

The previous temperature-target note exposed a methodological problem: recent mixed-target results were being compared without fixed random seeds.

So the next step was to make seed control explicit in DFODE-kit training and then measure how much nearby results move across seeds.

## What changed

### DFODE-kit seed support
Added explicit training seed support and checkpoint recording:
- `/opt/src/DFODE-kit/dfode_kit/training/config.py`
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
- `/opt/src/DFODE-kit/tests/test_train_config_architecture.py`

Behavior:
- `TrainingConfig.seed` can now be set explicitly
- `train(...)` now seeds Python, NumPy, and PyTorch before model creation/training
- checkpoints record the seed under `training_config.seed`

### Reproducible experiment scripts
Updated active mixed-target comparison scripts to pass a fixed seed:
- `/root/workspace/scripts/run_h2_temp_species_longer_training_comparison.py`
- `/root/workspace/scripts/run_h2_temperature_target_mode_comparison.py`

### New replicate script
- `/root/workspace/scripts/run_h2_temp_species_seeded_replicates.py`

## Experiment

Artifact:
- `/root/workspace/artifacts/experiments/h2_temp_species_seeded_replicates/summary.json`

Setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0, 1, 2`

Cases:
1. `supervised_deltaT_25ep`
2. `efno_lowmass_deltaT_25ep`

## Aggregated results

### `supervised_deltaT_25ep`
- one-step species MAE mean/std: `6.23e-05 ± 5.08e-06`
- one-step temperature MAE mean/std: `1.75e-01 ± 8.52e-03 K`
- rollout species MAE @1000 mean/std: `2.78e-01 ± 2.70e-01`
- rollout temperature MAE @1000 mean/std: `1.49e+03 ± 8.50e+02 K`

Range across seeds:
- rollout species MAE @1000: `1.47e-02` to `6.49e-01`
- rollout temperature MAE @1000: `2.95e+02 K` to `2.16e+03 K`

### `efno_lowmass_deltaT_25ep`
- one-step species MAE mean/std: `3.57e-04 ± 8.28e-05`
- one-step temperature MAE mean/std: `1.42e-01 ± 3.22e-03 K`
- rollout species MAE @1000 mean/std: `3.23e-01 ± 3.67e-01`
- rollout temperature MAE @1000 mean/std: `4.66e+03 ± 3.80e+03 K`

Range across seeds:
- rollout species MAE @1000: `5.22e-02` to `8.42e-01`
- rollout temperature MAE @1000: `1.66e+03 K` to `1.00e+04 K`

## What this teaches us

### 1. One-step metrics are fairly stable; rollout metrics are not
For both trainers, one-step metrics moved modestly across seeds compared with rollout metrics.

That means the recent confusion was real: nearby experiments can look similar one-step while diverging dramatically in autoregressive behavior.

### 2. The earlier interpretation problem was not imagined
The rollout spread is large enough that comparing single unseeded runs can easily produce misleading conclusions about:
- target parameterization
- EFNO-style weighting
- whether a change helps or hurts rollout stability

### 3. Supervised still looks stronger on one-step species fidelity
Across seeds, supervised remains clearly better on one-step species and element-mass accuracy.

### 4. EFNO-style still has the same structural pattern
Across seeds, EFNO-style still tends to achieve:
- slightly better one-step temperature MAE
- much worse one-step species fidelity
- unstable rollout quality with large variance

So seed control did not reverse the main qualitative picture. It clarified that the rollout side of the benchmark is noisy enough that single-run evidence is weak.

## Most useful conclusion

This was a productive step because it converted a suspicion into quantified evidence:
- **fixed seeds are necessary** for credible pairwise comparisons
- **multiple seeds are desirable** when judging rollout stability claims

## Best next step

Now that seed control exists, the next useful modeling step is better constrained:
1. keep fixed-seed baselines as the default comparison protocol
2. test the next target-design or reconstruction hypothesis under the same seed(s)
3. prioritize diagnosis of the BCT + species reconstruction contract, because the main supervised-vs-EFNO gap still appears on species fidelity and rollout behavior, not one-step temperature prediction alone

## Bottom line

This was not just infrastructure work. It produced direct experimental evidence that rollout variance across seeds is large enough to distort nearby mixed-target comparisons. That substantially improves the reliability of the next round of EFNO diagnosis.
