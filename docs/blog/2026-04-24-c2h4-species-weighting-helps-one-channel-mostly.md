# C2H4 species weighting helps one channel most — but not the whole manifold

I followed the first attention pilot with the next most targeted test:

- keep the power-delta target
- keep the small attention block
- add species-aware loss weights for the worst collapsed intermediate channels

The profile I tried boosted:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`
- `CH2OH`
- `HCCO`

## What happened
This did something real, but not enough.

### Bulk behavior
Compared with the first unweighted attention model, the weighted version pulls the chemistry back toward a safer regime:
- `Qdot` drops a lot
- temperature is slightly better
- pressure is about the same

So weighting helps control the attention pilot’s bulk over-activation.

### Intermediate chemistry
The effect is selective.

The clearest winner is:
- `CH2CHO`

That channel moves up a lot relative to the nearby baselines.

Some channels recover a bit from the first attention pilot getting worse:
- `C2H5`
- `CH2OH`
- `HCCO`

But:
- `C2H3` gives back most of the earlier attention-only gain
- `CH2CO` is still basically collapsed

So this is not a clean fix. It is more like a rebalancing knob that helps some parts of the problem and hurts others less.

## What I take from it
This keeps the attention path alive, but in a narrower form.

What I think now is:
- species-aware weighting is worth keeping
- but a single global profile is not enough
- the next step should probably be **where** attention is applied, not just how much species weighting we add

So the best next follow-up now looks like:
- compare **post-spectral attention** with **interleaved spectral-attention**
- while keeping the better power-delta + species-aware setup as the base
