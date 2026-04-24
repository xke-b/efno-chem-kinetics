# First C2H4 FNO bridge is in place

_Date: 2026-04-24_

A short update on the C2H4 next phase.

The stock DeepFlame C2H4 baseline through `5e-6` is now no longer the only thing in hand. I built the first end-to-end C2H4 FNO prototype path:
- mechanism-aligned smoke dataset under `Wu24sp.yaml`
- small DFODE-kit `fno1d` checkpoint
- DeepFlame export bundle with a case-local `inference.py`

This is **not** a claim that the model is already ready for the stock C2H4 CFD case.
But it is an important transition:
- the project now has its first concrete **offline train -> export** bridge for a C2H4 FNO model

Key artifacts:
- dataset:
  - `/root/workspace/data/c2h4_autoignition_smoke.npy`
- checkpoint:
  - `/root/workspace/artifacts/models/c2h4_fno_smoke.pt`
- export bundle:
  - `/root/workspace/artifacts/models/c2h4_fno_smoke_deepflame_bundle/`

The next step is to stop treating this as just an offline artifact and stage the first copied-case integration smoke test against the `5e-6` stock runtime target.
