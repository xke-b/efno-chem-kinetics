# C2H4 regime-support diagnosis: the current training datasets provide almost no local chemistry-label support for the real cool-onset CFD states, and even nearest neighbors often come from hot ~2400 K regions with near-zero labels

_Date: 2026-04-24_

## Why this follow-up mattered

The previous CFD-state checkpoint-vs-CVODE analysis showed two distinct coupled-failure modes:
- some branches **overreact in hot cells**
- interleaved mixed branches **underreact in cool onset cells**

The natural next question was whether the training datasets actually contain **locally relevant labeled examples** for the real CFD states in those regimes.

In other words:
- when a real C2H4 CFD cell at `1e-07` sits in the `510–700 K` onset band,
- what training samples are actually closest to it,
- and do those neighbors carry chemistry labels remotely similar to one-step CVODE chemistry from that same CFD state?

## New analysis script

Added:
- `/root/workspace/scripts/analyze_c2h4_regime_training_support.py`

This script:
- extracts real active CFD states from the C2H4 case at a chosen time
- builds two regime benchmarks:
  - cool onset: `510–700 K`
  - hot active: `1600–2600 K`
- computes one-step Cantera/CVODE chemistry labels for those exact states
- loads offline paired datasets
- finds nearest neighbors in **current-state thermochemical space** using `[T, P, BCT(Y)]`
- measures how well those neighbor labels match the true CFD-state one-step chemistry

## Output artifact

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_regime_training_support_1e-07.json`

## Datasets compared

- case-pair backbone:
  - `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`
- oneD/Xiao chemistry set:
  - `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.npy`
- mixed `r=0.2`:
  - `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r0p2.npy`
- mixed `r=1.0`:
  - `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r1p0.npy`

## Benchmark sizes

At the real C2H4 case time `1e-07`:
- cool onset `510–700 K`: `580` cells
- hot active `1600–2600 K`: `580` sampled cells

## Main result 1: the cool-onset benchmark is barely represented in the current training data

Current-state temperature fractions in the offline datasets:

- `casepair_dp100`
  - `510–700 K`: `3.286%`
  - `1600–2600 K`: `94.424%`
- `oned_100k`
  - `510–700 K`: `3.781%`
  - `1600–2600 K`: `49.263%`
- `mixed_r0p2`
  - `510–700 K`: `3.370%`
  - `1600–2600 K`: `86.837%`
- `mixed_r1p0`
  - `510–700 K`: `3.549%`
  - `1600–2600 K`: `71.909%`

So the onset band that dominates the interleaved-branch failure analysis is only about **3–4%** of these datasets.

That alone already supports the hypothesis that the coupled onset regime is not receiving enough direct supervision.

## Main result 2: nearest neighbors for the real cool-onset CFD states are often not cool

This is the strongest new evidence.

### For `casepair_dp100`
For the real CFD cool-onset cells (`510–700 K`), the nearest-neighbor current-state temperatures are:
- mean: **`2458.76 K`**
- median: `2458.76 K`
- p99: `2458.76 K`

### For `mixed_r0p2`
Nearest-neighbor current-state temperatures for the same cool CFD cells:
- mean: **`2397.51 K`**
- median: `2379.40 K`
- p99: `2458.76 K`

### For `mixed_r1p0`
Nearest-neighbor current-state temperatures:
- mean: **`2393.25 K`**
- median: `2368.98 K`
- p99: `2458.76 K`

Even the oneD-only `100k` set behaves similarly:
- mean nearest-neighbor temperature for cool CFD cells: **`2391.72 K`**

So in the full transformed current-state space used here, the real cool-onset CFD states do **not** find local offline neighbors from the same thermochemical regime. Their nearest offline matches are typically **hot states around 2.4e3 K**.

This is a severe manifold-support warning.

## Main result 3: those nearest-neighbor labels are almost chemistry-dead compared with real CVODE onset chemistry

For the cool-onset CFD benchmark, the true one-step chemistry activity is strong:
- true `ΔY` L1 mean: **`0.32816`**

But the nearest-neighbor dataset labels are essentially zero.

### case-pair backbone
Cool-onset neighbor-label summary:
- predicted-label `ΔY` L1 mean: **`2.50e-07`**
- true CVODE `ΔY` L1 mean: `0.32816`
- activity ratio: **`7.61e-07`**

Key species means from nearest labels vs real CVODE:
- `ΔC2H3`: `0` vs **`1.206e-03`**
- `ΔCH2CHO`: `0` vs **`2.303e-04`**
- `ΔCH2CO`: `~4.8e-20` vs **`1.792e-03`**
- `ΔOH`: `1.2e-07` vs **`2.244e-03`**
- `ΔHO2`: `1.68e-09` vs **`1.198e-04`**

### mixed `r=0.2`
Cool-onset neighbor-label summary:
- predicted-label `ΔY` L1 mean: **`9.43e-05`**
- true CVODE `ΔY` L1 mean: `0.32816`
- activity ratio: **`2.87e-04`**

### mixed `r=1.0`
Cool-onset neighbor-label summary:
- predicted-label `ΔY` L1 mean: **`9.05e-05`**
- true CVODE `ΔY` L1 mean: `0.32816`
- activity ratio: **`2.75e-04`**

### oneD/Xiao `100k`
Cool-onset neighbor-label summary:
- predicted-label `ΔY` L1 mean: **`1.67e-04`**
- true CVODE `ΔY` L1 mean: `0.32816`
- activity ratio: **`5.08e-04`**

So even the chemistry-oriented oneD set still provides locally matched labels that are orders of magnitude too weak for these real onset cells.

## Main result 4: the hot regime is better covered geometrically, but labels are still much too weak

For hot active CFD cells (`1600–2600 K`):
- `casepair_dp100` nearest-neighbor distance p50: `5.52`
- `mixed_r0p2` p50: `5.52`
- `mixed_r1p0` p50: `5.52`
- `oned_100k` p50: `15.59`

So the case-pair backbone is geometrically closer to the hot CFD manifold than the oneD set.

But even there, label support is weak.

For hot active cells:
- true `ΔY` L1 mean: `0.01695`
- case-pair nearest-label `ΔY` L1 mean: **`2.24e-07`**
- mixed nearest-label `ΔY` L1 mean: **`2.24e-07`**
- oneD `100k` nearest-label `ΔY` L1 mean: **`3.26e-04`**

So the case-pair datasets are not only cool-onset-poor; their local labels are also nearly chemistry-dead even for hot active cells.

## Interpretation

This result makes the training-data problem much more concrete.

### 1. The interleaved-branch cool-underreaction is now strongly explained by missing local label support
The real `510–700 K` CFD cells that matter for onset chemistry:
- are sparse in the current datasets
- do not find neighbors from the same thermochemical regime
- and the neighbor labels they do find are nearly zero compared with CVODE chemistry

That is exactly the setup that would encourage a learned model to suppress onset chemistry.

### 2. The case-pair datasets are semantically misaligned with chemistry-step supervision
The nearest-neighbor labels from the case-pair backbone are effectively chemistry-off compared with one-step CVODE from the same current state.

That supports the earlier suspicion that full-CFD pair labels are carrying transport/coupling semantics that do not match the chemistry operator the deployed model is expected to emulate.

### 3. More oneD chemistry helps geometry somewhat, but not enough by naive concatenation
Moving from `r=0.2` to `r=1.0` slightly improves current-state proximity for cool states, but the local label activity remains orders of magnitude too small.

So the problem is not just “more chemistry samples”; it is that the current oneD support is still not furnishing strong, local onset labels in the right part of the CFD manifold, and uniform mixing does not fix the semantic conflict.

## Updated hypothesis

A stronger version of the data bottleneck hypothesis is now justified:

> The main C2H4 deployment problem is not merely that the training data are imperfect. The real onset-regime CFD states are effectively out-of-manifold for the current offline datasets, and the nearest available labels from those datasets are far too inactive compared with the true one-step chemistry that the coupled solver needs.

## Most justified next step

The next data step should be **targeted onset-regime support**, not another broad ratio sweep.

That means prioritizing:
- a dedicated real-CFD cool-onset benchmark set for ongoing evaluation
- regime-targeted oneD/Xiao augmentation aimed specifically at the `510–700 K` onset band
- or direct chemistry relabeling / chemistry-native sampling for CFD-like onset states
- plus species-aware supervision on onset intermediates (`C2H3`, `CH2CHO`, `CH2CO`, `C2H5`, `HO2`, `OH`)

## Takeaway

This analysis substantially reduces uncertainty.

The current C2H4 training pipeline does not merely underperform at the cool onset regime; it provides almost no local label support for it at all. That makes the current cool-underreaction failure in DeepFlame understandable, and it argues strongly for targeted onset-regime data construction rather than more naive dataset scaling.
