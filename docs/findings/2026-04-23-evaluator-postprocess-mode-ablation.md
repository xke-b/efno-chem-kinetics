# Evaluator postprocess-mode ablation: DeepFlame-style last-species preservation materially changes Burke-aligned H2 conclusions

_Date: 2026-04-23_

## Why this was the next step

The previous DeepFlame compatibility check exposed a real mismatch between:
- the project evaluator's default species reconstruction rule
- the current DeepFlame H2 inference path's reconstruction rule

That meant some of the Burke-aligned offline conclusions were still mixing:
1. model behavior
2. postprocessing behavior

So the next concrete step was to make the evaluator capable of both contracts, then re-evaluate the Burke-aligned comparison under the deployment-facing contract.

## Code change

Updated:
- `/root/workspace/scripts/evaluate_species_delta_checkpoint.py`

New evaluator option:
- `--species-postprocess-mode closure`
- `--species-postprocess-mode preserve_last`

Definitions:
- `closure`: reconstruct `Y_last = 1 - sum(Y_main)`
- `preserve_last`: keep the input last-species value and renormalize predicted main species to sum to `1 - Y_last,input` (matching the current DeepFlame PyTorch H2 inference script)

## Re-evaluation data

Preserve-last re-evaluations were written to:
- `/root/workspace/artifacts/experiments/h2_burke_case_aligned_comparison/*_preserve_last_eval.json`

Cross-summary artifact:
- `/root/workspace/artifacts/experiments/h2_burke_case_aligned_comparison/closure_vs_preserve_last_summary.json`

Compared Burke-aligned seeded cases:
- `supervised_mlp`
- `corrected_self_rollout_predmainbct`

## Closure-mode means (old default evaluator contract)

### Supervised MLP
- one-step species MAE: `1.470e-04`
- one-step temperature MAE: `1.495 K`
- one-step element-mass MAE: `2.274e-04`
- final-horizon rollout species MAE: `5.025e-01`
- final-horizon rollout temperature MAE: `2.070e+05 K`
- final-horizon rollout element-mass MAE: `1.437`

### Corrected self-rollout EFNO
- one-step species MAE: `5.124e-04`
- one-step temperature MAE: `1.039 K`
- one-step element-mass MAE: `1.371e-03`
- final-horizon rollout species MAE: `2.085e-02`
- final-horizon rollout temperature MAE: `9.143e+02 K`
- final-horizon rollout element-mass MAE: `3.179e-02`

Under closure mode, EFNO looked overwhelmingly better on rollout metrics.

## Preserve-last means (DeepFlame-facing evaluator contract)

### Supervised MLP
- one-step species MAE: `9.815e-05`
- one-step temperature MAE: `1.495 K`
- one-step element-mass MAE: `1.554e-05`
- final-horizon rollout species MAE: `1.353e-02`
- final-horizon rollout temperature MAE: `1.794e+02 K`
- final-horizon rollout element-mass MAE: `5.097e-03`

### Corrected self-rollout EFNO
- one-step species MAE: `1.628e-04`
- one-step temperature MAE: `1.039 K`
- one-step element-mass MAE: `4.974e-05`
- final-horizon rollout species MAE: `1.634e-02`
- final-horizon rollout temperature MAE: `3.898e+02 K`
- final-horizon rollout element-mass MAE: `4.373e-03`

## Main interpretation

### 1. The postprocessing contract was not a minor detail
Changing only the last-species reconstruction rule dramatically reduced the apparent Burke rollout failure of the supervised baseline.

For supervised MLP, moving from `closure` to `preserve_last` changed final-horizon means from:
- rollout species MAE: `0.5025 -> 0.0135`
- rollout temperature MAE: `2.07e5 K -> 179 K`
- rollout element-mass MAE: `1.437 -> 0.00510`

So the earlier catastrophic Burke rollout picture for supervised MLP was dominated by evaluator/postprocessing mismatch, not only by the learned dynamics.

### 2. The Burke-aligned ranking becomes much closer under the deployment-facing contract
Under `preserve_last`:
- supervised is better on one-step species and one-step element metrics
- EFNO is better on one-step temperature
- supervised is slightly better on final-horizon rollout species and rollout temperature
- EFNO is slightly better on final-horizon rollout element-mass

That is a much more balanced and much less dramatic picture than the closure-mode summary.

### 3. The deployment-facing contract matters for model-selection decisions
Because DeepFlame H2 currently uses the preserve-last contract, deployment-facing checkpoint comparisons should not rely only on closure-mode evaluator summaries.

For Burke-aligned H2, this changes the practical interpretation from:
- “EFNO is decisively better than supervised on rollout”

to something closer to:
- “under the current DeepFlame species reconstruction contract, the two are competitive, with different strengths”

### 4. The corrected EFNO branch still remains relevant
This is not a negation of the corrected EFNO progress.

Instead, it sharpens the conclusion:
- the EFNO branch is still strong and exportable
- but some apparent rollout advantage on the Burke-aligned benchmark was really a postprocessing-contract artifact
- future deployment-facing checkpoint choices must compare under the same contract the solver will actually use

## Bottom line

Adding `--species-postprocess-mode preserve_last` to the evaluator closed an important offline-to-deployment mismatch.

For the Burke-aligned H2 benchmark, this substantially changes the interpretation of the supervised-vs-EFNO comparison and makes the deployment-facing evidence more trustworthy.

## Most useful next step

Use the new evaluator mode to re-check the most decision-relevant H2 comparisons under the deployment-facing contract before carrying one branch forward into a fuller DeepFlame-coupled test.
