# C2H4 chemistry-proxy 5k deployment attempt: fixing label semantics alone without enough coverage is not enough—the model fails catastrophically by `4e-7`

_Date: 2026-04-24_

## Why this was the next step

After the chemistry-proxy relabeling scout showed that the current case-pair CFD labels differ materially from one-step chemistry-only evolution, the next concrete question was obvious:

- if I train on the chemistry-proxy relabeled targets instead, does the coupled behavior improve?

That is the right experiment to distinguish:
- “label semantics matter”
from
- “label semantics matter and are already enough on their own.”

## What I trained

Dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_chemistry_proxy_5k.npy`

Runner:
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_chemistry_proxy_5k_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_chemistry_proxy_5k_fno_smoke_deepflame_bundle/`

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_chemistry_proxy_5k_fno_batched_full`

## Main runtime result

This chemistry-proxy-only `5k` model fails extremely early.

Observed written times:
- `1e-07`
- `2e-07`
- `3e-07`

It then crashes during the `4e-07` step with a thermodynamic failure in Cantera HP reconstruction:

- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP): No convergence in 500 iterations`

The crash state is severe:
- target enthalpy around `-1.30484e5`
- current pressure around `18524.84 Pa`
- starting temperature around `12.89 K`
- current temperature essentially collapsed to `~2.5e-236 K`

So this is not a mild regression. It is a very early catastrophic deployment failure.

## Additional early warning from active-set counts

The learned active-set counts collapse sharply just before failure:
- `2e-07`: `33508`
- `3e-07`: `33628`
- `4e-07` attempt: only `520`

That is a very strong indication that the learned trajectory is leaving the normal active regime almost immediately.

## Pre-failure field summary at `3e-07`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_chemistry_proxy_5k_fno_fields_3e-07_vs_2e-07.json`

The written `3e-07` fields already show catastrophic thermochemical drift:
- `T_min = 209.475 K`
- `T_mean = 497.624 K`
- pressure mean `≈ 98734 Pa`
- pressure minimum `≈ 18503.7 Pa`
- mean `Qdot ≈ -7.85e10`
- mean `|ΔT|` from `2e-07`: `45.21 K`

So the run is already badly broken before the final HP failure line appears.

## Matched comparison versus stock at `3e-07`

Artifacts:
- JSON:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_chemproxy5k_vs_stock_3e-07.json`
- figure:
  - `/root/workspace/docs/findings/images/c2h4-chemproxy5k-vs-stock-3e-07.png`

### Activity mismatch
At `3e-07`:
- stock active cells: `33671`
- model active cells: `520`
- active intersection: `500`

So unlike the best mixed model, this chemistry-proxy-only model fails mainly by collapsing out of the stock active regime almost immediately.

### Active-union bulk pathology
On the active union:
- stock mean `Qdot`: `1.328e9`
- model mean `Qdot`: `-2.444e12`
- `Qdot` ratio: about `-1840x`
- sign mismatch fraction: `0.991`
- stock mean `T`: `2405.41 K`
- model mean `T`: `425.88 K`
- mean absolute temperature difference: `1980.26 K`
- mean absolute pressure difference: `80586 Pa`

This is a much stronger failure than the earlier best-mix-vs-stock C2H4 pathology. The model is not just quantitatively wrong; it is on a qualitatively different and unphysical trajectory.

## Species pathology at `3e-07`

The early-failure chemistry-proxy model shows drastic distortions including:
- `C2H5`: exactly `0`
- `HCCO`: about `2.47e8x` stock mean
- `OH`: about `32.8x` stock mean
- `CO`: about `3.96e-4x` stock mean
- `CO2`: about `2.21e-3x` stock mean

So the model effectively destroys the stock thermochemical manifold almost immediately.

## Interpretation

This failed attempt is still highly informative.

It shows that:
- **label semantics do matter**
- but **fixing label semantics alone with a tiny relabeled subset is not enough**

More specifically, this result suggests that the current chemistry-proxy path has at least two severe limitations:
1. the relabeled dataset is too small (`5k`) to support coupled deployment
2. the simple chemistry-only proxy path removes too much of the state-transition structure needed to stay on the solver-relevant manifold

So the chemistry-proxy result does **not** refute the label-semantics hypothesis. Instead, it refines it:
- target faithfulness matters,
- but deployment usefulness also needs sufficient regime coverage and manifold support.

## What this changes

This result narrows the next sensible direction.

The forward path should not be:
- replace the current data path with a tiny pure chemistry-proxy subset

It should be something more like:
- larger chemistry-proxy relabeling on a stronger backbone,
- or mixed targets that preserve solver-relevant coverage while improving chemistry faithfulness,
- or regime-targeted relabeling rather than global small-subset replacement.

## Current takeaway

The first chemistry-proxy deployment test failed early and badly, but it was still valuable:
- it confirms that target-semantics correction cannot be treated as a drop-in substitute for coverage,
- and it sharpens the next question from “should we relabel?” to
- **how do we improve semantics without losing the solver-relevant manifold?**
