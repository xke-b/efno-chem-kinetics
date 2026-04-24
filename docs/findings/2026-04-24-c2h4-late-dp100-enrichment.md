# Late-window C2H4 dp100 enrichment: later case pairs do contain much stronger intermediate coverage, but naively adding them causes an earlier thermodynamic collapse

_Date: 2026-04-24_

## Why this was the next step

The recent C2H4 subset-mixing ablations suggested that the dominant problem is no longer just sample ratio. The remaining gap looked more like a **target-construction / label-semantics** problem, especially around missing late intermediates and products.

So the next useful question was:
- are the currently used early-window case-pair labels actually missing the late-chemistry species support we need?
- and if so, does adding a late-window dp100 subset help in practice?

## What I built

### Coverage diagnostic script
- `/root/workspace/scripts/analyze_c2h4_dataset_species_coverage.py`

This compares key late-chemistry species coverage across datasets and case states.

### Late-window dp100 dataset
Extracted with the existing case-pair extractor:
- `/root/workspace/data/c2h4_case_pairs_late_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_late_dp100.json`

Window:
- `2e-06 -> 3e-06 -> 4e-06 -> 5e-06`
- `T > 510 K`
- `|Δp| <= 100 Pa`

Result:
- `23006` rows total
- pair counts:
  - `2e-06 -> 3e-06`: `10000`
  - `3e-06 -> 4e-06`: `10000`
  - `4e-06 -> 5e-06`: `3006`

### Early+late combined dp100 dataset
Built with the mixed-dataset utility:
- `/root/workspace/data/c2h4_case_pairs_dp100_early_plus_late.npy`
- `/root/workspace/data/c2h4_case_pairs_dp100_early_plus_late.json`

Composition:
- early dp100: `50000`
- late dp100: `23006`
- total: `73006`

### New training/export runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_early_plus_late_fno_baseline.py`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_early_plus_late_fno_batched_full`

## Coverage result: later dp100 pairs really are richer in the missing late chemistry

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_early_late_species_coverage.json`

Compared with the early dp100 dataset, the late dp100 subset is much richer in the key missing intermediates.

### Key next-state coverage fractions (`>= 1e-8` for intermediates)

#### `C2H5`
- early dp100: `0.1226`
- late dp100: `0.2879`
- stock `5e-06`: `0.1563`

#### `C2H3`
- early dp100: `0.1727`
- late dp100: `0.5105`
- stock `5e-06`: `0.2660`

#### `CH2CHO`
- early dp100: `0.1410`
- late dp100: `0.3493`
- stock `5e-06`: `0.1834`

#### `CH2CO`
- early dp100: `0.1709`
- late dp100: `0.5447`
- stock `5e-06`: `0.2983`

So the later-window dp100 pairs are not empty or irrelevant; they are substantially more enriched in exactly the late chemistry that the deployed model has been failing to retain.

## Combined early+late training behavior

Training loss was much worse than the earlier dp100 baseline:
- epoch 1: `Loss ≈ 3.777634e-01`
- epoch 6: `Loss ≈ 2.298581e-01`

This is far worse than the early dp100-only run (`≈ 1.226254e-01` final loss).

That already suggested the enlarged target distribution had become harder to fit coherently with the present setup.

## Runtime result: worse, and it fails early

The combined early+late dp100 model does **not** reach `5e-6`.

It fails around `3.4e-6` with HP reconstruction failure:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP): No convergence in 500 iterations`
- with extreme pressure collapse in the failing cells:
  - `Current Pressure = 787 Pa`
  - `Current Pressure = 1091 Pa`

So this is not just a mild quality regression. It reintroduces a severe thermodynamic instability.

## Pre-failure field evidence

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_early_plus_late_fno_fields_3.3e-06_vs_2e-06.json`

At written `3.3e-06`, the combined early+late run already shows catastrophic pathologies:
- `T_min = 97.6 K`
- `p_min = 787 Pa`
- mean `Qdot = -5.76e9`
- `Qdot_min = -1.08e12`
- mean `|ΔT|` from `2e-06` ≈ `19.15 K`

For comparison, the pure early dp100 case at the same written time remains much healthier:
- artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_fno_batched_full_fields_3.3e-06_vs_2e-06.json`
- pure dp100 at `3.3e-06`:
  - `T_min = 499.3 K`
  - `p_min = 100772 Pa`
  - mean `Qdot = 3.50e8`
  - mean `|ΔT|` from `2e-06` ≈ `1.24 K`

So the late-enriched training data is not simply “better but harder”; in the current setup it actively destabilizes the deployment trajectory.

## Interpretation

This is an important result because it separates two questions:

1. **Does the late-window data contain useful missing chemistry?**
   - Yes. Very clearly.

2. **Can we just concatenate that late-window data into the current training recipe and expect improvement?**
   - No. Not with the current setup.

The evidence suggests:
- late chemistry support is genuinely missing from the current target path
- but naïvely broadening the target distribution across early + late regimes makes the model much harder to fit and can produce an unstable coupled trajectory

So the project has now learned something sharper than “add more representative data”:
- **representation matters, but regime mixing needs structure**

## What this changes

This result argues against simple concatenation as the next default move.

The next promising directions are now more structured, for example:
- staged/curriculum training rather than one-shot mixing
- regime-conditioned batching or weighting
- or a more explicit target path that separates early and late chemistry regimes instead of collapsing them into one undifferentiated dataset

## Current takeaway

- `dp100` remains the strongest simple single-dataset baseline
- late dp100 pairs are genuinely informative for missing intermediates
- but **naive early+late concatenation is a regression** and causes an earlier thermodynamic collapse
