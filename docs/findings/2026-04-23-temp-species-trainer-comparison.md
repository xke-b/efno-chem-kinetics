# Temperature+species holdout comparison: supervised baseline is still more stable than current EFNO-style training

_Date: 2026-04-23_

## Why this step mattered

After establishing a minimal `T + species` benchmark path, the most useful next question was not architectural novelty but:

> does the current `efno_style` training formulation help or hurt once temperature is added to the target?

So I ran a direct holdout comparison on the same H2 split, using the same small MLP backbone for both trainers.

## Experiment

Script:
- `/root/workspace/scripts/run_h2_temp_species_trainer_comparison.py`

Outputs:
- `/root/workspace/artifacts/experiments/h2_temp_species_holdout_comparison/summary.json`
- `/root/workspace/artifacts/experiments/h2_temp_species_holdout_comparison/supervised_temp_species_eval.json`
- `/root/workspace/artifacts/experiments/h2_temp_species_holdout_comparison/efno_temp_species_eval.json`

Common setup:
- dataset: H2 longprobe holdout split
- train trajectories: `0..11`
- test trajectories: `12..15`
- backbone: `MLP [64, 64]`
- target mode: `temperature_species`
- epochs: `10`

Trainer variants:
1. `supervised_physics`
2. `efno_style` with
   - `lambda_data = 1.0`
   - `lambda_elements = 1.0`
   - `lambda_mass = 1.0`

## Main result

### One-step holdout metrics

#### `supervised_physics_temp_species`
- species MAE: `5.98e-05`
- temperature MAE: `3.74e-01 K`
- element-mass MAE: `1.11e-04`
- invalid inverse-BCT count: `0`

#### `efno_style_temp_species`
- species MAE: `3.44e-04`
- temperature MAE: `2.49e-01 K`
- element-mass MAE: `6.94e-04`
- invalid inverse-BCT count: `0`

### Immediate interpretation

This is not a simple win/loss story on one-step metrics:
- `efno_style` gives **better one-step temperature MAE**
- but it gives **much worse one-step species accuracy**
- and **much worse element-mass accuracy**

So even before rollout, the current EFNO-style loss appears to be trading away too much species fidelity.

## Rollout stability matters more

The rollout comparison is more decisive.

### Species rollout MAE
At horizon `1000`:
- `supervised_physics_temp_species`: `6.96e-02`
- `efno_style_temp_species`: `5.17e-01`

So the EFNO-style temperature+species run is much less stable under autoregressive rollout.

### Temperature rollout MAE
At horizon `1000`:
- `supervised_physics_temp_species`: `4.27e+02 K`
- `efno_style_temp_species`: `9.71e+03 K`

This is strong negative evidence. The current EFNO-style formulation is not just worse in rollout; its temperature rollout becomes catastrophically unstable.

## What this teaches us

### 1. Adding temperature did not rescue the current EFNO-style trainer
That is useful information. It means the earlier underperformance of `efno_style` was not only a species-only artifact.

### 2. The current loss balance is probably wrong for mixed targets
The current implementation uses a single weighted data term plus species-based conservation terms. Once temperature is included, there is no explicit temperature-specific balancing term beyond its contribution to the data loss. That likely makes the tradeoff poorly conditioned.

### 3. One-step temperature improvements can be misleading
`efno_style` improved one-step temperature MAE while becoming much worse in rollout. This is exactly why holdout rollout evaluation is necessary.

## Most likely next diagnosis target
The next useful technical step is probably **loss design**, not another architecture swap.

Most relevant follow-up ideas:
1. add explicit weighting between temperature and species components inside the data loss
2. test whether temperature should be normalized or scaled differently from species deltas
3. inspect whether conservation losses are indirectly pushing species corrections in a way that destabilizes temperature rollout
4. compare `delta_T` against predicting transformed `T_next` or normalized `T_next`

## Bottom line

On the minimal `T + species` holdout benchmark, the current `efno_style` trainer is **not yet viable as a better baseline**. It slightly improves one-step temperature error, but substantially worsens species accuracy, elemental consistency, and especially rollout stability.

That is exactly the kind of negative result that narrows the next implementation step.
