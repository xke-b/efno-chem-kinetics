# Mixing broader and filtered C2H4 data helps, but dp100 still wins

_Date: 2026-04-24_

After the over-filtered `dp100 + dT10` dataset failed in the real solver, I tried a different kind of refinement: not a narrower subset, but a mixed dataset.

I built a combined C2H4 training set with:
- the full unfiltered case-pair data
- plus the better-performing `|Δp| <= 100 Pa` subset

That mixed model runs cleanly to `5e-6` and lands where you might expect:
- better than the fully unfiltered model on pressure behavior, temperature drift, and mean `Qdot`
- but still not as good as the pure `dp100` dataset on the main source-term metric

So the mixed dataset is a viable middle ground, but it does not take over as the best current target set. The current `dp100` dataset still remains the strongest single tested option.

That is useful because it says the next step should probably move from hard subset choices to a more deliberate mixed training strategy or weighting scheme, rather than more blind filtering.
