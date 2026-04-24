# C2H4 coupled failure is not one problem

_Date: 2026-04-24_

I just ran the deeper analysis that we needed: instead of only watching whether a model survives in coupled CFD, I took the **actual active CFD states** from the C2H4 case just before learned chemistry turns on, then compared each model’s one-step species changes against **one-step CVODE / Cantera chemistry integration** from those exact states.

That ended up being extremely useful.

## The big result

The C2H4 models are **not all failing in the same way**.

There are at least two distinct failure modes.

### 1) Hot-cell overreaction
Some branches — especially the promoted plain power-delta branch and the pure oneD/Xiao `100k` branch — react far too strongly in the hot regime.

The worst hot cells show things like:
- predicted total species change much larger than CVODE
- radical response with the wrong sign
- severe over-amplification of channels like `C2H3`

### 2) Cool-cell underreaction
The promoted mixed **interleaved-attention** branches do the opposite.

Their worst cells are almost entirely in the `510–700 K` active band, where CVODE shows the onset of intermediate formation — but the learned model predicts almost **no chemistry at all**.

That means these models are not exploding in the onset regime. They are **freezing** it.

## Why this matters

This changes the next-step logic a lot.

If all the models failed the same way, then a single architecture or stability fix might be enough.
But that is not the situation.

The evidence now says:
- some branches are too aggressive in hot cells
- some are too conservative in cool onset cells
- so the current C2H4 bottleneck looks more like a **regime-specific data/target mismatch** than one single architecture bug

## My current interpretation

The strongest root cause still looks like the training signal itself:
- pure oneD/Xiao chemistry support alone is not enough
- crude case-pair support alone is not chemistry-clean enough
- uniform mixing between them is too blunt

That explains why changing architecture changes the **shape** of the failure without fully solving it.

## What I think should happen next

The next fixes should be more targeted than another broad sweep.

The best candidates now are:
1. a dedicated **cool-onset CFD-state benchmark** in the `510–700 K` band
2. **regime-selective mixed-data construction** instead of uniform concatenation
3. **species-aware supervision** focused on onset intermediates like:
   - `C2H3`
   - `CH2CHO`
   - `CH2CO`
   - `C2H5`

So this was exactly the kind of diagnosis we needed.

It doesn’t solve the C2H4 problem yet — but it tells us much more clearly **which problem we actually have**.
