# C2H4 longer training changes the regime — not automatically for the better

_Date: 2026-04-24_

I just finished the first **GPU-trained, validation-aware, longer-budget** promotion run for the current C2H4 power-delta baseline.

This was the right next step because recent web-search evidence made it clear that our earlier `6`-epoch C2H4 runs were only scouting runs, not serious model-quality budgets.

## What changed

I added a real promotion path:
- train/validation split
- best-checkpoint restoration
- reduce-on-plateau LR scheduling
- checkpointed training history
- explicit support for `post_spectral` vs `interleaved` attention placement
- GPU training by default

Then I promoted the plain `power-delta` mixed-data C2H4 model to a `100`-epoch budget on GPU with validation.

## The result

The promoted model was **not** a clean improvement.

### Good news
It did lift several previously collapsed intermediates by many orders of magnitude very early in the run.

Examples at `2e-07` vs CVODE:
- `C2H3`: `4.32e-13x -> 2.08e-08x`
- `CH2CHO`: `2.60e-17x -> 5.47e-09x`
- `CH2CO`: `7.16e-10x -> 7.67e-08x`

So longer training is definitely **doing something real**.

### Bad news
Bulk source-term behavior got much worse.

At `2e-07` vs CVODE:
- old `6`-epoch power-delta: `Qdot` ratio `1.80e-2x`
- promoted `100`-epoch model: `Qdot` ratio **`2.70e+1x`**

So the promoted model swung from a strongly **over-damped** regime into a strongly **over-driven** regime.

That change also hurt deployment robustness:
- the earlier `6`-epoch power-delta case had survived to `1e-6`
- the promoted `100`-epoch validation-aware case failed much earlier in HP reconstruction, after progressing only through the early written times

## Why this matters

This is a useful negative result.

It means the current C2H4 problem is **not** just “train longer and it will fix itself.”

Longer, validation-aware GPU training changes the model behavior a lot — but right now it sharpens a tradeoff:
- better intermediate activity
- worse bulk `Qdot` / thermodynamic behavior
- earlier coupled-case failure

That is much better to know now than after a larger blind promotion sweep.

## What I think this means next

The next serious comparison should stay in the new promoted-training regime, but move to the nearby variants that might balance this tradeoff better:
- power-delta
- power-delta + attention
- power-delta + attention + species weighting
- and especially the unfinished **interleaved-attention** placement test

So the story is now sharper:

> C2H4 longer training is necessary, but budget alone is not the solution. It moves the model into a different regime, and that regime is not automatically more solver-useful.
