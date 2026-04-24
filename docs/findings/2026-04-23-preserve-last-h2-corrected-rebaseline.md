# Preserve-last re-baseline of corrected H2 comparisons: deployment-facing postprocessing changes the corrected-decode ranking

_Date: 2026-04-23_

## Why this was the next step

After adding `--species-postprocess-mode preserve_last` to the evaluator and seeing that it materially changed the Burke-aligned H2 conclusions, the next most useful step was to re-check the **main corrected-decode H2 comparison set** that had been driving offline-to-DeepFlame planning.

That meant revisiting the ES80-based H2 holdout benchmark under the current DeepFlame-style species reconstruction contract.

## Evaluated cases

Dataset:
- `/root/workspace/data/h2_autoignition_longprobe_test.npy`
- `/root/workspace/data/h2_autoignition_longprobe_test.json`

Re-evaluated seeded cases under `--species-postprocess-mode preserve_last`:
- `supervised_deltaT_25ep`
- `baseline_norollout_bctdecode`
- `teacherforced_rollout0p1_bctdecode`
- `self_rollout0p1_bctdecode`
- `self_rollout0p1_predicted_main_bct_bctdecode`

Artifacts:
- `/root/workspace/artifacts/experiments/h2_preserve_last_rebaseline/summary.json`
- `/root/workspace/artifacts/experiments/h2_preserve_last_rebaseline/closure_vs_preserve_last_summary.json`
- per-checkpoint evals under `/root/workspace/artifacts/experiments/h2_preserve_last_rebaseline/`

## Small failure recorded

The first batch re-evaluation attempt failed because the output directory did not exist yet.

That failure was useful rather than terminal: it confirmed the evaluator still assumes the parent output path already exists. I created:
- `/root/workspace/artifacts/experiments/h2_preserve_last_rebaseline/`

and reran successfully.

## Closure-mode means (legacy project-side comparison contract)

### Supervised baseline
- one-step species MAE: `6.228e-05`
- one-step temperature MAE: `0.1752 K`
- one-step element-mass MAE: `1.231e-04`
- rollout species MAE @1000: `2.779e-01`
- rollout temperature MAE @1000: `1494.33 K`
- rollout element-mass MAE @1000: `6.294e-01`

### Corrected no-rollout baseline
- rollout species MAE @1000: `9.898e-02`
- rollout temperature MAE @1000: `1900.70 K`
- rollout element-mass MAE @1000: `1.980e-01`

### Corrected teacher-forced rollout
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `704.71 K`
- rollout element-mass MAE @1000: `5.777e-02`

### Corrected self-rollout
- rollout species MAE @1000: `1.017e-02`
- rollout temperature MAE @1000: `95.98 K`
- rollout element-mass MAE @1000: `1.034e-02`

### Corrected self-rollout + predicted-main-BCT
- rollout species MAE @1000: `7.715e-03`
- rollout temperature MAE @1000: `73.52 K`
- rollout element-mass MAE @1000: `6.237e-03`

Under closure mode, the best corrected self-rollout branch looked decisively best overall on rollout metrics.

## Preserve-last means (DeepFlame-facing contract)

### Supervised baseline
- one-step species MAE: `2.419e-05`
- one-step temperature MAE: `0.1752 K`
- one-step element-mass MAE: `5.842e-06`
- rollout species MAE @1000: `5.985e-03`
- rollout temperature MAE @1000: `105.95 K`
- rollout element-mass MAE @1000: `3.313e-03`

### Corrected no-rollout baseline
- one-step species MAE: `5.897e-05`
- one-step temperature MAE: `0.1430 K`
- one-step element-mass MAE: `1.717e-05`
- rollout species MAE @1000: `8.613e-03`
- rollout temperature MAE @1000: `100.38 K`
- rollout element-mass MAE @1000: `4.913e-03`

### Corrected teacher-forced rollout
- one-step species MAE: `3.208e-05`
- one-step temperature MAE: `0.1210 K`
- one-step element-mass MAE: `1.174e-05`
- rollout species MAE @1000: `4.141e-03`
- rollout temperature MAE @1000: `91.18 K`
- rollout element-mass MAE @1000: `2.199e-03`

### Corrected self-rollout
- one-step species MAE: `3.535e-05`
- one-step temperature MAE: `0.1240 K`
- one-step element-mass MAE: `1.338e-05`
- rollout species MAE @1000: `4.154e-03`
- rollout temperature MAE @1000: `88.63 K`
- rollout element-mass MAE @1000: `2.864e-03`

### Corrected self-rollout + predicted-main-BCT
- one-step species MAE: `3.542e-05`
- one-step temperature MAE: `0.1235 K`
- one-step element-mass MAE: `1.277e-05`
- rollout species MAE @1000: `4.269e-03`
- rollout temperature MAE @1000: `94.38 K`
- rollout element-mass MAE @1000: `2.203e-03`

## Main interpretation

### 1. The deployment-facing contract sharply compresses the apparent gap between branches
Under preserve-last postprocessing, all of the corrected rollout-aware branches and the supervised baseline become much closer than they looked under closure-mode summaries.

The biggest change is the supervised baseline:
- rollout species MAE: `0.2779 -> 0.0060`
- rollout temperature MAE: `1494 K -> 106 K`
- rollout element-mass MAE: `0.629 -> 0.00331`

So the old closure-mode comparison substantially overstated the deployment-facing weakness of the supervised baseline.

### 2. The best corrected branch under closure mode is no longer the obvious deployment-facing winner
Under preserve-last:
- **best rollout species MAE**: `teacherforced_rollout0p1_bctdecode` (`0.004141`)
- **best rollout temperature MAE**: `self_rollout0p1_bctdecode` (`88.63 K`)
- **best rollout element-mass MAE**: `teacherforced_rollout0p1_bctdecode` (`0.002199`), narrowly ahead of `self_rollout0p1_predicted_main_bct_bctdecode` (`0.002203`)

The previously favored `self_rollout0p1_predicted_main_bct_bctdecode` branch is still strong, but it is no longer the clean best rollout choice once the postprocessing contract matches DeepFlame.

### 3. Supervised remains competitive even under the deployment-facing contract
Under preserve-last:
- supervised is still best on one-step species and element metrics
- rollout-aware corrected branches are better on temperature and usually better on rollout species/element metrics
- but the gap is now modest, not dramatic

That makes the deployment-facing H2 story much more nuanced than the earlier closure-mode narrative.

### 4. For DeepFlame-facing selection, teacher-forced rollout deserves renewed attention
One concrete change in understanding is that the old corrected-decode search had shifted emphasis toward non-oracle self-rollout branches because the closure-mode summaries strongly favored them.

Under preserve-last, the **teacher-forced corrected branch re-emerges as a top deployment-facing candidate**:
- best rollout species
- best rollout element-mass
- strong rollout temperature
- better one-step species/element metrics than the self-rollout corrected branches

## Bottom line

For the main corrected H2 comparison set, moving from closure reconstruction to the DeepFlame-style preserve-last contract materially changes the ranking and weakens the earlier claim that `self_rollout0p1_predicted_main_bct_bctdecode` is the clear best offline branch for deployment-facing use.

Under the current DeepFlame contract, the leading corrected rollout-aware branches are much closer, and `teacherforced_rollout0p1_bctdecode` is again a serious contender.

## Most useful next step

Before committing to a single H2 branch for deeper DeepFlame integration, run a **small deployment-facing head-to-head** between:
- `supervised_deltaT_25ep`
- `teacherforced_rollout0p1_bctdecode`
- `self_rollout0p1_bctdecode`
- `self_rollout0p1_predicted_main_bct_bctdecode`

using the exported DeepFlame-compatible checkpoints and the same preserve-last contract throughout.
