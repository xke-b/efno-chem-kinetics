# Full batched-bridge C2H4 case-aligned FNO run: a clean start-to-`5e-6` replay now completes without CUDA OOM and preserves nonzero heat release

_Date: 2026-04-24_

## Why this was the next step

After fixing the exported FNO bridge to use batched inference, the previous evidence was still only a repaired final-step replay from `4.9e-6 -> 5e-6`.

The next useful question was therefore stricter:
- does the **full** case-aligned C2H4 FNO run remain stable from the start through `5e-6` when the batched bridge is used throughout?

That is the necessary check before treating the batched bridge as the new default runtime path.

## Case

- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_fno_integration_batched_full`

This case was copied fresh from the trusted stock C2H4 baseline and configured with:
- case-aligned FNO bundle checkpoint
- batched exported `inference.py`
- `GPU on`
- `coresPerNode 8`
- `numberOfSubdomains 8`
- `mpirun -np 8`
- `startFrom startTime`
- `endTime 5e-6`

So this is the first clean full-horizon replay with the repaired bridge from the beginning of the run.

## Main result

The full batched-bridge case completes from start through `5e-6`.

Observed written times include the full chain from early learned steps through the target horizon:
- `1e-07`, `2e-07`, ..., `1e-06`, ..., `2e-06`, ..., `5e-06`

Crucially:
- no CUDA OOM line appears in the log
- `solver.err` remains empty

## Learned active-set behavior

Late-horizon learned active-set counts continue to grow rather than collapse:
- `3.1e-06`: `38939`
- `3.2e-06`: `39478`
- `3.3e-06`: `40034`
- `3.4e-06`: `40705`
- `3.5e-06`: `41545`
- `3.6e-06`: `42508`
- `3.7e-06`: `43589`
- `3.8e-06`: `44805`
- `3.9e-06`: `46147`
- `4e-06`: `47518`
- `4.1e-06`: `48977`
- `4.2e-06`: `50490`
- `4.3e-06`: `52012`
- `4.4e-06`: `53603`
- `4.5e-06`: `55221`
- `4.6e-06`: `56861`
- `4.7e-06`: `58541`
- `4.8e-06`: `60236`
- `4.9e-06`: `61958`
- `5e-06`: `63710`

This is higher than the earlier unbatched run at `5e-6` (`60316`) and shows no sign of the old early-collapse regime.

## `5e-6` field summary

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_fno_integration_batched_full_fields_5e-06_vs_2e-06.json`

At `5e-6`, the full batched run shows:
- `T_min = 499.158 K`
- `T_max = 2547.76 K`
- `T_mean = 566.54 K`
- `Qdot_min = -1.84091e9`
- `Qdot_max = 1.86878e11`
- `Qdot_mean = 1.44582e9`

Species-simplex closure remains tight:
- mean abs deviation from `1`: `2.34e-08`
- max abs deviation from `1`: `1.47e-06`

Compared with stock at `5e-6`:
- stock `T_min = 499.249 K`
- stock `T_max = 2462.06 K`
- stock `Qdot_mean ≈ 1.62e7`

So the full batched run preserves nonzero heat release and avoids the clearly broken zero-`Qdot` state of the old unbatched late path.

## Interpretation

This is a meaningful upgrade in confidence.

The project now has evidence that:
1. the case-aligned FNO path can run from start through `5e-6`
2. the repaired batched bridge remains stable across the full horizon
3. the earlier late CUDA OOM was a real bridge pathology, not just a model-quality symptom
4. the repaired full-horizon path no longer exhibits the zero-`Qdot` collapse seen in the unbatched run

This does **not** yet prove full physical correctness. The `Qdot` scale and some thermochemical details still differ materially from stock. But the runtime path itself is now much more trustworthy than before.

## Most useful next step

Compare the full batched case-aligned FNO run against the stock `5e-6` baseline more systematically—especially heat-release distribution, temperature distribution, and species means in the active region—to determine whether the remaining gap is now mainly model quality rather than bridge/runtime pathology.
