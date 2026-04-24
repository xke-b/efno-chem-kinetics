# C2H4 oneD DeepFlame augmentation is real — but the first mixed-label test still doesn’t fix the chemistry

I pushed the new solver-native C2H4 data path one step further.

After building a Xiao-style interpolation + constrained perturbation augmentation on top of the DeepFlame one-dimensional flame manifold, I tested two things:

1. train a model purely from that oneD-augmented labeled dataset
2. mix a small amount of that labeled data into the stronger `dp100` case-pair backbone

## Good news first
The pure oneD-augmented model survives to `1e-6` in the real C2H4 case.

That matters because it means this is not just a pretty data manifold. It can produce a runnable deployed model.

## But the chemistry is still wrong
At `1e-6`, the pure oneD-augmented model still:
- overdrives `Qdot`
- and basically deletes the key intermediate manifold

Species like:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`

collapse toward zero in the written fields.

So the path is solver-usable early, but not chemically faithful enough yet.

## Then I tried the obvious next mix
I built a mixed labeled dataset:
- full `dp100` backbone
- plus `0.2x` add-on from the labeled oneD DeepFlame augmented dataset

This mixed model also survives to `1e-6`.

But it still does **not** rescue the missing intermediate chemistry.
The written means for the same key intermediates remain effectively zero.
And mean `Qdot` is still about `18x` stock.

## What I take from this
This is a useful negative result.

It says the oneD DeepFlame augmentation is probably valuable as a **manifold source**, but not yet as a simple drop-in labeled-data correction when concatenated onto `dp100`.

So the next question is no longer:
- “is oneD DeepFlame augmentation worth using?”

I think the answer to that is yes.

The real next question is:
- how should it be used?

Most likely candidates now are:
- current-state augmentation with different label semantics
- target reformulation for multiscale intermediates
- or a more structured hybrid rather than direct labeled-pair concatenation

That is slower than a clean win, but it is much better than guessing.
