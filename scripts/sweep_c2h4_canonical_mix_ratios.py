#!/usr/bin/env python3
"""Sweep effective mix ratios between C2H4 case-pair dp100 and canonical augmented data.

This is a calibration study for how much canonical augmented data could be mixed
into the current best case-pair dataset before overshooting key species coverage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'OH', 'CO', 'CO2']
THRESHOLDS = {
    'C2H5': 1e-8,
    'C2H3': 1e-8,
    'CH2CHO': 1e-8,
    'CH2CO': 1e-8,
    'OH': 1e-5,
    'CO': 1e-4,
    'CO2': 1e-4,
}
CASE_SPECIES_ORDER = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO', 'HCCO', 'CH2CO', 'CH2OH', 'N2'
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--casepair', required=True)
    p.add_argument('--casepair-meta', required=True)
    p.add_argument('--canonical', required=True)
    p.add_argument('--canonical-meta', required=True)
    p.add_argument('--stock-json', required=True)
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-fig', required=True)
    return p.parse_args()



def dataset_stats(dataset_path: Path, meta_path: Path) -> dict:
    arr = np.load(dataset_path)
    meta = json.loads(meta_path.read_text())
    species_names = meta['species_names']
    n_species = len(species_names)
    next_species = arr[:, 2 + n_species + 2 :]
    out = {'rows': int(len(arr)), 'species': {}}
    for name in KEY_SPECIES:
        idx = species_names.index(name)
        vals = next_species[:, idx]
        thr = THRESHOLDS[name]
        out['species'][name] = {
            'mean_next': float(vals.mean()),
            'frac_next_ge_threshold': float(np.mean(vals >= thr)),
        }
    return out



def stock_stats(stock_json: Path) -> dict:
    payload = json.loads(stock_json.read_text())
    if 'species' in payload:
        species_block = payload['species']
    elif 'case_summaries' in payload:
        first_case = next(iter(payload['case_summaries'].values()))
        species_block = first_case['summary']['species']
    else:
        raise KeyError('Could not find stock species block in stock_json')

    out = {'species': {}}
    for name in KEY_SPECIES:
        record = species_block[name]
        out['species'][name] = {
            'mean': float(record['mean']),
            'frac_ge_threshold': float(record['frac_ge_threshold']),
        }
    return out



def mixed_metrics(base: dict, canon: dict, stock: dict, ratio: float) -> dict:
    # ratio = effective canonical weight relative to casepair weight.
    w_base = 1.0 / (1.0 + ratio)
    w_canon = ratio / (1.0 + ratio)
    result = {'ratio': ratio, 'species': {}, 'aggregate': {}}
    mae_mean = []
    mae_frac = []
    for sp in KEY_SPECIES:
        mix_mean = w_base * base['species'][sp]['mean_next'] + w_canon * canon['species'][sp]['mean_next']
        mix_frac = w_base * base['species'][sp]['frac_next_ge_threshold'] + w_canon * canon['species'][sp]['frac_next_ge_threshold']
        stock_mean = stock['species'][sp]['mean']
        stock_frac = stock['species'][sp]['frac_ge_threshold']
        err_mean = abs(mix_mean - stock_mean)
        err_frac = abs(mix_frac - stock_frac)
        mae_mean.append(err_mean)
        mae_frac.append(err_frac)
        result['species'][sp] = {
            'mixed_mean_next': mix_mean,
            'mixed_frac_next_ge_threshold': mix_frac,
            'stock_mean': stock_mean,
            'stock_frac_ge_threshold': stock_frac,
            'abs_error_mean': err_mean,
            'abs_error_fraction': err_frac,
        }
    result['aggregate'] = {
        'mean_abs_error_mean': float(np.mean(mae_mean)),
        'mean_abs_error_fraction': float(np.mean(mae_frac)),
        'combined_score': float(np.mean(mae_mean) + np.mean(mae_frac)),
    }
    return result



def plot(results: list[dict], out_fig: Path) -> None:
    ratios = [r['ratio'] for r in results]
    frac_err = [r['aggregate']['mean_abs_error_fraction'] for r in results]
    mean_err = [r['aggregate']['mean_abs_error_mean'] for r in results]
    combined = [r['aggregate']['combined_score'] for r in results]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    axes[0].plot(ratios, frac_err, marker='o')
    axes[0].set_xscale('log')
    axes[0].set_title('Mean abs fraction error')
    axes[0].set_xlabel('canonical / casepair weight ratio')
    axes[0].set_ylabel('error')

    axes[1].plot(ratios, mean_err, marker='o')
    axes[1].set_xscale('log')
    axes[1].set_title('Mean abs species-mean error')
    axes[1].set_xlabel('canonical / casepair weight ratio')
    axes[1].set_ylabel('error')

    axes[2].plot(ratios, combined, marker='o')
    axes[2].set_xscale('log')
    axes[2].set_title('Combined calibration score')
    axes[2].set_xlabel('canonical / casepair weight ratio')
    axes[2].set_ylabel('score')

    fig.suptitle('C2H4 canonical-mix calibration sweep')
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=180, bbox_inches='tight')



def main() -> None:
    args = parse_args()
    base = dataset_stats(Path(args.casepair), Path(args.casepair_meta))
    canon = dataset_stats(Path(args.canonical), Path(args.canonical_meta))
    stock = stock_stats(Path(args.stock_json))

    ratios = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    results = [mixed_metrics(base, canon, stock, ratio) for ratio in ratios]
    best = min(results, key=lambda r: r['aggregate']['combined_score'])
    payload = {
        'casepair_rows': base['rows'],
        'canonical_rows': canon['rows'],
        'ratios': results,
        'best_ratio_by_combined_score': best,
        'note': 'Calibration sweep for mixing paper-inspired canonical augmented C2H4 data into the current case-pair dp100 dataset.',
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    plot(results, Path(args.out_fig))
    print(json.dumps({'out_json': str(out_json.resolve()), 'out_fig': str(Path(args.out_fig).resolve())}, indent=2))


if __name__ == '__main__':
    main()
