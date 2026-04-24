# C2H4: the bulk heat release goes wrong by `3e-7`

_Date: 2026-04-24_

I followed up the first deployment scout by checking **when** the early-window intermediate branch actually leaves the CVODE trajectory in bulk heat release.

The answer is: **much earlier than `1e-6`**.

## What I found

For the deployed early-window intermediate branch:
- at `2e-7`, bulk `Qdot` is still fairly close to CVODE
- by `3e-7`, it has already moved into the wrong bulk regime
- by `5e-7`, the hot bulk is strongly overdriven
- by `1e-6`, the late failure is just the continuation of that earlier divergence

So the bad late behavior is not a sudden event. It starts early.

## The more important part

I also checked the model against CVODE on the **states it is actually visiting** at `3e-7` and `5e-7`.

That matters because I wanted to know whether the problem was only rollout drift, or whether the local one-step chemistry was already bad too.

The answer is: by `3e-7`, the local one-step behavior is already poor in the important channels.

Especially:
- `C2H3`
- `CH2CO`
- and the total update magnitude in the worst states

So the current deployed branch is not just drifting globally while staying locally fine.
It becomes **locally wrong early**, and then the rollout keeps compounding that.

## What this means for the next fix

This makes the next move clearer.

The next useful fix probably should not be another nearby species-weight tweak.
It should target the early in-loop bulk activity directly, especially in the `2e-7 -> 5e-7` window.

In other words, the next fix should be more about:
- bulk heat-release control
- or enthalpy/activity regularization

and less about one more small weight-profile adjustment.
