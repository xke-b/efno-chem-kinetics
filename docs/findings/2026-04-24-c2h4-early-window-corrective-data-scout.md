# C2H4 early-window corrective-data scout: adding `20k` aligned stock early-window pairs materially improves corrected one-step error at `2e-07`, especially reducing gross overreaction, but radical-balance error in `OH` remains a major obstacle

_Date: 2026-04-24_

## Why this was the next fix to try

The corrected trajectory-divergence analysis showed that the important chemistry drift begins almost immediately after the first learned step:
- mean `Qdot` ratio collapses by `2e-07`
- `C2H3` is already nearly dead at the earliest learned slice
- `CH2CO` falls badly by `2e-07`

That made the next useful corrective step clear:
- build an **early-window corrective dataset** from the stock C2H4 case,
- merge it into the alignment-fixed mixed data path,
- and test whether this improves the earliest corrected one-step behavior.

## New early-window corrective dataset

Extracted from the trustworthy stock-style C2H4 baseline:
- case: `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`
- times: `1e-07`, `2e-07`, `3e-07`, `4e-07`, `5e-07`
- filters:
  - `T > 510 K`
  - `|Δp| <= 100 Pa`
  - `5000` samples per pair

Artifacts:
- `/root/workspace/data/c2h4_case_pairs_stock_early_1e-07_to_5e-07_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_stock_early_1e-07_to_5e-07_dp100.json`

Result:
- `4` pair windows
- `20000` rows total

## New mixed dataset with explicit early corrective support

Built by concatenating:
- aligned mixed `r=0.2` dataset (`60000` rows)
- stock early-window corrective dataset (`20000` rows)

Artifacts:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_r0p2_aligned_plus_stockearly20k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_r0p2_aligned_plus_stockearly20k.json`

Total rows:
- `80000`

## New fix-branch training run

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke_baseline/summary.json`

### Training setup
- power-delta target
- attention heads `4`, attention layers `1`, post-spectral
- intermediate-species weighting profile `c2h4_intermediates_v1`
- validation-aware `12`-epoch smoke budget

### Best validation result
- best epoch: **`11`**
- best validation loss: **`0.68569`**

This improves on the previous alignment-fixed weighted smoke scout:
- previous best val loss: `0.72459`
- new best val loss: **`0.68569`**

## Early corrected one-step comparison at `2e-07`

This is the key check because `2e-07` is where the corrected trajectory-divergence analysis says the important chemistry drift starts.

### Previous alignment-fixed weighted smoke branch
Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_aligned_fno_powerdelta_attn1_intermediateweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

Corrected metrics:
- global MAE: `3.288e-04`
- global RMSE: `4.601e-03`

Top 1% worst states:
- true `ΔY` L1 mean: `4.46e-04`
- predicted `ΔY` L1 mean: **`2.976e-01`**

This branch is still badly overreacting in the early active region.

### New branch with `20k` stock early-window pairs
Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

Corrected metrics:
- global MAE: **`1.329e-04`**
- global RMSE: **`1.211e-03`**

Top 1% worst states:
- true `ΔY` L1 mean: `3.82e-04`
- predicted `ΔY` L1 mean: **`6.03e-02`**

So the early-window corrective data reduced the worst overreaction dramatically.

## Channel-level impact at `2e-07`

### Improvements
Compared with the prior alignment-fixed weighted smoke branch, the `+stockearly20k` branch improves:
- `C2H3` MAE:
  - from `1.061e-05`
  - to **`9.683e-06`**
- `CH2CO` MAE:
  - from `2.631e-06`
  - to **`2.401e-06`**
- `CH2CHO` MAE:
  - from `1.559e-07`
  - to **`1.438e-07`**

And it raises predicted means toward the correct order of magnitude instead of near-zero:
- `C2H3` predicted mean:
  - old: `-5.16e-07`
  - new: **`4.04e-07`**
  - truth: `9.99e-06`
- `CH2CO` predicted mean:
  - old: `2.09e-08`
  - new: **`2.47e-07`**
  - truth: `2.65e-06`

These are still under-predicted, but they move in the right direction.

### Remaining major problem: `OH`
The new branch is **not** a clean win in every channel.

At `2e-07`:
- old `OH` MAE: `2.635e-04`
- new `OH` MAE: **`3.602e-04`**

Predicted mean `ΔOH`:
- old: `-2.701e-04`
- new: **`-3.668e-04`**
- truth: `-6.675e-06`

So the early-window corrective data clearly reduces gross overall overreaction and improves several early intermediate channels, but it still leaves a substantial radical-balance problem in `OH`.

## Interpretation

This is a meaningful partial success.

### What worked
- adding explicit early-window stock support improved validation loss
- it reduced early gross overreaction at `2e-07`
- it improved `C2H3`, `CH2CO`, and `CH2CHO` error modestly but consistently

### What did not work yet
- the model is still far from correct on the early intermediates
- `OH` remains badly overdriven relative to corrected CVODE
- so the current fix path improves the early-window problem, but does not solve the radical-consistency problem

## Current takeaway

The strongest conclusion from this scout is:

> Early corrective data help. The first `20k` stock early-window add-on materially improves the earliest corrected one-step behavior at `2e-07`, especially by reducing gross overreaction, but the branch still has a major `OH` radical-balance error and is not yet deployment-ready.

## Best next fix from here

The next fix should now be more specific than “more early data.” The evidence points to:
1. **keep the early-window corrective data path**
2. add **explicit radical-balance control**, especially for `OH`
3. likely extend species-aware weighting beyond intermediates alone to include a small but targeted `OH` / `HO2` emphasis
4. then test again at the first divergence slice (`2e-07`) before spending more on coupled deployment
