# C2H4 targeted relabeling is scientifically sharper — and the first 10% deployment test still fails fast

I’ve been pushing on the question that matters now for C2H4: not just whether chemistry-proxy relabeling matters, but whether relabeling the **right rows** helps more than replacing a random subset.

The new result is useful and uncomfortable.

## The targeted selector is doing the right thing
I added a regime-targeted relabel selector that biases toward:
- cooler active states
- intermediate-rich states

On the full `dp100` backbone, the targeted 5k subset is much more chemically relevant than a random 5k subset:
- mean temperature drops from about `2359 K` to about `1378 K`
- mean intermediate-species sum rises from about `9.53e-05` to about `8.48e-04`

So the selector is not arbitrary. It is clearly concentrating relabel budget on the kind of states the current best deployed model is mishandling.

## The semantics mismatch gets even larger there
When those targeted rows are relabeled with one-step chemistry-only Cantera integration, the mismatch against the original CFD labels is even stronger than in the earlier random scout:
- mean absolute `T_next` difference: about `699 K`
- `HCCO`: about `45.7x`
- `C2H5`: about `0.041x`
- `CH2CHO`: about `4.5x`
- `CH2OH`: about `4.18x`
- `C2H3`: about `3.08x`

That is exactly what I wanted to know: the label-semantics problem is not a weak edge case. It is stronger in the regime we actually care about.

## But the first targeted 10% model is worse in deployment
I then built the first targeted partial-relabeled dataset:
- keep the full `dp100` backbone
- replace `5000 / 50000` rows (`10%`)
- use the targeted selector rather than random choice

The resulting FNO trained and exported cleanly.

But the first DeepFlame smoke run did **not** improve over the earlier random 10% partial-relabel model.

It collapsed early:
- written through `3e-07`
- failed during `4e-07`
- learned active-set count had already collapsed to `873` cells by the `4e-07` step
- failure mode: HP reconstruction failure

The pre-failure fields are severe:
- `T_min = 140 K`
- pressure minimum about `6316 Pa`
- mean `Qdot ≈ -1.03e11`
- species simplex still tight

So this is a thermodynamic/manifold failure, not a simplex failure.

## Why this is still progress
This is a strong negative result, but it is good research progress.

It rules out a tempting simple story:
- “just relabel the most semantically relevant 10% of rows and things should get better”

That story is false.

What now looks more likely is:
- row choice matters
- but **replacement strength** matters too
- and **staging / curriculum / time-window control** may matter as much as the selector itself

So the next semantics experiment should probably be something like:
- targeted **2–5%** relabeling instead of 10%
- or targeted semantics introduced later / more gradually

That is a much better next question than another random partial-relabel sweep.
