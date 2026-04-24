# DeepFlame H2 fallback-policy scout: HP-failure fallback alone is too weak, but a simple `|ΔT|` guard could conservatively intercept thousands of risky Burke cells

_Date: 2026-04-23_

## Why this was the next step

The HP-risk analysis showed that many DNN-active Burke cells are already thermodynamically unreconstructable at the next learned update.

That immediately suggested the next practical question:

> If we add a simple deployment-side safeguard, how large is the risky subset that would need fallback?

This is not yet a solver patch. It is a policy-sizing step to estimate whether a guarded hybrid strategy is plausible.

## Added helper script

- `/root/workspace/scripts/summarize_deepflame_h2_fallback_policy.py`

Artifacts used:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_mlp_hp_risk_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hp_risk_2e-06.json`

Output:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/fallback_policy_summary.json`

## Candidate safeguard policies considered

1. **Fallback on outright HP failure**
   - if Cantera HP reconstruction fails, use CVODE instead of the learned update

2. **Fallback on temperature guard**
   - if reconstructed next temperature is outside a safe band, e.g. `T_next < 300 K` or `T_next > 4000 K`, use CVODE

3. **Fallback on `|ΔT|` guard**
   - if `|T_next - T_current| > 500 K`, use CVODE

## What the existing HP-risk analysis implies

### Burke supervised
At `2e-06`:
- DNN-active cells: `8670`
- outright HP failures: `927` (`10.69%` of active cells)

Among the **successful** HP reconstructions:
- fraction with `T_next < 300 K`: `1.60%`
  - about `124` cells
- fraction with `|ΔT| > 500 K`: `36.12%`
  - about `2797` cells
- fraction with `|ΔT| > 1000 K`: `15.10%`
  - about `1169` cells

### Burke corrected self-rollout
At `2e-06`:
- DNN-active cells: `9161`
- outright HP failures: `1263` (`13.79%` of active cells)

Among the **successful** HP reconstructions:
- fraction with `T_next < 300 K`: `3.63%`
  - about `287` cells
- fraction with `|ΔT| > 500 K`: `37.30%`
  - about `2946` cells
- fraction with `|ΔT| > 1000 K`: `21.61%`
  - about `1707` cells

## Main interpretation

### 1. Fallback on outright HP failure is necessary, but not sufficient
A minimal hybrid policy that only catches explicit HP failures would reroute:
- `927` Burke supervised cells
- `1263` Burke corrected-self-rollout cells

That would remove the cells that definitely crash the reconstruction.

But the HP-risk analysis also shows that many cells that technically reconstruct still imply thermodynamically extreme updates.

So HP-failure fallback alone is probably too weak if the goal is not only to avoid immediate exceptions but also to avoid marching toward the next pathological state.

### 2. A `|ΔT|` guard is much more powerful than a simple low-temperature guard
A low-temperature guard like `T_next < 300 K` only catches a small extra subset:
- about `124` additional supervised cells
- about `287` additional corrected cells

By contrast, a `|ΔT| > 500 K` guard catches thousands of successful-but-extreme reconstructions:
- about `2797` supervised cells
- about `2946` corrected cells

That suggests `|ΔT|` is the more useful first deployment-side safety signal.

### 3. The guarded subset is large but still minority-sized
A rough count using:
- outright HP failures
- plus successful reconstructions with `|ΔT| > 500 K`

would conservatively flag on the order of:
- supervised: `927 + 2797 ≈ 3724` cells
- corrected self-rollout: `1263 + 2946 ≈ 4209` cells

out of about `8.7k–9.2k` DNN-active cells at `2e-06`.

So a guarded hybrid strategy would still leave a substantial subset of DNN-active cells using the learned model, while routing the most dangerous subset to a safer fallback.

## Bottom line

This scouting step suggests a realistic first stabilization experiment:
- **CVODE fallback on outright HP failure** should be the minimum safeguard
- adding a **`|ΔT| > 500 K` guard** looks much more promising than relying only on a low-temperature cutoff

## Most useful next step

The next concrete step should be to prototype a solver-side or case-side **hybrid fallback policy** for the Burke H2 case:
- try learned update first
- if HP reconstruction fails, or if reconstructed `|ΔT| > 500 K`, replace that cell with CVODE chemistry for the step

That is now the most direct way to test whether the learned chemistry can already be useful in the target case once the thermodynamically pathological subset is handled conservatively.
