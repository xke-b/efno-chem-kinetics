# A gentler C2H4 curriculum finally survives to `5e-6`, but it is not better than dp100

_Date: 2026-04-24_

I tested a much weaker late-stage curriculum for C2H4:
- start from the working early dp100 checkpoint
- fine-tune on late dp100 data
- but only for one epoch and at a much smaller learning rate

That worked in one important sense: it survived to `5e-6`.

So the late-data path is not fundamentally impossible. The strength of the curriculum matters a lot.

But the result is still not a true upgrade over the pure dp100 baseline. The gentle curriculum reached the horizon while giving back a lot on pressure spread, mean `Qdot`, and temperature drift, and it still did not recover the missing late intermediates in a convincing way.

So the lesson is now very specific:
- strong late adaptation breaks too early
- gentle late adaptation can survive
- but survival alone is not enough, because the model quality still regresses relative to the simpler dp100 baseline

That points the next step away from more blunt LR tuning and toward more selective late-stage objectives or regime-aware deployment logic.
