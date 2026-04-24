# DeepFlame C2H4 stock-case staging: the packaged example can be made runnable in `/root/workspace`, and the first learned-inference blocker narrows to rank-dependent runtime viability rather than missing assets or immediate chemistry failure

_Date: 2026-04-23_

## Why this was the next step

After the H2 deployment path was narrowed to a corrected-branch default plus guarded variant, the next useful unfinished thread was to reduce uncertainty around the second target DeepFlame case:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/C2H4`

The immediate goal here was not to solve C2H4 learning, but to establish whether the stock example can be staged reproducibly in `/root/workspace` and what the first practical blocker is.

## What I did

I created a workspace copy:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline`

Then I fetched the model assets expected by the example `Allrun`:
- downloaded `DNN_model.zip` from the case’s documented URL
- extracted only:
  - `DNN_model.pt`
  - `Wu24sp.yaml`

I also made the copied case suitable for small CPU smoke debugging:
- `GPU off`
- `startFrom startTime`
- `endTime 1e-6`
- `writeInterval 1e-7`
- `decomposeParDict` reduced from `8` to `4` ranks
- added missing copied support files:
  - `constant/g`
  - `constant/sprayCloudProperties`

## Important packaging findings

The source C2H4 example is incomplete unless its `Allrun` is allowed to fetch external assets.

Evidence:
- `constant/CanteraTorchProperties` points to `Wu24sp.yaml`
- but the example directory does not ship that file initially
- `Allrun` downloads `DNN_model.zip` and then copies:
  - `./DNN_model/C2H4/DNN_model.pt`
  - `./DNN_model/C2H4/Wu24sp.yaml`

So the first C2H4 blocker was simply missing packaged assets, and that has now been resolved for the workspace copy.

## Smoke-run sequence and outcomes

### 4-rank CPU smoke case: startup works, first DNN step kills a rank

The copied stock C2H4 case starts successfully and advances through the first CVODE step:
- it reaches `Time = 1e-07`
- it then reaches `Time = 2e-07`
- the DNN path is entered
- all ranks report `real inference points number: 8377`

Then the run aborts because one MPI rank is killed by signal 9 during the DNN phase.

From `solver.err`:
- `mpirun noticed that process rank 2 ... exited on signal 9 (Killed)`

From `run.log`:
- the case clearly survives the CVODE-only first step
- the failure occurs after `=== begin solve_DNN ===`
- all ranks are executing DNN inference on CPU when the process is killed

### 1-rank attempts: both informative, neither viable

I then tested lower-rank execution.

First, `mpirun -np 1 dfLowMachFoam -parallel` fails immediately with an OpenFOAM usage restriction:
- `attempt to run parallel on 1 processor`

Second, a true serial run (`dfLowMachFoam` without `-parallel`) also fails, but now inside DeepFlame chemistry-model setup:
- `FOAM FATAL ERROR: bad size -1`
- stack trace points into `Foam::dfChemistryModel<...>::dfChemistryModel(...)`

This is useful because it shows the stock DeepFlame C2H4 path in this build is not simply "run serial instead" compatible.

### 2-rank CPU smoke case: succeeds to the short horizon and remains viable on immediate extension, but a later long-horizon CPU continuation is killed

I then staged a 2-rank copy:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np2`

with:
- `numberOfSubdomains 2`
- `simpleCoeffs.n (2 1 1)`

That 2-rank run completed successfully to the planned short horizon:
- times written through `Time = 1e-06`
- `=== begin solve_DNN ===` observed on each learned step after the first CVODE-only step
- DNN-active point counts per rank remained in the expected range, roughly `1.67e4` to `1.70e4`

I then continued the same 2-rank case from `latestTime` first to `endTime = 2e-06`, and then further to `endTime = 5e-06`.
Those extensions also completed successfully:
- times written through `Time = 5e-06`
- total time steps completed in the current staged run: `50`
- DNN-active steps completed: `49`
- first DNN step still begins at `Time = 2e-07`
- latest observed per-rank inference-point counts remained stable, rising only modestly from the initial `~1.68e4` range to about `17238` and `17536` at `5e-06`
- `solver.err` remained empty on the successful 2-rank extensions

A compact run summary artifact is now recorded at:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np2_5e-6_summary.json`

That original CPU-path case was later extended successfully through `2e-05`, but a further continuation attempt toward `5e-05` was killed with exit code `137`.

So the stock C2H4 learned path is viable in this environment at 2 ranks for meaningful smoke horizons, but long-horizon CPU continuation eventually runs into a hard process kill.

## Likely interpretation

The 4-rank failure is strongly consistent with a resource / memory issue in the stock C2H4 DNN path rather than a chemistry or OpenFOAM startup bug.

I inspected the stock checkpoint:
- number of species networks: `23`
- total parameters across scalar subnetworks: `37,830,423`
- approximate fp32 parameter storage: about `144.3 MB`
- checkpoint file size: about `144.4 MB`

Because the case runs on `4` MPI ranks and each rank loads the full network set, the actual per-rank memory footprint is much larger than the checkpoint size once model objects, activations, tensors, Python, and OpenFOAM state are included.

So the first practical C2H4 blocker now appears more precisely to be:
- **the stock 24-species DNN inference path is not robust across rank configurations in this environment: 4 ranks fails during learned inference, 1-rank serial is not supported by the current DeepFlame chemistry-model path, but 2 ranks is viable for short smoke validation**

## Why this matters

This is useful progress even though the run failed.

We now know that the next C2H4 obstacle is not:
- missing mechanism wiring
- missing DNN assets
- startup dictionary mismatch
- immediate chemistry failure

Instead, the first concrete blocker is:
- **rank-dependent learned-inference runtime viability, with strong evidence that 4-rank CPU execution is too heavy while 2-rank execution is workable**

That significantly narrows the next debugging space.

## Most useful next step

The next concrete C2H4 step should now build on the successful 2-rank path:
1. treat the 2-rank stock case as the current C2H4 smoke baseline
2. prefer GPU inference for neural-network-integrated DeepFlame runs when the environment supports it, following the stock DeepFlame `TorchSettings` pattern
3. compare long-horizon CPU and GPU behavior to separate resource-limit failures from chemistry / deployment failures
4. separately, if needed, investigate why the current DeepFlame chemistry path is not serial-safe in this build

In short: C2H4 is now staged, assets are resolved, and a workable stock smoke baseline exists at 2 ranks, with long-horizon behavior now depending materially on the inference backend.
