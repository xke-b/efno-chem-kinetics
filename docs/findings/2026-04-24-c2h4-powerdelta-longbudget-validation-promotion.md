# C2H4 power-delta long-budget promotion: GPU validation-aware training improves some collapsed intermediates, but bulk `Qdot` behavior regresses sharply and the deployed case fails much earlier

_Date: 2026-04-24_

## Why this was the next step

The recent web search reinforced that our C2H4 `6`-epoch runs were only scouting runs. The next useful step was therefore not another tiny architecture tweak, but a **real promotion test**:

- use a larger training budget
- use a held-out validation split
- use best-checkpoint restoration
- use GPU training by default
- then test whether the promoted checkpoint is actually more solver-useful in DeepFlame

## Code changes made first

To support this, I finished the most useful unfinished training thread.

### DFODE-kit
- `/opt/src/DFODE-kit/dfode_kit/training/train.py`
  - added reusable raw-array / normalization split logic
  - added `validation_fraction` handling with train/validation split
  - records `training_history`, `best_epoch`, `best_metric`, and dataset split metadata in checkpoints
- `/opt/src/DFODE-kit/dfode_kit/training/supervised_physics.py`
  - added validation evaluation
  - added best-state restoration
  - added optional reduce-on-plateau LR scheduling
  - added early stopping support
- `/opt/src/DFODE-kit/dfode_kit/models/fno1d.py`
  - completed `attention_position` support for `post_spectral` vs `interleaved`
- `/opt/src/DFODE-kit/tests/test_fno1d_model.py`
  - added interleaved-attention coverage
- `/opt/src/DFODE-kit/tests/test_supervised_physics_trainer.py`
  - added validation-history / best-epoch coverage

### Workspace
- `/root/workspace/scripts/run_c2h4_fno_baseline_from_dataset.py`
  - now exposes:
    - `--attention-position`
    - `--validation-fraction`
    - `--early-stopping-patience`
    - `--early-stopping-min-delta`
    - `--lr-scheduler`
    - plateau scheduler knobs
  - now records checkpoint-side training history into the run summary
- `/root/workspace/scripts/export_dfode_fno_to_deepflame_bundle.py`
  - now preserves `attention_position` in exported FNO bundles and runtime reconstruction

## Promoted training run

I promoted the plain power-delta mixed-data baseline first.

Tag:
- `c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val.pt`

Bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_baseline/summary.json`

Training setup:
- dataset: `dp100 + oneD DeepFlame@0.2`
- target: `species_power_delta`
- epochs budget: `100`
- validation fraction: `0.1`
- train / validation samples: `54000 / 6000`
- seed: `0`
- batch size: `1024`
- optimizer LR: `1e-3`
- scheduler: `reduce_on_plateau`
- plateau patience / factor: `4 / 0.5`
- min LR: `1e-5`
- early stopping patience: `12`
- training device: **GPU** (`cuda` path in DFODE-kit training)

Observed checkpoint metadata:
- best epoch: `98`
- best validation loss: `0.1311017026503881`
- LR reductions occurred from `1e-3 -> 5e-4 -> 2.5e-4`

This is the first C2H4 run in this branch that is both:
- explicitly validation-aware
- trained at a materially longer budget on GPU

## DeepFlame deployment result

Deployed case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_np8`

The promoted model **did not improve deployment robustness**.

Instead:
- it ran through early learned steps
- but failed in HP reconstruction much earlier than the original 6-epoch power-delta deployment
- solver log shows progression through `1e-07`, `2e-07`, `3e-07`, and `4e-07`
- failure mode remained `ThermoPhase::setState_HPorUV (HP)` inside DeepFlame thermodynamic correction

Relevant logs:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_np8/run.log`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_promoted100_val_np8/solver.err`

## Comparison against CVODE at `2e-07`

Promoted-model comparison artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_promoted100_val_vs_cvode_2e-07_summary.json`

Reference 6-epoch comparison artifact generated for context:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_plus_oned_r0p2_powerdelta_6ep_vs_cvode_2e-07_summary.json`

### Bulk metrics at `2e-07`

#### 6-epoch power-delta
- `Qdot` ratio vs CVODE: `1.80e-2x`
- mean `|ΔT|`: `8.28e-03 K`
- mean `|Δp|`: `1.18 Pa`

#### promoted 100-epoch validation-aware power-delta
- `Qdot` ratio vs CVODE: **`2.70e+1x`**
- mean `|ΔT|`: **`1.37 K`**
- mean `|Δp|`: **`22.3 Pa`**

So the promoted model moved from the earlier **strongly over-damped** regime to a new **strongly over-driven** regime.

That is a major deployment-facing regression in bulk source-term behavior.

### Intermediate species at `2e-07`

There was a real upside:

#### `C2H3`
- 6-epoch: `4.32e-13x`
- promoted: **`2.08e-08x`**

#### `CH2CHO`
- 6-epoch: `2.60e-17x`
- promoted: **`5.47e-09x`**

#### `CH2CO`
- 6-epoch: `7.16e-10x`
- promoted: **`7.67e-08x`**

#### `C2H5`
- 6-epoch: `1.38e-08x`
- promoted: `6.07e-09x`

So the longer-budget promoted model did **partially lift several previously collapsed intermediates by many orders of magnitude**, but it did so while breaking bulk `Qdot` behavior badly enough to become less solver-usable overall.

## Interpretation

This is a scientifically useful negative result.

### What it tells us

1. **Longer training absolutely changes the learned regime** for C2H4.
   - The 6-epoch scout was not a stable proxy for what this model family wants to do under a larger budget.

2. **Validation-aware longer training did not automatically improve coupled usefulness.**
   - Better/longer optimization in offline training can move the surrogate into a deployment-worse regime.

3. **The main tradeoff is now clearer.**
   - short-budget power-delta: better bulk thermodynamics, severely collapsed intermediates
   - long-budget power-delta: some intermediate recovery, but badly over-driven heat release and earlier HP failure

4. **This strengthens the case for architecture-side and loss-balance follow-up, not plain budget scaling alone.**
   - We likely need the next promoted comparisons to test whether attention placement and/or species-aware weighting can recover intermediates **without** pushing `Qdot` into the over-driven regime.

## Current takeaway

The first GPU validation-aware long-budget promotion did **not** produce a new deployment baseline.

But it did reduce an important uncertainty:

> The current C2H4 power-delta branch is not simply “undertrained.” Longer validation-aware training changes it substantially, but the change is not an automatic improvement; it exposes a sharper bulk-vs-intermediate tradeoff.

## Most useful next step from here

The next justified follow-up is:
1. keep the new validation-aware GPU training path
2. compare **promoted** nearby variants rather than only 6-epoch scouts:
   - power-delta
   - power-delta + attention
   - power-delta + attention + species weighting
3. prioritize variants that preserve the better bulk control while lifting intermediates
4. finish the **interleaved-attention** comparison under this promoted training regime
