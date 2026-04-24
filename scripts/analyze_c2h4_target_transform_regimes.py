#!/usr/bin/env python3
"""Analyze C2H4 target-transform regime behavior inspired by Xiao et al. (2026).

This script compares the current DFODE-style BCT state-delta target against a
power transform applied directly to physical species deltas. The goal is to
quantify whether the BCT-delta target depends strongly on the current species
level in low-temperature/small-delta regimes, which would mirror the failure
mode discussed by Xiao et al. for Box-Cox-on-state targets.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, '/opt/src/DFODE-kit')
from dfode_kit.utils import BCT  # noqa: E402


DELTA_BINS = [
    (1e-15, 1e-12),
    (1e-12, 1e-10),
    (1e-10, 1e-8),
    (1e-8, 1e-6),
]

DEFAULT_SPECIES = [
    'O2',
    'C2H4',
    'HO2',
    'C2H5',
    'C2H3',
    'CH2CHO',
    'HCCO',
    'CH2CO',
    'CH2OH',
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', action='append', required=True, help='Path to dataset .npy; may be repeated')
    p.add_argument('--metadata', action='append', required=True, help='Path to dataset metadata .json; may be repeated')
    p.add_argument('--lambda-power', type=float, default=0.1)
    p.add_argument('--low-temp-threshold', type=float, default=1000.0)
    p.add_argument('--out', required=True)
    return p.parse_args()



def safe_log10(x: np.ndarray, floor: float = 1e-30) -> np.ndarray:
    return np.log10(np.clip(np.asarray(x, dtype=np.float64), floor, None))



def pearson_corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 3 or len(y) < 3:
        return None
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    x_std = x.std()
    y_std = y.std()
    if x_std <= 0 or y_std <= 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])



def summarize_array(values: np.ndarray) -> dict[str, float] | None:
    if len(values) == 0:
        return None
    values = np.asarray(values, dtype=np.float64)
    return {
        'min': float(values.min()),
        'p05': float(np.quantile(values, 0.05)),
        'p50': float(np.quantile(values, 0.50)),
        'p95': float(np.quantile(values, 0.95)),
        'max': float(values.max()),
        'mean': float(values.mean()),
        'std': float(values.std()),
    }



def _resolve_species_info(meta: dict, metadata_path: Path) -> tuple[list[str], int]:
    if 'species_names' in meta and 'n_species' in meta:
        return list(meta['species_names']), int(meta['n_species'])
    for component in meta.get('components', []):
        dataset_str = component.get('dataset')
        if not dataset_str:
            continue
        component_meta_path = Path(dataset_str).with_suffix('.json')
        if not component_meta_path.is_absolute():
            component_meta_path = (metadata_path.parent / component_meta_path).resolve()
        if component_meta_path.exists():
            component_meta = json.loads(component_meta_path.read_text(encoding='utf-8'))
            if 'species_names' in component_meta and 'n_species' in component_meta:
                return list(component_meta['species_names']), int(component_meta['n_species'])
    raise KeyError(f'Could not resolve species_names/n_species from {metadata_path}')



def analyze_dataset(dataset_path: Path, metadata_path: Path, lambda_power: float, low_temp_threshold: float) -> dict:
    data = np.load(dataset_path)
    meta = json.loads(metadata_path.read_text(encoding='utf-8'))
    species_names, n_species = _resolve_species_info(meta, metadata_path)

    current = data[:, : 2 + n_species]
    nxt = data[:, 2 + n_species :]
    temp = current[:, 0]
    y0 = np.clip(current[:, 2:], 0.0, 1.0)
    y1 = np.clip(nxt[:, 2:], 0.0, 1.0)
    delta = y1 - y0

    main_species_names = species_names[:-1]
    bct0 = BCT(y0)[:, :-1]
    bct1 = BCT(y1)[:, :-1]
    bct_delta = bct1 - bct0
    power_delta = np.sign(delta[:, :-1]) * (np.abs(delta[:, :-1]) ** lambda_power) / lambda_power

    low_temp_mask = temp < low_temp_threshold
    high_temp_mask = ~low_temp_mask

    per_species = {}
    for name in DEFAULT_SPECIES:
        if name not in main_species_names:
            continue
        idx = main_species_names.index(name)
        species_result = {
            'all': {},
            'low_temp': {},
            'high_temp': {},
        }
        for regime_name, regime_mask in [('all', np.ones(len(temp), dtype=bool)), ('low_temp', low_temp_mask), ('high_temp', high_temp_mask)]:
            d = delta[regime_mask, idx]
            y = y0[regime_mask, idx]
            bct = bct_delta[regime_mask, idx]
            pt = power_delta[regime_mask, idx]
            regime_result = {
                'count': int(len(d)),
                'current_y_summary': summarize_array(y),
                'abs_delta_summary': summarize_array(np.abs(d)),
                'abs_bct_delta_summary': summarize_array(np.abs(bct)),
                'abs_power_delta_summary': summarize_array(np.abs(pt)),
                'delta_bins': {},
            }
            for lo, hi in DELTA_BINS:
                mask = (np.abs(d) >= lo) & (np.abs(d) < hi)
                key = f'[{lo:.0e},{hi:.0e})'
                if int(mask.sum()) == 0:
                    regime_result['delta_bins'][key] = {'count': 0}
                    continue
                log_current_y = safe_log10(y[mask])
                log_abs_delta = safe_log10(np.abs(d[mask]))
                log_abs_bct = safe_log10(np.abs(bct[mask]))
                log_abs_pt = safe_log10(np.abs(pt[mask]))
                regime_result['delta_bins'][key] = {
                    'count': int(mask.sum()),
                    'current_y_log10_summary': summarize_array(log_current_y),
                    'bct_delta_log10_summary': summarize_array(log_abs_bct),
                    'power_delta_log10_summary': summarize_array(log_abs_pt),
                    'corr_log_current_y_vs_log_abs_bct_delta': pearson_corr(log_current_y, log_abs_bct),
                    'corr_log_current_y_vs_log_abs_power_delta': pearson_corr(log_current_y, log_abs_pt),
                    'corr_log_abs_delta_vs_log_abs_bct_delta': pearson_corr(log_abs_delta, log_abs_bct),
                    'corr_log_abs_delta_vs_log_abs_power_delta': pearson_corr(log_abs_delta, log_abs_pt),
                }
            species_result[regime_name] = regime_result
        per_species[name] = species_result

    derived_highlights = []
    for name, result in per_species.items():
        low_bins = result['low_temp']['delta_bins']
        for key, metrics in low_bins.items():
            if metrics.get('count', 0) < 100:
                continue
            corr_y_bct = metrics.get('corr_log_current_y_vs_log_abs_bct_delta')
            corr_y_pt = metrics.get('corr_log_current_y_vs_log_abs_power_delta')
            corr_d_bct = metrics.get('corr_log_abs_delta_vs_log_abs_bct_delta')
            corr_d_pt = metrics.get('corr_log_abs_delta_vs_log_abs_power_delta')
            if corr_y_bct is None or corr_d_bct is None or corr_d_pt is None:
                continue
            derived_highlights.append({
                'species': name,
                'delta_bin': key,
                'count': metrics['count'],
                'bct_current_y_dependence_abs_corr': abs(corr_y_bct),
                'power_current_y_dependence_abs_corr': abs(corr_y_pt) if corr_y_pt is not None else None,
                'bct_delta_resolution_corr': corr_d_bct,
                'power_delta_resolution_corr': corr_d_pt,
                'bct_vs_power_resolution_gap': corr_d_pt - corr_d_bct,
            })

    derived_highlights.sort(key=lambda item: (item['bct_vs_power_resolution_gap'], item['bct_current_y_dependence_abs_corr']), reverse=True)

    return {
        'dataset': str(dataset_path),
        'metadata': str(metadata_path),
        'lambda_power': lambda_power,
        'low_temp_threshold': low_temp_threshold,
        'n_rows': int(len(data)),
        'n_species': n_species,
        'species_names': species_names,
        'per_species': per_species,
        'top_low_temp_bct_pathologies': derived_highlights[:12],
    }



def main() -> None:
    args = parse_args()
    if len(args.dataset) != len(args.metadata):
        raise SystemExit('--dataset and --metadata must appear the same number of times')

    analyses = []
    for dataset_str, metadata_str in zip(args.dataset, args.metadata):
        analyses.append(
            analyze_dataset(
                Path(dataset_str).resolve(),
                Path(metadata_str).resolve(),
                lambda_power=args.lambda_power,
                low_temp_threshold=args.low_temp_threshold,
            )
        )

    out = {
        'analyses': analyses,
        'note': 'Current-Y dependence in small-delta regimes is undesirable for scale-separated low-temperature learning; PT should depend almost entirely on delta magnitude.',
    }

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
