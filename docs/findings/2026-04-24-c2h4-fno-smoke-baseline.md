# First C2H4 FNO smoke baseline: mechanism- and timestep-aligned offline prototype trained and exported into a DeepFlame bundle

_Date: 2026-04-24_

## Why this was the next step

After establishing the stock DeepFlame C2H4 runtime baseline through `5e-6`, the next useful step was to stop extending the stock case and build the first concrete FNO-side artifact that could eventually be integrated into that simulation.

The immediate milestone here was not full case success. It was narrower:
1. generate a first C2H4 dataset aligned to the stock mechanism and chemistry timestep
2. train a small DFODE-kit FNO checkpoint on that contract
3. export it into a DeepFlame-consumable bundle

## Artifacts created

### Dataset generator
- `/root/workspace/scripts/generate_c2h4_autoignition_pairs.py`

### Training/export runner
- `/root/workspace/scripts/run_c2h4_fno_smoke_baseline.py`

### Smoke dataset
- `/root/workspace/data/c2h4_autoignition_smoke.npy`
- `/root/workspace/data/c2h4_autoignition_smoke.json`

### Trained checkpoint
- `/root/workspace/artifacts/models/c2h4_fno_smoke.pt`

### DeepFlame export bundle
- `/root/workspace/artifacts/models/c2h4_fno_smoke_deepflame_bundle/DNN_model_fno.pt`
- `/root/workspace/artifacts/models/c2h4_fno_smoke_deepflame_bundle/inference.py`

### Summary artifact
- `/root/workspace/artifacts/experiments/c2h4_fno_smoke_baseline/summary.json`

## Dataset contract

This first dataset is only a **minimum viable mechanism- and timestep-aligned offline path**.

It uses:
- mechanism: `Wu24sp.yaml`
- species count: `24`
- reactions: `86`
- timestep: `1e-7`
- fuel: `C2H4:1`
- oxidizer: `O2:1,N2:3.76`
- reactor: homogeneous constant-pressure autoignition

Smoke dataset settings:
- `n_init = 24`
- `steps = 40`
- total rows: `960`
- row width: `52`
  - `[T, P, Y_1..Y_24, T_next, P_next, Y_next_1..Y_next_24]`

Important limitation:
- this is **not yet CFD-state sampled C2H4 data from the DeepFlame case**
- it is only the first aligned offline bridge into C2H4 FNO training

## First FNO training result

The smoke FNO was trained with:
- model: `fno1d`
- width: `32`
- modes: `8`
- layers: `4`
- trainer: `supervised_physics`
- target mode: `species_only`
- epochs: `8`
- batch size: `256`
- seed: `0`

Observed training-loss trend:
- epoch 1: `Loss ≈ 4.236519e-01`
- epoch 8: `Loss ≈ 3.603089e-01`

This is only a smoke baseline, but it confirms that the current DFODE-kit `fno1d` scaffold can be trained on the aligned 24-species C2H4 contract without immediate plumbing failure.

## DeepFlame export result

I also built the first FNO-specific DeepFlame export bridge:
- `/root/workspace/scripts/export_dfode_fno_to_deepflame_bundle.py`

Unlike the existing MLP export path, this FNO bridge keeps a single shared network and writes:
- an exported checkpoint bundle
- a case-local `inference.py`

Export metadata from the first bundle:
- input tokens: `26`
- output tokens: `23`
- export type: `dfode_fno_to_deepflame_bundle`

Validation on `64` smoke samples gave exact parity between the original offline FNO species branch and the exported bundle path under the implemented contract:
- `max_abs_next_species_diff = 0.0`
- `mean_abs_next_species_diff = 0.0`

That does **not** mean the model is already good enough for the C2H4 CFD case.
It means the first FNO export/inference bridge is working as an enabling artifact.

## What this changes

This is the first concrete C2H4 FNO integration milestone:
- there is now a mechanism-aligned dataset path
- there is now a trained C2H4 FNO smoke checkpoint
- there is now a DeepFlame-consumable FNO export bundle

So the project is no longer only at the "runtime baseline" stage for C2H4.
It now has the first end-to-end **offline-train -> export** bridge for an FNO model.

## Most useful next step

Move from this homogeneous smoke contract toward a more case-relevant C2H4 dataset and then test the exported FNO bundle in a copied DeepFlame C2H4 case as the first integration smoke test.
