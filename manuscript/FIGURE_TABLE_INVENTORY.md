# Manuscript figure and table inventory

This file tracks which manuscript claims are already backed by stable figures/tables and which still need packaging.

## Current manuscript figures

### Figure 1 — H2 corrected-decode ablation
- file used in manuscript:
  - `../docs/findings/images/h2-corrected-decode-ablation.png`
- supporting artifact:
  - `/root/workspace/artifacts/experiments/h2_efno_bct_state_decode_ablation/summary.json`
- supports claim:
  - fixing the transformed-state decode contract materially changed H2 rollout conclusions

### Figure 2 — H2 coupled operating windows
- file used in manuscript:
  - `../docs/findings/images/h2-deployment-operating-windows.png`
- supporting artifacts:
  - `burke_corrected_self_rollout_predmainbct_frozen_temperature_sweep_comparison.json`
  - `burke_corrected_self_rollout_predmainbct_ft650_riskguard_threshold_sweep.json`
- supports claim:
  - frozen-temperature and risk-guard choices materially reshape the learned/fallback operating regime in coupled deployment

### Figure 3 — Best mixed C2H4 model vs stock at 5e-6
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

### C2H4 chemistry-proxy failure figure
- desired claim:
  - pure tiny chemistry-proxy training fixes semantics in principle but destroys manifold support in deployment
- likely source artifacts:
  - `c2h4_chemproxy5k_vs_stock_3e-07.json`
  - `c2h4_casepair_dp100_chemistry_proxy_5k_fno_fields_3e-07_vs_2e-07.json`

## Current paper-readiness note

The manuscript now has enough stable figure/table material for a serious draft iteration, but one high-value optional addition remains:
- a C$_2$H$_4$ failure-boundary figure comparing the pure chemistry-proxy or targeted-partial pre-failure state against a healthier baseline
