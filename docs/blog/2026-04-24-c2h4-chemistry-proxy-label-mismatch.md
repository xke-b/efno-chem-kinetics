# The C2H4 label-semantics problem is now visible in the data itself

_Date: 2026-04-24_

I took the next step after the best-model-vs-stock diagnostic: instead of tuning another dataset ratio, I re-labeled a subset of the current `dp100` case-pair data with one-step Cantera chemistry under a const-pressure reactor assumption.

That gave the first direct measurement of how different the current full-CFD labels are from a chemistry-only proxy target.

The answer is: materially different.

On a 5k-row subset:
- mean absolute `T_next` difference is about `65 K`
- the original CFD labels carry about `22 Pa` mean `Δp`, while the chemistry-only relabel path keeps pressure effectively fixed
- several key intermediates are much larger in the chemistry-only relabel path than in the original CFD targets, including `HCCO`, `CH2CHO`, `CH2OH`, `C2H3`, and `CH2CO`

So the label problem is no longer just an inference from deployment behavior. It is visible in the targets themselves.

That makes the next direction much clearer: the C2H4 program now needs better relabeling and target construction more than another local sweep on the old full-CFD labels.
