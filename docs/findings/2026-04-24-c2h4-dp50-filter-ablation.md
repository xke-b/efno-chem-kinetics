# Tighter `|Δp| <= 50 Pa` C2H4 filter ablation: the response is non-monotonic, and `|Δp| <= 100 Pa` remains the best current pressure-filter baseline

_Date: 2026-04-24_

## Why this was the next step

After the first pressure-filtered C2H4 FNO result showed that `|Δp| <= 100 Pa` helps but does not solve the chemistry gap, the next low-cost question was whether simply tightening the pressure filter further would continue to improve the learned behavior.

The obvious next ablation was:
- `|Δp| <= 50 Pa`

## What I built and ran

### New tighter-filter runner
- `/root/workspace/scripts/run_c2h4_casepair_dp50_fno_baseline.py`

### New tighter-filter dataset
- `/root/workspace/data/c2h4_case_pairs_smoke_dp50.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp50.json`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp50_fno_batched_full`

Runtime regime stayed the same:
- stock-style `np=8` GPU
- batched FNO bridge
- `startFrom startTime`
- `endTime 5e-6`

## Training result

Training loss trend:
- epoch 1: `Loss ≈ 3.043060e-01`
- epoch 6: `Loss ≈ 1.211833e-01`

The model exported cleanly and the integrated case again completed through `5e-6` without OOM.

At `5e-6`:
- learned active-set count: `58068`

## Comparison against dp100, unfiltered, and stock

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp50_fno_batched_full_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp50_vs_dp100_vs_unfiltered_vs_stock_5e-06.json`

## Main result

The tighter `|Δp| <= 50 Pa` filter is **not** uniformly better than `|Δp| <= 100 Pa`.

This is a useful negative result.

## Where dp50 helps or changes behavior

The dp50 model remains solver-usable through `5e-6` and still improves on the fully unfiltered case-pair baseline in some broad ways.

At `5e-6`:
- mean `Qdot`
  - dp50: `1.108e9`
  - unfiltered: `1.446e9`
  - stock: `1.622e7`

So dp50 is still better than unfiltered on the worst source-term excess.

Some late intermediates also reappear weakly relative to the dp100 run:
- `C2H3`
  - dp50: `7.81e-13`
  - dp100: `0.0`
- `CH2CHO`
  - dp50: `1.35e-12`
  - dp100: `0.0`
- `CH2CO`
  - dp50: `1.24e-08`
  - dp100: `7.60e-10`

These are still far below stock, but the direction is informative.

## Where dp50 is worse than dp100

### Higher source-term excess
Mean `Qdot` at `5e-6`:
- dp50: `1.108e9`
- dp100: `5.118e8`
- stock: `1.622e7`

So the stock-normalized overprediction is:
- dp50: about `68.3x`
- dp100: about `31.6x`
- unfiltered: about `89.2x`

That makes dp100 clearly better than dp50 on the main source-term metric.

### Worse temperature drift than dp100
Mean `|ΔT|` from `2e-6` to `5e-6`:
- dp50: `4.76 K`
- dp100: `3.28 K`
- unfiltered: `5.35 K`
- stock: `0.83 K`

So dp50 lands between dp100 and unfiltered, rather than improving on dp100.

### Pressure tail still broader than dp100
At `5e-6`:
- dp50 `p_max = 123793 Pa`
- dp100 `p_max = 113365 Pa`
- unfiltered `p_max = 140676 Pa`
- stock `p_max = 102000 Pa`

So dp50 does improve on unfiltered, but it is worse than dp100 on pressure spread.

### Fuel is farther from stock than dp100
Mean `C2H4` at `5e-6`:
- dp50: `0.06089`
- dp100: `0.06148`
- stock: `0.06178`

So dp100 remains the better pressure-filter setting for the main fuel channel too.

## Interpretation

This ablation is useful because it shows the target-refinement response is **non-monotonic**.

A tighter pressure filter does not automatically improve the learned surrogate. In this case:
- `|Δp| <= 50 Pa` is still solver-usable
- and still beats the fully unfiltered case-pair baseline on some broad metrics
- but it does **not** beat `|Δp| <= 100 Pa` overall

So within the current pressure-filter family:
- `|Δp| <= 100 Pa` remains the best current operating point

## What this means for the next step

The project now has evidence against a simplistic “just tighten the pressure filter more” strategy.

That suggests the next useful refinement should probably change the subset logic, not just the pressure threshold. Examples:
- combine pressure and temperature-step filters
- use species-change filters
- or move toward a more explicitly chemistry-isolated labeling path

## Most useful next step

Run one mixed-filter ablation next—most naturally a `|Δp| <= 100 Pa` plus a modest `|ΔT|` cap—rather than continuing to squeeze the pressure threshold alone.
