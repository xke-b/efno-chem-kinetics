# DeepFlame H2 hybrid case prototype: a case-side Python fallback prototype lets both Burke-aligned candidates run to `5e-06`, with the corrected branch requiring much less fallback than supervised

_Date: 2026-04-23_

## Why this was the next step

The offline hybrid-fallback snapshot test suggested that a simple policy could eliminate next-step HP failures. The next useful step was to move that idea closer to the real solver path.

Rather than patching C++ immediately, I implemented a **case-side Python prototype** inside the copied Burke smoke-case `inference.py` files.

## What was changed

In the copied Burke smoke cases:
- `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp/inference.py`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct/inference.py`

I replaced the plain exported-species inference path with a guarded hybrid prototype:
1. run the exported DeepFlame-style species model
2. try local HP reconstruction in Python/Cantera
3. if reconstruction fails, or `T_next < 300 K`, or `|ΔT| > 500 K`, fallback to a one-step Cantera constant-pressure reactor advance for that cell
4. return source terms from the learned path or fallback path cell-by-cell

This is still a smoke/debug prototype, but it is much closer to actual case execution than the earlier offline snapshot study.

## Initial failed attempt and what it taught us

The first version of the patched Python hybrid inference still failed.

The failure showed up as top-level Python-side Cantera errors such as:
- `density must be positive. density = -nan`

That turned out to be a robustness issue in the batch-style Python inference implementation itself.

The fix was to switch to a **row-wise guarded inference path** so each cell could fail independently and be routed to fallback without poisoning the whole batch.

That failed attempt was useful because it showed that even the deployment-side prototype must itself be written conservatively if we want cell-local fallback to work in practice.

## Smoke runs completed

Both Burke-aligned hybrid-prototype cases were then rerun successfully.

### Cases
- `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp`
- `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct`

### Runtime target
- `endTime = 5e-06`
- `writeInterval = 1e-06`
- `np = 4`

Both runs now end with:
- `End`
- `Finalising parallel run`

So the hybrid case-side prototype converts the earlier failing Burke smoke runs into successful short runs.

## Aggregated fallback behavior by time

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/hybrid_case_run_5e-6_summary.json`

### Burke supervised
- `1e-06`: fallback `0`
- `2e-06`: fallback `223` (`hp_failures=2`, `guard_only=221`)
- `3e-06`: fallback `5081` (`hp_failures=1547`, `guard_only=3534`)
- `4e-06`: fallback `6578` (`hp_failures=3226`, `guard_only=3352`)
- `5e-06`: fallback `9361` (`hp_failures=5538`, `guard_only=3823`)

Temperature extrema by time:
- `2e-06`: `443.304, 2515.67`
- `3e-06`: `344.088, 2614.07`
- `4e-06`: `418.164, 2624.54`
- `5e-06`: `499.659, 2621.47`

### Burke corrected self-rollout
- `1e-06`: fallback `0`
- `2e-06`: fallback `268` (`hp_failures=0`, `guard_only=268`)
- `3e-06`: fallback `417` (`hp_failures=190`, `guard_only=227`)
- `4e-06`: fallback `1443` (`hp_failures=0`, `guard_only=1443`)
- `5e-06`: fallback `2683` (`hp_failures=921`, `guard_only=1762`)

Temperature extrema by time:
- `2e-06`: `499.994, 2481.22`
- `3e-06`: `359.442, 2509.51`
- `4e-06`: `416.312, 2520.18`
- `5e-06`: `357.82, 2471.37`

## Main interpretation

### 1. The hybrid safeguard is no longer only an offline hypothesis
It now works in a real target-case smoke run.

That is the most important progress in this step.

### 2. The corrected Burke branch behaves better under the hybrid case prototype
Both cases complete to `5e-06`, but the corrected self-rollout branch needs far less fallback than supervised.

At `5e-06`:
- supervised fallback cells: `9361`
- corrected fallback cells: `2683`

And at `3e-06`, where the unguarded cases used to fail:
- supervised fallback cells: `5081`
- corrected fallback cells: `417`

So under the hybrid deployment policy, the corrected Burke branch appears substantially more solver-usable than Burke supervised.

### 3. The corrected branch remains the better candidate for guarded deployment, even though its raw unguarded HP-risk looked worse in one earlier offline snapshot metric
That earlier apparent contradiction is now resolved by the closer-to-solver evidence.

The case-side prototype shows that once guarded fallback is actually applied in the loop, the corrected Burke branch is much less dependent on fallback than supervised over multiple steps.

## Bottom line

The most useful unfinished thread has now advanced from:
- export compatibility
- to failure diagnosis
- to fallback-policy design
- to a **working case-side hybrid prototype**

The current best practical H2 deployment branch is now:
- **Burke-aligned corrected self-rollout with hybrid fallback**

## Most useful next step

The next concrete step should be to turn this case-local Python prototype into a more principled and reproducible deployment path, for example by:
1. extracting the guarded hybrid logic into a reusable script/module rather than ad hoc case-local edits
2. comparing chemistry workload reduction and fallback fraction over a longer horizon than `5e-06`
3. if the short-run behavior remains stable, deciding whether to implement the same policy more cleanly in the solver/C++ path or continue with the Python prototype for H2 benchmarking
