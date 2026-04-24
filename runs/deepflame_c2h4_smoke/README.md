# DeepFlame C2H4 smoke staging

## Purpose

Workspace-local staging and startup debugging for the stock DeepFlame C2H4 PyTorch example:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/C2H4`

## Current staged cases

- `c2h4_stock_baseline/`
  - copied from the stock DeepFlame C2H4 example
  - external assets downloaded and extracted locally:
    - `DNN_model.pt`
    - `Wu24sp.yaml`
  - local smoke modifications:
    - `GPU off`
    - `startFrom startTime`
    - `endTime 1e-6`
    - `writeInterval 1e-7`
    - `decomposeParDict` reduced to `4` ranks
    - added `constant/g`
    - added `constant/sprayCloudProperties`
  - result:
    - startup succeeds
    - first DNN step at `Time = 2e-07` kills one MPI rank with signal `9`

- `c2h4_stock_baseline_np1/`
  - lower-rank follow-up
  - results:
    - `mpirun -np 1 ... -parallel` is invalid in OpenFOAM
    - true serial `dfLowMachFoam` fails inside `dfChemistryModel` setup with `bad size -1`

- `c2h4_stock_baseline_np2/`
  - 2-rank CPU follow-up baseline
  - `decomposeParDict` reduced to `2` ranks with `simpleCoeffs.n (2 1 1)`
  - result:
    - completes successfully through `Time = 1e-6`
    - continued successfully from `latestTime` through `Time = 2e-6`
    - further continued successfully from `latestTime` through `Time = 5e-6`
    - further continued successfully from `latestTime` through `Time = 1e-5`
    - further continued successfully from `latestTime` through `Time = 2e-5`
    - later continuation toward `5e-5` was killed with exit code `137`
    - DNN path is active from `Time = 2e-07` onward
    - summary artifacts:
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_5e-6_summary.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_1e-5_comparison_summary.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_2e-5_comparison_summary.json`

- `c2h4_stock_baseline_np2_gpu/`
  - copied from the successful `2e-5` 2-rank baseline and switched back to `GPU on`
  - result:
    - continues successfully much farther, with written fields through `4.11e-5`
    - then crashes during the `4.12e-5` DNN step with a segmentation fault in DeepFlame `solve_DNN`
    - current interpretation: GPU inference materially extends horizon versus CPU, but the next limiter looks like a DeepFlame runtime / communication failure rather than an obvious written-field chemistry pathology
    - summary artifacts:
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_failure_summary.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_fields_4.11e-05_vs_2e-05.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_cpu_vs_gpu_long_horizon_summary.json`

## Current interpretation

- the stock C2H4 learned path is now staged and runnable in `/root/workspace`
- the key issue is rank-dependent runtime viability:
  - `4` ranks: killed during DNN inference
  - serial: not supported by the current DeepFlame chemistry-model path in this build
  - `2` ranks: workable CPU smoke baseline through at least `2e-5`, and workable GPU-enabled written-field baseline through `4.11e-5`

## Most useful next step

- field analysis now indicates thermochemically well-behaved written states through `2e-5` on CPU and through pre-crash `4.11e-5` on the GPU-enabled path
- next: diagnose the GPU-path `solve_DNN` segmentation fault around `4.12e-5`, since that currently looks like the main limiter after switching back to GPU inference
