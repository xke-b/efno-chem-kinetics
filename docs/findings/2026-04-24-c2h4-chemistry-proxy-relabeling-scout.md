# C2H4 chemistry-proxy relabeling scout: current case-pair CFD labels differ materially from one-step chemistry-only evolution, especially on key intermediates

_Date: 2026-04-24_

## Why this was the next step

After the best-model-vs-stock error anatomy showed that the current best mixed C2H4 model still:
- over-drives cooler active cells,
- gets source-term sign wrong in much of the hot bulk,
- and suppresses key late intermediates,

…the strongest remaining hypothesis was that the bottleneck is not another dataset-mix tweak but the **label semantics themselves**.

So the next concrete step was to build the first chemistry-faithful proxy relabeling path from the existing case-pair data:
- take current CFD states from the `dp100` dataset,
- ignore the original full-CFD next-state labels,
- re-integrate each current state for one step in Cantera under a controlled reactor assumption,
- and quantify how different those chemistry-only proxy labels are from the original CFD labels.

This is not yet a final target path, but it is the first direct measurement of the label mismatch.

## New script

- `/root/workspace/scripts/relabel_c2h4_casepair_dataset_with_cantera.py`

This script:
- loads a case-pair dataset
- samples a subset if requested
- takes only the current state
- re-labels it with one-step Cantera integration
- supports `const_pressure` and `const_volume`
- writes a relabeled dataset plus a mismatch summary against the original labels

## Run performed

Source dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`

Mechanism:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_stock_baseline_np8_gpu_stocksrc/Wu24sp.yaml`

Relabeling setup:
- reactor: `const_pressure`
- `dt = 1e-7`
- subset size: `5000`
- seed: `0`

Outputs:
- relabeled dataset:
  - `/root/workspace/data/c2h4_case_pairs_smoke_dp100_chemistry_proxy_5k.npy`
- relabeled metadata:
  - `/root/workspace/data/c2h4_case_pairs_smoke_dp100_chemistry_proxy_5k.json`
- mismatch summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_dp100_cfd_vs_chemistry_proxy_5k_summary.json`

## Main result

The current `dp100` CFD labels differ materially from chemistry-only one-step evolution even before any model training.

### Bulk thermodynamic difference
- original CFD-label mean `T_next`: `2356.39 K`
- chemistry-proxy mean `T_next`: `2417.56 K`
- mean absolute `T_next` difference: `65.44 K`

So the full-CFD target and chemistry-only target are not close in temperature even at one step.

### Pressure difference confirms target-semantic mismatch
- original CFD-label mean absolute `Δp` from current state: `22.46 Pa`
- chemistry-proxy mean absolute `Δp` from current state: `~1.3e-11 Pa`

That is expected under a const-pressure reactor, but it makes the semantic mismatch explicit:
- the current case-pair labels are still carrying CFD-coupled pressure evolution,
- while a chemistry-only relabel path does not.

## Intermediate-species differences are substantial

Several key species shift strongly under chemistry-only relabeling.

### Chemistry-only proxy is **higher** than the original CFD label for:
- `HCCO`: `35.15x`
- `CH2CHO`: `4.27x`
- `CH2OH`: `3.71x`
- `C2H3`: `2.65x`
- `CH2CO`: `2.62x`
- `HO2`: `1.54x`

### Chemistry-only proxy is **lower** than the original CFD label for:
- `C2H5`: `0.041x`
- `OH`: `0.859x`

### Bulk products stay relatively similar:
- `CO`: `1.10x`
- `CO2`: `1.01x`

## Interpretation

This is a strong and useful result.

The current case-pair labels are not just “a little noisy” relative to chemistry-only evolution.
They are teaching a meaningfully different next-state map.

In particular:
- several late intermediates that the current deployed model later suppresses are actually **larger** under chemistry-only relabeling than under the original CFD labels,
- while stable bulk products remain relatively similar,
- which is exactly the kind of pattern that can let a model look acceptable on coarse thermodynamic/product metrics while learning the wrong intermediate manifold.

The `C2H5` exception is also important: the mismatch is not one-directional. It means the difference between CFD labels and chemistry-only labels is structured, not merely a global bias.

## What this changes

This is the first direct evidence that the C2H4 target-semantics issue is real in the data itself, not only in coupled deployment behavior.

So the priority reset is now supported by actual relabeling evidence:
- the present full-CFD case-pair labels do not faithfully represent chemistry-only one-step evolution
- at least under the simplest physically controlled proxy (`const_pressure`, `dt=1e-7`)

## Current takeaway

The next C2H4 gains are more likely to come from **better relabeling / target construction** than from more local dataset-mix sweeps.

The present chemistry-proxy scout does not yet solve the target problem, but it proves that the problem is real and large enough to matter.

## Most useful next step

The next justified follow-up is:
- build a **chemistry-proxy training subset** from the current best case-aligned backbone,
- then test whether training on those relabeled targets changes the source-term and intermediate-species pathologies seen in deployment,

rather than continuing to optimize only the original full-CFD target family.
