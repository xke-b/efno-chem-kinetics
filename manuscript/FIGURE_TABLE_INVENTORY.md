# Manuscript figure and table inventory

This file tracks which manuscript claims are already backed by stable figures/tables and which still need packaging.

## Current manuscript figures

### Figure 1 — Best mixed C2H4 model vs stock at 5e-6
- file used in manuscript:
  - `../docs/findings/images/c2h4-bestmix-r0p2-vs-stock-5e-06.png`
- supporting artifact:
  - `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_bestmix_r0p2_vs_stock_5e-06.json`
- supports claim:
  - current best mixed C2H4 model still has structured active-region source-term and species distortions

## Current manuscript tables

### Table 1 — H2 deployment summary
- manuscript file:
  - `manuscript/tables/h2_deployment_summary.tex`
- source artifacts:
  - `burke_corrected_self_rollout_predmainbct_frozen_temperature_sweep_comparison.json`
  - `burke_corrected_self_rollout_predmainbct_ft650_riskguard_threshold_sweep.json`
- supports claim:
  - H2 deployment requires safeguards and admits credible operating points

### Table 2 — C2H4 runtime summary at 5e-6
- manuscript file:
  - `manuscript/tables/c2h4_runtime_summary.tex`
- source artifacts:
  - stock 5e-6 field summary
  - best mixed model 5e-6 field summary
  - partial chem-proxy 10% ablation summary
- supports claim:
  - best mixed C2H4 model is better than naive semantics-only variants, but not yet solved

### Table 3 — C2H4 error anatomy summary
- manuscript file:
  - `manuscript/tables/c2h4_error_anatomy_summary.tex`
- source artifact:
  - `c2h4_bestmix_r0p2_vs_stock_5e-06.json`
- supports claim:
  - best mixed model still suppresses key late intermediates and distorts active-region chemistry

### Table 4 — C2H4 chemistry-proxy mismatch summary
- manuscript file:
  - `manuscript/tables/c2h4_chemproxy_mismatch_summary.tex`
- source artifact:
  - `c2h4_dp100_cfd_vs_chemistry_proxy_5k_summary.json`
- supports claim:
  - current full-CFD labels differ materially from chemistry-only proxy relabels

## High-priority missing packaging

### H2 offline corrected-decode figure
- desired claim:
  - decode-contract correction materially changed H2 rollout conclusions
- likely source artifacts:
  - `h2_efno_bct_state_decode_ablation/summary.json`
  - corrected vs legacy rollout findings docs

### H2 deployment timeline / fallback figure
- desired claim:
  - frozen-temperature and risk-guard choices change the learned/fallback operating regime over time
- likely source artifacts:
  - H2 frozen-temperature sweep and risk-threshold sweep JSON summaries

### C2H4 chemistry-proxy failure figure
- desired claim:
  - pure tiny chemistry-proxy training fixes semantics in principle but destroys manifold support in deployment
- likely source artifacts:
  - `c2h4_chemproxy5k_vs_stock_3e-07.json`
  - `c2h4_casepair_dp100_chemistry_proxy_5k_fno_fields_3e-07_vs_2e-07.json`

## Current paper-readiness note

The manuscript now has enough stable figure/table material for a serious draft iteration, but it still needs:
- a more complete H2 offline evidence figure set
- citations integrated into prose
- a clearer methods section with benchmark and case definitions
