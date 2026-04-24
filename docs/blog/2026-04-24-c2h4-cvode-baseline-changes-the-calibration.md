# The proper C2H4 CVODE baseline changes the calibration

I stopped comparing the recent C2H4 runs only against other learned models and added the more important baseline:

- same DeepFlame case
- same Wu24sp mechanism
- same `np=8` stock-style setup
- but with `TorchSettings { torch off; }`

So this is now a real in-loop DeepFlame chemistry reference for the `1e-6` horizon.

## What it says
The answer is pretty clear.

The stock DeepFlame learned example is **much closer to CVODE** than the current project C2H4 surrogates.

At `1e-6`, against CVODE:

### Stock DeepFlame learned model
- mean active-region `Qdot`: about `0.48x` CVODE
- mean active-region `|ΔT|`: about `1.6 K`
- key intermediate ratios stay in the right ballpark:
  - `C2H5`: `0.77x`
  - `C2H3`: `0.67x`
  - `CH2CHO`: `0.94x`
  - `CH2CO`: `1.21x`

### Pure oneD-augmented FNO
- mean active-region `Qdot`: about `8.4x` CVODE
- mean active-region `|ΔT|`: about `11.1 K`
- and it still wipes out the intermediate manifold:
  - `C2H5`: `0.0x`
  - `C2H3`: `3.7e-09x`
  - `CH2CHO`: `6.8e-12x`
  - `CH2CO`: `9.7e-09x`

### `dp100 + oneD@0.2`
- a bit better on bulk thermodynamics than pure oneD augmentation
- but still not chemically right where it matters
- the same intermediate species are still essentially zero

## Why this matters
This is the useful part of a negative result: it improves the calibration.

Before this, it was too easy to say:
- the oneD DeepFlame manifold is more physical
- the model survives to `1e-6`
- so maybe the chemistry is getting closer

The CVODE baseline says: **not yet**.

What the current models are doing is more specific:
- keeping some bulk fields superficially plausible
- while failing badly on the multiscale intermediate chemistry that actually matters for source terms

## What I think now
This makes the next bottleneck much clearer.

The dominant C2H4 problem is not just:
- runtime wiring
- or current-state support
- or “not enough oneD data”

It is much more likely:
- **target semantics / target formulation for multiscale intermediates**

That makes the Xiao-style power-delta / scale-separated target direction more justified than another naive data mix.
