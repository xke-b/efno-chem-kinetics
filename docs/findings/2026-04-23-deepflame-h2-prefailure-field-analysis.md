# DeepFlame H2 pre-failure field analysis: the early Burke smoke failure is driven more by thermodynamic temperature excursions than by obvious species-simplex collapse

_Date: 2026-04-23_

## Why this was the next step

The first Burke-aligned DeepFlame H2 smoke runs established that exported checkpoints:
- load into the real case
- survive the first learned updates
- then fail at about `3e-06` during Cantera HP reconstruction

So the next useful step was to inspect the last successfully written fields at `2e-06` to see what is already going wrong before the HP failure.

## Added analysis script

- `/root/workspace/scripts/analyze_deepflame_h2_smoke_fields.py`

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_mlp_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/comparison_summary.json`

## Cases analyzed

- `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct`

Compared written fields at:
- reference: `1e-06`
- pre-failure checkpoint: `2e-06`

## Important small finding about debugging observability

The written `selectDNN` field at `2e-06` is uniformly zero in these smoke cases, even though `run.log` clearly reports thousands of DNN inference points.

So for now, `selectDNN` is not a reliable field-level diagnostic of where learned chemistry was actually applied in this case configuration.

## Main result 1: both runs still satisfy the species simplex extremely well at `2e-06`

### Burke supervised
- species-sum min: `0.9999989075`
- species-sum max: `1.00000122528`
- mean abs deviation from `1`: `3.39e-09`
- max abs deviation from `1`: `1.23e-06`

### Burke corrected self-rollout
- species-sum min: `0.9999989070`
- species-sum max: `1.0000010121`
- mean abs deviation from `1`: `3.32e-09`
- max abs deviation from `1`: `1.09e-06`

Interpretation:
- the pre-failure written fields are still essentially on-simplex
- so the current case-side failure is **not** explained by gross species-sum drift or obvious species negativity in the written state

## Main result 2: the clearest difference is temperature behavior, not mass-fraction closure

### Burke supervised at `2e-06`
- global `min/max(T) = 128.433, 2515.67`
- fraction of cells with `T < 400 K`: `9.54e-05`
- fraction of cells with `T < 300 K`: `4.01e-05`
- fraction of cells with `T < 200 K`: `3.81e-06`
- fraction of cells with `T < 150 K`: `1.91e-06`

The coldest cell had:
- `T = 128.433 K`
- `p = 92453.6 Pa`
- dominant composition:
  - `N2 = 0.74566`
  - `H2O = 0.148926`
  - `O2 = 0.0864376`
  - `H = 0.0104354`
  - `O = 0.0042259`
  - `H2 = 0.00340273`

Relative to `1e-06`, that cold cell changed strongly, including:
- `H2O: +0.14676`
- `O2: -0.13812`
- `H: +0.01043`
- `O: +0.00422`
- `H2: -0.02462`

### Burke corrected self-rollout at `2e-06`
- global `min/max(T) = 499.994, 2481.14`
- fraction of cells with `T < 400 K`: `0`
- fraction of cells with `T < 300 K`: `0`
- fraction of cells with `T < 200 K`: `0`
- fraction of cells with `T < 150 K`: `0`

The coldest cell was still essentially unchanged from the initial low-temperature state:
- `T = 499.994 K`
- `p = 101319 Pa`
- dominant composition remained close to the initial mixture:
  - `N2 = 0.745124`
  - `O2 = 0.226354`
  - `H2 = 0.028522`

## Main result 3: the supervised Burke branch shows a localized but severe low-temperature excursion before failure

The key contrast is:
- **supervised Burke** already produces rare but severe cold outliers by `2e-06`
- **corrected self-rollout Burke** does not show those cold outliers in the written `2e-06` fields

That aligns with the earlier log-based observation that the supervised branch had much more extreme temperature behavior before the HP crash.

## Main interpretation

### 1. The immediate issue is not “species are obviously invalid everywhere”
The pre-failure written states remain near-perfect on the species simplex.

So the main case-side instability seems subtler than simple mass-fraction closure failure.

### 2. The more informative early warning signal is thermodynamic extremeness
The supervised Burke branch already creates physically suspicious low-temperature pockets by `2e-06`, including cells near `128 K` inside a hot reacting flow.

That is a much stronger warning sign for the later HP reconstruction failure than anything visible in species-sum diagnostics.

### 3. The corrected self-rollout Burke branch still fails, but it fails from a less visibly pathological written state
The corrected branch still aborts at `3e-06`, so it is not yet stable enough.

But at the last written time it looks materially healthier than the supervised Burke branch on temperature extrema.

That suggests the next intervention should focus on **thermodynamic robustness after species updates**, not only on simplex-preserving species postprocessing.

## Bottom line

The pre-failure field analysis narrows the diagnosis:
- the case-side Burke failures are **not** primarily caused by obvious species-simplex collapse in the written fields
- the stronger visible pathology is **temperature excursion behavior**, especially the rare very cold cells in the Burke supervised run
- the corrected Burke self-rollout branch looks better on that specific signal, even though it still ultimately fails

## Most useful next step

The next concrete step should be to inspect the thermodynamic reconstruction pathway itself around the failing update, for example by instrumenting or approximating:
- local enthalpy before/after DNN update
- predicted species changes in the coldest / most rapidly changing cells
- whether a deployment-side safeguard such as bounded species update magnitude, temperature floor-aware fallback, or hybrid CVODE fallback on flagged cells would likely prevent the HP failure
