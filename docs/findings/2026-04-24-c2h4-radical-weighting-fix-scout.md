# C2H4 radical-weighting fix scout: adding `OH`/`HO2` emphasis on top of the early-window corrective dataset improves corrected `2e-07` global error and cuts the `OH` overshoot roughly in half, but it badly overdrives `HO2` and does not solve `CH2CO`

_Date: 2026-04-24_

## Why this was the next fix

The previous early-window corrective-data scout showed a useful but incomplete result:
- adding `20k` aligned stock early-window pairs improved the corrected `2e-07` behavior substantially
- but `OH` remained the clearest remaining failure channel

That pointed to the next concrete fix:
- keep the early-window corrective dataset
- add explicit radical-aware weighting for `OH` and `HO2`
- re-check the first divergence slice at `2e-07`

## Code change

Updated:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Added a new species-weight profile:
- `c2h4_intermediates_radicals_v1`

Weights:
- intermediates (`C2H5`, `C2H3`, `CH2CHO`, `CH2CO`, `CH2OH`, `HCCO`): `20x`
- radicals:
  - `OH`: `10x`
  - `HO2`: `10x`

## New training run

### Dataset
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_r0p2_aligned_plus_stockearly20k.npy`

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_radicalweights_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_radicalweights_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_radicalweights_smoke_baseline/summary.json`

### Offline result
Best validation loss:
- **`0.84470`** at epoch `12`

This is **worse** than the early-window branch without radical weighting:
- intermediate-only branch: `0.68569`
- intermediate+radical branch: **`0.84470`**

So offline validation alone would not have recommended this change.

## Corrected `2e-07` CFD-state vs CVODE evaluation

### New artifact
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_radicalweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

### Baseline for comparison
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

## Main result

### Global corrected error improved despite worse offline validation
Intermediate-only early-window branch:
- global MAE: `1.329e-04`
- global RMSE: `1.211e-03`

Intermediate+radical branch:
- global MAE: **`8.614e-05`**
- global RMSE: **`1.112e-03`**

So radical weighting helps the early corrected CFD-state objective even though it hurts held-out validation loss.

## Channel-level effects

### `OH` improved a lot
This was the main goal, and it worked.

Intermediate-only branch:
- `OH` MAE: `3.602e-04`
- predicted mean `ΔOH`: `-3.668e-04`
- true mean `ΔOH`: `-6.675e-06`

Intermediate+radical branch:
- `OH` MAE: **`1.892e-04`**
- predicted mean `ΔOH`: **`-1.959e-04`**
- true mean `ΔOH`: `-6.675e-06`

So the `OH` overshoot was cut by roughly half.

### `C2H3` improved slightly
- MAE:
  - from `9.683e-06`
  - to **`9.526e-06`**
- predicted mean:
  - from `4.045e-07`
  - to **`5.594e-07`**
- truth:
  - `9.992e-06`

Still under-predicted, but directionally improved.

### `C2H5` improved slightly
- MAE:
  - from `8.630e-07`
  - to **`8.101e-07`**

### `CH2CO` got worse again
- MAE:
  - from `2.401e-06`
  - to **`2.586e-06`**
- predicted mean:
  - from `2.473e-07`
  - to **`8.215e-08`**
- truth:
  - `2.646e-06`

This is important: the radical fix did not preserve all intermediate gains.

### `HO2` became severely overdriven
This is the biggest new failure.

Intermediate-only branch:
- `HO2` MAE: `5.704e-07`
- predicted mean `ΔHO2`: `-9.97e-08`
- true mean `ΔHO2`: `4.68e-07`

Intermediate+radical branch:
- `HO2` MAE: **`1.357e-04`**
- predicted mean `ΔHO2`: **`1.362e-04`**
- true mean `ΔHO2`: `4.68e-07`

So the new branch overcompensates badly in `HO2`.

## Interpretation

This is an informative partial failure.

### What worked
- explicit radical weighting can improve the early corrected CFD-state objective
- it materially reduces the `OH` overshoot
- it also slightly helps `C2H3`

### What failed
- it hurts offline validation loss
- it introduces a serious `HO2` overreaction
- it does not solve `CH2CO`

So the current conclusion is not “radical weighting solved the problem.” It is narrower:

> Radical-aware weighting is a real control knob for the early `OH` failure, but the current symmetric `OH`/`HO2` weighting is too blunt and destabilizes `HO2` badly.

## Best next fix

The next most justified step is now more specific than before:
- **keep** the early-window corrective dataset
- keep some explicit `OH` control
- but do **not** weight `HO2` as strongly as `OH`
- and keep explicit support for `CH2CO`

A sensible next profile would likely be:
- keep intermediate weights
- add **moderate `OH` weight only**
- either remove `HO2` weighting or reduce it sharply

That is now the shortest path to testing whether the `OH` improvement can be retained without the severe `HO2` regression.
