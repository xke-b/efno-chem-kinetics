# DeepFlame H2 hybrid-fallback snapshot test: a simple HP-failure + `|ΔT|` guard can eliminate next-step HP failures in the Burke smoke states offline

_Date: 2026-04-23_

## Why this was the next step

The fallback-policy scout suggested that a practical first stabilization experiment should combine:
- fallback on outright HP failure
- fallback on large temperature-jump cells, e.g. `|ΔT| > 500 K`

The next concrete step was to test that idea on the actual written Burke smoke states.

## Added script

- `/root/workspace/scripts/simulate_deepflame_h2_hybrid_fallback_snapshot.py`

This is an offline snapshot experiment, not yet a solver patch.

For the written `2e-06` case state it does:
1. identify DNN-active cells (`T > 510 K`)
2. apply the exported DeepFlame-style learned species update
3. attempt HP reconstruction
4. flag cells if:
   - HP reconstruction fails, or
   - `|ΔT| > 500 K`, or
   - `T_next < 300 K`
5. replace flagged cells with a one-step Cantera reactor advance (`dt = 1e-6`) as a CVODE-like fallback
6. re-check HP reconstruction on the hybrid result

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_mlp_hybrid_snapshot.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hybrid_snapshot.json`

## Main result: the simple hybrid policy clears all next-step HP failures in this offline snapshot test

### Burke supervised

Baseline DNN-only next-step risk:
- active cells: `8670`
- HP failures: `927`
- success cells with `|ΔT| > 500 K`: `2797`
- success cells with `T_next < 300 K`: `124`

Hybrid fallback policy outcome:
- fallback cells: `3727`
- fallback fraction of active cells: `42.99%`
- rechecked HP failures after hybrid: `0`

Hybrid next-temperature summary:
- min: `371.78 K`
- max: `2653.47 K`
- mean: `2290.30 K`

Hybrid `ΔT` summary:
- min: `-499.14 K`
- max: `565.96 K`
- mean: `23.63 K`

### Burke corrected self-rollout

Baseline DNN-only next-step risk:
- active cells: `9161`
- HP failures: `1263`
- success cells with `|ΔT| > 500 K`: `2946`
- success cells with `T_next < 300 K`: `287`

Hybrid fallback policy outcome:
- fallback cells: `4209`
- fallback fraction of active cells: `45.94%`
- rechecked HP failures after hybrid: `0`

Hybrid next-temperature summary:
- min: `516.73 K`
- max: `2515.41 K`
- mean: `2154.23 K`

Hybrid `ΔT` summary:
- min: `-499.79 K`
- max: `157.65 K`
- mean: `-57.43 K`

## Main interpretation

### 1. The hybrid-fallback idea is viable enough to justify a solver-side prototype
This is the strongest evidence yet that a guarded hybrid deployment policy may rescue case-side use.

On the written Burke smoke states, the simple policy:
- fallback on HP failure
- fallback on `|ΔT| > 500 K`
- fallback on `T_next < 300 K`

reduced the rechecked next-step HP failure count to **zero** for both tested Burke candidates.

### 2. The fallback subset is large but still not all active cells
The policy flagged about:
- `43%` of active Burke-supervised cells
- `46%` of active Burke-corrected-self-rollout cells

That means more than half of the DNN-active cells still remained on the learned path in this snapshot test.

So this is not just “turn the model off everywhere.” It is a real hybrid regime.

### 3. The corrected Burke branch still looks attractive under the hybrid policy
After fallback, the corrected Burke branch has:
- no remaining HP failures in the snapshot recheck
- a healthier minimum next temperature (`516.7 K` vs `371.8 K` for supervised)
- a much smaller positive `ΔT` overshoot tail

So although the unguarded corrected branch had worse raw HP failure fraction than Burke supervised, it may still be a good candidate under a guarded deployment policy.

## Important caveat

This is an **offline snapshot approximation**, not a coupled solver run with fallback integrated into DeepFlame.

In particular:
- the fallback branch uses an offline one-step Cantera reactor advance as a CVODE-like substitute
- it is not yet wired into the actual solver loop
- it only checks the next-step reconstruction from the `2e-06` snapshot

So this is strong feasibility evidence, not final proof of stable coupled rollout.

## Bottom line

The most useful unfinished thread has now advanced from diagnosis to a plausible mitigation:

> A simple hybrid policy based on HP-failure detection plus a `|ΔT| > 500 K` guard can eliminate the next-step HP failures in the Burke smoke snapshots while still leaving a substantial fraction of active cells on the learned path.

## Most useful next step

The next concrete step should be to prototype this policy closer to the real solver path.

Best next move:
- implement or emulate a **cell-local hybrid fallback** for the Burke H2 case using:
  - learned update by default
  - CVODE fallback on HP failure
  - CVODE fallback on `|ΔT| > 500 K`
  - optional `T_next < 300 K` fallback

That is now the most direct experiment for testing whether the learned chemistry can survive in the real DeepFlame H2 case once the thermodynamically pathological subset is handled conservatively.
