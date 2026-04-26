# C2H4: the safe handoff window looks real and narrow

_Date: 2026-04-24_

I followed the first delayed-switch guard scout with a tighter local sweep around the promising `5e-07` handoff.

## What happened

- `4e-07` failed
- `5e-07` survived
- `6e-07` survived and actually looked better than `5e-07` at `1e-06`
- `7e-07` was not a clean improvement and was killed before producing a useful learned continuation

## Why this matters

This means the deployment-side scheduling effect is real, but it is not a vague “later is always better” story.
There seems to be a **narrow operational window** where this branch can take over without immediately ruining the run.

Right now, `6e-07` looks like the best fixed-time handoff I have tested for the enthalpy-regularized branch.

## Important caveat

This is still not a chemistry-fidelity win.
The first learned step after takeover is still quantitatively poor.

So the result is narrower:
- scheduling is a real control axis
- the safe region is narrow
- and the current branch is still better described as guardable than fully trustworthy
