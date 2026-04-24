# Larger early-window `dp100` dataset test: more data alone changes the regime strongly, but not in a straightforwardly better way

_Date: 2026-04-24_

## Why this was the next step

A reasonable concern is that the current C2H4 results may still be data-limited simply because the training datasets are too small.

The original early-window `dp100` case-pair baseline used a hard cap of:
- `10000` samples per consecutive time pair
- total rows: `50000`

So the next concrete step was to test a **larger dataset** without changing the target semantics:
- same early time window
- same `|Δp| <= 100 Pa` filter
- but **no per-pair sampling cap**

That isolates the effect of dataset size much better than mixing in new target constructions.

## What I built

### Larger uncapped early-window dataset
Generated:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_full.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_full.json`

Counts:
- `5e-07 -> 6e-07`: `21374`
- `6e-07 -> 7e-07`: `20303`
- `7e-07 -> 8e-07`: `20511`
- `8e-07 -> 9e-07`: `21268`
- `9e-07 -> 1e-06`: `21906`
- total: `105362` rows

So this is about **2.1x larger** than the original `50000`-row `dp100` training set.

### New runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_full_fno_baseline.py`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_full_fno_batched_full`

## Training behavior

Training loss improved relative to the capped `dp100` run:
- capped `dp100` final loss: `≈ 1.226254e-01`
- uncapped `dp100_full` final loss: `≈ 1.046150e-01`

So purely offline, the larger dataset looked promising.

## Runtime result

The larger-dataset model runs cleanly to `5e-6`.

At `5e-6`:
- learned active-set count: `33362`
- `solver.err` empty
- no OOM line

So this is a valid deployment-facing comparison.

## Main comparison versus the original `50k` `dp100` baseline

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_50k_vs_105k_comparison.json`

### Original `50k` `dp100`
- mean `Qdot`: `5.12e8`
- pressure max: `113365 Pa`
- `T_min = 499.157 K`
- mean `|ΔT|` from `2e-6`: `3.28 K`

### Larger `105k` `dp100_full`
- mean `Qdot`: `-5.92e7`
- pressure max: `103218 Pa`
- `T_min = 493.303 K`
- mean `|ΔT|` from `2e-6`: `1.82 K`

## Interpretation

This is a very informative result.

The larger dataset does **not** simply improve everything monotonically.

Instead, it changes the learned regime strongly:
- pressure behavior becomes much closer to stock
- temperature drift decreases
- but mean `Qdot` swings past the stock regime into **negative** territory
- and `T_min` drops below the clean ~`499 K` floor held by the earlier `dp100` baseline

So “more data” helped in some ways, but it also appears to have over-corrected the previous over-energetic bias.

## What this means

This is still useful evidence in favor of your suggestion.

It shows that dataset size really does matter here:
- doubling the dataset changed the deployment behavior materially
- so this problem is not already in a fully data-saturated regime

But it also shows that **scaling data alone is not enough**:
- larger data can move the model into a different failure mode
- not just smoothly improve the same one

So the current conclusion is more nuanced:
- yes, larger training datasets are worth testing
- but scaling interacts strongly with the target distribution, not just optimization noise

## Current takeaway

The first larger-dataset test says:
- **data scale matters**
- but the answer is not just “make the dataset bigger”
- we need to control *which* data we scale, not only *how much*

In particular, this strengthens the case for combining:
- better-calibrated data construction
- with dataset scaling

rather than relying on size alone.

## Most useful next step

The most justified follow-up is now:
- keep testing larger datasets,
- but do so on **better-calibrated target paths** (for example, calibrated canonical augmentation mixes),
- because the current uncapped `dp100` result shows that scale is powerful but not automatically aligned with solver fidelity.
