# C2H4 canonical-mix local refinement: `0.2` beats `0.1`, while `0.05` fails badly, so the first good operating window is broader than expected but still clearly nontrivial

_Date: 2026-04-24_

## Why this was the next step

After the first calibrated mixed result (`dp100 + canonical@0.1`) looked clearly better than both:
- pure `dp100` (`50k`)
- and the larger uncapped `dp100_full` (`105k`)

…the most useful next step was to test the local neighborhood rather than jump to a very different idea.

So I ran the first refinement around the promising small-mix regime:
- `0.05`
- `0.1`
- `0.2`

where the number means the effective canonical/case-pair weight ratio.

## New reusable scripts

- dataset builder:
  - `/root/workspace/scripts/build_c2h4_repeat_mixed_dataset.py`
- generic train/export runner:
  - `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`

These make it easier to continue local mix-ratio sweeps without cloning one-off scripts for every dataset.

## New datasets

### `r = 0.05`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p05.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p05.json`
- total rows: `52484`
- effective canonical/case-pair ratio: `0.04968`

### `r = 0.2`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p2.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p2.json`
- total rows: `59936`
- effective canonical/case-pair ratio: `0.19872`

## New trained/integrated runs

### `r = 0.05`
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p05_fno_smoke.pt`
- DeepFlame bundle:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p05_fno_smoke_deepflame_bundle/`
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_canonical_r0p05_fno_batched_full`
- field artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_canonical_r0p05_fno_batched_full_fields_5e-06_vs_2e-06.json`

### `r = 0.2`
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p2_fno_smoke.pt`
- DeepFlame bundle:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_canonical_r0p2_fno_smoke_deepflame_bundle/`
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_canonical_r0p2_fno_batched_full`
- field artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_plus_canonical_r0p2_fno_batched_full_fields_5e-06_vs_2e-06.json`

Both runs completed cleanly to `5e-6`:
- empty `solver.err`
- no OOM line
- stable learned active-set counts through the horizon

## Cross-comparison artifact

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_canonical_mix_local_refinement_comparison_5e-06.json`

## Main comparison at `5e-6`

### `dp100` (`50k`)
- mean `Qdot`: `5.118e8`
- `Qdot / stock ≈ 31.56x`
- pressure max: `113365 Pa`
- `T_min = 499.157 K`
- mean `|ΔT| = 3.277 K`

### `dp100_full` (`105k`)
- mean `Qdot`: `-5.921e7`
- `Qdot / stock ≈ -3.65x`
- pressure max: `103218 Pa`
- `T_min = 493.303 K`
- mean `|ΔT| = 1.824 K`

### `mix_r0p05`
- mean `Qdot`: `-3.986e8`
- `Qdot / stock ≈ -24.58x`
- pressure max: `102203 Pa`
- `T_min = 499.157 K`
- mean `|ΔT| = 1.684 K`

### `mix_r0p1`
- mean `Qdot`: `4.177e7`
- `Qdot / stock ≈ 2.58x`
- pressure max: `101739 Pa`
- `T_min = 499.157 K`
- mean `|ΔT| = 1.385 K`

### `mix_r0p2`
- mean `Qdot`: `2.514e7`
- `Qdot / stock ≈ 1.55x`
- pressure max: `102817 Pa`
- `T_min = 499.159 K`
- mean `|ΔT| = 0.927 K`

### stock
- mean `Qdot`: `1.622e7`
- pressure max: `102000 Pa`
- `T_min = 499.249 K`
- mean `|ΔT| = 0.828 K`

## Interpretation

This refinement is informative in two ways.

### 1) `0.1` was a real signal, not a fluke
The earlier `r = 0.1` success was not random. Nearby calibrated mixes really do outperform the old pure-`dp100` path.

### 2) The best current point shifts upward to `0.2`
In this first local refinement, `r = 0.2` is the strongest result:
- `Qdot` is much closer to stock than `r = 0.1`
- thermal drift is also much closer to stock
- the temperature floor stays healthy
- pressure remains close to stock, though slightly worse than `r = 0.1`

So the current best point in this tested neighborhood is:
- **`dp100 + canonical@0.2`**

## Important failure signal: `0.05` is bad
The `r = 0.05` run is not just slightly worse—it fails in a qualitatively important way:
- mean `Qdot` becomes strongly negative
- despite decent pressure behavior and a healthy `T_min`

That means the small-mix regime is not monotone in the naive way one might expect.

So the first lesson is:
- **too little canonical enrichment can be bad in a different way than too much**

This is valuable because it means the operating region is governed by a real balance, not just “add as little canonical data as possible.”

## Current takeaway

The calibrated canonical-mix path is now stronger than the earlier alternatives, and the current best tested point is:
- **`r = 0.2`**, not `0.1`

So the next question is no longer whether calibrated mixing helps.
It clearly does.

The next question is now:
- where exactly is the best operating window above `0.1` and around `0.2`?

## Most useful next step

The next justified refinement is a narrower sweep above `0.1`, for example:
- `0.15`
- `0.2`
- `0.25`
- maybe `0.3`

because the first local refinement says the optimum is likely **not** below `0.1`.
