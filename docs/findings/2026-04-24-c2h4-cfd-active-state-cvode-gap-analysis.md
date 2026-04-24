# C2H4 coupled-failure diagnosis on real CFD states: checkpoint-vs-CVODE one-step analysis shows two distinct failure modes—hot-cell overreaction and cool-cell underreaction—and points to data/target mismatch rather than a single architecture bug

_Date: 2026-04-24_

## Why this was the next step

The immediate need was to stop reasoning only from rollout survival and start analyzing the learned chemistry models on the **actual CFD states** they see just before coupled failure.

Following the user’s suggestion and borrowing from the Xiao paper’s evaluation style, I compared trained models against one-step Cantera/CVODE chemistry integration on real DeepFlame C2H4 active states.

The core question was:
- for the actual C2H4 cells that would trigger learned chemistry at the first DNN-active step,
- how far do the model-predicted species changes deviate from CVODE,
- and what kinds of CFD states produce the worst errors?

## New analysis script

Added:
- `/root/workspace/scripts/analyze_c2h4_cfd_checkpoint_vs_cvode.py`

This script:
- extracts active CFD states from a real DeepFlame case time directory
- runs one-step Cantera/CVODE chemistry integration from those exact states
- runs a DFODE-kit checkpoint on the same states
- compares **species delta** predictions in physical space
- reports Xiao-style metrics including:
  - MAE (physical)
  - RMSE (physical)
  - `R^2` (physical)
  - SSPI-like small-target score on `|ΔY| < 1e-15`
- ranks the worst cells by per-state delta RMSE
- summarizes their shared thermochemical attributes

## CFD state source used

Reference case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_cvode_baseline_np8_stockcopy`

State time analyzed:
- `1e-07`

This is the right pre-inference slice because the first learned chemistry step happens at the next step (`2e-07`) for cells above the frozen-temperature threshold.

Active-cell count:
- `33,508`

## Checkpoints analyzed

### Mixed-data power-delta promoted baseline
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val.pt`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_cfd_active_1e-07_vs_cvode.json`

### Mixed-data power-delta + interleaved attention (`r=0.2`)
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_interleaved_promoted100_val.pt`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_interleaved_promoted100_val_cfd_active_1e-07_vs_cvode.json`

### Mixed-data power-delta + interleaved attention (`r=1.0`)
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val.pt`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_cfd_active_1e-07_vs_cvode.json`

### Pure oneD/Xiao `100k` promoted model
- `/root/workspace/artifacts/models/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val.pt`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_cfd_active_1e-07_vs_cvode.json`

## Main result: two different learned failure modes

The analysis does **not** support a single universal failure mechanism.
Instead, the models fall into two clearly different regimes.

### Regime A — hot-cell overreaction
Most visible in:
- mixed `r=0.2` promoted power-delta
- pure oneD/Xiao `100k`

#### `r=0.2` promoted power-delta
Global active-state metrics:
- MAE: `7.72e-03`
- RMSE: `2.01e-02`
- `R^2`: `-20.74`
- small-target SSPI: `0.9957`

Worst 1% states:
- mean `T`: **`2458.6 K`**
- mean `p`: `101358 Pa`
- mean `|Qdot|`: `5.51e6`
- true `ΔY` L1 mean: `0.0166`
- predicted `ΔY` L1 mean: **`0.3070`**

Temperature-bin behavior:
- `510–700 K`: predicted `ΔY` L1 is only `7e-05x` CVODE
- `1600–2600 K`: predicted `ΔY` L1 is **`11.21x`** CVODE

This branch reacts far too strongly in the hot bulk.

#### pure oneD/Xiao `100k`
Global active-state metrics:
- MAE: `1.07e-03`
- RMSE: `5.59e-03`
- `R^2`: `-0.685`
- SSPI: `0.8500`

Worst 1% states:
- mean `T`: **`1329 K`**
- mean `p`: `103344 Pa`
- mean `|Qdot|`: `2.48e6`
- true `ΔY` L1 mean: `0.1969`
- predicted `ΔY` L1 mean: **`0.4708`**

A representative worst hot state shows:
- true `ΔC2H3 ≈ 5.84e-04`
- predicted `ΔC2H3 ≈ 1.26e-01`

So the oneD-only large model is not merely missing chemistry; it can massively over-amplify some intermediate production in the hot regime.

### Regime B — cool-cell underreaction / near-zero chemistry
Most visible in:
- mixed interleaved-attention branches (`r=0.2` and `r=1.0`)

#### `r=0.2` interleaved
Global active-state metrics:
- MAE: `9.30e-04`
- RMSE: `4.30e-03`
- `R^2`: ~`1.3e-05`
- SSPI: `0.9180`

Worst 1% states:
- mean `T`: **`529.3 K`**
- mean `p`: `103681 Pa`
- mean `|Qdot|`: essentially zero in the written field (`~2.89e-14`)
- true `ΔY` L1 mean: **`0.3288`**
- predicted `ΔY` L1 mean: **`2.25e-06`**

Temperature-bin behavior:
- `510–700 K`: predicted `ΔY` L1 is only **`1e-05x`** CVODE
- `1600–2600 K`: predicted `ΔY` L1 is only **`3.2e-05x`** CVODE

Representative worst cool state:
- current `T ≈ 524.8 K`
- true `ΔC2H3 ≈ 1.19e-03`
- predicted `ΔC2H3 = 0`
- true `ΔCH2CO ≈ 1.79e-03`
- predicted `ΔCH2CO ≈ 1.34e-15`

This branch is effectively freezing chemistry in the states where CVODE shows the onset of strong intermediate formation.

#### `r=1.0` interleaved
Global active-state metrics are almost the same:
- MAE: `9.29e-04`
- RMSE: `4.28e-03`
- `R^2`: `0.0095`
- SSPI: `0.9164`

Worst 1% states are again concentrated at:
- mean `T`: **`529.3 K`**
- mean `p`: `103679 Pa`

And the worst cells again show near-zero predicted chemistry where CVODE has substantial cool-regime intermediate growth.

So increasing the oneD fraction from `0.2` to `1.0` does **not** remove the cool underreaction pathology.

## Species-level clues

### Hot-overreaction branch (`r=0.2` promoted power-delta)
The most dramatic species failure is not the tiny intermediates alone, but **OH**:
- true mean `ΔOH`: `-6.85e-04`
- predicted mean `ΔOH`: **`+5.77e-02`**
- `R^2`: `-26499`

That is a strong signal that this branch is not merely noisy; it is learning the wrong radical response direction in the hot active regime.

### Cool-underreaction interleaved branches
For the interleaved branches, the issue is the opposite:
- `ΔC2H3`, `ΔCH2CHO`, `ΔCH2CO`, `ΔC2H5` are all driven essentially to zero in the worst cool states
- even `ΔOH` is heavily damped:
  - true mean `ΔOH`: `-6.85e-04`
  - predicted mean `ΔOH`: about `1e-07` to `2e-07`

This looks like a model that has become too conservative and is not activating the onset chemistry manifold.

## Synthesis: what likely causes what?

### 1. Target formulation is likely involved, but not the whole story
The current power-delta target helped bulk deployment in earlier tests, but the CFD-state analysis shows two opposite failure modes:
- overreaction in hot states for some branches
- underreaction in cool onset states for others

So the target is not universally wrong, but it is probably **not sufficient by itself** to encode the right regime balance.

### 2. Training-data preparation looks like the strongest root cause
The strongest common evidence points here.

- pure oneD/Xiao data alone overreacts or distorts hot/intermediate chemistry
- case-pair-heavy mixed models with interleaved attention become too damped in the cool onset region
- larger oneD fraction (`r=1.0`) still does not repair that onset failure cleanly

This suggests the model is being asked to learn from **semantically mixed supervision**:
- one source closer to chemistry-manifold evolution
- another source closer to full-CFD state transition behavior

The result is regime-dependent compromise rather than faithful chemistry.

### 3. Architecture matters, but it is not the primary root cause
Interleaved attention clearly changes the error structure:
- it greatly improves the hot-bulk overreaction seen in the plain promoted power-delta branch
- but it collapses toward near-zero chemistry in the coolest active states

So architecture changes the failure **shape**, but the underlying problem still looks data/regime-driven.

## Current hypothesis set

The evidence supports the following concrete hypotheses.

### Hypothesis A — cool-onset states are underrepresented or semantically conflicted
The worst errors for the interleaved branches cluster almost entirely in `510–700 K` active states.

That suggests the current training pipeline is not giving the model a clean enough signal for:
- low-temperature onset chemistry
- early intermediate formation
- radical pool build-up in the near-threshold active regime

### Hypothesis B — uniform mixing of oneD chemistry and CFD case-pair labels is too blunt
The difference between:
- pure oneD overreaction,
- mixed-branch cool underreaction,
- and ratio changes that do not fix either cleanly,

suggests we need **structured or regime-selective mixing**, not larger raw concatenation.

### Hypothesis C — the present loss still underweights the exact channels that matter most in the coupled onset regime
The current interleaved models can keep overall RMSE moderate while still zeroing out the onset-intermediate channels that matter for downstream thermo coupling.

That means bulk loss alone is insufficient to preserve the chemistry manifold needed by CFD.

## Most justified fixes to test next

Based on this diagnosis, the best next fixes are no longer broad sweeps.
They should target the identified failure regions directly.

### Fix 1 — regime-targeted CFD-state benchmark set for `510–700 K`
Build a dedicated evaluation subset from real CFD active cells in the `510–700 K` band and use it as a standing diagnostic benchmark for every promoted model.

### Fix 2 — regime-selective mixed-data construction
Instead of uniform `dp100 + oneD` concatenation, build mixtures where oneD/Xiao chemistry support is emphasized specifically for the cool-onset states that the interleaved models currently suppress.

### Fix 3 — species-aware supervision targeted at onset intermediates in the mixed promoted branch
Use the stronger promoted mixed interleaved branch, but add explicit weighting for:
- `C2H3`
- `CH2CHO`
- `CH2CO`
- `C2H5`
- possibly `HO2` / `OH`

with evaluation specifically on the CFD-state cool-onset benchmark.

## Current takeaway

This analysis substantially reduces uncertainty about the coupled-CFD failures.

> The current C2H4 models do not all fail for the same reason. Some branches fail by overreacting in hot cells, while the interleaved mixed branches fail by almost shutting chemistry off in the coolest active CFD states. The dominant root cause now looks more like regime-specific data/target mismatch than a single architecture bug.
