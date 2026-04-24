# EFNO high-threshold gated teacher/self ablation: adaptive self-exposure becomes active at realistic thresholds, but still does not beat pure teacher forcing

_Date: 2026-04-23_

## Why this was the next step

The previous gated teacher/self experiment was informative, but too conservative:
- thresholds `0.25` and `0.5` did nothing
- the measured normalized second-step feature gap was much larger, with mean around `2.16`

So the next concrete step was obvious:

> Test gating thresholds on the actual observed gap scale rather than on arbitrary small values.

This moves the gated-teacher/self idea from a null diagnostic to a real exposure-bias experiment.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_gated_teacher_self_high_threshold_ablation.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_high_threshold_ablation/summary.json`
- supporting gap-scale diagnostic from prior step:
  - `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_ablation/feature_gap_seed0_summary.json`

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

Cases:
1. `teacherforced_rollout0p1`
2. `gated_teacher_self_thr1p8`
3. `gated_teacher_self_thr2p0`
4. `gated_teacher_self_thr2p5`

## Aggregated results

### Pure teacher-forced reference
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`
- rollout element-mass MAE @1000: `5.78e-02`

### Gated threshold `1.8`
- one-step species MAE: `7.43e-05`
- one-step temperature MAE: `1.62e-01 K`
- one-step element-mass MAE: `1.42e-04`
- rollout species MAE @1000: `7.43e-02`
- rollout temperature MAE @1000: `7.96e+02 K`

### Gated threshold `2.0`
- one-step species MAE: `9.66e-05`
- one-step temperature MAE: `1.79e-01 K`
- one-step element-mass MAE: `1.77e-04`
- rollout species MAE @1000: `2.07e-01`
- rollout temperature MAE @1000: `2.58e+03 K`

### Gated threshold `2.5`
- one-step species MAE: `3.16e-04`
- one-step temperature MAE: `1.81e-01 K`
- one-step element-mass MAE: `6.36e-04`
- rollout species MAE @1000: `3.79e-01`
- rollout temperature MAE @1000: `4.96e+03 K`

## Main interpretation

### 1. Gating becomes active and meaningful once thresholds match the observed gap scale
Unlike the earlier tiny thresholds, these runs are no longer equivalent to pure teacher forcing.

So this is a real test of the gated-self-exposure idea.

### 2. A low active threshold (`1.8`) gives the most credible gated result
This case is interesting:
- one-step species and element-mass MAE are slightly better than pure teacher forcing
- rollout temperature remains in the same rough regime
- but rollout species still worsens substantially relative to pure teacher forcing

So cautious gating can recover some local-fit benefit, but it still gives up too much rollout quality.

### 3. Larger thresholds degrade quickly
At `2.0` and especially `2.5`, rollout performance collapses toward the same failure pattern seen with other self-exposure strategies.

That is consistent with the broader picture:
- once the training path admits too much self-generated second-step input, instability and degradation return quickly

## What this teaches us

This step improves understanding more than it improves the model.

### The gating idea is not useless, but it still does not beat pure teacher forcing
That matters.

The threshold `1.8` result shows that a realistic, selective gate can produce a qualitatively different tradeoff from pure teacher forcing. But the current best branch is still the pure teacher-forced EFNO setting, because rollout metrics remain better there.

### The useful self-exposure region, if it exists, is narrow
The results suggest something like a cliff:
- too conservative: no self exposure at all
- slightly permissive: some local-fit gains but worse rollout
- more permissive: rapid degradation

That is a strong hint that the present self-generated second-step features are still poorly calibrated for training use.

## Bottom line

This was a productive next step.

It showed that once gating thresholds are chosen on the actual feature-gap scale, the gate becomes active and changes behavior—but even then, the best gated branch does **not** beat pure teacher forcing overall.

So the best current EFNO branch remains the pure teacher-forced two-step model, and the next useful structural work should likely focus on improving or reparameterizing the self-generated second-step feature path itself rather than further threshold tuning.
