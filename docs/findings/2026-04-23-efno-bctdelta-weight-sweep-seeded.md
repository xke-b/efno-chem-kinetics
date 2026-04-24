# Seeded weight sweep on the best current EFNO MLP branch: stronger species weighting helps a little, but does not erase the baseline gap

_Date: 2026-04-23_

## Why this was the next step

After removing the main conservation-design failure modes, the cleanest remaining question was:

> can the current best EFNO-style MLP branch close more of the gap to the supervised baseline just by rebalancing temperature vs species data loss?

This matters because earlier weight sweeps were run before the conservation redesign work, so their conclusions were partly confounded by a degraded EFNO objective.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_efno_bctdelta_weight_sweep_seeded.py`

Artifact:
- `/root/workspace/artifacts/experiments/h2_efno_bctdelta_weight_sweep_seeded/summary.json`

Common setup:
- H2 longprobe holdout split
- `MLP [64,64]`
- `25` epochs
- seeds: `0,1,2`
- common EFNO-style settings:
  - `target_mode = "temperature_species"`
  - `species_data_space = "bct_delta"`
  - `lambda_data = 1.0`
  - `lambda_elements = 0.0`
  - `lambda_mass = 0.0`

Cases:
1. `tempw_1p0_speciesw_1p0`
2. `tempw_0p1_speciesw_2p0`
3. `tempw_0p05_speciesw_2p0`
4. `tempw_0p1_speciesw_4p0`

## Aggregated results

| case | one-step species MAE mean | one-step temp MAE mean (K) | one-step element-mass MAE mean | rollout species MAE @1000 mean | rollout temp MAE @1000 mean (K) |
|---|---:|---:|---:|---:|---:|
| `tempw_0p1_speciesw_4p0` | `1.12e-04` | `1.43e-01` | `1.61e-04` | `9.90e-02` | `1.90e+03` |
| `tempw_0p05_speciesw_2p0` | `1.12e-04` | `1.43e-01` | `1.62e-04` | `9.90e-02` | `1.90e+03` |
| `tempw_0p1_speciesw_2p0` | `1.16e-04` | `1.43e-01` | `1.69e-04` | `1.00e-01` | `1.97e+03` |
| `tempw_1p0_speciesw_1p0` | `1.20e-04` | `1.43e-01` | `1.81e-04` | `1.43e-01` | `3.02e+03` |

## What this teaches us

### 1. Stronger species weighting helps, but only a little
The best one-step species mean improved from:
- `1.20e-04` for `tempw_1p0_speciesw_1p0`
- to `1.12e-04` for the stronger-species settings

That is real but modest.

### 2. The no-conservation EFNO branch is fairly insensitive in this region
Three of the four cases cluster very tightly:
- one-step temperature MAE stays around `1.43e-01 K`
- rollout species MAE stays around `9.9e-02` to `1.0e-01`
- rollout temperature MAE stays around `1.90e+03` to `1.97e+03 K`

So the current best EFNO branch is no longer wildly unstable to nearby weight choices. That is useful progress in itself.

### 3. Equal weighting is clearly worse than the stronger-species region
`tempw_1p0_speciesw_1p0` is the weakest case in this sweep on:
- one-step species
- one-step element-mass
- rollout species
- rollout temperature

So the earlier qualitative lesson still survives in the cleaner no-conservation branch:
- species should be weighted more strongly than temperature in the current EFNO mixed-target data term

### 4. But the supervised MLP baseline still remains clearly stronger on one-step species
Reference seeded supervised MLP mean from the architecture comparison:
- one-step species MAE: `6.23e-05`

Best EFNO case here:
- one-step species MAE: `1.12e-04`

So this sweep narrows the EFNO branch slightly, but it does not close the main fidelity gap.

## Most useful conclusion

This is good negative-but-stabilizing evidence.

It says:
- the current best EFNO MLP branch does benefit from stronger species weighting
- but the remaining supervised-vs-EFNO gap is not mainly due to small mistakes in temperature/species scalar weights

So the next bottleneck is probably more structural than scalar reweighting alone.

## Bottom line

The current strongest EFNO-style MLP settings are now in a tighter region:
- `tempw_0p1_speciesw_4p0`
- `tempw_0p05_speciesw_2p0`

They are slightly better than the previous no-conservation default, but not enough to overturn the main conclusion: the supervised MLP baseline still has materially better species fidelity. The next useful step should therefore move from scalar weight tuning toward a more structural change in how rollout behavior or multi-step consistency is trained.
