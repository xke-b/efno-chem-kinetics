# DeepFlame H2 frozen-temperature sweep: `600–650 K` gating clearly outperforms `510 K`, and `650 K` gives the strongest long-horizon learned fraction in the current sweep

_Date: 2026-04-23_

## Why this was the next step

After the `600 K` ablation worked well, the next useful question was whether that result was:
- a one-off lucky point, or
- part of a broader activation-threshold tradeoff curve.

So I extended the case-side sweep to two nearby thresholds:
- `550 K`
- `650 K`

using the same corrected Burke hybrid case and the same `2e-05` horizon.

## Cases
- baseline: `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct` (`510 K`)
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft550`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft600`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`

## Artifacts
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft550_hybrid_2e-5_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_hybrid_2e-5_log_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_frozen_temperature_sweep_comparison.json`

## Main sweep result

### Collapse timing improves monotonically as the activation threshold rises
First time above `50%` fallback:
- `510 K`: `1.1e-05`
- `550 K`: `1.2e-05`
- `600 K`: `1.3e-05`
- `650 K`: `1.4e-05`

First time above `95%` fallback:
- `510 K`: `1.1e-05`
- `550 K`: `1.4e-05`
- `600 K`: not reached by `2e-05`
- `650 K`: not reached by `2e-05`

First time above `90%` HP-failure fraction:
- `510 K`: `1.2e-05`
- `550 K`: `1.6e-05`
- `600 K`: not reached by `2e-05`
- `650 K`: not reached by `2e-05`

So the sweep strongly confirms the central diagnosis: **the low-temperature activation region was the main driver of collapse**.

## Long-horizon comparison

### Learned fraction at `2e-05`
- `510 K`: `0.0070`
- `550 K`: `0.0000`
- `600 K`: `0.0808`
- `650 K`: `0.2944`

### Cumulative fallback fraction of active cells at `2e-05`
- `510 K`: `0.6864`
- `550 K`: `0.5156`
- `600 K`: `0.3734`
- `650 K`: `0.3610`

So among the thresholds tested so far:
- `550 K` is better than baseline but still collapses hard by the end
- `600 K` is a strong improvement
- `650 K` is the best current long-horizon point in this sweep

## Mid-horizon snapshots

### At `1e-05`
Learned fraction:
- `510 K`: `0.6919`
- `550 K`: `0.7875`
- `600 K`: `0.9528`
- `650 K`: `0.8983`

Interesting nuance:
- `600 K` is better than `650 K` at `1e-05`
- but `650 K` becomes better later in the run

### At `1.2e-05`
Learned fraction:
- `510 K`: `0.0249`
- `550 K`: `0.4947`
- `600 K`: `0.5136`
- `650 K`: `0.5313`

### At `1.4e-05`
Learned fraction:
- `510 K`: `0.0000`
- `550 K`: `0.0092`
- `600 K`: `0.6849`
- `650 K`: `0.4451`

Here `600 K` is actually better than `650 K`.

### At `2e-05`
Learned fraction:
- `510 K`: `0.0070`
- `550 K`: `0.0000`
- `600 K`: `0.0808`
- `650 K`: `0.2944`

So the current sweep shows a non-monotone short/mid-horizon tradeoff:
- `600 K` looks strongest around `1e-05` to `1.4e-05`
- `650 K` looks strongest by `2e-05`

## Coverage tradeoff

Higher thresholds reduce active learned-chemistry coverage.

Active cells at `1e-05`:
- `510 K`: `10201`
- `550 K`: `8970`
- `600 K`: `8708`
- `650 K`: `8586`

Active cells at `2e-05`:
- `510 K`: `15347`
- `550 K`: `11281`
- `600 K`: `9816`
- `650 K`: `9514`

So higher thresholds gain stability by shrinking the active DNN domain.

## Important practical interpretation

The sweep does **not** simply say “higher is always better.”

Instead, the current evidence suggests:
- `550 K` is not high enough to avoid late collapse robustly
- `600 K` is a strong balanced point in the current sweep
- `650 K` sacrifices a bit more coverage but gives the best long-horizon learned fraction by `2e-05`

That means the best threshold depends on what we value most:
- **earlier-horizon learned usage:** `600 K`
- **longer-horizon retained learned fraction:** `650 K`

## Updated conclusion

The project now has a concrete, working deployment-control family:
- frozen-temperature gating is not just helpful, it is one of the strongest current practical levers
- the best region in the present sweep is clearly above `550 K`
- the current promising operating window is roughly **`600–650 K`**

## Most useful next step

The next concrete step should be to refine within that window or combine it with one extra state-aware guard.

Best next options:
1. test an intermediate point such as `625 K`
2. or keep `600 K` / `650 K` and add one lightweight composition-aware guard for oxidizer-rich near-threshold cells

Given the current results, `625 K` is probably the simplest next experiment if we want a cleaner single-knob operating point.
