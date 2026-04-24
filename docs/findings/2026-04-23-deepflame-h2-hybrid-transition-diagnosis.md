# DeepFlame H2 hybrid transition diagnosis: the corrected Burke branch collapses after `1e-05` as the active-cell state shifts toward cooler, higher-pressure, more oxidizer-rich mixtures and the predicted next-step HP failure rate surges

_Date: 2026-04-23_

## Why this was the next step

The hybrid horizon extension established a clear transition:
- the corrected Burke hybrid branch is still mostly learned at `1e-05`
- it becomes near-total fallback by `1.1e-05`

So the next useful step was to inspect the state around that transition rather than extend the horizon blindly.

## New assets and artifacts

### Scripts
- `/root/workspace/scripts/analyze_deepflame_h2_transition_window.py`
- `/root/workspace/scripts/parse_deepflame_hybrid_log.py`

### Artifacts
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_transition_window_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_transition_comparison.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_fields_1e-05_vs_9e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_fields_1.1e-05_vs_1e-05.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_fields_1.2e-05_vs_1e-05.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hp_risk_1e-05.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hp_risk_1.1e-05.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hp_risk_1.2e-05.json`

## First important observation: the written fields themselves still look numerically well-behaved
At all three times (`1e-05`, `1.1e-05`, `1.2e-05`):
- species sums stay extremely tight to `1`
- no gross negative-species pathology appears in the written state
- temperature extrema remain bounded in a plausible range for this case

For example:
- `1e-05`: `min/max(T) = 370.907, 2428.61`
- `1.1e-05`: `377.889, 2434.31`
- `1.2e-05`: `365.664, 2435.01`

So the transition is **not** caused by obvious written-field blow-up.

## What changes in the DNN-active subset
The more informative signal comes from the cells that satisfy the DeepFlame activation rule `T > 510 K`.

### Active-cell counts rise modestly
- `1e-05`: `10442`
- `1.1e-05`: `10771`
- `1.2e-05`: `11245`

So part of the change is that more cells enter the learned/fallback competition window.

### Active cells become slightly cooler on average and more concentrated near the activation threshold
- active mean `T`
  - `1e-05`: `1841.66 K`
  - `1.1e-05`: `1824.62 K`
  - `1.2e-05`: `1800.36 K`
- active fraction with `T < 600 K`
  - `1e-05`: `0.0424`
  - `1.1e-05`: `0.0493`
  - `1.2e-05`: `0.0602`
- active fraction with `T < 700 K`
  - `1e-05`: `0.0630`
  - `1.1e-05`: `0.0711`
  - `1.2e-05`: `0.0845`

This is not a huge thermodynamic shift, but it is a directional one: the active set becomes more populated by cells closer to the `510 K` trigger threshold.

### Active cells also drift to higher pressure
- active mean `p`
  - `1e-05`: `105957.9 Pa`
  - `1.1e-05`: `106968.0 Pa`
  - `1.2e-05`: `107328.2 Pa`

So the collapse happens as the active set shifts toward slightly higher-pressure conditions.

## Composition shift in the active subset
Between `1e-05` and `1.2e-05`, the active-cell mean composition changes as follows:

- `H2`: `+0.00180`
- `O2`: `+0.02462`
- `H2O`: `-0.00761`
- `OH`: `-0.01726`
- `HO2`: `-6.99e-05`
- `H2O2`: `-8.41e-05`
- `H`: `+1.05e-04`
- `O`: `-0.00151`

Interpretation:
- the active subset becomes **more oxidizer-rich** (`O2` rises)
- and **less product / radical rich** (`H2O`, `OH`, `HO2`, `H2O2`, `O` all fall)

So the learned branch is being asked to operate more often on cooler, somewhat higher-pressure, less-burnt / less-radical states near the DNN activation boundary.

## HP-risk change is dramatic, not subtle
Using the real exported checkpoint on the written states:

### At `1e-05`
- active cells: `10442`
- offline HP failure fraction of active cells: `0.5394`
- hybrid runtime fallback fraction of active cells: `0.3081`

### At `1.1e-05`
- active cells: `10771`
- offline HP failure fraction of active cells: `0.9319`
- hybrid runtime fallback fraction of active cells: `0.9505`

### At `1.2e-05`
- active cells: `11245`
- offline HP failure fraction of active cells: `0.9882`
- hybrid runtime fallback fraction of active cells: `0.9751`

So the collapse is driven by a **real transition into an HP-unreconstructable next-step regime**, not merely by the guard staying conservative.

## Important nuance about the metrics
The offline HP-risk fractions and the runtime log fallback fractions are not numerically identical because they are measuring related but not identical things:
- the offline HP-risk script evaluates the exported model directly on the written state
- the runtime log also includes guard-triggered fallback and reflects the exact in-loop state/path

But around the transition they tell the same qualitative story:
- by `1.1e-05`, the corrected branch has entered a regime where most active cells are no longer safely usable by the learned path

## Main interpretation
The corrected hybrid branch fails late not because the written CFD state becomes obviously corrupted, but because the active DNN subset drifts into a region characterized by:
- slightly cooler active temperatures
- more near-threshold active cells
- somewhat higher pressure
- more oxidizer-rich / less product-radical compositions

In that region, the exported species update increasingly implies next-step states that are HP-unreconstructable.

## Updated practical conclusion
The corrected Burke hybrid policy is now best described as:
- a **meaningful short-horizon deployment bridge**
- still clearly superior to Burke supervised in guarded operation
- but not yet robust across the later active-state distribution that develops after `~1e-05`

## Most useful next step
The next concrete step should be targeted mitigation for this specific late-time regime, not more generic tuning.

The most useful candidates are:
1. **activation-region gating**
   - restrict learned chemistry further in the vulnerable near-threshold band (for example a higher `frozenTemperature` or an additional composition-aware guard)
2. **state-conditioned fallback diagnostics**
   - explicitly quantify fallback / HP-failure rates versus current-cell `T`, `p`, and a small set of species like `O2`, `H2O`, `OH`
3. **case-side guard ablation**
   - test whether a stricter temperature-band or composition-band guard can preserve a useful learned fraction beyond `1e-05` without collapsing immediately to full fallback

At this point the bottleneck is no longer “can the hybrid idea work at all?” It can. The bottleneck is now **how to keep the learned branch out of the specific active-state region that triggers the late HP-failure phase transition**.
