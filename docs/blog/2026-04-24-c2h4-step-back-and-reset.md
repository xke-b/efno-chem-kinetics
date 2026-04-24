# Stepping back on C2H4: the next bottleneck is not another mix ratio

_Date: 2026-04-24_

I agree that the recent C2H4 mix-ratio sweeps were starting to produce diminishing returns.

They were useful up to a point: they established that calibrated canonical enrichment helps, and that the current best tested region is around `dp100 + canonical@0.2`.

But the next important question is no longer “what is the next nearby ratio?”

It is:
- what deployment-facing error structure remains in the current best model,
- and how much of that comes from the fact that the current labels are still full-CFD transitions rather than chemistry-isolated targets?

So I’m resetting the priority stack:
- freeze `dp100 + canonical@0.2` as the current C2H4 data baseline
- stop treating local ratio hill-climbing as the main thread
- move next to a best-model-vs-stock diagnostic and then to better label semantics
