# A simple C2H4 curriculum beats naive early+late mixing, but not the dp100 baseline

_Date: 2026-04-24_

I tested the first structured version of late-data exposure for C2H4.

Instead of concatenating early and late dp100 data into one training set, I took the working early dp100 checkpoint and fine-tuned it briefly on the late dp100 dataset.

That helped.

The curriculum model got much farther than the naive early+late concatenation path:
- naive concatenation failed around `3.4e-6`
- early→late curriculum made it to about `4.5e-6`

So ordering matters. That is real progress.

But it still was not enough. The curriculum model eventually developed a cold/low-pressure tail and failed in HP reconstruction before the target `5e-6` horizon. The pure early dp100 model is still the best current deployment-facing baseline.

So the updated lesson is:
- late chemistry support matters
- naive mixing is too blunt
- curriculum is better than naive mixing
- but the late-stage exposure still needs to be gentler or more selective if it is going to help without breaking thermodynamic stability
