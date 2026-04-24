# A staged C2H4 model switch works better than running the late-enriched model from the start

_Date: 2026-04-24_

I tested the first concrete regime-aware deployment idea for C2H4.

Instead of running the gentle late-enriched curriculum model from `t=0`, I ran the pure `dp100` model up to `4e-6`, then switched to the gentle curriculum model only for the final `4e-6 -> 5e-6` segment.

That staged switch reached `5e-6` cleanly.

More importantly, it looked much healthier than running the gentle curriculum from the start:
- lower mean `Qdot`
- narrower pressure tail
- much smaller temperature drift

It is still not better than the pure `dp100` baseline, and it still does not rescue the missing late intermediates in a convincing way. But it is strong evidence that **deployment logic** may be a better lever than trying to make one shared model absorb both early and late regimes from the beginning.

So the new lesson is: if late-enriched behavior is only useful late, it may need to be deployed late as well.
