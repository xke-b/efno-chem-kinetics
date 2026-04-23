# DFODE-kit smoke-training blocker: constant-feature normalization caused NaNs

_Date: 2026-04-23_

## Context

To check whether the existing DFODE-kit baseline could consume a paper-aligned H2 autoignition dataset, I generated a tiny smoke dataset using the local 7-species / 16-reaction hydrogen mechanism:
- mechanism: `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml`
- state layout: `[T, P, Y..., T_next, P_next, Y_next...]`
- constant-pressure reactor
- `n_init=8`, `steps=10`, `dt=1e-7 s`

## Failure observed

A first smoke training run with the existing DFODE-kit MLP trainer produced `NaN` losses immediately.

## Root cause

The current preprocessing path standardized features with `torch.std(...)` directly. In the smoke dataset, pressure is constant for all samples, so the pressure feature had zero standard deviation. That led to division by zero during normalization and poisoned the training tensors.

## Fix applied in DFODE-kit

In `/opt/src/DFODE-kit/dfode_kit/training/train.py`:
- added `_safe_std(...)`
- switched normalization to use a safe standard deviation with constant columns mapped to `1.0`
- moved the `cantera` import inside `train(...)` to make preprocessing helpers easier to import in lightweight tests

Also added a regression test file:
- `/opt/src/DFODE-kit/tests/test_training_preprocess.py`

## Result after fix

The same smoke training run no longer produced NaNs. A 2-epoch smoke run completed with finite losses.

## Why this matters

This is directly relevant to the EFNO program because paper-aligned autoignition datasets are very likely to contain constant columns depending on reactor assumptions, especially pressure in constant-pressure setups. Without this fix, even baseline reproduction work is brittle.

## Remaining caveat

This only fixes a preprocessing stability issue. It does **not** yet make DFODE-kit paper-faithful for EFNO; FNO/EFNO models, physics-constrained losses aligned to the paper, and rollout evaluation harnesses still need to be added.
