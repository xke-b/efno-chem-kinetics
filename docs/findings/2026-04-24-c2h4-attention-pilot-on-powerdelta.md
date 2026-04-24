# C2H4 attention pilot on top of power-delta targets: a small post-spectral attention block changes some intermediate channels, but does not yet produce a clear overall win

_Date: 2026-04-24_

## Why this was the next step

After the CVODE baseline and the first power-delta deployment test, the next most justified architecture idea was a lightweight attention mechanism on top of the current spectral token path.

The reasoning was:
- power-delta targets already improved bulk thermodynamic behavior sharply
- the remaining gap looked concentrated in **rare but chemically decisive intermediate channels**
- a small attention block might help the model allocate representational capacity more selectively to those channels without abandoning the current export/deployment path

## Architecture change

I added optional attention support to the current DFODE-kit `fno1d` scaffold.

Main implementation:
- `/opt/src/DFODE-kit/dfode_kit/models/fno1d.py`

Current design:
- keep the existing spectral + pointwise stack
- then apply optional token-wise self-attention blocks before the final output projection

New model knobs:
- `attention_heads`
- `attention_layers`
- `attention_dropout`

For this first pilot I used:
- `attention_heads = 4`
- `attention_layers = 1`
- `attention_dropout = 0.0`

I also updated the FNO export bridge so the deployed DeepFlame bundle can rebuild the attention-augmented model shape consistently.

## Training/deployment setup

Dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2.npy`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke.pt`

Bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke_baseline/summary.json`

Deployed case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke_np8`

Reference comparison:
- CVODE baseline at `1e-6`

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_attn1_fields_1e-06_vs_2e-07.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_attn1_vs_cvode_1e-06_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_attn1_vs_powerdelta_compact_summary.json`
- `/root/workspace/docs/findings/images/c2h4-dp100-plus-oned-r0p2-powerdelta-attn1-vs-cvode-1e-06.png`

## Main result against CVODE at `1e-6`

### Bulk behavior
Compared with the non-attention power-delta model:

- mean active-region `Qdot` ratio vs CVODE:
  - power-delta only: **`8.51e-4x`**
  - power-delta + attention: **`1.03e-1x`**

- mean active-region `|ΔT|`:
  - power-delta only: **`0.338 K`**
  - power-delta + attention: **`0.343 K`**

- mean active-region `|Δp|`:
  - power-delta only: **`28.3 Pa`**
  - power-delta + attention: **`27.0 Pa`**

So the attention pilot gives:
- essentially unchanged temperature error
- a small pressure improvement
- but a much larger `Qdot` magnitude than the over-damped no-attention power-delta model

That means attention partially reactivates the chemistry, but not yet in a controlled or uniformly beneficial way.

### Intermediate species
This is the interesting part: the attention block does not help uniformly.

Key species mean ratios vs CVODE:

- `C2H5`
  - power-delta only: `3.13e-09x`
  - power-delta + attention: `2.45e-15x`
  - **worse**

- `C2H3`
  - power-delta only: `1.47e-14x`
  - power-delta + attention: `2.61e-09x`
  - **better by about five orders of magnitude**

- `CH2CHO`
  - power-delta only: `8.82e-19x`
  - power-delta + attention: `8.79e-12x`
  - **better by about seven orders of magnitude**

- `CH2CO`
  - power-delta only: `1.15e-10x`
  - power-delta + attention: `2.04e-12x`
  - **worse**

Bulk-reference channels remain similar:
- `OH`: `1.011x`
- `CO2`: `1.000x`

## Interpretation

This is a useful mixed result.

### What it says positively
- the attention idea is not inert; it does change the learned regime in a meaningful way
- some of the previously dead intermediate channels (`C2H3`, `CH2CHO`) moved upward by large orders of magnitude
- this supports the hypothesis that the current architecture can be too blunt for rare-species structure, and that lightweight token interaction reweighting can matter

### What it says negatively
- the first attention pilot is **not** a clean overall win
- it does not recover the full intermediate manifold
- it worsens some channels (`C2H5`, `CH2CO`)
- it also gives up some of the strongly damped bulk `Qdot` behavior that made the plain power-delta model attractive

So attention helps in a **selective and unstable** way rather than a globally corrective one.

## Current takeaway

The first post-spectral attention pilot is promising enough to justify further work, but not promising enough to declare the architecture problem solved. The strongest conclusion is narrower:

- **attention can move at least some collapsed intermediate channels in the right direction**
- but a naive one-block attention addition is not yet the right final architecture for C2H4

## Most justified next follow-up

The next attention-side experiment should be more targeted rather than larger by default. The best candidates now are:
1. attention + **species-aware weighting** in the loss
2. attention + **regime-focused dataset selection** rather than global retraining
3. attention placement variants (`interleaved` vs current `post-spectral`)

At this stage, the evidence says attention is worth continuing, but only with sharper diagnostics and species-aware objectives.
