# C2H4: better one-step chemistry still flipped the bulk rollout by `3e-7`

_Date: 2026-04-24_

The enthalpy-regularized C2H4 branch was the first nearby fix that clearly improved the corrected `2e-07` CFD-state-vs-CVODE one-step benchmark.

That was real progress.

But I followed it with the more important check: what happens in the real rollout?

## What I found

By `3e-07`, the deployed enthalpy-regularized branch had already flipped into a violently wrong bulk heat-release regime.

So this was not a clean deployment improvement.
It was a change in failure mode.

## Why this matters

This is exactly the kind of result that keeps an implementation study honest.
A model can get better on the corrected early one-step slice and still be worse where the coupled solver actually cares.

That means I should not promote branches based on the corrected `2e-07` benchmark alone.
The next C2H4 fix has to be judged immediately with time-resolved in-loop bulk metrics, not just local offline chemistry error.

## Current takeaway

A stronger enthalpy term is more promising than a simple activity penalty.
But the current version still does not control the real bulk rollout.

So the next step should be more rollout-aware or more deployment-aware, not just “more of the same” on the one-step objective.
