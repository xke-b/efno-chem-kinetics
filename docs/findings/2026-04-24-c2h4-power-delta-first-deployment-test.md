# C2H4 first power-delta deployment test on `dp100 + oneD@0.2`: bulk thermodynamics improve sharply against CVODE, but the intermediate-chemistry collapse remains

_Date: 2026-04-24_

## Why this was the next step

After establishing a proper DeepFlame C2H4 CVODE baseline at `1e-6`, the main conclusion was no longer ambiguous: the current C2H4 bottleneck is mainly a **target-semantics problem** for multiscale intermediates, not only a runtime or manifold-support problem.

A Xiao-style next step was therefore to replace the current species target
- `BCT(Y_next) - BCT(Y_current)`

with a direct power transform on the physical species delta:
- `sign(ΔY) * |ΔY|^λ / λ`
- with `λ = 0.1`

The first deployment test uses the previously justified mixed dataset:
- base: `dp100`
- add-on: oneD DeepFlame Xiao-style augmented labeled subset at ratio `0.2`

## Implementation work

I added first-pass support for `target_mode="species_power_delta"` across the project path:

DFODE-kit:
- `/opt/src/DFODE-kit/dfode_kit/utils.py`
  - added power-transform helpers
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
  - added `species_power_delta` target construction
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`
  - added decode support for power-delta targets inside the physics-style trainer
- `/opt/src/DFODE-kit/tests/test_training_preprocess.py`
  - added target-preparation smoke coverage

Workspace-side tooling:
- `/root/workspace/scripts/evaluate_species_delta_checkpoint.py`
  - added power-delta decode support
- `/root/workspace/scripts/export_dfode_fno_to_deepflame_bundle.py`
  - added export/runtime support for power-delta checkpoints
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`
  - added `--target-mode` and `--power-lambda`

## Training and export artifacts

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke_baseline/summary.json`

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke_np8`

## Important implementation failure caught and fixed

The **first** power-delta deployment attempt did not actually run correctly.

At the first learned step, the exported bridge hit:
- `('operands could not be broadcast together with shapes (8192,24) (8192,23) ',)`

This came from a runtime bug in the new power-delta inference path: the exported bridge was trying to add a `23`-component main-species delta to the full `24`-species vector. That meant the model silently returned zero source terms after the exception path.

I fixed the bridge by applying the predicted delta only to the `n_species - 1` main species before preserving/renormalizing the last species, then re-exported and reran the case.

This is scientifically important because without that check the first run would have looked superficially calm while actually exercising a broken inference path.

## Post-fix deployment result

The corrected power-delta model runs cleanly to `1e-6`.

Field artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_fields_1e-06_vs_2e-07.json`

Matched CVODE comparison:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_vs_cvode_1e-06_summary.json`
- `/root/workspace/docs/findings/images/c2h4-dp100-plus-oned-r0p2-powerdelta-vs-cvode-1e-06.png`

Compact direct comparison against the original BCT-delta mixed model:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_vs_bctdelta_compact_summary.json`

## Main result against CVODE at `1e-6`

### Bulk metrics improve sharply
Compared with the original `BCT(Y_next)-BCT(Y_current)` mixed-label model:

- mean active-region `Qdot` ratio vs CVODE:
  - old BCT-delta: **`8.59x`**
  - new power-delta: **`8.51e-4x`**

- mean active-region `|ΔT|` vs CVODE:
  - old BCT-delta: **`3.14 K`**
  - new power-delta: **`0.338 K`**

- mean active-region `|Δp|` vs CVODE:
  - old BCT-delta: **`103.3 Pa`**
  - new power-delta: **`28.3 Pa`**

So the power-delta target dramatically suppresses the earlier source-term overdrive and moves bulk thermodynamics much closer to the proper DeepFlame chemistry baseline.

### But the key intermediate chemistry is still not recovered
Key species mean ratios vs CVODE at `1e-6`:
- `C2H5`: **`3.13e-09x`**
- `C2H3`: **`1.47e-14x`**
- `CH2CHO`: **`8.82e-19x`**
- `CH2CO`: **`1.15e-10x`**

By contrast, bulk products/radicals remain superficially acceptable:
- `OH`: `1.011x`
- `CO2`: `1.000x`

## Interpretation

This is a strong partial result.

### What improved
- the power-delta target is not merely a theoretical preference; it **materially changes the deployment regime**
- it removes the massive early `Qdot` overdrive seen in the BCT-delta mixed model
- it improves temperature and pressure closeness to CVODE substantially

### What did not improve
- the reactive intermediate manifold is still effectively deleted
- the model is now closer to a **chemically over-damped** surrogate than to a faithful one

So the power-delta target helped the **bulk thermochemical calibration** but did **not** by itself solve the intermediate-chemistry semantics problem.

## Current takeaway

The first C2H4 power-delta deployment test is a meaningful advance because it separates two failure modes that had been entangled before:

1. **bulk source-term distortion** can be improved substantially by changing the target transform
2. **intermediate-manifold fidelity** still remains unresolved even after that improvement

That means the next C2H4 question is now sharper than before: not simply whether power-delta targets help, but how to combine them with regime-aware data or species-specific treatment so that the intermediate channels stop collapsing while keeping the newly improved bulk behavior.
