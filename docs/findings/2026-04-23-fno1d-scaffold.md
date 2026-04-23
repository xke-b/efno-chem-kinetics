# Initial FNO scaffold added and smoke-trained on H2 autoignition pairs

_Date: 2026-04-23_

## What was done

To resume the highest-value unfinished thread, I added a first **minimal FNO-style model scaffold** to DFODE-kit and checked that it can participate in the existing training path.

Implemented in DFODE-kit:
- `dfode_kit/models/fno1d.py`
- model export wiring in `dfode_kit/models/__init__.py`
- registry wiring in `dfode_kit/training/train.py`
- tests:
  - `tests/test_fno1d_model.py`

## Why this matters

Before implementing paper-specific EFNO losses and ablations, we needed evidence that the existing DFODE-kit training stack can support a non-MLP model family at all. This step establishes that.

## What the scaffold is

The current model is a **pragmatic 1D Fourier model over the feature-token axis**:
- input tokens: `2 + n_species`
- output tokens: `n_species - 1`
- lifting layer
- repeated spectral-conv + pointwise-conv residual blocks
- channel projection
- token projection to species-delta output size

## Important caveat

This is **not yet a paper-faithful EFNO implementation**.

Reasons:
1. the paper does not fully specify its FNO hyperparameters
2. this scaffold treats the state vector as a 1D token sequence, which is a useful prototype but not a validated statement about the authors' exact representation choice
3. physical constraints and weighted loss are not yet wired in paper form
4. rollout evaluation still needs to be formalized

So this should be viewed as an **enabling scaffold**, not as a completed reproduction.

## Smoke evidence collected

Using the local smoke dataset:
- mechanism: `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml`
- dataset: `/root/workspace/data/h2_autoignition_smoke.npy`
- shape: `(80, 18)`

A 2-epoch smoke training run completed successfully with finite losses using `model.name='fno1d'`.

Observed output:

```text
Epoch: 1, Loss1: 5.737149e-01, Loss2: 5.006733e-02, Loss3: 2.555634e+07, Loss: 6.237848e-01
Epoch: 2, Loss1: 5.566292e-01, Loss2: 4.565982e-02, Loss3: 2.330658e+07, Loss: 6.022913e-01
```

This is only a smoke check, but it confirms:
- registry path works
- model forward shape matches the current trainer contract
- training can proceed without crashing

## Immediate implications

The next most useful step is now clearer:
1. add a paper-oriented experimental trainer or loss path for EFNO
2. define rollout evaluation utilities
3. decide whether to keep extending this local `fno1d` scaffold or switch to a more standard FNO backend after additional evidence gathering

## Recommendation

Use this scaffold for:
- early plumbing checks
- smoke experiments
- understanding trainer/model contract issues

Do **not** treat it as the final reproduction baseline without further paper-alignment work.
