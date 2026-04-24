# Research-progress principles and targeted C2H4 relabel scout: define what counts as actual progress, then implement a selective-semantics path

_Date: 2026-04-24_

## Why this was the next step

The project had become structurally strong on documentation and manuscript assembly, but the next meaningful step needed to reconnect with the core of good research: experiments that reduce an important uncertainty rather than only adding more artifacts.

So I did two things in sequence:
1. used web search to gather principles for what makes research genuinely progressive,
2. turned those principles into a concrete coding step for the active C2H4 bottleneck.

## Web search: what makes good research and actual progress?

I used Exa search to gather sources on rigorous and progressive research practice.

Representative sources reviewed:
- Schwab et al., *Ten simple rules for good research practice* (PLOS Comput Biol, 2022)
- Casadevall and Fang, *Rigorous Science: a How-To Guide* (mBio, 2016)
- Vranješ and Niggemann, *Design Principles for Falsifiable, Replicable and Reproducible Empirical ML Research* (arXiv, 2024)
- Hunter, *The science of progress and the progress of science* (EMBO Reports, 2013)
- supporting discussion on the value of negative results and publication bias

## Distilled principles for this project

The most useful principles were:
- progress means reducing an important uncertainty, not just producing more output
- each experiment should test a sharp claim with a plausible failure mode
- negative results are valuable when they rule out a tempting explanation
- reproducibility is part of the result
- metrics should match operational use, not only offline fit
- small decisive experiments are often better than broad local sweeps

## Durable guidance file added

Created:
- `/root/workspace/manuscript/guidelines/research-progress-principles.md`

Also updated:
- `/root/workspace/manuscript/guidelines/README.md`

This now records the project-local standard for what should count as good progress in the next phase.

## Coding step: implement selective relabeling infrastructure for C2H4

The web-grounded conclusion was that the next C2H4 step should not be another broad sweep. It should be a **minimal decisive experiment** that tests the selective-semantics hypothesis directly.

### New script 1: targeted candidate selector
Created:
- `/root/workspace/scripts/select_c2h4_relabel_candidates.py`

What it does:
- loads a C2H4 dataset plus metadata
- scores rows by intermediate-species support
- enforces a temperature-bucket mix between cooler active states and hotter active states
- writes explicit row indices for reproducible targeted relabeling
- writes a targeted-vs-random selection summary

### New script 2: relabeler now supports explicit index files
Updated:
- `/root/workspace/scripts/relabel_c2h4_casepair_dataset_with_cantera.py`

New capability:
- `--index-file`

This allows chemistry-proxy relabeling to act on deliberately chosen rows rather than only a random sample.

## New targeted C2H4 relabel scout

### Source dataset
- `/root/workspace/data/c2h4_case_pairs_late_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_late_dp100.json`

### Targeted selection outputs
- indices:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_late_dp100_targeted_relabel_indices_3k.json`
- selection summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_late_dp100_targeted_relabel_selection_summary_3k.json`

### Chemistry-proxy relabel outputs
- relabeled dataset:
  - `/root/workspace/data/c2h4_case_pairs_late_dp100_targeted_chemproxy_3k.npy`
- relabeled metadata:
  - `/root/workspace/data/c2h4_case_pairs_late_dp100_targeted_chemproxy_3k.json`
- mismatch summary:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_late_dp100_targeted_cfd_vs_chemproxy_3k_summary.json`

## Main targeted-selection result

The targeted selector does what we wanted it to do.

Compared with a random 3k subset from the same late-window dataset:
- targeted subset mean temperature: `1398.65 K`
- random subset mean temperature: `2212.80 K`
- targeted intermediate-species sum mean: `3.134e-03`
- random intermediate-species sum mean: `5.358e-04`

So the targeted subset is about **5.85x richer** in the chosen intermediate manifold while shifting strongly toward the cooler regime that the deployed model was over-driving.

The selected 3k rows are explicitly balanced by construction:
- `1800` cool-active rows (`60%`)
- `1200` hot rows (`40%`)

## Main targeted relabeling result

When these targeted late-window rows are relabeled with one-step chemistry-only Cantera integration:
- mean absolute `T_next` difference between original CFD labels and chemistry-only proxy labels is `655.999 K`
- original mean absolute `Δp` from current state is `76.46 Pa`
- chemistry-proxy mean absolute `Δp` from current state is effectively zero under the const-pressure reactor assumption

Key species shifts remain large and structured:
- `HCCO`: `10.10x`
- `C2H3`: `2.13x`
- `OH`: `2.27x`
- `C2H5`: `0.0119x`
- `HO2`: `0.2395x`

This means the semantics mismatch is not only real in the earlier random early-window scout. It becomes even more pronounced in the late-window targeted regime that is closer to the deployed model's current failure anatomy.

## Why this matters

This is the first concrete implementation step toward the selective-semantics strategy implied by the earlier negative controls.

Instead of asking only:
- “what fraction of labels should be replaced?”

we can now ask a sharper research question:
- “does relabeling the right rows improve the chemistry manifold without destroying runtime support?”

That is much closer to actual progress than another random partial-replacement ablation.

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`

The manuscript now notes the new targeted relabeling scout as supporting evidence for the selective-semantics forward path.

## Current takeaway

The project now has both:
- a web-grounded local statement of what should count as good research progress,
- and a new coding path that operationalizes that standard for the active C2H4 bottleneck.

The next justified coding step is now clearer than before:
- train a model on a selectively relabeled dataset built from this targeted path,
- then test whether it improves late intermediates and source-term behavior relative to random relabeling and the current best mixed baseline.
