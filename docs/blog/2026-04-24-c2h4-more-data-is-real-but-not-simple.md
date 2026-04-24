# More C2H4 data matters — but not in a simple scaling-law way

_Date: 2026-04-24_

I tested the most direct version of the “try more data” idea on the current best early-window `dp100` dataset.

Instead of the capped `50000`-row training set, I regenerated the same early-window `|Δp| <= 100 Pa` case-pair dataset without the per-pair cap. That produced a `105362`-row dataset, about `2.1x` larger.

The result is genuinely informative.

The larger-dataset model runs to `5e-6`, and some broad solver-facing metrics improve: the pressure tail narrows and mean `|ΔT|` drift decreases.

But it does not just keep improving in one direction. The mean `Qdot` swings past the earlier over-energetic regime into negative territory, and the temperature minimum slips below the clean floor held by the smaller `dp100` baseline.

So the takeaway is:
- yes, data scale clearly matters here
- no, it is not just a smooth “more data = better model” story

The dataset is powerful enough to move the learned regime, but we still have to control *what* data are being scaled, not only *how much*.
