# Workspace survey and baseline inventory

_Date: 2026-04-23_

## Repositories and key paths

### This repository
- root: `/root/workspace`
- docs site: `/root/workspace/docs`
- papers: `/root/workspace/papers`

### DeepFlame
- repo: `/opt/src/deepflame-dev`
- solver tree: `/opt/src/deepflame-dev/applications/solvers/dfLowMachFoam`
- chemistry model integration: `/opt/src/deepflame-dev/src/dfChemistryModel`
- target example family: `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame`

### DFODE-kit
- repo: `/opt/src/DFODE-kit`
- package root: `/opt/src/DFODE-kit/dfode_kit`
- current models: `/opt/src/DFODE-kit/dfode_kit/models`
- current training entrypoint: `/opt/src/DFODE-kit/dfode_kit/training/train.py`

## Existing DeepFlame case inventory relevant to this project

### H2 case
Path:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2`

Observed baseline characteristics:
- bundled OpenFOAM case structure already present
- `Allrun` downloads `DNN_model.pt` if missing
- mechanism: `Burke2012_s9r23.yaml`
- `TorchSettings.inferenceDeltaTime = 1e-6`
- current inference path is plain PyTorch `inference.py`
- current workflow is DNN-centric, not EFNO-centric

### C2H4 case
Path:
- `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/C2H4`

Observed baseline characteristics:
- mechanism: `Wu24sp.yaml`
- also uses `DNN_model.pt`
- shorter chemistry inference step: `1e-7`

## Existing DFODE-kit baseline capabilities relevant to EFNO

### What already exists
- Cantera-based labeling pipeline for paired one-step data
- training config system for registered models/trainers
- MLP model builder and trainer registry
- tutorial assets for `twoD_HIT_flame`

### What is missing for paper-faithful EFNO work
- FNO/EFNO model class
- weighted loss for imbalanced reacting-flow samples
- physical conservation losses for training
- paper-style rollout evaluation harness
- export path from EFNO training artifact to DeepFlame-consumable inference code

## Immediate engineering implication

The best low-risk path is:
1. keep DeepFlame cases unchanged initially
2. reproduce the paper offline first
3. only then define the narrowest deployment contract needed for DeepFlame coupling

## Risks found in the current baseline

1. **Artifact mismatch risk**
   Existing DeepFlame examples expect a `DNN_model.pt` plus Python `inference.py`. EFNO may require a different checkpoint structure or a new inference shim.

2. **Benchmark mismatch risk**
   The paper's 3D NH3/H2 LES benchmark is not the same as the bundled H2 and C2H4 twoD_HIT_flame examples.

3. **Evaluation mismatch risk**
   Existing DFODE-kit training focuses on one-step supervised regression. The paper emphasizes recursive rollout and unseen-condition behavior.

## Baseline decision

For the next coding phase:
- use DFODE-kit as the main offline experimentation substrate
- use the DeepFlame H2 case as the first coupled target because it is closest to the paper's hydrogen chemistry setting
- defer C2H4 coupled work until the H2 baseline is working and documented
