# Partial chemistry-proxy relabeling keeps C2H4 alive — but still makes it worse

_Date: 2026-04-24_

I tested the next logical step after the pure chemistry-proxy model crashed early: keep the full `dp100` backbone, but replace only `10%` of its labels with chemistry-proxy relabels.

That did something important: the run survived to `5e-6`.

So preserving the CFD-aligned backbone really does help keep the trajectory on the solver-relevant manifold.

But the result is still not good. The model’s solver-facing quality regresses sharply:
- mean `Qdot` becomes strongly negative
- thermal drift becomes much worse
- the temperature floor drops below the healthier best-mix regime

So this is a useful narrowing result.

It rules out two naive options:
- tiny pure chemistry-proxy replacement
- random partial chemistry-proxy replacement

The next relabeling path now needs to be more selective: **which rows should be relabeled, and in what regime, to improve semantics without damaging the deployment manifold?**
