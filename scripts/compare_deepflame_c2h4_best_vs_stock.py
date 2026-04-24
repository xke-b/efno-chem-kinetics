#!/usr/bin/env python3
"""Compare a C2H4 learned DeepFlame case against the stock baseline on matched mesh fields."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH', 'N2'
]
KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'CH2OH', 'HCCO', 'CO', 'CO2', 'OH', 'HO2']
TEMP_BINS = [510.0, 700.0, 900.0, 1200.0, 1600.0, 2600.0]
QDOT_SIGN_EPS = 1e6


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--stock-case', required=True)
    p.add_argument('--model-case', required=True)
    p.add_argument('--time', required=True)
    p.add_argument('--reference-time', default='2e-06')
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-fig', required=True)
    return p.parse_args()



def read_internal_scalar_field(path: Path, fallback_n_cells: int | None = None) -> np.ndarray:
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('internalField') and 'List<scalar>' in stripped:
            count = int(lines[i + 1].strip())
            start = i + 3
            return np.array([float(lines[start + j].strip()) for j in range(count)], dtype=np.float64)
        if stripped.startswith('internalField') and 'uniform' in stripped:
            if fallback_n_cells is None:
                raise ValueError(f'Uniform field without fallback in {path}')
            value = float(stripped.split('uniform', 1)[1].replace(';', '').strip())
            return np.full(fallback_n_cells, value, dtype=np.float64)
    raise ValueError(f'Could not parse internalField from {path}')



def read_case_time_fields(case_dir: Path, time_name: str) -> dict[str, np.ndarray]:
    processor_dirs = sorted(p for p in case_dir.glob('processor*') if p.is_dir())
    base_fields = ['T', 'p', 'Qdot', 'rho', 'selectDNN']
    fields = {name: [] for name in [*base_fields, *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t)
        n = len(t)
        for name in ['p', 'Qdot', 'rho', 'selectDNN', *SPECIES]:
            fields[name].append(read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=n))
    return {k: np.concatenate(v) for k, v in fields.items()}



def summarize_bin(mask: np.ndarray, stock: dict[str, np.ndarray], model: dict[str, np.ndarray]) -> dict:
    if int(mask.sum()) == 0:
        return {'count': 0}
    stock_q = stock['Qdot'][mask]
    model_q = model['Qdot'][mask]
    strong = (np.abs(stock_q) >= QDOT_SIGN_EPS) | (np.abs(model_q) >= QDOT_SIGN_EPS)
    if strong.any():
        stock_sign = np.sign(stock_q[strong])
        model_sign = np.sign(model_q[strong])
        sign_mismatch = float(np.mean(stock_sign != model_sign))
    else:
        sign_mismatch = 0.0
    return {
        'count': int(mask.sum()),
        'stock_qdot_mean': float(np.mean(stock_q)),
        'model_qdot_mean': float(np.mean(model_q)),
        'mean_abs_qdot_diff': float(np.mean(np.abs(model_q - stock_q))),
        'sign_mismatch_fraction_strong_qdot': sign_mismatch,
        'stock_T_mean': float(np.mean(stock['T'][mask])),
        'model_T_mean': float(np.mean(model['T'][mask])),
    }



def build_summary(stock: dict[str, np.ndarray], model: dict[str, np.ndarray], frozen_temperature: float) -> dict:
    if stock['T'].shape != model['T'].shape:
        raise ValueError('Stock/model field shapes do not match')

    stock_active = stock['T'] > frozen_temperature
    model_active = model['T'] > frozen_temperature
    union_active = stock_active | model_active
    intersection_active = stock_active & model_active

    summary = {
        'n_cells_total': int(stock['T'].shape[0]),
        'n_active_stock': int(stock_active.sum()),
        'n_active_model': int(model_active.sum()),
        'n_active_union': int(union_active.sum()),
        'n_active_intersection': int(intersection_active.sum()),
        'activity': {
            'stock_only_fraction': float(np.mean(stock_active & ~model_active)),
            'model_only_fraction': float(np.mean(model_active & ~stock_active)),
            'intersection_fraction': float(np.mean(intersection_active)),
        },
    }

    mask = union_active
    stock_q = stock['Qdot'][mask]
    model_q = model['Qdot'][mask]
    stock_t = stock['T'][mask]
    model_t = model['T'][mask]
    stock_p = stock['p'][mask]
    model_p = model['p'][mask]

    strong = (np.abs(stock_q) >= QDOT_SIGN_EPS) | (np.abs(model_q) >= QDOT_SIGN_EPS)
    sign_mismatch = float(np.mean(np.sign(stock_q[strong]) != np.sign(model_q[strong]))) if strong.any() else 0.0

    summary['active_union_metrics'] = {
        'stock_qdot_mean': float(np.mean(stock_q)),
        'model_qdot_mean': float(np.mean(model_q)),
        'qdot_ratio_model_to_stock_mean': float(np.mean(model_q) / np.mean(stock_q)) if abs(np.mean(stock_q)) > 0 else None,
        'mean_abs_qdot_diff': float(np.mean(np.abs(model_q - stock_q))),
        'sign_mismatch_fraction_strong_qdot': sign_mismatch,
        'stock_T_mean': float(np.mean(stock_t)),
        'model_T_mean': float(np.mean(model_t)),
        'mean_abs_T_diff': float(np.mean(np.abs(model_t - stock_t))),
        'stock_p_mean': float(np.mean(stock_p)),
        'model_p_mean': float(np.mean(model_p)),
        'mean_abs_p_diff': float(np.mean(np.abs(model_p - stock_p))),
    }

    species_summary = {}
    for name in KEY_SPECIES:
        stock_v = stock[name][mask]
        model_v = model[name][mask]
        denom = max(float(np.mean(stock_v)), 1e-20)
        species_summary[name] = {
            'stock_mean': float(np.mean(stock_v)),
            'model_mean': float(np.mean(model_v)),
            'model_to_stock_mean_ratio': float(np.mean(model_v) / denom),
            'mean_abs_diff': float(np.mean(np.abs(model_v - stock_v))),
            'stock_p99': float(np.quantile(stock_v, 0.99)),
            'model_p99': float(np.quantile(model_v, 0.99)),
        }
    summary['key_species_active_union'] = species_summary

    bins = {}
    for lo, hi in zip(TEMP_BINS[:-1], TEMP_BINS[1:]):
        bin_mask = union_active & (stock['T'] >= lo) & (stock['T'] < hi)
        bins[f'{lo:.0f}-{hi:.0f}K'] = summarize_bin(bin_mask, stock, model)
    summary['temperature_bin_metrics'] = bins

    # rank strongest species distortions by log-ratio magnitude on means
    ranked = []
    for name, rec in species_summary.items():
        ratio = rec['model_to_stock_mean_ratio']
        ranked.append({
            'species': name,
            'model_to_stock_mean_ratio': ratio,
            'abs_log10_ratio': abs(float(np.log10(max(ratio, 1e-20)))) if ratio > 0 else 99.0,
            'stock_mean': rec['stock_mean'],
            'model_mean': rec['model_mean'],
        })
    summary['ranked_species_distortions'] = sorted(ranked, key=lambda x: x['abs_log10_ratio'], reverse=True)
    return summary



def plot(summary: dict, out_fig: Path) -> None:
    bins = summary['temperature_bin_metrics']
    labels = list(bins.keys())
    stock_q = [bins[k].get('stock_qdot_mean', np.nan) for k in labels]
    model_q = [bins[k].get('model_qdot_mean', np.nan) for k in labels]
    sign_mismatch = [bins[k].get('sign_mismatch_fraction_strong_qdot', np.nan) for k in labels]

    ranked = summary['ranked_species_distortions'][:6]
    species = [r['species'] for r in ranked]
    ratios = [r['model_to_stock_mean_ratio'] for r in ranked]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    x = np.arange(len(labels))
    width = 0.38
    axes[0].bar(x - width/2, stock_q, width=width, label='stock')
    axes[0].bar(x + width/2, model_q, width=width, label='best_mix_r0p2')
    axes[0].set_xticks(x, labels, rotation=25, ha='right')
    axes[0].set_title('Mean Qdot by stock-temperature bin')
    axes[0].legend(frameon=False)

    axes[1].bar(x, sign_mismatch)
    axes[1].set_xticks(x, labels, rotation=25, ha='right')
    axes[1].set_ylim(0, 1)
    axes[1].set_title('Qdot sign mismatch fraction')

    axes[2].bar(np.arange(len(species)), ratios)
    axes[2].axhline(1.0, color='k', linestyle='--', linewidth=1)
    axes[2].set_xticks(np.arange(len(species)), species, rotation=25, ha='right')
    axes[2].set_title('Top species mean-ratio distortions')
    axes[2].set_ylabel('model / stock mean')

    fig.suptitle('Best C2H4 mixed model vs stock at 5e-6')
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=180, bbox_inches='tight')



def main() -> None:
    args = parse_args()
    stock = read_case_time_fields(Path(args.stock_case), args.time)
    model = read_case_time_fields(Path(args.model_case), args.time)
    summary = build_summary(stock, model, args.frozen_temperature)
    summary.update({
        'stock_case': str(Path(args.stock_case).resolve()),
        'model_case': str(Path(args.model_case).resolve()),
        'time': args.time,
        'reference_time': args.reference_time,
        'frozen_temperature': args.frozen_temperature,
        'note': 'Deployment-facing matched-mesh comparison between stock C2H4 DeepFlame and the current best mixed learned model.',
    })
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    plot(summary, Path(args.out_fig))
    print(json.dumps({'out_json': str(out_json.resolve()), 'out_fig': str(Path(args.out_fig).resolve())}, indent=2))


if __name__ == '__main__':
    main()
