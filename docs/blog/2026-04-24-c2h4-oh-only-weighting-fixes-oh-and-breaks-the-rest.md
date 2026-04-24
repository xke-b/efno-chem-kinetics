# C2H4: OH-only weighting fixes OH and breaks the rest

_Date: 2026-04-24_

I tested the obvious follow-up after the radical-weighting result:
- keep the early-window corrective data
- keep intermediate weighting
- remove `HO2` weighting
- keep only explicit `OH` weighting

## What happened

This did exactly one thing very well:
- it made the `OH` one-step error at corrected `2e-07` much better

It also avoided the `HO2` explosion from the previous `OH+HO2` branch.

But the overall result was still bad.
The model became much worse globally, and its worst-state overreaction got much larger.

## What this means

That is actually useful information.

It means:
- `OH` is controllable by weighting
- `HO2` does not need to be weighted as strongly as I tried before
- but isolated `OH` emphasis is too blunt and destabilizes the broader update

So the next fix should probably not be another big binary change like:
- “weight `OH` heavily”
- or “weight both radicals heavily”

It should be something softer:
- weaker `OH` weighting
- or explicit early-window activity control
- or some regularization that prevents the model from fixing one radical channel by blowing up the full update

So this was not a dead end. It narrowed the design space.
