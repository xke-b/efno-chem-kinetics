# C2H4 FNO integration plan after the stock `np=8` GPU baseline

_Date: 2026-04-24_

## Why this note exists

The C2H4 stock DeepFlame baseline is now strong enough to stop treating runtime establishment as the only goal.

Current reference case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`

Current runtime target:
- survive the same DeepFlame case to `5e-6`

This note records the minimum credible next path for an FNO-based learned replacement that can eventually be integrated into this simulation.

## Immediate objective

Build the first **case-aligned C2H4 training/export/integration path** for an FNO model that is at least structurally deployable into the stock DeepFlame C2H4 runtime.

This is not yet the claim that the first FNO will survive to `5e-6`.
The immediate milestone is narrower:
1. generate a mechanism- and timestep-aligned offline dataset for C2H4
2. train an FNO checkpoint on that contract
3. export it into a DeepFlame-consumable bundle
4. prepare a case-side replacement path for the stock C2H4 example
5. only then test whether it survives toward the `5e-6` stock baseline target

## Minimum technical path

### 1. Dataset contract

Match the stock C2H4 case where possible:
- mechanism: `Wu24sp.yaml`
- chemistry timestep: `1e-7`
- state layout aligned with existing DFODE-kit / DeepFlame conventions:
  - `[T, P, Y_1, ..., Y_ns] -> next state / source term target`

The first practical offline contract should stay simple and reproducible, similar to the earlier H2 case-aligned workflow:
- one-step thermochemical state transitions
- use the same species ordering as `Wu24sp.yaml`
- keep the initial benchmark offline before case-side deployment

### 2. Model family

Use the existing DFODE-kit `fno1d` scaffold as the first exportable FNO path.

Important limitation:
- the current `fno1d` is still a project scaffold, not a paper-faithful EFNO reproduction for C2H4

So this first C2H4 FNO path should be treated as:
- **deployment-enabling prototype**, not final scientific endpoint

### 3. Export path

The existing DeepFlame exporter is MLP-specific.
For FNO, the practical bridge is different:
- keep a single shared FNO checkpoint
- export a bundle containing:
  - FNO weights
  - normalization statistics
  - a case-local `inference.py`

A first enabling script for that path is now added at:
- `/root/workspace/scripts/export_dfode_fno_to_deepflame_bundle.py`

This is the first bridge artifact, not the final validated deployment path.

### 4. Runtime target

The current runtime target should remain explicit:
- **stock C2H4 DeepFlame case, `np=8`, GPU on, survive to `5e-6`**

That avoids vague deployment claims.

## Most useful next concrete step

Implement the first mechanism- and timestep-aligned C2H4 offline dataset generation path for `Wu24sp.yaml`, then train a small FNO baseline on it before attempting case-side replacement.
