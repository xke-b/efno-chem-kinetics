# C2H4 one-dimensional DeepFlame augmented FNO: first training and integration smoke

_Date: 2026-04-24_

## Why this was the next step

After building the first Xiao-style interpolation + constrained perturbation augmentation on top of the DeepFlame one-dimensional flame manifold, the next sharp question was simple:

- does this new data path produce a model that can at least survive in the real DeepFlame C2H4 case,
- and if so, what chemistry does it preserve or destroy?

So I took the smallest useful next step:
- label the augmented oneD current-state manifold
- train a first FNO smoke baseline
- export it through the batched DeepFlame bridge
- run the C2H4 case to `1e-6`

## Dataset and model artifacts

Labeled dataset:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_smoke.npy`

Current-state metadata used with it:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_smoke.json`

Training/export summary:
- `/root/workspace/artifacts/experiments/c2h4_oned_deepflame_interp_aug_fno_smoke_baseline/summary.json`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_oned_deepflame_interp_aug_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_oned_deepflame_interp_aug_fno_smoke_deepflame_bundle/`

## Integrated case

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_oned_deepflame_interp_aug_fno_smoke_np8`

Like the other C2H4 deployment smoke tests, this was staged from the known-good `dp100` case template and run in the stock-style `np=8` GPU regime.

## Main runtime result

The first model trained from the Xiao-style augmented oneD DeepFlame manifold **does survive to `1e-6`**.

Written times reached:
- `1e-07`
- `2e-07`
- `3e-07`
- `4e-07`
- `5e-07`
- `6e-07`
- `7e-07`
- `8e-07`
- `9e-07`
- `1e-06`

So this data path is at least solver-usable at the same early horizon where earlier homogeneous-smoke and targeted-semantics failures often collapsed.

## Field analysis at `1e-6`

Artifacts:
- oneD-augmented model:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_oned_deepflame_interp_aug_fno_fields_1e-06_vs_2e-07.json`
- stock baseline reference:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_fields_1e-06_vs_2e-07.json`
- compact comparison summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_oned_deepflame_interp_aug_fno_vs_stock_1e-06_summary.json`

### Thermodynamic/global behavior

Compared with stock at `1e-6`:
- mean temperature difference: `+0.303 K`
- mean pressure difference: `+7.58 Pa`
- mean `Qdot` ratio: **`17.71x` stock**

So the model keeps the bulk thermodynamic state roughly aligned while still over-driving the heat-release source term materially.

### Species behavior

Some bulk channels remain plausible:
- `OH` mean ratio vs stock: `0.85x`
- `CO2` mean ratio vs stock: `1.003x`

But the reactive intermediate manifold is catastrophically suppressed:
- `C2H5` mean ratio vs stock: **`0.0x`**
- `C2H3` mean ratio vs stock: `5.60e-09`
- `CH2CHO` mean ratio vs stock: `7.14e-12`
- `CH2CO` mean ratio vs stock: `8.05e-09`

At `1e-6`, the written fields show:
- `C2H5` mean exactly `0.0`
- `C2H3`, `CH2CHO`, `HCCO`, `CH2CO` all effectively collapsed toward zero

## Interpretation

This is a mixed but important result.

### Positive information
The new data path is **much more viable than a naive reading of “oneD canonical data” would suggest**:
- the model trains
- exports cleanly
- integrates through `1e-6` in the real C2H4 case

So the DeepFlame oneD + Xiao-style augmentation path is not merely a data-manifold curiosity. It can produce a model that survives early deployment.

### Negative information
But the first model trained on this path still learns the wrong chemistry in a very recognizable way:
- bulk thermodynamic fields can look superficially acceptable
- `Qdot` is still too strong
- key intermediates are deleted almost completely

This makes the result scientifically useful because it separates two questions:
1. **Can the oneD-augmented path support early solver survival?**
   - yes
2. **Does the first version yet teach the right reactive intermediate chemistry?**
   - clearly no

## What this means next

The oneD-augmented path is now a credible backbone, but it still needs one or more of the following before it can become a serious deployment candidate:
- better label semantics
- target reformulation for multiscale intermediates
- stronger low-temperature / intermediate-preserving supervision
- or mixture with case-aligned data rather than pure oneD-derived labels

## Current takeaway

The first Xiao-style augmented oneD DeepFlame C2H4 model crosses an important threshold: it survives to `1e-6` in the real case. But it does so while deleting the key intermediate manifold and over-driving `Qdot`, so the next bottleneck is no longer whether the data path can produce a runnable model. It is whether that path can be made chemically faithful enough for useful deployment.
