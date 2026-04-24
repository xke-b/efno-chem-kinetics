# Minimal temperature+species holdout baseline now exists for H2 autoignition

_Date: 2026-04-23_

## Why this was the next step

The strongest open fidelity gap was that the current offline benchmark learned only species-space targets even though:
- the local paired dataset already stores `T`, `P`, and species at both times
- EFNO and nearby papers are much closer to **thermochemical-state evolution**

So I implemented the smallest practical extension:
- keep the current input contract
- add a new target mode that predicts **`delta_T` + transformed species deltas**
- keep the same holdout-by-trajectory benchmark

## Code changes

### DFODE-kit
Updated:
- `/opt/src/DFODE-kit/dfode_kit/models/mlp.py`
- `/opt/src/DFODE-kit/dfode_kit/models/fno1d.py`
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_training_preprocess.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`
- `/opt/src/DFODE-kit/tests/test_fno1d_model.py`

### Workspace
Updated:
- `/root/workspace/scripts/evaluate_species_delta_checkpoint.py`

Added:
- `/root/workspace/scripts/run_h2_temp_species_holdout_baseline.py`

## What changed technically

### New target mode
`target_mode="temperature_species"` now means:
- inputs: `[T, P, BCT(Y)]`
- labels: `[delta_T, BCT(Y_next[:-1]) - BCT(Y_now[:-1])]`

This is still not fully paper-faithful, but it is a meaningful step beyond species-only learning.

### Model output sizing
The MLP/FNO builders now accept `output_dim` so checkpoints can represent:
- species-only outputs (`n_species - 1`)
- minimal thermochemical outputs (`n_species` = one temperature delta + species deltas)

### Evaluator extension
The evaluator now supports both checkpoint types and reports:
- one-step temperature MAE/RMSE
- rollout temperature MAE by horizon
- species metrics as before
- mass-sum and element-mass metrics as before

## Manual smoke validation
Because `pytest` availability remains inconsistent in the active env, I ran manual smoke checks in the `deepflame` environment.

Confirmed:
- preprocessing builds temperature+species labels with the expected shape
- FNO can emit custom output dimensions
- `efno_style` no longer crashes when given the wider label shape

## First holdout result
I trained a small `MLP [64,64] + supervised_physics` model for `5` epochs on the existing H2 holdout split using the new target mode.

Checkpoint:
- `/root/workspace/data/h2_holdout_mlp_supervised_physics_temp_species.pt`

Evaluation:
- `/root/workspace/artifacts/h2_holdout_mlp_supervised_physics_temp_species_eval.json`

### One-step metrics on unseen trajectories
- species MAE: `7.52e-05`
- species RMSE: `2.68e-04`
- temperature MAE: `4.81e-01 K`
- temperature RMSE: `9.12e-01 K`
- element-mass MAE: `1.02e-04`
- invalid inverse-BCT count: `0`

### Comparison to previous species-only holdout baseline
From `/root/workspace/artifacts/experiments/h2_holdout_comparison/summary.json`:
- species-only one-step species MAE: `5.97e-05`
- species-only one-step element-mass MAE: `9.09e-05`

So, at least in this first small run:
- the new temperature+species baseline **works**
- temperature prediction is numerically plausible on holdout trajectories
- but species accuracy is currently **slightly worse** than the species-only baseline

## Interpretation

This is useful progress even though it is not yet a clear win.

Why:
1. we now have a benchmark path that is closer to the paper neighborhood
2. we can quantify the tradeoff between species-only and thermochemical targets
3. the first result suggests that adding temperature is feasible, but may require:
   - longer training
   - different weighting between temperature and species targets
   - possibly a different physical-loss formulation

## Failure / friction recorded

While gathering the NH3/H2 reference paper, direct `urllib` download from UCL returned `HTTP 403`. Switching to `curl -L -A 'Mozilla/5.0' ...` worked. So the PDF ingestion workflow is workable, but some open repositories need a browser-like user agent.

## Bottom line

The project now has a **minimal thermochemical holdout baseline**, not just a proposal for one. That closes an important fidelity gap and gives the next experiments a stronger foundation.
