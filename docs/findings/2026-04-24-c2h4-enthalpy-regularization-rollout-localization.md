# C2H4 enthalpy-regularization rollout localization: better corrected `2e-07` one-step chemistry does not prevent a violent in-loop bulk-heat-release flip by `3e-07`

_Date: 2026-04-24_

## Why this follow-up was needed

The first enthalpy-regularization scout showed a real improvement on the corrected `2e-07` CFD-state vs CVODE one-step benchmark, but the deployed branch still failed before `1e-6`.

That left an important question unresolved:

> Did stronger enthalpy regularization at least delay or soften the early in-loop bulk divergence, or did it only improve the offline one-step slice?

To answer that, I compared the deployed enthalpy-weighted branch against the CVODE baseline at multiple times and placed it directly against the previous intermediate-only deployed branch.

## New rollout artifacts

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_vs_cvode_2e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_vs_cvode_3e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_vs_cvode_5e-07_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_vs_cvode_9e-07_summary.json`

Deployed case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediateweights_enthalpy10_np8`

## Result summary

## `2e-07`: locally cleaner, globally still suspicious

At `2e-07`, the enthalpy-regularized branch looks numerically closer than the previous branch on bulk thermodynamic fields:
- mean `|ΔT|`: `0.0124 K`
- mean `|Δp|`: `1.28 Pa`
- mean `Qdot` ratio: `1.73x`

For comparison, the previous intermediate-only deployed branch had:
- mean `|ΔT|`: `0.186 K`
- mean `|Δp|`: `24.8 Pa`
- mean `Qdot` ratio: `1.20x`

So the enthalpy-weighted branch does look cleaner in some very early aggregate senses.

However, even here the strong-`Qdot` sign mismatch fraction is already high (`0.974`), so this slice is not unambiguously healthy.

## `3e-07`: the bulk regime flips violently in the wrong direction

At `3e-07`, the enthalpy-regularized branch is dramatically worse in bulk heat release than the previous intermediate-only branch.

### Enthalpy-regularized branch
- mean `Qdot` ratio: **`49.2x`**
- mean `|ΔT|`: `0.465 K`
- mean `|Δp|`: `97.1 Pa`
- strong-`Qdot` sign mismatch fraction: `0.855`

### Intermediate-only branch
- mean `Qdot` ratio: **`-0.316x`**
- mean `|ΔT|`: `0.440 K`
- mean `|Δp|`: `25.8 Pa`
- strong-`Qdot` sign mismatch fraction: `0.0427`

This means the new branch does **not** stabilize the early bulk regime. Instead, it replaces the earlier underreactive bulk failure with a violently overreactive one.

## `5e-07`: bulk overreaction remains severe

At `5e-07`, the enthalpy-regularized branch remains badly wrong:
- mean `Qdot` ratio: **`41.4x`**
- mean `|ΔT|`: `3.32 K`
- mean `|Δp|`: `328 Pa`
- strong-`Qdot` sign mismatch fraction: `0.841`

Compared with the previous intermediate-only branch:
- previous mean `Qdot` ratio: `6.31x`
- previous mean `|ΔT|`: `0.995 K`
- previous mean `|Δp|`: `41.8 Pa`
- previous sign mismatch: `0.0679`

So by `5e-07`, the stronger enthalpy regularization is clearly worse in coupled bulk behavior than the original intermediate-only early-window deployment.

## `9e-07`: branch survives longer, but the rollout is badly distorted

The enthalpy-regularized branch writes through `9e-07`, which is farther than some nearby failing branches, but the state is already badly distorted:
- mean `Qdot` ratio: `-30.3x`
- mean `|ΔT|`: `18.9 K`
- mean `|Δp|`: `800 Pa`

So longer survival here does not indicate trustworthy chemistry behavior.

## Species behavior remains incomplete

At the same rollout checkpoints, several important intermediates remain strongly suppressed.

Examples:
- `C2H3` mean ratio remains extremely low:
  - `0.00564x` at `2e-07`
  - `0.00262x` at `3e-07`
  - `0.00214x` at `5e-07`
- `CH2CO` mean ratio is near-zero throughout:
  - `4.24e-06x` at `2e-07`
  - `1.11e-06x` at `3e-07`
  - `2.82e-07x` at `5e-07`

Meanwhile, `OH` stays near the baseline bulk level, which is consistent with a branch that preserves some radical activity while still misrepresenting the key intermediate pathway structure.

## Interpretation

This is an important clarification of the previous enthalpy-regularization result.

### What remains true
- stronger enthalpy regularization improves the corrected `2e-07` one-step CFD-state benchmark
- it is therefore a more promising local training direction than scalar activity matching

### What is now newly clear
- that early one-step improvement does **not** translate into better rollout bulk behavior
- the enthalpy-weighted deployed branch undergoes a **violent bulk-heat-release flip by `3e-07`**
- the failure mode changes character rather than disappearing

So the practical conclusion is:

> The current enthalpy-weighted fix is not a deployment fix. It improves the corrected early one-step slice, but in-loop it pushes the model into a different bulk-activity pathology by `3e-07`.

## Consequence for next steps

This narrows the next useful move:
- do not treat corrected `2e-07` one-step improvement alone as sufficient evidence for deployment promotion
- any next C2H4 fix should be tested immediately with **time-resolved in-loop bulk metrics**
- if enthalpy-aware training is continued, it likely needs either:
  - a more targeted rollout-aware thermo loss, or
  - a deployment-side guard/hybrid policy that explicitly prevents the `3e-07` bulk flip
