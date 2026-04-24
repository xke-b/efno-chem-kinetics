# Holdout H2 comparison: on unseen trajectories, baseline supervised_physics remains better than the current EFNO-style trainer

_Date: 2026-04-23_

## Why this step was necessary

After the longer-horizon probe showed that the earlier small comparison dataset was too easy, the next obvious risk was still **same-dataset evaluation**. Training and evaluating on the same trajectories can hide generalization failures.

So the next concrete step was to enforce a **holdout split by initial-condition trajectory**.

## Setup

Source dataset:
- `/root/workspace/data/h2_autoignition_longprobe.npy`
- `16` initial-condition trajectories
- `1000` steps each
- constant-pressure reactor
- mechanism: `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml`

Split strategy:
- train trajectories: `0..11`
- holdout trajectories: `12..15`

Generated split files:
- train: `/root/workspace/data/h2_autoignition_longprobe_train.npy`
- test: `/root/workspace/data/h2_autoignition_longprobe_test.npy`

## Models compared

Backbone for both runs:
- MLP with hidden layers `[64, 64]`

Trainer variants:
1. `supervised_physics`
2. `efno_style`

Both trained for 10 epochs.

## Main result

### One-step performance on unseen trajectories
- `supervised_physics`
  - species MAE: `6.66e-05`
  - element-mass MAE: `1.09e-04`
- `efno_style`
  - species MAE: `4.10e-04`
  - element-mass MAE: `8.43e-04`

So the current `efno_style` trainer is **substantially worse** than the baseline on one-step generalization to unseen trajectories.

### Rollout behavior on unseen trajectories
The gap persists under rollout:
- `supervised_physics` remains meaningfully better than `efno_style`
- `efno_style` still accumulates larger errors earlier
- `efno_style` does not currently justify itself as an improvement

## Important interpretation

This is strong and useful negative evidence.

It means:
1. the earlier smoke improvement of `efno_style` was not robust
2. the longer and holdout-aware benchmark is much more trustworthy
3. our current EFNO-style weighting/conservation formulation is still under-tuned or mis-specified for this H2 benchmark

## Why this is progress

This result narrows the search space.

It suggests that the next useful work should focus on **diagnosis**, not blind scaling:
- inspect the weight distribution induced by the quartile rule
- inspect inverse-BCT clipping / invalid-state formation
- tune `lambda_data`, `lambda_elements`, `lambda_mass`
- consider whether the current species-only target is undermining the intended physical-loss design

## New durable artifact

To make this comparison reproducible, I added:
- `scripts/run_h2_holdout_comparison.py`

This provides a repeatable train/holdout experiment scaffold.

## Related artifacts

- experiment summary: `/root/workspace/artifacts/experiments/h2_holdout_comparison/summary.json`
- baseline holdout eval: `/root/workspace/artifacts/experiments/h2_holdout_comparison/baseline_holdout_eval.json`
- efno-style holdout eval: `/root/workspace/artifacts/experiments/h2_holdout_comparison/efno_holdout_eval.json`

## Bottom line

On a more meaningful H2 benchmark with unseen initial-condition trajectories, the current `efno_style` trainer is **not yet an improvement** over the existing baseline. That is exactly the kind of information a serious reproduction program needs.
