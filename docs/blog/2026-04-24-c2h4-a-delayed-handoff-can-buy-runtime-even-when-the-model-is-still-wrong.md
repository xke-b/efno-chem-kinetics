# C2H4: a delayed handoff can buy runtime even when the model is still wrong

_Date: 2026-04-24_

I tested the next practical idea after the enthalpy-rollout failure localization: don’t let the learned branch start from time zero.

Instead, keep stock chemistry early and hand off to the learned enthalpy-regularized branch later.

## What happened

Two simple delayed-switch cases reached `1e-06`:
- switch at `3e-07`
- switch at `5e-07`

That matters because the fully learned enthalpy branch failed before `1e-06`.

## What this does and does not mean

This is not a chemistry-accuracy victory.
The learned branch is still quantitatively poor right after takeover.

But it is still useful evidence:
- a deployment-side guard/hybrid policy is real
- later handoff looks safer than earlier handoff
- survival and chemistry fidelity still need to be judged separately

So the lesson is:

> a delayed handoff can buy runtime, but it does not by itself make the chemistry correct.

That is still progress, because it shows that scheduling is a real control axis for C2H4 deployment rather than just a workaround fantasy.
