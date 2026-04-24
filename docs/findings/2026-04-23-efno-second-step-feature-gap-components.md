# EFNO second-step feature-gap component analysis: the self-vs-teacher mismatch is overwhelmingly a species-BCT problem, with the reconstructed last species dominating

_Date: 2026-04-23_

## Why this was the next step

The exposure-bias thread has now produced a clear pattern:
- pure teacher forcing works well
- self-fed training is harmful
- mixing, schedules, and gating all fail once too much self-generated second-step input is admitted

So the next most useful question was no longer _whether_ the self-generated second-step features are bad. That is already established.

The sharper question is:

> Which components of the second-step feature vector are actually causing the gap?

That matters because the second-step feature vector combines:
- temperature
- pressure
- Box-Cox-transformed species features

If the mismatch is concentrated in one part of that vector, the next structural change should target that part rather than treating the whole feature vector as equally problematic.

## Analysis setup

Script:
- `/root/workspace/scripts/analyze_h2_second_step_feature_gap_components.py`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_ablation/feature_gap_seed0_summary.json`
- `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_ablation/feature_gap_components_seed0.json`

Checkpoint analyzed:
- `/root/workspace/data/h2_holdout_mlp_teacherforced_rollout0p1_tempw_0p1_speciesw_4p0_seed0.pt`

Dataset analyzed:
- `/root/workspace/data/h2_autoignition_longprobe_train.npy`

Species order from dataset metadata:
- `H`
- `O`
- `H2O`
- `OH`
- `O2`
- `H2`
- `N2`

## Main result

Overall mean absolute normalized second-step feature gap:
- `2.1608`

Group means:
- temperature: `2.08e-04`
- pressure: `0.0`
- species-BCT mean: `2.7781`

So the self-vs-teacher mismatch is **not** a temperature problem and not a pressure problem.
It is overwhelmingly a **species-BCT feature problem**.

## Per-component mean absolute normalized gap

- temperature: `0.00021`
- pressure: `0.0`
- `H`: `1.8671`
- `O`: `1.6107`
- `H2O`: `0.6893`
- `OH`: `1.4310`
- `O2`: `0.9940`
- `H2`: `2.8544`
- `N2`: `10.0`

## Most important interpretation

### 1. Temperature is not the issue in second-step feature construction
The temperature component is essentially negligible relative to the species-feature gap.

That is important because several earlier results showed that EFNO-style branches often had competitive or better temperature behavior. This analysis is consistent with that.

### 2. The gap is concentrated in species re-encoding, especially `H2` and the reconstructed final species `N2`
The largest mean gaps are:
- `N2`: `10.0`
- `H2`: `2.85`
- then `H`, `O`, and `OH`

This is a strong clue.

### 3. The reconstructed last species is the standout pathology
In the current contract, only the first `n_species - 1` species deltas are predicted directly. The last species is reconstructed by mass closure:
- `Y_last = 1 - sum(Y_main)`

That reconstructed final species is then Box-Cox transformed and used in the next-step feature vector.

For this H2 benchmark, the final species is `N2`, and its normalized second-step feature gap is enormous compared with every other component.

That strongly suggests that one major source of self-fed second-step mismatch is the **closure-reconstructed last species channel** in the feature builder.

## What this changes

This is the clearest mechanistic diagnosis so far for the exposure-bias problem.

The project can now say more precisely:
- the problem is not “autoregression” in the abstract
- it is not primarily temperature drift in the second-step input
- it is not evenly spread across all species features
- it is strongly concentrated in the **species Box-Cox re-encoding path**, with the largest pathology in the **closure-reconstructed final species feature**

## Bottom line

This analysis materially sharpens the next intervention target.

If the next structural experiment aims to improve self-generated second-step features, the most credible first target is now:
- the treatment of the final closure-reconstructed species channel in the second-step feature vector

rather than more generic teacher/self mixing or threshold tuning.
