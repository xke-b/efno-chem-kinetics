# Pressure-filtered C2H4 case-pair data path: a large near-constant-pressure active subset exists, and a first `|Δp| <= 100 Pa` filtered dataset is now extracted

_Date: 2026-04-24_

## Why this was the next step

After showing that the repaired full batched C2H4 FNO run is now mostly limited by surrogate/target quality rather than runtime failure, the next useful question was whether the current full-CFD state-pair labels could be improved cheaply before attempting a more elaborate chemistry-only labeling path.

The most accessible first idea was:
- isolate a more chemistry-like subset of active CFD transitions by filtering to pairs with small pressure drift between consecutive written times

This is not a full physics decomposition, but it is a plausible first step toward a less transport-contaminated target set.

## What I built

### Pair-regime analyzer
- `/root/workspace/scripts/analyze_c2h4_case_pair_regimes.py`

This analyzes active consecutive stock-case pairs and reports:
- `ΔT`
- `|Δp|`
- relative `|Δp|`
- species `L1` step size
- coverage fractions under candidate pressure-drift thresholds

### Pressure-filter support in extractor
Updated:
- `/root/workspace/scripts/extract_deepflame_c2h4_case_pairs.py`

New options:
- `--max-abs-delta-p`
- `--max-rel-delta-p`

So the extractor can now carve out a pressure-filtered subset directly.

## Regime analysis result

Analyzed active stock-case pairs over:
- `5e-07 -> 6e-07 -> 7e-07 -> 8e-07 -> 9e-07 -> 1e-06`
- active criterion: `T > 510 K`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_case_pair_regimes_5e-07_to_1e-06.json`

## Main evidence

Aggregate active-pair pressure-drift statistics:
- median `|Δp|`: `49 Pa`
- 95th percentile `|Δp|`: `233 Pa`
- 99th percentile `|Δp|`: `311 Pa`
- mean `|Δp|`: `82.38 Pa`

Aggregate active-pair temperature-change statistics:
- median `|ΔT|`: `0.18 K`
- 95th percentile `|ΔT|`: `15.16 K`
- 99th percentile `|ΔT|`: `49.38 K`
- mean `|ΔT|`: `2.47 K`

Aggregate fractions under candidate pressure filters:
- `|Δp| <= 25 Pa`: `0.4186`
- `|Δp| <= 50 Pa`: `0.5032`
- `|Δp| <= 100 Pa`: `0.6231`
- `|Δp| <= 250 Pa`: `0.9608`

So there is a substantial active subset with relatively small pressure drift. A `|Δp| <= 100 Pa` filter is a reasonable first compromise:
- it keeps about **62.3%** of active pairs
- while removing the broader-pressure tail

## First filtered dataset

Using the updated extractor, I generated:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.json`

Settings:
- times:
  - `5e-07`, `6e-07`, `7e-07`, `8e-07`, `9e-07`, `1e-06`
- active filter:
  - `T > 510 K`
- pressure filter:
  - `|Δp| <= 100 Pa`
- sampling cap:
  - `10000` rows per pair

Result:
- 5 consecutive time pairs
- `10000` sampled rows per pair
- total rows: `50000`
- row width: `52`

Because the retained subset under `|Δp| <= 100 Pa` is still larger than the sample cap for each pair, this filtered dataset can be produced without exhausting the available pair pool.

## Interpretation

This does not solve the target-quality problem by itself. The filtered pairs are still full-CFD transitions, not isolated chemistry labels.

But it is a meaningful refinement:
- it gives us a more chemistry-like subset than the unfiltered case-pair dataset
- it is cheap to generate reproducibly
- and it is large enough to train a first filtered baseline immediately

## Most useful next step

Train and export the first C2H4 FNO baseline on the pressure-filtered case-pair dataset and compare its `5e-6` behavior against the unfiltered case-pair FNO baseline, focusing especially on whether the source-term over-energetic bias and missing late intermediates improve.
