# DeepFlame H2 inference compatibility: exported corrected EFNO species branches can run, but two deployment-contract mismatches had to be surfaced and handled

_Date: 2026-04-23_

## Why this was the next step

After showing that the corrected best EFNO branch transfers well to a Burke-mechanism, `dt=1e-6 s` offline benchmark, the next useful question was:

> Can the current best DFODE-kit checkpoint be moved into the actual DeepFlame H2 inference contract without hidden compatibility failures?

That required checking more than accuracy. It required checking:
- checkpoint format
- model architecture assumptions
- species reconstruction contract
- runtime assumptions in the example `inference.py`

## Files added/updated

Added:
- `/root/workspace/scripts/export_dfode_checkpoint_to_deepflame.py`
- `/root/workspace/scripts/analyze_last_species_reconstruction_gap.py`
- `/root/workspace/artifacts/models/h2_burke_corrected_self_rollout_predmainbct_seed0_deepflame.pt`
- `/root/workspace/artifacts/models/h2_burke_corrected_self_rollout_predmainbct_seed0_deepflame_validation.json`
- `/root/workspace/artifacts/experiments/h2_burke_case_aligned_comparison/last_species_contract_gap_seed0.json`

Updated:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/inference.py`

## Result 1: the DFODE-kit MLP checkpoint is exportable into the current DeepFlame multi-network format

DeepFlame H2 currently expects a checkpoint with:
- per-species scalar subnetworks: `net0`, `net1`, ...
- species-only normalization arrays
- species-source-term postprocessing

DFODE-kit instead saves:
- one shared multi-output MLP under `net`
- normalization arrays for either species-only or `T + species` targets

For MLP checkpoints, this is still exportable because the shared hidden trunk plus linear output head can be rewritten exactly as separate scalar-output subnetworks by slicing the final output layer row-by-row.

I implemented that exporter in:
- `/root/workspace/scripts/export_dfode_checkpoint_to_deepflame.py`

I validated it on the Burke-aligned corrected best checkpoint:
- source: `/root/workspace/data/h2_burke_corrected_self_rollout_predmainbct_seed0.pt`
- export: `/root/workspace/artifacts/models/h2_burke_corrected_self_rollout_predmainbct_seed0_deepflame.pt`

Validation artifact:
- `/root/workspace/artifacts/models/h2_burke_corrected_self_rollout_predmainbct_seed0_deepflame_validation.json`

Validation summary on 128 test states:
- max abs next-species diff: `5.49e-08`
- mean abs next-species diff: `1.60e-08`
- max abs source-term diff: `8.77e-03`
- mean abs source-term diff: `2.53e-03`

Interpretation:
- the export is effectively exact for deployable species behavior
- the small source-term differences are numerical float-level effects after scaling by density and `dt`

## Result 2: a nontrivial last-species reconstruction contract mismatch exists between the current offline evaluator and DeepFlame inference

The export was **not** the first thing that failed.

My first comparison showed a noticeable mismatch, which turned out to be informative rather than just an error.

### The mismatch

The current project evaluator reconstructs the last species as:
- `Y_last = 1 - sum(Y_main)`

But DeepFlame H2 inference currently does this instead:
- keep the input last-species mass fraction unchanged
- renormalize the predicted main species to sum to `1 - Y_last,input`

That is a real contract difference.

I quantified the gap with:
- `/root/workspace/scripts/analyze_last_species_reconstruction_gap.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_burke_case_aligned_comparison/last_species_contract_gap_seed0.json`

For the corrected best Burke-aligned checkpoint on the full Burke test split:
- evaluator-closure one-step species MAE: `3.952e-04`
- DeepFlame-preserve-last one-step species MAE: `1.125e-04`

Contract-gap statistics:
- max abs species diff: `1.459e-02`
- mean abs species diff: `3.447e-04`
- mean per-sample max abs species diff: `1.551e-03`

## Important interpretation

This means current offline summaries and deployable DeepFlame species behavior are **not automatically the same thing** if they use different last-species reconstruction rules.

For this checkpoint on this benchmark, the DeepFlame preserve-last contract was actually **better** than the current evaluator closure rule on one-step species error.

So the deployment bridge exposed a real evaluation-contract issue, not just a formatting issue.

## Result 3: the target DeepFlame H2 `inference.py` had two hardcoded runtime assumptions that blocked the exported checkpoint

A first smoke attempt against the actual example inference script failed for two reasons:

1. **Hardcoded architecture**
   - the example script assumed layers `[n_species + 2, 1600, 800, 400, 1]`
   - the exported checkpoint used the smaller hidden layers from the trained Burke model
   - this caused state-dict size mismatch errors

2. **GPU-only assumption**
   - `CanteraTorchProperties` had `GPU on`
   - the script tried to use CUDA unconditionally when that switch was on
   - in the current environment this caused CPU/CUDA tensor mismatch problems

These failed attempts were useful because they identified the exact runtime assumptions that must be relaxed for robust deployment testing.

## Result 4: after patching the example H2 inference script, the exported checkpoint runs successfully

I updated:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/inference.py`

The patch does two things:
1. infer the scalar-network hidden-layer sizes from the checkpoint instead of hardcoding them
2. fall back to CPU when CUDA is unavailable even if the case dictionary requests GPU

After that patch, a smoke test using the exported checkpoint succeeded.

On a sampled Burke test state:
- `inference.py` returned a valid `(1, 9)` source-term vector
- max abs difference versus an independent local emulation of the same exported checkpoint was `2.19e-05`

That is strong evidence that the exported checkpoint is now practically loadable by the target DeepFlame H2 Python inference path.

## Bottom line

The corrected best H2 EFNO branch is now materially closer to deployable use in the DeepFlame H2 case.

Concrete progress from this step:
- **format bridge exists**: DFODE-kit MLP checkpoints can be exported into DeepFlame's current species-network checkpoint format
- **runtime bridge exists**: the H2 example inference script can load and run the exported checkpoint after removing hardcoded layer-size and GPU assumptions
- **evaluation caveat was discovered**: the current offline evaluator and DeepFlame inference do not use the same last-species reconstruction contract

## Most useful next step

The next high-value step is now to make the offline-to-deployment comparison cleaner by aligning the project-side evaluation path with the DeepFlame species reconstruction contract, at least as an explicit alternate mode, so future H2 checkpoint decisions can distinguish:
- intrinsic model quality
- deployment-format compatibility
- evaluator-vs-deployment postprocessing differences
