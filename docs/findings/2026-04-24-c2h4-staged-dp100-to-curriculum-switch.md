# Staged C2H4 deployment switch (`dp100 -> gentle curriculum` at `4e-6`): regime-aware deployment looks more promising than a single full-start late-enriched model

_Date: 2026-04-24_

## Why this was the next step

The gentle early→late curriculum result showed a useful but frustrating pattern:
- it survived to `5e-6`
- but it was clearly worse than pure `dp100` on pressure spread, `Qdot`, and temperature drift

That suggested the next concrete question should move from training design to **deployment logic**:
- if late-enriched behavior is only useful late, can it be introduced *late* rather than forcing one model to absorb both regimes from `t=0`?

So I ran the simplest regime-aware deployment experiment:
1. run the pure `dp100` model through `4e-6`
2. switch to the gentle curriculum model for the final `4e-6 -> 5e-6` segment

This is not yet a fully automated runtime-conditioned bridge, but it is a concrete staged-deployment test of the idea.

## What I ran

### Staged switch case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_then_gentle_curriculum_from4e-6`

Construction:
- copied the completed pure `dp100` case run
- kept the written state at `4e-6`
- removed later written times
- swapped in the gentle curriculum bundle
- restarted from `startTime = 4e-6`
- continued to `5e-6`

Gentle curriculum bundle used after the switch:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke_deepflame_bundle/`

## Runtime result

The staged switch reaches `5e-6` cleanly.

At the late segment:
- no OOM line
- `solver.err` empty
- learned active-set counts increase from:
  - `4.1e-06`: `38331`
  - `4.4e-06`: `39752`
  - `4.7e-06`: `42260`
  - `4.9e-06`: `44736`
  - `5e-06`: `46069`

So the staged path is solver-usable and keeps meaningful learned participation after the switch.

## Main comparison at `5e-6`

Artifacts:
- staged case analysis:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_then_gentle_curriculum_from4e-6_fields_5e-06_vs_2e-06.json`
- comparison summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_vs_gentle_full_vs_staged_switch_5e-06.json`

### Pure `dp100` full run
- mean `Qdot`: `5.12e8`
- pressure max: `113365 Pa`
- mean `|ΔT|`: `3.28 K`

### Gentle curriculum from start
- mean `Qdot`: `1.20e9`
- pressure max: `146985 Pa`
- mean `|ΔT|`: `9.43 K`

### Staged switch (`dp100 -> gentle curriculum` at `4e-6`)
- mean `Qdot`: `7.93e8`
- pressure max: `119319 Pa`
- mean `|ΔT|`: `3.60 K`

## Interpretation of that comparison

This is a meaningful improvement over the full-start gentle curriculum.

Relative to the gentle curriculum from `t=0`, the staged switch:
- reduces mean `Qdot` materially
- narrows the pressure tail substantially
- keeps mean `|ΔT|` much closer to the pure `dp100` baseline

In fact, on these broad solver-facing metrics the staged switch sits much closer to the pure `dp100` baseline than to the full-start gentle curriculum.

That is exactly the pattern you would want to see if **regime-aware deployment** is more promising than forcing a single late-enriched model to cover the whole trajectory.

## Quality tradeoff

The staged switch does still give back some quality relative to pure `dp100`.

At `5e-6`, compared with pure `dp100`:
- mean `Qdot` rises from `5.12e8` to `7.93e8`
- pressure max rises from `113365 Pa` to `119319 Pa`
- mean `|ΔT|` rises slightly from `3.28 K` to `3.60 K`

So it is not a free improvement.

But compared with the full-start gentle curriculum, the staged switch looks much healthier.

## Species-level note

The staged switch still does **not** solve the missing-intermediate problem in a strong mean-field way.

At `5e-6`, the staged switch still has essentially collapsed means for:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`

So this is not yet evidence that a staged deployment switch fixes the chemistry-fidelity problem.

It **is** evidence that staged deployment can be a better way to incorporate a late-enriched model without paying the full quality penalty of running it from the beginning.

## Current takeaway

This is the strongest evidence so far for the deployment-logic path.

The updated picture is:
- pure `dp100` remains the best current single-model baseline
- full-start gentle curriculum reaches `5e-6` but degrades quality too much
- a staged switch from `dp100` to the gentle curriculum at `4e-6` reaches `5e-6` and stays much closer to the pure `dp100` baseline than the full-start gentle curriculum

So **regime-aware deployment looks more promising than asking one shared late-enriched model to cover the whole trajectory from `t=0`**.

## Most useful next step

The next useful step is to move from this manual staged-switch proof-of-concept toward a more systematic regime-aware deployment rule, for example:
- switching by written-time / continuation schedule
- or switching by a simple state trigger rather than by hand-edited continuation

That should improve understanding of whether late-regime specialization is genuinely useful once applied only where it belongs.
