# C2H4 activity-regularization scout: a simple aggregate activity-L1 penalty improves offline validation slightly but worsens corrected `2e-07` behavior, so naive activity matching is not yet the right bulk-control fix

_Date: 2026-04-24_

## Why this was the next step

The previous analyses showed that the deployed early-window intermediate branch:
- departs from the correct bulk heat-release regime by `3e-07`
- is already locally wrong on its own visited states by then
- and likely needs something more structured than another nearby species-weight tweak

The smallest next implementation was therefore to test a simple **aggregate activity regularizer** in training.

## Code changes

### DFODE-kit trainer update
Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`

Added support for:
- `activity_l1_weight`

New loss term:
- `loss4 = mean(| sum(|Y_out - Y_in|) - sum(|Y_target - Y_in|) |)`

This penalizes mismatch in the total one-step species activity magnitude.

### Workspace training wrapper update
Updated:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Added CLI support for:
- `--activity-l1-weight`

## New training run

### Dataset
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_r0p2_aligned_plus_stockearly20k.npy`

### Branch
- intermediate weighting only
- attention enabled
- `activity_l1_weight = 1.0`

### Checkpoint
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_activity1_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_activity1_smoke_deepflame_bundle/`

### Summary
- `/root/workspace/artifacts/experiments/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_activity1_smoke_baseline/summary.json`

## Offline result

Best validation loss:
- **`0.68076`**

This is slightly better than the previous intermediate-only early-window branch:
- previous: `0.68569`
- new activity-regularized branch: **`0.68076`**

So offline, this looked mildly promising.

## Corrected `2e-07` CFD-state vs CVODE result

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_activity1_smoke_cfd_active_2e-07_vs_cvode_corrected.json`

### Comparison against the previous intermediate-only branch
Previous branch:
- MAE: `1.329e-04`
- RMSE: `1.211e-03`
- top 1% predicted `ΔY` L1: `6.03e-02`

Activity-regularized branch:
- MAE: **`2.062e-04`**
- RMSE: **`3.644e-03`**
- top 1% predicted `ΔY` L1: **`2.295e-01`**

So the corrected early-slice behavior becomes much worse.

### Key channels
- `C2H3` MAE worsens slightly:
  - from `9.683e-06`
  - to **`9.922e-06`**
- `CH2CO` MAE worsens slightly:
  - from `2.401e-06`
  - to **`2.416e-06`**
- `OH` MAE worsens:
  - from `3.602e-04`
  - to **`3.755e-04`**
- `HO2` stays essentially unchanged and still under-predicted

## Interpretation

This is another useful negative result.

### What it shows
- simple aggregate activity matching can help the held-out validation objective slightly
- but that does **not** translate into better corrected `2e-07` behavior on real CFD states
- in fact, the branch becomes substantially worse in overall early-slice error and worst-state overreaction

So the next conclusion is:

> A naive total-activity penalty is too blunt. Matching the scalar amount of species activity does not by itself control the physically important bulk-heat-release failure mode.

## Current takeaway

The recent sequence of fix attempts has now ruled out several simple local moves as sufficient solutions:
- stronger radical weighting
- OH-only weighting
- softer OH-only weighting
- naive aggregate activity-L1 regularization

That means the next promising fix likely needs to be more physically structured than a scalar activity penalty. Stronger candidates now are:
- enthalpy-aware or heat-release-aware regularization
- or a deployment guard / hybrid policy tuned to intervene before the `3e-07` bulk-regime flip
