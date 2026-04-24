# DeepFlame H2 risk-guard packaging: the FT650 logistic risk-guard case can now be reproduced from the plain FT650 case with a reusable generator script

_Date: 2026-04-23_

## Why this was the next step

The risk-threshold sweep gave us two explicit deployment modes:
- retention-oriented: plain `650 K`
- safety-oriented: `650 K + risk-guard@0.5`

The next useful step was to stop treating the guarded case as a one-off hand-edited artifact and package the transformation into a reproducible helper.

## New script

- `/root/workspace/scripts/create_deepflame_hybrid_case.py`

Current supported use:
- start from a plain hybrid DeepFlame case
- copy it to a destination case
- set `frozenTemperature`
- patch `inference.py` with the FT650 logistic risk-guard logic and threshold

## Reproducibility check

I used the new script to generate:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_generated`

from:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`

with:
- `frozenTemperature = 650`
- `risk-threshold = 0.5`

Then I compared the generated files against the existing manually created case:
- `.../burke_corrected_self_rollout_predmainbct_ft650_riskguard/inference.py`
- `.../burke_corrected_self_rollout_predmainbct_ft650_riskguard/constant/CanteraTorchProperties`

Both matched exactly by SHA-256.

### Exact-match evidence
- `inference.py`: identical
- `constant/CanteraTorchProperties`: identical

So the risk-guard deployment case is now reproducible from a script instead of being only a hand-edited snapshot.

## Why this matters

This changes the status of the current guarded deployment prototype:
- before: useful but ad hoc
- now: reproducible and easier to regenerate with new thresholds or base cases

That is important because the project now has two meaningful H2 deployment modes worth preserving:
1. plain `650 K`
2. `650 K + logistic risk guard @ 0.5`

## Current limitation

The packaging script is intentionally narrow and only supports the currently validated FT650 logistic risk-guard pattern.

That is acceptable for now because the goal was to make the proven prototype reproducible before generalizing further.

## Most useful next step

The next concrete step should be to use this packaged path to test **transfer** of the current risk-guard mode beyond the corrected FT650 branch.

Best next options:
1. apply the packaged risk-guard transformation to the Burke supervised branch and compare behavior
2. or extend the generator to support the threshold sweep variants (`0.4/0.5/0.6`) directly from CLI and regenerate those cases from one base case

Given the current scientific question, option 1 is probably more valuable because it asks whether the current risk model and guarded deployment recipe are branch-specific or more broadly useful.
