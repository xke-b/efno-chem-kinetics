# C2H4 corrected trajectory-divergence analysis and first aligned fix scout: the earliest drift begins by `2e-7` in `Qdot`, `C2H3`, and `CH2CO`, and the first alignment-fixed weighted-attention smoke retrain is now staged as the next corrective branch

_Date: 2026-04-24_

## Why this step followed from the corrected analysis

After correcting the species-order bug, the right next question was:
- **when** do the smoke-model trajectories first diverge from stock,
- in **which channels**,
- and what is the smallest plausible corrective retraining step to test first?

## New time-resolved divergence artifacts

### Plain power-delta smoke vs stock
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_smoke_trajectory_divergence.json`

### Attention smoke vs stock
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_attn1_smoke_trajectory_divergence.json`

These compare the full time-resolved matched-mesh rollout against the stock C2H4 baseline.

## Main result: the important chemistry drift begins almost immediately after the first learned step

For **both** smoke branches:
- first mean `Qdot` ratio below `0.5`: **`2e-07`**
- first `CH2CO` ratio below `1e-2`: **`2e-07`**
- first `HO2` ratio below `0.5`: **`6e-07`**

For `C2H3`, the ratio is already effectively collapsed at the earliest written learned time slice.

### Plain power-delta smoke
At `2e-07`:
- `Qdot` ratio: `4.05e-04`
- `C2H3` ratio: `1.43e-09`
- `CH2CO` ratio: `3.63e-08`
- `HO2` ratio: `0.937`

By `1e-06`:
- `Qdot` ratio: `1.79e-03`
- `C2H3` ratio: `2.19e-14`

### Attention smoke
At `2e-07`:
- `Qdot` ratio: `5.02e-03`
- `C2H3` ratio: `1.88e-08`
- `CH2CO` ratio: `1.09e-09`
- `HO2` ratio: `0.937`

By `1e-06`:
- `Qdot` ratio: `0.217`
- `C2H3` ratio: `3.89e-09`

## Interpretation

This sharpens the fix target substantially.

### What attention helped
The attention smoke branch preserves bulk `Qdot` much better than the plain power-delta branch later in the rollout.

### What attention did **not** fix
The crucial intermediates (`C2H3`, `CH2CO`) are still already badly collapsed by `2e-07`.

So the next fix should target the **earliest intermediate drift**, not only later bulk heat-release behavior.

## First corrective retraining step now completed

I trained the first alignment-fixed weighted-attention smoke model on the **corrected aligned `r=0.2` mixed dataset**.

### Dataset
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2_aligned.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2_aligned.json`

### New checkpoint
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_aligned_fno_powerdelta_attn1_intermediateweights_smoke.pt`

### Export bundle
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_aligned_fno_powerdelta_attn1_intermediateweights_smoke_deepflame_bundle/`

### Training summary
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_aligned_fno_powerdelta_attn1_intermediateweights_smoke_baseline/summary.json`

### Key setup
- aligned mixed dataset only
- power-delta targets
- attention heads `4`, layers `1`, post-spectral
- intermediate species weighting profile `c2h4_intermediates_v1`
- `12` epochs, validation-aware

### Result
Best validation loss:
- **`0.7246`** at epoch `12`

This is a first **fix branch**, not a final answer.

## Early corrected one-step check for the new fix branch

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_r0p2_aligned_attn1_intermediateweights_smoke_cfd_active_1e-07_vs_cvode_corrected.json`

Compared with the previously corrected promoted interleaved branch on the `1e-07` stock-active states, the new aligned weighted smoke model is:
- globally similar in corrected one-step error
- slightly improved in corrected global `R^2`
- slightly improved in corrected `OH` MAE

But it still does **not** yet revive the collapsed intermediate channels in this earliest slice:
- `C2H3` predicted mean remains effectively zero vs corrected CVODE mean `5.56e-06`
- `CH2CO` predicted mean remains effectively zero vs corrected CVODE mean `1.03e-06`

So this fix attempt is operationally useful—it establishes the corrected aligned retraining branch—but it is **not yet sufficient**.

## Current takeaway

The corrected C2H4 fix story is now clearer:

1. the earliest rollout divergence is visible by **`2e-07`**
2. the most important early-failing channels are still **`C2H3`** and **`CH2CO`**
3. attention helps later bulk `Qdot` more than it helps the first collapsed intermediates
4. the first alignment-fixed weighted retraining branch is now built and exportable, but its earliest one-step intermediate activation is still too weak

## Most justified next fix

The next corrective step should now be one of these, in this order of preference:
1. deploy and test the new **alignment-fixed weighted-attention smoke branch**
2. build a **narrow early-window corrective dataset** centered on the first learned times (`2e-07` to `4e-07`)
3. strengthen species-aware supervision specifically for the earliest divergent intermediates (`C2H3`, `CH2CO`, then `C2H5`, `CH2CHO`, `HO2`)

That is the shortest path from the corrected diagnosis to an actual deployment-facing fix attempt.
