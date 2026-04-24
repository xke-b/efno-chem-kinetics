# First C2H4 FNO integration smoke: the exported FNO bundle loads into the stock DeepFlame C2H4 case and runs cleanly through `5e-7`

_Date: 2026-04-24_

## Why this was the next step

After building the first C2H4 FNO smoke checkpoint and exporting it into a DeepFlame bundle, the next useful question was no longer purely offline.

The next concrete milestone was:
- can the exported FNO bundle actually replace the stock inference path in a copied DeepFlame C2H4 case and survive the first few learned steps?

## Case

- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_fno_smoke_integration`

This case was copied from the stock-style `np=8` GPU baseline and then modified to use the exported FNO bundle:
- replaced `inference.py` with:
  - `/root/workspace/artifacts/models/c2h4_fno_smoke_deepflame_bundle/inference.py`
- added model file:
  - `/root/workspace/artifacts/models/c2h4_fno_smoke_deepflame_bundle/DNN_model_fno.pt`
- updated `constant/CanteraTorchProperties`:
  - `torchModel "DNN_model_fno.pt";`

Runtime settings remained aligned with the credible stock baseline:
- `GPU on`
- `numberOfSubdomains 8`
- `coresPerNode 8`
- `-np 8`

## Result

The exported FNO bundle loaded and the copied DeepFlame C2H4 case completed cleanly through `5e-7`.

Observed timeline:
- `Time = 1e-07`
- `Time = 2e-07`
- `Time = 3e-07`
- `Time = 4e-07`
- `Time = 5e-07`

No solver-side fatal error appeared in:
- `solver.err`

## Important evidence

The FNO path is not bypassed.
It reported nonzero learned activity at every learned step in the continuation:
- `Time = 2e-07`: `33508`
- `Time = 3e-07`: `33508`
- `Time = 4e-07`: `33532`
- `Time = 5e-07`: `33509`

So this is a real DeepFlame integration smoke success, not just a file-loading success.

The run also recorded nonzero DNN timing breakdowns at the final step, including:
- `allsolveTime = 8.04871 s`
- `submasterTime = 6.51246 s`
- `getDNNinputsTime = 1.53791 s`
- `DNNinferenceTime = 2.79856 s`
- `updateSolutionBufferTime = 1.76149 s`

## Interpretation

This is an important transition point for the C2H4 thread.

Before this step, the project only had:
- a stock DeepFlame runtime baseline through `5e-6`
- an offline/export FNO bridge

After this step, the project now has:
- a **case-side FNO integration smoke success** in the real C2H4 DeepFlame runtime

Important limitations remain:
- the current FNO was trained only on a homogeneous smoke dataset, not CFD-state-sampled case data
- survival to `5e-7` is still much weaker than the stock baseline target of `5e-6`
- no claim should yet be made that this FNO is scientifically competitive or deployment-ready

But the integration barrier itself is now materially lower.

## Most useful next step

Extend this copied FNO-integration case beyond `5e-7` in controlled steps and determine whether the first failure mode is runtime-side or chemistry-surrogate-side, while beginning work on a more case-relevant C2H4 training dataset.
