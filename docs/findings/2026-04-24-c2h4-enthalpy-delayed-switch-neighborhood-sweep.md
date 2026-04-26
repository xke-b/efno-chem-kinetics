# C2H4 enthalpy delayed-switch neighborhood sweep: the deployment-safe handoff window is real but narrow, with `6e-07` outperforming `5e-07` and both earlier (`4e-07`) and later (`7e-07`) switches failing or destabilizing

_Date: 2026-04-24_

## Why this follow-up mattered

The first delayed-switch scout established that a deployment-side handoff can buy runtime for the enthalpy-regularized C2H4 branch, and that `5e-07` looked safer than `3e-07`.

The next useful question was therefore local and deployment-facing:

> Is there a broader safe region around `5e-07`, or is the apparent success just a one-off switch time?

## New cases

Generated and run:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch4e-07_np8`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch6e-07_np8`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch7e-07_np8`

Reference earlier successful cases:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch3e-07_np8`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_enthalpy10_switch5e-07_np8`

## Raw runtime outcome

### `4e-07` switch
- run starts from the stock state at `4e-07`
- does not produce a learned continuation write beyond the restart point
- MPI reports rank termination with signal 9

Interpretation:
- activating this branch that early is still not operationally safe

### `6e-07` switch
- reaches **`1e-06`** successfully

### `7e-07` switch
- starts from the stock state at `7e-07`
- begins the first learned step (`Time = 8e-07`) but the run is killed before a successful continuation write
- MPI again reports signal 9

Interpretation:
- switching too late is not monotonically safer; the branch likely enters a different unfavorable runtime region

## New comparison artifacts

### `6e-07` final and first-window comparisons
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch6e-07_vs_cvode_1e-06_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch6e-07_vs_cvode_7e-07_summary.json`

For context:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch5e-07_vs_cvode_1e-06_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_enthalpy10_switch5e-07_vs_cvode_6e-07_summary.json`

## `6e-07` beats `5e-07` at final time

At `1e-06`:

### Switch `5e-07`
- mean `Qdot` ratio: `-12.31x`
- mean `|ΔT|`: `6.49 K`
- mean `|Δp|`: `218 Pa`
- strong-`Qdot` sign mismatch: `0.282`
- `C2H3` mean ratio: `0.113x`
- `CH2CO` mean ratio: `0.276x`

### Switch `6e-07`
- mean `Qdot` ratio: **`-5.20x`**
- mean `|ΔT|`: **`3.17 K`**
- mean `|Δp|`: `246 Pa`
- strong-`Qdot` sign mismatch: **`0.192`**
- `C2H3` mean ratio: **`0.283x`**
- `CH2CO` mean ratio: **`0.508x`**

This is a meaningful improvement in the final-time chemistry comparison. The pressure error is slightly worse, but the major chemistry-facing metrics are better.

## First learned window is still poor, but `6e-07` is stronger on intermediates

### Switch `5e-07` evaluated at `6e-07`
- mean `Qdot` ratio: `8.29x`
- mean `|ΔT|`: `2.41 K`
- mean `|Δp|`: `64.7 Pa`
- strong-`Qdot` sign mismatch: `0.820`
- `CH2CO` mean ratio: `0.761x`

### Switch `6e-07` evaluated at `7e-07`
- mean `Qdot` ratio: `13.27x`
- mean `|ΔT|`: `3.14 K`
- mean `|Δp|`: `85.2 Pa`
- strong-`Qdot` sign mismatch: `0.789`
- `C2H3` mean ratio: `0.261x`
- `CH2CO` mean ratio: **`0.992x`**

So the first learned step is still not quantitatively good for either case, but the later `6e-07` activation better preserves important intermediate structure and gives a lower sign-mismatch fraction.

## Interpretation

This sweep provides the first local shape of the fixed-time handoff design space.

### What is now clearer
- there is a **real safe handoff neighborhood** around `5e-07 -> 6e-07`
- later is not monotonically better: `7e-07` was not a clean improvement
- earlier is also unsafe: `4e-07` fails immediately
- among the tested successful fixed-time switches, **`6e-07` is currently the best enthalpy-branch deployment point**

### What remains true
- even the best delayed-handoff case is still chemically inaccurate right after takeover
- this is still a guard/survival result, not a solved chemistry-fidelity result

## Current takeaway

The deployment-side handoff problem is now narrower and more actionable than before:

> The current enthalpy-regularized C2H4 branch has a nontrivial but narrow activation window, and `6e-07` is the best current fixed-time switch among tested candidates.

This is useful because it turns “guarded deployment” from a generic idea into a measurable operating-window problem.

## Best next step

The strongest next move is now likely one of:
- a very local refinement around `5e-07 -> 6e-07` with one additional candidate (for example `5.5e-07`), or
- a state-conditioned switch rule seeded from the same neighborhood, since fixed-time activation is clearly real but still brittle.
