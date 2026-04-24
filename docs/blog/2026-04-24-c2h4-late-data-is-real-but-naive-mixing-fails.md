# The missing late C2H4 chemistry is real, but naive early+late mixing fails

_Date: 2026-04-24_

I tested the next deeper C2H4 target-construction question: are the missing late intermediates absent because the current dp100 training window simply does not contain enough late chemistry?

The answer is yes.

A late-window dp100 dataset built from `2e-6 -> 5e-6` contains much stronger coverage of the missing intermediates like `C2H5`, `C2H3`, `CH2CHO`, and `CH2CO` than the original early-window dp100 dataset.

So I then tried the obvious next move: concatenate early dp100 and late dp100 into one training set.

That failed in an informative way.

The combined model trained much worse offline and then crashed in-case around `3.4e-6` with a severe thermodynamic failure. The written `3.3e-6` state already showed a catastrophic cold/low-pressure tail and strongly negative mean `Qdot`.

So the lesson is sharper now:
- the late chemistry support really is missing in the simpler dataset
- but naive regime mixing is not the right fix

That points the next step toward structured regime handling—like curriculum or regime-aware mixing—instead of just concatenating early and late case pairs and hoping for the best.
