# Mixed-dataset C2H4 ablation (`unfiltered + dp100`): blending broader coverage with the better pressure-filter subset yields a viable middle ground, but `dp100` still remains the best single tested target set

_Date: 2026-04-24_

## Why this was the next step

After the mixed-filter `dp100 + dT10` dataset failed in-case, the next useful refinement was to avoid over-narrowing the target distribution.

Instead of further restricting transitions, I tested a simple mixed dataset that **preserves broader coverage** while still including the better-performing pressure-filtered subset:
- unfiltered case pairs
- plus the `|Δp| <= 100 Pa` case-pair subset

This is a first structural refinement that changes the dataset composition without forcing all labels into a narrowly filtered regime.

## What I built

### Dataset builder
- `/root/workspace/scripts/build_c2h4_mixed_casepair_dataset.py`

This concatenates multiple paired-state datasets and writes a combined metadata record.

### New mixed dataset
- `/root/workspace/data/c2h4_case_pairs_smoke_mixed_unfiltered_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_mixed_unfiltered_dp100.json`

Composition:
- `50000` unfiltered rows
- `50000` dp100 rows
- total: `100000` rows

### New training/export runner
- `/root/workspace/scripts/run_c2h4_casepair_mixed_unfiltered_dp100_fno_baseline.py`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_mixed_unfiltered_dp100_fno_batched_full`

## Training result

The mixed dataset trains cleanly.

Loss trend:
- epoch 1: `Loss ≈ 2.440199e-01`
- epoch 6: `Loss ≈ 1.026500e-01`

This is better than the unfiltered-only and dp100-only final training losses, though not as low as the over-narrow `dp100 + dT10` subset that later failed in-case.

## Runtime result

The mixed-dataset model remains solver-usable through `5e-6` with the batched bridge.

At `5e-6`:
- learned active-set count: `51824`
- no OOM line appears
- `solver.err` remains empty

So the mixed-dataset path avoids the HP-failure behavior seen in the over-filtered `dp100 + dT10` attempt.

## Comparison against unfiltered, dp100, and stock

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_mixed_unfiltered_dp100_fno_batched_full_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_mixed_unfiltered_dp100_vs_dp100_vs_unfiltered_vs_stock_5e-06.json`

## Main behavior

### Better than unfiltered on the main broad pathologies
At `5e-6`:
- mean `Qdot`
  - mixed: `7.85e8`
  - unfiltered: `1.45e9`
  - stock: `1.62e7`
- pressure max
  - mixed: `121172 Pa`
  - unfiltered: `140676 Pa`
  - stock: `102000 Pa`
- mean `|ΔT|` from `2e-6`
  - mixed: `3.20 K`
  - unfiltered: `5.35 K`
  - stock: `0.83 K`

So the mixed dataset clearly improves over the fully unfiltered target set.

### But still not as good as dp100 on the main source-term metric
Compared with dp100:
- mean `Qdot`
  - mixed: `7.85e8`
  - dp100: `5.12e8`
  - stock: `1.62e7`
- stock-normalized `Qdot` ratio
  - mixed: `48.4x`
  - dp100: `31.6x`
  - unfiltered: `89.2x`

So the mixed dataset is a useful middle ground, but `dp100` still remains the best current single tested target set on the main source-term-overactivity metric.

### Pressure behavior also lands in the middle
Pressure max at `5e-6`:
- mixed: `121172 Pa`
- dp100: `113365 Pa`
- unfiltered: `140676 Pa`
- stock: `102000 Pa`

Mean pressure:
- mixed: `101914 Pa`
- dp100: `101825 Pa`
- unfiltered: `102359 Pa`
- stock: `101347 Pa`

Again, the mixed dataset helps relative to unfiltered, but does not beat dp100.

## Species-level interpretation

The mixed dataset also lands between the two earlier successful baselines.

Examples at `5e-6`:
- `C2H4`
  - mixed: `0.06102`
  - dp100: `0.06148`
  - unfiltered: `0.06019`
  - stock: `0.06178`
- `CO2`
  - mixed: `0.00425`
  - dp100: `0.00298`
  - unfiltered: `0.00404`
  - stock: `0.00487`
- `CO`
  - mixed: `5.04e-04`
  - dp100: `4.41e-04`
  - unfiltered: `4.63e-04`
  - stock: `8.11e-04`

But the hard missing-intermediate problem remains:
- `C2H5 = 0`
- `C2H3 = 0`
- `CH2CHO = 0`
- `CH2CO` remains negligible

So blending coverage helps stabilize the dataset choice, but it does not solve the deeper late-chemistry-target gap.

## Interpretation

This mixed-dataset ablation is useful because it shows a more structural tradeoff:
- over-narrow filtering can fail in-case
- broader unfiltered coverage is solver-usable but overly energetic
- a simple coverage+filter blend gives a robust middle ground

However, within the currently tested options:
- **dp100 remains the best current single target set**
- the mixed dataset is a credible backup/bridge option, but not yet the front-runner

## Most useful next step

Use the current evidence to stop blind subset squeezing and move one layer up in target design. The next best step is likely to keep dp100 as the reference filtered target, while testing a deliberately mixed training curriculum or weighting scheme that preserves broader coverage without giving back as much source-term control.
