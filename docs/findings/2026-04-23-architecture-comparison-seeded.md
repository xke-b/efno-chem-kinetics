# Seeded architecture comparison: the current FNO1d scaffold does not close the mixed-target gap and is much less rollout-stable than the MLP baseline

_Date: 2026-04-23_

## Why this was the next step

After removing the main self-inflicted EFNO conservation issues, the next unresolved question was whether the remaining gap is mostly about **backbone choice** rather than loss design.

So I compared the current MLP baseline against the provisional `fno1d` scaffold under the same fixed-seed H2 temp+species benchmark.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_architecture_comparison_seeded.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_architecture_comparison_seeded/summary.json`

Common setup:
- H2 longprobe holdout split
- `25` epochs
- seeds: `0,1,2`

Cases:
1. `supervised_mlp`
2. `supervised_fno1d`
3. `efno_bctdelta_noconserve_mlp`
4. `efno_bctdelta_noconserve_fno1d`

Model configs:
- MLP: `[64,64]`
- FNO1d: `width=32`, `modes=8`, `n_layers=4`

## Aggregated results

| case | one-step species MAE mean | one-step temp MAE mean (K) | one-step element-mass MAE mean | rollout species MAE @1000 mean | rollout temp MAE @1000 mean (K) |
|---|---:|---:|---:|---:|---:|
| `supervised_mlp` | `6.23e-05` | `1.75e-01` | `1.23e-04` | `2.78e-01` | `1.49e+03` |
| `supervised_fno1d` | `7.72e-05` | `2.18e-01` | `1.53e-04` | `6.16e-01` | `4.54e+04` |
| `efno_bctdelta_noconserve_mlp` | `1.16e-04` | `1.43e-01` | `1.69e-04` | `1.00e-01` | `1.97e+03` |
| `efno_bctdelta_noconserve_fno1d` | `1.74e-04` | `1.01e-01` | `3.16e-04` | `2.25e-01` | `3.01e+04` |

## What this teaches us

### 1. The current FNO1d scaffold is not the architecture rescue for this benchmark
For both trainers, the current `fno1d` model is worse than the MLP on species and rollout stability.

That means the remaining gap is not simply “use an operator backbone and performance will improve.”

### 2. The FNO scaffold still shows a real temperature signal
The strongest temperature number in the comparison came from:
- `efno_bctdelta_noconserve_fno1d`
  - one-step temperature MAE mean: `1.01e-01 K`

So the FNO scaffold is not useless. It can fit temperature aggressively.

But that gain comes with worse species fidelity and much worse rollout behavior.

### 3. Rollout stability is the clearest failure for the current FNO path
The most damaging numbers are rollout temperature:
- `supervised_fno1d`: `4.54e+04 K`
- `efno_bctdelta_noconserve_fno1d`: `3.01e+04 K`

These are far worse than the corresponding MLP cases.

So the present `fno1d` scaffold is not yet credible as the first offline operator baseline for this thermochemical benchmark.

### 4. The best current EFNO branch is still the no-conservation MLP branch
Among the EFNO-style cases here, the better branch remains:
- `efno_bctdelta_noconserve_mlp`

It still lags the supervised MLP on one-step species MAE, but it is much more stable than the FNO version and keeps the earlier temperature advantage.

## Most useful conclusion

This is useful negative evidence.

It says the current research bottleneck is **not** that EFNO-style merely needs the provisional `fno1d` scaffold to succeed. On this benchmark, the current FNO scaffold makes the tradeoff worse, not better.

## Bottom line

The most useful working baseline hierarchy is now:
1. `supervised_mlp` as the strongest overall offline thermochemical baseline
2. `efno_bctdelta_noconserve_mlp` as the strongest current EFNO-style branch
3. treat the present `fno1d` scaffold as an enabling prototype, not a competitive mixed-target baseline

This narrows the next step: either improve the MLP-based EFNO-style objective further, or replace the current `fno1d` scaffold with a more standard/operator-faithful backend before drawing architecture-level conclusions.
