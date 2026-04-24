# EFNO self-rollout predicted-full-BCT-prenorm ablation: a broader full-species redesign collapses exactly to the earlier main-BCT variant under the current decode contract

_Date: 2026-04-23_

## Why this was the next step

After ruling out more one-channel fixes, the next useful step was to test a broader non-oracle redesign of the **full species second-step feature contract**.

The idea was:
- keep the species block in a coherent Box-Cox-space representation
- avoid mixing direct main-species BCT channels with an inconsistent separately patched last-species channel

So I tested a new self-rollout construction where the second-step species feature block is built from the **pre-normalization full species state**:
- main species from the predicted next-step BCT state
- last species from mass-closure before the later normalization used for loss evaluation

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added rollout species-feature mode:
- `"predicted_full_bct_prenorm"`

Behavior:
- decode predicted main species from BCT state
- form a full pre-normalization species vector using closure for the last species
- Box-Cox transform that full pre-normalization species vector
- use it as the self-generated second-step species feature block

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_self_rollout_predicted_full_bct_prenorm_ablation.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_predicted_full_bct_prenorm_ablation/summary.json`
- `/root/workspace/artifacts/experiments/h2_efno_self_rollout_predicted_full_bct_prenorm_ablation/normalization_activity_seed0.json`

Compared:
1. `teacherforced_rollout0p1`
2. `self_rollout0p1`
3. `self_rollout0p1_predicted_main_bct`
4. `self_rollout0p1_predicted_full_bct_prenorm`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- `target_mode = "temperature_species"`
- `species_data_space = "bct_delta"`
- `temperature_loss_weight = 0.1`
- `species_loss_weight = 4.0`
- `lambda_elements = 0.0`
- `lambda_mass = 0.0`
- `rollout_consistency_weight = 0.1`

## Aggregated result

### Teacher-forced reference
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`

### Pure self-rollout
- rollout species MAE @1000: `4.881e-01`
- rollout temperature MAE @1000: `8.403e+03 K`

### Predicted-main-BCT
- one-step species MAE: `3.264e-04`
- one-step temperature MAE: `1.846e-01 K`
- one-step element-mass MAE: `6.525e-04`
- rollout species MAE @1000: `3.627e-01`
- rollout temperature MAE @1000: `6.457e+03 K`
- rollout element-mass MAE @1000: `7.801e-01`

### Predicted-full-BCT-prenorm
- one-step species MAE: `3.264e-04`
- one-step temperature MAE: `1.846e-01 K`
- one-step element-mass MAE: `6.525e-04`
- rollout species MAE @1000: `3.627e-01`
- rollout temperature MAE @1000: `6.457e+03 K`
- rollout element-mass MAE @1000: `7.801e-01`

These results are effectively identical to the earlier `predicted_main_bct` branch.

## Why the two variants collapsed together

The follow-up normalization-activity diagnostic explains why.

Representative seed-0 training-set results:
- pre-normalization species-sum mean: about `6.30`
- fraction with pre-normalization species sum `> 1`: `1.0`
- mean absolute full-block BCT difference between pre-normalization and normalized species states: about `1.448`
- mean absolute **last-species** BCT difference between pre-normalization and normalized species states: `0.0`

Interpretation:
1. the pre-normalization species state is never close to a valid mass-fraction state under this contract
2. the closure-derived last species is clamped to zero before and after normalization in the representative checkpoint
3. therefore `predicted_full_bct_prenorm` reduces to the same practical feature block as `predicted_main_bct` under the current decode path:
   - main channels are the same predicted BCT state
   - last channel is the same collapsed near-zero feature

## Main interpretation

### 1. This broader redesign did not create a meaningfully new regime
Although it looked like a larger contract change, the current decode path makes it functionally equivalent to the earlier `predicted_main_bct` branch.

### 2. The current self-generated closure species is more pathological than expected
The diagnostic shows the pre-normalization decoded species state is so inconsistent that:
- the species block must be renormalized heavily for evaluation
- the closure last species is already collapsed to zero in the representative checkpoint

That means the real structural issue is upstream of the last Box-Cox transformation.

### 3. The broader bottleneck is now even clearer
The issue is not just a bad choice of how to encode the last species after closure.
The deeper problem is that the current decoded species state used to build self-generated second-step features is itself badly off the simplex.

## What this changes

This failed attempt is useful because it removes another plausible path:
- a seemingly broader full-species pre-normalization BCT redesign does **not** produce a new improvement regime under the current decode contract

The next useful intervention should therefore target the **decoded species-state construction itself**, not only how that state is re-encoded into second-step features.

## Bottom line

A broader full-species self-rollout feature redesign was tested, but under the present decode/closure behavior it collapses exactly to the earlier `predicted_main_bct` branch.

That is informative: the next bottleneck lies deeper, in the structure of the self-generated decoded species state rather than only in its final second-step feature encoding.
