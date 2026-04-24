# Weighted-mixed C2H4 ablation (`unfiltered + 2x dp100`): naive oversampling of the better subset is solver-usable, but it regresses relative to both pure `dp100` and the simpler `1:1` mixed dataset

_Date: 2026-04-24_

## Why this was the next step

After the first `1:1` mixed dataset (`unfiltered + dp100`) produced a viable middle ground, the next concrete question was whether a **more dp100-heavy mix** could preserve the broader-coverage benefit while pulling the model closer to the better `dp100` runtime behavior.

Rather than adding new trainer machinery first, I tested the simplest practical proxy for dataset weighting:
- include the unfiltered dataset once
- include the `dp100` dataset twice

This gives a `1:2` effective sampling ratio in favor of `dp100`.

## What I built

### Reusable mixed-dataset builder reuse
Using:
- `/root/workspace/scripts/build_c2h4_mixed_casepair_dataset.py`

I built:
- `/root/workspace/data/c2h4_case_pairs_smoke_mixed_unfiltered_dp100x2.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_mixed_unfiltered_dp100x2.json`

Composition:
- `50000` unfiltered rows
- `50000` dp100 rows
- another `50000` dp100 rows
- total: `150000` rows

### New training/export runner
- `/root/workspace/scripts/run_c2h4_casepair_mixed_unfiltered_dp100x2_fno_baseline.py`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_mixed_unfiltered_dp100x2_fno_batched_full`

## Training behavior

Training remained stable and the final offline loss improved further relative to the earlier `1:1` mixed dataset.

Loss trend:
- epoch 1: `Loss ≈ 2.060005e-01`
- epoch 6: `Loss ≈ 8.945889e-02`

This is lower than the earlier `1:1` mixed dataset final loss (`≈ 1.026500e-01`).

So again, the offline fit looked encouraging.

## Runtime result

The weighted-mix model remained solver-usable through `5e-6`.

At `5e-6`:
- learned active-set count: `61157`
- no OOM lines
- `solver.err` empty

So this was not a runtime wiring failure. It is a meaningful deployment-facing comparison.

## But the result is a regression

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_mixed_unfiltered_dp100x2_fno_batched_full_fields_5e-06_vs_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_mixed_unfiltered_dp100x2_vs_mix_vs_dp100_vs_unfiltered_vs_stock_5e-06.json`

### Main source-term metric got worse than the simpler `1:1` mix
Mean `Qdot` at `5e-6`:
- weighted mix (`1:2`): `1.020e9`
- simple mix (`1:1`): `7.85e8`
- pure dp100: `5.12e8`
- unfiltered: `1.446e9`
- stock: `1.62e7`

Stock-normalized mean `Qdot`:
- weighted mix: `62.9x`
- simple mix: `48.4x`
- dp100: `31.6x`
- unfiltered: `89.2x`

So the dp100-heavy oversampling **did not** continue the improvement trend.

### Pressure behavior also regressed
Pressure max at `5e-6`:
- weighted mix: `137764 Pa`
- simple mix: `121172 Pa`
- dp100: `113365 Pa`
- unfiltered: `140676 Pa`
- stock: `102000 Pa`

This pushes the weighted mix much closer to the unfiltered pressure tail than to the dp100 case.

### Thermal drift also got worse
Mean `|ΔT|` from `2e-6`:
- weighted mix: `5.16 K`
- simple mix: `3.20 K`
- dp100: `3.28 K`
- unfiltered: `5.35 K`
- stock: `0.83 K`

So the weighted mix also gave back much of the thermal-drift improvement.

## Species-level notes

At `5e-6`:
- `C2H4`
  - weighted mix: `0.06035`
  - simple mix: `0.06102`
  - dp100: `0.06148`
  - stock: `0.06178`
- `OH`
  - weighted mix: `5.28e-04`
  - simple mix: `2.78e-04`
  - dp100: `3.17e-04`
  - stock: `1.34e-04`

The weighted mix is visibly more over-active than the simple mix in radicals/source behavior.

And the deeper late-chemistry gap still remains unresolved:
- `C2H5 = 0`
- `C2H3 = 0`
- `CH2CHO = 0`
- `CH2CO` still negligible

## Interpretation

This is another useful non-monotonic result.

It shows that:
- lower offline loss does **not** imply better coupled-solver behavior
- naive oversampling of the “better” subset is **not** a reliable stand-in for the weighting/curriculum we actually want
- dataset-composition effects are strongly non-monotonic in the deployment-facing metrics

So the current ranking becomes clearer:
1. **pure `dp100`** remains the best current single tested target set
2. **simple `1:1` mixed dataset** is a viable middle ground
3. **`1:2` weighted mix toward dp100** is solver-usable but a regression relative to the simpler mix
4. **over-narrow `dp100 + dT10`** fails in-case

## What this changes

This result argues against continuing with simple duplication-based dataset weighting as the main next lever.

If weighting is to be explored further, it likely needs to be done more deliberately, for example through:
- explicit curriculum ordering
- per-source batch mixing control
- or a target path that changes label semantics rather than only dataset frequency

## Most useful next step

The next useful move is now less about *how many times* to repeat dp100 examples and more about *what the labels mean*. The evidence is increasingly pointing toward a deeper target-construction issue, especially for the missing late intermediates/products, rather than a simple sample-ratio problem.
