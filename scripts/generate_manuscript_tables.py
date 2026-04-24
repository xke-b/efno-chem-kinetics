#!/usr/bin/env python3
"""Generate manuscript-ready LaTeX tables from current experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/root/workspace')
ART = ROOT / 'artifacts' / 'experiments'
OUT = ROOT / 'manuscript' / 'tables'


def fmt(x, digits=3):
    if x is None:
        return '--'
    if isinstance(x, str):
        return x
    if abs(x) >= 1e4 or (abs(x) > 0 and abs(x) < 1e-3):
        return f'{x:.2e}'
    return f'{x:.{digits}f}'



def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')



def c2h4_table() -> None:
    stock = json.loads((ART / 'deepflame_c2h4_smoke_analysis' / 'c2h4_stock_baseline_np8_gpu_stocksrc_fields_5e-06_vs_2e-06.json').read_text())
    best = json.loads((ART / 'deepflame_c2h4_smoke_analysis' / 'c2h4_casepair_dp100_plus_canonical_r0p2_fno_batched_full_fields_5e-06_vs_2e-06.json').read_text())
    partial = json.loads((ART / 'deepflame_c2h4_smoke_analysis' / 'c2h4_casepair_dp100_partial_chemproxy5k_fno_fields_5e-06_vs_2e-06.json').read_text())
    rows = [
        ('Stock DeepFlame', stock['qdot']['mean'], 1.0, stock['pressure']['max'], stock['temperature']['min'], stock['deltas_from_reference']['T']['mean_abs_delta']),
        ('Best mixed ($dp100+canon@0.2$)', best['qdot']['mean'], best['qdot']['mean']/stock['qdot']['mean'], best['pressure']['max'], best['temperature']['min'], best['deltas_from_reference']['T']['mean_abs_delta']),
        ('Partial chem-proxy (10\%)', partial['qdot']['mean'], partial['qdot']['mean']/stock['qdot']['mean'], partial['pressure']['max'], partial['temperature']['min'], partial['deltas_from_reference']['T']['mean_abs_delta']),
    ]
    body = '\n'.join(
        f"{name} & {fmt(q)} & {fmt(ratio)} & {fmt(pmax)} & {fmt(tmin)} & {fmt(dT)} \\\\" for name, q, ratio, pmax, tmin, dT in rows
    )
    tex = rf"""\begin{{table}}[t]
\centering
\small
\caption{{C$_2$H$_4$ deployment-facing summary at $5\times10^{{-6}}$ for the stock baseline, the current best mixed model, and a naive partial chemistry-proxy relabeling ablation.}}
\label{{tab:c2h4-runtime-summary}}
\begin{{tabular}}{{p{{3.1cm}}rrrrr}}
\toprule
Model & Mean $\dot{{Q}}$ & $\dot{{Q}}$/stock & $p_{{\max}}$ (Pa) & $T_{{\min}}$ (K) & mean $|\Delta T|$ (K) \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    write(OUT / 'c2h4_runtime_summary.tex', tex)



def h2_table() -> None:
    sweep = json.loads((ART / 'deepflame_h2_smoke_analysis' / 'burke_corrected_self_rollout_predmainbct_frozen_temperature_sweep_comparison.json').read_text())['summary']
    risk = json.loads((ART / 'deepflame_h2_smoke_analysis' / 'burke_corrected_self_rollout_predmainbct_ft650_riskguard_threshold_sweep.json').read_text())['summary']
    rows = [
        ('FT550', sweep['ft550']['learned_fraction_at_2e-05'], sweep['ft550']['cumulative_fallback_fraction_active_at_2e-05'], sweep['ft550']['first_time_above_95pct_fallback']),
        ('FT600', sweep['ft600']['learned_fraction_at_2e-05'], sweep['ft600']['cumulative_fallback_fraction_active_at_2e-05'], sweep['ft600']['first_time_above_95pct_fallback']),
        ('FT650', sweep['ft650']['learned_fraction_at_2e-05'], sweep['ft650']['cumulative_fallback_fraction_active_at_2e-05'], sweep['ft650']['first_time_above_95pct_fallback']),
        ('FT650+risk@0.5', risk['risk_t05']['learned_fraction_at_2e-05'], risk['risk_t05']['cumulative_fallback_fraction_active_at_2e-05'], risk['risk_t05']['first_time_above_95pct_fallback']),
    ]
    body = '\n'.join(
        f"{name} & {fmt(learned)} & {fmt(fallback)} & {ft95 if ft95 is not None else '--'} \\\\" for name, learned, fallback, ft95 in rows
    )
    tex = rf"""\begin{{table}}[t]
\centering
\small
\caption{{Selected H$_2$ coupled-deployment operating points for the corrected branch in DeepFlame.}}
\label{{tab:h2-deployment-summary}}
\begin{{tabular}}{{p{{2.5cm}}p{{2.8cm}}p{{3.4cm}}p{{2.2cm}}}}
\toprule
Mode & Learned frac. at $2\times10^{{-5}}$ & Cum. fallback frac. at $2\times10^{{-5}}$ & First time $>95\%$ fallback \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    write(OUT / 'h2_deployment_summary.tex', tex)



def c2h4_error_anatomy_table() -> None:
    comp = json.loads((ART / 'deepflame_c2h4_smoke_analysis' / 'c2h4_bestmix_r0p2_vs_stock_5e-06.json').read_text())
    rows = []
    for rec in comp['ranked_species_distortions'][:6]:
        rows.append((rec['species'], rec['stock_mean'], rec['model_mean'], rec['model_to_stock_mean_ratio']))
    body = '\n'.join(
        f"{name} & {fmt(stock)} & {fmt(model)} & {fmt(ratio)} \\\\" for name, stock, model, ratio in rows
    )
    tex = rf"""\begin{{table}}[t]
\centering
\small
\caption{{Largest active-region species distortions for the current best mixed C$_2$H$_4$ model relative to stock at $5\times10^{{-6}}$.}}
\label{{tab:c2h4-error-anatomy}}
\begin{{tabular}}{{lrrr}}
\toprule
Species & Stock mean & Model mean & Model/stock \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    write(OUT / 'c2h4_error_anatomy_summary.tex', tex)



def c2h4_chemproxy_mismatch_table() -> None:
    relabel = json.loads((ART / 'deepflame_c2h4_smoke_analysis' / 'c2h4_dp100_cfd_vs_chemistry_proxy_5k_summary.json').read_text())
    rows = []
    for rec in relabel['ranked_key_species_shift'][:6]:
        rows.append((rec['species'], rec['orig_mean_next'], rec['chem_mean_next'], rec['chem_to_orig_mean_ratio']))
    body = '\n'.join(
        f"{name} & {fmt(orig)} & {fmt(chem)} & {fmt(ratio)} \\\\" for name, orig, chem, ratio in rows
    )
    tex = rf"""\begin{{table}}[t]
\centering
\small
\caption{{Largest mean-ratio shifts between original CFD next-state labels and chemistry-proxy relabels on a 5k-row C$_2$H$_4$ subset.}}
\label{{tab:c2h4-chemproxy-mismatch}}
\begin{{tabular}}{{lrrr}}
\toprule
Species & Original next mean & Chemistry-proxy next mean & Chem/original \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
    write(OUT / 'c2h4_chemproxy_mismatch_summary.tex', tex)



def main() -> None:
    c2h4_table()
    h2_table()
    c2h4_error_anatomy_table()
    c2h4_chemproxy_mismatch_table()
    print(json.dumps({'tables_dir': str(OUT.resolve())}, indent=2))


if __name__ == '__main__':
    import json
    main()
