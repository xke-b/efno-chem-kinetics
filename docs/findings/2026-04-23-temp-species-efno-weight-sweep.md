# Small EFNO-style mixed-target weight sweep: temperature weighting helps rollout, but supervised baseline still wins overall

_Date: 2026-04-23_

## Why this was the next step

The previous temperature+species comparison suggested that the current `efno_style` trainer had a mixed-target loss-design problem:
- one-step temperature looked decent
- species fidelity was poor
- rollout temperature was catastrophically unstable

So the next concrete step was to add explicit weighting between:
- the temperature component of the data loss
- the species component of the data loss

and then run a small holdout sweep.

## Code change

Updated:
- `/opt/src/DFODE-kit/dfode_kit/training/efno_style.py`
- `/opt/src/DFODE-kit/tests/test_efno_style_trainer.py`

New trainer params now supported:
- `temperature_loss_weight`
- `species_loss_weight`

This only changes the **data-loss decomposition** for mixed targets; the mass and element losses remain unchanged.

## Sweep script and artifacts

Script:
- `/root/workspace/scripts/run_h2_temp_species_efno_weight_sweep.py`

Outputs:
- `/root/workspace/artifacts/experiments/h2_temp_species_efno_weight_sweep/summary.json`
- per-case eval JSONs under the same directory

## Sweep cases

All runs used:
- H2 longprobe holdout split
- `MLP [64,64]`
- `efno_style`
- `target_mode = temperature_species`
- `lambda_data = lambda_elements = lambda_mass = 1.0`
- `10` epochs

Cases:
1. `tempw_1p0_speciesw_1p0`
2. `tempw_0p1_speciesw_1p0`
3. `tempw_0p01_speciesw_1p0`
4. `tempw_0p1_speciesw_2p0`

## Main results

### Ranking by one-step species MAE

| case | one-step species MAE | one-step temp MAE (K) | rollout species MAE @1000 | rollout temp MAE @1000 (K) |
|---|---:|---:|---:|---:|
| `tempw_0p1_speciesw_2p0` | `2.65e-04` | `2.22e-01` | `8.40e-02` | `6.12e+01` |
| `tempw_1p0_speciesw_1p0` | `2.96e-04` | `1.83e-01` | `5.96e-02` | `2.15e+03` |
| `tempw_0p1_speciesw_1p0` | `3.46e-04` | `2.27e-01` | `4.09e-02` | `1.08e+03` |
| `tempw_0p01_speciesw_1p0` | `4.28e-04` | `2.16e-01` | `2.05e-01` | `2.89e+02` |

## What improved

### 1. Explicit temperature weighting clearly matters
This is the most important finding.

Compared with the earlier unweighted temperature+species EFNO-style run, the new weighted variants can reduce extreme rollout-temperature blow-up substantially.

A notable example:
- `tempw_0p1_speciesw_2p0`
  - rollout temperature MAE at horizon `1000`: about `6.12e+01 K`

That is still not ideal, but it is **far better** than the earlier catastrophic behavior.

### 2. Species-vs-temperature tradeoff is real
The sweep shows no single setting that is best on everything:
- `tempw_0p1_speciesw_2p0` gives the best one-step species MAE of the EFNO-style sweep
- `tempw_0p1_speciesw_1p0` gives the best rollout species MAE at horizon `1000`
- `tempw_1p0_speciesw_1p0` gives the best one-step temperature MAE
- `tempw_0p1_speciesw_2p0` gives by far the best rollout temperature stability

So the mixed-target objective is genuinely multi-objective.

## What did **not** improve enough

The EFNO-style sweep still does **not** beat the supervised baseline overall.

Reference supervised result from the earlier temp+species holdout comparison:
- one-step species MAE: `5.98e-05`
- one-step temperature MAE: `3.74e-01 K`
- rollout species MAE @1000: `6.96e-02`
- rollout temperature MAE @1000: `4.27e+02 K`

Interpretation:
- EFNO-style can now achieve **better one-step temperature** than supervised
- and some weighted variants achieve **better rollout temperature** than supervised
- but EFNO-style is still much worse on **one-step species accuracy**
- and does not yet provide a clearly superior overall tradeoff

## Most useful conclusion

This sweep changes the situation in an important way:
- before: the mixed-target EFNO-style loss looked simply broken
- now: it looks **tunable**, but still not good enough

That is real progress, because it narrows the next step to targeted loss-design work rather than abandoning the path outright.

## Best next technical step

The next useful experiment should probably combine:
1. **explicit temperature/species data weights**
2. **sweeps over `lambda_elements` and `lambda_mass`**
3. possibly **longer training** for the most promising settings

In particular, `tempw_0p1_speciesw_2p0` looks like the strongest next candidate for follow-up because it improved both one-step species error and rollout-temperature stability relative to the other EFNO-style settings.

## Bottom line

Adding explicit mixed-target data weights did not make EFNO-style training win, but it did turn an obviously unstable formulation into a more diagnosable and partially recoverable one. That is useful negative-but-constructive evidence.
