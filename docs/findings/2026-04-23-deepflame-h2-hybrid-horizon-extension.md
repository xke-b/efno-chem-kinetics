# DeepFlame H2 hybrid horizon extension: the corrected Burke hybrid branch stays mostly learned through `1e-05`, then collapses into near-total fallback after `1.1e-05`

_Date: 2026-04-23_

## Why this was the next step

After the first case-side hybrid prototype succeeded to `5e-06`, the next unresolved question was whether the corrected Burke branch was:
- merely surviving a short transient, or
- actually maintaining a meaningful learned fraction over a longer horizon.

So I extended the corrected Burke hybrid case to a longer horizon and added a reusable log parser to quantify fallback usage over time.

## New reusable asset

- `/root/workspace/scripts/parse_deepflame_hybrid_log.py`

This parser extracts, by solver time:
- total active DNN cells
- total fallback cells
- HP-failure fallback cells
- guard-only fallback cells
- learned cells
- fallback / learned fractions
- temperature extrema

## New artifacts

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hybrid_2e-5_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hybrid_1e-5_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_mlp_hybrid_5e-6_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/hybrid_case_selected_comparison.json`

## Run setup

Case:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct`

Procedure:
1. run from `0` to `1e-05`
2. restart from latest time and continue to `2e-05`

The continued run completed successfully to `2e-05`.

## Main quantitative result

### Corrected Burke hybrid branch remains mostly learned through `1e-05`
Selected times:

- `5e-06`
  - active cells: `9270`
  - fallback cells: `2683`
  - fallback fraction: `0.2894`
  - learned fraction: `0.7106`
- `1e-05`
  - active cells: `10201`
  - fallback cells: `3143`
  - fallback fraction: `0.3081`
  - learned fraction: `0.6919`

So the corrected branch does **not** immediately deteriorate after `5e-06`; it still keeps about `69%` of active cells on the learned path at `1e-05`.

### But a sharp degradation begins at `1.1e-05`
- `1.1e-05`
  - active cells: `10442`
  - fallback cells: `9925`
  - fallback fraction: `0.9505`
  - learned fraction: `0.0495`
- `1.2e-05`
  - fallback fraction: `0.9751`
- `1.3e-05`
  - fallback fraction: `0.9958`
- `1.4e-05`
  - fallback fraction: `1.0000`
  - learned fraction: `0.0`

Interpretation markers from the parsed summary:
- last corrected time with fallback fraction below `50%`: `1e-05`
- first corrected time with fallback fraction above `95%`: `1.1e-05`
- first corrected time with all active cells on fallback: `1.4e-05`

So the corrected hybrid branch has a **clear phase transition** between `1e-05` and `1.1e-05`.

## Comparison to supervised hybrid branch

The supervised branch already reached near-total fallback much earlier:
- supervised first time above `95%` fallback: `5e-06`

By contrast:
- corrected first time above `95%` fallback: `1.1e-05`

That means the corrected hybrid branch roughly doubles the useful learned-dominant horizon relative to supervised in this Burke smoke setting.

## What changes at the collapse point

Before collapse, corrected fallback is a mixed regime with both:
- HP-failure fallback
- guard-only fallback

Examples:
- `1e-05`
  - `hp_failure_fraction_active = 0.1081`
  - `guard_only_fraction_active = 0.2000`

At collapse onset:
- `1.1e-05`
  - `hp_failure_fraction_active = 0.5394`
  - `guard_only_fraction_active = 0.4111`
- `1.2e-05`
  - `hp_failure_fraction_active = 0.9319`
  - `guard_only_fraction_active = 0.0433`
- `1.4e-05`
  - `hp_failure_fraction_active = 0.9853`

So the late-time breakdown is not just the guard being conservative. It becomes predominantly a **true HP-failure regime**.

## Temperature interpretation

Even during the late degraded regime, solver temperature extrema remain bounded rather than catastrophically diverging:
- `1e-05`: `370.907, 2428.61`
- `1.4e-05`: `499.35, 2420.75`
- `2e-05`: `337.389, 2370.15`

This confirms the hybrid policy is doing its stabilization job. But it also shows that stabilization alone is not enough: after `~1.1e-05`, the learned branch has mostly stopped being useful because fallback is carrying almost all active cells.

## Updated interpretation

The corrected Burke self-rollout branch with hybrid fallback is now best understood as:
- **clearly better than supervised under guarded deployment**
- **meaningfully learned-dominant through `1e-05`**
- **not yet a sustained long-horizon learned chemistry replacement**, because it transitions into near-total fallback after that point

## Most useful next step

The next useful diagnosis is no longer “does hybrid fallback work?” It does.

The next question is:
- **what changes in the CFD state around `1.1e-05` that turns the corrected branch from ~70% learned usage into near-total HP failure?**

The most useful next concrete step is therefore to compare written fields around:
- `1e-05` (still mostly learned)
- `1.1e-05` / `1.2e-05` (collapse onset)

with a targeted state-distribution and HP-risk analysis, instead of continuing blind horizon extension.
