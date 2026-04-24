# DeepFlame H2 risk-guard config packaging: the FT650 logistic guard coefficients are now externalized into a reusable model config consumed by the case generator

_Date: 2026-04-23_

## Why this was the next step

After the supervised-transfer result, the most useful unfinished thread was to make the current corrected-branch deployment pair easier to preserve and reuse.

The previous generator script still hardcoded the logistic risk-model coefficients directly inside the Python source. That was reproducible enough for one case, but not clean enough for durable reuse.

So I externalized the FT650 logistic risk model into a dedicated config artifact and updated the generator to consume that config.

## New config artifact

- `/root/workspace/artifacts/models/deepflame_h2_ft650_logistic_hp_risk_v1.json`

It records:
- model name and description
- frozen temperature
- default risk threshold
- feature names
- species indices used by the case-side risk computation
- feature normalization statistics
- logistic weights and bias
- provenance link back to the fit artifact

## Updated generator

- `/root/workspace/scripts/create_deepflame_hybrid_case.py`

Key update:
- it now accepts `--risk-config`
- if `--risk-threshold` is omitted, it uses the config’s `default_risk_threshold`
- it renders the patched `inference.py` from the external config rather than from source-hardcoded coefficients

So the current guarded deployment mode is now parameterized by a risk-model artifact rather than buried in the generator implementation.

## Reproducibility check

I regenerated the corrected FT650 risk-guard case using the external config:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_generated_from_config`

from:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`

Then I compared against the validated manual `ft650_riskguard` case.

Result:
- `inference.py`: exact match
- `constant/CanteraTorchProperties`: exact match

So the externalized config path preserves exact reproducibility for the current best safety-oriented prototype.

## Why this matters

This pushes the project one step further from ad hoc case hacking toward reusable deployment artifacts.

The H2 deployment pair is now easier to preserve as explicit objects:
1. plain FT650 base case
2. FT650 + risk-guard policy defined by:
   - a risk-model config JSON
   - a reusable case generator

That makes later transfer tests, threshold variants, or branch-specific guard updates easier to manage cleanly.

## Updated practical status

The corrected H2 deployment recommendation is now packaged as:
- **retention-oriented mode**: plain FT650
- **safety-oriented mode**: FT650 + logistic risk guard from `deepflame_h2_ft650_logistic_hp_risk_v1.json`

## Most useful next step

The next concrete step should likely be to document this deployment pair explicitly in one concise operator-facing note or README section, so the current recommendation is easy to apply without reconstructing it from many findings pages.

A secondary option would be to create a second config artifact if a future branch-specific risk model becomes justified, but the present evidence suggests staying focused on the corrected branch for now.
