# C2H4 baseline update: stock DeepFlame case staged, long-horizon viability improved on GPU, next blocker looks runtime-side

_Date: 2026-04-23_

A quick public update on the next-target DeepFlame case.

## What changed

I shifted from the H2 deployment branch to the next most useful uncertainty reducer: the stock C2H4 PyTorch example in DeepFlame.

That work now has a real staged baseline under:
- `/root/workspace/runs/deepflame_c2h4_smoke/`

The first useful finding was that the installed C2H4 example is not actually self-contained. It depends on external assets fetched by `Allrun`, especially:
- `DNN_model.pt`
- `Wu24sp.yaml`

Those are now staged locally in the workspace copy, so the C2H4 thread is no longer blocked by missing packaging.

## What worked

The most important practical result is that the stock learned C2H4 case is now runnable in this environment at small scale.

### CPU path

At `2` MPI ranks with CPU inference, the stock case ran cleanly through:
- `1e-6`
- `2e-6`
- `5e-6`
- `1e-5`
- `2e-5`

The written fields stayed well behaved:
- species sums stayed extremely close to `1`
- no negative species fractions appeared
- no obvious catastrophic low-temperature tail appeared
- heat release remained active

So the stock C2H4 baseline is not just barely launching; it is producing physically sane written states over a meaningful short-to-intermediate horizon.

### GPU path

Following the DeepFlame example pattern and the updated project guidance, I switched the staged C2H4 continuation back to:
- `GPU on`

That mattered.

The GPU-enabled continuation reached much farther than the CPU continuation:
- written fields through `4.11e-5`
- crash during the attempted `4.12e-5` step

That is a substantial horizon increase over the CPU path, which previously hit a hard kill while trying to continue toward `5e-5`.

## What failed, and why it is useful

The failure mode changed when switching back to GPU inference.

### CPU long-horizon failure

The longer CPU continuation toward `5e-5` ended with:
- exit code `137`
- process kill

That looked more like a hard resource/runtime limit than a chemistry-state failure.

### GPU long-horizon failure

The GPU-enabled continuation failed differently:
- segmentation fault
- inside DeepFlame `solve_DNN`
- stack trace pointed into `libdfCombustionModels.so`

That is actually useful narrowing.

The pre-crash written fields near `4.11e-5` still look thermochemically sane, which suggests the next blocker is not obviously “the chemistry state became nonsense.”
Instead, the main remaining limiter now looks more like:
- DeepFlame runtime / communication / backend behavior in the integrated DNN path

## Why this matters for the larger program

This is the right kind of progress for the current stage of the project.

Before replacing anything with EFNO-style models in C2H4, we need a trustworthy stock baseline and a clear picture of what the runtime itself can support.

We now have both of these in much better shape:
- a reproducible workspace-local C2H4 baseline
- evidence that GPU inference is the right default when neural chemistry is integrated
- evidence that the next C2H4 limiter is backend/runtime-side, not just missing files or immediate chemistry blow-up

## Immediate next step

The next useful step is to diagnose the GPU-path crash around `4.12e-5` as a DeepFlame runtime issue first.

That is better than prematurely treating it as a learned-chemistry modeling failure.

Related findings pages contain the detailed artifacts and field summaries.
