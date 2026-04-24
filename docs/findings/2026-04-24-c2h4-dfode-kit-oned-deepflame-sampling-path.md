# C2H4 DFODE-kit one-dimensional DeepFlame sampling path: confirmed, staged, and smoke-validated

_Date: 2026-04-24_

## Why this mattered

A useful correction to the current thinking is that Xiao et al. (2026) do not just use an abstract canonical flame manifold. They specifically sample from a **one-dimensional flame simulation**, then augment and transform targets.

DFODE-kit already documents a closely aligned workflow:
- initialize a DeepFlame-backed one-dimensional freely propagating premixed flame
- run the case
- sample it to HDF5
- then augment / label / train

So instead of treating our Cantera-only canonical generator as the only route, I checked whether DFODE-kit’s documented DeepFlame 1D path is already usable for C2H4 with the Wu24sp mechanism.

## Relevant DFODE-kit references

Confirmed in:
- `/opt/src/DFODE-kit/README.md`
- `/opt/src/DFODE-kit/tutorials/README.md`
- `/opt/src/DFODE-kit/dfode_kit/cases/deepflame.py`

Key documented workflow:
1. `init oneD-flame`
2. run the generated DeepFlame case
3. `sample` the finished case into HDF5
4. continue to augmentation/labeling/training

This means a Xiao-style “sample from 1D flame simulation first” workflow is already a natural DFODE-kit path, not a foreign addition.

## Concrete staging result

Initialized a workspace-local C2H4 case via DFODE-kit:
- `/root/workspace/runs/dfode_c2h4_oned_flame_phi1`

Initialization command used:
```bash
PYTHONPATH=/opt/src/DFODE-kit python -m dfode_kit.cli.main init oneD-flame \
  --mech /root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc/Wu24sp.yaml \
  --fuel C2H4:1 \
  --oxidizer air \
  --phi 1.0 \
  --out /root/workspace/runs/dfode_c2h4_oned_flame_phi1 \
  --apply --force
```

Generated metadata:
- `/root/workspace/runs/dfode_c2h4_oned_flame_phi1/dfode-init-plan.json`

Resolved flame properties from DFODE-kit init:
- laminar flame speed: `0.7192348476753527 m/s`
- laminar flame thickness: `2.6781858850077547e-4 m`

## Important bug found and fixed upstream in local DFODE-kit checkout

While staging this case, I found a real bug in:
- `/opt/src/DFODE-kit/dfode_kit/cases/deepflame.py`

### Bug
`update_one_d_sample_config(...)` used substring matching:
- `if key in line:`

This caused the `simTime` replacement to also match the `simTimeStep` line, overwriting the time step with the full simulation time.

### Symptom before fix
Generated `system/sampleConfigDict` had:
- `simTimeStep` incorrectly equal to `simTime`

For this C2H4 case, that meant an obviously wrong giant step size.

### Fix
I changed replacement matching to require the line to declare the exact key token, preventing `simTime` from clobbering `simTimeStep`.

Modified file:
- `/opt/src/DFODE-kit/dfode_kit/cases/deepflame.py`

Added regression test:
- `/opt/src/DFODE-kit/tests/test_deepflame_case_setup.py`

After regeneration, the case now correctly contains:
- `simTimeStep             1e-06;`
- `simTime                 0.0037608963923266366;`

## Case-run smoke validation

Using the documented DeepFlame environment order, I ran the staged case.

The stock `Allrun` exposed another practical container issue:
- `mpirun` failed because it did not include `--allow-run-as-root`

This is a container/runtime issue, not a oneD-flame-science issue.

After launching the solver manually with:
```bash
mpirun --allow-run-as-root -np 4 dfLowMachFoam -parallel
```

the case completed successfully.

Key evidence:
- log: `/root/workspace/runs/dfode_c2h4_oned_flame_phi1/log.mpirun`
- written times reached through the expected final horizon
- reconstructed case succeeded via `reconstructPar`

## Sampling result

I then sampled the finished case through DFODE-kit:

```bash
PYTHONPATH=/opt/src/DFODE-kit python -m dfode_kit.cli.main sample \
  --mech /root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc/Wu24sp.yaml \
  --case /root/workspace/runs/dfode_c2h4_oned_flame_phi1 \
  --save /root/workspace/data/c2h4_dfode_oned_phi1_sample.h5 \
  --include_mesh
```

Produced artifact:
- `/root/workspace/data/c2h4_dfode_oned_phi1_sample.h5`

The HDF5 contains:
- mesh group
- scalar field snapshots for the full one-dimensional flame trajectory
- species/state layout with 26 channels (`T`, `p`, species)

## Why this changes the forward path

This is important because it removes a false dichotomy.

We no longer have to think of the C2H4 data path as only:
- case-pair CFD extraction, or
- Cantera-only canonical flame generation

We now also have a **validated DeepFlame-backed 1D flame sampling path** inside the existing DFODE-kit workflow, which is much closer to Xiao’s starting point.

## Practical takeaway

The next C2H4 data-preparation direction should treat this new artifact as a serious candidate source for future experiments:
- DeepFlame 1D flame sampling → HDF5 manifold
- then augmentation/interpolation/filtering
- then low-temperature / scale-separated target tests

That is a more faithful Xiao-style path than jumping directly from full CFD state pairs to target reformulation.

## Current takeaway

The main progress from this step is not just another artifact. It is that we now have a **working, documented, DeepFlame-native 1D C2H4 sampling pipeline** in the workspace, and the first attempt surfaced and fixed a real DFODE-kit case-generation bug that would have silently broken that workflow.
