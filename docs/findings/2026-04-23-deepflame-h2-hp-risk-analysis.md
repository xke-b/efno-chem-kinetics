# DeepFlame H2 HP-risk analysis at `2e-06`: many DNN-active Burke cells are already thermodynamically unreconstructable before the observed solver crash

_Date: 2026-04-23_

## Why this was the next step

The pre-failure field analysis showed that the written `2e-06` states were still close to the species simplex, so the next bottleneck to examine was the **HP reconstruction itself**.

The most useful concrete question was:

> If we take the written `2e-06` state, apply the exported DeepFlame-style species update to the cells that would enter the DNN path, and then try Cantera HP reconstruction cell-by-cell, how many cells are already thermodynamically non-viable?

## Added script

- `/root/workspace/scripts/analyze_deepflame_h2_hp_reconstruction_risk.py`

Artifacts:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_mlp_hp_risk_2e-06.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_hp_risk_2e-06.json`

## Cases analyzed

- `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct`

State used:
- written fields at `2e-06`

Mechanism:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/Burke2012_s9r23.yaml`

DNN-active cells were defined exactly as the current DeepFlame H2 inference path would use them:
- `T > frozenTemperature = 510 K`

## Main result 1: many cells are already HP-invalid at the next learned update

### Burke supervised
- DNN-active cells: `8670`
- HP reconstruction failures: `927`
- failure fraction of active cells: `10.69%`

### Burke corrected self-rollout
- DNN-active cells: `9161`
- HP reconstruction failures: `1263`
- failure fraction of active cells: `13.79%`

This is the strongest evidence so far that the real case-side failure is indeed localized in the HP reconstruction step after the learned species update.

## Main result 2: even the “successful” HP reconstructions are often thermodynamically extreme

### Burke supervised successful reconstructions
- predicted next-temperature min: `1.38 K`
- predicted next-temperature max: `2722.50 K`
- mean predicted next-temperature: `2085.68 K`
- delta-T min: `-2394.35 K`
- delta-T max: `+2021.15 K`
- mean delta-T: `-240.29 K`

### Burke corrected self-rollout successful reconstructions
- predicted next-temperature min: `1.22 K`
- predicted next-temperature max: `2515.41 K`
- mean predicted next-temperature: `1876.82 K`
- delta-T min: `-2205.34 K`
- delta-T max: `+37.22 K`
- mean delta-T: `-504.33 K`

So the problem is not just that some cells fail completely. Even many cells that technically reconstruct are already being pushed into highly suspicious thermodynamic states.

## Main result 3: the two branches fail in different ways

### Burke supervised failure pattern
Sample failure cells near the DNN threshold (`T ≈ 510–520 K`) reconstruct to compositions such as:
- `N2 ≈ 0.745`
- `H2O ≈ 0.164–0.172`
- `O2 ≈ 0.058–0.069`
- `H ≈ 0.014–0.016`
- `O ≈ 0.005–0.006`
- `H2 ≈ 0.0017–0.0023`

The failure signature is strong water/radical production with very low target enthalpy relative to the reconstructed state.

### Burke corrected self-rollout failure pattern
Sample failure cells also start around `T ≈ 510 K`, but the failed predicted compositions are different:
- `N2 ≈ 0.745`
- `H2O ≈ 0.102`
- `HO2 ≈ 0.038`
- `O2 ≈ 0.036–0.038`
- `O ≈ 0.025`
- `H ≈ 0.023`

So the corrected branch tends to generate a much more radical/HO2-rich failed state.

## Main result 4: corrected self-rollout looked better in the written fields, but its next-step HP-risk is actually worse

This is an important nuance.

The earlier pre-failure field analysis suggested the corrected Burke self-rollout branch looked healthier than Burke supervised at the last written time because it did not yet show the rare cold outliers seen in the supervised run.

But this deeper HP-risk analysis shows:
- the corrected branch has a **higher fraction of outright HP reconstruction failures** at the next step
- and its successful reconstructions are often associated with very large negative temperature jumps

So the healthier written `2e-06` field does **not** imply a healthier next learned update under the solver's HP path.

## Bottom line

The real target-case bottleneck is now much clearer:
- the Burke-aligned exported checkpoints are not primarily failing because of obvious species-simplex collapse
- they are failing because the next DeepFlame-style learned species update makes a substantial fraction of DNN-active cells thermodynamically unreconstructable under the solver's enthalpy-pressure correction path

And among the two Burke-aligned candidates tested here:
- Burke supervised produces more visibly pathological written temperature outliers by `2e-06`
- Burke corrected self-rollout produces a **higher next-step HP failure fraction** when analyzed cell-by-cell from the same written state

## Most useful next step

The next concrete step should be to test a **deployment-side safeguard** rather than another blind offline ranking exercise.

The smallest high-value intervention is likely one of:
1. **hybrid CVODE fallback on flagged cells**
   - if predicted HP reconstruction fails or predicted next temperature falls outside a safety band, use CVODE for that cell
2. **bounded species-update magnitude** for deployment
   - especially near the `T ≈ 510 K` activation band where many failures appear
3. **temperature/enthalpy safety filter**
   - reject DNN species updates that imply extreme next-step HP temperatures

Given the present evidence, hybrid fallback on flagged cells is the most direct next experiment because it can test whether the learned model is already useful in the case if the thermodynamically pathological subset is handled conservatively.
