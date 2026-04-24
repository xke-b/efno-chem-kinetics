# Full batched C2H4 case-aligned FNO vs stock at `5e-6`: runtime pathology is largely fixed, but the learned chemistry still departs materially from stock source terms and late intermediates

_Date: 2026-04-24_

## Why this was the next step

After the full start-to-`5e-6` batched-bridge C2H4 FNO run completed without CUDA OOM, the next useful question became narrower and more scientific:
- with the runtime pathology largely repaired, how close is the full batched case-aligned FNO run to the trusted stock baseline at `5e-6`?

That comparison is necessary to separate:
- bridge/runtime correctness
from
- remaining model-quality limitations.

## Compared cases

### Full batched case-aligned FNO run
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_fno_integration_batched_full`

### Trusted stock baseline
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`

Comparison horizon:
- main time: `5e-6`
- reference time for within-case drift: `2e-6`

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_fno_integration_batched_full_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_fno_batched_full_vs_stock_5e-06.json`

## Main result

The full batched run now looks much healthier as a runtime artifact than the earlier unbatched path, but it still departs materially from stock in thermochemical behavior.

## What is now healthy

### Species-simplex closure remains tight
Full batched FNO at `5e-6`:
- mean abs species-sum deviation from `1`: `2.34e-08`
- max abs species-sum deviation from `1`: `1.47e-06`

Stock at `5e-6`:
- mean abs species-sum deviation from `1`: `1.03e-08`
- max abs species-sum deviation from `1`: `1.06e-06`

So gross species geometry is no longer the main issue.

### No catastrophic cold-tail pathology
Full batched FNO:
- `T_min = 499.158 K`
- `T_max = 2547.76 K`
- `T_mean = 566.54 K`

Stock:
- `T_min = 499.249 K`
- `T_max = 2462.06 K`
- `T_mean = 560.11 K`

So the full batched FNO run is somewhat hotter on average and reaches a higher peak temperature, but it no longer shows the earlier catastrophic low-temperature collapse.

## Remaining thermochemical gap

### Temperature drift is still larger than stock
Mean `|ΔT|` from `2e-6` to `5e-6`:
- full batched FNO: `5.35 K`
- stock: `0.83 K`

So even with the bridge fixed, the learned run still drifts more than stock over the same window.

### Pressure range is much broader
Full batched FNO:
- `p_min = 100659 Pa`
- `p_max = 140676 Pa`
- `p_mean = 102359 Pa`

Stock:
- `p_min = 100657 Pa`
- `p_max = 102000 Pa`
- `p_mean = 101347 Pa`

The mean pressure difference is modest (`≈ 1.01 kPa`), but the **upper tail is much broader** in the learned run.

### Heat-release behavior is still far from stock
Full batched FNO:
- `Qdot_min = -1.84e9`
- `Qdot_max = 1.87e11`
- `Qdot_mean = 1.44582e9`

Stock:
- `Qdot_min = -1.67e8`
- `Qdot_max = 6.93e9`
- `Qdot_mean = 1.62e7`

So the full batched FNO no longer has the broken zero-`Qdot` pathology, but its heat-release scale is still much too large:
- mean `Qdot` is about **89x stock**

This is the clearest remaining quantitative gap.

## Species-level interpretation

Selected mean species at `5e-6`:

- `H2`
  - full batched FNO: `5.49e-05`
  - stock: `1.16e-05`
  - ratio: `4.73x`
- `O2`
  - full: `0.21360`
  - stock: `0.21193`
  - ratio: `1.008x`
- `OH`
  - full: `1.79e-04`
  - stock: `1.34e-04`
  - ratio: `1.33x`
- `H2O`
  - full: `3.37e-03`
  - stock: `2.32e-03`
  - ratio: `1.45x`
- `CO`
  - full: `4.63e-04`
  - stock: `8.11e-04`
  - ratio: `0.57x`
- `CO2`
  - full: `4.04e-03`
  - stock: `4.87e-03`
  - ratio: `0.83x`
- `C2H4`
  - full: `0.06019`
  - stock: `0.06178`
  - ratio: `0.974x`

Late intermediates/products remain especially underrepresented in the learned run:
- `C2H5`
  - full: `2.62e-22`
  - stock: `5.07e-07`
- `C2H3`
  - full: `0.0`
  - stock: `1.95e-06`
- `CH2CHO`
  - full: `8.93e-16`
  - stock: `2.23e-07`
- `CH2CO`
  - full: `1.61e-17`
  - stock: `7.11e-06`

So the learned run is not merely a uniformly scaled version of stock chemistry. It appears to overstate some broad hot/reactive quantities while still suppressing several late intermediate channels.

## Interpretation

The picture is now much clearer than before.

### What appears fixed
- the runtime bridge pathology that caused late CUDA OOM and zero-`Qdot`
- the catastrophic short-horizon collapse seen in the homogeneous-smoke FNO path

### What remains
- the learned chemistry still does not match stock source-term behavior closely
- the learned run still develops a broader pressure tail
- important intermediate/product channels remain strongly underpredicted

So the dominant remaining bottleneck now looks like **model/data-target quality**, not basic runtime integration.

## Best current conclusion

The project has now crossed two important barriers for C2H4:
1. case-aligned data made the FNO path solver-usable through the target horizon
2. batched inference made the runtime bridge robust enough for that horizon

After those fixes, the remaining gap is now much more credibly attributable to the learned surrogate itself and the limitations of the current CFD-state-pair target construction.

## Most useful next step

Move from runtime repair to target-quality repair: the next high-value step is to improve the case-aligned C2H4 labels beyond crude full-CFD state pairs, or at least train/evaluate variants that explicitly account for the current over-energetic source-term behavior and missing late intermediates.
