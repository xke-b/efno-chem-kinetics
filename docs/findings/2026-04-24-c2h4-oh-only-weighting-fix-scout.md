# C2H4 OH-only weighting fix scout: removing `HO2` weighting avoids the radical blow-up, and sharply improves `OH` one-step error at `2e-07`, but it destabilizes the overall state badly and produces catastrophic worst-state overreaction

_Date: 2026-04-24_

## Why this was the next fix

The previous radical-weighting scout showed a very specific pattern:
- adding `OH` + `HO2` weighting improved corrected `2e-07` global error
- `OH` overshoot dropped substantially
- but `HO2` became catastrophically overdriven

That pointed to the next narrow fix:
- keep the early-window corrective dataset
- keep intermediate weighting
- keep explicit `OH` weighting
- remove `HO2` weighting

## Code change

Updated:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Added profile:
- `c2h4_intermediates_oh_v1`

Weights:
- intermediates (`C2H5`, `C2H3`, `CH2CHO`, `CH2CO`, `CH2OH`, `HCCO`): `20x`
- `OH`: `10x`
- `HO2`: no extra weighting

## New training run

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohweights_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohweights_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohweights_smoke_baseline/summary.json`

### Offline result
Best validation loss:
- **`0.80210`**

This is:
- worse than intermediate-only (`0.68569`)
- better than `OH+HO2` weighting (`0.84470`)

So offline validation again does not cleanly predict the corrected CFD-state objective.

## Corrected `2e-07` CFD-state vs CVODE result

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_ohweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

## Main result

This branch is **not** a clean improvement.
It helps the specific `OH` channel strongly, but breaks the global behavior badly.

### Global metrics
Compared with the intermediate-only branch:
- intermediate-only
  - MAE: `1.329e-04`
  - RMSE: `1.211e-03`
- intermediate + `OH`
  - MAE: **`3.369e-04`**
  - RMSE: **`7.559e-03`**

So the global corrected error gets much worse.

### Worst-state behavior
Top 1% worst states:
- intermediate-only predicted `ΔY` L1 mean: `6.03e-02`
- intermediate + `OH` predicted `ΔY` L1 mean: **`4.37e-01`**

This is a major regression.

## Channel-level behavior

### `OH` improves dramatically
This was the intended effect, and it worked.

- intermediate-only `OH` MAE: `3.602e-04`
- intermediate + `OH` `OH` MAE: **`1.769e-05`**

Predicted mean `ΔOH`:
- intermediate-only: `-3.668e-04`
- intermediate + `OH`: **`-1.248e-05`**
- truth: `-6.675e-06`

So `OH` becomes much closer to corrected CVODE.

### `HO2` stays tame
Unlike the previous `OH+HO2` branch, `HO2` does not blow up:
- `HO2` MAE: `5.891e-07`
- predicted mean `ΔHO2`: `-1.073e-07`
- truth: `4.682e-07`

So removing `HO2` weighting did fix the `HO2` explosion problem.

### But key intermediates get worse again
- `C2H3` MAE worsens slightly: `9.866e-06`
- `CH2CO` MAE worsens: `2.634e-06`
- predicted `CH2CO` mean drops back toward zero: `1.63e-08` vs truth `2.65e-06`

## Interpretation

This is another highly informative failure.

### What worked
- `OH` weighting alone can target the `OH` channel very effectively
- removing `HO2` weighting avoids the severe `HO2` overreaction introduced by the previous branch

### What failed
- the branch becomes globally unstable in corrected `2e-07` error
- worst-state overreaction becomes much larger
- key intermediates such as `CH2CO` regress again

So the lesson is not “weight only `OH`.”
The lesson is narrower:

> `OH` is controllable by weighting, but isolated `OH` emphasis without a stronger balancing mechanism can improve the target radical channel while destabilizing the rest of the state update.

## Current takeaway

The three nearby branches now outline a clear tradeoff:

### Intermediate-only
- best overall balance so far
- still bad `OH`

### Intermediate + `OH` + `HO2`
- best corrected global `2e-07` MAE/RMSE among these three
- better `OH`
- catastrophic `HO2`

### Intermediate + `OH` only
- best `OH` channel accuracy
- avoids `HO2` blow-up
- worst global instability / overreaction

## Best next step

The next fix probably should **not** be another simple weight-profile tweak alone.
The evidence now suggests we need a more structured control mechanism, such as:
- smaller `OH` weight than `10x`
- or channel-dependent clipping / regularization
- or an auxiliary penalty tied to radical-balance / total activity in the early window

The shortest next step is likely:
- keep the early-window corrective dataset
- revert to the better-balanced intermediate-only or `OH+HO2` branch as the base
- add a **weaker** `OH` emphasis rather than the current strong `OH`-only move
