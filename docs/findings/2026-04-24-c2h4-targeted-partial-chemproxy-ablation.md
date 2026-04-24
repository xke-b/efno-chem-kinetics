# C2H4 targeted partial chemistry-proxy ablation: regime-targeted relabeling sharpens the semantics hypothesis, but a first targeted 10% deployment attempt still collapses early

_Date: 2026-04-24_

## Why this was the next step

After establishing a selective relabeling path, the next useful question was no longer whether targeted rows could be found. It was whether replacing the **right** 10% of labels behaved better than the previous random 10% relabeling ablation.

That makes this a more meaningful experiment than another random-fraction sweep:
- keep the same basic `dp100` backbone,
- replace the same number of labels (`5000` rows),
- but choose them from a regime-targeted selector that emphasizes cool-active and intermediate-rich states.

## New infrastructure used

### Targeted candidate selector
- `/root/workspace/scripts/select_c2h4_relabel_candidates.py`

### Updated relabeler with explicit index-file support
- `/root/workspace/scripts/relabel_c2h4_casepair_dataset_with_cantera.py`

### Updated mixed-dataset constructor that now respects explicit selected indices
- `/root/workspace/scripts/create_c2h4_partial_relabel_dataset.py`

## Selection result on the full `dp100` backbone

Source dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`

Selection outputs:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_relabel_indices_5k.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_relabel_selection_summary_5k.json`

Compared with a random 5k subset from the same dataset, the targeted subset is much more aligned with the diagnosed failure regime:
- targeted mean temperature: `1378.02 K`
- random mean temperature: `2358.80 K`
- targeted intermediate-species sum mean: `8.478e-04`
- random intermediate-species sum mean: `9.526e-05`

So the targeted subset is about **8.9x richer** in the chosen intermediate manifold while shifting strongly away from the hot-bulk-dominated random selection.

## Chemistry-proxy relabel mismatch on the targeted subset

Relabel outputs:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_chemproxy_5k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_chemproxy_5k.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_smoke_dp100_targeted_cfd_vs_chemproxy_5k_summary.json`

The semantics mismatch is even larger than in the earlier random `dp100` scout:
- mean absolute `T_next` difference: `699.30 K`
- original mean absolute `Δp` from current state: `20.38 Pa`
- chemistry-proxy mean absolute `Δp` from current state: effectively zero under the const-pressure reactor assumption

Key species shifts remain large and structured:
- `HCCO`: `45.72x`
- `C2H5`: `0.0411x`
- `CH2CHO`: `4.51x`
- `CH2OH`: `4.18x`
- `C2H3`: `3.08x`
- `CH2CO`: `2.91x`

So the targeted subset is not only more aligned with the failure regime; it also exposes an even stronger label-semantics mismatch.

## Mixed dataset built

New mixed dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_partial_chemproxy5k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_targeted_partial_chemproxy5k.json`

Construction:
- base: full `dp100` backbone (`50000` rows)
- replaced rows: `5000`
- replaced fraction: `0.1`
- replacement rows come from the explicit targeted selector, not a random sample

## Trained/exported model

Training/export summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_targeted_partial_chemproxy5k_fno_smoke_baseline/summary.json`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_targeted_partial_chemproxy5k_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_targeted_partial_chemproxy5k_fno_smoke_deepflame_bundle/`

Training completed normally and export validation remained exact for the bundle itself.

## First deployment smoke attempt

Staged case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_targeted_partial_chemproxy5k_fno_smoke_np8`

Important failed attempt recorded:
- the first copied-case launch failed because I removed the root `0/` directory before decomposition, so the parallel run could not find `processor*/0/p`
- that was a setup mistake, not a model result
- I restored `0/`, reran `decomposePar`, and repeated the smoke run

## Main deployment result

The corrected smoke attempt **did not** inherit the late-horizon survival of the random 10% partial-relabeled model.

Instead:
- written times reach through `3e-07`
- the run then fails during the `4e-07` step
- at `Time = 4e-07`, the learned active-set count had already collapsed to only `873` cells
- failure mode: HP reconstruction failure in `dfChemistryModel::correctThermo()`

Pre-failure field summary at `3e-07`:
- artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_targeted_partial_chemproxy5k_fno_fields_3e-07_vs_2e-07.json`
- `T_min = 140.066 K`
- pressure minimum `= 6316.47 Pa`
- mean `Qdot = -1.0345e11`
- species simplex remains tight

## Interpretation

This is a strong and useful negative result.

### What worked
- the targeted selector successfully concentrated relabel effort on more relevant thermochemical states
- the relabel mismatch is indeed larger and more relevant in that targeted regime
- the new infrastructure for selective semantics experiments is now working end to end

### What failed
- simply replacing the ``right'' 10% of labels is **not** enough by itself
- in fact, this first targeted 10% attempt is worse than random partial relabeling in deployment survival

### What this means scientifically
This does **not** falsify the selective-semantics hypothesis.
It does falsify a simpler version of it:
- ``replace the most semantically mismatched rows, at the same fraction as before, and deployment will improve''

The result suggests the next bottleneck is likely about **how strongly, when, and where** the new semantics are injected, not only whether the chosen rows are more relevant.

Possible interpretations now worth testing:
- the targeted replacement is too aggressive at the current fraction (`10%`)
- late/intermediate-rich rows may need a weaker mixing schedule
- the semantics change may need to be coupled with a curriculum or staged deployment strategy
- selecting good rows is necessary but not sufficient; replacement magnitude and temporal support matter too

## Current takeaway

This is real progress because it narrows the search sharply.

We now know:
- random partial relabeling survives but regresses qualitatively
- targeted partial relabeling sharpens semantics but can destroy deployment stability even earlier

So the next semantics experiment should not be another uniform fraction replacement. It should test a more structured path such as:
- lower targeted replacement fraction
- targeted relabeling plus curriculum
- targeted relabeling limited to a better-controlled temporal window
- or staged deployment that activates the semantics-specialized model only where/when it is needed
