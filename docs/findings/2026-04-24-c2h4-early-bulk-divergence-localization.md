# C2H4 early bulk-divergence localization: the deployed early-window intermediate branch already departs from CVODE bulk heat release by `3e-07`, and its one-step self-state error is no longer small there, so the in-loop bulk failure is not only late manifold drift

_Date: 2026-04-24_

## Why this was the next step

The previous deployment scout established two important facts about the alignment-fixed early-window intermediate branch:
- it runs cleanly to `1e-6`
- but by `1e-6` its bulk heat-release behavior is badly wrong relative to CVODE

The next question was therefore:
- **when** does the bulk divergence first appear,
- and by that time is the model still locally close to CVODE on the states it visits, or has the local one-step chemistry already become poor?

## New early-time case-vs-CVODE rollout comparisons

For the deployed case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediateweights_np8`

I compared against:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_cvode_baseline_np8_stockcopy`

at times:
- `2e-07`
- `3e-07`
- `5e-07`
- plus the already-known `1e-06`

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_vs_cvode_2e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_vs_cvode_3e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_vs_cvode_5e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_vs_cvode_1e-06_summary.json`

## New self-case one-step analyses

I also evaluated the deployed branch against corrected CVODE **on its own visited states** at:
- `3e-07`
- `5e-07`

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_selfcase_3e-07_vs_cvode_corrected.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_selfcase_5e-07_vs_cvode_corrected.json`

## Main result 1: bulk `Qdot` divergence starts much earlier than `1e-6`

### At `2e-07`
Bulk agreement is still fairly reasonable:
- mean `Qdot` ratio: **`1.20x`**
- mean `|ΔT|`: `0.186 K`
- mean `|Δp|`: `24.8 Pa`

### At `3e-07`
Bulk behavior has already shifted into the wrong regime:
- mean `Qdot` ratio: **`-0.316x`**
- mean `|ΔT|`: `0.440 K`
- mean `|Δp|`: `25.8 Pa`

The sign flip is especially visible in the cool active band:
- `510–700 K` bin `Qdot` ratio: **`0.0695x`**
- sign mismatch fraction: **`0.510`**

So by `3e-07`, the model is no longer just slightly biased; it is already wrong in the direction and magnitude of heat release in the early active regime.

### At `5e-07`
The hot bulk is strongly overdriven:
- mean `Qdot` ratio: **`6.31x`**
- `1600–2600 K` bin `Qdot` ratio: **`57.98x`**

### At `1e-06`
This late failure is the continuation of an earlier trend, not a sudden collapse:
- mean `Qdot` ratio: **`-44.96x`**
- `1600–2600 K` bin `Qdot` ratio: **`-356.97x`**

## Main result 2: the early in-loop bulk failure is not only manifold drift; local one-step error is already bad by `3e-07`

This is the most useful clarification from this turn.

### Self-case one-step error at `3e-07`
- global MAE: **`1.67e-05`**
- global RMSE: **`3.57e-04`**

Top 1% worst visited states:
- mean `T`: `784 K`
- true one-step `ΔY` L1 mean: `6.76e-04`
- predicted one-step `ΔY` L1 mean: **`2.32e-02`**

Key channels:
- `C2H3` predicted mean: ~`0`
- true mean: `1.49e-05`
- `CH2CO` predicted mean: ~`0`
- true mean: `3.37e-06`
- `OH` predicted mean: `-2.62e-05`
- true mean: `-1.15e-05`

### Self-case one-step error at `5e-07`
- global MAE: **`3.24e-05`**
- global RMSE: **`4.09e-04`**

Top 1% worst visited states:
- mean `T`: `2199 K`
- true one-step `ΔY` L1 mean: `1.64e-03`
- predicted one-step `ΔY` L1 mean: **`2.65e-02`**

Again the key intermediates remain nearly dead:
- `C2H3` predicted mean: `1.51e-08`
- true mean: `1.79e-05`
- `CH2CO` predicted mean: `7.47e-10`
- true mean: `4.27e-06`

So by `3e-07`, the branch is already not locally accurate enough on the states it visits.

## Interpretation

This refines the earlier manifold-drift story.

### What remains true
By `1e-6`, manifold drift is real and important.

### What this new analysis adds
For the early-window intermediate deployment branch, the bulk thermodynamic failure is **not only** a late-stage self-consistent drift on the wrong manifold.

Instead:
- bulk `Qdot` behavior is already wrong by **`3e-07`**
- and by then, local one-step chemistry on self states is already poor in the important channels
- especially `C2H3`, `CH2CO`, and bulk activity magnitude in the worst states

So the deployed branch is not simply “locally fine but globally drifted.”
It becomes **both** locally poor **and** globally drifted very early.

## Current takeaway

The strongest current conclusion is:

> The first alignment-fixed early-window deployment branch crosses into the wrong bulk heat-release regime by `3e-07`, and this is already accompanied by large local one-step errors on the branch’s own visited states. That means the next fix should target early in-loop bulk activity directly, not just later manifold drift or isolated channel weighting.

## Best next step

The next fix should now be centered on the `2e-07 -> 5e-07` interval and should likely include some form of:
- early-window bulk-activity control,
- or enthalpy/heat-release regularization,
- rather than more species-weight tuning alone.
