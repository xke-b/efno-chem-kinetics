# EFNO gated teacher/self ablation: conservative gating collapses back to pure teacher forcing because the self-generated second-step features are still far away

_Date: 2026-04-23_

## Why this was the next step

After fixed-ratio and scheduled teacher/self mixing both degraded the best teacher-forced EFNO branch, the next useful idea was to try a more selective exposure-bias bridge:

> Only use the self-generated second-step input when it is already close enough to the teacher-forced second-step input.

That is a more state-aware strategy than either:
- fixed global mixing
- globally scheduled mixing

## Implementation

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

Added rollout mode:
- `rollout_consistency_mode = "gated_teacher_self"`

Added parameter:
- `rollout_self_gate_threshold`

Behavior:
- compute self-generated normalized second-step features
- compare them to teacher-forced normalized second-step features using per-sample mean absolute difference
- if the gap is below threshold, use the self-generated version
- otherwise, fall back to the teacher-forced version

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_gated_teacher_self_ablation.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_ablation/summary.json`

Tested gates:
1. `threshold = 0.25`
2. `threshold = 0.5`

Reference:
- pure teacher-forced two-step EFNO

## Main result

Both gated runs produced the **same aggregate metrics** as the pure teacher-forced reference.

That initially looks surprising, but the follow-up diagnosis explains it.

## Follow-up diagnosis: why the gate did nothing

I computed the distribution of per-sample mean absolute gap between:
- self-generated normalized second-step features
- teacher-forced normalized second-step features

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_gated_teacher_self_ablation/feature_gap_seed0_summary.json`

For the seed-0 teacher-forced checkpoint on the training rollout pairs:
- mean gap: `2.16`
- min gap: `1.61`
- 1% quantile: `1.69`
- 5% quantile: `1.82`
- median: `1.98`
- 95% quantile: `2.95`

So thresholds like `0.25` and `0.5` were far below even the **minimum** observed gap.

That means the gate almost never, effectively never, selected self-generated second-step features.

## What this teaches us

### 1. Conservative gating currently reduces to pure teacher forcing
This is useful evidence, not a dead end.

It means the self-generated second-step features are not just a little noisy; they are still far enough from the teacher-forced second-step features that a cautious gate will almost always reject them.

### 2. The bottleneck is now quantitatively clearer
The project already suspected that the self-generated second-step features were poor.

Now there is direct quantitative evidence that their normalized feature mismatch is typically around `2` in mean absolute difference per sample on this benchmark.

### 3. A useful gate cannot be chosen blindly
A threshold-based bridge now needs either:
- much larger thresholds
- thresholding on a different signal
- a more meaningful confidence measure than raw normalized feature difference

## Bottom line

This was a productive diagnostic failure.

The gated teacher/self idea did not produce a new best model, but it revealed something important:
- the current self-generated second-step features are so far from the teacher-forced ones that conservative gating simply falls back to teacher forcing everywhere

That sharpens the next design question from:
- “should we mix teacher and self?”

to:
- “what signal could identify *trustworthy* self-generated second-step states, or how can we reduce the gap itself?”
