# DeepFlame H2 frozen-temperature refinement: `625 K` improves mid-horizon behavior but collapses worse than `650 K` by `2e-05`

_Date: 2026-04-23_

## Why this was the next step

The `550/600/650 K` sweep showed a promising operating window around `600–650 K`, but the best point was still ambiguous:
- `600 K` looked strong at parts of the mid-horizon
- `650 K` looked strongest by `2e-05`

So the next minimal refinement was to test the midpoint:
- `625 K`

## Case
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft625`

Modified setting:
- `frozenTemperature 625;`

Run horizon:
- `0` to `2e-05`

## Artifact
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft625_hybrid_2e-5_log_summary.json`
- comparison against `600 K` and `650 K`:
  - `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft625_refinement_comparison.json`

## Main result

`625 K` is **not** the best current compromise.

It is better than `600 K` at some earlier and mid-horizon times, but it collapses more severely later and is clearly worse than `650 K` by `2e-05`.

## Key comparisons

### Collapse timing
First time above `50%` fallback:
- `600 K`: `1.3e-05`
- `625 K`: `1.3e-05`
- `650 K`: `1.4e-05`

First time above `80%` fallback:
- `600 K`: `1.7e-05`
- `625 K`: `1.5e-05`
- `650 K`: `1.5e-05`

First time above `95%` fallback:
- `600 K`: not reached by `2e-05`
- `625 K`: `1.6e-05`
- `650 K`: not reached by `2e-05`

So on collapse timing alone, `625 K` is already worse than both surrounding candidates on one important criterion.

## Early and mid-horizon behavior

### At `1e-05`
Learned fraction:
- `600 K`: `0.9528`
- `625 K`: `0.9639`
- `650 K`: `0.8983`

### At `1.2e-05`
Learned fraction:
- `600 K`: `0.5136`
- `625 K`: `0.5336`
- `650 K`: `0.5313`

### At `1.4e-05`
Learned fraction:
- `600 K`: `0.6849`
- `625 K`: `0.7797`
- `650 K`: `0.4451`

So `625 K` actually looks excellent through parts of the mid-horizon.

## But late-horizon behavior breaks badly

### At `1.6e-05`
Learned fraction:
- `600 K`: `0.2123`
- `625 K`: `0.0362`
- `650 K`: `0.1341`

### At `2e-05`
Learned fraction:
- `600 K`: `0.0808`
- `625 K`: `0.0000`
- `650 K`: `0.2944`

HP-failure fraction at `2e-05`:
- `600 K`: `0.4622`
- `625 K`: `0.7206`
- `650 K`: `0.3530`

Cumulative fallback fraction at `2e-05`:
- `600 K`: `0.3734`
- `625 K`: `0.4243`
- `650 K`: `0.3610`

This is decisive: `625 K` does not interpolate smoothly between `600 K` and `650 K`; it creates a worse late-time outcome than `650 K`, and even worse than `600 K` on the end-of-run learned fraction.

## Interpretation

The sweep is now telling a more nuanced story than “pick the midpoint.”

- `600 K` gives the strongest behavior in some mid-horizon windows
- `625 K` also looks strong in the mid-horizon, even stronger at `1.4e-05`
- but `625 K` then collapses sharply
- `650 K` gives the best retained learned fraction and lowest cumulative fallback by `2e-05`

So the current tradeoff frontier is no longer ambiguous:
- if we care about **end-of-horizon survivability**, `650 K` is the best current single-threshold setting
- if we care more about **some earlier-horizon learned coverage**, `600 K` remains a credible alternative

## Updated conclusion

`625 K` is useful information because it rules out the naive idea that the best point must lie between `600 K` and `650 K`.

The strongest current single-knob candidates are now:
- **`600 K`** for strong earlier/mid-horizon behavior
- **`650 K`** for the strongest long-horizon survival in the current sweep

Among those, **`650 K` is the best current default if the goal is to keep the learned branch meaningfully active out to `2e-05`.**

## Most useful next step

The next concrete step should likely stop refining pure temperature thresholds and instead combine the best current threshold with one more state-aware restriction.

Best candidate now:
1. take the `650 K` case as the current deployment default
2. add one lightweight composition-aware guard for oxidizer-rich near-threshold states
3. test whether that improves the remaining late-time collapse without shrinking learned coverage too aggressively

At this point, additional pure threshold interpolation looks lower-value than adding one extra physically motivated guard on top of the now-best threshold region.
