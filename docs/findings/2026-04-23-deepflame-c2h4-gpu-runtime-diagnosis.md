# DeepFlame C2H4 GPU runtime diagnosis: the long-horizon GPU crash is likely a rank-group communication issue in `solve_DNN`, and the stock examples implicitly expect `mpirun -np 8` to match `coresPerNode 8`

_Date: 2026-04-23_

## Why this was the next step

After switching the staged stock C2H4 case back to GPU inference, the run reached much farther than the CPU path, writing fields through `4.11e-5`, but then failed at `4.12e-5` with a segmentation fault inside DeepFlame `solve_DNN`.

That changed the most useful next question from "how far can the case run?" to:
- is this a chemistry-state failure, or a DeepFlame runtime / communication failure?

## Key evidence

### Observed GPU failure signature

From the staged GPU case:
- case:
  - `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np2_gpu`
- error:
  - segmentation fault at `Time = 4.12e-05`
- stack points into:
  - `UIPstream::read(...)`
  - `operator>>(Istream&, List<GpuProblem>&)`
  - `dfChemistryModel<...>::solve_DNN(...)`
  - `libdfCombustionModels.so`

This strongly suggests a message-passing / receive-side failure rather than an immediately thermochemical field failure.

### Pre-crash fields still look sane

The last written GPU-path fields at `4.11e-05` remain thermochemically well behaved:
- species-sum mean: about `1.0000000015`
- species-sum max absolute deviation from `1`: about `1.09e-06`
- `T_min ≈ 499.5 K`
- `T_max ≈ 2459.0 K`

So the crash point is not well explained by obvious written-field simplex collapse or catastrophic temperature corruption.

## Source-level diagnosis

I inspected DeepFlame’s PyTorch DNN path in:
- `/opt/src/deepflame-dev/src/dfChemistryModel/pytorchFunctions.H`
- `/opt/src/deepflame-dev/src/dfChemistryModel/dfChemistryModel.C`

### 1. The stock examples assume a grouped-rank pattern

Both stock PyTorch DeepFlame examples use:
- `mpirun -np 8`

Evidence:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/C2H4/Allrun`
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/Allrun`

And the C2H4 `CanteraTorchProperties` uses:
- `coresPerNode 8;`

So the installed example is implicitly configured for a world-size / grouping assumption of `8` ranks.

### 2. `solve_DNN` groups ranks by `cores_`, without guarding against `Pstream::nProcs()`

In the PyTorch GPU path, `cores_` is read from:
- `TorchSettings.coresPerNode`

Then the code uses rank-group logic like:
- `if (!(Pstream::myProcNo() % cores_))` for submasters
- `if (Pstream::myProcNo() % cores_)` for slaves
- loops of the form:
  - `for (label i = 1; i < cores_; i++)`

Critically, the submaster path gathers messages with:
- `UIPstream recv(i + Pstream::myProcNo(), pBufs);`

and later redistributes with the same `1 .. cores_-1` range.

In the inspected code, those loops are not bounded by `Pstream::nProcs()`.

That means a configuration such as:
- `mpirun -np 2`
- `coresPerNode 8`

creates a mismatch between:
- the assumed group size (`8`)
- the actual world size (`2`)

This is a strong source-level explanation for why the GPU path can fail inside `UIPstream::read(...)`.

### 3. Why this matters for the observed crash

The GPU segfault stack landed precisely in the receive-side stream path used by those grouped communications.

That does **not** prove a single exact line caused the crash, but it does make the following interpretation credible:
- the stock DeepFlame GPU DNN path expects rank-group communication patterns consistent with the example’s original `np=8`, `coresPerNode=8` design
- our reduced-rank smoke configuration breaks those assumptions
- the long-horizon GPU failure is therefore more plausibly a runtime communication bug / unsupported reduced-rank configuration than a chemistry-state failure

## Follow-up evidence from the `coresPerNode=2` attempt

I also staged:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np2_gpu_cpn2`

with:
- `mpirun -np 2`
- `coresPerNode 2`

That attempt did **not** immediately become an operationally clean fix. It ran slowly enough to be impractical for the current loop, and the attempt was manually stopped.

That is still useful information:
- simply forcing `coresPerNode` to match `-np` is not yet a demonstrated practical solution in this environment
- but the source inspection still indicates that the original `np=2`, `coresPerNode=8` GPU setup was structurally suspicious

## What this changes

This narrows the C2H4 next step.

The current GPU failure should be treated primarily as a DeepFlame runtime / rank-grouping issue, not yet as evidence that the stock learned C2H4 chemistry path is physically failing by `4.12e-5`.

## Most useful next step

Before launching more long GPU runs, the next useful work should be one of:
1. patch or instrument the DeepFlame GPU `solve_DNN` path so rank-group receives/sends are explicitly bounded by `Pstream::nProcs()`
2. or stage a cleaner reduced-rank GPU configuration only after verifying its communication assumptions in source
3. keep the pre-crash GPU fields through `4.11e-5` as the current longest viable stock C2H4 written-field baseline
