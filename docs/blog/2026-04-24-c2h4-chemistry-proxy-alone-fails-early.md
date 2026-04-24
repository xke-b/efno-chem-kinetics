# Chemistry-proxy labels alone are not enough for C2H4

_Date: 2026-04-24_

I tested the first direct follow-up to the label-semantics hypothesis: train an FNO on a small `5k` chemistry-proxy relabeled subset and run it in DeepFlame.

It failed very early.

The run only wrote through `3e-07` and then crashed during `4e-07` with an HP reconstruction failure. By the last written state, the model had already collapsed far away from the stock manifold:
- mean temperature around `498 K`
- pressure minimum around `18.5 kPa`
- mean `Qdot` strongly negative
- learned active-set count collapsing from `33628` to just `520` at the `4e-07` attempt

This is useful because it sharpens the label-semantics story.

It does **not** say semantics do not matter. It says something more specific:
- semantics matter,
- but a tiny pure chemistry-proxy subset is not enough to preserve the solver-relevant manifold.

So the next target path should probably be a larger or mixed relabeling strategy, not a drop-in replacement with a tiny chemistry-only subset.
