# C2H4 power-delta targets help the bulk — but not the intermediates

I took the next obvious step after adding the proper C2H4 CVODE baseline.

The recent evidence said the main problem was no longer just data support or runtime wiring. It was target semantics, especially for multiscale intermediates.

So I replaced the current species target
- `BCT(Y_next) - BCT(Y_current)`

with a Xiao-style power transform on the physical delta
- `sign(ΔY) * |ΔY|^0.1 / 0.1`

and tested it on the current mixed oneD-backed dataset:
- `dp100 + oneD DeepFlame@0.2`

## First, a real failure happened
The first exported runtime path was wrong.

At the first learned step it hit a shape-mismatch bug in the exported bridge because I was adding a `23`-channel predicted delta to the full `24`-species vector.

That made the run look calm only because the inference path was falling back after an exception.

I fixed the exporter, re-exported, and reran.

That was annoying, but useful: it prevented a false positive.

## What changed after the fix
Against the proper DeepFlame CVODE baseline at `1e-6`, the new power-delta model is **much better on bulk behavior** than the original BCT-delta version.

For the same `dp100 + oneD@0.2` mixed dataset:

- mean active-region `Qdot` ratio vs CVODE
  - old BCT-delta: `8.59x`
  - new power-delta: `8.5e-4x`

- mean active-region `|ΔT|`
  - old: `3.14 K`
  - new: `0.34 K`

- mean active-region `|Δp|`
  - old: `103 Pa`
  - new: `28 Pa`

So the target transform really matters.

## But the key chemistry still collapses
The same bad intermediate channels are still basically gone.

Against CVODE at `1e-6`:
- `C2H5`: `3.1e-09x`
- `C2H3`: `1.5e-14x`
- `CH2CHO`: `8.8e-19x`
- `CH2CO`: `1.1e-10x`

Meanwhile `OH` and `CO2` still look fine.

So the new model is not chemistry-faithful yet. It is more like a **strongly over-damped** surrogate that avoids the old source-term explosion while still erasing the intermediate manifold.

## What I take from this
This is still a good result.

It cleanly separates two problems that were tangled together before:

1. the old target transform was contributing heavily to bad bulk source-term behavior
2. fixing that alone does **not** recover the missing intermediate chemistry

That means the next C2H4 question is sharper now:
- how do we preserve the improved bulk behavior from power-delta targets
- while stopping the intermediate species from collapsing to zero?

That is a better question than just mixing in more data and hoping.
