# DeepFlame H2 frozen-temperature ablation: raising the hybrid activation threshold from `510 K` to `600 K` dramatically delays the Burke corrected-branch collapse

_Date: 2026-04-23_

## Why this was the next step

The transition diagnosis suggested that the corrected Burke hybrid branch collapses when the learned model is applied to a growing population of cooler, near-threshold, more oxidizer-rich active cells.

That made the most direct next experiment a simple activation-region restriction:
- keep the same guarded hybrid policy
- but raise `frozenTemperature` from `510 K` to `600 K`

## Case and change

Copied case:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft600`

Modified file:
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft600/constant/CanteraTorchProperties`
  - `frozenTemperature 510;` → `frozenTemperature 600;`

Run horizon:
- `0` to `2e-05`

## Artifact

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft600_hybrid_2e-5_log_summary.json`
- comparison against the `510 K` baseline:
  - `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft600_comparison.json`

## Main result

This simple threshold change helps **a lot**.

### Collapse timing shifts substantially
Baseline `510 K` corrected branch:
- first time above `50%` fallback: `1.1e-05`
- first time above `95%` fallback: `1.1e-05`
- first time above `90%` HP-failure fraction: `1.2e-05`

`600 K` corrected branch:
- first time above `50%` fallback: `1.3e-05`
- first time above `95%` fallback: **never reached by `2e-05`**
- first time above `90%` HP-failure fraction: **never reached by `2e-05`**

So the activation-region hypothesis was correct: keeping the learned branch out of the cooler near-threshold regime materially improves deployment behavior.

## Head-to-head snapshots

### At `1e-05`
Baseline `510 K`:
- active cells: `10201`
- fallback fraction: `0.3081`
- HP-failure fraction: `0.1081`
- learned fraction: `0.6919`

`600 K`:
- active cells: `8708`
- fallback fraction: `0.0472`
- HP-failure fraction: `0.000115`
- learned fraction: `0.9528`

### At `1.1e-05`
Baseline `510 K`:
- fallback fraction: `0.9505`
- HP-failure fraction: `0.5394`
- learned fraction: `0.0495`

`600 K`:
- fallback fraction: `0.0343`
- HP-failure fraction: `0.0`
- learned fraction: `0.9657`

This is the clearest single result in the ablation.

### At `1.2e-05`
Baseline `510 K`:
- fallback fraction: `0.9751`
- HP-failure fraction: `0.9319`
- learned fraction: `0.0249`

`600 K`:
- fallback fraction: `0.4864`
- HP-failure fraction: `0.00926`
- learned fraction: `0.5136`

Even once the `600 K` case begins to degrade, it is still far healthier than the `510 K` branch in the same time window.

### At `1.4e-05`
Baseline `510 K`:
- fallback fraction: `1.0`
- HP-failure fraction: `0.9853`
- learned fraction: `0.0`

`600 K`:
- fallback fraction: `0.3151`
- HP-failure fraction: `0.0854`
- learned fraction: `0.6849`

This means the `600 K` gate preserves a substantial learned contribution well past the point where the `510 K` branch has already collapsed completely.

### At `2e-05`
Baseline `510 K`:
- fallback fraction: `0.9930`
- HP-failure fraction: `0.6534`
- learned fraction: `0.0070`

`600 K`:
- fallback fraction: `0.9192`
- HP-failure fraction: `0.4622`
- learned fraction: `0.0808`

The `600 K` case is still not a solved long-horizon deployment path, but it remains meaningfully better all the way to `2e-05`.

## Tradeoff

The improvement comes with a clear cost:
- fewer cells are allowed onto the learned path

For example:
- active cells at `1e-05`
  - `510 K`: `10201`
  - `600 K`: `8708`
- active cells at `2e-05`
  - `510 K`: `15347`
  - `600 K`: `9816`

So this is not “free.” It improves stability by shrinking the learned-chemistry domain.

That said, the trade currently looks favorable because the removed cells were exactly the ones implicated by the transition diagnosis.

## Interpretation

This ablation provides direct deployment-side evidence that:
- the late corrected-branch collapse was strongly tied to the low-temperature activation band near the original `510 K` threshold
- a simple state-region restriction can substantially delay or reduce the collapse
- the next practical design space should focus on **state-aware gating**, not only model retraining

## Updated conclusion

The best current deployment-facing H2 prototype is now:
- **corrected Burke hybrid fallback with a stricter activation threshold than `510 K`**

At least within the first simple guard ablation, `600 K` is clearly better than `510 K`.

## Most useful next step

The next high-value step is to map the tradeoff curve rather than stop at one point:
1. test one or two nearby thresholds such as `550 K` and `650 K`
2. compare:
   - learned fraction over time
   - fallback fraction over time
   - HP-failure fraction over time
   - cumulative learned coverage
3. decide whether a single higher `frozenTemperature` is enough, or whether a composition-aware guard is still needed

This experiment shifts the project from diagnosis to an actual deployment-control knob that demonstrably improves solver behavior.
