# Early-to-late C2H4 curriculum test: structured late-data exposure helps more than naive concatenation, but still destabilizes before `5e-6`

_Date: 2026-04-24_

## Why this was the next step

The previous late-dp100 enrichment test established two things:
- late-window dp100 pairs really do contain the missing intermediate coverage
- naive early+late concatenation destabilizes the deployed model badly and fails around `3.4e-6`

That made the next most useful step a **structured regime-mixing test** rather than another static mixture.

The simplest such structure is curriculum:
1. start from the working early-window dp100 checkpoint
2. then fine-tune on the late-window dp100 dataset

This is still a small, reproducible intervention, but it tests whether *ordering* helps where one-shot mixing failed.

## What I built

### Curriculum runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_early_to_late_curriculum.py`

This script:
- loads the existing early dp100 checkpoint
- preserves its normalization contract
- fine-tunes it for a small late-stage training run on the late dp100 dataset
- exports a DeepFlame bundle for deployment testing

### Inputs
- init checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_fno_smoke.pt`
- late curriculum dataset:
  - `/root/workspace/data/c2h4_case_pairs_late_dp100.npy`

### Output checkpoint / bundle
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_fno_smoke.pt`
- bundle:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_fno_smoke_deepflame_bundle/`

### Integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_early_to_late_curriculum_fno_batched_full`

## Training behavior

The late-stage fine-tune is hard, but it is at least coherent enough to run.

Late-stage loss trend over 3 fine-tune epochs:
- epoch 1: `Loss ≈ 1.225532e+00`
- epoch 2: `Loss ≈ 9.559001e-01`
- epoch 3: `Loss ≈ 9.173814e-01`

These are large losses, which is consistent with the late regime being substantially different from the early training distribution.

## Runtime result

This curriculum model does **not** fully solve the problem, but it is materially better than naive early+late concatenation.

### Horizon reached
- curriculum model fails during the `4.5e-6` step
- naive early+late concatenation failed around `3.4e-6`
- pure early dp100 still remains the only tested path that reaches `5e-6`

So curriculum improves the late-enrichment path by roughly `1.1e-6` of additional runtime horizon.

## Log evidence

Late active learned-set counts remained large rather than collapsing immediately:
- `3.3e-06`: `50057`
- `3.8e-06`: `49514`
- `4.2e-06`: `49986`
- `4.4e-06`: `50392`
- `4.5e-06`: `50508`

So this is not a trivial “model gave up” failure. The learned path stays active deep into the late window.

## Failure mode

The case still fails with HP reconstruction error, but later than the naive mixed case:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP): No convergence in 500 iterations`

Representative failing states at `4.5e-6` show very low temperatures and depressed pressures:
- `Starting Temperature ≈ 72.16 K`, `Current Pressure ≈ 52593 Pa`
- `Starting Temperature ≈ 65.46 K`, `Current Pressure ≈ 57690 Pa`

So the instability is still thermodynamic, not bridge/runtime related.

## Pre-failure written-state comparison at `4.4e-6`

Artifacts:
- curriculum:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_early_to_late_curriculum_fields_4.4e-06_vs_2e-06.json`
- pure early dp100 reference:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_fno_batched_full_fields_4.4e-06_vs_2e-06.json`

### Curriculum at `4.4e-6`
- `T_min = 200.63 K`
- `p_min = 29070 Pa`
- `p_max = 149572 Pa`
- mean `Qdot = -9.83e9`
- mean `|ΔT|` from `2e-6` ≈ `25.84 K`

### Pure early dp100 at `4.4e-6`
- `T_min = 499.19 K`
- `p_min = 100686 Pa`
- `p_max = 109903 Pa`
- mean `Qdot = 4.04e8`
- mean `|ΔT|` from `2e-6` ≈ `2.54 K`

So even though curriculum pushes the late-enrichment idea farther than naive concatenation, its late pre-failure state is still much less healthy than the pure early dp100 baseline.

## Species-level interpretation

Curriculum does appear to activate more late-chemistry channels than pure early dp100.

At `4.4e-6`, curriculum has nonzero means or visible maxima for species that were effectively collapsed under pure early dp100, for example:
- `C2H5`: max `1.48e-08` vs pure early dp100 `0`
- `C2H3`: max `3.36e-04` vs pure early dp100 `0`
- `CH2CHO`: max `3.14e-03` vs pure early dp100 `0`
- `CH2CO`: max `7.81e-03` vs pure early dp100 `6.33e-07`

But this partial chemistry recovery comes together with severe thermodynamic damage:
- broad pressure distortion
- cold-tail reappearance
- strongly negative mean `Qdot`

So the late-chemistry enrichment is not yet arriving in a solver-compatible way.

## Interpretation

This is a useful intermediate result.

It shows that **structure matters**:
- naive early+late mixing failed too early
- curriculum is clearly better than naive concatenation
- but still not good enough to replace the pure early dp100 baseline

So the project learned something more specific than before:
- the late-window information is valuable
- ordering the regimes helps
- but the current one-model, one-contract curriculum still transfers late chemistry too aggressively or too incompatibly into the deployment trajectory

## Current ranking

Among the late-enrichment family tested so far:
1. **pure early dp100** — still the best solver-usable baseline; reaches `5e-6`
2. **early→late curriculum** — better than naive late mixing, reaches about `4.5e-6`
3. **naive early+late concatenation** — fails around `3.4e-6`

## What this changes

Curriculum is now justified as a meaningful mechanism, but not yet a solution.

That means the next structured step should probably make the late-stage exposure **gentler or more selective**, for example:
- smaller late-stage learning rate / fewer updates
- weaker late-stage sampling weight
- or explicit regime-conditioned deployment logic instead of forcing one unified model to absorb both regimes fully

## Current takeaway

- late-data support is real
- structure beats naive concatenation
- but the current curriculum still trades too much thermodynamic stability for late-chemistry recovery
- **pure early dp100 remains the deployment-facing reference baseline** for now
