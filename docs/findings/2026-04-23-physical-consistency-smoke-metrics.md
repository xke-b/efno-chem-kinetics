# Physical-consistency smoke metrics now tracked for baseline checkpoints

_Date: 2026-04-23_

## What changed

The rollout evaluator was extended to compute physics-relevant quantities from the local mechanism:
- one-step element-mass MAE
- rollout element-mass MAE by horizon
- rollout mass-sum MAE by horizon

This is still a **species-only evaluator**, so it remains an intermediate tool rather than a full paper-faithful EFNO benchmark. But it materially improves evidence quality because the EFNO paper is explicitly about physical consistency, not only regression accuracy.

## Evaluated checkpoints

1. **Baseline MLP + `supervised_physics` trainer**
2. **Provisional `fno1d` + `supervised_physics` trainer**
3. **MLP + new `efno_style` trainer**

All evaluations used the local smoke dataset:
- `/root/workspace/data/h2_autoignition_smoke.npy`
- mechanism: `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml`

## One-step results

| Model / trainer | species MAE | element-mass MAE | mass-sum MAE |
| --- | ---: | ---: | ---: |
| MLP + supervised_physics | 2.36e-03 | 5.50e-03 | 6.87e-09 |
| FNO1d + supervised_physics | 1.65e-02 | 3.86e-02 | 3.66e-09 |
| MLP + efno_style | 2.24e-03 | 5.22e-03 | 7.33e-09 |

## Rollout highlights at horizon 10

| Model / trainer | rollout species MAE | rollout element-mass MAE | rollout mass-sum MAE |
| --- | ---: | ---: | ---: |
| MLP + supervised_physics | 3.96e-01 | 7.52e-01 | 7.79e-01 |
| FNO1d + supervised_physics | 1.83e-01 | 4.27e-01 | 8.38e-09 |
| MLP + efno_style | 5.91e-02 | 1.38e-01 | 2.79e-09 |

## Interpretation

### 1. The new evaluator is immediately useful
The new metrics clearly separate models that may have similar one-step performance but different rollout physical behavior.

### 2. The `efno_style` trainer materially improves rollout behavior on the smoke test
Compared with the earlier MLP baseline, the `efno_style` trainer greatly reduced:
- rollout species error
- rollout element-mass drift
- rollout mass-sum drift

This is only a tiny experiment, but it is exactly the kind of evidence we need to prioritize physics-aware training paths.

### 3. The provisional `fno1d` scaffold is still not competitive here
On this smoke case, `fno1d` remains weaker than the MLP variants in one-step and element-consistency metrics. Its mass-sum behavior stays numerically tight, but its rollout element error remains much larger than the `efno_style` MLP.

### 4. Rollout diagnostics matter more than one-step diagnostics
The strongest insight from this step is that one-step metrics alone would have hidden major differences in long-horizon physical behavior.

## Direct implication for the project

The next useful thread is not just “make a bigger Fourier model.” It is:
1. preserve the new physical-consistency evaluator
2. compare trainers on a somewhat larger H2 dataset
3. then test whether the same physics-aware ideas help a Fourier backbone, not only an MLP

## Artifact locations

- MLP eval: `/root/workspace/artifacts/h2_autoignition_smoke_mlp_eval.json`
- FNO1d eval: `/root/workspace/artifacts/h2_autoignition_smoke_fno1d_eval.json`
- MLP + efno_style eval: `/root/workspace/artifacts/h2_autoignition_smoke_mlp_efno_style_eval.json`
