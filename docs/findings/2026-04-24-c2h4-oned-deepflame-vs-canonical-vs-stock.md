# C2H4 one-dimensional DeepFlame sample vs Cantera canonical sample vs stock active states

_Date: 2026-04-24_

## Why this was the next step

After confirming that DFODE-kit’s documented one-dimensional DeepFlame sampling path works for C2H4, the immediate question was whether that sampled manifold is actually a better starting point than the earlier Cantera-only canonical generator.

The most useful first comparison was therefore:
- raw DeepFlame oneD sampled manifold
- current Cantera canonical/interpolation/perturbation smoke manifold
- stock active C2H4 case states at `5e-6`

The point was not yet to train another model, but to determine which manifold is misaligned in which direction.

## Script and artifacts

Script:
- `/root/workspace/scripts/compare_c2h4_oned_sample_to_canonical_and_stock.py`

Artifacts:
- JSON:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_oned_deepflame_vs_canonical_vs_stock.json`
- figure:
  - `/root/workspace/docs/findings/images/c2h4-oned-deepflame-vs-canonical-vs-stock.png`

Inputs:
- oneD DeepFlame sample:
  - `/root/workspace/data/c2h4_dfode_oned_phi1_sample.h5`
- Cantera canonical smoke dataset:
  - `/root/workspace/data/c2h4_canonical_interp_aug_smoke.npy`
  - `/root/workspace/data/c2h4_canonical_interp_aug_smoke.json`
- stock active reference states:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`
  - active snapshot time: `5e-6`

## Main result

The comparison shows a useful three-way structure:

1. **Raw DeepFlame oneD sampling is much more pressure-aligned to the stock case than the Cantera-only canonical manifold.**
2. **Raw DeepFlame oneD sampling still under-covers the intermediate-rich reactive manifold needed by the stock active set.**
3. **The Cantera canonical manifold over-corrects in the opposite direction, strongly over-enriching intermediates/products relative to stock.**

So the current evidence suggests that the best future data path is likely not:
- raw oneD DeepFlame sample alone, or
- raw canonical augmentation alone,

but rather a **Xiao-style augmentation of the DeepFlame oneD sample**.

## Pressure alignment

### DeepFlame oneD sample
- pressure mean: `101966.11 Pa`
- pressure p99: `102011.0 Pa`

### Stock active states at `5e-6`
- pressure mean: `101848.44 Pa`
- pressure p99: `101997.0 Pa`

### Cantera canonical sample
- pressure mean: `101325.0 Pa`
- pressure is effectively constant at 1 atm

Interpretation:
- the DeepFlame oneD sample is far more case-like in pressure support than the Cantera canonical manifold
- that is a real advantage for deployment-facing usefulness

## Temperature structure

### DeepFlame oneD sample
- `T_min = 299.94 K`
- `T_p50 = 300.56 K`
- `T_p99 = 2379.77 K`
- mean `T = 1116.66 K`

### Stock active states
- `T_min = 510.03 K`
- `T_p50 = 2460.87 K`
- `T_p99 = 2462.03 K`
- mean `T = 2312.45 K`

### Cantera canonical sample
- `T_min = 290.0 K`
- `T_p50 = 1349.52 K`
- `T_p99 = 2372.92 K`
- mean `T = 1326.53 K`

Interpretation:
- the raw oneD DeepFlame sample is dominated by cold/unburnt states
- this mirrors Xiao’s data-imbalance motivation almost exactly: the raw one-dimensional manifold needs balancing/interpolation/augmentation if it is going to represent the reactive zone well

## Intermediate-species coverage

### Stock active states at `5e-6`
Fractions above threshold:
- `C2H5`: `0.1563`
- `C2H3`: `0.2660`
- `CH2CHO`: `0.1834`
- `CH2CO`: `0.2983`

### Raw DeepFlame oneD sample
Fractions above threshold:
- `C2H5`: `0.0526`
- `C2H3`: `0.0484`
- `CH2CHO`: `0.0469`
- `CH2CO`: `0.0737`

### Cantera canonical sample
Fractions above threshold:
- `C2H5`: `0.7271`
- `C2H3`: `0.6594`
- `CH2CHO`: `0.7271`
- `CH2CO`: `0.7778`

Interpretation:
- raw oneD DeepFlame sampling is **too sparse** in the reactive intermediate manifold
- the current Cantera canonical generator is **too aggressive** in the opposite direction
- stock lies between them

This is exactly the kind of gap that Xiao-style interpolation plus constrained perturbation is meant to address.

## Major species and products

For `OH`, `CO`, and `CO2`, the same pattern appears:

### DeepFlame oneD sample
- `OH` threshold fraction: `0.4305`
- `CO` threshold fraction: `0.4478`
- `CO2` threshold fraction: `0.4425`

### Stock active states
- `OH`: `1.0`
- `CO`: `1.0`
- `CO2`: `1.0`

### Cantera canonical sample
- `OH`: `0.8116`
- `CO`: `0.9541`
- `CO2`: `0.9420`

Interpretation:
- raw oneD DeepFlame sampling still underrepresents active product-rich states
- canonical augmentation pushes much closer to fully reacted support, but likely overshoots for current deployment needs

## What this changes

This comparison substantially sharpens the next C2H4 data-preparation step.

### Before
The main intuition was:
- Cantera canonical data helps chemistry coverage
- DeepFlame oneD data is more faithful to the actual solver path

### After
We can say something stronger:
- **DeepFlame oneD sampling gives the better physical backbone**
- **but it needs reactive-zone densification**
- **the current Cantera canonical generator shows roughly the right direction of correction, but too much of it**

So the next justified experiment is:
- build a **Xiao-style interpolation + perturbation augmentation path on top of the DeepFlame oneD HDF5 sample**, not only on top of the Cantera canonical flame

## Current takeaway

The current best interpretation is:
- raw DeepFlame oneD sampling is more case-faithful than the Cantera-only canonical sample,
- but it inherits exactly the reactive-zone imbalance problem Xiao et al. describe,
- while the current Cantera canonical augmentation overcompensates.

That makes the DeepFlame oneD HDF5 sample a strong candidate backbone for the next C2H4 data-generation iteration.
