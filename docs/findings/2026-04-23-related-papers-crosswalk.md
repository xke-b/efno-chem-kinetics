# Crosswalk from the other local papers to current EFNO reproduction decisions

_Date: 2026-04-23_

## Purpose

This note records how the other papers in `/root/workspace/papers` inform the EFNO program.

## Papers examined

1. `Li et al. - 2026 - DFODE-Kit ...`
2. `Li et al_2025_Comprehensive deep learning for combustion chemistry integration.pdf`
3. `Xiao et al. - 2026 - Enhancing deep learning of ammonia/natural gas combustion kinetics via physics-aware data augmentati.pdf`

## Key takeaways relevant to current work

### 1. DFODE-kit paper
Relevant ideas:
- canonical-flame sampling as a practical data source
- augmentation to approximate turbulent composition-space coverage
- multiscale preprocessing and physics-informed constraints
- a posteriori validation in CFD, not only offline ML metrics
- end-to-end timing and communication overhead matter

Current implication:
- our current benchmark work should keep moving toward **a posteriori usefulness**, not just one-step regression
- rollout evaluation and future DeepFlame integration remain aligned with the package paper's priorities

### 2. Comprehensive deep learning for combustion chemistry integration (2025)
Relevant ideas:
- low-dimensional canonical laminar flames can be used as the base data source
- perturbation/data augmentation broaden composition-space coverage
- generalization should be tested across fuels and turbulent flame configurations
- strong emphasis on **a posteriori validation** in reacting-flow simulations

Current implication:
- our holdout-by-initial-condition evaluation is a good start, but not sufficient
- future evaluation should explicitly distinguish:
  - offline seen-condition accuracy
  - offline unseen-condition generalization
  - CFD-coupled a posteriori usefulness

### 3. Xiao et al. (2026) on physics-aware augmentation and scale separation
Relevant ideas:
- data imbalance near steep flame-front gradients is an important problem
- physics-aware augmentation can improve training data quality
- scale-separating target formulations can help low-temperature / small-magnitude targets
- a posteriori HIT-flame validation under unseen conditions is critical

Current implication:
- the current H2 one-step datasets can easily become too trivial if the sampled horizon is too short
- target formulation matters a lot; our present species-only target path may need scale-aware redesign
- future EFNO-style work should likely compare:
  - BCT-only targets
  - explicit scale-separated targets
  - horizon choices that avoid near-identity labels

## Most immediate effect on the program

These papers strengthen three near-term decisions:

1. **Use harder, more informative datasets**
   - already supported by the longer-horizon H2 probe
2. **Prefer holdout and unseen-condition evaluation over same-dataset scoring**
   - already supported by the new holdout comparison
3. **Treat target formulation and data construction as first-class design choices**
   - not just model-backbone choices

## Bottom line

The other local papers support the current direction:
- benchmark-first
- holdout-aware
- rollout-aware
- physics-aware
- ultimately a-posteriori / coupled-usefulness oriented

They also warn against a common trap already observed here:
- seemingly excellent results on too-easy one-step datasets can be misleading.
