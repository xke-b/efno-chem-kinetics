# First case-aligned C2H4 FNO integration result: the CFD-state-pair FNO reaches `1e-6` cleanly and removes the early collapse seen with the homogeneous-smoke FNO

_Date: 2026-04-24_

## Why this was the next step

After establishing that the original homogeneous C2H4 smoke dataset was badly mismatched to the active-state distribution of the real DeepFlame C2H4 case, the most useful next step was to test whether a first case-aligned dataset could improve actual case-side survival.

The immediate goal was pragmatic:
- train a small FNO on the extracted CFD state-pair dataset
- export it into the existing DeepFlame FNO bundle format
- run it in the real C2H4 case
- compare its short-horizon behavior against the earlier homogeneous-smoke FNO baseline

## What I built

### Case-aligned FNO runner
- `/root/workspace/scripts/run_c2h4_casepair_fno_baseline.py`

This trains a small `fno1d` checkpoint on:
- `/root/workspace/data/c2h4_case_pairs_smoke.npy`

and exports a DeepFlame bundle under:
- `/root/workspace/artifacts/models/c2h4_casepair_fno_smoke_deepflame_bundle/`

## Training result

Training setup:
- model: `fno1d`
- width: `32`
- modes: `8`
- layers: `4`
- trainer: `supervised_physics`
- target mode: `species_only`
- epochs: `6`
- batch size: `512`
- seed: `0`

Observed loss trend:
- epoch 1: `Loss ≈ 3.462614e-01`
- epoch 6: `Loss ≈ 1.200046e-01`

Export validation on `128` samples again showed exact parity between the offline checkpoint and exported bundle path:
- `max_abs_next_species_diff = 0.0`
- `mean_abs_next_species_diff = 0.0`

## Integrated case

New copied case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_fno_integration`

It stayed in the trusted stock-style runtime regime:
- `GPU on`
- `coresPerNode 8`
- `numberOfSubdomains 8`
- `mpirun -np 8`

The case used:
- exported bundle `inference.py`
- exported model `DNN_model_fno.pt`
- `endTime = 1e-6`

## Result

The case-aligned FNO-integrated C2H4 case completed cleanly through `1e-6`.

Observed timeline:
- `1e-07`
- `2e-07`
- `3e-07`
- `4e-07`
- `5e-07`
- `6e-07`
- `7e-07`
- `8e-07`
- `9e-07`
- `1e-06`

No solver-side fatal error appeared in:
- `solver.err`

## Learned activity

The learned active-set counts stayed healthy and increased monotonically across the run:
- `2e-07`: `33508`
- `3e-07`: `33546`
- `4e-07`: `33688`
- `5e-07`: `33867`
- `6e-07`: `33894`
- `7e-07`: `33967`
- `8e-07`: `34036`
- `9e-07`: `34127`
- `1e-06`: `34197`

At `1e-06`, the integrated case still looked thermodynamically sane in the log summary:
- `min/max(T) = 499.79, 2484.02`

## Contrast with the homogeneous-smoke FNO baseline

Earlier homogeneous-smoke FNO integration outcome:
- survived through `9e-7`
- failed during the `1e-6` attempt in HP reconstruction
- active-set counts collapsed sharply before failure:
  - `7e-07`: `33630`
  - `8e-07`: `10200`
  - `9e-07`: `5346`

New case-aligned CFD-pair FNO outcome:
- survives cleanly through `1e-6`
- active-set counts do **not** collapse
- no HP reconstruction failure appears over this horizon

## Interpretation

This is the strongest evidence so far that the main bottleneck in the first C2H4 FNO attempt was the training-distribution mismatch, not merely the use of an FNO architecture or the DeepFlame runtime wiring.

Important caution remains:
- the new training dataset is still not chemistry-only
- the extracted labels include full CFD evolution between written times

So this is not yet a final scientific training contract.
But it is a highly informative result:
- **even a crude case-aligned CFD state-pair dataset is substantially more useful for short-horizon C2H4 integration than the original homogeneous smoke dataset**

## Most useful next step

Extend the case-aligned FNO-integrated C2H4 case beyond `1e-6` in controlled steps toward the stock `5e-6` target, and determine whether the next failure mode now shifts later or changes character.
