# DeepFlame H2 FT650 + O2 guard ablation: a simple oxidizer-rich near-threshold current-state guard helps early and mid-horizon behavior, but still collapses to full fallback by `2e-05`

_Date: 2026-04-23_

## Why this was the next step

The temperature-threshold sweep identified `650 K` as the best current single-threshold default for long-horizon guarded deployment. The next natural step was to add one lightweight composition-aware restriction on top of that threshold.

I implemented a simple current-state guard in the copied `650 K` case:
- if `current_T < 900 K`
- and current `O2 > 0.10`
- then skip the learned update and immediately use the CVODE fallback for that cell

This was intended to keep the learned branch out of the oxidizer-rich near-threshold region implicated by the transition diagnosis.

## Case and code

Case:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_o2guard`

Modified file:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_o2guard/inference.py`

New local guard parameters:
- `CURRENT_STATE_GUARD_T_MAX = 900.0`
- `CURRENT_STATE_GUARD_O2_MIN = 0.10`

I also updated the reusable parser so it can record the new `state_guard` count:
- `/root/workspace/scripts/parse_deepflame_hybrid_log.py`

## Artifact
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_o2guard_hybrid_2e-5_log_summary.json`
- comparison against plain `650 K`:
  - `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_o2guard_comparison.json`

## Main result

This guard is **partially helpful but not sufficient**.

It improves several early and mid-horizon metrics, but it does **not** improve the final `2e-05` outcome. In fact, by `2e-05` the guarded case has transitioned to full fallback.

That is a useful failure: it means the remaining bad regime is not captured adequately by this simple one-band O2 guard.

## Early and mid-horizon improvements

### At `1e-05`
Plain `650 K`:
- learned fraction: `0.8983`
- fallback fraction: `0.1017`

`650 K + O2 guard`:
- learned fraction: `0.9451`
- fallback fraction: `0.0549`
- state-guard fraction: `0.0306`

### At `1.2e-05`
Plain `650 K`:
- learned fraction: `0.5313`
- fallback fraction: `0.4687`
- HP-failure fraction: `0.0100`

`650 K + O2 guard`:
- learned fraction: `0.6592`
- fallback fraction: `0.3408`
- HP-failure fraction: `0.0`
- state-guard fraction: `0.0304`

### At `1.4e-05`
Plain `650 K`:
- learned fraction: `0.4451`
- fallback fraction: `0.5549`
- HP-failure fraction: `0.0874`

`650 K + O2 guard`:
- learned fraction: `0.5682`
- fallback fraction: `0.4318`
- HP-failure fraction: `0.0`
- state-guard fraction: `0.0292`

### At `1.6e-05`
Plain `650 K`:
- learned fraction: `0.1341`
- fallback fraction: `0.8659`
- HP-failure fraction: `0.3273`

`650 K + O2 guard`:
- learned fraction: `0.3838`
- fallback fraction: `0.6162`
- HP-failure fraction: `0.2796`
- state-guard fraction: `0.0302`

So up to around `1.6e-05`, this simple composition-aware guard is clearly beneficial.

## But it fails late

### At `2e-05`
Plain `650 K`:
- learned fraction: `0.2944`
- fallback fraction: `0.7056`
- HP-failure fraction: `0.3530`
- cumulative fallback fraction: `0.3610`

`650 K + O2 guard`:
- learned fraction: `0.0`
- fallback fraction: `1.0`
- HP-failure fraction: `0.4010`
- cumulative fallback fraction: `0.3579`
- state-guard fraction: `0.0447`

So despite a slightly lower cumulative fallback fraction, the final state is worse in the most important practical sense: by `2e-05`, the learned branch is gone.

## Interpretation

This experiment is still valuable because it separates two facts:

1. **Composition-aware gating is directionally useful**
   - the guard improves behavior substantially through much of the run

2. **This particular guard is too crude**
   - a single `T < 900 K` and `O2 > 0.10` rule does not preserve long-horizon learned usefulness
   - only about `3–4.5%` of active cells are directly state-guarded, so the remaining collapse is caused by a broader set of problematic states than this rule captures

In other words, the late failure mechanism is more complex than just “high-O2 near-threshold cells.”

## Updated conclusion

The best current single-threshold default remains:
- **`frozenTemperature = 650 K`**

And this new ablation adds an important nuance:
- composition-aware gating is promising
- but the first simple O2-based guard is **not yet a better default** than plain `650 K`

## Most useful next step

The next concrete step should not be more ad hoc hand-tuning of one rule at a time.

The most useful next move is to build a **state-conditioned failure map** for the `650 K` case, for example fallback / HP-failure rates binned by:
- current `T`
- current `O2`
- possibly one product/radical measure such as `H2O` or `OH`

That would let us design the next guard from measured failure regions rather than intuition alone.
