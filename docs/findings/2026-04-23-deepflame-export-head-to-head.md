# DeepFlame-export head-to-head on H2: deployment-format evaluation favors teacher-forced corrected EFNO over the previously preferred self-rollout branch

_Date: 2026-04-23_

## Why this was the next step

After re-baselining the corrected H2 comparisons under the DeepFlame-style `preserve_last` contract, the next most useful step was to stop reasoning only from the project-side evaluator and move one layer closer to actual deployment.

So I ran a direct **exported-checkpoint head-to-head** on the leading H2 candidates.

## What was compared

Shortlisted seed-0 H2 candidates:
- `supervised_deltaT_25ep`
- `teacherforced_rollout0p1_bctdecode`
- `self_rollout0p1_bctdecode`
- `self_rollout0p1_predicted_main_bct_bctdecode`

New script:
- `/root/workspace/scripts/run_h2_deepflame_export_head_to_head.py`

Artifacts:
- summary: `/root/workspace/artifacts/experiments/h2_deepflame_export_head_to_head/summary.json`
- per-case export evals: `/root/workspace/artifacts/experiments/h2_deepflame_export_head_to_head/*_export_eval.json`
- exported DeepFlame-compatible candidate checkpoints: `/root/workspace/artifacts/models/h2_deepflame_candidates/*.pt`

Dataset:
- `/root/workspace/data/h2_autoignition_longprobe_test.npy`
- `/root/workspace/data/h2_autoignition_longprobe_test.json`

## Evaluation contract used here

This is not the old thermochemical evaluator contract.

Instead, each candidate was evaluated after export into the current DeepFlame-compatible multi-network species format using this deployment-style path:
1. predict next species with the exported DeepFlame-style model
2. reconstruct next temperature from **current enthalpy + predicted next species at fixed pressure**

So this head-to-head is closer to the real species-only deployment path than the earlier direct checkpoint evaluator.

## Small failure recorded and fixed

The first batch preserve-last re-baselining attempt had failed because the evaluator assumed the parent directory for `--out` already existed.

That was fixed in:
- `/root/workspace/scripts/evaluate_species_delta_checkpoint.py`

The evaluator now creates the parent output directory automatically when `--out` is used.

## Export fidelity check

The exported checkpoints remained numerically faithful to the original species branch.

Example validation ranges from the export metadata:
- max abs next-species diff: roughly `1e-08` to `1e-08`
- max abs source-term diff: about `1e-02` to `3e-02`

So differences in the head-to-head are coming from the deployment contract itself, not from a bad export.

## Deployment-format head-to-head results

### 1. Teacher-forced corrected EFNO
- one-step species MAE: `2.925e-05`
- one-step temperature MAE: `0.4086 K`
- one-step element-mass MAE: `1.128e-05`
- rollout species MAE @1000: `4.376e-03`
- rollout temperature MAE @1000: `270.42 K`
- rollout element-mass MAE @1000: `3.244e-03`

### 2. Self-rollout corrected EFNO
- one-step species MAE: `3.304e-05`
- one-step temperature MAE: `0.7855 K`
- one-step element-mass MAE: `1.313e-05`
- rollout species MAE @1000: `4.710e-03`
- rollout temperature MAE @1000: `399.89 K`
- rollout element-mass MAE @1000: `3.972e-03`

### 3. Supervised baseline
- one-step species MAE: `2.390e-05`
- one-step temperature MAE: `0.1660 K`
- one-step element-mass MAE: `5.674e-06`
- rollout species MAE @1000: `6.203e-03`
- rollout temperature MAE @1000: `144.75 K`
- rollout element-mass MAE @1000: `2.168e-03`

### 4. Self-rollout + predicted-main-BCT corrected EFNO
- one-step species MAE: `3.306e-05`
- one-step temperature MAE: `0.8121 K`
- one-step element-mass MAE: `1.283e-05`
- rollout species MAE @1000: `7.487e-03`
- rollout temperature MAE @1000: `468.33 K`
- rollout element-mass MAE @1000: `4.372e-03`

## Main interpretation

### 1. The exported deployment-format comparison does **not** support carrying forward `self_rollout0p1_predicted_main_bct_bctdecode` as the default H2 candidate
That branch was previously the preferred one under the older closure-mode offline interpretation.

But under the exported deployment-style path, it is the weakest of the four shortlisted candidates on:
- rollout species MAE
- rollout temperature MAE
- rollout element-mass MAE

So it should no longer be treated as the default DeepFlame-facing H2 branch.

### 2. Teacher-forced corrected EFNO is the best rollout-species deployment candidate in this head-to-head
Among the exported deployment-style evaluations, `teacherforced_rollout0p1_bctdecode` gives the best rollout species MAE and clearly beats the two self-rollout corrected branches.

### 3. Supervised remains very competitive under deployment-format evaluation
Supervised is still best on:
- one-step species
- one-step temperature
- one-step element mass
- rollout temperature
- rollout element mass

Its only clear weakness here is rollout species, where teacher-forced corrected EFNO is better.

So the deployment-format comparison is even more conservative than the preserve-last evaluator re-baseline: it does not show a single clear across-the-board winner.

### 4. Deployment-format temperature behavior differs from direct thermochemical-head evaluation
This head-to-head reconstructs temperature through the species-only deployment path rather than using the trained temperature head directly.

That matters.

For example, compared with the preserve-last direct evaluator summaries, rollout temperatures are substantially worse for the corrected rollout-aware branches under the species-only deployment path. That is evidence that dropping the direct temperature head and relying on enthalpy reconstruction changes practical behavior in a nontrivial way.

## Bottom line

The first deployment-format head-to-head changes the current H2 shortlist interpretation again.

For DeepFlame-facing use:
- `self_rollout0p1_predicted_main_bct_bctdecode` should be demoted from default-candidate status
- `teacherforced_rollout0p1_bctdecode` becomes the strongest corrected rollout-aware species candidate in the exported deployment path
- `supervised_deltaT_25ep` remains a very strong reference and is still better on several deployment-format metrics

## Most useful next step

The next concrete step should be to carry **two** H2 candidates forward rather than one:
- `teacherforced_rollout0p1_bctdecode`
- `supervised_deltaT_25ep`

and perform the first small DeepFlame-coupled or case-side smoke comparison with exported checkpoints, since the deployment-format evidence no longer supports a single obvious EFNO winner.
