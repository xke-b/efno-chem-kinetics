# Teacher-forced two-step EFNO vs supervised MLP: the best current EFNO branch now wins the rollout tradeoff decisively

_Date: 2026-04-23_

## Why this comparison mattered

After the teacher-forced two-step ablation, the obvious next question was no longer whether that EFNO variant beats the older EFNO baselines. It does.

The more important question was:

> Does the new teacher-forced EFNO branch actually close the gap to the seeded supervised MLP reference, or does it just improve within the EFNO family?

That is the key benchmark question for the current offline reproduction track.

## Inputs used

This comparison re-used existing seeded experiment artifacts with the same:
- H2 longprobe holdout split
- `25` training epochs
- seeds `0,1,2`
- `MLP [64,64]` backbone

Source summaries:
- supervised reference:
  - `/root/workspace/artifacts/experiments/h2_temp_species_seeded_replicates/summary.json`
- EFNO teacher-forced ablation:
  - `/root/workspace/artifacts/experiments/h2_efno_teacher_forced_rollout_ablation/summary.json`

Comparison script:
- `/root/workspace/scripts/compare_h2_teacherforced_vs_supervised.py`

Comparison artifact:
- `/root/workspace/artifacts/experiments/h2_teacherforced_vs_supervised_comparison/summary.json`

Cases compared:
1. `supervised_deltaT_25ep`
2. `baseline_tempw_0p1_speciesw_4p0`
3. `teacherforced_rollout0p1_tempw_0p1_speciesw_4p0`

## Mean metrics

### Supervised MLP reference
- one-step species MAE: `6.23e-05`
- one-step temperature MAE: `1.75e-01 K`
- one-step element-mass MAE: `1.23e-04`
- rollout species MAE @1000: `2.78e-01`
- rollout temperature MAE @1000: `1.49e+03 K`
- rollout element-mass MAE @1000: `6.29e-01`

### Previous best one-step EFNO baseline
- one-step species MAE: `1.12e-04`
- one-step temperature MAE: `1.43e-01 K`
- one-step element-mass MAE: `1.61e-04`
- rollout species MAE @1000: `9.90e-02`
- rollout temperature MAE @1000: `1.90e+03 K`
- rollout element-mass MAE @1000: `1.98e-01`

### Best current teacher-forced EFNO branch
- one-step species MAE: `8.25e-05`
- one-step temperature MAE: `1.21e-01 K`
- one-step element-mass MAE: `1.56e-04`
- rollout species MAE @1000: `2.97e-02`
- rollout temperature MAE @1000: `7.05e+02 K`
- rollout element-mass MAE @1000: `5.78e-02`

## Relative comparison: teacher-forced EFNO vs supervised

Teacher-forced EFNO is:
- **32.5% worse** on one-step species MAE
- **30.9% better** on one-step temperature MAE
- **26.4% worse** on one-step element-mass MAE
- **89.3% better** on rollout species MAE @1000
- **52.8% better** on rollout temperature MAE @1000
- **90.8% better** on rollout element-mass MAE @1000

## Main conclusion

This is the most important benchmark update so far:

### The best current EFNO-style branch no longer trails supervised overall
Instead, it now shows a **clear tradeoff inversion**:
- supervised remains better on the most local one-step species and element metrics
- teacher-forced EFNO is much better on temperature prediction and dramatically better on long-horizon rollout behavior

Given the project goal of usefulness in coupled simulation, that is a major shift.

## Why this is scientifically useful

This result sharpens the story from vague to specific:

### Old picture
- supervised looked strongest overall
- EFNO looked interesting but structurally weaker

### New picture
- one-step supervised fitting is still strongest for species-local accuracy
- but the best EFNO branch is now clearly stronger on the rollout side that matters for autoregressive use

That means the choice is no longer “supervised wins, EFNO loses.”
It is now a **one-step fidelity vs rollout stability/consistency tradeoff**.

## Interpretation

The teacher-forced result suggests that EFNO-style objectives are especially helpful for shaping dynamics over time, but the previous self-fed training path hid that benefit behind exposure-bias and reconstruction errors.

So the current evidence supports this view:
- EFNO-style learning can produce better rollout behavior than the plain supervised reference
- but the training procedure must avoid or soften the damaging self-fed second-step input construction used in the naive rollout-consistency attempt

## Decision update

For the offline H2 thermochemical benchmark, the best current EFNO branch should now be treated as:
- a credible competitor to supervised MLP
- likely the stronger branch when rollout behavior is prioritized

## Next most useful step

The next structural experiment should target the gap between:
- teacher-forced training-time benefit
- self-fed inference-time reality

The best next move is therefore not more scalar tuning. It is an exposure-bias bridge such as:
- mixed teacher-forced / self-fed second-step inputs
- scheduled sampling style transition
- limited-noise perturbation of next-step features during teacher-forced two-step training

## Bottom line

The project now has direct evidence that the best current EFNO branch can beat the seeded supervised MLP reference on the metrics most closely tied to rollout usefulness, even while still losing on the most local one-step species and element metrics.

That is a meaningful advance in both understanding and benchmark position.
