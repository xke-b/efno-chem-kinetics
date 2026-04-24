# DeepFlame H2 FT650 risk-threshold sweep: the logistic risk guard is robust, but `0.5` remains the best balance among `0.4/0.5/0.6`

_Date: 2026-04-23_

## Why this was the next step

The first risk-guard prototype at threshold `0.5` was the best guard attempted so far, but it still traded away some final learned retention relative to plain `650 K`.

The next logical step was therefore not a new guard family, but a small threshold sweep.

## Cases
- plain baseline: `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`
- risk guard `0.4`:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_t04`
- risk guard `0.5`:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard`
- risk guard `0.6`:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_t06`

## Artifacts
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_riskguard_threshold_sweep.json`

## Main result

The risk-guard family is fairly stable, but among the tested thresholds:
- **`0.5` remains the best overall balance**

### End-of-run comparison at `2e-05`
Plain `650 K`:
- learned fraction: `0.2944`
- HP-failure fraction: `0.3530`
- cumulative fallback fraction: `0.3610`

Risk guard `0.4`:
- learned fraction: `0.2274`
- HP-failure fraction: `0.0104`
- cumulative fallback fraction: `0.3835`
- state-guard fraction: `0.3078`

Risk guard `0.5`:
- learned fraction: `0.2411`
- HP-failure fraction: `0.0223`
- cumulative fallback fraction: `0.3806`
- state-guard fraction: `0.2998`

Risk guard `0.6`:
- learned fraction: `0.2271`
- HP-failure fraction: `0.0388`
- cumulative fallback fraction: `0.3883`
- state-guard fraction: `0.2824`

So within the risk-guard family:
- `0.4` is safest but most conservative
- `0.6` gives back more HP failure than `0.5` without improving final learned fraction
- `0.5` is the strongest compromise

## Mid-horizon behavior

### At `1.4e-05`
Learned fraction:
- plain `650 K`: `0.4451`
- risk `0.4`: `0.4346`
- risk `0.5`: `0.4407`
- risk `0.6`: `0.4386`

HP-failure fraction:
- plain `650 K`: `0.0874`
- risk `0.4`: `0.0049`
- risk `0.5`: `0.0091`
- risk `0.6`: `0.0116`

This is the attractive part of the risk-guard family: mid-horizon learned fraction stays close to the plain `650 K` case while HP-failure incidence drops by nearly an order of magnitude.

### At `1.6e-05`
Learned fraction:
- plain `650 K`: `0.1341`
- risk `0.4`: `0.3064`
- risk `0.5`: `0.2984`
- risk `0.6`: `0.2002`

HP-failure fraction:
- plain `650 K`: `0.3273`
- risk `0.4`: `0.0078`
- risk `0.5`: `0.0181`
- risk `0.6`: `0.0339`

Again, all three risk thresholds are much better than plain `650 K` at this time, but `0.5` still looks like the best overall balance.

## Interpretation

The sweep clarifies three things:

1. **The logistic risk model is genuinely useful**
   - all three thresholds greatly reduce HP failures compared with plain `650 K`

2. **The risk-threshold family is fairly robust**
   - performance does not collapse wildly when moving from `0.4` to `0.6`

3. **Threshold `0.5` is still the best local operating point tested so far**
   - it preserves more final learned fraction than `0.4`
   - and yields lower HP-failure incidence and lower cumulative fallback than `0.6`

## Updated conclusion

The current best guarded prototype is now:
- **FT650 + logistic risk guard at threshold `0.5`**

But the plain `650 K` case still remains the best option if the single most important metric is **final learned fraction at `2e-05`**.

So we now have a clean tradeoff:
- **plain `650 K`**: best learned retention by end of run
- **FT650 + risk guard @ `0.5`**: best current safety-oriented guarded policy

## Most useful next step

The next high-value step is no longer local guard tuning.

The most useful next step should be to turn this into a reusable artifact rather than a one-off case patch, for example:
1. extract the risk-guard logic into a reusable case-side helper or generator
2. document the two recommended deployment modes explicitly:
   - retention-oriented: plain `650 K`
   - safety-oriented: `650 K` + risk guard `0.5`
3. if we want one more experiment, evaluate whether the same risk model transfers at all to the supervised branch or another nearby case

At this point, the main scientific uncertainty has shifted from “what guard family should we try?” to “which deployment objective do we want to optimize for?”
