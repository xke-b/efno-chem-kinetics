# C2H4 FNO vs stock pre-failure comparison at `8e-7`: the first integrated FNO case fails thermodynamically before it fails chemically on-simplex

_Date: 2026-04-24_

## Why this was the next step

After the first C2H4 FNO-integrated case reached `9e-7` and then failed during the `1e-6` attempt, the most useful follow-up was to inspect the last successful written state and compare it directly against the trusted stock C2H4 baseline at the same horizon.

The immediate goal was to answer a narrower question:
- is the pre-failure pathology mainly a species-simplex breakdown, or mainly a thermodynamic/state-evolution problem?

## Important tooling note

The first attempt to run the C2H4 field analyzer failed because it handled `uniform` OpenFOAM fields incorrectly. Some written fields like `selectDNN` or rare species channels are stored as `uniform 0;`, and the older parser could accidentally latch onto an unrelated integer later in the file and fabricate the wrong cell count.

I fixed that parser in:
- `/root/workspace/scripts/analyze_deepflame_c2h4_smoke_fields.py`

The fix is simple and important:
- for `uniform` fields, use the known fallback cell count from `T`
- do **not** try to infer a count by scanning arbitrary standalone integers elsewhere in the file

That failed attempt was therefore useful diagnosis, not dead work.

## Cases compared

### FNO-integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_fno_smoke_integration`

### Trusted stock baseline
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`

Comparison horizon:
- main comparison time: `8e-7`
- reference time for within-case drift: `5e-7`

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_fno_smoke_integration_fields_8e-07_vs_5e-07.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_fields_8e-07_vs_5e-07.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_fno_vs_stock_8e-07_comparison.json`

## Main result

At `8e-7`, the FNO-integrated case is still tightly on-simplex but is already thermodynamically far less healthy than stock.

### Species-simplex closure stays tight in both cases
FNO-integrated at `8e-7`:
- species-sum mean absolute deviation from `1`: `1.14e-08`
- species-sum max absolute deviation from `1`: `1.40e-06`

Stock at `8e-7`:
- species-sum mean absolute deviation from `1`: `7.14e-09`
- species-sum max absolute deviation from `1`: `1.10e-06`

So the FNO-integrated case is **not** failing first because of gross mass-fraction simplex collapse.

## Thermodynamic contrast is much sharper

### Temperature
FNO-integrated at `8e-7`:
- `T_min = 235.021 K`
- `T_max = 1845.63 K`
- `T_mean = 500.52 K`
- mean `|ΔT|` from `5e-7` to `8e-7`: `53.82 K`
- largest `|ΔT|` from `5e-7` to `8e-7`: `1901.99 K`

Stock at `8e-7`:
- `T_min = 499.886 K`
- `T_max = 2461.85 K`
- `T_mean = 560.87 K`
- mean `|ΔT|` from `5e-7` to `8e-7`: `0.261 K`
- largest `|ΔT|` from `5e-7` to `8e-7`: `235.44 K`

The strongest visible pre-failure signal is therefore a severe cold-tail / thermodynamic-drift pathology in the FNO-integrated case that is absent from stock.

### Pressure
FNO-integrated at `8e-7`:
- `p_min = 68387.8 Pa`
- `p_max = 128587 Pa`
- `p_mean = 100431 Pa`

Stock at `8e-7`:
- `p_min = 101182 Pa`
- `p_max = 102386 Pa`
- `p_mean = 101340 Pa`

So the FNO-integrated case also develops a much broader pressure spread than stock by the same horizon.

### Heat release / source behavior
FNO-integrated at `8e-7`:
- `Qdot_mean = -8.16e9`
- mean `|ΔQdot|` from `5e-7`: `1.19e10`

Stock at `8e-7`:
- `Qdot_mean = 1.54e6`
- mean `|ΔQdot|` from `5e-7`: `1.82e7`

So the FNO-integrated case is not just thermally noisier; it is in a qualitatively different source-term regime.

## Chemical-state interpretation

The FNO-integrated case looks chemically underdeveloped / quenched relative to stock by `8e-7`.

Selected mean species values at `8e-7`:

- `OH`
  - FNO: `1.03e-07`
  - stock: `1.39e-04`
- `H2O`
  - FNO: `1.57e-07`
  - stock: `2.35e-03`
- `CO`
  - FNO: `6.85e-06`
  - stock: `8.03e-04`
- `CO2`
  - FNO: `2.02e-03`
  - stock: `4.95e-03`
- `O2`
  - FNO: `0.21139`
  - stock: `0.21185`
- `H2`
  - FNO: `6.68e-03`
  - stock: `1.10e-05`

This suggests the learned chemistry is not driving the case into a hot, over-reactive blow-up. Instead, it appears too chemically weak / misaligned in a way that leaves the state colder, less product-rich, and more thermodynamically inconsistent under HP reconstruction.

## Interpretation

The best current reading is:
1. the first integrated C2H4 FNO case survives the wiring/runtime barrier
2. it also preserves species-simplex geometry reasonably well
3. but it drifts into a thermodynamically unhealthy, chemically underdeveloped state long before the stock baseline does
4. the eventual HP reconstruction crash near `1e-6` is therefore consistent with a **state-trajectory fidelity problem**, not just a species postprocessing problem

## Most useful next step

The higher-value next intervention is now clearer:
- prioritize a more case-relevant C2H4 training dataset over further polishing of this tiny homogeneous smoke model

A guarded fallback prototype could still be useful later, but this comparison suggests the deeper bottleneck is the training-data / state-distribution mismatch rather than a simple postprocessing bug.
