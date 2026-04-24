# C2H4 enthalpy-regularization scout: strengthening the existing enthalpy-consistency term improves corrected `2e-07` offline error substantially, but the deployed branch still distorts bulk heat release badly and fails before `1e-6`

_Date: 2026-04-24_

## Why this was the next step

After the early bulk-divergence localization and the failed scalar activity-regularization scout, the next most justified structured fix was to strengthen the **enthalpy-consistency** term that already exists in the supervised-physics trainer.

This is more physically targeted than a scalar activity penalty and cheaper to test than adding a full heat-release surrogate term.

## Code changes

### DFODE-kit trainer
Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`

Added support for:
- `enthalpy_loss_weight`

The existing `loss3 / 1e13` contribution is now multiplied by a configurable weight.

### Workspace training wrapper
Updated:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Added CLI support for:
- `--enthalpy-loss-weight`

## New training run

### Branch
- alignment-fixed early-window dataset
- intermediate weighting
- attention enabled
- `enthalpy_loss_weight = 10.0`

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_enthalpy10_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_enthalpy10_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_enthalpy10_smoke_baseline/summary.json`

## Offline result

Best validation loss:
- **`0.71378`**

This is worse than the earlier activity-regularized branch (`0.68076`) but still close to the better nearby offline branches.

## Corrected `2e-07` CFD-state vs CVODE result

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_enthalpy10_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

### Comparison against the intermediate-only branch
Intermediate-only:
- MAE: `1.329e-04`
- RMSE: `1.211e-03`
- top 1% predicted `ΔY` L1: `6.03e-02`

Enthalpy-regularized (`10x`):
- MAE: **`5.627e-05`**
- RMSE: **`6.353e-04`**
- top 1% predicted `ΔY` L1: **`4.21e-02`**

This is a clear offline early-slice improvement.

### Channel-level effects at `2e-07`
Relative to the intermediate-only branch:
- `C2H3` MAE improves slightly:
  - `9.68e-06 -> 9.60e-06`
- `OH` MAE improves materially:
  - `3.60e-04 -> 3.15e-04`
- `HO2` MAE improves:
  - `5.70e-07 -> 5.20e-07`
- `CH2CO` gets slightly worse:
  - `2.40e-06 -> 2.50e-06`

So this branch is the first structured regularization scout that genuinely improves the corrected `2e-07` target instead of merely moving tradeoffs around.

## Deployment scout

### Staged case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediateweights_enthalpy10_np8`

### Run result
This branch runs farther than the radical-weighted failure case, with written times through:
- `9e-07`

Then it fails before `1e-6` with:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP)`

So enthalpy weighting improves the branch, but does not yet make it robust enough for the `1e-6` target.

## In-loop comparison at `5e-07`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_vs_cvode_5e-07_summary.json`

### Bulk behavior remains bad
At `5e-7` vs CVODE:
- mean `Qdot` ratio: **`41.4x`**
- mean `|ΔT|`: `3.32 K`
- mean `|Δp|`: `328 Pa`
- strong-`Qdot` sign mismatch fraction: `0.841`

So despite the better corrected `2e-07` one-step behavior, the branch still develops a severe bulk heat-release pathology in-loop.

## Interpretation

This is the first structured-fix result in this neighborhood that is genuinely mixed rather than simply negative.

### What worked
- stronger enthalpy consistency improves the corrected early-slice benchmark substantially
- it reduces early worst-state overreaction
- it is more deployment-viable than the failed radical-weighted branch

### What did not work yet
- the branch still distorts bulk `Qdot` badly in-loop by `5e-7`
- it still fails before `1e-6`

So the main lesson is:

> Enthalpy-aware regularization is a more promising direction than scalar activity matching, but the current simple strengthening of the enthalpy term is still not enough to control the coupled bulk heat-release failure.

## Current takeaway

Among the recent structured fix attempts:
- scalar activity regularization failed
- stronger enthalpy regularization is the first one that clearly helps the corrected early-slice target
- but deployment evidence says it still does not solve the early bulk-heat-release pathology

## Best next step

The next promising direction is now narrower:
- continue with enthalpy/thermo-aware regularization rather than scalar activity penalties
- but combine it with a deployment-facing control near the `3e-7 -> 5e-7` regime where bulk `Qdot` first goes badly wrong
