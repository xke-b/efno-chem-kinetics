# C2H4 multiscale architecture ideas after the CVODE and power-delta calibrations

_Date: 2026-04-24_

## Context

After the recent C2H4 calibration work, the picture is sharper:

- the proper DeepFlame CVODE baseline at `1e-6` showed that the current project surrogates remain far from chemistry-faithful on key intermediates
- the first power-delta deployment test on `dp100 + oneD@0.2` showed that changing the target transform can dramatically improve **bulk thermodynamic / source-term behavior**
- but the same test also showed that target reformulation alone does **not** recover the missing reactive intermediate manifold

So the next C2H4 question is not just about targets anymore. It is now reasonable to ask whether the current model class is also too weak or too poorly structured for the multiscale intermediate-chemistry problem.

This note records a focused architecture idea shortlist, with explicit selection of what is worth testing next.

## Source note

The motivating ideas discussed here are:
- frequency-domain learning can help separate coarse and fine scales
- naive FNO may still be insufficient for the full multiscale target problem
- possible extensions include:
  - multi-scale Fourier branches
  - wavelet-style decomposition
  - attention mechanisms
  - residual / correction formulations
  - hybrid physics-aware couplings

These are useful hypotheses, not yet validated project findings.

## What seems most plausible for this project

### 1. Attention on top of the existing spectral token path

This is the most attractive next architecture idea.

Why it fits the project:
- the current `fno1d` scaffold already maps the thermochemical state into a token sequence and applies repeated spectral + pointwise mixing
- attention can be inserted as a relatively local architectural extension without completely rewriting the export/runtime path
- attention gives the model a way to **reweight interactions among state components dynamically**, which is attractive for cases where a tiny subset of intermediate species matters strongly only in narrow regimes
- this is more plausible as a short-turnaround experiment than wavelets or a full multibranch operator redesign

Why it is relevant to the current C2H4 failure:
- the model is currently able to keep some bulk quantities (`T`, `p`, `OH`, `CO2`) in the right ballpark while collapsing rare or multiscale intermediates (`C2H5`, `C2H3`, `CH2CHO`, `CH2CO`)
- that pattern suggests the model may be under-allocating representational capacity to **small but chemically decisive channels**
- an attention block could let the network condition more sharply on the combinations of temperature, pressure, and species channels that indicate entry into those reactive submanifolds

### 2. Multi-scale Fourier branches

This is interesting, but not the first thing I would test.

Why it is promising:
- separate low-/mid-/high-mode pathways are a natural extension of the frequency-domain argument
- it would let the model learn different spectral regimes with less interference

Why it is not first:
- the current project bottleneck is not yet obviously a pure “missing high-frequency spatial content” problem
- our input is a flattened thermochemical state vector, not a spatial field in the classic FNO sense
- a multi-branch Fourier redesign is a larger architecture change, while attention is a smaller and more interpretable first test

### 3. Wavelet transform / multiresolution decomposition

This is scientifically interesting, but lower priority right now.

Why not first:
- it is a larger divergence from the current export and runtime path
- it adds implementation and deployment complexity before we have exhausted simpler structure changes
- the current evidence still points more strongly to **semantics and rare-regime weighting** than to a proven need for localized wavelet machinery

### 4. Residual / correction learning

This is attractive as a second-tier follow-up.

Potential use here:
- predict a correction on top of a simpler baseline or target decomposition
- especially attractive if paired with the new power-delta target, where the model already appears to behave like an over-damped corrector

Why not first:
- a good residual baseline has to be defined carefully in the coupled DeepFlame setting
- it is easy to create a residual formulation that looks good offline but is awkward at export/deployment time

### 5. Hybrid physics-aware coupling

This remains strategically relevant, but it is not the next small experiment.

Reason:
- this is closer to deployment policy or solver coupling design than to a fast architecture test
- right now we still need a better learned chemistry representation before investing in more complex hybridization beyond the existing safeguards and baseline comparisons

## Selected ideas to carry forward

Based on the current evidence, the ideas worth taking forward now are:

### Priority A — attention mechanism

**Selected as the next architecture family to test.**

Minimal design goal:
- add a small attention block to the existing `fno1d` token pipeline rather than replacing the whole model

Good first versions:
1. **post-spectral self-attention**
   - after the spectral + pointwise stack, apply multi-head self-attention over tokens before the final token projection
2. **interleaved spectral-attention blocks**
   - alternate spectral blocks and lightweight attention blocks
3. **attention-gated token reweighting**
   - cheaper than full attention; lets the network amplify chemically important token interactions

Why this is the first test:
- smallest conceptual jump from the current architecture
- keeps export feasibility in reach
- directly targets the “rare but important channels get ignored” hypothesis

### Priority B — power-delta target + attention combination

**Selected as the preferred experimental pairing.**

Reason:
- power-delta already improved bulk deployment behavior strongly
- the next question is whether a stronger architecture can preserve that bulk improvement while recovering intermediate chemistry
- testing attention on top of the old BCT-delta target would be less informative than testing it with the currently better-calibrated target transform

### Priority C — species-aware weighting / diagnostic attention readout

**Selected as a supporting design idea.**

Reason:
- if attention is introduced, inspect whether attention mass actually shifts toward the intermediate species in reactive regimes
- pair architecture tests with explicit per-species evaluation against CVODE at `1e-6`
- do not rely only on global MAE or runtime survival

## Concrete experiment plan

### Experiment 1: lightweight spectral-attention FNO on `dp100 + oneD@0.2` with power-delta targets

Goal:
- test whether attention recovers any of the lost intermediate manifold while keeping the improved bulk behavior from power-delta targets

Minimal implementation sketch:
- start from current `dfode_kit/models/fno1d.py`
- add optional params such as:
  - `attention_heads`
  - `attention_layers`
  - `attention_dropout`
  - `attention_position` = `post_spectral` or `interleaved`
- keep the input/output contract unchanged so export remains feasible

Evaluation:
1. offline sanity on the training/holdout data
2. export validation parity check
3. DeepFlame deployment to `1e-6`
4. compare against CVODE using:
   - `Qdot`
   - `|ΔT|`
   - `|Δp|`
   - `C2H5`, `C2H3`, `CH2CHO`, `CH2CO`

Success criterion:
- retain much of the bulk improvement from power-delta
- improve at least some key intermediate ratios by meaningful orders of magnitude versus the current power-delta mixed model

### Experiment 2: attention ablation on pure oneD-augmented data

Run only if Experiment 1 shows movement.

Purpose:
- separate “architecture helps” from “architecture only helps because of the mixed dataset backbone”

### Experiment 3: multi-scale spectral branch only if attention moves the right metrics but not enough

Reason:
- if attention helps but still saturates, that would be a stronger justification for a larger multi-branch spectral redesign

## What I am not selecting first

Not first:
- wavelets
- large multi-branch Fourier redesign
- fully hybrid solver-operator coupling changes

Reason:
- they are larger deviations with less immediate deployment payoff than a lightweight attention extension

## Current takeaway

The best architecture idea to test next is **attention added to the current spectral operator path**, especially combined with the new **power-delta target**. That is the smallest credible next step that could improve multiscale intermediate chemistry without abandoning the current export/deployment workflow.
