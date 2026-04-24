# Extending the case-aligned C2H4 FNO toward `5e-6`: it reaches the stock horizon, but the late run shows a CUDA OOM warning and zero-`Qdot` written fields, so the result is promising but not yet trustworthy

_Date: 2026-04-24_

## Why this was the next step

After the first case-aligned C2H4 FNO reached `1e-6` cleanly, the natural next step was to keep pushing it toward the stock runtime target of `5e-6`.

The key questions were:
- does the case-aligned FNO continue to outperform the earlier homogeneous-smoke FNO?
- does it fail later, or can it actually reach the stock short-horizon target?
- if it reaches `5e-6`, is the late-time behavior trustworthy?

## Case

- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_fno_integration`

The case remained in the trusted stock-style runtime regime:
- `GPU on`
- `coresPerNode 8`
- `numberOfSubdomains 8`
- `mpirun -np 8`

I first extended the run from `1e-6` to `2e-6`, then from `2e-6` to `5e-6`.

## Intermediate result: `2e-6`

The case extended cleanly through:
- `1.1e-06`
- `1.2e-06`
- `1.3e-06`
- `1.4e-06`
- `1.5e-06`
- `1.6e-06`
- `1.7e-06`
- `1.8e-06`
- `1.9e-06`
- `2e-06`

At `2e-06`, the learned active-set count was still healthy and increasing:
- `2e-06`: `35630`

and the log still looked sane:
- `min/max(T) = 499.566, 2504.93`

## Late result: reaches `5e-6`

The case then continued all the way through:
- `2.1e-06` ... `5e-06`

Final learned active-set count at `5e-06`:
- `60316`

This is much higher than both:
- the earlier homogeneous-smoke FNO path, which never made it to `1e-6`
- the stock-case active count at `5e-6` (`34730` in the earlier stock baseline summary)

So in the narrow sense of **survival horizon**, the case-aligned FNO path now reaches the project’s stock short-horizon target.

## But there is an important late-time trust problem

At the `5e-06` step, the log reports:
- `real inference points number: 60316`
- followed immediately by a Python-side message:
  - `CUDA error: out of memory`

Yet the solver still continues to completion.

That means the current result is not yet clean evidence of a fully healthy learned run. The late path is likely using a degraded or fallback-like inference behavior inside the case-local Python bridge after the GPU OOM event.

## Field evidence at `5e-6`

I compared the written `5e-06` fields against the trusted stock baseline.

### Good news
The case-aligned FNO still preserves species-simplex closure tightly:
- mean abs deviation from `1`: `2.20e-08`
- max abs deviation from `1`: `1.53e-06`

Temperature also does **not** show the catastrophic cold-tail seen in the earlier homogeneous-smoke FNO failure regime:
- case-aligned FNO `T_min = 499.207 K`
- stock `T_min = 499.249 K`

So the earlier short-horizon thermodynamic collapse really has been removed.

### Bad news
The written `Qdot` field at `5e-06` in the case-aligned FNO run is:
- min: `0.0`
- max: `0.0`
- mean: `0.0`

while the stock case at the same horizon still has active nonzero heat release:
- stock `Qdot_mean ≈ 1.62e7`

This zero-`Qdot` result, together with the logged CUDA OOM warning, is a strong sign that the late `5e-6` case-aligned FNO run is **not yet scientifically trustworthy as-is**.

## Interpretation

This extension still improves understanding significantly.

### What is now strongly supported
1. the case-aligned training distribution matters a lot
2. it removes the early collapse and HP-failure behavior seen with the homogeneous-smoke FNO
3. it allows the C2H4 FNO path to survive to the stock `5e-6` horizon in the real DeepFlame runtime

### What is not yet supported
1. that the late `5e-6` case-aligned FNO run is fully correct physically
2. that the current case-local inference bridge handles the growing active-set load robustly on GPU
3. that zero-`Qdot` late fields are acceptable—they are not

So the current result is best read as:
- **a major distribution-alignment success**
- but **not yet a clean deployment-quality success**

## Most useful next step

Diagnose the case-local FNO inference path under growing active-set size and fix the late GPU-memory failure mode before making stronger claims about the `5e-6` case-aligned result.
