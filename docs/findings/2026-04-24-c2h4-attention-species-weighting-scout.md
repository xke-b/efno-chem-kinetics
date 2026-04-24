# C2H4 attention + species-weighting scout: targeted intermediate weighting improves the first attention pilot’s bulk `Qdot` calibration and strongly lifts `CH2CHO`, but does not recover the full intermediate manifold

_Date: 2026-04-24_

## Why this was the next step

The first attention pilot on top of the power-delta target gave a mixed result:
- some channels improved (`C2H3`, `CH2CHO`)
- some worsened (`C2H5`, `CH2CO`)
- bulk `Qdot` became less over-damped again

That suggested the next move should not be “more attention layers” by default, but a more targeted test:
- keep the same lightweight attention architecture
- keep the same power-delta target
- add **species-aware supervision pressure** toward the collapsed intermediate channels

## Weighting design

I added optional species-channel loss weights to the supervised trainer.

DFODE-kit change:
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`

Workspace run helper:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`
  - now supports a named weight profile

First profile tested:
- `c2h4_intermediates_v1`

Weighted main-species channels (weight `20`):
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`
- `CH2OH`
- `HCCO`

All other main-species channels keep weight `1`.

## Training/deployment setup

Model tag:
- `c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_intermediateweights_smoke`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_intermediateweights_smoke.pt`

Bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_intermediateweights_smoke_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_intermediateweights_smoke_baseline/summary.json`

Deployed case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_intermediateweights_smoke_np8`

Reference comparison artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_attn1_intermediateweights_fields_1e-06_vs_2e-07.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_attn1_intermediateweights_vs_cvode_1e-06_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_attention_weighting_compact_summary.json`
- `/root/workspace/docs/findings/images/c2h4-dp100-plus-oned-r0p2-powerdelta-attn1-intermediateweights-vs-cvode-1e-06.png`

## Main result against CVODE at `1e-6`

### Bulk metrics
Compared across the three nearby models:

#### power-delta only
- `Qdot` ratio vs CVODE: `8.51e-4x`
- mean `|ΔT|`: `0.338 K`
- mean `|Δp|`: `28.3 Pa`

#### power-delta + attention
- `Qdot` ratio vs CVODE: `1.03e-1x`
- mean `|ΔT|`: `0.343 K`
- mean `|Δp|`: `27.0 Pa`

#### power-delta + attention + intermediate weighting
- `Qdot` ratio vs CVODE: **`1.48e-2x`**
- mean `|ΔT|`: **`0.336 K`**
- mean `|Δp|`: `28.1 Pa`

So the weighted model pulls the attention pilot back toward the better bulk-behaved regime:
- much less `Qdot` activation than unweighted attention
- temperature slightly better than both nearby variants
- pressure roughly unchanged

### Intermediate species
The weighting effect is selective.

#### `CH2CHO`
- power-delta only: `8.82e-19x`
- attention: `8.79e-12x`
- attention + weighting: **`1.61e-08x`**

This is the clearest positive movement in this scout.

#### `C2H5`
- power-delta only: `3.13e-09x`
- attention: `2.45e-15x`
- attention + weighting: `2.67e-11x`

Partial recovery from the attention-only collapse, but still worse than plain power-delta.

#### `C2H3`
- power-delta only: `1.47e-14x`
- attention: `2.61e-09x`
- attention + weighting: `2.33e-13x`

The weighting scout gives back most of the `C2H3` improvement from the attention pilot.

#### `CH2CO`
- power-delta only: `1.15e-10x`
- attention: `2.04e-12x`
- attention + weighting: `5.34e-13x`

Still very poor.

#### `CH2OH`
- power-delta only: `1.49e-08x`
- attention: `1.92e-11x`
- attention + weighting: `3.57e-09x`

Some recovery over attention-only, but not a breakthrough.

#### `HCCO`
- power-delta only: `1.69e-09x`
- attention: `9.46e-12x`
- attention + weighting: `6.30e-10x`

Again, partial recovery versus attention-only, but still not a strong result.

## Interpretation

This is another useful partial result.

### What improved
- species-aware weighting stabilizes the attention pilot’s bulk chemistry behavior relative to the unweighted attention case
- `Qdot` is pulled much closer to the heavily damped power-delta regime
- `CH2CHO` improves dramatically relative to both nearby baselines
- some channels that attention had badly worsened (`C2H5`, `CH2OH`, `HCCO`) recover somewhat

### What did not improve enough
- the full intermediate manifold is still far from recovered
- `C2H3` loses most of the improvement that attention alone produced
- `CH2CO` remains essentially collapsed
- there is no single clean weighted attention win across all target intermediates

## Current takeaway

Species-aware weighting is worth keeping in the design space, but this first profile does **not** solve the problem. It behaves like a rebalancing knob:
- it can restore some bulk control lost by the first attention pilot
- and it can help specific channels like `CH2CHO`
- but it does not yet create a consistently good intermediate-chemistry surrogate

## Most justified next follow-up

The next best step is now narrower than before:
1. keep **power-delta + attention**
2. keep species-aware ideas
3. move from one global weight profile to a more **targeted regime-aware weighting or placement test**

The strongest immediate architecture-side follow-up is likely:
- compare **post-spectral attention** against **interleaved spectral-attention** while keeping the better parts of the weighted setup fixed.
