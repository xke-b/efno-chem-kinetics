# The DFODE-kit one-dimensional DeepFlame sampling path for C2H4 is real — and the first staging pass found a real bug

A very useful correction landed today: Xiao et al. (2026) are not just doing abstract canonical-state generation. They start from a **one-dimensional flame simulation**, then augment and transform targets.

That mattered because DFODE-kit already documents almost exactly that workflow.

So instead of only thinking in terms of:
- full CFD case-pair extraction, or
- my own Cantera-only canonical generator,

I checked whether the existing DFODE-kit oneD DeepFlame path actually works for C2H4 with `Wu24sp.yaml`.

## Short answer
Yes.

I initialized a DeepFlame-backed one-dimensional freely propagating premixed C2H4/air flame case, ran it, and sampled it into HDF5.

New case:
- `/root/workspace/runs/dfode_c2h4_oned_flame_phi1`

New sampled artifact:
- `/root/workspace/data/c2h4_dfode_oned_phi1_sample.h5`

That gives us a real DFODE-kit/DeepFlame-native oneD flame manifold for C2H4.

## It also found a real bug
The first staging pass surfaced a genuine DFODE-kit bug in case generation.

In `dfode_kit/cases/deepflame.py`, placeholder replacement used substring matching. That meant:
- the `simTime` replacement also matched the `simTimeStep` line
- so the generated case silently got an absurdly large timestep

That is the kind of bug that can waste a lot of time if nobody notices it.

I fixed it locally and added a regression test.

So this was not just a paperwork step. It improved the actual tooling.

## One more practical issue
The stock `Allrun` also failed in this container because `mpirun` did not include:
- `--allow-run-as-root`

That is a container/runtime issue, not a science issue, and the case ran once launched manually with the root-safe MPI flag.

## Why this matters for the research
This changes the C2H4 forward path in a useful way.

We now have a third serious data source:
- not only full CFD state pairs
- not only Cantera-only canonical flames
- but also **DeepFlame-native one-dimensional flame sampling through DFODE-kit**

That is much closer to the starting point used in Xiao et al. (2026).

So the next C2H4 data-prep question is no longer abstract. We can now ask it on top of a real oneD DeepFlame flame manifold:
- how to interpolate it
- how to perturb it
- how to filter it
- and how to apply low-temperature / scale-separated targets on top of it

That feels like a better next stage than pretending the current case-pair data alone is enough.
