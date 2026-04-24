# C2H4 species-order alignment bug: mixed datasets were concatenating incompatible species layouts, and earlier Cantera-on-CFD analyses overstated cool-onset chemistry by feeding case-order states into mechanism-order chemistry without reordering

_Date: 2026-04-24_

## Why this matters

While building targeted cool-onset support data, I found a more fundamental tooling problem in the C2H4 pipeline:

- the **case-pair CFD datasets** use species order
  - `H, H2, O, O2, OH, ...`
- the **Wu24sp / Cantera mechanism order** is
  - `H, O2, OH, O, H2, ...`
- the existing **oneD/Xiao chemistry-labeled datasets** follow the mechanism order
- but the existing **mixed datasets** were created by plain concatenation without reordering

That means the previous mixed datasets combined rows with **different species-channel semantics in the same tensor columns**.

Separately, some of my newer CFD-state-vs-CVODE analysis scripts were taking case-order CFD states and feeding them directly into Cantera as if they were already in mechanism order. That inflated the apparent cool-onset chemistry by orders of magnitude.

## Concrete evidence of the bug

### Case-pair metadata
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.json`
  - `species_names` begins: `H, H2, O, O2, OH, ...`

### oneD/Xiao labeled metadata
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.json`
  - `species_names` begins: `H, O2, OH, O, H2, ...`

So the old mixed datasets such as:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r1p0.npy`

were built from incompatible channel orders.

## Script fixes applied

### 1. Mixed-dataset builder now reorders to a common target layout
Updated:
- `/root/workspace/scripts/build_c2h4_mixed_casepair_dataset.py`

It now:
- reads `species_names` from component metadata
- reorders each paired dataset into the first dataset’s species layout before concatenation
- records whether reordering happened

### 2. Current-state Cantera labeler now supports explicit input species order
Updated:
- `/root/workspace/scripts/label_c2h4_current_states_with_cantera.py`

It now:
- accepts optional `--metadata`
- reorders input states from metadata order into mechanism order before Cantera
- reorders Cantera outputs back to the input order for saved datasets

### 3. Regime-support and checkpoint-vs-CVODE analyses now reorder CFD states before Cantera
Updated:
- `/root/workspace/scripts/analyze_c2h4_regime_training_support.py`
- `/root/workspace/scripts/analyze_c2h4_cfd_checkpoint_vs_cvode.py`

So the chemistry reference is no longer computed from misordered species vectors.

## New corrected artifacts

### Corrected aligned mixed dataset (`r=0.2`)
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2_aligned.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2_aligned.json`

The metadata explicitly records that the oneD component was reordered from mechanism order into case-pair order.

### Real-CFD cool-onset current states and corrected chemistry labels
- current states:
  - `/root/workspace/data/c2h4_cfd_active_coolonset_1e-07_current.npy`
  - `/root/workspace/data/c2h4_cfd_active_coolonset_1e-07_current.json`
- corrected labeled pairs in case order:
  - `/root/workspace/data/c2h4_cfd_active_coolonset_1e-07_labeled_caseorder.npy`
  - `/root/workspace/data/c2h4_cfd_active_coolonset_1e-07_labeled_caseorder.json`

### Small targeted mixed dataset with exact cool-onset CFD chemistry support
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_cfdcool580.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_cfdcool580.json`

## Quantifying the Cantera-order bug on the real cool-onset CFD states

For the extracted `580` real cool-onset CFD cells at `1e-07`:

### Wrong Cantera interpretation of case-order states
One-step mean total chemistry activity:
- `ΔY` L1 mean = **`0.32816`**

### Corrected Cantera interpretation after reordering into mechanism order
One-step mean total chemistry activity:
- `ΔY` L1 mean = **`1.1283e-04`**

That is a huge correction.

Selected channel means, wrong vs corrected:
- `ΔOH`
  - wrong: `2.244e-03`
  - corrected: `-1.319e-06`
- `ΔC2H3`
  - wrong: `1.206e-03`
  - corrected: `2.731e-07`
- `ΔCH2CO`
  - wrong: `1.792e-03`
  - corrected: `2.934e-08`

So the earlier claim that the `510–700 K` cells at `1e-07` were undergoing very strong one-step chemistry was an artifact of species-order mismatch.

## Corrected regime-support result

Corrected artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_regime_training_support_alignment_check_1e-07_corrected.json`

### For the exact cool-onset CFD-support mix
Dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_cfdcool580.npy`

For the cool-onset benchmark:
- nearest-neighbor distance p50: **`0.0`**
- neighbor-label `ΔY` L1 mean: **`1.1283e-04`**
- true corrected `ΔY` L1 mean: **`1.1283e-04`**
- activity ratio: **`1.0`**

That is a useful sanity check that the corrected label path is now consistent.

### For the old corrupted mixed `r=0.2` dataset
Cool-onset corrected support:
- neighbor-label `ΔY` L1 mean: `9.431e-05`
- corrected true `ΔY` L1 mean: `1.1283e-04`
- activity ratio: `0.914`

### For the new aligned mixed `r=0.2` dataset
Cool-onset corrected support:
- neighbor-label `ΔY` L1 mean: `1.343e-04`
- corrected true `ΔY` L1 mean: `1.1283e-04`
- activity ratio: `1.31`

So after correcting the species-order bug, the cool-onset regime is **not** as chemistry-rich at `1e-07` as I previously thought.

## Corrected checkpoint-vs-CVODE result at `1e-07`

Corrected artifacts:
- plain power-delta:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_cfd_active_1e-07_vs_cvode_corrected.json`
- interleaved attention:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_interleaved_promoted100_val_cfd_active_1e-07_vs_cvode_corrected.json`

### Plain promoted power-delta still clearly overreacts
- global RMSE: `2.016e-02`
- mean predicted `ΔOH`: `5.7735e-02`
- corrected true mean `ΔOH`: `-3.380e-06`

This hot-radical overreaction diagnosis survives the correction.

### Interleaved `r=0.2` at `1e-07` is much closer to corrected CVODE than previously thought
- global RMSE: **`1.75e-05`**
- corrected true mean `ΔOH`: `-3.380e-06`
- predicted mean `ΔOH`: `8.94e-08`

So the earlier narrative that the interleaved branch was catastrophically suppressing very strong cool-onset chemistry at `1e-07` is **not supported after correcting species order**.

## Updated interpretation

Two things are now true at once:

1. The C2H4 pipeline really did contain a major data/alignment bug.
2. After correcting that bug, the plain promoted power-delta branch still looks physically problematic, but the interleaved branch’s early-step behavior is much less obviously wrong than I had concluded from the buggy analysis.

That means several recent C2H4 conclusions need narrower wording:
- the **mixed-data alignment bug is real** and must be treated as a serious confounder
- the **cool-onset underreaction story at `1e-07` was overstated by the order bug**
- the **plain power-delta hot overreaction signal survives the correction**
- the next diagnostic target should move toward **later CFD times / pre-failure windows under corrected ordering**, not keep over-interpreting the `1e-07` onset slice

## Most useful next step now

The best next step is no longer just “add more onset data.” It is:
- rebuild the important mixed datasets in aligned form
- rerun the key offline and coupled diagnostics with corrected species ordering
- especially re-check the interleaved branch in the later pre-failure window where deployment actually goes bad
