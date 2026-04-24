# OpenAlex citation graph around the EFNO paper

_Date: 2026-04-23_

## Why this was the next useful step

The guidance now explicitly says to use scholarly search tools such as OpenAlex to expand the reference graph around EFNO. That is useful here because there is no obvious public EFNO codebase, so the next best evidence source is the paper neighborhood:
- what EFNO cites
- what now cites EFNO
- which nearby papers are most relevant to dataset construction, preprocessing, physical constraints, and CFD-facing evaluation

## Durable artifacts added

- script: `/root/workspace/scripts/openalex_work_graph.py`
- EFNO graph artifact: `/root/workspace/artifacts/papers/efno_weng_2025/openalex_graph.json`

## Root work

- **Weng et al. — Extended Fourier Neural Operators to learn stiff chemical kinetics under unseen conditions**
- DOI: `10.1016/j.combustflame.2024.113847`
- OpenAlex work id: `W4404610207`
- cited by: `13` works in the current OpenAlex snapshot
- references: `36` works

## What EFNO cites that matters most for this project

The OpenAlex graph confirms that EFNO sits at the intersection of:
1. **classical reacting-flow numerics and reduction**
2. **ANN/tabulation work for combustion chemistry**
3. **operator-learning models such as DeepONet/FNO**
4. **data balancing / transformation ideas**

### Particularly relevant references surfaced by OpenAlex

- **Box-Cox transformation / skew handling**
  - Box and Cox, *An Analysis of Transformations* (1964)
  - Supports the paper's use of BCT for skewed species distributions.

- **Combustion chemistry acceleration / tabulation lineage**
  - Chatzopoulos et al. (2012), RCCE + ANN for turbulent flames
  - Franke et al. (2017), ANN tabulation for LES-PDF combustion
  - Wan et al. (2020), ML-based chemistry reduction for DNS oxy-flames

- **Mechanism reduction / turbulent-combustion framing**
  - Lu and Law (2005), directed relation graph
  - Peters (1988), laminar flamelet concepts

- **Operator-learning lineage**
  - Lu et al. (2021), DeepONet
  - Li et al. (2020), Fourier Neural Operator

## What now cites EFNO that looks most actionable

Among the citing papers, several are directly relevant to the current reproduction-and-extension path.

### 1. Data-augmented physics-informed operator learning for H2 combustion
- DOI: `10.1016/j.engappai.2025.111850`
- OpenAlex title: *Fast and accurate prediction of H2 combustion via data-augmented physics-informed operator learning*

Useful signal from OpenAlex abstract:
- 0D constant-volume hydrogen combustion
- `11` thermochemical variables: `9` species + `T` + `p`
- variables span up to `11` orders of magnitude
- uses **small amounts of pre-labeled training data** to augment a physics-informed approach
- reports strong accuracy with limited data

Immediate relevance:
- strengthens the case that our current **species-only** target path is not paper-faithful enough
- supports moving toward **joint thermochemical targets** rather than species-only deltas
- reinforces that **scale disparity** is a first-class issue, not a detail

### 2. Widely applicable NH3/H2 turbulent-combustion acceleration
- DOI: `10.1016/j.combustflame.2025.114218`
- Title: *Deep learning based combustion chemistry acceleration method for widely applicable NH3/H2 turbulent combustion simulations*

Even without full abstract text in OpenAlex, the title alone is relevant because it points to:
- a broader-condition training/evaluation objective
- direct turbulent-combustion applicability
- likely overlap with the local Peking University DFODE line already present in `/root/workspace/papers`

Immediate relevance:
- a reminder that the real target is not just offline autoignition regression
- we should keep building toward **widely applicable** and **coupled-simulation** evaluation

### 3. Phy-ChemNODE
- DOI: `10.3389/fther.2025.1594443`
- Title: *Phy-ChemNODE: an end-to-end physics-constrained autoencoder-NeuralODE framework for learning stiff chemical kinetics of hydrocarbon fuels*

Useful signal from OpenAlex abstract:
- learns stiff chemistry in a **latent space**
- uses end-to-end AE + NeuralODE training
- includes **elemental mass conservation constraints** in the loss
- evaluates **a posteriori autoregressive inference**
- studies weighting of loss terms and latent dimension

Immediate relevance:
- independently supports our decision to add physical-consistency metrics early
- reinforces that **loss-weight tuning** is important and should not be treated casually
- provides an adjacent comparison point if EFNO-style losses continue to underperform

### 4. Scientific machine learning in combustion for discovery, simulation, and control
- DOI: `10.1016/j.proci.2025.105796`

Immediate relevance:
- likely useful as a survey/framing paper for later manuscript and docs work
- likely valuable for positioning EFNO relative to the broader combustion-ML landscape

## Concrete implications for current implementation choices

### A. Joint temperature + species prediction is becoming harder to avoid
The citation graph adds more support for a concern already visible in the EFNO paper itself:
- several neighboring works model the **full thermochemical state**, not only species deltas
- our current DFODE-kit path is still **species-only**

So the current baseline remains useful, but it should be treated as an **intermediate scaffold**, not the final reproduction target.

### B. Data construction and transformation are central, not auxiliary
The graph reinforces three design priorities:
1. hard enough datasets
2. transformations for extreme scale disparity
3. careful balancing when samples are uneven or concentrated in easy regions

That is consistent with what we already observed experimentally:
- the earlier small H2 comparison was too trivial
- the longer-horizon and holdout-aware benchmark was more informative
- the current EFNO-style loss design is not yet sufficient by itself

### C. A-posteriori and rollout validation remain the right north star
Both the local papers and EFNO citation neighborhood keep pointing the same way:
- one-step metrics are necessary but insufficient
- rollout/autoregressive behavior matters
- coupled-CFD usefulness matters even more

## Recommended near-term follow-up

Based on this citation graph, the next high-value technical steps are:

1. **Extend the benchmark contract from species-only to thermochemical state prediction**
   - at minimum, prototype `T + species`
   - document any pressure handling choice explicitly

2. **Tune and diagnose the current EFNO-style loss more systematically**
   - especially `lambda_data`, `lambda_elements`, `lambda_mass`
   - inspect whether the current quartile-inspired weighting is over-amplifying hard tails or destabilizing training

3. **Inspect nearby 2025 papers more directly**
   - especially the H2 operator-learning paper and the NH3/H2 broad-applicability paper
   - extract any concrete dataset or preprocessing details if accessible

## Bottom line

OpenAlex did not solve the missing-code problem, but it did improve the evidence base. The EFNO paper clearly belongs to an active, combustion-specific line of work where the important recurring themes are:
- skew-aware transformations
- physics constraints
- broad-condition generalization
- full thermochemical-state learning
- rollout / a-posteriori validation

That strengthens the conclusion that our next model-side work should focus less on adding arbitrary architectures and more on:
- better target design
- better split design
- better physical-loss tuning
- and eventually a more paper-faithful thermochemical-state benchmark.
