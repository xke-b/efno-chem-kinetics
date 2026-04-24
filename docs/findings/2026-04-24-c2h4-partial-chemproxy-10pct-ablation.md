# C2H4 partial chemistry-proxy label replacement (`10%`) ablation: preserving the CFD backbone keeps the run alive to `5e-6`, but naive partial relabeling still degrades solver-facing behavior badly

_Date: 2026-04-24_

## Why this was the next step

The first pure chemistry-proxy deployment attempt failed catastrophically by `4e-7`, which showed that fixing label semantics alone with a tiny relabeled subset is not enough.

The obvious next question was then:
- can we improve semantics **without** losing the solver-relevant manifold by only replacing a fraction of labels inside the stronger `dp100` backbone?

So I ran the simplest version of that idea:
- keep the full `dp100` dataset structure,
- replace only `10%` of next-state labels with chemistry-proxy relabels,
- then train and deploy.

## New script

- `/root/workspace/scripts/create_c2h4_partial_relabel_dataset.py`

This script takes a base dataset and a relabeled subset and replaces only the selected rows' next-state labels.

## Mixed dataset built

- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_partial_chemproxy5k.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_partial_chemproxy5k.json`

Construction:
- base dataset: `dp100` (`50000` rows)
- replaced rows: `5000`
- replaced fraction: `0.1`

So this is a first hybrid target-semantics test, not yet a large-scale relabeling campaign.

## Training and deployment artifacts

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_partial_chemproxy5k_fno_smoke.pt`

DeepFlame bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_partial_chemproxy5k_fno_smoke_deepflame_bundle/`

Integrated case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_partial_chemproxy5k_fno_batched_full`

Field artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_casepair_dp100_partial_chemproxy5k_fno_fields_5e-06_vs_2e-06.json`

Comparison artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_partial_chemproxy5k_vs_bestmix_summary.json`

## Main runtime result

Unlike the pure chemistry-proxy `5k` model, this partial-relabel model remains solver-usable through `5e-6`:
- empty `solver.err`
- no OOM line
- learned active-set counts stay substantial through the horizon
- final learned active-set count at `5e-6`: `34302`

So preserving the CFD-aligned backbone does indeed rescue gross deployment stability.

## But solver-facing quality degrades badly

### Best current mixed reference (`dp100 + canonical@0.2`)
- mean `Qdot`: `2.514e7`
- `Qdot / stock ≈ 1.55x`
- pressure max: `102817 Pa`
- `T_min = 499.159 K`
- mean `|ΔT| = 0.927 K`

### Partial chem-proxy `10%`
- mean `Qdot`: `-9.883e8`
- `Qdot / stock ≈ -60.95x`
- pressure max: `102927 Pa`
- `T_min = 492.524 K`
- mean `|ΔT| = 9.153 K`

### Stock
- mean `Qdot`: `1.622e7`
- pressure max: `102000 Pa`
- `T_min = 499.249 K`
- mean `|ΔT| = 0.828 K`

## Interpretation

This is a useful middle result.

### Positive result
Partial relabeling does exactly one thing we hoped for:
- it keeps the run on the solver-relevant manifold well enough to survive to `5e-6`

So the collapse of the pure chemistry-proxy `5k` model was **not** proof that chemistry-faithful relabeling is useless. It was proof that a tiny pure relabeled subset cannot carry the whole deployment by itself.

### Negative result
Naive partial replacement is still not good enough.

Even though the run survives, the solver-facing behavior regresses sharply:
- mean `Qdot` flips strongly negative
- temperature quality worsens substantially
- the temperature floor drops below the healthier best-mix regime

So the current `10%` partial-relabeled path is stable but still qualitatively wrong.

## What this means

This narrows the target-semantics story further.

The evidence now suggests:
1. pure tiny chemistry-proxy replacement is too weak to preserve the manifold
2. naive partial replacement can preserve stability but still distort source-term behavior badly
3. therefore the next useful relabeling path must be **more selective or more structured**, not just “replace some random fraction of labels”

That is real progress because it eliminates two naive options:
- tiny pure chemistry-proxy subset
- random partial chemistry-proxy replacement

## Current takeaway

The right next question is no longer whether relabeling matters. It does.

The next question is:
- **which rows should be relabeled, and in which regimes, if we want semantics gains without damaging the deployment manifold?**

That points directly toward regime-targeted relabeling rather than uniform random replacement.
