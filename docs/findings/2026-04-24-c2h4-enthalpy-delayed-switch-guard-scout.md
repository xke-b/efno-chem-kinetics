# C2H4 enthalpy delayed-switch guard scout: a simple deployment-side delayed handoff lets the enthalpy-regularized branch reach `1e-6`, but the coupled chemistry remains quantitatively poor

_Date: 2026-04-24_

## Why this was the next step

The rollout-localization result for the enthalpy-regularized branch showed:
- corrected `2e-07` one-step chemistry improved substantially
- but the fully learned rollout flipped into a violent bulk-heat-release error by `3e-07`

That made the next useful question deployment-side rather than training-side:

> Can a simple delayed handoff keep the solver in a safer regime long enough to extend runtime, even if the learned chemistry is not yet quantitatively trustworthy?

This is effectively a first **guard / hybrid policy scout** using stock chemistry early and the enthalpy-regularized learned branch later.

## Staged delayed-switch cases

Using the completed stock C2H4 run as the source case and the enthalpy-regularized bundle as the learned branch, I staged two delayed-handoff cases.

### Switch at `3e-07`
Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch3e-07_np8`

### Switch at `5e-07`
Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch5e-07_np8`

Both were generated with:
- `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`

## Runtime result

Both delayed-switch cases reached:
- **`1e-06`**

This is important because the fully learned enthalpy-regularized case failed before `1e-06`, while these simple deployment-side guards did not.

So the guard idea is operationally real.

## Comparison artifacts

### Final-time comparisons
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch3e-07_vs_cvode_1e-06_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch5e-07_vs_cvode_1e-06_summary.json`

### First learned-window comparisons
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch3e-07_vs_cvode_4e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch5e-07_vs_cvode_6e-07_summary.json`

## Final-time (`1e-06`) result: delayed switching helps survival and some bulk metrics

## Baseline for comparison
The earlier always-learned intermediate-only deployment at `1e-06` had:
- mean `Qdot` ratio: `-44.96x`
- mean `|ΔT|`: `23.03 K`
- mean `|Δp|`: `595 Pa`

## Switch at `3e-07`
At `1e-06`:
- mean `Qdot` ratio: **`-17.13x`**
- mean `|ΔT|`: **`16.22 K`**
- mean `|Δp|`: **`178 Pa`**

This is still poor, but substantially less bad than the earlier always-learned intermediate-only deployment on bulk thermodynamic fields.

Intermediate preservation also improves somewhat:
- `C2H3` mean ratio: `0.056x`
- `CH2CO` mean ratio: `0.0263x`

## Switch at `5e-07`
At `1e-06`:
- mean `Qdot` ratio: **`-12.31x`**
- mean `|ΔT|`: **`6.49 K`**
- mean `|Δp|`: **`218 Pa`**

This is the best of the three on `Qdot` and temperature error.

Intermediate preservation improves further:
- `C2H3` mean ratio: `0.113x`
- `CH2CO` mean ratio: `0.276x`

So later handoff appears safer than earlier handoff for this branch family.

## But first learned-step behavior is still quantitatively bad

The delayed-switch cases survive, but the first learned window after handoff is already poor.

## `3e-07 -> 4e-07` handoff
At `4e-07` for the `3e-07` switch case:
- mean `Qdot` ratio: `-3.20x`
- mean `|ΔT|`: `1.44 K`
- mean `|Δp|`: `23.0 Pa`
- strong-`Qdot` sign mismatch fraction: `0.822`

## `5e-07 -> 6e-07` handoff
At `6e-07` for the `5e-07` switch case:
- mean `Qdot` ratio: `8.29x`
- mean `|ΔT|`: `2.41 K`
- mean `|Δp|`: `64.7 Pa`
- strong-`Qdot` sign mismatch fraction: `0.820`

So the deployment guard extends runtime, but it does not make the learned chemistry accurate immediately after takeover.

## Interpretation

This is a useful partial success.

### What worked
- a simple delayed handoff is enough to let the enthalpy-regularized learned branch reach `1e-06`
- later switching (`5e-07`) is safer than earlier switching (`3e-07`)
- delayed switching also improves several final-time bulk metrics relative to the earlier always-learned intermediate-only deployment

### What did not work yet
- the learned branch is still quantitatively poor in its first active window after takeover
- strong-`Qdot` sign mismatch remains very high (`~0.82`) after both delayed handoffs
- the delayed-switch policy is therefore a **runtime stabilizer**, not yet an accurate chemistry deployment solution

## Current takeaway

This is the first clear evidence in the current C2H4 enthalpy branch family that a **deployment-side guard / hybrid policy can buy meaningful runtime** even when the learned model is not yet good enough to run from the start.

That narrows the next step:
- deployment-side scheduling is now worth treating as a real control axis
- but it must be evaluated jointly with chemistry fidelity, not only survival

## Best next step

The next useful deployment-facing refinement is likely:
- a small sweep in the delayed-handoff neighborhood around `5e-07`
- or a state-conditioned handoff instead of a fixed-time handoff

because the current evidence suggests that **later, safer activation** is real, but the branch still needs tighter control when it first takes over.
