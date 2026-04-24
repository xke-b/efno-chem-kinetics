# The first C2H4 FNO-integrated case reaches `9e-7` and then fails during the `1e-6` attempt

_Date: 2026-04-24_

A quick follow-up on the new C2H4 FNO path.

I extended the first copied FNO-integrated C2H4 DeepFlame case beyond the initial `5e-7` smoke horizon.

Result:
- the case completes through `9e-7`
- it then fails during the next step toward `1e-6`

The failure is not a wiring/import/runtime-communication issue.
It is a thermodynamic one:
- `CanteraError ... setState_HPorUV (HP): No convergence in 500 iterations`

That is actually useful progress. It means the first C2H4 FNO bridge is real enough that the main bottleneck has already shifted away from basic integration and toward thermodynamic consistency under the case runtime.

A useful pre-failure sign is that the learned active-set count drops sharply just before failure:
- `7e-7`: `33630`
- `8e-7`: `10200`
- `9e-7`: `5346`

So the next questions are now sharper:
- what in the predicted state is pushing HP reconstruction over the edge?
- how different are the last successful FNO-integrated fields from the stock C2H4 baseline?
- is the next intervention better training data, a guarded fallback path, or both?
