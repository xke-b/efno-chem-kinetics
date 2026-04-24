# C2H4 proper DeepFlame chemistry baseline at `1e-6`: CVODE confirms the current oneD-backed models are still far from solver-native chemistry fidelity

_Date: 2026-04-24_

## Why this was necessary

Recent C2H4 DeepFlame comparisons had mostly been made against:
- the stock DeepFlame learned example, or
- other learned-model variants.

That was useful for deployment debugging, but it was **not** yet the proper chemistry baseline for a scientific claim. The stronger reference is the same DeepFlame case run with standard chemistry integration rather than a neural surrogate.

So I staged and ran a matched C2H4 reference case with:
- the same stock-style `np=8` decomposition and mesh
- the same Wu24sp mechanism
- `chemistry on`
- `TorchSettings { torch off; }`

This gives a DeepFlame in-loop **CVODE chemistry baseline** for the current `1e-6` horizon.

## Reference case

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_cvode_baseline_np8_stockcopy`

Key configuration change:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_cvode_baseline_np8_stockcopy/constant/CanteraTorchProperties`
  - `torch off`

Control settings for this baseline run:
- start from `0`
- run to `1e-6`
- `deltaT = 1e-7`
- `writeInterval = 1e-7`

Reference field artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_cvode_baseline_np8_fields_1e-06_vs_2e-07.json`

## Practical note

A first fresh-staged CVODE case built from a lighter copy/decompose path failed at startup with a mesh-file lookup error (`Cannot find file "points" in directory "polyMesh" ...`). The reliable workaround was to copy the already working stock-source `np=8` case, retain its processor-mesh structure, clear the post-`0` written times, and then switch `torch` off. That workaround is now the trusted path for this baseline.

## CVODE baseline state at `1e-6`

At `1e-6`, the CVODE case is thermochemically sane and internally consistent:
- total cells: `1,048,576`
- `selectDNN` cells: `0` (as expected; torch disabled)
- mean temperature: `560.75 K`
- mean pressure: `101338.12 Pa`
- mean `Qdot`: `6.06e6`
- species-sum mean absolute deviation from `1`: `1.06e-08`

Selected mean species values at `1e-6`:
- `OH`: `1.394e-4`
- `CO2`: `4.936e-3`
- `C2H5`: `2.124e-7`
- `C2H3`: `1.657e-6`
- `CH2CHO`: `8.285e-8`
- `CH2CO`: `1.354e-6`

These last four species are exactly the intermediate channels the new oneD-backed learned models had been suppressing.

## Matched comparisons against CVODE at `1e-6`

Comparison artifacts:
- stock DeepFlame learned example vs CVODE:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_dnn_vs_cvode_1e-06_summary.json`
  - `/root/workspace/docs/findings/images/c2h4-stock-dnn-vs-cvode-1e-06.png`
- oneD-augmented FNO vs CVODE:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_oned_aug_fno_vs_cvode_1e-06_summary.json`
  - `/root/workspace/docs/findings/images/c2h4-oned-aug-fno-vs-cvode-1e-06.png`
- `dp100 + oneD@0.2` FNO vs CVODE:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_vs_cvode_1e-06_summary.json`
  - `/root/workspace/docs/findings/images/c2h4-dp100-plus-oned-r0p2-vs-cvode-1e-06.png`
- compact multi-model summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_models_vs_cvode_1e-06_compact_summary.json`

For context, I also compared the earlier best current-data mix:
- `dp100 + canonical@0.2` vs CVODE:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_canonical_r0p2_vs_cvode_1e-06_summary.json`
  - `/root/workspace/docs/findings/images/c2h4-dp100-plus-canonical-r0p2-vs-cvode-1e-06.png`

## Main quantitative picture

### 1. The stock DeepFlame learned C2H4 model is much closer to CVODE than the current experimental surrogates

Against CVODE at `1e-6`, the stock learned example gives:
- mean active-region `Qdot` ratio: **`0.476x` CVODE**
- mean active-region `|ΔT|`: **`1.57 K`**
- mean active-region `|Δp|`: **`57.2 Pa`**

Key species mean ratios vs CVODE:
- `C2H5`: **`0.769x`**
- `C2H3`: **`0.671x`**
- `CH2CHO`: **`0.942x`**
- `CH2CO`: **`1.205x`**
- `OH`: **`0.995x`**
- `CO2`: **`1.000x`**

So the stock learned model is not perfect on `Qdot`, but it preserves the crucial intermediate manifold far better than the current project surrogates.

### 2. The pure oneD-augmented FNO is still badly wrong in chemistry space

Against CVODE at `1e-6`, the pure oneD-augmented model gives:
- mean active-region `Qdot` ratio: **`8.44x` CVODE**
- mean active-region `|ΔT|`: **`11.07 K`**
- mean active-region `|Δp|`: **`310.6 Pa`**

Key species mean ratios vs CVODE:
- `C2H5`: **`0.0x`**
- `C2H3`: **`3.75e-09x`**
- `CH2CHO`: **`6.75e-12x`**
- `CH2CO`: **`9.70e-09x`**
- `OH`: `0.846x`
- `CO2`: `1.003x`

This confirms that the earlier stock-relative diagnosis was real: the model keeps bulk products and temperature superficially plausible while effectively deleting the reactive intermediate manifold.

### 3. The first `dp100 + oneD@0.2` mixed-label model does not fix the chemistry problem

Against CVODE at `1e-6`, the mixed model gives:
- mean active-region `Qdot` ratio: **`8.59x` CVODE**
- mean active-region `|ΔT|`: **`3.14 K`**
- mean active-region `|Δp|`: **`103.3 Pa`**

Key species mean ratios vs CVODE:
- `C2H5`: **`1.97e-10x`**
- `C2H3`: **`7.26e-11x`**
- `CH2CHO`: **`3.31e-09x`**
- `CH2CO`: **`7.25e-09x`**
- `OH`: `0.958x`
- `CO2`: `0.999x`

So this mix improves bulk-state closeness relative to the pure oneD-augmented model, but it still does **not** recover the missing intermediate chemistry.

### 4. The earlier `dp100 + canonical@0.2` best mix is also still far from CVODE on the same failure channels

Against CVODE at `1e-6`:
- mean active-region `Qdot` ratio: **`8.00x` CVODE**
- mean active-region `|ΔT|`: **`2.46 K`**
- mean active-region `|Δp|`: **`128.4 Pa`**

Key species mean ratios vs CVODE:
- `C2H5`: **`3.81e-13x`**
- `C2H3`: **`3.60e-09x`**
- `CH2CHO`: **`1.82e-08x`**
- `CH2CO`: **`1.60e-09x`**

So the proper CVODE baseline says the current C2H4 problem is not just a oneD-augmentation problem. It is the broader **intermediate-chemistry semantics / target formulation problem**.

## Interpretation

The main value of this baseline is that it sharpens the evidence chain.

### What is now clear
- comparing only against other learned models was not enough
- the stock DeepFlame learned example is substantially closer to proper in-loop chemistry than the current project surrogates at `1e-6`
- the oneD-backed models do not merely have a mild calibration issue; they are still deleting the reactive intermediate manifold by orders of magnitude
- this failure persists even when temperature, pressure, `OH`, and `CO2` can look superficially acceptable

### What is now less plausible
- “more oneD manifold support alone will fix the deployment problem”
- “early runtime survival implies chemistry quality is already competitive”

## Current takeaway

The proper DeepFlame CVODE baseline confirms that the project’s current C2H4 surrogates remain far from chemistry-faithful in the coupled solver, even when they survive to `1e-6`. The dominant C2H4 gap is now more confidently identified as **target semantics for multiscale intermediate chemistry**, not just solver compatibility or missing current-state support.
