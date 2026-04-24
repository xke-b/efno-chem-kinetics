# First pressure-filtered C2H4 FNO result: a simple `|Δp| <= 100 Pa` filter improves the full `5e-6` run materially, but does not yet solve the chemistry gap

_Date: 2026-04-24_

## Why this was the next step

After establishing that the dominant remaining C2H4 bottleneck was target quality rather than runtime pathology, the next low-cost experiment was to test whether a more chemistry-like subset of the case-pair labels could improve behavior.

The chosen refinement was simple:
- keep only active consecutive pairs with `|Δp| <= 100 Pa`

This does not create chemistry-only labels, but it removes a sizable part of the full-CFD transition set that is most obviously pressure-drift dominated.

## What I built and ran

### New training/export runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_fno_baseline.py`

Dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.json`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_fno_batched_full`

Runtime regime remained the trusted stock-style one:
- `GPU on`
- `coresPerNode 8`
- `numberOfSubdomains 8`
- batched FNO bridge
- `startFrom startTime`
- `endTime 5e-6`

## Training result

Training setup matched the earlier case-pair baseline closely:
- model: `fno1d`
- width: `32`
- modes: `8`
- layers: `4`
- trainer: `supervised_physics`
- target mode: `species_only`
- epochs: `6`
- batch size: `512`

Observed loss trend:
- epoch 1: `Loss ≈ 3.210141e-01`
- epoch 6: `Loss ≈ 1.226254e-01`

Export validation again showed exact offline/export parity on the validation samples.

## Runtime result

The pressure-filtered FNO run completes through `5e-6` with the batched bridge.

At `5e-6`:
- learned active-set count: `43825`
- no OOM line appears in the log
- `solver.err` remains empty

So the filtered model remains solver-usable through the target horizon.

## Comparison against the unfiltered case-pair FNO and stock

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_fno_batched_full_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_vs_unfiltered_vs_stock_5e-06.json`

## Main improvements from pressure filtering

### Lower temperature drift
Mean `|ΔT|` from `2e-6` to `5e-6`:
- pressure-filtered: `3.28 K`
- unfiltered case-pair FNO: `5.35 K`
- stock: `0.83 K`

### Narrower pressure tail
At `5e-6`:
- filtered `p_max = 113365 Pa`
- unfiltered `p_max = 140676 Pa`
- stock `p_max = 102000 Pa`

Mean pressure:
- filtered: `101824.9 Pa`
- unfiltered: `102359.3 Pa`
- stock: `101347.5 Pa`

So the pressure-filtered model is materially closer to stock on pressure behavior.

### Lower over-energetic `Qdot`
Mean `Qdot` at `5e-6`:
- filtered: `5.118e8`
- unfiltered: `1.446e9`
- stock: `1.622e7`

So the pressure-filtered model reduces the stock-normalized `Qdot` overprediction from:
- about **89.2x** stock

down to:
- about **31.6x** stock

This is still too large, but it is a meaningful improvement.

### Fuel level is closer to stock
Mean `C2H4` at `5e-6`:
- filtered: `0.06148`
- unfiltered: `0.06019`
- stock: `0.06178`

So the filtered model moves the main fuel channel closer to stock.

## Remaining problems

The pressure filter does **not** solve the chemistry gap.

Late intermediate/product channels remain strongly suppressed:
- `C2H5`
  - filtered: `0.0`
  - stock: `5.07e-07`
- `C2H3`
  - filtered: `0.0`
  - stock: `1.95e-06`
- `CH2CHO`
  - filtered: `0.0`
  - stock: `2.23e-07`
- `CH2CO`
  - filtered: `7.60e-10`
  - stock: `7.11e-06`

Some broad reactive/product quantities are still too high relative to stock:
- `OH`
  - filtered: `3.17e-04`
  - stock: `1.34e-04`
- `H2O`
  - filtered: `4.45e-03`
  - stock: `2.32e-03`

So the filter helps with trajectory quality and source-term excess, but it does not recover the missing late chemistry detail.

## Interpretation

This is a useful incremental win.

The `|Δp| <= 100 Pa` filter does exactly the kind of thing we hoped a cheap target refinement might do:
- improves pressure behavior
- reduces thermal/source overactivity
- keeps the run solver-usable through `5e-6`

But it does **not** solve the deeper modeling problem.

The strongest remaining issue is still that the current target construction—even after filtering—is not rich enough to reproduce the late intermediate chemistry seen in the stock case.

## Most useful next step

Use this as evidence that target refinement matters, then move one step further: compare one or two stronger subset constructions (for example tighter pressure filters or additional small-`|ΔT|` / species-change filters) rather than jumping straight to a much more complex labeling system without an intermediate ablation.
