# C2H4 Xiao-style augmentation on the DeepFlame one-dimensional manifold: first smoke result

_Date: 2026-04-24_

## Why this was the next step

The previous comparison showed:
- the raw DeepFlame one-dimensional C2H4 sample is the **better physical backbone** than the Cantera-only canonical sample
- but it still suffers from the same flame-front undercoverage problem Xiao et al. (2026) describe
- the Cantera canonical augmentation corrects that imbalance in the right direction, but overshoots too aggressively

So the most useful next step was to build the first **Xiao-style interpolation + constrained perturbation augmentation path directly on top of the DeepFlame one-dimensional HDF5 sample** and then measure whether its manifold moves in the right direction.

## New scripts

Generation:
- `/root/workspace/scripts/generate_c2h4_oned_deepflame_interpolated_augmented_states.py`

Comparison:
- `/root/workspace/scripts/compare_c2h4_current_state_manifolds.py`

## Generated dataset

Current-state smoke dataset:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_smoke.npy`
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_smoke.json`

Settings:
- interpolation temperature step: `10 K`
- target size: `20000`
- perturb copies: `1`
- `alpha_t = 50 K`
- `alpha_p_frac = 0.05`
- `alpha_y = 0.10`
- HRR ratio limit: `50`

Generation summary:
- raw DeepFlame oneD states: `50500`
- interpolated states: `56607`
- accepted augmented states: `20000`
- label attempts / perturb attempts: `32911`
- rejections:
  - `hrr_ratio`: `12911`
  - `max_attempts_exhausted`: `430`

This is a **current-state manifold smoke**, not yet a labeled training dataset.

## Comparison artifacts

JSON:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_current_state_manifold_comparison.json`

Figure:
- `/root/workspace/docs/findings/images/c2h4-current-state-manifold-comparison.png`

Compared manifolds:
- raw oneD DeepFlame sample
- current Cantera canonical sample
- new augmented oneD DeepFlame sample
- stock active C2H4 case states at `5e-6`

## Main result

The first Xiao-style augmentation on the DeepFlame oneD manifold moves the manifold in the **right direction**.

It is the first C2H4 manifold in this project that simultaneously:
- preserves the strong pressure alignment of the DeepFlame oneD backbone
- enriches missing reactive intermediates substantially
- avoids the extreme over-enrichment of the current Cantera-only canonical sample

## Pressure behavior stays case-faithful

### Raw oneD DeepFlame
- mean pressure: `101966.11 Pa`

### Augmented oneD DeepFlame
- mean pressure: `101967.29 Pa`
- p99 pressure: `102021.29 Pa`

### Stock active states
- mean pressure: `101848.44 Pa`

### Cantera canonical sample
- mean pressure: `101325.0 Pa`

Interpretation:
- the augmentation preserves the DeepFlame oneD pressure backbone
- unlike the Cantera-only canonical path, it does not collapse to a fixed 1 atm manifold

## Reactive intermediate coverage improves sharply

Fractions above threshold:

### `C2H5`
- raw oneD: `0.0526`
- augmented oneD: `0.3489`
- stock active: `0.1563`
- canonical Cantera: `0.7271`

### `C2H3`
- raw oneD: `0.0484`
- augmented oneD: `0.3230`
- stock active: `0.2660`
- canonical Cantera: `0.6594`

### `CH2CHO`
- raw oneD: `0.0469`
- augmented oneD: `0.3455`
- stock active: `0.1834`
- canonical Cantera: `0.7271`

### `CH2CO`
- raw oneD: `0.0737`
- augmented oneD: `0.3826`
- stock active: `0.2983`
- canonical Cantera: `0.7778`

Interpretation:
- the augmentation clearly fixes the strongest undercoverage problem of the raw oneD sample
- for these key intermediates, it moves from severe undercoverage to a regime that is much closer to stock
- it still overshoots stock, but much less than the Cantera canonical path

## Major product/reactive-species behavior

### `OH`
- raw oneD: `0.4305`
- augmented oneD: `0.6902`
- stock active: `1.0`
- canonical Cantera: `0.8116`

### `CO`
- raw oneD: `0.4478`
- augmented oneD: `0.7602`
- stock active: `1.0`
- canonical Cantera: `0.9541`

### `CO2`
- raw oneD: `0.4425`
- augmented oneD: `0.7531`
- stock active: `1.0`
- canonical Cantera: `0.9420`

Interpretation:
- the augmentation helps materially here too
- but the manifold is still not as product-rich as the stock active states
- this means the augmentation is improving reactive-zone support without simply collapsing into an over-burnt/product-saturated manifold

## Temperature structure

### Raw oneD DeepFlame
- `T_p50 = 300.56 K`
- mean `T = 1116.66 K`

### Augmented oneD DeepFlame
- `T_p50 = 1566.99 K`
- mean `T = 1381.29 K`

### Stock active states
- `T_p50 = 2460.87 K`
- mean `T = 2312.45 K`

Interpretation:
- the augmentation successfully reweights the manifold away from the cold/unburnt dominance of the raw oneD sample
- but it does not simply become the same as the stock active set, which is expected because the stock active set is already conditioned on `T > 510 K` and late-horizon activity

## What this means

This is a positive result.

It does **not** yet prove that the augmented oneD manifold will train a better deployable model. But it does show that the data-preparation direction is now much sharper:

- raw DeepFlame oneD = good backbone, poor reactive coverage
- Cantera canonical = useful chemistry enrichment, but too aggressive and too detached from the case pressure support
- augmented DeepFlame oneD = a more balanced middle regime

That makes this the most justified current candidate backbone for the next labeled C2H4 experiment.

## Next step

The next concrete step should be:
- label this augmented oneD DeepFlame manifold with one-step chemistry integration
- build a first small training run from it
- compare offline and, if reasonable, deployment behavior against `dp100`, `dp100 + canonical@0.2`, and the current semantics ablations

## Current takeaway

The first Xiao-style augmentation directly on the DeepFlame oneD manifold is scientifically useful and directionally successful. It improves the raw oneD manifold toward the stock reactive set while preserving the better physical backbone that the Cantera-only canonical path lacked.
