# DeepFlame C2H4 stock-field analysis: the 2-rank stock learned baseline remains thermochemically well-behaved through `5e-6`, with tight species-simplex closure and no obvious low-temperature failure signature in written fields

_Date: 2026-04-23_

## Why this was the next step

After establishing that the stock C2H4 PyTorch example is viable at `2` ranks through `5e-6`, the next useful question was whether the written fields already show any obvious pathology before pushing the horizon further.

## Case analyzed

- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np2`
- analysis script:
  - `/root/workspace/scripts/analyze_deepflame_c2h4_smoke_fields.py`
- artifacts:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_fields_2e-06_vs_1e-06.json`
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_fields_5e-06_vs_1e-06.json`
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_field_comparison_summary.json`
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_5e-6_summary.json`

## Horizon update

After the initial field inspection through `5e-6`, I extended the same `2`-rank stock case further to `1e-5`, and then again to `2e-5`.
That CPU-path continuation sequence completed successfully:
- last written CPU-path time: `2e-05`
- total CPU-path time steps completed in the staged run: `200`
- CPU-path DNN-active steps completed: `199`
- observed CPU-path per-rank inference counts ranged from `16754` to `19257`
- latest observed CPU-path per-rank inference counts at `2e-05`: `19257` and `18108`
- `solver.err` remained empty on the successful CPU-path run

I then tested the same `2`-rank stock baseline with **GPU inference enabled**, following the stock DeepFlame C2H4 example pattern (`GPU on` in `TorchSettings`).
That GPU-path continuation reached much farther before failing:
- last written GPU-path time: `4.11e-05`
- last attempted GPU-path time in the log: `4.12e-05`
- total GPU-path time steps observed in the copied continuation log: `413`
- GPU-path DNN-active steps observed: `411`
- observed GPU-path per-rank inference counts ranged from `16754` to `21471`
- latest observed per-rank inference counts near failure: `21471` and `19100`
- failure mode changed from CPU-path kill (`137`) to a **GPU-path segmentation fault** in DeepFlame `solve_DNN`, with the stack trace pointing into `libdfCombustionModels.so`

Additional artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_1e-5_comparison_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_2e-5_comparison_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_failure_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_fields_4.11e-05_vs_2e-05.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_cpu_vs_gpu_long_horizon_summary.json`

## Main findings

### 1. The written species fields remain extremely well behaved

At `5e-6`:
- total cells analyzed: `1,048,576`
- species-sum mean: `1.0000000006895884`
- species-sum mean absolute deviation from `1`: `1.092979319030453e-08`
- species-sum max absolute deviation from `1`: `1.1053100000824045e-06`

No species showed:
- negative mass fractions
- mass fractions above `1`

At `1e-5`:
- species-sum mean: `0.9999999991414776`
- species-sum mean absolute deviation from `1`: `1.1749024431802775e-08`
- species-sum max absolute deviation from `1`: `1.0660597433709285e-06`

At `2e-5` on the CPU path:
- species-sum mean: `1.000000000749895`
- species-sum mean absolute deviation from `1`: `1.2759645492948875e-08`
- species-sum max absolute deviation from `1`: `1.087301999991297e-06`

At `4.11e-5` on the GPU path, just before the crash:
- species-sum mean: `1.0000000015057715`
- species-sum mean absolute deviation from `1`: `1.5079995284184247e-08`
- species-sum max absolute deviation from `1`: `1.0922737343488365e-06`

So the stock C2H4 learned baseline is not showing the kind of species-simplex failure that would immediately disqualify it as a usable reference case, even near the GPU-path crash point.

### 2. The written temperature field looks stable over this horizon

At `2e-6`:
- `T_min = 499.566 K`
- `T_max = 2463.09 K`
- `T_mean = 560.5205 K`

At `5e-6`:
- `T_min = 499.207 K`
- `T_max = 2462.81 K`
- `T_mean = 560.1405 K`

At `1e-5`:
- `T_min = 499.254 K`
- `T_max = 2462.5 K`
- `T_mean = 560.0667 K`

At `2e-5` on the CPU path:
- `T_min = 499.343 K`
- `T_max = 2461.31 K`
- `T_mean = 560.5770 K`

At `4.11e-5` on the GPU path:
- `T_min = 499.509 K`
- `T_max = 2459.04 K`
- `T_mean = 562.7515 K`

Interpretation:
- the minimum temperature stays close to the nominal cold-side initialization near `500 K`
- there is no H2-like written-field evidence here of rare catastrophic cold cells collapsing to implausible temperatures
- peak temperatures remain in a similar physical range even near the GPU-path crash point

### 3. The heat-release field remains active but not obviously unstable in the written snapshots

At `2e-6`:
- `Qdot_min = -1.39756e8`
- `Qdot_max = 7.14212e9`
- `Qdot_mean = 8.120119e6`

At `5e-6`:
- `Qdot_min = -1.70653e8`
- `Qdot_max = 6.94517e9`
- `Qdot_mean = 1.6212188e7`

At `1e-5`:
- `Qdot_min = -1.91711e7`
- `Qdot_max = 7.06910e9`
- `Qdot_mean = 2.0136284e7`

At `2e-5` on the CPU path:
- `Qdot_min = -3.24028e7`
- `Qdot_max = 7.76358e9`
- `Qdot_mean = 2.4660733e7`

At `4.11e-5` on the GPU path:
- `Qdot_min = -5.81404e6`
- `Qdot_max = 9.31180e9`
- `Qdot_mean = 3.0881408e7`

So the learned run is not becoming obviously quiescent; it still carries a strong reacting structure while remaining thermochemically plausible in the written fields even near the GPU-path crash point.

### 4. Bulk composition means are nearly unchanged between `2e-6` and `5e-6`

Selected mean mass fractions:

At `2e-6`:
- `O2`: `0.2118925`
- `H2O`: `0.00233561`
- `CO2`: `0.00491133`
- `C2H4`: `0.06177433`
- `N2`: `0.71810261`

At `5e-6`:
- `O2`: `0.21193256`
- `H2O`: `0.00231869`
- `CO2`: `0.00486783`
- `C2H4`: `0.06177491`
- `N2`: `0.71810242`

These changes are small, which is consistent with a short-horizon smoke run that remains physically coherent rather than rapidly drifting.

### 5. `selectDNN` is again not a trustworthy written-field activity indicator here

The written `selectDNN` field is uniformly zero in the analyzed snapshots:
- unique values: `[0.0]`

But the solver log clearly shows active learned inference from `2e-7` onward, with per-rank inference counts in the `~1.68e4` to `~1.75e4` range.

So, as in the earlier H2 work, the written `selectDNN` field should not currently be used as the authoritative indicator of where the learned path was actually active.

## What this changes

This improves the C2H4 readiness picture in two ways:

1. The stock C2H4 PyTorch example now has a real workspace-local smoke baseline that is not only runnable at `2` ranks, but also looks physically sane in written fields through `2e-5` on CPU and through `4.11e-5` on the GPU-enabled path.
2. The next uncertainty is now narrower and more backend-specific: the CPU path eventually hard-kills, while the GPU path reaches much farther but segfaults inside DeepFlame `solve_DNN` rather than showing a clear thermochemical field pathology.

## Most useful next step

Diagnose the GPU-path failure mode around `4.12e-5` as a DeepFlame runtime / communication issue first, rather than treating it as a chemistry-state failure. In parallel, keep the successful pre-crash GPU-path written fields as the current longest viable stock C2H4 baseline evidence.
