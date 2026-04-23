# EFNO-style trainer slice added: weighted data loss plus element and mass conservation

_Date: 2026-04-23_

## Why this step was next

The most useful unfinished thread was to move from a generic Fourier-model scaffold toward a **paper-oriented EFNO training path**.

The EFNO paper emphasizes three ingredients beyond a vanilla backbone:
- imbalance-aware weighted data loss
- element conservation
- mass-fraction-sum conservation

So the next concrete step was to encode those ideas into DFODE-kit in a minimal, testable training slice.

## What was added in DFODE-kit

### New trainer
- `dfode_kit/training/efno_style.py`

This trainer is an **approximation** of the paper's stated ingredients, not a claim of exact reproduction.

Implemented components:
1. **weighted data loss**
   - per-sample weights from adjacent species-change magnitude
   - quartile-style weighting inspired by the paper text
   - current values:
     - `1.0` for high-change samples
     - `0.5` for middle band
     - `0.1` for low-change samples
2. **element conservation loss**
   - based on a mechanism-derived species-to-element mass mapping
3. **mass-fraction-sum loss**
   - enforces total species mass fraction close to 1

### Training config extension
- `TrainerConfig` now includes `params`

This enables explicit trainer-side weights such as:
- `lambda_data`
- `lambda_elements`
- `lambda_mass`

### Training pipeline updates
- training now computes:
  - sample weights
  - element-mass matrix from the mechanism
- both are passed into the trainer path when needed

## Important limitation

This still does **not** make the setup fully paper-faithful.

Main reason:
- the current DFODE-kit target still predicts **species updates only**, not the joint temperature/species evolution discussed in the paper

So this is best understood as a **paper-oriented intermediate slice**.

## Smoke evidence collected

Using the same tiny H2 autoignition smoke dataset, I trained an MLP with the new `efno_style` trainer for 2 epochs.

Observed training losses:

```text
Epoch: 1, DataLoss: 7.056735e-05, ElementLoss: 9.828720e-03, MassLoss: 1.788139e-08, Loss: 9.899305e-03
Epoch: 2, DataLoss: 4.422473e-05, ElementLoss: 6.008797e-03, MassLoss: 1.713634e-08, Loss: 6.053039e-03
```

Evaluation against the same smoke dataset produced:
- one-step species MAE: `2.24e-03`
- one-step species RMSE: `4.11e-03`
- rollout species MAE by horizon:

```text
[0.00139, 0.00312, 0.00732, 0.01915, 0.03400, 0.04221, 0.05033, 0.05795, 0.05856, 0.05906]
```

## Comparison to earlier smoke MLP baseline

Earlier smoke MLP baseline rollout MAE by horizon ended at roughly:
- `0.396` by horizon 10

The new `efno_style` trainer ended at roughly:
- `0.059` by horizon 10

This is only a tiny smoke test, but it is still valuable evidence:
- the new trainer is numerically stable
- conservation-aware / weighted training can materially affect rollout behavior
- rollout-sensitive evaluation is already changing design decisions, which is exactly what the project needs

## Failures treated as information

During this step, an implementation attempt assumed Cantera `Species` objects exposed `molecular_weight`; that failed in the local environment. The fix was to use `gas.molecular_weights[s_idx]` instead. This clarified the mechanism-matrix implementation path and was folded into the final code.

## Most useful next step

Now that a first EFNO-style trainer exists, the next best move is:
1. compare `supervised_physics` vs `efno_style` on a slightly larger H2 dataset
2. add explicit physical-consistency metrics to the evaluator
3. decide whether to extend the current species-only target or move to a joint temperature+species target that is closer to the paper
