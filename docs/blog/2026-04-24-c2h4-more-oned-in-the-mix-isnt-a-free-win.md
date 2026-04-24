# C2H4: more oneD in the mix isn’t a free win

_Date: 2026-04-24_

After the negative result on the standalone `100k` oneD/Xiao chemistry model, the next obvious question was whether the oneD chemistry support works better as a **bigger supplement** to the case-aligned `dp100` backbone.

So I tried the direct version of that idea:
- keep `50k` `dp100` rows
- add `50k` oneD/Xiao labeled rows
- train a promoted **interleaved-attention** model on the full `100k` mixed dataset

## What happened offline

The result was not encouraging.

Best validation losses:
- mixed `dp100 + oneD@0.2` promoted interleaved attention: `0.116`
- larger mixed `dp100 + oneD@1.0` promoted interleaved attention: **`0.156`**

So simply turning up the oneD chemistry fraction made the promoted mixed model **harder to fit**, not easier.

## What happened in DeepFlame

The deployed case:
- wrote `1e-07`
- turned on learned chemistry at `2e-07`
- then failed in HP reconstruction again

So the larger oneD supplement did **not** rescue early deployment stability either.

## What this means

This is another useful narrowing result.

It says the issue is probably **not**:
- “just add more oneD chemistry and the mixed model will improve”

Instead, the problem looks more structured:
- too little oneD support does not fix chemistry
- much more oneD support does not automatically help and can hurt
- the next move should probably be **smarter mixing**, not just **more mixing**

That points toward things like:
- regime-selective mixing
- species-aware supervision
- or narrower oneD-ratio neighborhoods with better architecture/loss choices

So the role of the oneD/Xiao path is getting clearer:

**valuable, yes — but not something we can just scale up uniformly inside the mixed dataset and expect a free win.**
