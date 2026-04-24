# C2H4: radical weighting helps OH but breaks HO2

_Date: 2026-04-24_

I took the next obvious fix after the early-window corrective-data result: keep the new early stock window in the training set, but add explicit weighting for radical channels, especially `OH` and `HO2`.

## What happened

This was a mixed result, but a useful one.

### Good news
At the corrected `2e-07` CFD-state-vs-CVODE slice:
- global MAE improved
- global RMSE improved
- and the `OH` overshoot was cut by about half

So radical-aware weighting is clearly a real control knob.

### Bad news
It broke `HO2` badly.

The new branch overdrives `HO2` by a huge amount relative to corrected CVODE.
It also does not fix `CH2CO`.

## What I think this means

The important lesson is not that radical weighting failed.
It is that the current **symmetric** `OH` / `HO2` weighting is too blunt.

The model seems to need:
- some explicit `OH` control
- but not such aggressive `HO2` emphasis

So the next fix should be more surgical:
- keep the early-window corrective data
- keep intermediate weighting
- add moderate `OH` emphasis
- reduce or remove `HO2` weighting

That is now the shortest sensible next step.
