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
    - source-level diagnosis points to a likely mismatch between the stock example’s implicit `np=8`, `coresPerNode=8` grouping assumption and our reduced-rank `np=2` smoke setup
    - summary artifacts:
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_failure_summary.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_gpu_fields_4.11e-05_vs_2e-05.json`
      - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_cpu_vs_gpu_long_horizon_summary.json`

- `c2h4_stock_baseline_np2_gpu_cpn2/`
  - copied from the GPU path and changed to `coresPerNode 2`
  - result:
    - not yet an operationally good fix
    - attempt was slow enough to be manually stopped
    - interpretation: matching `coresPerNode` to `-np` is not yet a demonstrated practical solution by itself

- `c2h4_stock_baseline_np8_gpu_stocksrc/`
  - fresh stock-source case aligned with the original DeepFlame example assumptions
  - settings:
    - `GPU on`
    - `numberOfSubdomains 8`
    - `coresPerNode 8`
    - `-np 8`
  - current smoke result:
    - completes cleanly through `5e-6`
    - learned active-set counts remain stably nonzero and slowly increase:
      - `2e-7`: `33508`
      - `1e-6`: `33912`
      - `2e-6`: `34197`
      - `2.1e-6`: `34208`
      - `2.5e-6`: `34244`
      - `3e-6`: `34300`
      - `4e-6`: `34504`
      - `5e-6`: `34730`
    - `solver.err` remains empty
  - summary artifacts:
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_5e-7_summary.json`
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_1e-6_summary.json`
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_2e-6_summary.json`
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_5e-6_summary.json`
  - interpretation:
    - stock-style rank count restores nonzero learned activity under the restored source path
    - this is now the most credible next runtime baseline for C2H4 GPU follow-up

- `c2h4_casepair_dp100_then_gentle_curriculum_from_4.5e-6/`
  - current best manual staged-switch deployment proof-of-concept
  - workflow:
    - run pure `dp100` through `4.5e-6`
    - switch to the gentle curriculum model only for `4.5e-6 -> 5e-6`
  - result:
    - reaches `5e-6` cleanly
    - stays much closer to pure `dp100` than running the gentle curriculum from `t=0`
  - summary artifacts:
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_gentle_switch_time_sweep_5e-06.json`
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_vs_gentle_full_vs_staged_switch_5e-06.json`

- `c2h4_casepair_dp100_then_gentle_curriculum_from_4.5e-6_generated/`
  - generator-produced reproduction of the best current manual staged switch
  - produced by:
    - `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`
  - source case:
    - `c2h4_casepair_dp100_fno_batched_full/`
  - switch bundle:
    - `/root/workspace/artifacts/models/c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke_deepflame_bundle/`
  - result:
    - cleanly reproduces the `4.5e-6 -> 5e-6` staged switch continuation

- `c2h4_cvode_baseline_np8_stockcopy/`
  - proper DeepFlame chemistry reference for the C2H4 `1e-6` horizon
  - baseline chosen:
    - primary source case: `c2h4_stock_baseline_np8_gpu_stocksrc/`
    - rationale: same trusted stock-style `np=8` decomposition and case packaging as the learned baseline, but with `TorchSettings { torch off; }` to recover in-loop standard chemistry integration
  - current settings:
    - `torch off`
    - `startFrom startTime`
    - `endTime 1e-6`
    - `writeInterval 1e-7`
  - result:
    - runs cleanly through `1e-6`
    - `selectDNN` stays inactive as expected
    - used as the matched reference for learned-vs-CVODE comparisons at `1e-6`
  - notes:
    - a lighter fresh-copy/decompose staging attempt hit a mesh lookup error for `points`; copying the already working stock-source `np=8` case and switching torch off was the reliable workaround
  - summary artifacts:
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_cvode_baseline_np8_fields_1e-06_vs_2e-07.json`
    - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_models_vs_cvode_1e-06_compact_summary.json`

## Current interpretation

- the stock C2H4 learned path is now staged and runnable in `/root/workspace`
- the key issue is rank-dependent runtime viability:
  - `4` ranks: killed during DNN inference
  - serial: not supported by the current DeepFlame chemistry-model path in this build
  - `2` ranks: workable CPU smoke baseline through at least `2e-5`, and workable GPU-enabled written-field baseline through `4.11e-5`

## Most useful next step

- field analysis now indicates thermochemically well-behaved written states through `2e-5` on CPU and through pre-crash `4.11e-5` on the GPU-enabled path
- next: diagnose the GPU-path `solve_DNN` segmentation fault around `4.12e-5`, since that currently looks like the main limiter after switching back to GPU inference
