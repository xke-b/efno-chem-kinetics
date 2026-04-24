# C2H4 FNO batched-inference fix: chunking the case-local FNO bridge removes the late CUDA OOM and restores nonzero `Qdot` at `5e-6`

_Date: 2026-04-24_

## Why this was the next step

The previous case-aligned C2H4 FNO run reached `5e-6`, but it was not trustworthy as evidence because the late log contained:
- `CUDA error: out of memory`

and the written `Qdot` field at `5e-6` had collapsed to all zeros.

That made the next diagnosis very specific:
- the case-aligned training distribution looked much better
- but the case-local FNO Python bridge was likely not handling the growing DNN-active set robustly on GPU

## Root cause hypothesis

The original exported FNO `inference.py` processed the entire active subset in one GPU batch:
- gather all cells with `T > frozenTemperature`
- normalize them
- run one forward pass
- decode them in one shot

By `5e-6`, the active subset had grown to:
- `60316` cells

That is far larger than the early-horizon active set and was enough to trigger the late GPU-memory failure in the unbatched bridge.

## Fix implemented

Updated exporter:
- `/root/workspace/scripts/export_dfode_fno_to_deepflame_bundle.py`

The generated case-local FNO bridge now:
- uses `DEFAULT_BATCH_SIZE = 8192`
- runs inference over the active subset in chunks
- catches GPU OOM during a batch
- halves batch size and retries if needed
- clears CUDA cache on retry when using GPU

So the export path is now more robust to active-set growth.

## Re-generated bundle and re-test

I re-exported the case-aligned C2H4 FNO bundle and staged a replay case:
- replay case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_fno_integration_batched`

This replay case was copied from the earlier `c2h4_casepair_fno_integration`, but:
- replaced `inference.py` with the new batched bridge
- restarted from the last good written state before the questionable final step
- replayed only the `4.9e-6 -> 5e-6` step

## Result

The replayed batched case completes the `5e-6` step with:
- no CUDA OOM line in the log
- `real inference points number: 60316`
- nonzero written `Qdot`

At `5e-6` in the replayed batched case:
- `Qdot_min = -3.86093e8`
- `Qdot_max = 1.85705e11`
- `Qdot_mean = 1.4222541787825623e9`

That is qualitatively different from the broken unbatched run, where:
- `Qdot_min = 0`
- `Qdot_max = 0`
- `Qdot_mean = 0`

## Other field checks

The replayed batched case still preserves:
- tight species-simplex closure
- a healthy low-temperature floor

At `5e-6` in the replayed batched case:
- species-sum mean abs deviation from `1`: `2.15e-08`
- species-sum max abs deviation from `1`: `1.52e-06`
- `T_min = 499.212 K`
- `T_max = 2543.23 K`

The within-step drift from `4.9e-6` to `5e-6` also looks modest rather than catastrophic:
- mean `|ΔT| ≈ 0.270 K`
- largest `|ΔT| ≈ 27.30 K`

## Interpretation

This is a meaningful runtime diagnosis and fix.

It shows that the previous late-time trust problem was not only about the learned model. A substantial part of the issue was the **inference implementation itself**:
- unbatched active-set inference was not robust as active learned participation grew
- batching removed the CUDA OOM symptom
- batching restored nonzero source behavior at `5e-6`

So the current C2H4 case-aligned FNO path is now in a much stronger position:
1. case-aligned data removed the early `~1e-6` collapse
2. batched inference removed the late `5e-6` GPU-OOM / zero-`Qdot` bridge pathology

## Remaining caution

This does not yet prove full physical correctness of the learned model. But it upgrades the result from:
- "survives to `5e-6` with a suspicious late-time bridge failure"

to something much stronger:
- "survives to `5e-6` with the main observed bridge pathology repaired"

## Most useful next step

Re-run the case-aligned C2H4 FNO from an earlier point with the batched bridge as the default export path and then compare the full `5e-6` batched run systematically against stock, rather than relying only on the repaired final-step replay.
