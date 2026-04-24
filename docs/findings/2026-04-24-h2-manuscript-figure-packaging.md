# H2 manuscript figure packaging: promote corrected-decode and coupled operating-window evidence into manuscript-ready figures

_Date: 2026-04-24_

## Why this was the next step

After the previous manuscript iteration, the paper was C2H4-heavy in packaged figures and tables. The strongest missing manuscript-facing evidence was on the H2 side:
- one figure showing why the corrected decode contract mattered offline
- one figure showing how coupled operating windows change under threshold and guard choices

## New plotting scripts

Created:
- `/root/workspace/scripts/plot_h2_corrected_decode_ablation.py`
- `/root/workspace/scripts/plot_h2_deployment_operating_windows.py`

These convert stable JSON artifacts into manuscript-ready H2 figures.

## New manuscript-ready figures

Generated:
- `/root/workspace/docs/findings/images/h2-corrected-decode-ablation.png`
- `/root/workspace/docs/findings/images/h2-deployment-operating-windows.png`

### Figure 1: corrected-decode ablation
Source artifact:
- `/root/workspace/artifacts/experiments/h2_efno_bct_state_decode_ablation/summary.json`

Purpose:
- compare legacy decode vs corrected BCT-state decode on rollout metrics
- make explicit that the decode fix changed the empirical conclusion most strongly for self-rollout branches

### Figure 2: coupled operating windows
Source artifacts:
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_frozen_temperature_sweep_comparison.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_riskguard_threshold_sweep.json`

Purpose:
- show how learned fraction and HP-failure fraction evolve over time
- compare threshold choices (`baseline`, `FT550`, `FT600`, `FT650`)
- compare FT650 risk-guard thresholds (`0.4`, `0.5`, `0.6`) against plain FT650

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`
- `/root/workspace/manuscript/FIGURE_TABLE_INVENTORY.md`

The manuscript now includes both new H2 figures directly in the H2 sections. This makes the H2 side of the paper much more balanced with the C2H4 side.

## Compile status

The manuscript recompiles successfully after adding the new H2 figures.

Current compile output:
- `/root/workspace/manuscript/main.pdf`

## Current takeaway

The paper now has manuscript-ready visual evidence for the two most important H2 claims:
- the offline corrected-decode result was a real regime change, not a cosmetic implementation cleanup
- the coupled H2 deployment story is fundamentally about operating windows and safeguards, not simply about a single best checkpoint

## Remaining high-value manuscript gap

With these H2 figures packaged, the next strongest paper-facing gap is no longer basic evidence balance between H2 and C2H4. The next likely best step is to strengthen the manuscript narrative itself:
- add citations from the EFNO and related-paper notes
- expand methods and experimental setup details
- decide whether one more targeted C2H4 semantics experiment is needed for the paper or should be scoped explicitly as future work
