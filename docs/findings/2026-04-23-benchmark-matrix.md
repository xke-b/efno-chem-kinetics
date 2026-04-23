# Initial benchmark matrix for EFNO reproduction

_Date: 2026-04-23_

## Benchmark order

| Stage | Benchmark | Purpose | Status |
| --- | --- | --- | --- |
| 1 | ROBER | smallest stiff ODE sanity check; verify EFNO/FNO rollout code | planned |
| 1 | POLLU | higher-dimensional stiff ODE generalization check | planned |
| 2 | H2 autoignition (7sp/16rxn) | chemistry-relevant reproduction baseline from paper | smoke dataset generated |
| 3 | DeepFlame H2 twoD_HIT_flame | first coupled-usefulness test | not started |
| 4 | DeepFlame C2H4 twoD_HIT_flame | second coupled-usefulness test | not started |

## Primary metrics

### Offline metrics
- one-step MSE / MAE
- species-wise relative error
- rollout error vs. horizon
- seen vs. unseen-condition split performance
- mass-fraction sum error
- element conservation error

### Coupled metrics
- solver stability / crash-free progression
- field-level relative `L2`
- drift over rollout horizon
- wall-clock savings vs. chemistry integration baseline
- whether temperature assimilation reduces drift

## Planned reproduction bundles

### Bundle A — minimal method verification
- implement vanilla FNO and EFNO on ROBER
- verify BCT and physics loss wiring
- produce rollout plots under unseen initial conditions

### Bundle B — paper-aligned chemistry benchmark
- generate 7-species H2 autoignition dataset
- run MLP baseline first
- add vanilla FNO
- add EFNO with:
  - BCT
  - element conservation loss
  - mass-fraction-sum loss
- run ablations

Current evidence:
- MLP smoke training works after safe-std normalization fix
- a provisional `fno1d` model scaffold has been added to DFODE-kit and smoke-trained successfully

### Bundle C — coupled-usefulness transition
- map offline checkpoint format to DeepFlame inference contract
- start with H2 case small debug run
- compare learned model against current DNN setup and solver chemistry baseline

## Current assumptions ledger

1. Use `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml` as the closest local match to the paper's 7-species/16-reaction H2 mechanism.
2. H2 autoignition dataset should include temperature in the state, so reactor integration must evolve energy, not species-only chemistry.
3. Constant-pressure vs. constant-volume autoignition is still ambiguous from the paper text; scripts should keep this configurable.
4. Offline reproduction precedes DeepFlame integration work.

## Executed today

- added `scripts/generate_h2_autoignition_pairs.py`
- generated a smoke dataset with shape `(80, 18)` using:
  - mechanism: `ES80_H2-7-16.yaml`
  - `n_init=8`
  - `steps=10`
  - `dt=1e-7 s`
  - reactor mode: `const_pressure`
- verified mass-fraction sums remain numerically consistent in generated pairs

## Next concrete experiments

1. decide whether the current `fno1d` scaffold is sufficient for the first offline comparison or whether a more standard FNO backend should replace it
2. design and implement rollout evaluation utilities
3. decide and document the initial autoignition reactor assumption (`const_pressure` vs `const_volume`)
4. backfill ROBER and POLLU generators once the model/training scaffold is stable
