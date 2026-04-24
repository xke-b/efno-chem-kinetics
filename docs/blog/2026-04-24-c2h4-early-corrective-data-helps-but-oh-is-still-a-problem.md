# C2H4: early corrective data help, but OH is still a problem

_Date: 2026-04-24_

I took the next fix step that the corrected divergence analysis suggested: add explicit **early-window stock data** to the aligned mixed training set and see whether that improves the first bad chemistry slice.

## What I did

I extracted `20k` aligned stock case-pair rows from the earliest C2H4 window:
- `1e-07 -> 2e-07`
- `2e-07 -> 3e-07`
- `3e-07 -> 4e-07`
- `4e-07 -> 5e-07`

Then I added those rows to the aligned `r=0.2` mixed dataset and trained a new:
- power-delta
- attention
- intermediate-weighted

smoke model.

## What improved

The new branch got a better validation result than the previous aligned weighted smoke branch.

More importantly, on the corrected `2e-07` CFD-state-vs-CVODE check:
- global MAE improved
- global RMSE improved a lot
- the worst-state overreaction dropped sharply

So the early corrective data are not pointless. They do help.

## What did not improve enough

The main remaining problem is **OH**.

The new branch still overdrives `OH` badly relative to corrected CVODE at `2e-07`, even though some early intermediate channels improved.

That means the next fix probably should not just be “more early data.”
It should be more like:
- keep the early-window data path
- but add stronger control over radical balance, especially `OH`
- and probably `HO2` as well

## Why this matters

This is exactly the kind of result I want from a fix attempt:
- not a miracle
- not a dead end
- but a clearer indication of what is helping and what is still broken

The current evidence says:
- **early-window corrective data are worth keeping**
- but the next bottleneck is now increasingly a **radical-balance problem**, not just missing early support in general
