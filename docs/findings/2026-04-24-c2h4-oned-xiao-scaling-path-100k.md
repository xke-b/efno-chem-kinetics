# C2H4 oneD Xiao-style scaling path: the solver-native augmentation + chemistry-label pipeline now reaches `100k` labeled states cleanly, and the measured throughput makes million-scale data collection practical

_Date: 2026-04-24_

## Why this was the next step

After the first GPU validation-aware promotion run, the remaining question was no longer whether the current C2H4 models are under-trained in the abstract, but whether the **right data path** can be scaled meaningfully.

The Xiao et al. paper reports approximately `8,000,000` valid perturbed states after filtering. Our current C2H4 oneD-backed path had only been exercised at smoke scale:
- `20,000` current states
- `20,000` labeled pairs

So the next concrete step was to test whether the **DeepFlame oneD + Xiao-style augmentation + one-step chemistry labeling** path is operationally scalable, rather than merely conceptually plausible.

## New scaling utility

I added a chunked labeling script:
- `/root/workspace/scripts/label_c2h4_current_states_with_cantera.py`

What it does:
- accepts current-state datasets of shape `N x (2 + n_species)`
- advances each state by one chemistry step with Cantera
- writes paired outputs of shape `N x 2*(2+n_species)`
- uses chunked `.npy` memmap output rather than holding all labeled rows in RAM
- records per-chunk timings and overall throughput

This turns the oneD/Xiao path into a practical large-dataset workflow rather than a smoke-only manual step.

## Smoke validation of the chunked labeler

First, I verified the new chunked labeler on a small subset of the existing smoke current-state dataset.

Command outcome:
- `5,000` rows labeled successfully
- throughput: about `2.36e3 rows/s`

Output:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_chunked_smoke.npy`

This confirmed that the scale-ready path is consistent with the existing oneD current-state format.

## First medium-scale oneD Xiao-style build

### 1) Generate a larger current-state manifold

Generated:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_100k.npy`
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_100k.json`

Key generation stats:
- target states: `100,000`
- canonical oneD states: `50,500`
- interpolated states: `56,607`
- total perturbation attempts: `164,423`
- accepted states: `100,000`
- effective attempts per accepted state: about `1.64`
- dominant rejection reason: `hrr_ratio`

This matters because it shows the current Xiao-style constraints are not so restrictive that scaling becomes pathological.

### 2) Label the `100k` current states with chemistry

Generated:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.npy`
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.json`

Configuration:
- mechanism: `Wu24sp.yaml`
- reactor: `const_pressure`
- `dt = 1e-7`
- chunk size: `5000`

Measured result:
- labeled rows: `100,000`
- total time: `41.776 s`
- overall throughput: **`2393.7 rows/s`**
- chunk throughput was very stable, mostly around `2.37e3–2.44e3 rows/s`

## Practical scaling implications

Using the observed labeling throughput (`~2394 rows/s`), rough single-process estimates are:

- `100k` rows: `~42 s`  _(observed)_
- `500k` rows: `~3.5 min`
- `1M` rows: `~7.0 min`
- `8M` rows: `~55.7 min`

So purely from the **chemistry-labeling throughput** side, Xiao-scale data volume is not a fantasy on this machine.

### Storage implications

The labeled format is `N x 52` in `float64`.
Approximate storage:
- `100k` labeled rows: about `41.6 MB`
- `1M` labeled rows: about `416 MB`
- `8M` labeled rows: about `3.33 GB`

That is large, but still practical for staged experiments.

## What this result changes

This removes an important uncertainty.

Before this step, the oneD/Xiao scaling argument was mostly conceptual:
- the paper uses millions of states
- our solver-native oneD path looked promising
- but we had not shown that our pipeline could actually scale efficiently

After this step, the situation is clearer:

1. **The right C2H4 data path is now operational at medium scale.**
2. **The chemistry-labeling step is not the immediate bottleneck.**
3. **A `0.5M–1M` next-stage dataset is operationally justified now.**
4. **Even multi-million-scale data is plausible if the next medium-scale results are directionally positive.**

## Important caution

This does **not** yet prove that more oneD-backed data alone will solve deployment.

It only proves that:
- we now have a viable scale-ready solver-native data pipeline
- the earlier `20k/60k` sizes were more about workflow maturity than hard compute limits

The real scientific question remains whether increasing this oneD/Xiao-style chemistry dataset will improve the coupled C2H4 tradeoff:
- preserve or improve bulk `Qdot/T/p`
- while recovering the intermediate manifold
- without reintroducing earlier HP instability

## Current takeaway

The project can now move beyond small-data excuses on the oneD/Xiao side.

> We now have a working, chunked, solver-native C2H4 data path that reaches `100k` labeled states cleanly and fast enough that `0.5M–1M` is the right next-scale experiment.

## Most useful next step

The next justified move is:
1. build a **`0.5M` or `1M` labeled oneD/Xiao dataset**
2. train a promoted C2H4 model on it
3. compare against:
   - the current `60k` mixed baseline
   - CVODE at early and later horizons
   - deployment survival in the real DeepFlame case
