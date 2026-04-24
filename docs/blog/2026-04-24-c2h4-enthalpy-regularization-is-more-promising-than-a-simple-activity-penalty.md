# C2H4: enthalpy regularization is more promising than a simple activity penalty

_Date: 2026-04-24_

I followed the failed activity-penalty attempt with a more physical version of the same idea: strengthen the enthalpy-consistency term that already exists in training.

## What happened

This was the first structured regularization result in this neighborhood that looks genuinely promising offline.

At the corrected `2e-07` CFD-state-vs-CVODE check:
- global MAE improved a lot
- global RMSE improved a lot
- the worst-state overreaction dropped

So this is clearly a better direction than the scalar activity penalty.

## But the deployment result is still not good enough

When I staged the enthalpy-regularized branch in the real DeepFlame case:
- it ran farther than the failed radical-weighted branch
- but it still failed before `1e-6`
- and by `5e-7` its bulk heat release was still badly wrong relative to CVODE

So the current conclusion is not “enthalpy fixed it.”
It is narrower:

> enthalpy-aware regularization is a more promising control direction than scalar activity matching, but the current simple version is still not enough to keep the coupled bulk heat release sane.

That is still useful progress, because it reduces uncertainty about which class of fixes is worth continuing.
