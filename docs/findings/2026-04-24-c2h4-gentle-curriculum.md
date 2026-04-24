# Gentle C2H4 curriculum test: a much smaller late-stage update survives to `5e-6`, but it does so by trading back a large amount of thermodynamic quality

_Date: 2026-04-24_

## Why this was the next step

The first early→late curriculum test showed that structure helps:
- naive early+late concatenation failed around `3.4e-6`
- a stronger late-stage curriculum pushed that to about `4.5e-6`

That suggested the next step should be a **gentler** late-stage exposure rather than another blunt mixture.

So I tested the smallest practical curriculum variant:
- initialize from the working early dp100 checkpoint
- fine-tune on the late dp100 dataset
- but use a much smaller late-stage learning rate and only one epoch

## What I built

### Gentle curriculum runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_early_to_late_curriculum_gentle.py`

Settings:
- init checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_fno_smoke.pt`
- late dataset:
  - `/root/workspace/data/c2h4_case_pairs_late_dp100.npy`
- stage LR: `1e-4`
- stage epochs: `1`

### Output checkpoint / bundle
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke.pt`
- bundle:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke_deepflame_bundle/`

### Integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_batched_full`

## Training behavior

The gentle late stage still looks hard offline, but the intervention is intentionally tiny.

Single late-stage epoch:
- `Loss ≈ 1.713706e+00`

That number is large, but the key question here was not offline fit quality in isolation. It was whether a much smaller late-stage update could preserve deployment stability while still introducing some late-regime influence.

## Main runtime result

This gentle curriculum model **does reach `5e-6`**.

That is the first successful late-enrichment-style path that survives to the target horizon.

At `5e-6`:
- learned active-set count: `72973`
- `solver.err` empty
- no OOM lines

So this is a genuine runtime-surviving curriculum result.

## But the quality tradeoff is large

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fields_5e-06_vs_2e-06.json`

Compared with the pure early dp100 baseline at `5e-6`, the gentle curriculum survives the horizon but gives back a lot of solution quality.

### Gentle curriculum at `5e-6`
- `T_min = 499.157 K`
- `p_max = 146985 Pa`
- mean `Qdot = 1.200e9`
- mean `|ΔT|` from `2e-6` ≈ `9.43 K`
- learned active cells: `72973`

### Pure early dp100 at `5e-6`
- `T_min ≈ 499.19 K`
- `p_max = 113365 Pa`
- mean `Qdot ≈ 5.12e8`
- mean `|ΔT|` from `2e-6` ≈ `3.28 K`
- learned active cells: `43825`

So the gentle curriculum succeeds on horizon survival, but:
- pressure spread gets much worse
- mean `Qdot` roughly doubles relative to pure dp100
- temperature drift roughly triples relative to pure dp100

In other words, it survives by remaining thermodynamically admissible enough, but it is clearly less faithful than the pure dp100 baseline on the main deployment-facing quality metrics.

## Late learned activity

The learned active-set count keeps rising through the late window:
- `4.4e-06`: `62457`
- `4.5e-06`: `64141`
- `4.6e-06`: `65868`
- `4.7e-06`: `67590`
- `4.8e-06`: `69340`
- `4.9e-06`: `71151`
- `5e-06`: `72973`

So this gentle curriculum is not conservative in the sense of suppressing learned participation. It actually expands learned participation substantially relative to pure dp100.

## Species-level interpretation

The gentle curriculum does not obviously solve the missing-intermediate retention problem at the mean-field level.

At `5e-6` the key late species remain extremely weak on average:
- `C2H5` mean ≈ `1.66e-14`
- `C2H3` mean ≈ `5.45e-15`
- `CH2CHO` mean ≈ `1.73e-10`
- `CH2CO` mean ≈ `9.23e-18`

There are some nonzero maxima and rare activations, but the broad missing-late-chemistry issue is still not resolved in a solver-useful way.

So the late-stage curriculum update improved runtime survival relative to the stronger curriculum, but not by actually recovering robust late-chemistry fidelity.

## Interpretation

This is a valuable non-binary result.

It shows three things at once:
1. **Curriculum strength matters a lot**.
   - strong curriculum: fails before `5e-6`
   - gentle curriculum: reaches `5e-6`
2. **The late-stage signal can be introduced without immediate catastrophic collapse**.
3. **But survival alone is not enough**.
   - the gentle curriculum substantially worsens pressure and source-term quality relative to pure dp100
   - and it still does not recover the missing late intermediates convincingly

So the current lesson is sharper than before:
- late-regime exposure must be gentle to avoid collapse
- but gentle exposure alone is not enough to produce a clearly better solver-facing model

## Current ranking

For deployment-facing usefulness at the tested `5e-6` horizon:
1. **pure early dp100** — still best overall quality / stability tradeoff
2. **gentle early→late curriculum** — now reaches `5e-6`, but with clearly degraded pressure / `Qdot` / drift behavior
3. **strong early→late curriculum** — improved over naive mixing but still failed around `4.5e-6`
4. **naive early+late concatenation** — failed around `3.4e-6`

## What this changes

The late-data question is no longer simply “can we include late data at all?”

Answer:
- yes, but only very gently if we want to survive to `5e-6`
- and even then, the result is not yet better than the pure dp100 baseline

So the next useful step should probably not be another manual LR tweak alone. The evidence is now pointing toward either:
- more selective late-stage objectives or batch composition
- or explicit deployment/regime conditioning, because a single shared model still seems to trade fidelity in one regime for another.
