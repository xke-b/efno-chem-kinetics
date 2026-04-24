# C2H4 `dp100 + oneD DeepFlame Xiao-style@0.2` test: early runtime survives, but the one-dimensional add-on does not yet rescue intermediate chemistry

_Date: 2026-04-24_

## Why this was the next step

The first model trained purely from the Xiao-style augmented one-dimensional DeepFlame manifold reached `1e-6`, which established that the new data path can support early deployment survival. But it still deleted the key intermediate manifold almost completely.

That sharpened the next question:
- can the one-dimensional DeepFlame augmentation become useful as a **supplement** to the stronger solver-aligned `dp100` backbone, rather than as a standalone dataset?

To test that, I built a small mixed labeled dataset:
- keep the full `dp100` labeled backbone (`50000` rows)
- add a `10000`-row subset from the labeled oneD DeepFlame Xiao-style augmented dataset
- effective add-on ratio: `0.2`

This is the most direct analog so far to the earlier successful `dp100 + canonical@0.2` current-data idea, except now the add-on comes from a **DeepFlame one-dimensional flame manifold** rather than the Cantera-only canonical path.

## Mixed dataset and model artifacts

10k labeled oneD subset:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_smoke_10k.npy`
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_smoke_10k.json`

Mixed dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2.json`

Training/export summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_smoke_baseline/summary.json`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_smoke_deepflame_bundle/`

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_smoke_np8`

## Main runtime result

The mixed model reaches `1e-6` cleanly in the stock-style `np=8` GPU regime.

Written times reached:
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

So adding the oneD DeepFlame augmentation at `0.2` does not harm early runtime survivability.

## Field analysis at `1e-6`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_fields_1e-06_vs_2e-07.json`

Reference:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_fields_1e-06_vs_2e-07.json`

### Global behavior
Compared with stock at `1e-6`:
- mean temperature difference: about `+0.04 K`
- mean pressure difference: about `+0.82 Pa`
- mean `Qdot` ratio: about **`18.03x` stock**

So bulk state alignment remains good, but source-term overdrive remains large.

### Intermediate-species behavior
The key negative result is that the oneD add-on still does **not** rescue the missing reactive intermediate manifold.

At `1e-6`, the written fields still collapse toward zero for:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`
- `HCCO`

Examples from the written means:
- `C2H5`: `4.03e-17`
- `C2H3`: `1.20e-16`
- `CH2CHO`: `2.73e-16`
- `CH2CO`: `9.81e-15`

These are effectively absent relative to stock.

## Interpretation

This is a useful negative result.

### What worked
- the mixed dataset trains and exports cleanly
- the case remains stable through `1e-6`
- the oneD add-on does not obviously poison the early solver path

### What did not work
- adding a `0.2` oneD DeepFlame augmented label component to `dp100` does **not** restore the key intermediate manifold by `1e-6`
- `Qdot` remains strongly over-driven

So the oneD DeepFlame augmentation is not yet acting as the kind of chemically corrective add-on that the earlier canonical-mix direction seemed to provide.

## What this means next

The evidence now points away from a simple “just mix in oneD-augmented labeled data” story.

More plausible next directions are:
- use the oneD DeepFlame manifold primarily as a **current-state augmentation source**, but keep label semantics closer to case-aligned chemistry
- apply **target reformulation** or regime-specific target handling for multiscale intermediates
- or build a more structured hybrid between case-aligned labels and oneD-derived augmentation, rather than direct labeled-pair concatenation

## Current takeaway

The oneD DeepFlame Xiao-style data path is now clearly useful as a solver-native manifold source, but this first `r=0.2` labeled-data mixing experiment shows that it is not yet a drop-in chemistry fix for the current `dp100` deployment problem. Early runtime survives, but the intermediate-chemistry failure remains essentially unresolved.
