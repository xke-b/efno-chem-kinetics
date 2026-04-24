# C2H4: more oneD chemistry is not yet enough

_Date: 2026-04-24_

After proving that the solver-native oneD/Xiao C2H4 data path can scale to `100k` labeled states, I used that dataset for the next obvious test:

- train a larger oneD-only chemistry model
- deploy it in the real DeepFlame case
- see whether scaling the oneD chemistry dataset alone improves the result

## What I trained

Model:
- `c2h4_oned_deepflame_interp_aug_100k_fno_powerdelta_promoted100_val`

Data:
- `100,000` labeled oneD/Xiao states
- power-delta targets
- GPU training
- validation-aware 100-epoch promotion run

Offline, it was not obviously stronger than the mixed-data promoted branches:
- mixed promoted power-delta best val loss: `0.131`
- mixed promoted interleaved-attention best val loss: `0.116`
- oneD-only `100k` promoted power-delta best val loss: `0.175`

## What happened in DeepFlame

The result is a useful failure.

The case:
- wrote `1e-07`
- turned on learned chemistry at `2e-07`
- then failed in HP reconstruction during thermodynamic correction

So scaling the oneD/Xiao chemistry dataset by itself did **not** produce a better standalone deployment path.

In fact, it is worse than the earlier small oneD smoke result that had survived to `1e-6`.

## Why this matters

This narrows the role of the oneD/Xiao path.

It still looks valuable, but less as a pure standalone chemistry-label source and more as:
- a solver-native manifold backbone
- an augmentation source
- a component of a mixed dataset

That is an important distinction.

The project is not learning that oneD/Xiao data is useless.
It is learning something sharper:

> more oneD chemistry support alone is not enough to solve the C2H4 deployment problem.

## What I think this means next

The right next move is not another pure oneD-only scale-up.

The better next target is:
- go back to the **mixed-data regime**
- use the improved oneD/Xiao path there
- and test whether promoted attention / interleaved attention can use that richer chemistry support without triggering the early HP failures of the standalone path

So this is a negative result, but a productive one:

**the scalable oneD/Xiao path is real, but it probably needs to be mixed with case-aligned support rather than used alone.**
