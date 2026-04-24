# C2H4 oneD-only `100k` Xiao-style power-delta promotion: scaling the solver-native chemistry dataset alone does not yet rescue deployment, and the promoted case fails at the first learned step after `1e-7`

_Date: 2026-04-24_

## Why this was the next step

After proving that the oneD/Xiao solver-native data path can scale to `100k` labeled states, the next useful question was not abstract throughput anymore, but model usefulness:

- if we train a larger oneD-only chemistry model on that `100k` dataset,
- does deployment improve relative to the earlier `20k` oneD-augmented path,
- or does scaling the oneD chemistry manifold alone still miss the real C2H4 deployment bottleneck?

This was the sharpest way to turn the new scaling path into scientific evidence.

## Training setup

Dataset:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.npy`
- metadata: `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.json`

Tag:
- `c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val.pt`

Bundle:
- `/root/workspace/artifacts/models/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_baseline/summary.json`

Configuration:
- target: `species_power_delta`
- epochs budget: `100`
- validation fraction: `0.1`
- train / validation rows: `90000 / 10000`
- batch size: `1024`
- GPU training
- scheduler: reduce-on-plateau
- best epoch: `100`
- best validation loss: `0.17527415603399277`

## Immediate offline context

This oneD-only `100k` model is not obviously a stronger offline candidate than the mixed-data promoted branches.

For comparison:
- mixed `dp100 + oneD@0.2` promoted power-delta best val loss: `0.13110`
- mixed promoted power-delta + interleaved attention best val loss: `0.11611`
- oneD-only `100k` promoted power-delta best val loss: `0.17527`

So even before deployment, the scaled oneD-only chemistry path still looks harder to fit than the mixed-data branch.

## DeepFlame deployment result

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_np8`

Logs:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_np8/run.log`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val_np8/solver.err`

Main result:
- the case writes `1e-07`
- the first DNN-active step begins at `2e-07`
- the solver then fails in HP reconstruction during thermodynamic correction

So this promoted oneD-only model does **not** reproduce the earlier oneD result that survived to `1e-6`.

## Failure signature

At `2e-07`, the run log shows:
- `real inference points number: 33508`
- learned chemistry is active on GPU
- the case proceeds through the DNN solve and transport solves
- then fails in `ThermoPhase::setState_HPorUV (HP)`

Representative failures from the log:
- target enthalpy `345256.040355552`, pressure `103386.46557871485`, starting temperature `1798.7908024982587`
- target enthalpy `344350.046386085`, pressure `103801.13995642077`, starting temperature `431.06374830526073`

The second failed state is especially informative because the starting temperature is only about `431 K`, so the failure is not confined to the hottest tail.

## Interpretation

This is a useful negative result.

### What it tells us

1. **Scaling the oneD/Xiao chemistry dataset alone is not enough.**
   - We now have a larger solver-native chemistry dataset, but the oneD-only deployment path is still not a solver-usable replacement.

2. **More oneD chemistry support does not automatically fix HP stability.**
   - In fact, this promoted `100k` oneD-only power-delta model fails much earlier in-case than the earlier `20k` oneD smoke baseline.

3. **The oneD path still looks better as a backbone or augmentation source than as a standalone deployment target.**
   - This is consistent with earlier evidence that pure oneD-derived models can preserve some broad manifold structure while still failing badly on the solver-relevant reactive transition states.

4. **The next scaling move should prioritize mixed-data or hybrid semantics, not pure oneD-only scaling.**
   - The more promising direction now remains:
     - mixed `dp100 + oneD`
     - larger oneD add-on fractions or staged mixtures
     - promoted attention / weighting variants under the mixed-data regime

## Current takeaway

The `100k` scaling milestone is still valuable, but it narrows the conclusion:

> the oneD/Xiao solver-native path is scalable, but scaling it as a standalone chemistry-label source does not yet produce a deployment-positive C2H4 surrogate.

That means the project should keep using the oneD/Xiao path, but more likely as:
- a **supplemental chemistry manifold source**
- a larger add-on to a case-aligned backbone
- or a generator for richer hybrid datasets rather than a pure training source by itself

## Most useful next step

The next justified experiment is now:
1. keep the new scale-ready oneD/Xiao data pipeline
2. move back to the **mixed-data deployment regime**
3. test whether the promoted interleaved-attention branch or a larger mixed-data chemistry supplement can use the richer oneD support without inheriting the standalone path’s early HP failure
