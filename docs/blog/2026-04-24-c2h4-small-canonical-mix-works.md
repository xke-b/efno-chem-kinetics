# A small calibrated canonical mix is the best C2H4 data result so far

_Date: 2026-04-24_

I tested the first mixed C2H4 dataset that combines:
- the current best solver-aligned `dp100` case-pair data
- a small paper-inspired canonical augmented component

The mix was chosen from the earlier coverage scout: about a `0.1` canonical/case-pair effective weight ratio.

This is the first result from the canonical-data thread that looks clearly better than both nearby extremes.

At `5e-6`, the mixed model:
- runs cleanly
- keeps a healthy temperature floor
- pulls pressure much closer to stock
- cuts the huge `Qdot` overshoot of the original `dp100` baseline
- and avoids the negative-`Qdot` overcorrection that appeared when I simply scaled the raw `dp100` dataset up to `105k` rows

So the story is getting clearer:
- raw case-pair scaling alone is too blunt
- canonical augmentation alone is too rich
- a **small calibrated mix** is a much better direction than either extreme
