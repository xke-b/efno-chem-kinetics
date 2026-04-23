# EFNO replication program: staged execution plan

_Date: 2026-04-23_

## Mission framing

This project will proceed in a benchmark-first order:

1. build a repeatable PDF-to-notes workflow
2. extract a faithful EFNO implementation/evaluation spec from the paper
3. reproduce the paper incrementally on small ODE and 0D chemistry problems
4. evaluate unseen-condition generalization and rollout stability
5. extend DFODE-kit with an EFNO-capable training/evaluation path
6. integrate trained models into the target DeepFlame CFD cases
7. document results continuously in docs and a LaTeX preprint

## Workspace and codebase survey

### Main workspace
- Contract: `/root/workspace/AGENTS.md`
- Docs site root: `/root/workspace/docs`
- Papers: `/root/workspace/papers`
- Current repo remote: `https://github.com/xke-b/efno-chem-kinetics.git`

### DeepFlame
- Repo: `/opt/src/deepflame-dev`
- Relevant target cases:
  - `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2`
  - `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/C2H4`
- H2 example currently uses:
  - mechanism `Burke2012_s9r23.yaml`
  - `inferenceDeltaTime 1e-6`
  - PyTorch model file `DNN_model.pt`

### DFODE-kit
- Repo: `/opt/src/DFODE-kit`
- Current repo remote: `https://github.com/xke-b/DFODE-kit.git`
- Existing strengths:
  - case initialization
  - case running
  - labeling/integration
  - MLP training baseline
- Current gap relative to EFNO paper:
  - no FNO/EFNO model family yet
  - no explicit physics-constrained EFNO trainer
  - no paper-aligned rollout/generalization benchmark harness yet

## Staged plan

### Stage 0 — ingestion and specification lock
**Goal:** remove PDF ambiguity before coding the method.

Deliverables:
- reproducible PDF extraction script
- extracted plain-text paper artifacts
- implementation spec with explicit ambiguities
- benchmark matrix and reproduction checklist

Immediate actions:
- [x] inspect workspace, papers, DeepFlame, DFODE-kit, CFD case paths
- [x] build first PDF extraction workflow with `pypdf`
- [ ] finish structured paper spec from extracted text
- [ ] identify unresolved hyperparameters and source-code gaps

### Stage 1 — minimal EFNO reproduction on toy stiff systems
**Goal:** reproduce the paper's simplest stiff ODE settings before touching CFD.

Targets:
- ROBER
- POLLU

Deliverables:
- dataset generation scripts
- EFNO baseline implementation
- training configs
- autoregressive rollout evaluation scripts
- comparison against simpler baselines where practical

Acceptance checks:
- unseen-initial-condition evaluation reproduced
- recursive rollout plots produced
- paper-spec deviations documented explicitly

### Stage 2 — 0D hydrogen autoignition reproduction
**Goal:** reproduce the paper's chemistry-relevant benchmark with Cantera/CVODE.

Targets:
- 7-species / 16-reaction H2/O2 mechanism case described in the paper
- train/test splits over equivalence ratio and temperature
- evaluate BCT and physics constraints ablations

Deliverables:
- data generation script
- train/eval configs
- rollout and generalization metrics
- DNN/MLP baseline using existing DFODE-kit plumbing

Acceptance checks:
- seen-condition and unseen-temperature cases reproduced
- physical consistency metrics added:
  - element conservation error
  - mass-fraction-sum error
  - rollout drift vs. ground truth

### Stage 3 — EFNO support inside DFODE-kit
**Goal:** make EFNO training/evaluation durable instead of one-off scripts.

Planned work:
- add model registry entry for FNO/EFNO
- add physics-constrained trainer path
- add reproducible config objects for paper-style experiments
- add tests for serialization and basic forward/train loops
- document CLI or scripted usage

Constraint:
- do this only after a working minimal reproduction exists

### Stage 4 — target DeepFlame coupled-case preparation
**Goal:** prepare credible coupled benchmarks before expensive runs.

Planned work:
- inspect closest tutorial/example baselines per DeepFlame skill
- create living case READMEs for active cases
- document model I/O contract required by DeepFlame inference hooks
- compare existing DeepFlame DNN artifact format with EFNO deployment needs
- start with small debug runs before scaling

Target cases:
- H2 twoD_HIT_flame
- C2H4 twoD_HIT_flame

### Stage 5 — coupled CFD evaluation
**Goal:** test offline-good models for actual solver usefulness.

Primary questions:
- does EFNO remain stable in coupled rollout?
- does it preserve physical consistency better than baseline DNN integration?
- does it improve accuracy/speed tradeoff versus standard chemistry integration?
- does data assimilation / temperature-from-solver coupling reduce drift?

Deliverables:
- case-level run ledgers
- timing comparisons
- field error plots
- rollout drift analysis
- failure notes

### Stage 6 — publishable record
**Goal:** maintain a paper trail from day one.

Deliverables:
- docs pages for findings/results
- regular technical blog posts
- figure assets and experiment tables
- LaTeX manuscript and compiled PDF preprint

## Known ambiguities and risks

1. The paper text extracted cleanly, but some implementation hyperparameters are not stated clearly in text:
   - exact Fourier mode count
   - channel width / latent width
   - optimizer and schedule
   - batch size
   - exact weighting coefficients in the total loss
2. The paper mixes focal-loss discussion with a final quartile-based weighted loss formulation; implementation intent must be recorded carefully.
3. The paper's 3D turbulent NH3/H2 LES case is not identical to the target DeepFlame bundled cases, so coupled replication will require a documented adaptation path.
4. Current DeepFlame examples are DNN-oriented; EFNO deployment may need an intermediate export or a DeepFlame-side integration shim.

## Immediate next actions after this plan

1. Finish the paper implementation spec page from extracted text.
2. Create a reproducible experiment matrix covering ROBER, POLLU, and H2 autoignition.
3. Inspect DFODE-kit data/model/training seams needed for an EFNO prototype.
4. Identify the smallest first coding change enabling paper-aligned H2 autoignition baselines.
5. Commit and push the initial ingestion/docs artifacts.
