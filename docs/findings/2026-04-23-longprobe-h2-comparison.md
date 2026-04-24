# Longer-horizon H2 probe changes the story: small smoke data were too easy, and current EFNO-style weighting is not yet better

_Date: 2026-04-23_

## Why this step mattered

The previous small comparison dataset (`64` initial conditions, `50` steps) turned out to be almost trivial: the one-step species changes were essentially zero. That made it a poor benchmark for deciding between trainer designs.

So the next concrete step was to create a more informative probe dataset and rerun the comparison.

## What was done

### 1. Diagnosed the earlier small comparison dataset
For `/root/workspace/data/h2_autoignition_smallcmp.npy`:
- mean species absolute delta per pair: `2.86e-12`
- max species absolute delta per pair: `6.89e-10`
- rows with any species delta > `1e-8`: `0 / 3200`

Conclusion:
- the earlier dataset was effectively a near-identity mapping for one-step prediction
- excellent scores there were not strong evidence of true chemical-learning quality

### 2. Built a longer-horizon probe dataset
Generated:
- `/root/workspace/data/h2_autoignition_longprobe.npy`
- `/root/workspace/data/h2_autoignition_longprobe.json`

Configuration:
- mechanism: `ES80_H2-7-16.yaml`
- `n_init = 16`
- `steps = 1000`
- `dt = 1e-7 s`
- constant-pressure reactor

Dataset shape:
- `(16000, 18)`

This probe is materially more informative:
- mean species abs delta per pair: `6.53e-05`
- max species abs delta per pair: `6.42e-03`
- rows with any species delta > `1e-5`: `11496 / 16000`
- rows with any species delta > `1e-3`: `970 / 16000`

Several trajectories showed substantial total evolution over 1000 steps.

## Trainer comparison run
Using the longer probe dataset, I trained two models with the same MLP backbone (`[64, 64]`) for 10 epochs:

1. `MLP + supervised_physics`
2. `MLP + efno_style`

Both were evaluated with the physical-consistency rollout evaluator.

## Key result

### One-step metrics
- `supervised_physics`:
  - one-step species MAE: `6.66e-05`
  - one-step element-mass MAE: `1.09e-04`
- `efno_style`:
  - one-step species MAE: `4.10e-04`
  - one-step element-mass MAE: `8.43e-04`

So on this longer, more informative dataset, the current `efno_style` trainer is **worse** than the baseline on one-step performance.

### Rollout behavior
- `supervised_physics` stays small for a long prefix of the rollout and only becomes large late in difficult regimes.
- `efno_style` accumulates much larger rollout error much earlier.
- The `efno_style` evaluation also reported `one_step_invalid_inverse_count = 40`, while the baseline had `0`.

## Interpretation

This is valuable negative information.

It means:
1. the earlier smoke success of `efno_style` was partly a benchmark artifact
2. the current weighting / conservation-loss balance in `efno_style` is **not yet tuned well enough** for this more meaningful H2 probe
3. benchmark difficulty matters a lot; trivial one-step datasets can produce misleading optimism

## Practical conclusion

The next best step is no longer just “scale up the same efno_style trainer.”
It is to:
1. add a proper train/test split with unseen initial conditions
2. sweep `lambda_data`, `lambda_elements`, and `lambda_mass`
3. inspect where inverse-BCT invalid states are produced
4. only then re-judge whether the EFNO-style loss path is genuinely helping

## Artifacts

- long probe baseline eval: `/root/workspace/artifacts/h2_autoignition_longprobe_mlp_supervised_physics_eval.json`
- long probe efno_style eval: `/root/workspace/artifacts/h2_autoignition_longprobe_mlp_efno_style_eval.json`

## Bottom line

A failed improvement attempt is still progress here: it revealed that our previous benchmark was too easy and that the current EFNO-style trainer needs more careful calibration before it can be treated as a real advance.
