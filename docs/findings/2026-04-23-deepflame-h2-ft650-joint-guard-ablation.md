# DeepFlame H2 FT650 joint guard ablation: an evidence-grounded `(T, O2, H2O)` current-state guard lowers HP-failure incidence but over-falls back and is still worse than plain FT650 by the end of the run

_Date: 2026-04-23_

## Why this was the next step

The state-conditioned failure map showed that the late `650 K` failure region is broader than a simple `O2 > 0.10` rule. The risky region appeared concentrated in:
- moderate active temperatures
- moderate `O2` (`~0.02–0.10`)
- lower `H2O`

So the next useful step was to test a more evidence-grounded joint current-state guard.

## Case and implementation

Case:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_jointguard`

Modified file:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_jointguard/inference.py`

Current-state guard used:
- `650 K <= current_T <= 1600 K`
- `0.02 <= current_O2 <= 0.10`
- `current_H2O < 0.20`

Guarded cells are routed directly to CVODE fallback before the learned update.

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_jointguard_hybrid_2e-5_log_summary.json`
- comparison against plain `650 K` and the earlier simple O2 guard:
  - `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_guard_family_comparison.json`

## Main result

This joint guard is another **useful but not sufficient** intervention.

It reduces HP-failure fractions substantially at later times, but it also over-expands fallback and still ends the run in a worse learned-coverage regime than plain `650 K`.

## Comparison to plain `650 K`

### At `1.2e-05`
Plain `650 K`:
- learned fraction: `0.5313`
- fallback fraction: `0.4687`
- HP-failure fraction: `0.0100`

Joint guard:
- learned fraction: `0.4752`
- fallback fraction: `0.5248`
- HP-failure fraction: `0.00023`
- state-guard fraction: `0.0339`

This already shows the tradeoff clearly:
- much lower HP failure
- but too much extra fallback too early

### At `1.4e-05`
Plain `650 K`:
- learned fraction: `0.4451`
- fallback fraction: `0.5549`
- HP-failure fraction: `0.0874`

Joint guard:
- learned fraction: `0.3434`
- fallback fraction: `0.6566`
- HP-failure fraction: `0.0609`
- state-guard fraction: `0.0707`

### At `1.6e-05`
Plain `650 K`:
- learned fraction: `0.1341`
- fallback fraction: `0.8659`
- HP-failure fraction: `0.3273`

Joint guard:
- learned fraction: `0.1948`
- fallback fraction: `0.8052`
- HP-failure fraction: `0.2126`
- state-guard fraction: `0.0619`

So in the mid-late regime, the joint guard does reduce HP failure materially and can modestly improve learned fraction relative to plain `650 K`.

## End-of-run outcome

### At `2e-05`
Plain `650 K`:
- learned fraction: `0.2944`
- fallback fraction: `0.7056`
- HP-failure fraction: `0.3530`
- cumulative fallback fraction: `0.3610`

Simple O2 guard:
- learned fraction: `0.0`
- fallback fraction: `1.0`
- HP-failure fraction: `0.4010`
- cumulative fallback fraction: `0.3579`

Joint guard:
- learned fraction: `0.0656`
- fallback fraction: `0.9344`
- HP-failure fraction: `0.1749`
- cumulative fallback fraction: `0.4265`
- state-guard fraction: `0.0825`

Interpretation:
- the joint guard is much better than the simple O2-only guard in terms of preserving any learned fraction at all
- it cuts the end-time HP-failure fraction roughly in half versus plain `650 K`
- but it still loses badly to plain `650 K` on retained learned coverage and cumulative fallback burden

## What this teaches us

This experiment adds two important pieces of evidence:

1. **The failure map was directionally correct**
   - targeting the moderate-`O2`, moderate-`T`, lower-`H2O` region does reduce HP-failure incidence

2. **A hard rule based on that region is still too blunt**
   - it removes too many cells from the learned path
   - especially earlier than necessary
   - and the cumulative fallback burden becomes worse than the plain `650 K` case

So the problem is not simply “identify the bad region and exclude it wholesale.”

## Updated conclusion

The best current deployment default is still:
- **plain `frozenTemperature = 650 K`**

The guard family comparison now looks like this:
- plain `650 K`: best long-horizon learned retention so far
- `650 K + simple O2 guard`: too weakly targeted, collapses fully by `2e-05`
- `650 K + joint guard`: better targeted and lowers HP-failure fraction, but still over-falls back and is worse than plain `650 K` on final learned usefulness

## Most useful next step

The next step should likely stop using hand-written rectangular guard rules.

The highest-value follow-up is to build a **small data-driven guard model or score**, for example:
- predict HP-failure risk from current `(T, O2, H2O)`
- then fallback only when the estimated risk is above a threshold

That would preserve the insight from the failure map without imposing a crude hard box in state space.
