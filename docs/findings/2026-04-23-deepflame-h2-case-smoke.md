# DeepFlame H2 case-side smoke test: 7-species checkpoints are structurally incompatible, and Burke-aligned 9-species exports start but fail after the first DNN-driven updates

_Date: 2026-04-23_

## Why this was the next step

After the exported deployment-format head-to-head, the next concrete step was to stop reasoning from dataset-only evaluation and run an actual **case-side DeepFlame smoke test** on the target H2 example.

## Cases staged

Workspace run area:
- `/root/workspace/runs/deepflame_h2_smoke/`

Primary baseline:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2`

Smoke copies created from that baseline.

## Small case-side modifications

For smoke runs I used a short debug setup:
- `startFrom startTime`
- `endTime 3e-6` or `5e-6` during debugging
- `writeInterval 1e-6` or `5e-6`
- `GPU off`
- `decomposeParDict` adjusted to `4` ranks
- added missing case files required by this solver startup path:
  - `constant/g`
  - `constant/sprayCloudProperties`

These modifications were only for startup/deployment debugging, not a final production case.

## Failure 1: the earlier 7-species H2 candidates cannot be deployed into the target H2 DeepFlame case

I first tried using exported checkpoints from the earlier ES80 7-species H2 benchmark.

That failed during DNN initialization with shape mismatches like:
- checkpoint first layer expected `9` inputs
- target DeepFlame H2 case expects `11` inputs (`T`, `P`, 9 species)

This was not a minor runtime bug. It exposed a structural incompatibility:

> the main earlier H2 offline winners were trained on a 7-species mechanism, while the target DeepFlame H2 case uses Burke 9-species chemistry.

That means those earlier 7-species candidates cannot be carried directly into this case.

This failure was important because it forced the correct next move: use the Burke-aligned 9-species checkpoints instead of trying to force the 7-species branch into the 9-species case.

## Burke-aligned candidates tested next

I exported and smoke-tested the actual 9-species Burke-aligned candidates:
- `/root/workspace/artifacts/models/h2_deepflame_candidates/h2_burke_supervised_mlp_seed0_deepflame.pt`
- `/root/workspace/artifacts/models/h2_deepflame_candidates/h2_burke_corrected_self_rollout_predmainbct_seed0_deepflame.pt`

Case copies:
- `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct`

## Result: both Burke-aligned exported checkpoints start and run through the first DNN-driven step

For both case copies:
- `blockMesh` succeeded
- `decomposePar` succeeded
- `dfLowMachFoam -parallel` started successfully on `4` ranks
- the solver completed the first CVODE-driven step at `1e-6`
- the solver then entered the DNN path at `2e-6`
- the case wrote processor-time outputs at:
  - `1e-06`
  - `2e-06`

That is a meaningful advance over previous uncertainty: the Burke-aligned exported checkpoints are **case-loadable** and can drive at least the initial learned-chemistry updates inside the actual DeepFlame H2 case.

## Failure 2: both Burke-aligned candidates abort on the next DNN-driven step due to HP thermodynamic reconstruction failure

Both runs fail at `Time = 3e-06` inside thermodynamic correction after the DNN species update.

The key error pattern is:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP)`
- `No convergence in 500 iterations`
- then `FOAM FATAL ERROR` from `dfChemistryModel::correctThermo()`

So the current failure mode is not checkpoint loading anymore. It is:

> the case-side species update becomes thermodynamically non-viable under the solver's enthalpy-pressure reconstruction path after the first learned updates.

## Important comparison between the two Burke candidates

At `Time = 2e-06` (the first DNN-driven update), the temperature ranges differ notably.

### Burke supervised
- `min/max(T) = 128.433, 2515.67`

### Burke corrected self-rollout
- `min/max(T) = 499.994, 2481.14`

Interpretation:
- both runs still eventually fail at `3e-06`
- but the corrected Burke self-rollout branch appears to produce a much less extreme first DNN-driven temperature excursion than the Burke supervised branch

That does **not** mean it is solved, but it is a meaningful mechanistic clue.

## What this changes

### 1. The true case-side gating issue is now clearer
The main blocker is no longer:
- checkpoint export format
- case startup wiring
- Python inference entrypoint compatibility

The new bottleneck is:
- **thermodynamic consistency / HP reconstruction stability after learned species updates inside the actual case**

### 2. The 7-species H2 line should not be treated as directly deployable to the target H2 case
The smoke test showed that mechanism/species-count alignment is a hard requirement, not a soft preference.

### 3. The Burke-aligned path is now the correct deployment branch
The target DeepFlame H2 case should be explored with Burke-aligned 9-species checkpoints, not the earlier 7-species longprobe winners.

## Bottom line

The first actual DeepFlame H2 case-side smoke test produced two important results:

1. **negative but useful**: earlier 7-species H2 candidates are structurally incompatible with the target 9-species Burke case
2. **positive but incomplete**: Burke-aligned exported checkpoints load, start, run through early DNN-driven updates, and write output up to `2e-06`, but both currently fail at `3e-06` during HP thermodynamic reconstruction

## Most useful next step

The next step should focus specifically on the new true bottleneck:
- inspect the written `1e-06` and `2e-06` fields from the Burke smoke cases
- quantify whether the pre-failure states violate reasonable thermochemical bounds or species simplex structure
- use that to decide whether the next intervention should be:
  - species clipping / safer deployment postprocessing,
  - mixed deployment constraints,
  - or re-training Burke-aligned candidates with deployment-facing thermodynamic stability objectives
