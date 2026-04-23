# Smoke rollout baselines: current MLP beats provisional FNO1d on tiny H2 dataset

_Date: 2026-04-23_

## Purpose

After adding a provisional `fno1d` model scaffold, I ran a very small baseline check to see whether the current DFODE-kit training contract can support meaningful one-step and autoregressive evaluation.

## Dataset

Local smoke dataset:
- mechanism: `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml`
- file: `/root/workspace/data/h2_autoignition_smoke.npy`
- metadata: `/root/workspace/data/h2_autoignition_smoke.json`
- shape: `(80, 18)`
- setup: `n_init=8`, `steps=10`, `dt=1e-7 s`, constant-pressure reactor

## Evaluator added

- `scripts/evaluate_species_delta_checkpoint.py`

This evaluator follows the **current DFODE-kit species-delta checkpoint contract**, not the final EFNO paper contract.

Important limitation:
- it evaluates **species only**
- temperature is not predicted by the current baseline path
- therefore this is useful as baseline evidence and mismatch documentation, not as paper-faithful EFNO evaluation

## Results

### MLP smoke baseline
- one-step species MAE: `2.36e-03`
- one-step species RMSE: `4.48e-03`
- one-step mass-sum MAE: `6.87e-09`
- rollout species MAE by horizon:

```text
[0.0038, 0.0088, 0.0205, 0.0410, 0.0661, 0.0747, 0.0749, 0.0749, 0.1177, 0.3960]
```

### Provisional FNO1d smoke baseline
- one-step species MAE: `1.65e-02`
- one-step species RMSE: `2.81e-02`
- one-step mass-sum MAE: `3.66e-09`
- rollout species MAE by horizon:

```text
[0.0158, 0.0266, 0.0339, 0.0483, 0.0762, 0.1165, 0.1571, 0.1827, 0.1881, 0.1830]
```

## Interpretation

1. **The evaluator works** and provides immediate rollout evidence.
2. **The current MLP baseline is stronger than the provisional FNO1d on this tiny smoke setting.**
3. **Autoregressive drift is visible even on the smoke dataset**, especially for the MLP at the longest horizon.
4. **This strengthens the case for explicit rollout-focused evaluation**, which is central to the EFNO paper.
5. **The current DFODE-kit contract remains mismatched to the paper** because temperature evolution is not part of the learned output path.

## Most useful conclusion

The new `fno1d` scaffold is good enough for plumbing and experimentation, but it should not yet be considered the reproduction baseline. The next real milestone is to define a more paper-aligned EFNO training/evaluation path, especially around:
- temperature handling
- physical constraints
- weighted loss
- rollout metrics

## Related artifacts

- MLP eval JSON: `/root/workspace/artifacts/h2_autoignition_smoke_mlp_eval.json`
- FNO1d eval JSON: `/root/workspace/artifacts/h2_autoignition_smoke_fno1d_eval.json`
