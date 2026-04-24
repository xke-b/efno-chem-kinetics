# DeepFlame C2H4 stock `np=8` GPU smoke: stock-style rank count restores nonzero learned activity and now runs cleanly through `5e-6`

_Date: 2026-04-23_

## Why this was the next step

After the reduced-rank C2H4 debugging loop, it became clear that I should stop over-focusing on `np=2` and test a configuration that matches the stock DeepFlame example assumptions more closely.

The stock PyTorch C2H4 example uses:
- `mpirun -np 8`
- `GPU on`
- `coresPerNode 8`

So the most useful next step was a fresh, short-horizon smoke run in that stock-like configuration.

## Case

- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc`

Key settings:
- `GPU on`
- `numberOfSubdomains 8`
- `simpleCoeffs.n (4 2 1)`
- `startFrom startTime`
- `endTime 2e-7`
- `writeInterval 1e-7`
- stock DeepFlame source restored before this run

## Result

The stock-style `np=8` GPU smoke run first completed cleanly through `2e-7`, and I then continued the same case from `latestTime` to `5e-7`, then to `1e-6`, then to `2e-6`, and finally to `5e-6`.

Observed timeline:
- `Time = 1e-07`
- `Time = 2e-07`
- continued learned steps:
  - `Time = 3e-07`
  - `Time = 4e-07`
  - `Time = 5e-07`
  - `Time = 6e-07`
  - `Time = 7e-07`
  - `Time = 8e-07`
  - `Time = 9e-07`
  - `Time = 1e-06`
  - `Time = 1.1e-06`
  - `Time = 1.2e-06`
  - `Time = 1.3e-06`
  - `Time = 1.4e-06`
  - `Time = 1.5e-06`
  - `Time = 1.6e-06`
  - `Time = 1.7e-06`
  - `Time = 1.8e-06`
  - `Time = 1.9e-06`
  - `Time = 2e-06`
  - `Time = 2.1e-06`
  - ...
  - `Time = 5e-06`
- run ends cleanly

No solver-side fatal error appeared in:
- `solver.err`

## Important evidence

At the first learned step (`Time = 2e-07`), the run reported:
- `real inference points number: 33508`

On the continuations to `5e-7`, `1e-6`, `2e-6`, and then `5e-6`, the learned active set remained stably nonzero and gradually increased:
- `Time = 3e-07`: `33536`
- `Time = 4e-07`: `33671`
- `Time = 5e-07`: `33686`
- `Time = 6e-07`: `33691`
- `Time = 7e-07`: `33785`
- `Time = 8e-07`: `33833`
- `Time = 9e-07`: `33882`
- `Time = 1e-06`: `33912`
- `Time = 1.1e-06`: `33924`
- `Time = 1.2e-06`: `33952`
- `Time = 1.3e-06`: `33986`
- `Time = 1.4e-06`: `34013`
- `Time = 1.5e-06`: `34039`
- `Time = 1.6e-06`: `34062`
- `Time = 1.7e-06`: `34111`
- `Time = 1.8e-06`: `34150`
- `Time = 1.9e-06`: `34187`
- `Time = 2e-06`: `34197`
- `Time = 2.1e-06`: `34208`
- `Time = 2.5e-06`: `34244`
- `Time = 3e-06`: `34300`
- `Time = 4e-06`: `34504`
- `Time = 5e-06`: `34730`

The `2e-6 -> 5e-6` continuation summary is recorded at:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_5e-6_summary.json`

Compact run summary artifacts are now recorded at:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_5e-7_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_1e-6_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_2e-6_summary.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_stock_baseline_np8_gpu_stocksrc_5e-6_summary.json`

This matters because it directly answers the concern raised by the earlier failed source-patch experiments:
- the restored stock-source path does **not** collapse to zero learned activity here
- the stock-like `np=8` GPU configuration produces a nonzero learned active set immediately and maintains it through `5e-6`

The run also recorded nonzero DNN timing breakdowns, for example:
- `allsolveTime = 4.38315 s`
- `submasterTime = 3.85632 s`
- `sendProblemTime = 0.171537 s`
- `recvProblemTime = 0.166481 s`
- `getDNNinputsTime = 0.409505 s`
- `DNNinferenceTime = 2.82527 s`
- `updateSolutionBufferTime = 0.45507 s`

So the integrated GPU DNN path is genuinely active and not trivially bypassed.

## Interpretation

This is a useful correction to the previous reduced-rank loop.

The new evidence says:
1. the restored stock DeepFlame source is behaving sensibly again in this short test
2. a stock-like `np=8`, `GPU on`, `coresPerNode 8` configuration avoids the obviously broken `real inference points number: 0` behavior seen after the bad source patch
3. the earlier reduced-rank GPU issues should not be treated as the only relevant deployment regime; the stock-style rank count is materially different and more credible as the next C2H4 baseline
4. the stock-style `np=8` GPU baseline is now strong enough through `5e-6` that it can serve as the immediate runtime target for future learned-model replacement work

## Most useful next step

With the stock-style `np=8` GPU baseline now established through `5e-6`, the next useful step is to pivot from runtime establishment toward model-replacement preparation: build the first case-aligned C2H4 training/integration path for a DeepFlame-compatible learned model, using this `5e-6` stock baseline as the runtime target to match or survive.
