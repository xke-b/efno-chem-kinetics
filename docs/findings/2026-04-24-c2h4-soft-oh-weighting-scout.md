# C2H4 soft-OH weighting scout: a weaker `OH` weight avoids the catastrophic instability of strong OH-only weighting and preserves `HO2`, but it does not improve corrected `2e-07` error over the better nearby branches

_Date: 2026-04-24_

## Why this was the next step

The nearby fix sweep had already shown:
- **intermediate + `OH` + `HO2`** improved corrected global error but catastrophically over-drove `HO2`
- **intermediate + `OH` only** fixed `OH` very well but destabilized the full update badly

So the next justified move was a softer variant:
- keep the early-window corrective dataset
- keep intermediate weighting
- add only a **small `OH` weight**
- leave `HO2` unweighted

## Code change

Updated:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Added profile:
- `c2h4_intermediates_ohsoft_v1`

Weights:
- intermediates: `20x`
- `OH`: `3x`
- `HO2`: baseline

## New training run

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohsoftweights_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohsoftweights_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohsoftweights_smoke_baseline/summary.json`

### Offline result
Best validation loss:
- **`0.72639`**

This is much better than the stronger radical-weighted nearby variants:
- `OH+HO2`: `0.84470`
- strong `OH` only: `0.80210`

It is also close to the earlier intermediate-only branch:
- intermediate-only: `0.68569`

So offline, the soft-`OH` branch looks much more reasonable than the stronger radical variants.

## Corrected `2e-07` CFD-state vs CVODE result

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohsoftweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

## Main result

This branch is **not a breakthrough**, but it is informative.

### Global metrics
- soft `OH` branch:
  - MAE: **`1.033e-04`**
  - RMSE: **`1.271e-03`**

Compared with nearby branches:
- intermediate-only:
  - MAE `1.329e-04`, RMSE `1.211e-03`
- `OH+HO2`:
  - MAE `8.614e-05`, RMSE `1.112e-03`
- strong `OH` only:
  - MAE `3.369e-04`, RMSE `7.559e-03`

So the soft-`OH` branch:
- improves MAE over the intermediate-only baseline
- avoids the catastrophic instability of strong `OH` weighting
- but does **not** beat the better global `OH+HO2` branch
- and slightly worsens RMSE relative to the intermediate-only branch

### Worst-state behavior
Top 1% worst states:
- soft `OH` predicted `ΔY` L1 mean: **`8.42e-02`**
- intermediate-only: `6.03e-02`
- strong `OH` only: `4.37e-01`

So the soft-`OH` version is much safer than strong `OH` weighting, but still not clearly better than the intermediate-only branch in worst-state behavior.

## Channel-level behavior

### `OH`
- intermediate-only `OH` MAE: `3.602e-04`
- soft `OH` MAE: **`3.420e-04`**
- strong `OH` only `OH` MAE: `1.769e-05`

So soft `OH` weighting helps `OH` only modestly.

### `HO2`
- soft `OH` `HO2` MAE: `6.163e-07`
- predicted mean `ΔHO2`: `3.318e-07`
- true mean `ΔHO2`: `4.682e-07`

This is good news: unlike the `OH+HO2` branch, `HO2` remains controlled.

### `CH2CO`
- intermediate-only `CH2CO` MAE: `2.401e-06`
- soft `OH` `CH2CO` MAE: **`2.349e-06`**

A small improvement here.

### `C2H3`
- intermediate-only `C2H3` MAE: `9.683e-06`
- soft `OH` `C2H3` MAE: **`1.007e-05`**

This gets slightly worse.

## Interpretation

This is a useful narrowing result.

### What it shows
- a **small** `OH` weight is much safer than a large one
- it avoids the catastrophic failure mode of strong `OH`-only weighting
- it also avoids the `HO2` explosion caused by explicit `HO2` weighting
- but it does not produce a clear across-the-board win over the better nearby branches

### Current tradeoff summary
- **intermediate-only**: best balanced baseline so far
- **soft `OH`**: safer radical tweak, small MAE gain, modest `CH2CO` help, but no decisive win
- **`OH+HO2`**: strongest global early-slice error among these nearby variants, but unacceptable `HO2` blow-up
- **strong `OH` only**: best `OH`, but globally unstable

## Current takeaway

The soft-`OH` result suggests that simple weighting alone is reaching diminishing returns.

> A weaker `OH` weight makes the branch safer and more balanced, but it does not cleanly solve the early-window problem. The next useful fix is likely to require something beyond another nearby weight tweak.

## Best next step

The next justified direction is probably **not** another manual weight-profile sweep. Better candidates now are:
- deploy the currently best-looking nearby branch and check if the offline early-slice win survives in-loop
- or add a more structured activity/radical regularizer rather than channel weights alone
- or build a later-corrective dataset around the next divergence interval after `2e-07`
