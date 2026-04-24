# C2H4 targeted partial chemistry-proxy ablation (`2%`): lowering the targeted replacement strength delays collapse substantially, but still does not recover solver-usable deployment

_Date: 2026-04-24_

## Why this was the next step

The first targeted partial-relabeled C2H4 deployment attempt used the same replacement fraction as the earlier random partial relabeling test:
- `5000 / 50000` rows (`10%`)

That result failed very early, which ruled out the simple idea that better row choice alone is enough.

The next sharp question was therefore:
- does the targeted path fail because the selected rows are wrong,
- or because the semantics are being injected too aggressively at `10%`?

So I ran the smallest cleaner follow-up:
- keep the same targeted selector idea,
- lower the targeted replacement fraction to `2%` (`1000 / 50000` rows),
- and rerun training/export/deployment.

## New targeted subset

Selector outputs:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_relabel_indices_1k.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_relabel_selection_summary_1k.json`

This targeted 1k subset is highly concentrated in the intended regime:
- `600` cool rows (`60%`)
- `400` hot rows (`40%`)
- mean temperature: `1571.06 K`
- intermediate-species sum mean: `1.975e-03`

Compared with a random 1k subset:
- random mean temperature: `2334.44 K`
- random intermediate-species sum mean: `1.000e-04`

So the targeted selector still enriches the chosen intermediate manifold strongly while avoiding a hot-bulk-dominated sample.

## Relabeling and mixed dataset

Relabeled dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_chemproxy_1k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_chemproxy_1k.json`
- mismatch summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_cfd_vs_chemproxy_1k_summary.json`

Mixed targeted-partial dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_partial_chemproxy1k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_partial_chemproxy1k.json`

Replacement fraction:
- `1000 / 50000 = 0.02`

## Training/export

Training/export summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_targeted_partial_chemproxy1k_fno_smoke_baseline/summary.json`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_targeted_partial_chemproxy1k_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_targeted_partial_chemproxy1k_fno_smoke_deepflame_bundle/`

Training and export completed normally.

## Deployment smoke result

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_targeted_partial_chemproxy1k_fno_smoke_np8`

Main result:
- the run progresses much farther than the targeted `10%` model
- written times reach through `8e-07`
- the run then fails during the `9e-07` step with HP reconstruction failure

So lowering the targeted replacement fraction from `10%` to `2%` is **materially better**, but still far from solver-usable deployment.

## Pre-failure field anatomy at `8e-07`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_targeted_partial_chemproxy1k_fno_fields_8e-07_vs_2e-07.json`

Key metrics:
- `T_min = 105.469 K`
- pressure minimum `= 1160.37 Pa`
- mean `Qdot = -2.225e10`
- species simplex remains tight
- `C2H5` is identically zero in the written `8e-07` fields
- major late intermediates remain effectively collapsed (`C2H3`, `CH2CHO`, `HCCO`, `CH2CO`, `CH2OH` all near zero)

So, again, the issue is not simplex failure. It is thermodynamic and chemical-manifold failure.

## Interpretation

This is a useful mixed result.

### Positive information
Lowering the targeted fraction from `10%` to `2%` clearly helps horizon survival:
- targeted `10%`: fail during `4e-07`
- targeted `2%`: fail during `9e-07`

So replacement strength does matter, not just row choice.

### Negative information
But `2%` targeted replacement is still not enough to recover the kind of solver-usable behavior seen even in the random `10%` partial relabeling survival test.

The model still develops:
- severe cold outliers
- catastrophic pressure collapse in some cells
- strongly negative mean `Qdot`
- effective deletion of the key intermediate manifold

### What this narrows next
This means the next semantics path should probably not be:
- larger targeted replacement
- or another uniform targeted fraction at similar strength without another design change

More justified next directions now are:
- even weaker targeted replacement with stronger backbone preservation
- staged or scheduled deployment of semantics-specialized models
- curriculum-style training rather than direct target replacement
- target design changes inspired by Xiao et al. rather than simple subset substitution alone

## Current takeaway

This experiment is real progress because it changes the decision boundary.

We now know:
- better row choice alone is insufficient
- targeted replacement strength matters a lot
- reducing targeted replacement from `10%` to `2%` improves survival substantially
- but the targeted semantics path is still not solver-usable in its current direct-substitution form

So the next useful experiment should likely combine **weaker semantics injection** with **training or deployment staging**, rather than continuing only with direct targeted substitution.
