# DeepFlame H2 FT650 risk-model prototype: a tiny logistic HP-risk model is much better behaved than hand-written guards, but still does not beat plain FT650 on final learned retention

_Date: 2026-04-23_

## Why this was the next step

The joint hand-written guard confirmed that the failure structure is real but also showed that rectangular exclusion rules are too blunt.

So the next useful step was to build the smallest possible data-driven risk model from the measured HP-failure labels and test it as a case-side guard.

## New scripts and artifacts

### Scripts
- `/root/workspace/scripts/fit_deepflame_h2_hp_risk_model.py`

### Offline fit artifact
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_hp_risk_logistic_model.json`

### Case-side prototype
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard`

### Run summaries
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_riskguard_hybrid_2e-5_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_riskguard_comparison.json`

## Offline risk model

I fit a small logistic model on active-cell HP-failure labels from the `650 K` case at:
- `1.2e-05`
- `1.6e-05`
- `2e-05`

Features:
- current `T`
- current `p`
- current `O2`
- current `H2O`
- current `OH`

### Fit quality
- samples: `27426`
- mean failure fraction: `0.2643`
- rank-correlation-like score: `0.7475`

This is not a perfect classifier, but it is strong enough to justify a deployment-side prototype.

### Useful threshold region
At global threshold `0.5`:
- flagged fraction: `0.2534`
- recall: `0.8664`
- precision: `0.9035`
- specificity: `0.9667`

That looked like a reasonable first operating point, so I used `risk >= 0.5` as the case-side guard threshold.

## Case-side FT650 risk-guard prototype

I copied the `650 K` case and added a current-state risk guard to:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard/inference.py`

The guard computes the logistic risk score from the current state and routes the cell directly to CVODE fallback when:
- `risk_score >= 0.5`

## Main result

This data-driven guard is clearly better than the earlier hand-written guards, but it still does **not** beat plain `650 K` on the final learned fraction.

## Comparison at key times

### At `1e-05`
Plain `650 K`:
- learned fraction: `0.8983`
- fallback fraction: `0.1017`

Risk guard:
- learned fraction: `0.8963`
- fallback fraction: `0.1037`
- state-guard fraction: `0.0029`

So early behavior is essentially preserved.

### At `1.2e-05`
Plain `650 K`:
- learned fraction: `0.5313`
- HP-failure fraction: `0.0100`

Risk guard:
- learned fraction: `0.5308`
- HP-failure fraction: `0.00069`
- state-guard fraction: `0.2118`

This is very good: almost identical learned fraction, but much lower HP-failure incidence.

### At `1.4e-05`
Plain `650 K`:
- learned fraction: `0.4451`
- HP-failure fraction: `0.0874`

Risk guard:
- learned fraction: `0.4407`
- HP-failure fraction: `0.0091`
- state-guard fraction: `0.1356`

Again, much lower HP failure at nearly the same learned fraction.

### At `1.6e-05`
Plain `650 K`:
- learned fraction: `0.1341`
- HP-failure fraction: `0.3273`

Risk guard:
- learned fraction: `0.2984`
- HP-failure fraction: `0.0181`
- state-guard fraction: `0.2112`

This is the strongest part of the prototype result. It beats plain `650 K` decisively at this time.

### At `2e-05`
Plain `650 K`:
- learned fraction: `0.2944`
- fallback fraction: `0.7056`
- HP-failure fraction: `0.3530`
- cumulative fallback fraction: `0.3610`

Risk guard:
- learned fraction: `0.2411`
- fallback fraction: `0.7589`
- HP-failure fraction: `0.0223`
- cumulative fallback fraction: `0.3806`
- state-guard fraction: `0.2998`

Interpretation:
- the risk guard massively reduces HP-failure incidence
- but it pays for that by increasing fallback and reducing final learned retention
- unlike the hand-written O2-only guard, it still preserves substantial learned participation at `2e-05`
- unlike plain `650 K`, it is more conservative by the end of the run

## Guard-family interpretation

Relative to the earlier guard family:
- **simple O2 guard**: improved mid-horizon but collapsed completely by `2e-05`
- **joint hand-written guard**: reduced HP failures but over-fell back too aggressively
- **logistic risk guard**: best balanced guard tried so far

But the best current overall deployment default still depends on priority:
- **if learned retention at the end matters most**: plain `650 K` is still better
- **if minimizing HP-failure incidence matters more**: the logistic risk guard is more attractive

## Updated conclusion

This is the first case-side mitigation beyond hard threshold rules that looks genuinely promising.

The current picture is now:
- plain `650 K` remains the best current single-knob default for retained learned fraction
- the data-driven risk guard is the strongest guard prototype so far
- the remaining challenge is tuning the guard threshold so it preserves more learned fraction without giving back too much HP safety

## Most useful next step

The next concrete step should be a **small threshold sweep on the risk score**, not another new model.

The most useful nearby experiment is to test a few thresholds such as:
- `0.4`
- `0.5`
- `0.6`

That should tell us whether we can recover more final learned fraction than the current `0.5` prototype while still keeping HP-failure incidence far below the plain `650 K` case.
