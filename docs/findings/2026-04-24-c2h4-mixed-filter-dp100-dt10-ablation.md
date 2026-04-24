# Mixed-filter C2H4 ablation (`|Δp| <= 100 Pa` and `|ΔT| <= 10 K`): the cleaner-looking training subset fits better offline but fails earlier in-case, so smaller-step filtering is not automatically more solver-useful

_Date: 2026-04-24_

## Why this was the next step

After the pressure-filter family showed non-monotonic behavior, the next sensible refinement was to change the subset logic rather than only squeezing pressure harder.

The first mixed-filter trial was:
- `|Δp| <= 100 Pa`
- `|ΔT| <= 10 K`

The hope was that this would define a more chemistry-like local transition subset by removing both larger pressure drift and larger thermal jumps.

## What I built and ran

### Updated extractor usage
I used the now-extended extractor with:
- `--max-abs-delta-p 100`
- `--max-abs-delta-t 10`

Generated local dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_dt10.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_dt10.json`

### New training/export runner
- `/root/workspace/scripts/run_c2h4_casepair_dp100_dt10_fno_baseline.py`

### New integrated case
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_dt10_fno_batched_full`

Runtime regime remained the trusted stock-style one:
- stock-style `np=8` GPU
- batched FNO bridge
- `startFrom startTime`
- target horizon initially `5e-6`

## Offline/training behavior looked encouraging

Training loss dropped much more than in the earlier pressure-only filtered runs:
- epoch 1: `Loss ≈ 2.206062e-01`
- epoch 6: `Loss ≈ 7.122682e-02`

This is substantially lower than:
- dp100 final loss `≈ 1.226254e-01`
- dp50 final loss `≈ 1.211833e-01`
- unfiltered case-pair final loss `≈ 1.200046e-01`

So purely as an offline fit to the filtered target subset, this mixed-filter dataset looked promising.

## In-case result: worse, not better

The integrated mixed-filter model did **not** reach `5e-6`.

Instead, it failed during the `4.2e-6` step with:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP): No convergence in 500 iterations`
- propagated from `dfChemistryModel::correctThermo()`

The failing state reported:
- target enthalpy: `137337.28`
- current pressure: `67761.05 Pa`
- starting temperature: `1677.70 K`

So this is a real return of the HP-failure family, not a bridge/runtime-memory issue.

## Pre-failure behavior

Late active-set counts did not grow the way the successful batched runs did. Instead they gradually declined:
- `2.3e-06`: `32904`
- `2.8e-06`: `32689`
- `3.3e-06`: `32455`
- `3.8e-06`: `32248`
- `4.1e-06`: `32054`
- `4.2e-06`: `31975`

Just before failure, the log also showed a strong cold-tail / thermodynamic warning sign returning:
- `min/max(T) = 67.1437, 2147.77` at `4.1e-06`

That is much less healthy than the successful batched case-pair baselines.

## Interpretation

This is an important failed attempt.

It shows that a training subset can look **cleaner and easier offline** while still becoming **less solver-useful in the real coupled runtime**.

The most plausible reading is:
- the mixed `dp100 + dT10` filter may have over-selected small local transitions
- which makes one-step supervised fitting easier
- but leaves the learned model less capable in the broader state transitions the real case still visits later in the run

So this result warns against overtrusting offline loss improvements when the deployment objective is coupled-solver usefulness.

## Current target-filter ranking

Based on actual solver behavior so far:
1. **dp100 only** remains the best current filter in the tested family
   - reaches `5e-6`
   - improves pressure and `Qdot` materially over unfiltered
2. **dp50 only** is solver-usable but worse than dp100 overall
3. **dp100 + dT10** looks good offline but fails earlier in-case

## What this changes

This failed mixed-filter ablation is still progress because it rules out an easy next step:
- simply adding a small-`|ΔT|` cap on top of pressure filtering is **not** automatically helpful for solver-facing performance

That means the next useful refinement should likely preserve broader state coverage while improving target quality another way, rather than further narrowing toward tiny local steps.

## Most useful next step

Do not keep squeezing local-transition filters blindly. The next better step is likely to preserve the stronger dp100 coverage and improve the target formulation more structurally—for example by distinguishing broad solver-state coverage from chemistry-dominant coverage, or by designing a mixed dataset rather than a single aggressively filtered subset.
