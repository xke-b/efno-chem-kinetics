# C2H4 switch-time contract validation: off-grid delayed handoff times are not valid restart states, and the staging script now fails fast with the nearest written-time suggestion

_Date: 2026-04-24_

## Why this mattered

After the delayed-switch neighborhood sweep identified `6e-07` as the best current fixed-time handoff, the obvious next refinement was to try an intermediate candidate such as `5.5e-07`.

That attempt failed immediately, but the failure was informative: it was **not** a chemistry failure. It was a restart-contract failure.

## What happened

Attempted case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch5p5e-07_np8`

DeepFlame aborted with file-not-found errors such as:
- `cannot find file ... /processor0/5.5e-07/p`

So `5.5e-07` is not a valid restart point for this stock-style case because it is **not one of the written time directories**.

## Root cause

The staging helper previously accepted any numeric `--switch-time` and rewrote `controlDict` accordingly, but it did not check whether the source case actually contains restartable fields at that time.

That made the tool permissive in a misleading way: arbitrary floating-point handoff times looked valid at the CLI level, but some of them were impossible at runtime.

## Fix

Updated:
- `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`

New behavior:
- inspects available written times under `processor0`
- requires `switch_time` to match an actual written restart time
- if not, raises a clear `ValueError`
- reports the nearest available written time and the full available set

Example new error:
- `switch_time 5.5e-07 is not a written restart time ... Nearest available written time is 6e-07`

## Why this is useful

This is a small but important reproducibility fix.

It prevents a class of misleading deployment experiments where a failed restart could be mistaken for:
- learned-model instability
- guard-policy weakness
- or solver-side chemistry failure

when the actual problem is simply that the requested switch time is not restartable.

## Consequence for the current sweep

The current fixed-time neighborhood should therefore be interpreted only on **written restart times**. In the present stock baseline, the meaningful tested local candidates are:
- `5e-07`
- `6e-07`
- `7e-07`

Under that correct contract:
- `5e-07` survives
- `6e-07` survives and is currently best
- `7e-07` destabilizes

## Current takeaway

> The next deployment-side refinement should respect the written-time restart grid explicitly. Off-grid times like `5.5e-07` are not chemistry experiments; they are invalid restart requests.
