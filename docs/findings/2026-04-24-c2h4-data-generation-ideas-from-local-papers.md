# Data-generation and augmentation ideas from the other local papers: the strongest inspiration for C2H4 is interpolation-balanced canonical data plus physics-constrained perturbation and filtering

_Date: 2026-04-24_

## Why this note

After the recent C2H4 experiments, the main bottleneck is no longer just runtime integration. It is increasingly clear that **training-data quality and coverage** are the limiting factors.

The obvious next question was whether the other local papers in `/root/workspace/papers` suggest more promising data-generation or augmentation strategies than the current crude CFD state-pair filtering path.

## Papers checked

1. `Li et al_2025_Comprehensive deep learning for combustion chemistry integration.pdf`
2. `Xiao et al. - 2026 - Enhancing deep learning of ammonia/natural gas combustion kinetics via physics-aware data augmentati.pdf`
3. `Li et al. - 2026 - DFODE-Kit Deep learning package for solving flame chemical kinetics with high-dimensional stiff ord.pdf`

I extracted their text and reviewed the dataset-construction / augmentation sections.

## What the papers suggest

### 1. Li et al. (2025): canonical laminar flames + constrained perturbation + HRR filtering
Key method details from the paper text:
- collect base states from **canonical 1D laminar premixed flames** under target-relevant operating conditions
- sample thermochemical states along those trajectories
- augment with **random perturbations** to temperature, pressure, and inert species
- perturb reactive species with an **exponential randomization** to respect multiscale species magnitudes
- renormalize reactive species to preserve mass fractions
- filter perturbed states using a **heat-release-rate change criterion**
  - in the paper, reject perturbed states whose HRR is more than `100x` above or below the original state

Why this matters for us:
- this is much closer to a **chemistry-oriented data path** than our current full-CFD state-pair subsets
- it explicitly addresses the “canonical manifold is too narrow” problem without immediately jumping to full turbulent-case sampling
- the HRR filter is especially relevant because our current late C2H4 failures often show source-term overactivity

### 2. Xiao et al. (2026): flame-structure interpolation to fix imbalance in reactive regions
This is the most directly useful idea for the current C2H4 problem.

Key method details:
- generate base data from a **single canonical 1D premixed laminar flame**
- identify that the dataset is **imbalanced**:
  - too many slowly reacting / near-equilibrium states
  - too few flame-front / strongly reactive states
- fix this by **interpolating thermochemical states at evenly spaced temperature intervals** between neighboring flame states
- then apply random perturbation on both original and interpolation-generated states
- filter nonphysical states afterward

Why this matters for us:
- our current C2H4 case-pair labels appear to have the opposite of “nice coverage”: they are solver-realistic but still miss or underweight the late intermediate-rich regions we need
- Xiao et al. gives a concrete, physically motivated way to **densify underrepresented reactive regions** without having to sample an entire expensive target CFD distribution directly
- this is probably the strongest local-paper inspiration for the next C2H4 data path

### 3. Li et al. (2026) DFODE-kit paper: augmentation with physical checks and explicit labeling loop
Key method details:
- sample from low-dimensional canonical flames
- apply controlled perturbations to create off-manifold states
- **re-label each perturbed state** with Cantera/CVODE
- reject states that fail **element-ratio / physical-consistency checks**

Why this matters for us:
- it suggests a concrete implementation path inside our own tool stack:
  - sample canonical states
  - perturb them
  - re-integrate them with the chemistry solver
  - keep only physically consistent labeled pairs
- that is much more principled than continuing to rely only on full-CFD consecutive written states

## What this means for the current C2H4 bottleneck

Yes: the other papers in `/root/workspace/papers` do contain useful inspiration, and it points in a clearer direction than our current subset sweeps.

The strongest takeaways are:
1. **Move closer to canonical chemistry data again**, instead of relying only on crude CFD state-pair subsets.
2. **Do not rely on raw canonical trajectories alone**; broaden them with constrained perturbations.
3. **Explicitly address data imbalance in reactive regions**, especially via interpolation/densification near the flame front.
4. **Filter augmented states physically**, with criteria like HRR change and/or element-ratio consistency.

## Most justified next data path

Based on the local-paper evidence, the next promising C2H4 data-construction path is:

### A. Build a canonical C2H4 1D flame dataset
- one or a small family of canonical C2H4 premixed flames aligned with the target mechanism and broadly relevant operating conditions

### B. Add interpolation-based densification
- densify states in underrepresented reactive regions, likely using temperature-ordered interpolation as in Xiao et al.

### C. Add physics-constrained perturbation
- perturb `T`, `p`, inert species, and reactive species using scale-aware rules
- re-normalize appropriately

### D. Re-label with Cantera/CVODE and filter
- integrate the perturbed states forward with the chemistry solver
- reject nonphysical or overly extreme labels using criteria such as:
  - HRR change thresholds
  - element-balance consistency
  - basic thermodynamic admissibility checks

## Why this is more promising than the current path

Our recent C2H4 experiments already showed that:
- naive full-CFD case-pair labels can be solver-usable but chemically biased
- simple `|Δp|` / `|ΔT|` subset logic is non-monotonic
- naive early+late mixing can destabilize badly
- even gentle late curriculum mostly helps by deployment timing, not by fixing the underlying chemistry-coverage problem

The local-paper methods suggest a more principled alternative:
- **construct better chemistry-oriented labels first**, then worry about deployment specialization second

## Current takeaway

Yes — checking the other local papers was worth it. The best concrete inspiration is:
- **Xiao et al. (2026): interpolation to repair reactive-region imbalance**
- combined with
- **Li et al. (2025) / DFODE-kit (2026): constrained perturbation + physical filtering + re-labeling**

That is now the most justified next data-generation direction for C2H4.
