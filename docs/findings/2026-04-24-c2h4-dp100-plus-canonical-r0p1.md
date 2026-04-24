# C2H4 `dp100 + canonical@0.1` test: a small calibrated canonical fraction improves over both the original `dp100` baseline and the larger uncapped `dp100` scale-up

_Date: 2026-04-24_

## Why this was the next step

The previous two results pointed in the same direction:
- the paper-inspired canonical augmentation path contains the missing intermediate-rich chemistry, but overshoots if treated as a replacement
- larger datasets matter, but scaling raw `dp100` alone moved the model into a different failure mode, including negative mean `Qdot`

So the most useful next step was to test the simplest calibrated mixture suggested by the coverage scout:
- keep the current best `dp100` case-pair baseline as the main dataset
- add only a **small canonical augmented fraction**
- start near the scout’s crude best point, around a canonical/case-pair weight ratio of `0.1`

## Dataset construction

Generated mixed dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p1.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p1.json`

Construction:
- base `dp100` rows: `50000`
- canonical augmented smoke rows per copy: `414`
- canonical copies: `12`
- effective canonical rows: `4968`
- effective canonical/case-pair ratio: `0.09936`
- total rows: `54968`

This is intentionally a first calibration test, not yet an optimized weighting scheme.

## Training and deployment artifacts

Runner:
- `/root/workspace/scripts/run_c2h4_casepair_dp100_plus_canonical_r0p1_fno_baseline.py`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p1_fno_smoke.pt`

DeepFlame export:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p1_fno_smoke_deepflame_bundle/`

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_canonical_r0p1_fno_batched_full`

Field artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_canonical_r0p1_fno_batched_full_fields_5e-06_vs_2e-06.json`

Cross-comparison artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_canonical_mix_vs_baselines_5e-06.json`

## Runtime result

The mixed model ran cleanly to `5e-6`:
- `solver.err` empty
- no OOM line
- learned active-set counts remained stable and ended at `34444`

## Main comparison at `5e-6`

### Original `dp100` (`50k` rows)
- mean `Qdot`: `5.118e8`
- pressure max: `113365 Pa`
- `T_min = 499.157 K`
- mean `|ΔT|`: `3.277 K`
- `Qdot / stock ≈ 31.56x`

### Larger uncapped `dp100_full` (`105362` rows)
- mean `Qdot`: `-5.921e7`
- pressure max: `103218 Pa`
- `T_min = 493.303 K`
- mean `|ΔT|`: `1.824 K`
- `Qdot / stock ≈ -3.65x`

### Mixed `dp100 + canonical@0.1`
- mean `Qdot`: `4.177e7`
- pressure max: `101739 Pa`
- `T_min = 499.157 K`
- mean `|ΔT|`: `1.385 K`
- `Qdot / stock ≈ 2.58x`

### Stock reference
- mean `Qdot`: `1.622e7`
- pressure max: `102000 Pa`
- `T_min = 499.249 K`
- mean `|ΔT|`: `0.828 K`

## Interpretation

This is the clearest positive result yet from the canonical-data thread.

A **small calibrated canonical fraction** does what the previous two single-path attempts could not do on its own:
- it removes most of the huge `Qdot` overshoot from the original `dp100` baseline
- it avoids the negative-mean-`Qdot` overcorrection seen in the larger uncapped `dp100_full` dataset
- it keeps the healthy temperature floor of the original `dp100` baseline
- it brings pressure behavior very close to stock
- it improves thermal drift substantially versus the original `dp100` baseline

So the current picture is now much sharper:
- scaling raw case-pair data alone is too blunt
- canonical augmentation alone is too rich
- **small calibrated mixing is materially better than either extreme**

## Current takeaway

The best current data-side story for C2H4 is now:
- use the solver-relevant `dp100` case-pair path as the backbone
- add a small amount of canonical augmented chemistry support
- avoid both pure overshoot and pure overcorrection

This is not the final answer, but it is a real step toward a better regime.

## Most useful next step

The next justified experiment is now a **local refinement around the successful small-mix region**, for example:
- `0.05`
- `0.1`
- `0.2`

with the same deployment-facing `5e-6` test,
so we can tell whether `0.1` is truly near the best operating point or just the first good point we tried.
