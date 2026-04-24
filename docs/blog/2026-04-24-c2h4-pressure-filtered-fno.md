# A simple pressure filter helps the C2H4 FNO, but it is not enough yet

_Date: 2026-04-24_

I trained and ran the first C2H4 FNO on a pressure-filtered subset of the case-pair labels, using only active pairs with `|Δp| <= 100 Pa`.

This is still not a chemistry-only target. But it is a more chemistry-like subset than the full unfiltered CFD pair set.

Result at `5e-6`:
- the filtered model still runs cleanly with the batched bridge
- its pressure behavior is much better than the unfiltered case-pair FNO
- its mean `Qdot` drops a lot
- its average temperature drift also improves

Most notably, the mean `Qdot` overprediction drops from about `89x` stock in the unfiltered case-pair FNO to about `31.6x` stock in the pressure-filtered one.

That is a real improvement.

But the chemistry gap is still there. Important late intermediates like `C2H5`, `C2H3`, `CH2CHO`, and `CH2CO` remain badly underpredicted or effectively absent.

So this is useful evidence that target refinement matters, but it is also evidence that a simple pressure filter is not enough to recover the missing late chemistry detail.
