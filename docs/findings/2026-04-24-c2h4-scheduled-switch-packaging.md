# C2H4 scheduled-switch packaging: the manual late-horizon switch can now be reproduced as a reusable case generator

_Date: 2026-04-24_

## Why this was the next step

The switch-time sweep showed that a late staged deployment is more promising than running the late-enriched model from the beginning, and that `4.5e-6` is the strongest tested switch point so far.

The next useful step was therefore not another manual continuation edit, but packaging that workflow into a reproducible operator-facing artifact.

## What I built

### New generator
- `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`

It automates the staged-switch workflow by:
- copying a completed source case
- swapping in a new inference bundle
- setting `startFrom startTime`
- setting `startTime = <switch time>`
- setting `endTime`
- removing later written times so the continuation is reproducible
- writing metadata for the generated switch case

## What I validated

I used the generator to reproduce the current best manual switch setup:
- source case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_fno_batched_full`
- switch bundle:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke_deepflame_bundle/`
- switch time:
  - `4.5e-6`
- generated case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_then_gentle_curriculum_from_4.5e-6_generated`

Generated metadata:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_then_gentle_curriculum_from_4.5e-6_generated/scheduled_switch_metadata.json`

## Reproduction result

The generated case runs cleanly from `4.5e-6` to `5e-6`.

Observed late active-set counts match the earlier manual `4.5e-6` switch case:
- `4.6e-06`: `40560`
- `4.7e-06`: `41173`
- `4.8e-06`: `41836`
- `4.9e-06`: `42672`
- `5e-06`: `43867`

So the switch-case packaging is now operationally reproducible rather than dependent on hand-edited continuation directories.

## Important implementation note

The first version of the generator had a bug in how it recognized the retained switch-time directory name (`4.5e-6` vs `4.5e-06`). That accidentally removed the restart-time directory and caused missing-field startup failures like:
- `cannot find file .../processor0/4.5e-06/p`

I fixed this by changing the cleanup logic to compare parsed floating-point time values rather than string spellings. That failure was useful because it hardened the generator against the mixed scientific-notation directory names that appear in OpenFOAM case trees.

## Why this matters

This is not yet a chemistry-fidelity solution, but it is meaningful deployment progress:
- it turns the best current staged-switch proof-of-concept into a reusable workflow
- it reduces the risk of manual continuation mistakes
- and it makes the next experiments about switch rules easier to run and compare systematically

## Current takeaway

The best current deployment-style C2H4 staged-switch mode can now be reproduced with a generator instead of by hand:
- early segment: pure `dp100`
- late segment: gentle curriculum
- current best tested manual switch time: `4.5e-6`

## Most useful next step

Use this generator as the base for a more systematic scheduled-switch study and then decide whether to:
- keep a fixed-time schedule as the deployment artifact
- or generalize it into a simple state-triggered switch rule.
