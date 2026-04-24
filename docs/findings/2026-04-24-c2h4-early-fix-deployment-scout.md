# C2H4 early-fix deployment scout: the alignment-fixed early-window intermediate branch runs cleanly to `1e-6` but badly distorts bulk heat release in-loop, while the stronger radical-weighted branch crashes at the first learned step despite better corrected one-step offline metrics

_Date: 2026-04-24_

## Why this was the right next step

After the nearby weighting/fix sweep, continuing to look only at corrected `2e-07` one-step metrics was no longer enough.

The next deployment-facing question was:
- which of the nearby branches actually behaves better **in the real C2H4 DeepFlame loop**?

I therefore staged and tested two deployment candidates built from the same early-window corrective dataset:
1. the more balanced **intermediate-only** early-window branch
2. the stronger **intermediate + `OH` + `HO2`** radical-weighted branch that looked best on corrected `2e-07` global MAE/RMSE offline

## Tooling fix encountered along the way

While staging these cases, I found a bug in the scheduled-switch case generator when using `switch_time = 0`.

### Problem
The generator only removed written times satisfying:
- `time > switch_time`
- and `time <= end_time`

So when copying a source case that already had times beyond `end_time`, old later time directories remained in place and polluted the staged case.

### Fix
Updated:
- `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`

It now removes **all** time directories later than `switch_time`, which is the right behavior for a clean restart/staged case.

## Staged deployment cases

### Early-window intermediate-only branch
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediateweights_np8`
- bundle:
  - `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediateweights_smoke_deepflame_bundle/`

### Early-window intermediate + radical branch
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediate_radicalweights_np8`
- bundle:
  - `/root/workspace/artifacts/models/c2h4_r0p2_aligned_plus_stockearly20k_fno_powerdelta_attn1_intermediate_radicalweights_smoke_deepflame_bundle/`

Both were staged from:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`

with:
- `switch_time = 0`
- `end_time = 1e-6`

## Result 1: the intermediate-only early-window branch runs cleanly to `1e-6`

The intermediate-only case ran successfully through:
- `1e-07` ... `1e-06`

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediateweights_np8`

Run evidence:
- `solver.err` is empty
- `run.log` ends cleanly

### Matched comparison to CVODE at `1e-6`
Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_aligned_early20k_intermediate_vs_cvode_1e-06_summary.json`

This is where the important negative result appears.

#### Bulk behavior becomes badly wrong
At `1e-6` vs CVODE:
- mean `Qdot` ratio: **`-44.96x`**
- mean `|ΔT|`: **`23.0 K`**
- mean `|Δp|`: **`595 Pa`**
- strong-`Qdot` sign mismatch fraction: `0.332`

So even though the branch survives to `1e-6`, it does **not** remain physically close to the CVODE reference in-loop.

#### Intermediate species improve relative to the older attention smoke branch
Compared with the older attention smoke branch at `1e-6`, the new early-window branch is much less collapsed in several key channels:
- `C2H5` ratio: `8.88e-02` vs old `2.45e-15`
- `C2H3` ratio: `9.92e-03` vs old `2.61e-09`
- `CH2CHO` ratio: `2.95e-01` vs old `8.79e-12`
- `CH2CO` ratio: `1.87e-03` vs old `2.04e-12`
- `HO2` ratio: `3.92e-01` vs old `1.53e-01`

So the early corrective data **do** improve intermediate preservation in-loop.

But the bulk heat-release behavior becomes dramatically worse.

## Result 2: the stronger radical-weighted branch crashes at the first learned step

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_r0p2_aligned_plus_stockearly20k_attn1_intermediate_radicalweights_np8`

Written times:
- `0`
- `1e-07`
- `2e-07`

Then it fails with:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP)`
- `No convergence in 500 iterations`

The failure occurs at the first learned step after `1e-07`.

This is especially informative because offline, that branch looked stronger on the corrected `2e-07` CFD-state benchmark than the intermediate-only branch.

So we now have a direct deployment-facing mismatch:

> Better corrected one-step early-slice metrics did not translate into better in-loop robustness. The stronger radical-weighted branch actually fails sooner.

## Interpretation

This deployment scout is extremely useful because it breaks a local-optimization illusion.

### What survives from the earlier offline work
- early-window corrective data do matter
- they can reduce early one-step errors
- they can revive several collapsed intermediate channels in-loop

### What the deployment scout adds
- the branch with the better-balanced weighting survives, but can badly distort **bulk heat release**
- the branch with better corrected early-slice MAE/RMSE can still fail **immediately** in the real solver

So the project is now facing a more precise tradeoff:
- **chemistry-pathway preservation** improved
- but **thermodynamic / enthalpy consistency under coupled rollout** remains a severe limiter

## Current takeaway

The strongest current conclusion is:

> The C2H4 problem is no longer just intermediate collapse. The first alignment-fixed early-window deployment branch shows that we can recover significant intermediate support and still make the bulk heat-release behavior much worse in-loop, while the stronger radical-weighted branch fails immediately with HP reconstruction errors.

## Most justified next step

The next fix should now be more deployment-aware than the recent pure weight sweeps.

The most promising next actions are:
1. add a **bulk activity / enthalpy consistency control** rather than more channel weighting alone
2. analyze the successful but distorted intermediate-only deployment case at early written times (`2e-07`, `3e-07`, `5e-07`) to see when bulk `Qdot` flips into the wrong regime
3. avoid assuming that the best corrected one-step MAE branch is the best deployment candidate without an actual in-loop test
