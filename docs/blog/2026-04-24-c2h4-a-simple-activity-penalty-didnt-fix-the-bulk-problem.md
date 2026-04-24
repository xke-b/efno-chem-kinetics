# C2H4: a simple activity penalty didn’t fix the bulk problem

_Date: 2026-04-24_

I tried the smallest structured follow-up after the early bulk-divergence analysis: add a training penalty that matches the **total one-step activity magnitude**.

## What happened

Offline, it looked mildly encouraging.
The validation loss improved a bit.

But on the corrected `2e-07` CFD-state-vs-CVODE check, it got worse:
- global error increased
- worst-state overreaction increased a lot
- and the key channels did not improve

## What this means

This is useful because it rules out another tempting shortcut.

A scalar “match the total activity” penalty is too blunt.
It does not actually solve the physically important problem, which is not just how much chemistry happens, but **what kind of chemistry happens and how that affects bulk heat release**.

So the next fix should probably be more physically specific than a generic activity penalty.
That likely means:
- enthalpy / heat-release-aware control
- or an explicit deployment guard before the branch crosses into the wrong bulk regime around `3e-7`
