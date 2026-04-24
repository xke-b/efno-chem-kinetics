# C2H4 attention helps some intermediates — but not all

I took the next small architecture step after the power-delta target result:

- keep the same `dp100 + oneD@0.2` mixed dataset
- keep the better power-delta target
- add a **small attention block** on top of the current spectral token path

This was the smallest clean test of the idea that the current FNO scaffold might be too blunt for rare but chemically important intermediate channels.

## What happened
Against the proper CVODE baseline at `1e-6`, the result is mixed.

### Bulk behavior
Compared with the no-attention power-delta model:
- temperature error is basically unchanged
- pressure is a little better
- but `Qdot` gets much larger again

So attention partially reactivates chemistry that the plain power-delta model had over-damped.

### Intermediate chemistry
This is the interesting part.

Some channels move in the right direction by a lot:
- `C2H3`: improved by about five orders of magnitude
- `CH2CHO`: improved by about seven orders of magnitude

But others get worse:
- `C2H5`
- `CH2CO`

So the first attention block is **not** a clean win. It is more like a proof that architecture matters and that attention can move the intermediate manifold, but not yet in a controlled enough way.

## What I take from it
This is still useful.

It means the architecture hypothesis survives in a refined form:
- a naive spectral model can indeed be too blunt
- a small attention block can help some collapsed channels
- but a one-block attention add-on is not yet the right final answer

So the next attention experiments should be sharper, not just bigger.

The most justified follow-ups now look like:
- attention + species-aware weighting
- attention + regime-focused data selection
- or attention placement variants instead of simply stacking more layers
