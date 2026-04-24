# C2H4 case-aligned data path: the current smoke dataset is badly mismatched to the stock DeepFlame active-state distribution, and a first CFD state-pair extractor is now in place

_Date: 2026-04-24_

## Why this was the next step

After comparing the first FNO-integrated C2H4 case against stock near failure, the next high-value question was whether the current offline smoke dataset even covers the thermochemical region seen by the trusted stock C2H4 CFD run.

That mattered because the evidence was pointing toward a state-distribution mismatch rather than a simple postprocessing bug.

## What I built

### Active-state mismatch analyzer
- `/root/workspace/scripts/analyze_c2h4_case_dataset_mismatch.py`

This script compares:
- a DeepFlame C2H4 case
- selected written CFD times
- an offline paired-state dataset

using a practical active-cell approximation:
- `T > frozenTemperature`

This approximation is needed because the written `selectDNN` field is not reliable in this setup.

### First case-aligned extractor
- `/root/workspace/scripts/extract_deepflame_c2h4_case_pairs.py`

This extracts paired CFD states between consecutive written times at fixed cell ordering.

Important limitation:
- these are **case-aligned CFD state pairs**, not isolated chemistry-only labels
- they include full CFD evolution between written times

So this is a data-path prototype, not yet the final chemistry-labeling solution.

## Stock-case vs smoke-dataset mismatch result

Compared:
- stock case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`
- times:
  - `5e-07`, `1e-06`, `2e-06`, `5e-06`
- offline dataset:
  - `/root/workspace/data/c2h4_autoignition_smoke.npy`
- active-cell criterion:
  - `T > 510 K`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_active_vs_smoke_dataset_mismatch.json`

## Main mismatch evidence

### Temperature coverage is very poor
Offline smoke dataset current-state temperatures:
- min: `1013.77 K`
- median: `1397.52 K`
- max: `1792.85 K`

Aggregated active stock-case states:
- min: `510.09 K`
- 1st percentile: `538.37 K`
- median: `2459.03 K`
- 99th percentile: `2462.86 K`
- max: `2463.64 K`

Coverage summary:
- case fraction below dataset temperature minimum: `0.03525`
- case fraction above dataset temperature maximum: `0.9425875`

So **about 94.3% of sampled active stock-case states lie above the current smoke dataset temperature ceiling**.

### Pressure coverage is also poor
Offline smoke dataset pressure:
- effectively constant at `101325 Pa`

Aggregated active stock-case states:
- min: `101233 Pa`
- median: `101593 Pa`
- 99th percentile: `102425 Pa`
- max: `102521 Pa`

Coverage summary:
- case fraction below dataset pressure minimum: `0.0012875`
- case fraction above dataset pressure maximum: `0.91255`

So **about 91.3% of sampled active stock-case states lie above the smoke dataset pressure** because the current dataset is constant-pressure while the case is not.

### Composition mismatch is severe
Selected species means:

- `O2`
  - smoke dataset: `1.70e-07`
  - active stock case: `2.58e-02`
- `OH`
  - smoke dataset: `7.11e-07`
  - active stock case: `4.22e-03`
- `H2O`
  - smoke dataset: `5.09e-07`
  - active stock case: `7.19e-02`
- `CO`
  - smoke dataset: `1.56e-06`
  - active stock case: `2.47e-02`
- `CO2`
  - smoke dataset: `2.85e-09`
  - active stock case: `1.51e-01`
- `C2H4`
  - smoke dataset: `6.97e-02`
  - active stock case: `2.92e-03`

The current smoke dataset is therefore not just missing the right temperature band; it is also centered on a very different chemical regime.

## First case-aligned extracted dataset

I then used the new extractor on the trusted stock case:
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`
- times:
  - `5e-07`, `6e-07`, `7e-07`, `8e-07`, `9e-07`, `1e-06`
- filter:
  - current `T > 510 K`
- sample cap:
  - `10000` rows per consecutive time pair

Generated local dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke.json`

Summary:
- 5 consecutive time pairs
- `10000` sampled active rows per pair
- total rows: `50000`
- row width: `52`
- layout remains compatible with the paired-state contract:
  - `[T, P, species..., T_next, P_next, species_next...]`

## Interpretation

This is the strongest evidence so far that the first tiny homogeneous C2H4 smoke dataset is the wrong training-distribution anchor for the CFD replacement problem.

The mismatch is severe in:
- temperature
- pressure
- chemical composition

That makes the forward path clearer:
- the next useful C2H4 model should be trained on a case-aligned dataset, or at least include a large case-aligned component
- the extracted CFD state-pair dataset is now a first concrete bridge to that path

## Important caution

The extracted CFD pairs are not yet chemistry-isolated labels. They mix chemistry with the full CFD step between written outputs. So they should be treated as:
- a better distribution-matching prototype dataset
- not yet the final scientific training target

## Most useful next step

Use the extracted case-pair dataset to train a first case-aligned C2H4 smoke model and compare its DeepFlame integration behavior against the current homogeneous-smoke FNO baseline.
