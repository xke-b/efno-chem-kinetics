# C2H4: a better early-slice model can still fail in the real solver

_Date: 2026-04-24_

I moved the latest C2H4 fix branches out of the offline loop and back into the real DeepFlame case.

That was the right move, because it exposed something important:

- the more balanced early-window branch can run cleanly to `1e-6`
- but its bulk heat-release behavior becomes badly wrong in-loop
- and the stronger radical-weighted branch, which looked better on corrected early-slice one-step metrics, actually crashes at the first learned step

## Why this matters

This is exactly the kind of trap it is easy to fall into if I keep looking only at offline corrected `2e-07` metrics.

A branch can look better on the early benchmark and still be worse where it actually counts: inside the solver.

## What I learned

### 1) Early corrective data do help some chemistry channels
The early-window branch preserves several intermediate species much better than the older attention smoke branch.
So that part was real.

### 2) Better intermediates do not guarantee better bulk thermodynamics
The same branch that preserves more intermediates can still drive bulk `Qdot` badly off the CVODE reference.

### 3) Better early one-step MAE still does not guarantee in-loop robustness
The stronger radical-weighted branch looked better offline at the corrected early slice, but it crashed immediately with an HP reconstruction failure.

## What I think the project needs next

At this point I do not think another nearby species-weight sweep is the main answer.
The next useful fix probably has to be more deployment-aware, especially around:
- bulk activity control
- enthalpy consistency
- and how to stop the model from preserving some chemistry while still pushing the solver into thermodynamic trouble

So this was a very useful step.
It showed that the current bottleneck is no longer just “revive the missing intermediates.”
Now it is also very clearly about **keeping the coupled thermodynamics sane while doing that**.
