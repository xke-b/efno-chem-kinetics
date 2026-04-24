# C2H4 corrected late-window self-case analysis: by `1e-6`, both the plain power-delta and attention smoke models are locally close to CVODE on their own visited states, which points to state-distribution drift and manifold distortion—not just instantaneous one-step chemistry error—as the main late-stage deployment problem

_Date: 2026-04-24_

## Why this was the right next step

After fixing the C2H4 species-order alignment bug, the next useful question was not another training sweep. It was:

- in the **later pre-failure / pre-extension window** where the smoke models have already evolved far from stock behavior,
- are they still making obviously wrong **one-step chemistry updates** on the states they actually visit,
- or has the main problem shifted to the fact that the coupled solver has already drifted onto the wrong thermochemical manifold?

To answer that, I evaluated the existing smoke-deployed models **on their own written CFD states** at `1e-06`, using corrected species ordering for the Cantera/CVODE reference.

## Corrected self-case one-step analysis artifacts

### Plain power-delta smoke model on its own `1e-06` states
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke.pt`
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_smoke_np8`
- artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_smoke_selfcase_1e-06_vs_cvode_corrected.json`

### Attention smoke model on its own `1e-06` states
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke.pt`
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r0p2_fno_powerdelta_attn1_smoke_np8`
- artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_attn1_smoke_selfcase_1e-06_vs_cvode_corrected.json`

## Main result: on their own late-time states, both smoke models are locally close to corrected CVODE

This is the key result.

### Plain power-delta smoke model
On its own active states at `1e-06`:
- global one-step MAE: **`5.35e-06`**
- global one-step RMSE: **`4.22e-05`**

Active-state summary:
- mean `T`: `2378.53 K`
- mean written `Qdot`: `1.58e5`

Top 1% worst states:
- mean `T`: `1942.85 K`
- mean true one-step `ΔY` L1: `2.82e-03`
- mean predicted one-step `ΔY` L1: `4.27e-07`

Key species mean one-step deltas vs corrected CVODE:
- `C2H3`: `0` vs `2.23e-05`
- `CH2CO`: `~3e-14` vs `4.98e-06`
- `OH`: `5.59e-08` vs `-1.49e-05`

### Attention smoke model
On its own active states at `1e-06`:
- global one-step MAE: **`5.34e-06`**
- global one-step RMSE: **`4.21e-05`**

Active-state summary:
- mean `T`: `2378.61 K`
- mean written `Qdot`: **`1.92e7`**

Top 1% worst states:
- mean `T`: `1943.32 K`
- mean true one-step `ΔY` L1: `2.82e-03`
- mean predicted one-step `ΔY` L1: `3.52e-07`

Key species mean one-step deltas vs corrected CVODE:
- `C2H3`: `2.87e-13` vs `2.21e-05`
- `CH2CO`: `2.76e-13` vs `4.98e-06`
- `OH`: `7.31e-08` vs `-1.59e-05`

## Why this is surprising relative to earlier field comparisons

The earlier field-level comparisons at `1e-06` already showed that the attention smoke case had become chemically distorted relative to stock/CVODE fields:
- it preserved bulk `OH`, `CO`, and `CO2` reasonably
- but it severely suppressed intermediate species such as `C2H5`, `C2H3`, `CH2CHO`, `CH2CO`, `CH2OH`, `HCCO`
- and its written `Qdot` behavior remained strongly off relative to stock/CVODE

That earlier evidence remains valid.

But the new corrected self-case analysis adds a more specific interpretation:

> By `1e-6`, the model can be locally close to CVODE **on the states it has already drifted onto**, while those states are themselves chemically wrong relative to the stock/CVODE trajectory.

In other words, the deployment problem is not only “the one-step operator is bad everywhere.” It is also:
- the surrogate steers the simulation onto the wrong manifold,
- then behaves locally almost self-consistently around that wrong manifold,
- while intermediate chemistry and heat-release structure remain globally distorted.

## Strongest evidence for manifold drift as the late-stage problem

Compare these two facts for the attention smoke model at `1e-06`:

### Fact A — local one-step checkpoint-vs-CVODE error on self states is small
- global RMSE: `4.21e-05`

### Fact B — field-level chemistry distortion relative to stock is still severe
From the existing `1e-06` stock-vs-model summary:
- mean active-region `Qdot` ratio vs stock/CVODE: **`0.103x`**
- `C2H5` mean ratio: **`2.45e-15x`**
- `C2H3` mean ratio: **`2.61e-09x`**
- `CH2CO` mean ratio: **`2.04e-12x`**
- strong-`Qdot` sign mismatch fraction: **`0.804`**

So the surrogate is not simply failing because every local chemistry step is grossly wrong on the states it currently sees. Instead, the coupled rollout has already moved onto a state distribution whose intermediate composition / heat-release structure is globally inconsistent with the stock trajectory.

## What this says about the current failure mode

This changes the most useful diagnosis again, in a narrower and more precise way.

### The plain power-delta branch
Still clearly problematic:
- even after the alignment fix, its earlier hot-radical overreaction signal remained real on stock states
- on its own late states, it is also locally too inactive in the worst hot region

### The attention smoke branch
The attention smoke branch now looks different from the earlier simplified story.

At `1e-06`, it is **not** best described as catastrophically wrong on every local one-step update. Instead:
- it has already drifted into a globally distorted manifold with collapsed intermediates
- but once there, the one-step update against corrected CVODE on that manifold is relatively small

That means the main remaining problem is likely **trajectory/distribution error accumulated over rollout**, not only per-step supervised error on late visited states.

## Updated takeaway

The corrected late-window result is:

> For the C2H4 smoke models, especially the attention branch, the important late-stage failure mode is increasingly consistent with **manifold drift under rollout**: the surrogate visits the wrong thermochemical states, and those states carry wrong intermediate chemistry and heat-release structure, even though the local one-step chemistry error computed on those already-drifted states can be modest.

## Most useful next step now

The next high-value diagnostic is no longer just another static one-step comparison. It should be a **corrected trajectory-divergence analysis** over time, asking:
- when do the model trajectories first separate materially from stock in intermediate-species space,
- and which channels drift first before the large field-level `Qdot` mismatch becomes obvious?

That is the right next thread for deciding whether to prioritize:
- rollout-aware retraining on aligned data,
- trajectory-local correction data near the first divergence window,
- or deployment-side guards that intervene before the manifold drift becomes unrecoverable.
